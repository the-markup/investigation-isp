import numpy as np
import pandas as pd
from pandas.api.types import CategoricalDtype
from matplotlib.lines import Line2D
import matplotlib.ticker as mtick
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
pd.options.mode.chained_assignment = None 

from config import (
    speed_labels, 
    income_labels, 
    redlininggrade2name, 
    race_labels
)

RACE_COL = 'race_perc_non_white'

def aspirational_quartile(series, labels):
    desc = series.describe()
    bins = []
    sections = ['min', '25%','50%', '75%', 'max']
    for sect in sections:
        boundry = desc[sect]
        if len(bins) != 0:
            if bins[-1] == boundry:
                bins[-1] = bins[-1] - .001
        bins.append(boundry)
    return pd.cut(
        series,
        bins=bins,
        labels=labels,
        include_lowest=True
    )


## For all ISP analysis
def filter_df(fn, isp):
    """
    Filters out no service offers, and cities which we can't analyze
    """
    df = pd.read_csv(fn)
    df = df[df.speed_down != 0]
    df = bucket_and_bin(df)
    df['isp'] = isp
    if isp == 'Verizon':
        df.price = df.price.replace({40: 39.99, 49.99: 39.99})
        df = df[df.price == 39.99]
        nyc_cities = ['new york', 'brooklyn', 'queens', 'staten island', 'brooklyn', 'bronx']
        nyc = []
        for city, _df in df.groupby('major_city'):
            if city in nyc_cities:
                nyc.extend(_df.to_dict(orient='records'))
        nyc = pd.DataFrame(nyc)
        nyc['major_city'] = 'new york city'
        
        # add NYC
        df = df[~df.major_city.isin(nyc_cities)]
        df = df.append(nyc)
        
    elif isp == 'EarthLink':
        df = df[df.contract_provider.isin(['AT&T', 'CenturyLink'])]
        
    homogenous_cities = {'bridgeport', 'wilmington'}
    df = df[~df.major_city.isin(homogenous_cities)]
    return df


def bucket_and_bin(df, limitations=False):
    """This is how we wrangle our data"""
    # These are our IVs
    # https://www.federalreserve.gov/consumerscommunities/cra_resources.htm
    df.loc[df['income_lmi'] < -100, 'income_lmi'] = None   
    df.loc[df['median_household_income'] == -666666666.0, 'median_household_income'] = None  
    
    df['income_level'] = aspirational_quartile(
        df['median_household_income'],
        labels=['Low', 'Middle-Lower', 'Middle-Upper', 'Upper Income'],
    ) 
    
    df['speed_down_bins'] = pd.cut(
        df.speed_down, 
        [-1, 0.00001, 25,  100, 200, 100000],
        labels=speed_labels,
        right=False
    )
 
    try:
        df['race_quantile'] = aspirational_quartile(
            df.race_perc_non_white, 
            labels=race_labels
        )
        
    except:
        print(df.major_city.iloc[0])
    
    if limitations:
        df['race_quantile'] = pd.cut(df['race_perc_non_white'], 
                                     bins=[0, .4, .6, 1],
                                     labels=['most white', 'integrated', 'least white'])
        
        df['income_level'] = pd.cut(df['income_lmi'], 
                                    bins=[-1e10, .5, 1.2, 1e10],
                                    labels=['Low', 'Middle', 'Upper Income'])
    
    # this is our DV
    df['is_slow'] = df.apply(
        lambda x: 1 if x['speed_down_bins'] == "Slow (<25 Mbps)" else 0, 
        axis=1
    )
   
    return df

def unserved(df, isp='AT&T', height=5):
    # percentage of households unserved
    city2unserved = {}
    for city, _df in df.groupby('major_city'):
        city2unserved[city] = len(_df[_df.speed_down == 0]) / len(_df)
    
    to_plot = pd.Series(city2unserved).sort_values() * 100
    ax = to_plot.plot(
        kind='barh', figsize=(6, height), 
        width=.5,
        color = 'black',  edgecolor =None,
    )
    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Only show ticks on the left and bottom spines
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

    ax.set_ylabel("")
    ax.set_xlabel("Percentage of unserved housholds")

    plt.title(f'Percentage of unserved households by {isp}',
                 loc='left', y=1.025, size=12.5)

def speed_breakdown(df, location='National', isp='AT&T'):
    categories = set(df.speed_down_bins.unique())
    legend_elements = [Line2D([0], [0], marker='o', color='w', 
                          label=label, markerfacecolor=c, markersize=10)
                   for label, c in speed_labels.items() if label in categories][::-1]   
    to_plot =  pd.DataFrame(df.speed_down_bins.value_counts(normalize=True).sort_index())
    ax = to_plot.T.plot.barh(
        stacked=True, figsize=(8, 2.6), 
        color = [speed_labels.get(l) for l in to_plot.index]
    )
    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Only show ticks on the left and bottom spines
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    
    ax.axes.yaxis.set_visible(False)
    
    ax.set_ylabel("")
    ax.set_xlabel("Percentage of residential Internet offers")
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))


    ax.legend(handles=legend_elements[::-1],
              loc='lower left', 
              bbox_to_anchor= (-0.025, 1.0), 
              ncol=5,
              handletextpad=0.0,
              labelspacing=0, 
              borderaxespad=.1, 
              borderpad=0.1,
              frameon=False,
              prop={'size': 9.2})

    plt.title(f'{isp} {location} Residential Download Speeds (N={len(df):,})',
              loc='left', y=1.075, size=15.5)
    plt.show()


def race(df, isp='AT&T', location='National'):
    categories = set(df.speed_down_bins.unique())
    legend_elements = [Line2D([0], [0], marker='o', color='w', 
                          label=label, markerfacecolor=c, markersize=10)
                   for label, c in speed_labels.items() if label in categories][::-1]   
    
    df['color'] = df['speed_down_bins'].apply(lambda x: speed_labels.get(x))
    
    df = df[~df.race_perc_non_white.isnull()]
    to_plot = (df.groupby('race_quantile').speed_down_bins
          .value_counts(normalize=True)
          .sort_index() * 100 ).unstack()[[
        c for c in speed_labels.keys() if c in categories
    ]][::-1]
    ax = to_plot.plot(
        kind='barh', stacked=True, figsize=(8, 5), 
        color = [v for k,v in speed_labels.items() if k in categories],
    )
    bin_counts = df.race_quantile.value_counts().sort_index()[::-1]

    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Only show ticks on the left and bottom spines
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

    ax.set_ylabel("")
    ax.set_xlabel("Percentage of residential Internet offers")

    ax.legend(handles=legend_elements[::-1],
              loc='lower left', 
              bbox_to_anchor= (-0.025, 1.015), 
              ncol=5,
              handletextpad=0.0,
              labelspacing=0, 
              borderaxespad=.1, 
              borderpad=0.1,
              frameon=False,
              prop={'size': 9.2})

    plt.title(f'{isp} {location} Residential Download Speeds by \n'
              f'Block Group Racial and Ethnic Demographics (N={len(df):,})',
              loc='left', y=1.075, size=15.5)
    # label counts
    rects = ax.patches
    heights = sorted(set([r.get_y() for r in rects]))
    for label, h in zip(bin_counts, heights):
        ax.text(101, h+.1, f'N={label:,}', ha='left', va='bottom')
    
    plt.text(0, -1.2, 
             f"Race and ethnicity bucketed into quartiles based on percentage of non-hispanic white residents.",
            horizontalalignment='left',
            verticalalignment='center',);

    plt.show()
    
def income(df, isp="AT&T", location="National"):
    categories = set(df.speed_down_bins.unique())
    legend_elements = [Line2D([0], [0], marker='o', color='w', 
                          label=label, markerfacecolor=c, markersize=10)
                   for label, c in speed_labels.items() if label in categories][::-1]
    
    df['color'] = df['speed_down_bins'].apply(lambda x: speed_labels.get(x))
#     df = df[(~df['income_lmi'].isnull()) & (df['income_lmi'] > -11808.606100)]
    df.loc[:, 'income_level'] = df['income_level'].astype(
         CategoricalDtype(income_labels, ordered=True)
    ).copy(deep=True)
    
    to_plot = (df.groupby('income_level').speed_down_bins
                 .value_counts(normalize=True)
                 .sort_index() * 100 ).unstack()[
        [c for c in speed_labels.keys() if c in categories]
    ]
    
    ax = to_plot.plot(
        kind='barh', stacked=True, figsize=(8,4), 
        color = [v for k,v in speed_labels.items() if k in categories],
    )

    bin_counts = df.income_level.value_counts().sort_index()

    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Only show ticks on the left and bottom spines
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

    ax.set_ylabel("")
    ax.set_xlabel("Percentage of residential Internet offers")

    plt.title(f'{isp} {location} Residential Download Speeds\n'
             f'by Block Group Median Income (N={len(df):,})',
            loc='left',
    #          x=0.48,
             y=1.125,
             size=15.5)

    ax.legend(handles=legend_elements[::-1],
              loc='lower left', 
              bbox_to_anchor= (-0.025, 1.015), ncol=5,
              handletextpad=0.0,
              labelspacing=0, 
              borderaxespad=.1, 
              borderpad=0.1,
              frameon=False,
              prop={'size': 9.2})

    plt.text(0, -1.4, f"Income-levels defined by the Community Reinvestment Act.\n"
             "Median household income from the 2019 5-year American Community Survey.",
            horizontalalignment='left',
            verticalalignment='center',);

    # label counts
    rects = ax.patches
    heights = sorted(set([r.get_y() for r in rects]))
    for label, h in zip(bin_counts, heights):
        ax.text(101, h+.1, f'N={label:,}', ha='left', va='bottom')

    plt.show()
    
    

def redlining(df, isp="AT&T", location="National"):
    categories = set(df.speed_down_bins.unique())
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', 
               label=label, markerfacecolor=c, markersize=10)
        for label, c in speed_labels.items() 
        if label in categories
    ][::-1]    
    
    df['color'] = df['speed_down_bins'].apply(lambda x: speed_labels.get(x))
    df = df[(~df.redlining_grade.isnull()) & (df.redlining_grade != 'E')]
    if df.empty:
        return
    
    to_plot = (df.groupby('redlining_grade').speed_down_bins
                 .value_counts(normalize=True)
                 .sort_index() * 100 ).unstack()[::-1][[
        c for c in speed_labels.keys() if c in categories
    ]]
    
    ax = to_plot.plot(kind='barh', stacked=True, figsize=(8, 4), 
                      color = [v for k,v in speed_labels.items() if k in categories],
    )

    bin_counts = df['redlining_grade'].value_counts().sort_index()[::-1]
    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Only show ticks on the left and bottom spines
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

    labels = [redlininggrade2name.get(item.get_text()) for item in ax.get_yticklabels()]
    ax.set_yticklabels(labels)
    
    ax.set_ylabel("")
    ax.set_xlabel("Percentage of residential Internet offers")

    ax.legend(handles=legend_elements[::-1],
              loc='lower left', 
              bbox_to_anchor= (-0.025, 1.015), 
              ncol=5,
              handletextpad=0.1,
              labelspacing=0, 
              borderaxespad=.1, 
              borderpad=0.1,
              frameon=False,
              prop={'size': 9.2})

    plt.title(f'{isp} {location} Residential Download Speeds by \n'
              f'Neighborhoods Historically Rated for Redlining (N={len(df):,})',
              loc='left',
              y=1.075,
              size=15.5)

    # label counts
    rects = ax.patches
    heights = sorted(set([r.get_y() for r in rects]))
    for label, h in zip(bin_counts, heights):
        ax.text(101, h+.1, f'N={label:,}', ha='left', va='bottom')
    
    plt.text(0, -1.4, "Historic HOLC grades digitized by the Mapping Inequality project.\n"
                      'A grade of "D" means the neighborhood was Redlined.',
            horizontalalignment='left',
            verticalalignment='center',);

    plt.show()
    
def plot_race(df, location='National', isp='AT&T', price="$55"):
    categories = set(df.speed_down_bins.unique())
    legend_elements = [Line2D([0], [0], marker='o', color='w', 
                          label=label, markerfacecolor=c, markersize=10)
                   for label, c in speed_labels.items() if label in categories][::-1]
    n_intervals = 21
    steps = 1 / n_intervals
    intervals = np.arange(0, 1. +  steps, steps)
    intervals = [np.round(_, 2) for _ in intervals]
    intervals[-1] = 1.01
        
    df['race_perc'] = pd.cut(df[RACE_COL], bins=intervals, right=False)
    cuts = pd.pivot_table(
        data = df,
        columns = 'speed_down_bins',
        index = 'race_perc',
        values = ['address_full'],
        aggfunc='count',
        fill_value = 0,
    )
    cuts.sort_values(by='race_perc', inplace=True)
    cuts = cuts.divide(cuts.sum(axis=1), axis=0)
    cuts = cuts[[('address_full', c) for c in speed_labels.keys() if c in categories]]
    data = np.cumsum(cuts.values, axis=1)
    ig, ax = plt.subplots(figsize=(8, 8))
    if cuts.isnull().values.any():
        plt.fill_between(x=[1,0], y1=[1,1], y2=.05,
                         interpolate=True, facecolor="none", zorder=-100,
                         hatch="\\\\\\\\\\", edgecolor="grey", linewidth=0.0)
    for i, col in enumerate(cuts.columns):
        label = col[-1]
        ax.fill_betweenx(intervals[1:], data[:, i], 
                         label=col[-1], color=speed_labels.get(label),
                         zorder=-i)
#         ax.plot(data[:, i], intervals[1:], 
#                 ls="-", linewidth=1.4,
#                 alpha=1, c="white")
    ax.margins(y=0)
    ax.set_ylim(steps, 1)
    ax.set_xlim(0, 1)
    ax.set_axisbelow(False)
    plt.gca().invert_yaxis()

    # Hide the right and top spines
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)

    # Only show ticks on the left and bottom spines
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')

    # special ticks for y-axis
    if n_intervals == 21:
        ax.set_yticks(np.arange(steps, 1 + steps, steps*2), minor=True)
    elif n_intervals == 11:
        ax.set_yticks(np.arange(steps, 1 + steps, steps), minor=True)

    plt.yticks(np.arange(steps, 1 + steps, ((1 - steps) / 2)),
               ['100% white', 'Integrated\nblock groups', '0% white'])

    ax.legend(handles=legend_elements[::-1],
              loc='lower left', 
              bbox_to_anchor= (-0.025, 1.015), ncol=5,
              handletextpad=0.0,
              labelspacing=0, 
              borderaxespad=.1, 
              borderpad=0.1,
              frameon=False,
              prop={'size': 9.2})

    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    ax.grid(which='major', 
            axis='x', 
            linestyle='-',
            alpha=.27,
            zorder=1000, 
            color='white')

    ax.grid(which='both', 
            axis='y', 
            linestyle='-',
            alpha=.27,
            zorder=1000, 
            color='white')
    
    # titles and subtitles
    plt.title(f'{isp} {location} Residential Download Speeds by\n'
              f'Block Group Racial and Ethnic Demographic (N={len(df):,})',
              loc='left', y=1.055, size=15.5)
    
    plt.text(0, 1.11, f"All prices quoted at {price}. 2019 5-year ACS data (y-axis) bucketed in 5-percent increments."
             "\nNumber of households (x-axis) normalized across speed tiers within buckets.",
            horizontalalignment='left',
            verticalalignment='center',);
    
    plt.show()
    
