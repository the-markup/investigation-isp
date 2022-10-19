# How We Uncovered Disparities in Internet Deals

This repository contains code and data supporting our investigation "[Dollars to Megabits: You May Be Paying 400 Times As Much As Your Neighbor for Internet](https://themarkup.org/still-loading/2022/10/19/dollars-to-megabits-you-may-be-paying-400-times-as-much-as-your-neighbor-for-internet-service)" from the series [Still Loading](https://themarkup.org/series/still-loading).

Our methodology is described in detail in "[How We Uncovered Disparities in Internet Deals](https://themarkup.org/show-your-work/2022/10/19/how-we-uncovered-disparities-in-internet-deals)".

Please read that document to understand the context for the code and data in this repository.
The data in this repository, described in more detail below, include the results of our automated collecting of ISP offers, plus records from the U.S. Census Bureau and other sources necessary for the analysis. 

The code in this repository, also described in more detail below, demonstrates how we processed and analyzed that data. 


## Data
This directory is where inputs, intermediaries, and outputs are saved.

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

Tables and figures featured in our methodology and story can be found in `data/ouput/tables/` and `data/output/figs/`, respectively.

The `data/` directory also features `data/input/` and `data/intermediary/` files that were collected and processed to create the files in `data/output`. Their entirety is not stored in GitHub due to space restrictions. See [the section below](#Download-all-data) to access this data. 

In `data/input/`, we stored historical redlining maps that were digitized by the University of Richmond's [Mapping Inequality](https://dsl.richmond.edu/panorama/redlining/#loc=5/39.1/-94.58&text=intro) project (`data/input/redlining/`), as well as [TIGER](https://www.census.gov/cgi-bin/geo/shapefiles/index.php) shapefiles from the U.S. Census Bureau (`data/input/census/shape/`).

In `data/intermediary/` you will find aggregated data from the American Community Survey (`data/intermediary/census/`), and the FCC's Form 477 (`data/intermediary/fcc/bg_providers.csv`).

<hr>

Below, we highlight three components of the data that we believe others will find most useful: all offers collected, by ISP; all offers collected, by ISP and city; and summary data regarding the disparities observed for each city-ISP combination.

### Offers by address
The address-level internet service offers we collected are stored in the data/output/ directory, with one file per internet service provider. (For instance, `data/output/speed_price_att.csv.gz` contains the offers we collected from AT&T.).

Those files contain the following columns:

| column                      | description                                                                                                                                    |
|:----------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------|
| `address_full`                | The complete postal address of a household we searched.                                                                                        |
| `incorporated_place`          | The incorporated city that the address belongs to.                                                                                              |
| `major_city`                  | The city that the address is in.                                                                                                               |
| `state`                       | The state that the address is in.                                                                                                          |
| `lat`                         | The address’s latitude. From OpenAddresses or NYC Open Data.                                          |
| `lon`                         | The address’s longitude. From OpenAddresses or NYC Open Data.                                           |
| `block_group`                 | The Census block group of the address, as of 2019. From the Census Geocoder API based on `lat` and `lon`.                                                                                              |
| `collection_datetime`         | The Unix timestamp that the address was used to query the provider's website.                                                                   |
| `provider`                    | The internet service provider.                                                                                                                  |
| `speed_down`                  | Cheapest advertised download speed for the address.                                                                                            |
| `speed_up`                    | Cheapest advertised upload speed for the address.                                                                                              |
| `speed_unit`                  | The unit of speed. This is always in megabits per second (Mbps).                                                                                |
| `price`                       | The cost in USD of the cheapest advertised internet plan for the address.                                                                       |
| `technology`                  | The kind of technology (fiber or non-fiber) used to serve the cheapest internet plan.                                                           |
| `package`                     | The name of the cheapest internet plan.                                                                                                         |
| `fastest_speed_down`          | The advertised download speed of the fastest package. This is usually the same as the cheapest plan if the `speed_down` is less than 200 Mbps. |
| `fastest_speed_price`         | The advertised upload speed of the fastest internet package for the address.                                                                   |
| `fn`                          | The name of the file of API responses where this record was parsed from. To be used for trouble shooting. API responses are hosted externally in AWS s3.                                                                       |
| `redlining_grade`             | The redlining grade, merged from Mapping Inequality based on the `lat` and `lon` of the adddress.                                              |
| `race_perc_non_white`         | The percentage of people of color (not non-Hispanic White) in the addresse's Census block group expressed as a proportion. Sourced from the 2019 5-year American Community Survey.  |
| `median_household_income `    | The median household income in the addresses' Census block group. Sourced from the 2019 5-year American Community Survey                       |
| `income_lmi`                  | `median_household_income` divided by the city median household income (sourced from U.S. Census Bureau).                                                                         |
| `income_dollars_below_median` | City median household income minus the `median_household_income`.                                                                              |
| `ppl_per_sq_mile`             | People per square mile is used to determine population density. Sourced from 2019 TIGER shape files from the U.S. Census Bureau.               |
| `n_providers`                 | The number of other wired competitors in the addresses' Census block group. Sourced from FCC Form 477.                                              |
| `internet_perc_broadband`     | The percentage of the population that is already subscriped to broadband in an addresses' Census block group expressed as a proportion.                                  |


This dataset was created in `notebooks/1-process-offers.ipynb`. 

You can find a similar file for inidividuals cities, [below](#Localized-datasets).

### Localized datasets
In addition to the ISP-level offer files described above, we have generated similar data files for each ISP-city combination, listed and linked below. For column definitions, see the section above.

Do you want to write a local story based on the data we collected? We wrote a [story recipe](https://themarkup.org/story-recipes/2022/10/19/how-to-investigate-if-low-income-least-white-neighborhoods-are-offered-the-worst-internet-deals-in-your-city) guide to help you do that. 

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


### Offer Maps
To view an interactive address-level map for the cities in our investigation, you can download the [Kepler.gl](https://kepler.gl/) maps for each provider.

Click any of the links below to view a map for the provider you are interested in.

- Map for [AT&T](https://markup-public-data.s3.amazonaws.com/isp/at%26t-kepler.gl.html)
- Map for [CenturyLink](https://markup-public-data.s3.amazonaws.com/isp/centurylink-kepler.gl.html)
- Map for [EarthLink](https://markup-public-data.s3.amazonaws.com/isp/earthlink-kepler.gl.html)
- Map for [Verizon](https://markup-public-data.s3.amazonaws.com/isp/verizon-kepler.gl.html)

Now you can use the search bar to quick-travel to specific addresses or cities. If you know the areas, this will be immediately useful. However, if you would like an overlay of any socioeconomic factor in our investigation (median household income, the percentage of non-Hispanic White residents in the area, or redlining grades) we can produce them by request.

These maps should be viewed alongside summaries of how speeds vary across each city and between areas.

Please refer to the [methodology](https://themarkup.org/show-your-work/2022/10/19/how-we-uncovered-disparities-in-internet-deals) or this summary [file](#summary-of-disparities) for that information.

### Summary of Disparities
The `data/output/tables/table1_disparities_by_city.csv` file summarizes the disparities we observed for each city-ISP combination, and represents the core of our findings.

It contains the following:


| column                | description                                                                                                                               |
|:----------------------|:------------------------------------------------------------------------------------------------------------------------------------------|
| `major_city`           | The city analyzed.                                                                                                                      |
| `state`                 | The state that the city is in.                                                                                                             |
| `isp`                   | The internet service provider.                                                                                                             |
| `uniform_speed`         | Whether the city had virtually the same speeds offered; we omit these cities from out disparate outcome analysis.                         |
| `income_disparity`      | Whether we identifed a disparity between lower- and upper- income areas.                                                                         |
| `pct_slow_lower_income` | Percentage of addresses in lower-income areas that were offered slow speeds (>25 Mbps) expressed as a proportion.                                                   |
| `pct_slow_upper_income` | Percentage of addresses in upper-income areas that were offered slow speeds expressed as a proportion.                                                               |
| `income_pct_pt_diff`    | The percentage point difference between income groups offered slow speeds, if this was at or greater than 5, `income_disparity` is `True` |
| `flag_income`           | In cases where we did not analyze this city for income-based disparities, the reason why. See our methodology document for more details.                               |
| `race_disparity`        | Whether we identified a disparity between the most-White and least-White areas.                                |
| `pct_slow_least_white`  | Percentage of addresses in least-White areas that were offered slow speeds expressed as a proportion.                                                               |
| `pct_slow_most_white`   | Percentage of addresses in most-White areas that were offered slow speeds expressed as a proportion.                                                                 |
| `race_pct_pt_diff`      | The percentage point difference in slow speed offers between the most-White and least-White areas. If this was at or greater than 5, `race_disparity` is `True`.                                                   |
| `flag_race`             | In cases where we did not analyze this city based on racial or ethnic groups, the reason why. See our methodology document for more details.                                                                    |
| `redlining_disparity`   | Whether we identified a disparity between HOLC-rated A/B vs. D areas.                                                                                   |
| `pct_slow_d_rated`      | Percentage of addresses in historically D-rated areas that were offered slow speeds expressed as a proportion.                                                      |
| `pct_slow_ab_rated`     | Percentage of addresses in historically A and B-rated areas that were offered slow speeds expressed as a proportion.                                                |
| `redlining_pct_pt_diff` | The percentage point difference in slow speed offers between historically D-rated and A/B-rated  neighborhoods. If this was at or greater than 5, `redlining_disparity` is `True`.                                            |
| `flag_redlining`        | In cases where we did not analyze this city with redlining grades, the reason why. See our methodology document for more details.                                                                                    |

This file was generated in `notebooks/3-statistical-tests-and-regression.ipynb`.

### Download all data
Certain data files were too large to host on GitHub but have been uploaded to Amazon Web Services' Simple Storage Service (Amazon S3):

`s3://markup-public-data/isp/input.tar.xz` (~7.7 GB uncompressed) contains open source addresses (`data/input/addresses/open_addresses_enriched/` and `data/input/isp/`), bulk data from government sources: the  U.S. Census Bureau (`data/input/census/acs5/`) and FCC Form 477 (`data/input/fcc/fbd_us_with_satellite_dec2020_v1.csv.gz`). 

`s3://markup-public-data/isp/isp-intermedairy.tar.xz` (~5.7 GB uncompressed) and contains API responses from each ISP (`data/intermediary/isp/`) appended to the geographic data we pulled in above.

For your convenience we have included a command-line script to download these files: 
```
data/download_external_data.sh
```


## Re-running Notebooks
### Python
Make sure you have Python 3.8+ installed. We used [Miniconda](https://docs.conda.io/en/latest/miniconda.html) to create a Python 3.8 [virtual environment](https://stackoverflow.com/a/56713819).


Install the Python packages with pip:<br>
```
pip install -r requirements.txt
```

The notebooks are intended to be run sequentially, but can also be run independently.
To run all notebooks in sequence, you can use the command 
```nbexec notebooks```

Note that when `recalculate = False` in each notebook, files that exist are not regenerated.

## Notebooks
The Python/Jupyter notebooks in this repository’s notebooks/ directory demonstrate the steps we took to process and analyze the data we collected. If you want a quick overview of the main methodology, you can skip directly to 3-statistical-tests-and-regression.ipynb.

### 0-get-acs-data.ipynb
This notebook collects data from the U.S. Census Bureau's American Community Survey. If you want to re-fetch this data, you'll need to register for an [API key](https://api.census.gov/data/key_signup.html) and assign it as the environment variable `CENSUS_API_KEY`. Otherwise, this is not necessary, as all outputs we used in this analysis are already saved in this repository.

### 1-process-offers.ipynb
This notebook parses and preprocesses the JSON responses for offers collected from each ISP's service lookup tools. The functions that parse each API response can be found in `noteobooks/parsers.py`.

See examples of the API response JSON in `data/intermediary/isp/`, or [download](#Download-all-data) all the data.

### 2a-att-reports.ipynb / 2b-verizon-reports.ipynb / 2c-centurylink-reports.ipynb / 2d-earthlink-reports.ipynb
An overview of offers by each ISP. This contains breakdowns for each city served by the ISP by income level, race/ethnicity, and historical redlining grades. 

The code to produce the charts in these notebooks can be found in `notebooks/aggregators.py`

### 3-statistical-tests-and-regression.ipynb
This notebook contains the bulk of our analyses. In it, we test for disparities in slow speed offers by income-level, race/ethnicity, and historical redlining grades.

This is also where we use logistic regression to adjust for business factors to see if accounting for them would eliminate the disparities we observed.

### 4-verizon-spotcheck.ipynb
This notebook examines Verizon's price changes, addressed in the Limitations section of the methodology document.

### 5-find-closest-fiber-address.ipynb
This notebook uses scikit-learn's BallTree algorithm to find the closest address with blazing fast speeds (≥200 Mbps) for any address in a city. We used the results to create the topper graphic in the main story.
