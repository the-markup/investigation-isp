"""
ASYNC EarthLink price and speed
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
import signal

import numpy as np
import pandas as pd
import tqdm.asyncio
import aiohttp
import asyncio
from aiocfscrape import CloudflareScraper
from aiohttp import ClientHttpProxyError, ClientResponseError
from aiohttp.web import HTTPException
from multiprocessing import Pool

from utils import Proxy, read_ndjson, dump_ndjson


# params to change
VERBOSE = False
STATUS = True # set True for tqdm status bar. Note: confusing when using multiprocessing N_JOBS > 1)
N_THREADS = 8
REQUEST_LIMIT = 10000000
N_JOBS = 4
DIR_NAME = '/home/chino/code/markup/isp'
LANDING_PAGE = ["449ce933-8d27-4c69-a876-fe5a8e87171b"] # change this dail


# don't change these.
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:81.0) Gecko/20100101 Firefox/81.0',
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:98.0) Gecko/20100101 Firefox/98.0",
]


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:98.0) Gecko/20100101 Firefox/98.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/json;charset=utf-8",
    "Origin": "https://checkout.earthlink.net",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": "https://checkout.earthlink.net/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

AUTH_URL = "https://api.earthlink.com/affiliate/sessions/landing-pages"
OFFERS_URL = 'https://checkout.earthlink.net/serviceability/prequal'

def handler(signum, frame):
    print("Times up! Exiting...")
    sys.exit(0)
signal.signal(signal.SIGALRM, handler)
# signal.alarm(60 * 60 * 2)

class Session:
    def __init__(self, session, proxy):
        self.session = session
        self.proxy = proxy

    async def get(self, retries=2, verify=None, *args, **kwargs):
        for n in range(retries):
            async with self.session.request("GET", proxy=self.proxy.get_proxy(), headers=HEADERS,
                                            *args **kwargs) as response:
                if response.status == 200:
                    data = await response.json()
                    if verify: 
                        try:
                            data[verify]
                            break
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
        for n in range(1, retries+1):
            HEADERS['User-Agent'] = random.choice(USER_AGENTS)
            async with self.session.request("POST", proxy=self.proxy.get_proxy(), headers=HEADERS,
                                            *args, **kwargs) as response:
                if response.status == 200:
                    await asyncio.sleep(0)
                    data = await response.json()
                    if verify: 
                        try:
                            data[verify]
                            break
                        except:
                            continue
                    break

                else:
                    data = {"error_status": response.status, "error_body": await response.text()}
                    if response.status == 429:
                        wait = int(response.headers['Retry-After'])
                        if (random.random() >= .66) or (n == 2):
                            print(f"Rate limited {n} {wait}")
                            await asyncio.sleep(wait)
                        else:
                            print("Rate limited, trying again in 30")
                            await asyncio.sleep(random.uniform(18, 32))
                            self.proxy.generate_proxy()
                        continue
                        
                    if response.status in [500, 502, 503, 504]:
                        print(f'error {response.status}')
                        await asyncio.sleep(random.uniform(.4, 2.2) * min(n, 1))
                        continue
        return data
    
    async def get_offers(self, full_address):
#         if int(time.time()) - self.last_auth >= 60:
#             await self.authorize()
        json_data = {
            "address": full_address,
            "affiliateID": "ELNKWWW",
#             "promoCode": self.promocode,
            "partner": "elnkwww",
            "keyFlags": "extended_output"
        }

        response = await self.post(url=OFFERS_URL, json=json_data, verify='products')
        return response


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
            start = int(time.time())
            status = 0
            proxy = Proxy(refresh_in=10)
            session = Session(session=client_session, proxy=proxy)

            full_address = record['address_full']
            if VERBOSE:
                print(f"Getting offers for {full_address}")
            trial_and_tribulations = {}
            for n in range(2):
                try:
#                     await session.authorize()                    
                    await asyncio.sleep(random.uniform(2, 30))
                    offers = await session.get_offers(full_address = full_address)
                    if not offers.get('error_status'):
                        record['offers_earthlink'] = offers
                        status = 200
                        break
                    else:
                        print(offers)

                except (asyncio.exceptions.TimeoutError, aiohttp.ServerDisconnectedError) as e:
                    print("Server issue")
                    await asyncio.sleep(random.uniform(.3, 1))
                    session.proxy.generate_proxy()
                    
                except (aiohttp.ClientProxyConnectionError, aiohttp.ClientHttpProxyError) as e:
                    print("Proxy issue")
                    await asyncio.sleep(random.uniform(.6, 1))
                    session.proxy.generate_proxy()
                    break

                except Exception as e:
                    print(f"Exception for {full_address} {e}")
                    await asyncio.sleep(random.uniform(.2, 1.4))
                    session.proxy.generate_proxy()

            record['collection_status'] = status
            record['collection_api_calls'] = trial_and_tribulations
            record['collection_datetime'] = int(time.time())
            scraping_duration = int(time.time()) - start
            to_sleep = ((2.5 * 60) - scraping_duration) * random.uniform(-1.05, 1.05)
            to_sleep = min(0, to_sleep)
            await asyncio.sleep(to_sleep)
            return record

    return async_get_offers


async def el_scraper(files, request_limit=100, n_threads=10):
    """
    A job that opens a list of input files for each census block group.
    The addresses in the census block group are sent through the ATT lookup tool asyncronusly
    until successfully capturing 10 percent of addresses in a block group.
    """
    http_client = chunked_http_client(n_threads)
    timeout = aiohttp.ClientTimeout(total=60 * 2)
    connector = aiohttp.TCPConnector(limit=30)

    collected = 0
    async with CloudflareScraper(timeout=timeout, connector=connector) as client_session:
        for fn in files:
            if collected < request_limit:
                start = int(time.time())
                fn_out = fn.replace('/inputs/', '/outputs/')
                if os.path.exists(fn_out):
                    continue
                os.makedirs(os.path.dirname(fn_out), exist_ok=True)                
                    
                print(f"working on {fn}")
                todo = read_ndjson(fn)
                quota = int(len(todo) * 0.1)
                if quota < 10:
                    quota = len(todo)
                quota = min(47, quota)
                
                await asyncio.sleep(random.uniform(.1, .4))
                output_addresses = []
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
                    todo_ = todo[quota + 3 : quota + difference + 5]
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
            duration = int(time.time()) - start
            print(f"verified {successful} addresses from {len(output_addresses)} for {fn_out} in {duration} seconds")
            collected += 1        
    return True       
            
    
def async_loop(files):
    loop = asyncio.get_event_loop()
    start = time.time()
    result = loop.run_until_complete(
        el_scraper(files, request_limit=REQUEST_LIMIT, n_threads=N_THREADS)
    )
    end = time.time()
    print(f"Time: {end - start}")
    return True
    
if __name__ == "__main__":
    inputs = list(range(0, N_JOBS))
    files_to_parse = glob.glob(f'{DIR_NAME}/data/inputs/earthlink/*/*.geojson.gz')
    random.shuffle(files_to_parse)
    print(f"files to process {len(files_to_parse)}")
    list_of_inputs = []
    for output in np.array_split(np.array(files_to_parse), N_JOBS):
        list_of_inputs.append(output)
    with Pool(processes=N_JOBS) as pool:
        for record in pool.imap_unordered(async_loop, list_of_inputs):
            pass