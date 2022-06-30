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

from config import cities
from utils import (
    Proxy, 
    format_full_address, 
    read_ndjson, 
    dump_ndjson,
    street_to_number
)

n_threads = 100
request_limit = 10000000000
percent_addresses_ok = .7

def chunked_http_client(n_threads):
    """
    Returns a function that can fetch from a URL, ensuring that only
    "num_chunks" of simultaneous connects are made.
    """
    semaphore = asyncio.Semaphore(n_threads)
    
    async def async_verify_address(record, state, city, proxy, client_session, *args, **kwargs):
        nonlocal semaphore
        async with semaphore:
            if client_session.closed:
                sys.exit(1)
            address = record['raw_address']
            address = ' '.join(address.split())
        
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:81.0) Gecko/20100101 Firefox/81.0',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/json',
                'apikey': '5vbCkJw5g5e3LNaY8cgcnPpyQGPrhjIw',
                'Origin': 'https://www.verizon.com',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Referer': 'https://www.verizon.com/',
            }

            params = {
                'streetterm': address,
            }
            try:
                for n in range(2):
                    async with client_session.request("GET", 
                                                      url='https://api.verizon.com/locus-typeahead/address/typeahead-address',
                                                      headers=headers, 
                                                      params=params,
                                                      proxy=proxy.get_proxy(new_ip=False),
                                                      **kwargs) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('meta', {}).get('code') == '200.1':
                                suggestions = data.get('addresses')
                                if suggestions:
                                    record['address_suggestions'] = suggestions
                                    await asyncio.sleep(.2)
                                    return record
                            else:
                                proxy.generate_proxy()
        
                        # wait and make the request again
                        elif response.status in [429, 502, 503, 504]:
                            print(f"Rate limited: {address} code: {response.status}")
                            proxy.generate_proxy()
                            await asyncio.sleep(3)
                            
                        else:
                            print(await response.json())
                return None
                
            except aiohttp.ClientProxyConnectionError as e:
                print("Too many proxy connections")
                await asyncio.sleep(2)
            
            
    return async_verify_address


async def run_experiment(request_limit=request_limit, n_threads=n_threads):
    http_client = chunked_http_client(n_threads)
    timeout = aiohttp.ClientTimeout(total=60)
    inputs = [_ for _ in cities if _.get('verizon') == True]
    for d in inputs:
        fn = d['fn'].replace('../data/open_addresses/', '../data/open_addresses_enriched/')
        city = d['city']
        state = d['state']
        fn_out = f'../data/verizon_addresses/{city}_{state}.json.gz'
        os.makedirs(os.path.dirname(fn_out), exist_ok=True)
        print(f"{city} time baby")

        if city != 'WILMINGTON':
            continue
        
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
        print(len(input_addresses), len(todo))
        unique_inputs = len(set([_['raw_address'] for _ in input_addresses]))
        del done 
                
        # did we collect enough?
        if len(output_addresses) / len(input_addresses) >= percent_addresses_ok: 
            print("nah, we gucci")
            continue
            
        proxy = Proxy(refresh_in=5)
        async with aiohttp.ClientSession(timeout=timeout) as client_session:
            tasks = [
                http_client(record=record,
                            state=state,
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