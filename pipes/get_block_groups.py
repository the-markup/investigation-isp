"""
Geocoding

This script converts coordinates into census block groups.
"""

import json
import gzip
import requests
import random
import time
import sys
import glob
import os

import tqdm.asyncio
import aiohttp
import asyncio

# from config import cities

n_threads = 400

output_dir = '../data/open_addresses_enriched/'
os.makedirs(output_dir, exist_ok=True)

def chunked_http_client(n_threads):
    """
    Returns a function that can fetch from a URL, ensuring that only
    "num_chunks" of simultaneous connects are made.
    """
    semaphore = asyncio.Semaphore(n_threads)
    
    async def get_census_block_group(address, client_session, vintage=419, *args, **kwargs):
        nonlocal semaphore
        async with semaphore:
            if client_session.closed:
                sys.exit(1)
                
            lon, lat = address['geometry']['coordinates']
            url = ('https://geocoding.geo.census.gov/geocoder/geographies/'
                   f'coordinates?x={lon}&y={lat}&benchmark=4&vintage={vintage}&layers=10&format=json')

            async with client_session.request("GET", url=url, **kwargs) as response:
                if response.status == 200:
                    data = await response.json()
                    address['geography'] = data.get('result')

                # wait and make the request again
                elif response.status in [429, 502, 503, 504]:
                    print(f"Rate limited: {address} code: {response.status}")
                    await asyncio.sleep(3)

                await asyncio.sleep(.02)
                return address
            
    return get_census_block_group

async def run_experiment(n_threads=n_threads):
    http_client = chunked_http_client(n_threads)
    timeout = aiohttp.ClientTimeout(total=60)
#     files = glob.glob('../data/open_addresses/*.json.gz')
    cities = []
    with open('../data/cities.ndjson', 'r') as f:
        for line in f:
            cities.append(json.loads(line))
    files = [_['fn'] for _ in cities]
    for fn in files:
        print(fn)
        fn_out = fn.replace('../data/open_addresses/', output_dir)
        if os.path.exists(fn_out): 
            print("We gucci")
            continue
            
        addresses = []
        n_records = 0
        with gzip.open(fn, 'rb') as f:
            for line in f.readlines():
                n_records += 1
                record = json.loads(line)
#                 address = ' '.join([record['number'], record['street']])
#                 first_record = suggestions[0]
#                 if first_record.get('propertyType') == 'R':
#                     record['address'] = first_record
                addresses.append(record)
                    
        print(f"Originally {n_records}, we gonna get {len(addresses)}")
        output_addresses = []
        async with aiohttp.ClientSession(timeout=timeout) as client_session:
            tasks = [
                http_client(address=address, client_session=client_session) 
                for address in addresses
            ]
            for future in tqdm.asyncio.tqdm.as_completed(tasks):
                payload = await future
                output_addresses.append(payload)
                
        with gzip.open(fn_out, 'wt') as f:
            for line in output_addresses:
                f.write(json.dumps(line) + '\n')
    return True

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    start = time.time()
    result = loop.run_until_complete(
        run_experiment(n_threads=n_threads)
    )
    end = time.time()
    print(f"Time: {end - start}")