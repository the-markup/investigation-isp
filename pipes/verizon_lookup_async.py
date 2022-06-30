"""
ASYNC verizon price and speed
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
from aiohttp import ClientHttpProxyError, ClientResponseError, ContentTypeError
from aiohttp.web import HTTPException
from pathos.multiprocessing import ProcessingPool as Pool

from utils import Proxy, read_ndjson, dump_ndjson

# params to change
VERBOSE = False
STATUS = True # set True for tqdm status bar. Note: confusing when using multiprocessing (n_files_open > 1)
N_THREADS = 6
REQUEST_LIMIT = 10000000
N_JOBS = 3
END_AFTER_N_MINS = 10

DIR_NAME = '/home/chino/code/markup/isp'
EORDER = "_e_=NESCGjan%2fsOuQBj6IilwPQ6qA%3d%3d" # change this manually daily
EORDER = "_e_=NESBvQJXNN1XVQDd%2bQ98QK30w%3d%3d" # change this manually daily
EORDER = "_e_=NESXC3jnovafcZQaS0eDGxNCA%3d%3d"

# don't change these.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
    'Origin': 'https://www.verizon.com',
    'DNT': '1',
}

AUTH_URL = 'https://www.verizon.com/inhome/generatetoken'
VISIT_URL = 'https://www.verizon.com/inhome/generatevisitid'
UNITS_URL = 'https://api.verizon.com/atomapi/v1/addresslookup/addresses/units'
ADDR_VERIFY_URL = "https://api.verizon.com/atomapi/v1/addressqualification/address/qualification"
ADDR_ID_URL = "https://api.verizon.com/atomapi/v1/addresslookup/addresses/streetbyzip"
FIOS_URL = 'https://api.verizon.com/atomapi/v1/qualifiedproducts/accordion/products/plans'
HSI_URL = 'https://www.verizon.com/foryourhome/ordering/Services/GetAllProducts'

def handler(signum, frame):
    print("Times up! Exiting...")
    sys.exit(0)

#Set alarm for 7 minutes
signal.signal(signal.SIGALRM, handler)
signal.alarm(60 * END_AFTER_N_MINS)


class Session:
    def __reduce__(self):
        return IntegrityList, (self.file_path,) 
    def __init__(self, session, proxy):
        self.session = session
        self.proxy = proxy
    
    async def register(self):
        await self.authorize()
        await self.get_visit_id()
    
    async def authorize(self, retries=2):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
            'Accept-Language' : 'en,en-US;q=0,5',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8"',
        }
        for n in range(retries):
            async with self.session.request("GET", 
                                            url=AUTH_URL,
                                            headers=headers,
                                            cookies={},
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
    
    async def get_visit_id(self):
        headers = {
            'Host': 'www.verizon.com',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-store',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'DNT': '1',
            'Referer': 'https://www.verizon.com/inhome/qualification?lid=//global//residential',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.visitor_ids = await self.get(url=VISIT_URL,
                                          headers=headers,
                                          verify='visit_id')
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
                            print(f"Can't find {verify} in {json.dumps(data, indent=2)}")
                            continue
                    break
                else:
                    data = {"error_status": response.status, "error_body": await response.text()}
                    if response.status in [429, 500, 502, 503, 504]:
                        await asyncio.sleep(random.uniform(.2, 1.2) * min(n, 1))
                        self.proxy.generate_proxy()
                        continue
                    await asyncio.sleep(random.uniform(.2, 1))
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
                            print(f"Can't find {verify} in {json.dumps(data, indent=2)}")
                            continue
                    break
                else:
                    data = {"error_status": response.status, "error_body": await response.text()}
                    if response.status in [429, 500, 502, 503, 504]:
                        await asyncio.sleep(random.uniform(.2, 1.2) * min(n, 1))
                        self.proxy.generate_proxy()
                        continue
                    await asyncio.sleep(random.uniform(.2, 1))

        return data
    
    async def get_address_id(self, street_address, zipcode):
        """
        Address ID is necessary to make API call.
        address_no_commas can look like: 149 MILBURN ST BUFFALO NY 14212
        """
        params = {
            'streetterm': street_address,
            'zip': zipcode,
        }
        response = await self.get(url=ADDR_ID_URL, params=params)
        return response
    
    async def check_address_units(self, address_id):
        """Check if the address has multiple units"""
        now = int(time.time())
        if self.visitor_ids['expirationTime'] - now < 30:
            await self.get_visit_id()
                
        cookies = {
            'visit_id': self.visitor_ids['visit_id'],
            'visitor_id': self.visitor_ids['visitor_id'],
            'token': self.authorization['access_token'],
            'gpv_p17': 'qualification',
            'zipcode': '0',
        }
        
        headers = {
            'Connection': 'keep-alive',
            'Gsm-Id': '',
            'Pragma': 'no-cache',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-store',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            'sec-ch-ua-platform': '"macOS"',
            'Origin': 'https://www.verizon.com',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://www.verizon.com/',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1',
        }
        
        params = {'baseAddressId': address_id}
        resp_unit = await self.get(url=UNITS_URL, params=params, cookies=cookies, verify='data')
        return resp_unit
    
    async def is_address_qualified(self, address_id, state, zipcode, city):
        """Check if the address is qualified. This might not be necessary"""
        now = int(time.time())
        if self.visitor_ids['expirationTime'] - now < 30:
            await self.get_visit_id()
            
        cookies = {
            'visit_id': self.visitor_ids['visit_id'],
            'visitor_id': self.visitor_ids['visitor_id'],
            'token': self.authorization['access_token'],
            'zipcode': zipcode
        }
        
        headers = {
            'Connection': 'keep-alive',
            'Gsm-Id': '',
            'Pragma': 'no-cache',
            'DNT': '1',
            'X-XSRF-TOKEN': '',
            'sec-ch-ua-mobile': '?0',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-store',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            'Origin': 'https://www.verizon.com',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://www.verizon.com/',
            'Accept-Language': 'en-US,en;q=0.9',
            'DNT': '1',
        }

        params = {
            'addressID': address_id,
            'state': state,
            'zip': zipcode,
            'isRememberMe': 'N',
            'oneLQ': 'Y',
            'city': city,
        }
        
        headers = {
            'Referer': 'https://www.verizon.com/',
        }

        response = await self.get(url=ADDR_VERIFY_URL, params=params, headers=headers, cookies=cookies, verify='data')
        return response
    
    
    async def check_fios(self):
        """
        This seems to only show up for FIOs (and returns an error for addresses with HSI). 
        Calling `is_address_qualified` previously seemes necessary.
        """
        now = int(time.time())
        if self.visitor_ids['expirationTime'] - now < 30:
            await self.get_visit_id()
            
        body = {
            "uid": self.visitor_ids['visit_id'],
            "idType":"visit",
            "contract":"MTM",
            "isPromoInclude":False,
            "serviceType":"Data",
            "intents":[]
        }
        headers = {
            'Host': 'api.verizon.com',
            'Connection': 'keep-alive',
            'Content-Length': '126',
            'Pragma': 'no-cache',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-store',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
            'Origin': 'https://www.verizon.com',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Referer': 'https://www.verizon.com/inhome/buildproducts',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        response = await self.post(url=FIOS_URL, json=body, headers=headers, cookies={}, verify='data')
        return response
    
    
    async def check_hsi_plans(self, zipcode):
        """
        This API call returns speed and price for HSI plans.
        This does not work without `order_info`. I'm totally unsure how this is set.
        Something about `order_info` requires zipcode.
        """
        now = int(time.time())
        if self.visitor_ids['expirationTime'] - now < 30:
            await self.get_visit_id()
            
        cookies = {
            'visit_id': self.visitor_ids['visit_id'], 
            'visitor_id': self.visitor_ids['visitor_id'],
            'token': self.authorization['access_token'],
            'zipcode': zipcode,
            'EOrdering': EORDER,
        }
                
        headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            'DNT': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.verizon.com/foryourhome/ordering/ordernew/buildhsi.aspx',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        timeout = aiohttp.ClientTimeout(total=5)
        jar = aiohttp.CookieJar(quote_cookie=False)
        jar.update_cookies(cookies)
        async with aiohttp.ClientSession(cookie_jar=jar, timeout=timeout) as sess:
            for n in range(2):
                async with sess.request("GET", url=HSI_URL, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        try:
                            data['PrdServices']
                        except:
                            continue
                        break
                    
                    data = {"error_status": response.status, "error_body": await response.text()}
                    if response.status in [429, 500, 502, 503, 504]:
                        await asyncio.sleep(random.uniform(.2, 1.2) * min(n, 1))
                        self.proxy.generate_proxy()
                        continue
                    await asyncio.sleep(random.uniform(.2, 1))
            await sess.close()
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
            connector = aiohttp.TCPConnector(limit=10)
            jar = aiohttp.CookieJar(quote_cookie=False)
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(connector=connector, cookie_jar=jar, timeout=timeout) as session:
                proxy = Proxy()
                session = Session(session, proxy)
                await session.register()

                status = 0
                street_address = record['address_full']                
                address_no_commas = street_address.replace(',', ' ')
                address_id = record.get('address_ntas_id')
                city = record['address_city']
                state = record['address_state']
                zipcode = record['address_zipcode']

                trial_and_tribulations = {}
                for n in range(2):
                    try:
                        # Check addresses
                        if not address_id:
                            trial_and_tribulations['address_id'] = True
                            if VERBOSE:
                                print(f"Checking address ID for {street_address}")
                            addresses = await session.get_address_id(street_address=address_no_commas, zipcode=zipcode)
                            addresses =  addresses.get('addressesbau', [])
                            if addresses:
                                address_id = addresses['addressesbau'][0]['addressID']
                            else:
                                trial_and_tribulations['cant_verify_address_id'] = True
                                status = 400
                                if VERBOSE:
                                    print(f"Couldn't verify {street_address}")

                        # check units
                        if address_id:
                            units_meta = await session.check_address_units(address_id=address_id)
                            await asyncio.sleep(random.uniform(.1, .4))
                            if units_meta.get('data'):
                                if VERBOSE:
                                    print(f"{street_address} is multiunit")
                                trial_and_tribulations['is_mdu'] = True
                                units = [
                                    unit.get('addressId') for unit in units_meta['data'].get('unitDetails', [{}])
                                ]
                                if units:
                                    address_id = units[0]
                                    if VERBOSE:
                                        print(f"new address id {address_id}")
                            if VERBOSE:
                                print(f"Checking qualifications for {street_address}")
                                
                            quals = await session.is_address_qualified(address_id=address_id, 
                                                                       state=state, 
                                                                       zipcode=zipcode, 
                                                                       city=city)
                            await asyncio.sleep(random.uniform(.1, .4))
                            if quals.get('data'):
                                qualified = [s['servicename'] for s in quals['data']['services'] if s['qualified'] == 'Y']
                                if not qualified:
                                    if VERBOSE:
                                        print(f"No internet at {street_address}")
                                    status = 200
                                    record['offer_verizon'] = {}
                                    
                                elif 'FiOSData' in qualified:
                                    if VERBOSE:
                                        print(f"FIOS at {street_address}")
                                    trial_and_tribulations['is_fios'] = True
                                    offers = await session.check_fios()
                                    if not offers.get("error_status"):
                                        record['offer_verizon'] = offers
                                        status = 200
                                    
                                elif 'HSI' in qualified:
                                    if VERBOSE:
                                        print(f"HSI at {street_address}")
                                    await asyncio.sleep(random.uniform(.2, .5))
                                    trial_and_tribulations['is_hsi'] = True
                                    offers = await session.check_hsi_plans(zipcode=zipcode)
                                    if not offers.get("error_status"):
                                        record['offer_verizon'] = offers
                                        status = 200

                            record['availability_qualifications'] = quals
                            break
                            
                    except (aiohttp.ClientProxyConnectionError, aiohttp.ClientHttpProxyError, asyncio.exceptions.TimeoutError) as e:
                        print("Proxy issue")
                        await asyncio.sleep(1)
                        proxy.generate_proxy()

                    except Exception as e:
                        print(f"Exception for {street_address} {e}")
                        await asyncio.sleep(1)
                    
                record['collection_status'] = status
                record['collection_api_calls'] = trial_and_tribulations
                record['collection_datetime'] = int(time.time())
                return record
        
    return async_get_offers


async def verizon_scraper(files, request_limit=100, n_threads=20):
    """
    A job that opens a list of input files for each census block group.
    The addresses in the census block group are sent through the ATT lookup tool asyncronusly
    until successfully capturing 10 percent of addresses in a block group.
    """
    http_client = chunked_http_client(n_threads)
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as client_session:
        collected = 0
        for fn in files:
            if collected < request_limit:
                fn_out = fn.replace('/inputs/', '/outputs_spotcheck/')
                if os.path.exists(fn_out):
                    continue
                # start things up
                os.makedirs(os.path.dirname(fn_out), exist_ok=True)
                print(f"working on {fn}")
                start = int(time.time())
                todo = read_ndjson(fn)
                quota = int(len(todo) * 0.1)
                if quota < 10:
                    quota = len(todo)
                
                # collect data here
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
                duration = int(time.time()) - start
                print(f"verified {successful} addresses from {len(output_addresses)} for {fn_out} in {duration} seconds")
                collected += 1
    return True       
            
    
def async_loop(files):
    loop = asyncio.get_event_loop()
    start = time.time()
    result = loop.run_until_complete(
        verizon_scraper(files, request_limit=REQUEST_LIMIT, n_threads=N_THREADS)
    )
    end = time.time()
    print(f"Time: {end - start}")
    return True
    
if __name__ == "__main__":
    inputs = list(range(0, N_JOBS))
    files_to_parse = glob.glob(f'{DIR_NAME}/data/inputs/verizon/boston/*.geojson.gz')
    random.shuffle(files_to_parse)
    print(f"files to process {len(files_to_parse)}")
    list_of_inputs = []
    for output in np.array_split(np.array(files_to_parse), N_JOBS):
        list_of_inputs.append(output)
    with Pool(processes=N_JOBS) as pool:
        for record in pool.map(async_loop, list_of_inputs):
            pass