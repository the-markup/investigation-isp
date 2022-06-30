import os
import random
import json

username = os.environ.get('BRIGHT_DATA_USER')
password = os.environ.get('BRIGHT_DATA_PASSWORD')
port = 22225
session_id = random.random()
super_proxy_url = f'http://{username}-country-us-session-{session_id}:{password}@zproxy.lum-superproxy.io:{port}'
proxies = { 
    "http"  : super_proxy_url, 
    "https" : f'https://{username}-country-us-session-{session_id}:{password}@zproxy.lum-superproxy.io:{port}', 
}

cities = []
with open('../data/cities.ndjson', 'r') as f:
    for line in f:
        cities.append(json.loads(line))
        
# EarthLink
name2speed_el = {
    'Earthlink Internet 3Mx1M': 3,
    'EarthLink Internet 3M': 3,
    'EarthLink Internet 6M': 6,
    'Earthlink Internet 6Mx1M': 6,
    'EarthLink Internet 9Mx1M': 9,
    'EarthLink Internet 10M': 10,
    'Earthlink Internet 12Mx1M': 12,
    'EarthLink Internet 12M': 12,
    'EarthLink Internet 15M': 15,
    'Earthlink Internet 18Mx1.5M': 18,
    'Earthlink Internet 24Mx3M': 24,
    'EarthLink Internet 25Mx2M' : 25,
    'EarthLink Internet 30M': 30,
    'Earthlink Internet 45Mx6M': 45,
    'Earthlink Internet 75Mx8M': 75,
    'EarthLink Internet 75M': 75,
    'Earthlink Fiber 100Mx100M': 100,
    'EarthLink Internet 115Mx7M': 115,
    'EarthLink Fiber 300Mx300M': 300,
}

state2redlining = {
    'TX': ['../data/redlining/TXHouston19XX.geojson'],
    'CA': ['../data/redlining/CALosAngeles1939.geojson'],
    'LA': ['../data/redlining/LANewOrleans1939.geojson'],
    'KS': ['../data/redlining/KSWichita1937.geojson'],
    'IA': ['../data/redlining/IADesMoines19XX.geojson'],
    'OH': ['../data/redlining/OHCleveland1939.geojson'],
    'WV': ['../data/redlining/WVCharleston1938.geojson'],
    'AR': ['../data/redlining/ARLittleRock19XX.geojson'],
    'AZ': ['../data/redlining/AZPhoenix19XX.geojson'],
    'OR': ['../data/redlining/ORPortland1937.geojson'],
    'PA': ['../data/redlining/PAPhiladelphia1937.geojson'],
    'KY': ['../data/redlining/KYLouisville1938.geojson'],
    'MD': ['../data/redlining/MDBaltimore1937.geojson'],
    'WI': ['../data/redlining/WIMilwaukeeCo1937.geojson'],
    'IN': ['../data/redlining/INIndianapolis1937.geojson'],
    'NE': ['../data/redlining/NEOmaha19XX.geojson'],
    'FL': ['../data/redlining/FLJacksonville1937.geojson'],
    'MI': ['../data/redlining/MIDetroit1939.geojson'],
    'IL': ['../data/redlining/ILChicago1940.geojson'],
    'UT': ['../data/redlining/UTSaltLakeCity19XX.geojson'],
    'MA': ['../data/redlining/MABoston1938.geojson'],
    'GA': ['../data/redlining/GAAtlanta1938.geojson'],
    'RI': ['../data/redlining/RIProvidence19XX.geojson'],
    'NJ': ['../data/redlining/NJEssexCo1939.geojson'],
    'CO': ['../data/redlining/CODenver1938.geojson'],
    'MN': ['../data/redlining/MNMinneapolis1937.geojson'],
    'WA': ['../data/redlining/WASeattle1936.geojson'],
    'MO': ['../data/redlining/MOGreaterKansasCity1939.geojson'],
    'MS': ['../data/redlining/MSJackson19XX.geojson'],
    'NC': ['../data/redlining/NCCharlotte1935.geojson'],
    'TN': ['../data/redlining/TNMemphis19XX.geojson'],
    'NY': [
        '../data/redlining/NYBronx1938.geojson',
        '../data/redlining/NYBrooklyn1938.geojson',
        '../data/redlining/NYManhattan1937.geojson',
        '../data/redlining/NYQueens1938.geojson',
        '../data/redlining/NYStatenIsland1940.geojson',
    ],
}