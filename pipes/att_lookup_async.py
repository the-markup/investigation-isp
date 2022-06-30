"""
ASYNC ATT price and speed
This code uses multiprocessing to create `n_files_open` (usually 10) jobs.
Each job operates off of a unique input file.
The input file contains filepaths of addresses for census block groups.
Each census block group's addresses are sent through a workflow resembling using an address lookup tool
to collect speed and price data. 
This happens ascyronously with `n_threads` (usually 10-50) addresses being scraped at the same time.

Note: input and ouput files should be in the `../data/` folder for this script to work.
In the future this will use absolute paths or s3.
"""
import os
import json
import gzip
import requests
import random
import time
import sys
import glob
from multiprocessing import Pool

import numpy as np
import pandas as pd
import tqdm.asyncio
import aiohttp
import asyncio
from aiohttp import ClientHttpProxyError, ClientResponseError
from aiohttp.web import HTTPException

from utils import Proxy, read_ndjson, dump_ndjson

DIR_NAME = '/home/chino/code/markup/isp'
VERBOSE = False
STATUS = True # set True for tqdm status bar. Note: confusing when using multiprocessing (n_files_open > 1)
N_THREADS = 10
REQUEST_LIMIT = 1000000
N_JOBS= 10

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:98.0) Gecko/20100101 Firefox/98.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Origin": "https://www.att.com",
    "DNT": "1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


async def auth(session, proxy):
    async with session.request("GET", 
                               url="https://www.att.com/msapi/id",
                               proxy=proxy.get_proxy()) as response:
        if response.status == 200:
            try:
                data = await response.text()
                return data
            except Exception as e:
                text = await response.text()
                print(f"Authentication failure. {e} {text}")
                proxy.generate_proxy()
                raise
        elif response.status in [428, 429, 500, 502, 503, 504]:
            await asyncio.sleep(1)
        return None

async def check_address(session, proxy, street_address=None, zipcode=None, unit=False, retries=2, address_id=None):
    if address_id:
        json_data = {
            "lobs": ["broadband"],
            "addressId": address_id,
            "mode": "addressId",
            "customerType": "consumer"
        }
    else:
        json_data = {
            "lobs": ["broadband"],
            "addressLine1": street_address.upper(),
            "city": "",
            "state": "",
            "mode": "fullAddress",
            "zip": str(zipcode),
            "unitType1": "",
            "customerType": "consumer",
        }
    
    if unit:
        json_data['AddressLine2'] = unit
    
    headers = {
      **HEADERS,
      **{"referer": "https://www.att.com/buy/bundles/dtvstream/plans"},
    }
    for n in range(retries):
        async with session.request("POST", 
                                   url= "https://www.att.com/msapi/onlinesalesorchestration/att-wireline-sales-eapi/v1/baseoffers",
                                   headers=headers,
                                   json=json_data,
                                   proxy=proxy.get_proxy()) as response:
            if response.status == 200:
                data = await response.json()
                try:
                    data["content"]
                except:
                    continue
                # check the format looks right
                break
                
            else:
                data = {"error_status": response.status, "error_body": await response.text()}
                print(f"check_address {street_address} {data}")
                if response.status == 428:
                    raise Exception("Capcha'd")
                if response.status in [429, 500, 502, 503, 504]:
                    await asyncio.sleep(random.uniform(.2, 1.2) * min(n, 1))
                    proxy.generate_proxy()
                    continue
                    
                await asyncio.sleep(random.uniform(.1, .4))
    return data


async def get_offers(session, proxy, address_id, street_address, zipcode, retries=2):
    json_data = {
        "lobs": [
            "broadband"
        ],
        "addressId": address_id,
        "addressLine1": street_address,
        "addressLine2": "",
        "mode": "addressId",
        "city": "",
        "state": "",
        "zip": zipcode,
        "customerType": "consumer",
        "relocation_flag": True
    }

    for n in range(retries):
        async with session.request("POST", 
                                   url="https://www.att.com/msapi/onlinesalesorchestration/att-wireline-sales-eapi/v1/baseoffers",
                                   headers=HEADERS,
                                   json=json_data,
                                   proxy=proxy.get_proxy()) as response:
            if response.status == 200:
                data = await response.json()
                try:
                    data['content']
                except:
                    continue
                
                break
            
            else:
                data = {"error_status": response.status, "error_body": await response.text()}
                print(f"get_offers {street_address} {data}")
                if response.status == 428:
                    raise Exception("Capcha'd")
                if response.status in [429, 500, 502, 503, 504]:
                    await asyncio.sleep(random.uniform(1, 1.2) * min(n, 1))
                    proxy.generate_proxy()
                    continue
                
                await asyncio.sleep(random.uniform(.1, .4))
    return data

            
def chunked_http_client(n_threads):
    """
    API-version of looking up one addresses in the ATT lookup tool.
    """
    semaphore = asyncio.Semaphore(n_threads)
    async def async_get_offers(record, client_session, *args, **kwargs):
        nonlocal semaphore
        async with semaphore:
            if client_session.closed:
                sys.exit(1)
            connector = aiohttp.TCPConnector(limit=5)
            async with aiohttp.ClientSession(connector=connector) as session:
                proxy = Proxy()
                status = 0
                street_address = record['address_streetline']
                zipcode = record['address_zipcode']
                trial_and_tribulations = {}
                for n in range(2):
                    try:
                        await auth(session, proxy)
                        await asyncio.sleep(random.uniform(.2, .5))
                        resp = await check_address(session=session, proxy=proxy, street_address=street_address, zipcode=zipcode)
                        availability_status =  resp.get('content', {}).get('serviceAvailability', {}).get('availabilityStatus')
                        address_id = resp["content"]["serviceAvailability"]["addressFeatures"].get("addressId")

                        if availability_status == 'CLOSEMATCH':
                            if VERBOSE:
                                print(f"close match at {street_address} {zipcode}")
                            trial_and_tribulations['closematch'] = True
                            matches = resp['content']['serviceAvailability']['closeMatchAddress']
                            if matches:
                                await asyncio.sleep(random.uniform(.1, .5))
                                address_id = matches[0]['addressId']
                                resp = await check_address(session=session, proxy=proxy, address_id=address_id)
                                availability_status = resp.get('content', {}).get('serviceAvailability', {}).get('availabilityStatus')
                                if VERBOSE:
                                    print(f"New status for {street_address} is {availability_status}")
                                address_id = resp["content"]["serviceAvailability"]["addressFeatures"]["addressId"]
                        
                        if availability_status == 'MDU':
                            if VERBOSE:
                                print(f"MUD at {street_address}")
                            trial_and_tribulations['mdu'] = True
                            units = resp['content']['serviceAvailability']['mduAddress']
                            units = [u for u in units if u.get('addressLine2') != ""]
                            if not units:
                                units = resp['content']['serviceAvailability']['mduAddress']
                            for unit in units:
                                unit_number = unit['addressLine2']
                                address_id = unit['addressId']
                                if VERBOSE:
                                    print(f"new address {street_address} {unit} {address_id} {zipcode}")
                                await asyncio.sleep(random.uniform(.2, .5))
                                resp = await check_address(session=session, proxy=proxy, address_id=address_id)
                                availability_status = resp.get('content', {}).get('serviceAvailability', {}).get('availabilityStatus')
                                if VERBOSE:
                                    print(f"New status for {street_address} is {availability_status}")
                                if availability_status != 'MDU':
                                    address_id = resp["content"]["serviceAvailability"]["addressFeatures"]["addressId"]
                                    break
                                    
                        if availability_status == 'CLOSEMATCH':
                            if VERBOSE:
                                print(f"close match at {street_address} {zipcode}")
                            trial_and_tribulations['closematch'] = True
                            matches = resp['content']['serviceAvailability']['closeMatchAddress']
                            if matches:
                                await asyncio.sleep(random.uniform(.2, .5))
                                address_id = matches[0]['addressId']
                                resp = await check_address(session=session, proxy=proxy, address_id=address_id)
                                availability_status = resp.get('content', {}).get('serviceAvailability', {}).get('availabilityStatus')
                                address_id = resp["content"]["serviceAvailability"]["addressFeatures"]["addressId"]
                                
                        if availability_status in ['EXISTINGSERVICES', 'GREEN']:
                            has_internet = resp['content']['serviceAvailability']['availableServices']
                            if has_internet.get('hsiaAvailable'):
                                await asyncio.sleep(random.uniform(.2, .5))
                                offers = await get_offers(session=session, proxy=proxy, 
                                                          address_id=address_id, 
                                                          street_address=street_address, 
                                                          zipcode=zipcode)
                                record['offer_att'] = offers
                                if not offers.get('error_status'):
                                    status = 200
                            else:
                                if VERBOSE:
                                    print("no service")
                                record['offer_att']= {}
                                status = 200
                        elif availability_status == "CONNECTEDCOMMUNITY":
                            status = 200
                            record["offer_att"] = {}
                        elif availability_status == 'RED':
                            status = 400
                            offers = await get_offers(session=session, proxy=proxy, 
                                                      address_id=address_id, 
                                                      street_address=street_address, 
                                                      zipcode=zipcode)
                            record['offer_att'] = offers
                        else:
                            print(f"{street_address} with status {availability_status} after {trial_and_tribulations}")

                        record['availability_att'] = resp
                        record['availability_status'] = availability_status
                        break

                    except (aiohttp.ClientProxyConnectionError, aiohttp.ClientHttpProxyError) as e:
                        print("Proxy issue")
                        await asyncio.sleep(2)
                        proxy.generate_proxy()

                    except Exception as e:
                            print(f"Exception for {street_address} {e}")
                            await asyncio.sleep(1)
                    
                record['collection_status'] = status
                record['collection_api_calls'] = trial_and_tribulations
                record['collection_datetime'] = int(time.time())
                
                return record
        
    return async_get_offers


async def att_scraper(files, request_limit=100, n_threads=10):
    """
    A job that opens a list of input files for each census block group.
    The addresses in the census block group are sent through the ATT lookup tool asyncronusly
    until successfully capturing 10 percent of addresses in a block group.
    """
    http_client = chunked_http_client(n_threads)
    timeout = aiohttp.ClientTimeout(total=60 * 2)
    collected = 0
    for fn in files:
        if collected < request_limit:
            fn_out = fn.replace('/input/', '/output/')
            if os.path.exists(fn_out):
                continue
            os.makedirs(os.path.dirname(fn_out), exist_ok=True)
            print(f"working on {fn}")
            todo = read_ndjson(fn)
            quota = int(len(todo) * 0.1)
            if quota < 10:
                quota = len(todo)
            
            output_addresses = []
            async with aiohttp.ClientSession(timeout=timeout) as client_session:
                todo_ = todo[:quota + 3]
                tasks = [http_client(record=record, client_session=client_session) for record in todo_]
                completed = tqdm.asyncio.tqdm.as_completed(tasks) if STATUS else asyncio.as_completed(tasks)
                for future in completed:
                    payload = await future
                    if payload:
                        output_addresses.append(payload)
                successful = len([_ for _ in output_addresses if _['collection_status'] in [200, 400]])
                if successful < quota:
                    # collect more data if we didn't hit the quota...
                    difference = quota - successful
                    todo_ = todo[quota + 3 : quota + difference + 8]
                    tasks = [http_client(record=record, client_session=client_session) for record in todo_]
                    completed = tqdm.asyncio.tqdm.as_completed(tasks) if STATUS else asyncio.as_completed(tasks)
                    for future in completed:
                        payload = await future
                        if payload: 
                            output_addresses.append(payload)
                    successful = len([_ for _ in output_addresses if _['collection_status'] in [200, 400]])

            # save 10 percent sample worth of hits.
            output = []
            hits = 0
            for row in output_addresses:
                if hits == quota:
                    break
                output.append(row)
                if row['collection_status'] in [200, 400]:
                    hits += 1
            if hits < quota * .9:
                print(f"failed to hit quota for {fn_out}")
                continue
            dump_ndjson(fn_out, output)
            print(f"verified {successful} addresses from {len(output_addresses)} for {fn_out}")
            collected += 1        
    return True       
            
    
def async_loop(files):
    loop = asyncio.get_event_loop()
    start = time.time()
    result = loop.run_until_complete(
        att_scraper(files, request_limit=REQUEST_LIMIT, n_threads=N_THREADS)
    )
    end = time.time()
    print(f"Time: {end - start}")
    return True
    
if __name__ == "__main__":
    files_to_parse = glob.glob(f'{DIR_NAME}/data/input/isp/att/*/*.geojson.gz')
    random.shuffle(files_to_parse)
    
    list_of_inputs = []
    for output in np.array_split(np.array(files_to_parse), N_JOBS):
        list_of_inputs.append(output)
    
    with Pool(processes=N_JOBS) as pool:
        for record in pool.imap_unordered(async_loop, list_of_inputs):
            pass