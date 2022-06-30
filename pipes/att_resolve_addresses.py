"""
ATT Geocoding Scraper
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
from async_retrying import retry

from config import cities
from utils import Proxy, format_full_address, read_ndjson, dump_ndjson

n_threads = 20
request_limit = 10000000
percent_addresses_ok = .7
    
def chunked_http_client(n_threads):
    """
    Returns a function that can fetch from a URL, ensuring that only
    "num_chunks" of simultaneous connects are made.
    """
    semaphore = asyncio.Semaphore(n_threads)
    
    @retry(attempts=3)
    async def async_verify_address(record, proxy, city, client_session, *args, **kwargs):
        nonlocal semaphore
        async with semaphore:
            if client_session.closed:
                sys.exit(1)
            address = record['raw_address']
            address = ' '.join(address.split())

            headers = {
                'authority': 'us-autocomplete-pro.api.smartystreets.com',
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'en-US,en;q=0.9',
                'origin': 'https://www.att.com',
                'referer': 'https://www.att.com/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'cross-site',
            }
            params = {
                'search': address,
                'max_results': '10',
                'agent': 'smartystreets (sdk:javascript@1.4.2)',
                'auth-id': '2021202165494638221',  
            }
            for n in range(2):
                try:
                    async with client_session.request("GET", 
                                                      url='https://us-autocomplete-pro.api.smartystreets.com/lookup',
                                                      headers=headers, 
                                                      params=params,
                                                      proxy=proxy.get_proxy(new_ip=True), # new IP for every API call.
                                                      **kwargs) as response:
                        if response.status == 200:
                            data = await response.json()
                            suggestions = data.get('suggestions')
                            if suggestions:
                                record['address_suggestions'] = suggestions
                                await asyncio.sleep(.2)
                                return record

                        # wait and make the request again
                        elif response.status in [429, 502, 503, 504]:
                            print(f"Rate limited: {address} {response.status}")
                            await asyncio.sleep(15)
                except aiohttp.ClientProxyConnectionError as e:
                    print("Too many proxy connections")
                    await asyncio.sleep(2)
            return None
            
    return async_verify_address


async def run_experiment(request_limit=request_limit, n_threads=n_threads):
    http_client = chunked_http_client(n_threads)
    timeout = aiohttp.ClientTimeout(total=60)
    inputs = [_ for _ in cities if _.get('att') == True]
    for d in inputs:
        fn = d['fn'].replace('../data/open_addresses/', '../data/open_addresses_enriched/')
        city = d['city']
        state = d['state']
        if city != 'JACKSON':
            continue
        fn_out = f'../data/att_addresses/{city}_{state}.json.gz'
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
        print(len(todo) / len(input_addresses))
        unique_inputs = len(set([_['raw_address'] for _ in input_addresses]))
        del done
        
        # did we collect enough?
        if len(output_addresses) / len(input_addresses) >= percent_addresses_ok: 
            print("nah, we gucci")
            continue
        
        proxy = Proxy()
        async with aiohttp.ClientSession(timeout=timeout) as client_session:
            tasks = [
                http_client(record=record,
                            city=city,
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