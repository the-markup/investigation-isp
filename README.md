# Racial and Economic Disparities in Internet Service Offers

This repository contains code to reproduce the findings featured in our story "TK" from our series Still Loading.

Our methodology is described in "How We Investigated Internet Services Offered to Disadvantaged Communities".

Data that we collected and analyzed are in the `data` folder.

Jupyter notebooks used for data collection, preprocessing and analysis are in the `notebooks` folder.


## Installation
### Python
Make sure you have Python 3.8+ installed, we used [Miniconda](https://docs.conda.io/en/latest/miniconda.html) to create a Python 3.8 virtual environment.

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
Collect data from the U.S. Census Bureau's American Community Survey. If you want to collect your own census data, you'll need to regiester for an [API key](https://api.census.gov/data/key_signup.html), and assign it as the environment variable `CENSUS_API_KEY`. To re-create out results, this is not necessary, as all outputs we used in this analysis are saved in this repository.

### 1-process-offers.ipynb
Parses and preprocesses the JSON responses for offers collected from ISP's service lookup tools. The functions that parse each response can be found in `parsers.py`.

### 2a-att-reports.ipynb
An overview of offers by the ISP AT&T. This contains breakdowns cities served by AT&T by income-level, race/ethnicity, and historical redlining grades. The same notebooks exist for Verizon (`2b-verizon-reports.ipynb`), CenturyLink (`2c-centurylink-reports.ipynb`), and EarthLink (`2d-earthlink-reports.ipynb`).

The code to produce these charts is in `analysis.py`

### 3-statistical-tests-and-regression.ipynb *
The bulk of analysis is in this notebook. 

This is where we test for disparities between social groups that get offered the worst deals (download speeds below 25 Mbps for the same price as faster speeds in the same city).

This is also where we use logistic regression to adjust for business factors to see if accounting for them would eliminate the disparities we observed.

### 4-verizon-spotcheck.ipynb
A look into Verizon's price changes for limitations in the methdology.

### 5-city-template.ipynb
Used to generate a high-level summary of Internet offers for every city in our investigation. This is a work in progress


<hr>

There are also several Python utility scripts in this directory:

### aggregators.py
Used to aggregate data and produce charts in notebooks starting with "2".

### parsers.py
Parses JSON from lookup tools and geocodes addresses within HOLC grades. See examples of the JSON in `data/intermediary/isp`, or [download](#Download-all-data) all the data.

### config.py
Contains shared variables used throughout notebooks.

### istarmap.py
Monkeypatch of `Multiprocessing.Pool` so we can run statsmodels using multiple cores. Used in `3-statistical-tests-and-regression.ipynb`


## Data
This directory is where inputs, intermediaries and outputs are saved.


Address data was downloaded from [OpenSources](https://opensources.io) and [NYC Open Data](https://data.cityofnewyork.us/City-Government/NYC-Address-Points/g6pj-hd8k) and grouped and compressed into block groups in `data/input/isp`. 

We use these [gzip](https://www.gzip.org/)ped-[GeoJSON](https://geojson.org/) files to sample addresses to search from each ISP's lookup tool. 

Raw API responses from lookup tools are saved by block group in `data/intermediary/isp`. The complete directory us not stored on GitHub due to space restrictions. See [end of this section](#Download-all-data) on how to access this data. We provide one file as an example of a block group's data on this directory.

We merge demographic data from the 2019 American Community Survey (`data/intermediary/census`), historic HOLC grades (`data/input/redlining`) for each ISP and save them with this pattern `data/output/speed_price_{isp}.csv.gz`.

These files (such as `data/output/speed_price_att.csv.gz`) contain offers for each ISP in each city in our study.

Here's a data dictionary for offers.
| column                      | description                                                                                                                                    |
|:----------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------|
| address_full                | The complete postal address of a household we searched.                                                                                        |
| incorporated_place          | The incorporated city that the address belongs to                                                                                              |
| major_city                  | The city that the address is in.                                                                                                               |
| state                       | The state the that the address is in.                                                                                                          |
| lat                         | The latitudinal coordinate that the address is in.                                                                                             |
| lon                         | The Longitudinal coorindate that the address is in.                                                                                            |
| block_group                 | The census block group of the address as of 2019.                                                                                              |
| collection_datetime         | The unix timestamp that the address was used to query the provider's website                                                                   |
| provider                    | The internet service provider                                                                                                                  |
| speed_down                  | Cheapest advertised download speed for the address.                                                                                            |
| speed_up                    | Cheapest advertised upload speed for the address.                                                                                              |
| speed_unit                  | The unit of speed, should always be Megabits per second (Mbps).                                                                                |
| price                       | The cost in USD of the cheapest advertised internet plan for the address                                                                       |
| technology                  | The kind of technology (Fiber or non-Fiber) used to serve the cheapest internet plan                                                           |
| package                     | The name of the cheapest internet plan                                                                                                         |
| fastest_speed_down          | The advertised download speed of the fastest package. This is usually the same as the cheapest plan if the `speed_down` is less than 200 Mbps. |
| fastest_speed_price         | The advertised upload speed of the fastest internet package for the address.                                                                   |
| fn                          | TK                                                                                                                                             |
| redlining_grade             | The redlining grade, merged from Mapping Inequality based on the `lat` and `lon` of the adddress.                                              |
| geoid                       | The Census bureau's GEOID for the address                                                                                                      |
| race_perc_non_white         | The percentage of people of color (not non-Hispanic White) in the Census block group. Sourced from the 2019 5-year American Community Survey.  |
| income_lmi                  | `median_household_income` divided by the city median household income.                                                                         |
| ppl_per_sq_mile             | People per square mile is used to determine population density. Sourced from 2019 TIGER shape files from the U.S. Census Bureau.               |
| n_providers                 | The number of other competitors in the addresses` Census block group. Sourced from FCC form 477.                                               |
| income_dollars_below_median | City median household income minus the `median_household_income`.                                                                              |
| internet_perc_broadband     | The percentage of the population that is already subscriped to broadband in an addresses' Census block group.                                  |
| median_household_income     | The median household income in the addresses' Census block group. Sourced from the 2019 5-year American Community Survey                       |
| income_level                | How we categorized income. We binned `median_household_income` into quartiles                                                                  |
| speed_down_bins             | How we categorized addresses by `speed_down`.                                                                                                  |
| race_quantile               | How we categorized race and ethnicity. We binned `race_perc_non_white` into quartiles.                                                         |
| is_slow                     | `True` if `speed_down` is below 25 Mbps.                                                                                                       |

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

### Download all data
Some files are are too big to store on Github. You can find them hosted in the public s3 directory:
```s3://markup-investigation-isp```
These can be downloaded locally using this command (but it is not necessary to run our codes, since their outputs are already downloaded.)
```make download```
NOTE: THIS IS NOT FUNCTIONAL YET

Externally hosted files are mostly `input`s related to open addresses (`data/input/addresses/open_addresses_enriched` and `data/input/isp`), bulk data from government sources: the census (`data/input/census/acs5/`) and FCC (`data/input/fcc/fbd_us_with_satellite_dec2020_v1.csv.gz`), and the API responses from each ISP (`data/intermediary/isp/`. 

## pipes
Contains scrapers for each ISP, and Census API.