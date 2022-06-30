"""
Utility functins
This was originally just Selenium util functions, 
but its now a general utils file for working with addresses, 
generating proxies, and working with gzipped newline-delimited json (ndjson) files.
"""

import os
import re
import gzip
import json
import time
import random
import tempfile
import functools
import shutil
import requests
from typing import List, Dict

def generate_proxy():
    username = os.environ.get('BRIGHT_DATA_USER')
    password = os.environ.get('BRIGHT_DATA_PASSWORD')
    port = 22225
    session_id = random.random()
    super_proxy_url = f'http://{username}-country-us-session-{session_id}:{password}@zproxy.lum-superproxy.io:{port}'

    return super_proxy_url

class Proxy:
    """
    A proxy manager that rotates IP addresses
    after `refresh_in` seconds, or a new IP every time.
    """
    def __init__(self, refresh_in=10, requests_mode=False, verbose=False):
        self.refresh_in=refresh_in
        self.verbose=verbose
        self.requests_mode=requests_mode
        self.generate_proxy()
        
    def generate_proxy(self):
        now = int(time.time())
        self.proxy = generate_proxy()
        self.init_time = now
        if self.verbose:
            print(f"New proxy generated at {now}")
            
    def get_proxy(self, new_ip=False, as_dict=False):
        """Either get a new IP or use the same one until `refresh_in` seconds"""
        if new_ip:
            return generate_proxy()
        else:
            now = int(time.time())
            if now - self.init_time >= self.refresh_in:
                self.generate_proxy()
        if self.requests_mode or as_dict:
            return { 
                "http"  : self.proxy, 
                "https" : self.proxy 
            }
        return self.proxy
    
class Session:
    """
    To handle authentication within each ISP
    """
    def __init__(self, auth_url, verbose=False, *args, **kwargs):
        self.auth_url = auth_url
        self.verbose=verbose
        self.authorize(*args, **kwargs)
    
    def authorize(self, *args, **kwargs):
        self.authorization = requests.get(self.auth_url, *args, **kwargs).json()
        if self.verbose:
            print(f"Authorizing a token: {json.dumps(self.authorization)}")
    
    def get_token(self):
        a = self.authorization
        now = int(time.time())
        if int(a["issued_at"]) + int(a["expires_in"]) - now < 30:
            self.authorize()
        return  f"Bearer {self.authorization['access_token']}"
    
def make_ordinal(n):
    '''
    Convert an integer into its ordinal representation::

        make_ordinal(0)   => '0th'
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    '''
    n = int(n)
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix

def fix_numerical_street(street):
    split = street.split(' ')
    fixed_street = []
    for word in split:
        if word.isdigit():
            word = make_ordinal(word)
        fixed_street.append(word)
    return ' '.join(fixed_street)

def street_to_number(street):
    """
    Extracts number from streetname
    """
    split = street.split(' ')
    number = []
    for word in split:
        if word.isdigit():
            number.append(word)
    if number:
        return number[0]
    return street

def remove_direction(street):
    directions = {'N', 'W', 'S', 'E'}
    split = street.split(' ')
    fixed_street = []
    for word in split:
        if word.upper() not in directions:
            fixed_street.append(word)
    return ' '.join(fixed_street)

def format_full_address(row: dict, city: str, state: str):
    """
    Returns a street address from OpenAddress data
    """
    a = row['properties']
    street = a['street']
    if state == 'HI':
        honolulu_city = a['city']
        if honolulu_city:
            city = honolulu_city.split('/')[0].rstrip().upper()
    
    if city.upper() in ['LOS ANGELES']:
        street = remove_direction(street)
    
    if city.upper() in ['QUEENS', 'BOSTON']:
        street = street_to_number(street)
        address = f"{a['number']} {street}, {state} {a['postcode'].split('.')[0]}"

    else:
        street = fix_numerical_street(street)
        address = f"{a['number']} {street}, {city} {state} {a['postcode'].split('.')[0]}"
    return address

def read_ndjson(fn: str):
    data = []
    with gzip.open(fn, 'rb') as f:
        for line in f.readlines():
            data.append(json.loads(line))
    return data

def dump_ndjson(fn_out: str, 
                output: List[Dict]):
    with gzip.open(fn_out, 'wt') as f:
        for line in output:
            f.write(json.dumps(line) + '\n')