## Data for AP

This directory has the cheapest internet plans for AT&T, Verizon, CenturyLink and EarthLink.

Address-level data is available in gzipped csv files for each provider, and split by city and providers in `by_city`.

Each file has the following columns:


| column                      | description                                                                                                                                                          |
|:----------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| address_full                | The complete postal address of a household we searched.                                                                                                              |
| incorporated_place          | The incorporated city that the address belongs to                                                                                                                    |
| major_city                  | The city that the address is in.                                                                                                                                     |
| state                       | The state the that the address is in.                                                                                                                                |
| lat                         | The latitudinal coordinate that the address is in.                                                                                                                   |
| lon                         | The Longitudinal coorindate that the address is in.                                                                                                                  |
| block_group                 | The census block group of the address as of 2019.                                                                                                                    |
| collection_datetime         | The unix timestamp that the address was used to query the provider's website                                                                                         |
| provider                    | The internet service provider                                                                                                                                        |
| speed_down                  | Cheapest advertised download speed for the address.                                                                                                                  |
| speed_up                    | Cheapest advertised upload speed for the address.                                                                                                                    |
| speed_unit                  | The unit of speed, should always be Megabits per second (Mbps).                                                                                                      |
| price                       | The cost in USD of the cheapest advertised internet plan for the address                                                                                             |
| technology                  | The kind of technology (Fiber or non-Fiber) used to serve the cheapest internet plan                                                                                 |
| package                     | The name of the cheapest internet plan                                                                                                                               |
| fastest_speed_down          | The advertised download speed of the fastest package. This is usually the same as the cheapest plan if the `speed_down` is less than 200 Mbps.                       |
| fastest_speed_price         | The advertised upload speed of the fastest internet package for the address.                                                                                         |
| speed_down_bins             | How we categorized addresses by `speed_down`.                                                                                                                        |
| redlining_grade             | The redlining grade, merged from Mapping Inequality based on the `lat` and `lon` of the adddress.                                                                    |
| race_perc_non_white         | The percentage of the population in the Census block group that is non-White. This includes hispanic Whites. Sourced from the 2019 5-year American Community Survey. |
| race_quantile               | Our classification of relative race and ethnicity in the city using quartiles cut from `race_per_non_white`.                                                         |
| median_household_income     | The median household income in the addresses' Census block group. Sourced from the 2019 5-year American Community Survey                                             |
| income_dollars_below_median | City median household income minus the `median_household_income`.                                                                                                    |
| income_level                | Our classification of relative income level in the city using quartiles cut from `median_household_income`.                                                          |
| ppl_per_sq_mile             | People per square mile is used to determine population density. Sourced from 2019 TIGER shape files from the U.S. Census Bureau.                                     |
| n_providers                 | The number of other competitors in the addresses` Census block group. Sourced from FCC form 477.                                                                     |
| internet_perc_broadband     | The percentage of the population that is already subscriped to broadband in an addresses' Census block group.                                                        |
| contract_provider           | Only used for `provider` = EarthLink. Used to denote who EarthLink leases infrastructure from.                                                                       |