"""
ASYNC CenturyLink price and speed
This code uses multiprocessing to create `N_JOBS` (usually 10) jobs.
Each job operates off of a unique input file.
The input file contains filepaths of addresses for census block groups.
Each census block group's addresses are sent through a workflow resembling using an address lookup tool
to collect speed and price data. 
This happens ascyronously with `N_THREADS` (usually 10-50) addresses being scraped at the same time.

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

import numpy as np
import pandas as pd
import tqdm.asyncio
import aiohttp
import asyncio
from async_retrying import retry
from aiohttp import ClientHttpProxyError, ClientResponseError
from aiohttp.web import HTTPException
from multiprocessing import Pool

from utils import Proxy, read_ndjson, dump_ndjson

# params to change
VERBOSE = False
STATUS = True # set True for tqdm status bar. Note: confusing when using multiprocessing (n_files_open > 1)
N_THREADS = 9
REQUEST_LIMIT = 10000000
N_JOBS = 11
DIR_NAME = '/home/chino/code/markup/isp/'

# don't change these.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:81.0) Gecko/20100101 Firefox/81.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Access-Control-Request-Method': 'GET',
    'Access-Control-Request-Headers': 'access-control-allow-origin,authorization,contenttype,withcredentials,x-b3-spanid,x-b3-traceid',
    'Referer': 'https://shop.centurylink.com/',
    'Origin': 'https://shop.centurylink.com',
    'DNT': '1',
    'Connection': 'keep-alive',
}

AUTH_URL = "https://shop.centurylink.com/uas/oauth"
ADDR_PREDICT_URL = "https://api.lumen.com/Application/v4/DCEP-Consumer/addressPredict"
ADDR_PICK = "https://api.lumen.com/Application/v4/DCEP-Consumer/preference"
ADDR_VERIFY_URL = "https://api.lumen.com/Application/v4/DCEP-Consumer/identifyAddress"
ORDER_URL = "https://api.lumen.com/Application/v4/DCEP-Consumer/getOrderRefNbr"
OFFERS_URL = "https://api.centurylink.com/Application/v4/DCEP-Consumer/offer"


class Session:
    def __init__(self, session, proxy):
        self.session = session
        self.proxy = proxy
        
    async def authorize(self, retries=2):
        for n in range(retries):
            async with self.session.request("GET", 
                                            url=AUTH_URL,
                                            headers=HEADERS,
                                            proxy=self.proxy.get_proxy()) as response:
                if response.status == 200:
                    self.authorization = await response.json()
                    break
                    
                else:
                    data = {"error_status": response.status, "error_body": await response.text()}
                    if response.status in [429, 500, 502, 503, 504]:
                        await asyncio.sleep(random.uniform(.2, 1.2) * min(n, 1))
                        self.proxy.generate_proxy()
                        continue
                        
                    await asyncio.sleep(random.uniform(.2, 1.2))
        return
                
    async def headers(self):
        try:
            a = self.authorization
        except:
            await self.authorize()
            a = self.authorization
            
        now = int(time.time())
        if int(a["issued_at"]) + int(a["expires_in"]) - now < 30:
            await self.authorize()
        return {
            **HEADERS,
            **{"Authorization": f"Bearer {self.authorization['access_token']}"},
        }

    async def get(self, retries=2, verify=None, *args, **kwargs):
        for n in range(retries):
            async with self.session.request("GET", proxy=self.proxy.get_proxy(),
                                            *args, **{**kwargs, **{"headers": await self.headers()}}) as response:
                if response.status == 200:
                    data = await response.json()
                    if verify: 
                        try:
                            data[verify]
                        except:
                            continue
                    break

                else:
                    data = {"error_status": response.status, "error_body": await response.text()}
                    if response.status in [429, 500, 502, 503, 504]:
                        await asyncio.sleep(random.uniform(.2, 1.2) * min(n, 1))
                        self.proxy.generate_proxy()
                        continue

                    await asyncio.sleep(random.uniform(.1, .4))
        return data

    async def post(self, retries=2, verify=None, *args, **kwargs):
        for n in range(retries):
            async with self.session.request("POST", proxy=self.proxy.get_proxy(),
                                            *args, **{**kwargs, **{"headers": await self.headers()}}) as response:
                if response.status == 200:
                    data = await response.json()
                    if verify: 
                        try:
                            data[verify]
                        except:
                            continue
                    break

                else:
                    data = {"error_status": response.status, "error_body": await response.text()}
                    if response.status in [429, 500, 502, 503, 504]:
                        await asyncio.sleep(random.uniform(.2, 1.2) * min(n, 1))
                        self.proxy.generate_proxy()
                        continue

                    await asyncio.sleep(random.uniform(.1, .4))

        return data


def chunked_http_client(n_threads):
    """
    API-version of looking up one addresses in the CL lookup tool.
    """
    semaphore = asyncio.Semaphore(n_threads)
    async def async_get_offers(record, client_session, *args, **kwargs):
        nonlocal semaphore
        async with semaphore:
            if client_session.closed:
                sys.exit(1)
            async with aiohttp.ClientSession() as session:
                proxy = Proxy()
                session = Session(session, proxy)
                await session.authorize()
                status = 0
                street_address = record['address_full']
                trial_and_tribulations = {}
                for n in range(2):
                    try:
                        # Check addresses
                        addresses = await session.get(
                            url=ADDR_PREDICT_URL,
                            params={"addr": street_address}
                        )
                        matches = addresses.get("predictedAddressList")
                        if matches:
                            top_address = addresses["predictedAddressList"][0]
                            address_id = top_address["addressId"]
                            street_address =top_address["fullAddress"]

                            # create order number
                            order = await session.get(url=ORDER_URL, verify='nbr')

                            # verify address before lookup
                            json_data = {
                                "addressId": address_id,
                                "fullAddress": street_address,
                                "provider": addresses["provider"],
                                "orderRefNum": order["nbr"],
                            }
                            addr_verify = await session.post(url=ADDR_VERIFY_URL, 
                                                             json=json_data, 
                                                             verify='message')
                            if VERBOSE:
                                print("address verification" + json.dumps(addr_verify))
                            availability_status = addr_verify['message']

                            if availability_status == "Out Of Region":
                                status = 400

                            is_mdu = availability_status == 'YELLOW - MDU matches'                    
                            if is_mdu:
                                if VERBOSE:
                                    print("is_mdu")
                                trial_and_tribulations["is_mdu"] = True
                                units = addr_verify['addrValInfo']['mduInfo']['mduList']
                                if units:
                                    first_unit = units[0]
                                    geosec = first_unit["geoSecUnitId"]
                                    unit_number = first_unit.get("unitNumber")
                                    if not unit_number:
                                        unit_number = first_unit["unitDescription"]
                                    json_data = {
                                        **json_data, **{
                                            "mdu": True,
                                            "geoSecUnitId": geosec,
                                            "unitNumber": unit_number
                                        }
                                    }
                                    if VERBOSE:
                                        print(json_data)
                                    addr_verify = await session.post(url=ADDR_VERIFY_URL, 
                                                                     json=json_data,
                                                                     verify='message')
                                    if VERBOSE:
                                        print("address verificartion 2" + json.dumps(addr_verify))
                                    availability_status = addr_verify['message']

                            # get offfers
                            if  availability_status == "GREEN - exact match":
                                if VERBOSE:
                                    print("matched")
                                json_data = {
                                    "orderRefNum": order["nbr"],
                                    "addressId": address_id,
                                    "fullAddress": street_address,
                                    "wireCenter": addr_verify["addrValInfo"]["wireCenter"],
                                    "billingSource": addr_verify["addrValInfo"]["billingSource"],
                                }
                                if is_mdu:
                                    json_data = {
                                        **json_data, **{
                                            "geoSecUnitId": geosec,
                                            "unitNumber": unit_number
                                        }
                                    }
                                if VERBOSE:
                                    print(json.dumps(json_data))
                                offers = await session.post(url=OFFERS_URL,
                                                            json=json_data)
                                if VERBOSE:
                                    print("offers" + json.dumps(offers))
                                if not offers.get('error_status'):
                                    status = 200
                                    record['offer_centurylink'] = offers
                            else:
                                status = 400
                                record['offer_centurylink'] = {}

                            record['availability_centurylink'] = addr_verify
                            record['availability_status'] = availability_status
                            break

                    except (aiohttp.ClientProxyConnectionError, aiohttp.ClientHttpProxyError, asyncio.exceptions.TimeoutError) as e:
                        print("Proxy issue")
                        await asyncio.sleep(2)
                        proxy.generate_proxy()

                    except Exception as e:
                        print(f"Exception for {street_address} {e}")
                        await asyncio.sleep(1)
                        proxy.generate_proxy()
                    
                record['collection_status'] = status
                record['collection_api_calls'] = trial_and_tribulations
                record['collection_datetime'] = int(time.time())
                
                return record
        
    return async_get_offers


async def cl_scraper(files, request_limit=100, n_threads=10):
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
            fn_out = fn.replace('/inputs/', '/outputs/')
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
        cl_scraper(files, request_limit=REQUEST_LIMIT, n_threads=N_THREADS)
    )
    end = time.time()
    print(f"Time: {end - start}")
    return True
    
if __name__ == "__main__":
    inputs = list(range(0, N_JOBS))
    files_to_parse = glob.glob(f'{DIR_NAME}/data/inputs/centurylink/*/*.geojson.gz')
    random.shuffle(files_to_parse)
    print(f"files to process {len(files_to_parse)}")
    list_of_inputs = []
    for output in np.array_split(np.array(files_to_parse), N_JOBS):
        list_of_inputs.append(output)
    with Pool(processes=N_JOBS) as pool:
        for record in pool.imap_unordered(async_loop, list_of_inputs):
            pass