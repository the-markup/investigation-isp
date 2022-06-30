"""
Geocoding Census Designated Places

This script converts coordinates into Census designated places that are incorporated
"""

import json
import gzip
import requests
import random
import time
import sys
import glob
import os
from multiprocessing import Pool

import numpy as np
import tqdm.asyncio
import aiohttp
import asyncio

from utils import read_ndjson
# from config import cities

n_threads = 30
N_JOBS = 6

output_dir = '../data/outputs/'
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
            if isinstance(address.get('geography_places'), dict):
                return address  
#             if isinstance(address['geography'].get('places'), dict):
#                 address['geography_places'] = address['geography'].get('places').get('geography')
#                 return address
                
            lat, lon = address['geometry']['coordinates']
            
            url = ("https://geocoding.geo.census.gov/geocoder/geographies/"
                   f"coordinates?x={lat}&y={lon}&benchmark=4&vintage={vintage}&format=json")
            place = None
            for n in range(3):
                try:
                    async with client_session.request("GET", url=url, **kwargs) as response:
                        if response.status == 200:
                            data = await response.json()
                            try:
                                data['result']
                                place = data['result']['geographies']
                                break
                            except Exception as e:
                                print(e)
                                await asyncio.sleep(5)
                                continue

                        # wait and make the request again
                        elif response.status in [429, 502, 503, 504]:
                            print(f"Rate limited: {address} code: {response.status}")
                            await asyncio.sleep(15)
                            continue
                except Exception as e:
                    print(e)
                    await asyncio.sleep(10)

            address['geography_places'] = place
            return address
            
    return get_census_block_group

async def run_experiment(files, n_threads=n_threads):
    http_client = chunked_http_client(n_threads)
    timeout = aiohttp.ClientTimeout(total=120)
    for fn in tqdm.tqdm(files):
        fn_out = fn.replace('/data/outputs_v3/', '/data/outputs_v4/').replace('/data/outputs/', '/data/outputs_v4/')
#         fn_out = fn.replace('_geocoded.json.gz', '_geocoded_v2.json.gz')
        if os.path.exists(fn_out): 
            print("We gucci")
            continue
        os.makedirs(os.path.dirname(fn_out), exist_ok=True)
        
        addresses = read_ndjson(fn)
                    
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

def async_loop(files):
    loop = asyncio.get_event_loop()
    start = time.time()
    result = loop.run_until_complete(
        run_experiment(n_threads=n_threads, files=files)
    )
    end = time.time()
    print(f"Time: {end - start}")
    
if __name__ == "__main__":
    files = glob.glob('/home/chino/code/markup/isp/data/outputs_v3/earthlink/*/*.geojson.gz')
#     files.extend(glob.glob('/home/chino/code/markup/isp/data/outputs/att/jackson/*.geojson.gz'))
#     files.extend(glob.glob('/home/chino/code/markup/isp/data/outputs/verizon/wilmington/*.geojson.gz'))
    random.shuffle(files)
#     files = ["../data/inputs/earthlink/remaining_records_remainder_geocoded.json.gz"]
    print(f"files to process {len(files)}")
    list_of_inputs = []
    for output in np.array_split(np.array(files), N_JOBS):
        list_of_inputs.append(output)
    with Pool(processes=N_JOBS) as pool:
        for record in pool.imap_unordered(async_loop, list_of_inputs):
            pass