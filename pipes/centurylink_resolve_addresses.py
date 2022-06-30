"""
Verizon Geocoding Scraper
"""
import os
import json
import gzip
import requests
import random
import time
import sys

import pandas as pd
import tqdm.asyncio
import aiohttp
import asyncio

from browser_utils import Proxy, Session, format_full_address, read_ndjson, dump_ndjson
from config import cities

n_threads = 100
request_limit = 1000000
percent_addresses_ok = .7
AUTH_URL = "https://shop.centurylink.com/uas/oauth"
    
def chunked_http_client(n_threads):
    """
    Returns a function that can fetch from a URL, ensuring that only
    "num_chunks" of simultaneous connects are made.
    """
    semaphore = asyncio.Semaphore(n_threads)
    
    async def async_verify_address(record, session, proxy, client_session, *args, **kwargs):
        nonlocal semaphore
        async with semaphore:
            if client_session.closed:
                sys.exit(1)
            address = record['raw_address']
            address = ' '.join(address.split())
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Access-Control-Allow-Origin': '*',
                'Authorization': session.get_token(),
                'Connection': 'keep-alive',
                'ContentType': 'application/json',
                'Origin': 'https://shop.centurylink.com',
                'Referer': 'https://shop.centurylink.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
                'sec-ch-ua-mobile': '?0',
                'withCredentials': 'true',
            }
            params = {'addr': address}
            try:
                async with client_session.request("GET", 
                                                  url='https://api.lumen.com/Application/v4/DCEP-Consumer/addressPredict',
                                                  headers=headers, 
                                                  params=params,
                                                  proxy=proxy.get_proxy(new_ip=False),
                                                  **kwargs) as response:
                    if response.status == 200:
                        data = await response.json()
                        suggestions = data.get('predictedAddressList')
                        if suggestions:
                            record['address_suggestions'] = suggestions
                            await asyncio.sleep(.2)
                            return record
                        rate_limit = data.get('exception')
                        if rate_limit:
                            if rate_limit['httpStatusCode'] == '500':
                                print("rate limited")
                                proxy.generate_proxy()
                                session.get_token()
                                await asyncio.sleep(3)
                    # wait and make the request again
                    elif response.status in [429, 502, 503, 504]:
                        print(f"Rate limited: {address} code: {response.status}")
                        proxy.generate_proxy()
                        session.get_token()
                        await asyncio.sleep(3)
                    return None
                
        except aiohttp.ClientProxyConnectionError as e:
                print("Too many proxy connections")
                await asyncio.sleep(2)
            
    return async_verify_address


async def run_experiment(request_limit=request_limit, n_threads=n_threads):
    http_client = chunked_http_client(n_threads)
    timeout = aiohttp.ClientTimeout(total=60)
    inputs = [_ for _ in cities if _.get('centurylink') == True]
    for d in inputs:
        fn = d['fn'].replace('../data/open_addresses/', '../data/open_addresses_enriched/')
        city = d['city']
        state = d['state']
        if state != 'IA':
            continue
        fn_out = f'../data/centurylink_addresses/{city}_{state}.json.gz'
        os.makedirs(os.path.dirname(fn_out), exist_ok=True)
        print(f"{city} time baby")

        # get inputs
        geojson = read_ndjson(fn)
        
        input_addresses = [
            {**record, **{"raw_address": format_full_address(record, city=city, state=state)}}  for record in geojson]
        print(f"all addresses: {len(input_addresses)}")
        output_addresses = []
        done = []
        if os.path.exists(fn_out):
            output_addresses.extend(read_ndjson(fn_out))
            done = [_.get('raw_address') for _ in output_addresses]
            print(f"collected addresses: {len(done)} {done[:2]}")
            
        # what's left to do? remove extra spaces and dupes.
        print("ok..........")
        done = set(done)
        todo = [a for a in input_addresses if a.get('raw_address') not in done]
        random.shuffle(todo)
        print(len(input_addresses), len(todo))
        unique_inputs = len(set([_['raw_address'] for _ in input_addresses]))
        del done
        
        # did we collect enough?
        if len(output_addresses) / len(input_addresses) >= percent_addresses_ok: 
            print("nah, we gucci")
            continue
        
        session = Session(AUTH_URL)        
        proxy = Proxy()
        async with aiohttp.ClientSession(timeout=timeout) as client_session:
            tasks = [
                http_client(record=record,
                            session=session,
                            proxy=proxy,
                            client_session=client_session) for record in todo[:request_limit]
            ]
            for future in tqdm.asyncio.tqdm.as_completed(tasks):
                payload = await future
                if payload:
                    output_addresses.append(payload)
                    
        print(f"verified {len(output_addresses)} addresses")
        dump_ndjson(fn_out, output_addresses)

    return True       
            

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    start = time.time()
    result = loop.run_until_complete(
        run_experiment(request_limit=request_limit, n_threads=n_threads)
    )
    end = time.time()
    print(f"Time: {end - start}")