"""
Verison Scraper
Nede to implement the main script
"""

import requests
import time
import json

AUTH_URL = 'https://www.verizon.com/inhome/generatetoken'
VISIT_URL = 'https://www.verizon.com/inhome/generatevisitid'
UNITS_URL = 'https://api.verizon.com/atomapi/v1/addresslookup/addresses/units'
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36'

class Session:
    def authorize(self):
        headers = {
            'User-Agent': user_agent,
            'Accept-Language' : 'en,en-US;q=0,5',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8"',
        }
        resp = requests.get(url=AUTH_URL, headers=headers)
        self.authorization = resp.json()
    
    def get_visit_id(self):
        headers = {
            'Host': 'www.verizon.com',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Authorization': 'Bearer ' + self.authorization['access_token'],
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-store',
            'User-Agent': user_agent,
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Referer': 'https://www.verizon.com/inhome/qualification?lid=//global//residential',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        resp = requests.get(url=VISIT_URL, headers=headers)
        self.visitor_ids = resp.json()

    @property
    def headers(self):
        auth = self.authorization
        now = int(time.time())
        if int(auth["issued_at"]) + int(auth["expires_in"]) - now < 30:
            self.authorize()

        return {
            "Authorization": f"Bearer {self.authorization['access_token']}",
        }

    def get(self, *args, **kwargs):
        return requests.get(*args, **{**kwargs, **{"headers": self.headers}})

    def post(self, *args, **kwargs):
        return requests.post(*args, **{**kwargs, **{"headers": self.headers}})

def get_address_id(session, address_no_commas, zipcode):
    """
    Address ID is necessary to make API call.
    address_no_commas can look like: 149 MILBURN ST BUFFALO NY 14212
    """
    url = ('https://api.verizon.com/atomapi/v1/addresslookup/addresses/streetbyzip'
           f'?zip={zipcode}&streetterm={address_no_commas}')
    headers = {
        'Origin':'https://www.verizon.com',
        'User-Agent': user_agent,
    }
    resp = session.get(url=url, headers=headers)
    try:
        address_id_base =  resp.json()['addressesbau'][0]['addressID']
        return address_id_base
    except Exception:
        print(f"error {resp.content}")

def check_address_units(session, address_id_base):
    """Check if the address has multiple units"""
    now = int(time.time())
    if session.visitor_ids['expirationTime'] - now < 30:
        session.get_visit_id()
    cookies = {
        'visit_id': session.visitor_ids['visit_id'],
        'visitor_id': session.visitor_ids['visitor_id'],
        'token': session.authorization['access_token'],
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
        'User-Agent': user_agent,
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
        'sec-ch-ua-platform': '"macOS"',
        'Origin': 'https://www.verizon.com',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.verizon.com/',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    params = (
        ('baseAddressId', address_id_base),
    )
    resp_unit = session.get(UNITS_URL, headers=headers, params=params, cookies=cookies)
    return resp_unit.json()

def is_address_qualified(session, address_id, state, zipcode, city):
    """Check if the address is qualified. This might not be necessary"""
    cookies = {
        'visit_id': session.visitor_ids['visit_id'],
        'visitor_id': session.visitor_ids['visitor_id'],
        'token': session.authorization['access_token'],
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
        'User-Agent': user_agent,
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'Origin': 'https://www.verizon.com',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://www.verizon.com/',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    params = {
        'addressID': address_id,
        'state': state,
        'zip': zipcode,
        'isRememberMe': 'N',
        'oneLQ': 'Y',
        'city': city,
    }

    response = session.get('https://api.verizon.com/atomapi/v1/addressqualification/address/qualification', 
                            headers=headers, params=params, cookies=cookies)
    return response.json()

def check_fios(session):
    """
    This seems to only show up for FIOs (and returns an error for addresses with HSI). 
    Calling `is_address_qualified` previously seemes necessary.
    """
    url = 'https://api.verizon.com/atomapi/v1/qualifiedproducts/accordion/products/plans'
    body = {
        "uid": session.visitor_ids['visit_id'],
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
        'User-Agent': user_agent,
        'Origin': 'https://www.verizon.com',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Referer': 'https://www.verizon.com/inhome/buildproducts',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    response = session.post(url=url, json=body, headers=headers)
    return response.json()

def check_hsi_plans(session, zipcode, 
                    order_info='_e_=NEScrpqiSNYsfRw1htIPZi8bw%3d%3d'):
    """
    This API call returns speed and price for HSI plans.
    This does not work without `order_info`. I'm totally unsure how this is set.
    Something about `order_info` requires zipcode.
    """
    now = int(time.time())
    if session.visitor_ids['expirationTime'] - now < 30:
        session.get_visit_id()
    cookies = {
        'visit_id': session.visitor_ids['visit_id'], 
        'visitor_id': session.visitor_ids['visitor_id'],
        'token': session.authorization['access_token'],
        'zipcode': zipcode,
        # unsure how this is generated?
        'EOrdering': order_info,
    }

    headers = {
        'Connection': 'keep-alive',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
        'DNT': '1',
        'User-Agent': user_agent,
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.verizon.com/foryourhome/ordering/ordernew/buildhsi.aspx',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    response = requests.get('https://www.verizon.com/foryourhome/ordering/Services/GetAllProducts', 
                        headers=headers, cookies=cookies)
    return response.json()