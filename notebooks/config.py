import json

cities = []
with open('../data/input/addresses/cities.ndjson', 'r') as f:
    for line in f:
        cities.append(json.loads(line))
        
inc_city_att = [
    'Atlanta city',
    'Charleston city',
    'Charlotte city',
    'Chicago city',
    'Cleveland city',
    'Detroit city',
    'Houston city',
    'Huntsville city',
    'Indianapolis city (balance)',
    'Jacksonville city',
    'Jackson city',
    'Kansas City city',
    'Little Rock city',
    'Los Angeles city',
    'Louisville city',
    'Memphis city',
    'Milwaukee city',
    'New Orleans city',
    'Oklahoma City city',
    'Wichita city',
]

inc_city_cl = [
    'Albuquerque city',
    'Billings city',
    'Boise City city',
    'Cheyenne city',
    'Denver city',
    'Des Moines city',
    'Fargo city',
    'Las Vegas city',
    'Minneapolis city',
    'Omaha city',
    'Phoenix city',
    'Portland city',
    'Salt Lake City city',
    'Seattle city',
    'Sioux Falls city'
]

inc_city_verizon = [
    'Baltimore city',
    'Boston city',
    'New York city',
    'Newark city',
    'Philadelphia city',
    'Providence city',
    'Virginia Beach city',
    'Washington city',
    'Wilmington city'
]

inc_city_el = [
    'Albuquerque city',
    'Atlanta city',
    'Billings city',
    'Boise City city',
    'Bridgeport city',
    'Charleston city',
    'Charlotte city',
    'Cheyenne city',
    'Chicago city',
    'Cleveland city',
    'Denver city',
    'Des Moines city',
    'Detroit city',
    'Fargo city',
    'Houston city',
    'Huntsville city',
    'Indianapolis city (balance)',
    'Jacksonville city',
    'Kansas City city',
    'Las Vegas city',
    'Little Rock city',
    'Los Angeles city',
    'Louisville city',
    'Memphis city',
    'Milwaukee city',
    'New Orleans city',
    'Oklahoma City city',
    'Omaha city',
    'Phoenix city',
    'Portland city',
    'Salt Lake City city',
    'Seattle city',
    'Sioux Falls city',
    'Wichita city'
]

state2redlining = {
    'TX': ['../data/input/redlining/TXHouston19XX.geojson'],
    'CA': ['../data/input/redlining/CALosAngeles1939.geojson'],
    'LA': ['../data/input/redlining/LANewOrleans1939.geojson'],
    'KS': ['../data/input/redlining/KSWichita1937.geojson'],
    'IA': ['../data/input/redlining/IADesMoines19XX.geojson'],
    'OH': ['../data/input/redlining/OHCleveland1939.geojson'],
    'WV': ['../data/input/redlining/WVCharleston1938.geojson'],
    'AR': ['../data/input/redlining/ARLittleRock19XX.geojson'],
    'AZ': ['../data/input/redlining/AZPhoenix19XX.geojson'],
    'OR': ['../data/input/redlining/ORPortland1937.geojson'],
    'PA': ['../data/input/redlining/PAPhiladelphia1937.geojson'],
    'KY': ['../data/input/redlining/KYLouisville1938.geojson'],
    'MD': ['../data/input/redlining/MDBaltimore1937.geojson'],
    'WI': ['../data/input/redlining/WIMilwaukeeCo1937.geojson'],
    'IN': ['../data/input/redlining/INIndianapolis1937.geojson'],
    'NE': ['../data/input/redlining/NEOmaha19XX.geojson'],
    'FL': ['../data/input/redlining/FLJacksonville1937.geojson'],
    'MI': ['../data/input/redlining/MIDetroit1939.geojson'],
    'IL': ['../data/input/redlining/ILChicago1940.geojson'],
    'UT': ['../data/input/redlining/UTSaltLakeCity19XX.geojson'],
    'MA': ['../data/input/redlining/MABoston1938.geojson'],
    'GA': ['../data/input/redlining/GAAtlanta1938.geojson'],
    'RI': ['../data/input/redlining/RIProvidence19XX.geojson'],
    'NJ': ['../data/input/redlining/NJEssexCo1939.geojson'],
    'CO': ['../data/input/redlining/CODenver1938.geojson'],
    'MN': ['../data/input/redlining/MNMinneapolis1937.geojson'],
    'WA': ['../data/input/redlining/WASeattle1936.geojson'],
    'MO': ['../data/input/redlining/MOGreaterKansasCity1939.geojson'],
    'MS': ['../data/input/redlining/MSJackson19XX.geojson'],
    'NC': ['../data/input/redlining/NCCharlotte1935.geojson'],
    'TN': ['../data/input/redlining/TNMemphis19XX.geojson'],
    'NY': [
        '../data/input/redlining/NYBronx1938.geojson',
        '../data/input/redlining/NYBrooklyn1938.geojson',
        '../data/input/redlining/NYManhattan1937.geojson',
        '../data/input/redlining/NYQueens1938.geojson',
        '../data/input/redlining/NYStatenIsland1940.geojson',
    ],
}

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
    'EarthLink Internet 18M': 18,
    'Earthlink Internet 18Mx1.5M': 18,
    'Earthlink Internet 24Mx3M': 24,
    'EarthLink Internet 25Mx2M': 25,
    'EarthLink Internet 30M': 30,
    'Earthlink Internet 45Mx6M': 45,
    'EarthLink Internet 45M': 45,
    'EarthLink Internet 70Mx3M': 70,
    'Earthlink Internet 75Mx8M': 75,
    'EarthLink Internet 75M': 75,
    'Earthlink Fiber 100Mx100M': 100,
    'EarthLink Internet 115Mx7M' : 115,
    'EarthLink Fiber 300Mx300M': 300,
}

speed_labels = {
    'No service' : "#5D5D5D", 
    'Slow (<25 Mbps)' : '#801930', 
    'Medium (25-100)' : '#a8596d', 
    'Fast (100-200)' : '#aebdcf', 
    "Blazin' (>200)": '#7b89a1'
}

income_labels = [
    'Low', 
    'Moderate', 
    'Middle', 
    'Upper Income'
]

redlininggrade2name = {
    'A' : 'A - Best',
    'B' : 'B - Desirable',
    'C' : 'C - Declining',
    'D' : 'D - Hazardous',
}