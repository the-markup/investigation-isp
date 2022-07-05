# Racial and Economic Disparities in Internet Service Offers

This repository contains code to reproduce the findings featured in our story "TK" and "TK" from our series TK.

Our methodology is described in "TK".

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
These notebooks are intended to be run sequentially, but they are not dependent on one another.  If you want a quick overview of the methodology, you only need to concern yourself with the notebooks with an asterisk(*).

Run every notebook with this command:
```
make run
```
Note that when `recalculate = False` in each notebook, files that exist are not re-generated.

### 0-get-acs-data.ipynb
Collect data from the U.S. Census Bureau's American Community Survey. If you want to collect your own census data, you'll need to regiester for an [API key](https://api.census.gov/data/key_signup.html), and assign it as the environment variable `CENSUS_API_KEY`. This is not necessary as all outputs have already been calcualted and saved in this repository.

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

There are also several Python utility scripts in this directory:

### aggregators.py
Used to aggregate data and primarily produce charts in notebooks starting with "2".

### parsers.py
Parsers for JSON from lookup tools and geocodes addresses within HOLC grades.

### config.py
Contains shared variables used throughout notebooks.

### istarmap.py
Monkeypatch of `Multiprocessing.Pool`.


## Data
This directory is where inputs, intermediaries and outputs are saved.

Address data was downloaded from [OpenSources](https://opensources.io) and [NYC Open Data](https://data.cityofnewyork.us/City-Government/NYC-Address-Points/g6pj-hd8k) and grouped into block groups in `data/input/isp`. Each of these gzipped-JSON files is an input fed into the lookup tool collectors. 

Raw API responses from each ISP's lookup tools are saved by block group in `data/intermediary/isp`. The complete directory us not stored on GitHub due to space restrictions. See end of this section on how to access this data. We provide one file as an example of a block group's data on this directory.

We merge demographic data from the 2019 American Community Survey (`data/intermediary/census`), historic HOLC grades (`data/input/redlining`) for each ISP and save them with this pattern `data/output/speed_price_{isp}.csv.gz`.

These files (such as `data/output/speed_price_att.csv.gz`) contain offers for each ISP in each city in our study.

Tables and figures featured in our methodology and story can be found in `data/ouput/tables` and `data/output/figures`, respectively.

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

Some files are are too big to store on Github. You can find them hosted in the public s3 directory:
```s3://markup-investigation-isp```
These can be downloaded locally using this command (but it is not necessary to run our codes, since their outputs are already downloaded.)
```make download```
NOTE: THIS IS NOT FUNCTIONAL YET

These files that are externally hosted are mostly `input`s related to open addresses (`data/input/addresses/open_addresses_enriched` and `data/input/isp`), bulk data from government sources: the census (`data/input/census/acs5/`) and FCC (`data/input/fcc/fbd_us_with_satellite_dec2020_v1.csv.gz`), and the API responses from each ISP (`data/intermediary/isp/`. 

## pipes
Contains scrapers for each ISP, and Census API.