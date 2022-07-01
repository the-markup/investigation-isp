# Racial and Economic Disparities in Internet Service Offers

Data that we collected and analyzed are in the `data` folder.

Jupyter notebooks used for data collection, preprocessing and analysis are in the `notebooks` folder.


## Installation
### Python
Make sure you have Python 3.6+ installed, we used [Miniconda](https://docs.conda.io/en/latest/miniconda.html) to create a Python 3.8 virtual environment.

Then install the Python packages:<br>
```
pip install -r requirements.txt
```

Use the `Makefile` to create a virtual environment and download the dependencies
```
make venv
```

## Notebooks
These notebooks are intended to be run sequentially, but they are not dependent on one another.

Run every notebook with this command:
```
make run
```
Note that when `recalculate = False` (the default) in each notebook, files that exist are not re-generated.

### 0-get-acs-data.ipynb
Collect data from the U.S. Census Bureau's American Community Survey. You'll need an Census [API key](https://api.census.gov/data/key_signup.html) and assign an environment variable `CENSUS_API_KEY`.

### 1-process-offers.ipynb
Parses and preprocesses the JSON responses for offers collected from ISP's service lookup tools. The functions that parse each response can be found in `parsers.py`.

### 2a-att-reports.ipynb
An overview of offers by the ISP AT&T. This contains breakdowns cities served by AT&T by income-level, race/ethnicity, and historical redlining grades. The same notebooks exist for Verizon (`2b-verizon-reports.ipynb`), CenturyLink (`2c-centurylink-reports.ipynb`), and EarthLink (`2d-earthlink-reports.ipynb`).

The code to produce these charts is in `analysis.py`

### 3-statistical-tests-and-regression.ipynb *
The bulk of analysis is in this notebook. 

This is where we calclate the distance to fiber-level speeds, speed disparities between social groups, and logistic regression to see if business factors eliminate disparities we observed.

### 4-verizon-spotcheck.ipynb
A look into Verizon's price changes for limitations in the methdology.

### 5-city-template.ipynb
Used to generate a high-level summary of Internet offers for every city in our investigation.


<hr>

There are also several Python scripts in this directory:

###  utils.py
Contains general functions that are re-used.

### analysis.py
Used to produce charts in notebooks starting with "2".

### parsers.py
Parsers for JSON from lookup tools and geocodes addresses within HOLC grades.

### config.py
Contains shared variables used throughout notebooks.

### istarmap.py
Monkeypatch of `Multiprocessing.Pool`.


## Data
This directory is where inputs, intermediaries and outputs are saved.

Bulk address data was downloaded from openaddresses and NYC open data and saved in `data/input/openaddressess_raw/`. These addresses were filtered and geocoded with Census block groups. 

From there, we group all households by block group and save each in `data/input/isp`. Each of these gzipped-JSON files is an input fed into the lookup tool collectors. 

Raw API responses from each ISP's lookup tools are saved by block group in `data/intermediary/isp`.

We merge demographic data from the 2019 American Community Survey (`data/intermediary/census`), historic HOLC grades (`data/input/redlining`) for each ISP and save them with this pattern `data/output/speed_price_{isp}.csv.gz`.

These files contain offers for each ISP in each city in our study, including addresses that were not offered Internet services and other addresses which were otherwise removed from analysis.

Everything generated for the analysis and used for a graph are saved in either `data/ouput/tables` or `data/output/figures`.

```
data
├── input
│   ├── redlining
│   ├── addresses
│   │   ├── cities.ndjson
│   │   └── open_addresses_enriched
│   ├── fcc
│   │   └── fbd_us_with_satellite_dec2020_v1.csv.gz
│   ├── census
│   │   ├── shape
│   │   └── acs5
│   └── isp
│       ├── att
│       ├── centurylink
│       ├── earthlink
│       └── verizon
├── intermediary
│   ├── fcc
│   │   └── bg_providers.csv
│   ├── census
│   │   ├── aggregated_tables_plus_features.csv.gz
│   │   └── 2019_acs_5_shapes.geojson.gz
│   └── isp
│       ├── att
│       ├── centurylink
│       ├── earthlink
│       └── verizon
└── output
    ├── speed_price_att.csv.gz
    ├── speed_price_centurylink.csv.gz    
    ├── speed_price_earthlink.csv.gz
    ├── speed_price_verizon.csv.gz
    ├── tables
    └── figures
```

## pipes
Contains scrapers for each ISP, and Census API.