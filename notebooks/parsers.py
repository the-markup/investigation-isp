import gzip
import json

import numpy as np
import pandas as pd
from tqdm import tqdm
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from sklearn.neighbors import BallTree

from config import name2speed_el, state2redlining, cities


## Census Geocoding
def get_incorporated_places(row: dict):
    places = []
    if row['geography'].get('places'):
        places = row['geography'].get('places', {}).get('geographies', {}).get('Incorporated Places', [])
    elif row.get('geography_places'):
        places = row.get('geography_places').get('Incorporated Places', [])
    return '|'.join([_.get('NAME') for _ in places])

def get_state(row: dict):
    places = []
    if row['geography'].get('places'):
        places = row['geography'].get('places', {}).get('geographies', {}).get('States', [])
    elif row.get('geography_places'):
        places = row.get('geography_places').get('States', [])
    return '|'.join([_.get('STUSAB') for _ in places])

## Redlining
def get_holc_grade(row: dict, 
                   polygons: list) -> str:
    """
    Converts any lat and lon in a dictionary into a shapely point,
    then iterate through a list of dictionaries containing 
    shapely polygons shapes for each HOLC-graded area.
    """
    point = Point(float(row['lon']), float(row['lat']))
    for polygon in polygons:
        if polygon['shape'].contains(point):
            return polygon['grade']
    return None

def check_redlining(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get redlining grades for each address in "df".
    Note: we use city-level HOLC grades, but index on state. 
    Thanks for the Mapping Inequality project for digitizing the maps,
    which are stored in `../data/input/redlining`.
    """
    data = []
    for state, _df in tqdm(df.groupby('state')):
        # read redlining maps for each city in `df`.
        files = state2redlining.get(state, [])
        polygons = []
        if files:
            for fn in files:
                geojson = json.load(open(fn))
                for record in geojson['features']:
                    shape = Polygon(record['geometry']['coordinates'][0][0])
                    grade = record['properties']['holc_grade']
                    polygons.append({
                        "shape": shape,
                        "grade": grade
                    })
            _df['redlining_grade'] = _df.apply(get_holc_grade,
                                               polygons=polygons, 
                                               axis=1)
        data.extend(_df.to_dict(orient='records'))
    return pd.DataFrame(data)

## Distance
def get_closest_fiber(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert coordinates to radians and fit a sklearn ball tree 
    to find closest household with 200 Mbps speeds.
    """
    _df = df[df.speed_down >= 200]
    
    # create a ball tree just on fiber households
    tree = BallTree(np.deg2rad(_df[['lat', 'lon']]), metric="haversine")
    # find the closest fiber for every household
    distances, indices = tree.query(np.deg2rad(df[['lat', 'lon']]),
                                    k=1, return_distance=True)
    df["closest_fiber_miles"] = distances * 3958.756
    
    # merge the info of the closest fiber household
    closest = _df.iloc[indices[:, 0]].reset_index(drop=True) 
    return df.merge(closest, 
                    how='left',
                    left_index=True, right_index=True, 
                    suffixes=['', '_closest_fiber'])

## ATT
# https://about.att.com/sites/broadband/performance
def get_cheapest_speed_att(row: dict):
    """
    Parse each offer from AT&T's API, and return the cheapest one.
    """
    try:
        if row.get('offer_att'):
            row = row['offer_att']
            if isinstance(row, dict):

                is_fiber = (row.get('content', {})
                               .get("serviceAvailability", {})
                               .get("availableServices", {}).get("fiberAvailable"))
                internet = row.get('content', {}).get('baseOffers', {}).get('broadband')

                if internet:
                    plans = []
                    for plan in internet['basePlans']:
                        offer = plan['product']
                        package = offer['shortDisplayName']
                        speed_unit = offer['downloadSpeed']['uom']
                        speed_down = offer['downloadSpeed']['speed']
                        speed_up = offer['uploadSpeed']['speed'] if 'FIBER' not in package else speed_down
                        if speed_unit == 'Kbps':
                            speed_down = speed_down * .001
                            speed_up = speed_up * .001
                            speed_unit = 'Mbps'
                        plans.append({
                            'package': package,
                            'speed_unit': speed_unit,
                            'speed_down': speed_down,
                            'speed_up': speed_up,
                            'price': offer['price']['netPrice'],
                            'technology': 'Fiber' if is_fiber else 'Not Fiber',
                        })
                    plans = pd.DataFrame(plans) 

                    baseplan = plans.sort_values(by='price', ascending=True).iloc[0]
                    fastest_plan = plans.sort_values(by='speed_down', ascending=False).iloc[0]
                    return pd.DataFrame([dict(
                        speed_down = baseplan['speed_down'],
                        speed_up = baseplan['speed_up'],
                        speed_unit = baseplan['speed_unit'],
                        price = baseplan['price'],
                        technology = baseplan['technology'],
                        package = baseplan['package'],
                        fastest_speed_down = fastest_plan['speed_down'],
                        fastest_speed_price = fastest_plan['price']
                    )]).iloc[0]
    except Exception as e:
        pass
    return pd.DataFrame([dict(
        speed_down = 0,
        speed_up = 0,
        speed_unit = "",
        price = None,
        technology = None,
        package = None,
        fastest_speed_down = 0,
        fastest_speed_price = 0
    )]).iloc[0]

def parse_att(row: dict):
    lon, lat =  row['geometry']['coordinates']
    incorporated_place = get_incorporated_places(row)

    record = {
        "address_full": row['address_full'],
        "incorporated_place" : incorporated_place,
        "major_city": row['major_city'],
        "state" : get_state(row),
        "lat": lat,
        "lon": lon,
#         "availability_status" : row.get('availability_status'),
        "block_group": str(row['block_group']),
        "collection_datetime": row['collection_datetime'],
        'provider': 'AT&T'
    }
    speeds = dict(get_cheapest_speed_att(row))        
    record = {**record, **speeds}
    return record

def att_workflow(fn: str):
    data = []
    with gzip.open(fn, 'rb') as f:
        for line in f.readlines():
            row = json.loads(line)
            if row['collection_status'] != 0:
                record = parse_att(row)
                record['fn'] = fn
                data.append(record)
    return data


## CL
def get_cheapest_speed_cl(row: dict):
    """
    Parse each offer from CenturyLink's API, and return the cheapest one.
    """
    if isinstance(row['offer_centurylink'], dict):
        if row['offer_centurylink'].keys():            
            offer_list = row['offer_centurylink'].get('offersList')
            offers = []
            for offer in offer_list:  
                speed_down = float(offer['downloadSpeedMbps'])
                speed_up = float(offer['uploadSpeedMbps'])
                offers.append({
                    'speed_down': speed_down,
                    'speed_up': speed_up,
                    'speed_unit': 'Mbps',
                    'price': offer.get('price'),
                    'technology': 'Fiber' if speed_down == speed_up else 'Not Fiber',
                    'package': offer['offerName']
                })
            if offers:
                
                cheapest_speed =  (pd.DataFrame(offers)
                                       .sort_values(by='price', ascending=True)
                                       .reset_index(drop=True).iloc[0])
                fastest_speed = (pd.DataFrame(offers)
                                       .sort_values(by='speed_down', ascending=False)
                                       .reset_index(drop=True).iloc[0])
                
                cheapest_speed['fastest_speed_down'] = fastest_speed['speed_down']
                cheapest_speed['fastest_speed_price'] = fastest_speed['price']
                
                return cheapest_speed
            
    return pd.DataFrame([{
        'speed_down': 0,
        'speed_up': 0,
        'speed_unit': 'Mbps',
        'price': None,
        'technology': None,
        'package': None,
        'fastest_speed_down': 0,
        'fastest_speed_price': 0
    }]).iloc[0]


def parse_cl(row: dict):
    lon, lat =  row['geometry']['coordinates']
    incorporated_place = get_incorporated_places(row)

    record = {
        "address_full": row['address_full'],
        "incorporated_place" : incorporated_place,
        "major_city": row['major_city'],
        "state" : [_['state'] for _ in cities if _['city'].lower() == row['major_city']][0],
        "lat": lat,
        "lon": lon,
#         "availability_status" : row.get('availability_status'),
        "block_group": str(row['block_group']),
        "collection_datetime": row['collection_datetime'],
        'provider': 'CenturyLink'

    }
    speeds = dict(get_cheapest_speed_cl(row))
    record = {**record, **speeds}
    return record

def cl_workflow(fn: str):
    try:
        data = []
        with gzip.open(fn, 'rb') as f:
            for line in f.readlines():
                row = json.loads(line)
                if row['collection_status'] != 0:
                    record = parse_cl(row)
                    record['fn'] = fn
                    data.append(record)
        return data
    except Exception as e:
        print(f"{fn} {e}")
        return []
    
    
## Verizon
def get_cheapest_speed_hsi(row: dict):
    """
    Return cheapest offer by Verizon's HSI service.
    Verizon has a different API response for High-Speed Internet (HSI)
    than for Fios.
    """
    plans = []
    products = row['offer_verizon']['PrdServices']
    for service in products:
        service_name = service['Name']
        if "Internet" in service_name:
            service_name = service['ServiceDesc']
            speeds = service["UKey"]
            speed_down, speed_up = speeds.split('_')
            # speed converted to Mbps
            speed_down = int(speed_down) * .000001
            speed_up = int(speed_up) * .000001
            internet = dict(
                speed_down = speed_down,
                speed_up = speed_up,
                speed_unit = 'Mbps',
                price = service['Price'],
                technology = "Not fiber",
                package = "HSI " + service_name
            )
            plans.append(internet)
    cheapest_offer = pd.DataFrame(plans).sort_values(by=['price', 'speed_down'], 
                                           ascending=[True, False]).iloc[0]
    fastest_offer = pd.DataFrame(plans).sort_values(by=['speed_down'], 
                                           ascending=False).iloc[0]
    cheapest_offer['fastest_speed_down'] = fastest_offer['speed_down']
    cheapest_offer['fastest_speed_price'] = fastest_offer['price']
    return cheapest_offer

def get_cheapest_speed_fios(row: dict):
    """
    Get cheapest offer for Fios based on API response from Verizon.
    Note: We assume symmetrical speeds for Fiber.
    """
    plans = []
    products = row['offer_verizon']['data'].get('products', [])    
    for service in products:
        try:
            service_name = service['name']
            internet = dict(
                speed_down = float(service['downSpeed'].rstrip('M')),
                speed_up = float(service['downSpeed'].rstrip('M')),
                speed_unit = 'Mbps',
                price = float(service['displayPrice'].replace('$', '')),
                technology = "Fiber",
                package = "FiOS " + service_name
            )
            plans.append(internet)
        except Exception as e:
            print(service['name'], e)
    if plans:
        cheapest_offer = pd.DataFrame(plans).sort_values(by='price', 
                                                         ascending=True).iloc[0]
        fastest_offer = pd.DataFrame(plans).sort_values(by='speed_down', 
                                                         ascending=False).iloc[0]
        cheapest_offer['fastest_speed_down'] = fastest_offer['speed_down']
        cheapest_offer['fastest_speed_price'] = fastest_offer['price']
        return cheapest_offer
    
    return pd.DataFrame([{
        'speed_down': 0, 'speed_up': 0, 'price': None, 'package':'FiOS',
        'fastest_speed_down': 0, 'fastest_speed_price': 0
    }]).loc[0]
    
def get_cheapest_speed_verizon(row: dict):
    offer = row.get('offer_verizon')
    if not offer:
        return pd.DataFrame([{
            'speed_down': 0, 'speed_up': 0, 'price': None,
            'fastest_speed_down': 0, 'fastest_speed_price': 0
        }]).loc[0]
    
    if isinstance(offer, float):
        return pd.DataFrame([{
            'speed_down': 0, 'speed_up': 0, 'price': None,
            'fastest_speed_down': 0, 'fastest_speed_price': 0
        }]).loc[0]
    elif offer.get('data'):
        return get_cheapest_speed_fios(row)
    elif offer.get('PrdServices'):
        return get_cheapest_speed_hsi(row)
    
def parse_verizon(row: dict, include_offer_meta = False):
    lon, lat =  row['geometry']['coordinates']
    incorporated_place = get_incorporated_places(row)
    in_service = (row.get('availability_qualifications', {})
                     .get('data', {})
                     .get('inService'))
    record = {
        "address_full": row['address_full'],
        "incorporated_place" : incorporated_place,
        "major_city": row['major_city'],
        "state" : get_state(row),
        "lat": lat,
        "lon": lon,
#         "availability_status" : row.get('availability_status'),
        "block_group": str(row['block_group']),
        "collection_datetime": row['collection_datetime'],
        'in_service' : True if in_service == 'Y' else False,
        'provider': 'Verizon'

    }
    speeds = dict(get_cheapest_speed_verizon(row))
    record = {**record, **speeds}
    if include_offer_meta:
        record['offer'] = row.get('offer_verizon')
    return record

def verizon_workflow(fn: str, include_offer_meta=False):
    try:
        data = []
        with gzip.open(fn, 'rb') as f:
            for line in f.readlines():
                row = json.loads(line)
                if row['collection_status'] != 400:
                    record = parse_verizon(row, include_offer_meta)
                    record['fn'] = fn
                    data.append(record)
        return data
    except Exception as e:
        print(f"{fn} {e}")
        return []

## EarthLink
def get_cheapest_speed_el(row: dict):
    """
    Parse each offer from EarthLink's API, and return the cheapest one.
    """
    if not isinstance(row['offers_earthlink'], dict):
        return pd.DataFrame([{
            "price": None, "download_speed": 0, "speed_unit": None,
            "upload_speed":0, "technology": None, "plan_name": None
        }]).iloc[0]
    offers = row['offers_earthlink']['products']
    if offers:
        providers = row['offers_earthlink'].get("extendedInfo")
        if providers:
            providers = providers.get("serviceableService", [])
            code2meta = {
                _.get("level"): _ for _ in providers
            }
        else:
            code2meta = {}
        
        plans = []
        for offer in offers:
            service_name = offer['serviceName']
            serv_level = offer["servLevel"]
            provider = (code2meta.get(serv_level, {})
                                 .get("vendor", "").replace(" IMA", ""))
            technology = code2meta.get(serv_level, {}).get("servLineType")
            plans.append(dict(
                price=float(offer['price'].lstrip('$')),
                speed_down= float(name2speed_el.get(service_name.lower(), service_name)),
                speed_up = int(offer['upstreamSpd']) / 1000,
                speed_unit = "Mbps",
                technology=technology,
                package=service_name,
                contract_provider = provider
            ))
        cheapest_offer = pd.DataFrame(plans).sort_values(by='price', 
                                                         ascending=True).iloc[0]
        fastest_offer = pd.DataFrame(plans).sort_values(by='speed_down', 
                                                        ascending=False).iloc[0]
        cheapest_offer['fastest_speed_down'] = fastest_offer['speed_down']
        cheapest_offer['fastest_speed_price'] = fastest_offer['price']
        return cheapest_offer
    else:
        return pd.DataFrame([{
            "price": None, "speed_down": 0, "speed_up":0,
            "speed_unit": None, "technology": None, "package": None,
            "fastest_speed_down": 0, "fastest_speed_price": 0
        }]).iloc[0]
    
    
def parse_el(row: dict, include_offer_meta=False):
    lon, lat =  row['geometry']['coordinates']
    incorporated_place = get_incorporated_places(row)

    record = {
        "address_full": row['address_full'],
        "incorporated_place" : incorporated_place,
        "major_city": row['major_city'],
        "state" : get_state(row),
        "lat": lat,
        "lon": lon,
#         "availability_status" : row.get('availability_status'),
        "block_group": str(row['block_group']),
        "collection_datetime": row['collection_datetime'],
        'provider': 'EarthLink'

    }
    speeds = dict(get_cheapest_speed_el(row))
    record = {**record, **speeds}
    if include_offer_meta:
        reccord['offers_earthlink'] = row['offers_earthlink']
    
    return record
    
def el_workflow(fn: str, include_offer_meta=False):
    try:
        data = []
        with gzip.open(fn, 'rb') as f:
            for line in f.readlines():
                row = json.loads(line)
                if row['collection_status'] != 0:
                    record = parse_el(row, include_offer_meta)
                    record['fn'] = fn
                    data.append(record)
        return data
    except Exception as e:
        print(f"{fn} {e}")
        return []
    
def read_ndjson(fn: str):
    data = []
    with gzip.open(fn, 'rb') as f:
        for line in f.readlines():
            data.append(json.loads(line))
    return data