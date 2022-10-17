# Uncovering Disparities in Internet Service Offers

This repository contains code to reproduce the findings featured in our story "[Dollars to Megabits: You May Be Paying 400 Times as Much as your Neighbor for Internet](https://themarkup.org/still-loading)" from our series [Still Loading](https://themarkup.org/still-loading).

Our methodology is described in "[How We Uncovered Disparities in Internet Deals Offered to Disadvantaged Communities](https://themarkup.org/still-loading)".

Data that we collected and analyzed are in the `data` folder.

Jupyter notebooks used for data collection, preprocessing and analysis are in the `notebooks` folder.


## Data
This directory is where inputs, intermediaries and outputs are saved.

Here is an overview of how the directory is organized:

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
    ├── by_city
    ├── figs
    └── tables
```

A [summary](https://github.com/the-markup/investigation-isp/blob/main/data/output/tables/table1_cities_ranked_by_categories.csv) of disparties for each city and provider across socioeconomic categories can be found in `data/output/tables/table1_cities_ranked_by_categories`.

Address-level Internet service plans for each provider are stored in the `data/output/` directory, the file for AT&T is called `data/output/speed_price_att.csv.gz`.

A data dictionary for this file:

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
| fn                          | The name of the file of API responses where this record was parsed from.                                                                       |
| redlining_grade             | The redlining grade, merged from Mapping Inequality based on the `lat` and `lon` of the adddress.                                              |
| race_perc_non_white         | The percentage of people of color (not non-Hispanic White) in the Census block group. Sourced from the 2019 5-year American Community Survey.  |
| income_lmi                  | `median_household_income` divided by the city median household income.                                                                         |
| ppl_per_sq_mile             | People per square mile is used to determine population density. Sourced from 2019 TIGER shape files from the U.S. Census Bureau.               |
| n_providers                 | The number of other competitors in the addresses  Census block group. Sourced from FCC form 477.                                               |
| income_dollars_below_median | City median household income minus the `median_household_income`.                                                                              |
| internet_perc_broadband     | The percentage of the population that is already subscriped to broadband in an addresses' Census block group.                                  |
| median_household_income     | The median household income in the addresses' Census block group. Sourced from the 2019 5-year American Community Survey                       |


You can find a similar file for inidividuals cities, [below](#Localized-datasets).

Tables and figures featured in our methodology and story can be found in `data/ouput/tables` and `data/output/figs`, respectively.

The `data/` directory also features `data/input/` and `data/intermediary/` for files that were collected and processed to create the `data/output` files mentioned above. The complete directory is not stored on GitHub due to space restrictions. See [end of this section](#Download-all-data) on how to access this data. 

Address data was downloaded from [OpenSources](https://opensources.io) and [NYC Open Data](https://data.cityofnewyork.us/City-Government/NYC-Address-Points/g6pj-hd8k) and grouped and into block groups in `data/input/isp` as [gzip](https://www.gzip.org/)ped-[GeoJSON](https://geojson.org/) files. 

These records get fed into lookup tools for each ISP's webszite. Raw API responses from lookup tools are saved by block group in `data/intermediary/isp`. 

We provide one file as an example of a block group's data on this directory.

We collected demographic data from the 2019 American Community Survey (`data/intermediary/census`), historic redlining grades (`data/input/redlining`) from University of Richmond's [Mapping Inequality](https://dsl.richmond.edu/panorama/redlining/#loc=5/39.1/-94.58&text=intro) project.


### Download all data
You can find all of the other input and intermediary files hosted externally.

You can find them hosted as xz-compressed archives in AWS S3 here:
```
s3://markup-public-data/isp/isp-input.tar.xz
s3://markup-public-data/isp/isp-intermedairy.tar.xz
```

These can be downloaded locally using `data/download_external_data.sh`.

`s3://markup-public-data/isp/input.tar.xz` is about 7.7 GB compressed and contains open source addresses (`data/input/addresses/open_addresses_enriched` and `data/input/isp`), bulk data from government sources: the census (`data/input/census/acs5/`) and FCC (`data/input/fcc/fbd_us_with_satellite_dec2020_v1.csv.gz`). 

`s3://markup-public-data/isp/isp-intermedairy.tar.xz` is about 5.7 GB and contains API responses from each ISP (`data/intermediary/isp/`) appended to the geographic data we pulled in above.

### Localized datasets
Do you want to write a local story based on the data we collected?

We wrote a story recipe guide to help do that, and below is a list of each city we collected, and a link to the street-level data for each. Note that the data has been categorized based on an addresses' surrounding socioeconomics.

 - Albuquerque, N.M. ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/albuquerque_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/albuquerque_earthlink_plans.csv)) 
 - Atlanta, Ga. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/atlanta_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/atlanta_earthlink_plans.csv)) 
 - Billings, Mont. ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/billings_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/billings_earthlink_plans.csv)) 
 - Boise, Idaho ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/boise_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/boise_earthlink_plans.csv)) 
 - Charleston, S.C. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/charleston_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/charleston_earthlink_plans.csv)) 
 - Charlotte, N.C. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/charlotte_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/charlotte_earthlink_plans.csv)) 
 - Cheyenne, Wyo. ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/cheyenne_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/cheyenne_earthlink_plans.csv)) 
 - Chicago, Ill. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/chicago_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/chicago_earthlink_plans.csv)) 
 - Columbus, Ohio ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/columbus_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/columbus_earthlink_plans.csv)) 
 - Denver, Colo. ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/denver_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/denver_earthlink_plans.csv)) 
 - Des Moines, Iowa ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/des%20moines_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/des%20moines_earthlink_plans.csv)) 
 - Detroit, Mich. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/detroit_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/detroit_earthlink_plans.csv)) 
 - Fargo, N.D. ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/fargo_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/fargo_earthlink_plans.csv)) 
 - Houston, Texas ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/houston_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/houston_earthlink_plans.csv)) 
 - Huntsville, Ala. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/huntsville_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/huntsville_earthlink_plans.csv)) 
 - Indianapolis, Ind. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/indianapolis_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/indianapolis_earthlink_plans.csv)) 
 - Jackson, Miss. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/jackson_at&t_plans.csv)) 
 - Jacksonville, Fla. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/jacksonville_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/jacksonville_earthlink_plans.csv)) 
 - Kansas City, Mo. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/kansas%20city_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/kansas%20city_earthlink_plans.csv)) 
 - Las Vegas, Nev. ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/las%20vegas_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/las%20vegas_earthlink_plans.csv)) 
 - Little Rock, Ark. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/little%20rock_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/little%20rock_earthlink_plans.csv)) 
 - Los Angeles, Calif. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/los%20angeles_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/los%20angeles_earthlink_plans.csv)) 
 - Louisville, Ky. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/louisville_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/louisville_earthlink_plans.csv)) 
 - Milwaukee, Wis. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/milwaukee_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/milwaukee_earthlink_plans.csv)) 
 - Minneapolis, Minn. ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/minneapolis_centurylink_plans.csv)) 
 - Nashville, Tenn. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/nashville_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/nashville_earthlink_plans.csv)) 
 - New Orleans, La. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/new%20orleans_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/new%20orleans_earthlink_plans.csv)) 
 - Newark, N.J. ([Verizon](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/newark_verizon_plans.csv)) 
 - Oklahoma City, Okla. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/oklahoma%20city_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/oklahoma%20city_earthlink_plans.csv)) 
 - Omaha, Neb. ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/omaha_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/omaha_earthlink_plans.csv)) 
 - Phoenix, Ariz. ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/phoenix_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/phoenix_earthlink_plans.csv)) 
 - Portland, Ore. ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/portland_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/portland_earthlink_plans.csv)) 
 - Salt Lake City, Utah ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/salt%20lake%20city_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/salt%20lake%20city_earthlink_plans.csv)) 
 - Seattle, Wash ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/seattle_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/seattle_earthlink_plans.csv)) 
 - Sioux Falls, S.D. ([CenturyLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/sioux%20falls_centurylink_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/sioux%20falls_earthlink_plans.csv)) 
 - Virginia Beach, Va. ([Verizon](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/virginia%20beach_verizon_plans.csv)) 
 - Washington ([Verizon](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/washington_verizon_plans.csv)) 
 - Wichita, Kan. ([AT&T](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/wichita_at&t_plans.csv), [EarthLink](https://github.com/the-markup/investigation-isp/blob/main/data/output/by_city/wichita_earthlink_plans.csv)) 

To view an interactive address-level map for any of these cities, you can download the [Kepler.gl](https://https://kepler.gl/) maps for each provider.

Click the link to download an HTML file for the provider you are interested in, and open the HTML file in a web browser. (You can do this by dragging the file into the browser.)

- Map for [AT&T](https://markup-public-data.s3.amazonaws.com/isp/at%26t-kepler.gl.html)
- Map for [CenturyLink](https://markup-public-data.s3.amazonaws.com/isp/centurylink-kepler.gl.html)
- Map for [EarthLink](https://markup-public-data.s3.amazonaws.com/isp/earthlink-kepler.gl.html)
- Map for [Verizon](https://markup-public-data.s3.amazonaws.com/isp/verizon-kepler.gl.html)

Once the file is open in a browser, use the search bar for specific addresses or cities to quick travel. If you would like an overlay of any socioeconomic factor, we can produce them by request.

These maps should be viewed with summaries of how speeds vary across each city. Please refer to the [methodology]() or this [file](https://github.com/the-markup/investigation-isp/blob/main/data/output/tables/table1_cities_ranked_by_categories.csv) to how large disparities are between areas of the same city.


## Installation
### Python
Make sure you have Python 3.8+ installed, we used [Miniconda](https://docs.conda.io/en/latest/miniconda.html) to create a Python 3.8 virtual environment.


Install the Python packages with pip:<br>
```
pip install -r requirements.txt
```

## Notebooks
These notebooks are intended to be run sequentially, but they are not dependent on one another.  If you want a quick overview of the methodology, you only need to concern yourself with `3-statistical-tests-and-regression.ipynb`.

To run all notebooks you can use the command `nbexec notebooks`.

Note that when `recalculate = False` in each notebook, files that exist are not re-generated.

### 0-get-acs-data.ipynb
Collect data from the U.S. Census Bureau's American Community Survey. If you want to collect your own census data, you'll need to regiester for an [API key](https://api.census.gov/data/key_signup.html), and assign it as the environment variable `CENSUS_API_KEY`. To re-create out results, this is not necessary, as all outputs we used in this analysis are saved in this repository.

### 1-process-offers.ipynb
Parses and preprocesses the JSON responses for offers collected from ISP's service lookup tools. The functions that parse each response can be found in `parsers.py`.

### 2a-att-reports.ipynb
An overview of offers by the ISP AT&T. This contains breakdowns cities served by AT&T by income-level, race/ethnicity, and historical redlining grades. The same notebooks exist for Verizon (`2b-verizon-reports.ipynb`), CenturyLink (`2c-centurylink-reports.ipynb`), and EarthLink (`2d-earthlink-reports.ipynb`).

The code to produce these charts is in `analysis.py`

### 3-statistical-tests-and-regression.ipynb
The bulk of analysis is in this notebook. 

This is where we test for disparities between social groups that get offered the worst deals (download speeds below 25 Mbps for the same price as faster speeds in the same city).

This is also where we use logistic regression to adjust for business factors to see if accounting for them would eliminate the disparities we observed.

### 4-verizon-spotcheck.ipynb
A look into Verizon's price changes for limitations in the methdology.

### 5-find-closest-fiber-address.ipynb
Using scikit-learn's `BallTree` algorithim to find the closest address with blazing fast speeds (≥200 Mbps) for any address in a city. We used this to create the topper graphic in the main story.

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



