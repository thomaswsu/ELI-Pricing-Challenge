from datetime import date
import investpy
import pandas
from matplotlib import pyplot as plt 
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
import numpy as np
from scipy import stats
import math as m
import random

def getIndexPrice(ticker: str, country: str, startDate: str, endDate: str) -> pandas.DataFrame:
    """
    Examples: 
    getIndexPrice(ticker="FTSE MIB", country="Italy", startDate="24/01/2011", endDate="24/01/2021")
    getIndexPrice(ticker="Hang Seng CEI", country="Hong Kong", startDate="24/01/2011", endDate="24/01/2021")
    getIndexPrice(ticker="Nasdaq 100 ", country="United States", startDate="24/01/2011", endDate="24/01/2021")
    """
    return(investpy.indices.get_index_historical_data(index = ticker, country=country, from_date=startDate, to_date=endDate))

def moneteCarlo(initalPrice: float, iterations: int, standardDeviation: float) -> float:
    """
    How else do I do

    Crucially, Monte Carlo simulations ignore everything that is not built into the price movement (macro trends, company leadership, hype, cyclical factors); in other words, they assume perfectly efficient markets.
    """
    price = initalPrice
    for _ in range(iterations):
        price += stats.norm.cdf(random.random()) * standardDeviation
    return(price)

def valueELI(issuePrice: float, intialFixingDate: date, finalFixingDate: date, finalRedemptionDate: date) -> float:
    return(0)


if __name__ == "__main__":
    random.seed(2021) # set seed for random number generator for monte carlo

    global FTSEMIB
    global HSCEI
    global NDX 

    names = ["FTSE MIB", "Hang Seng CEI", "Nasdaq 100"]

    # Get past market prices MILAN
    FTSEMIB = getIndexPrice(ticker="FTSE MIB", country="Italy", startDate="24/01/2011", endDate="24/01/2021")
    HSCEI = getIndexPrice(ticker="Hang Seng CEI", country="Hong Kong", startDate="24/01/2011", endDate="24/01/2021")
    NDX = getIndexPrice(ticker="Nasdaq 100", country="United States", startDate="24/01/2011", endDate="24/01/2021")

    indexes = [FTSEMIB, HSCEI, NDX]

    # Convert price data to list because I know how to use lists 
    priceLists = []
    for index in indexes:
        priceLists.append(list(index["Open"]))

    # Get dates for each index
    dates = []
    for index in indexes:
        dates.append(list(pandas.DatetimeIndex.to_pydatetime(index.index))) # poor naming...

    # Plot FTSEMIB for visual context 
    fig, ax = plt.subplots()

    # Format xaxis
    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    years_fmt = mdates.DateFormatter('%Y')

    plt.plot_date(dates[1], priceLists[1], 'b-')
    formatter = DateFormatter('%m/%d/%y')
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(years_fmt)
    ax.xaxis.set_minor_locator(months)
    ax.grid(True)

    # Make best fit line 
    xAxies = []
    statistics = []
    for i in range(len(indexes)):
        xAxies.append(range(0, len(dates[i])))
        slope, b, r_value, p_value, std_err = stats.linregress(xAxies[i], priceLists[i])
        statistics.append([slope, b, r_value, p_value, std_err])

    # statistics[1][0] is slope
    # statistics[1][0] is b
    plt.plot(dates[1], statistics[1][0] * xAxies[1] + statistics[1][1])
    
    standardDeviations = []
    for i in range(len(indexes)):
        standardDeviations.append(statistics[i][4])

    # Actually plot
    fig.autofmt_xdate()
    plt.show()


    # Print some stats for now
    for i in range(len(names)):
        print("{} Slope: {}, {} Standard Deviation: {}".format(names[i], statistics[i][0], names[i], standardDeviations[i]))




""" 
Sources:
https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html
https://matplotlib.org/3.1.1/gallery/ticks_and_spines/date_demo_rrule.html#sphx-glr-gallery-ticks-and-spines-date-demo-rrule-py
https://matplotlib.org/3.1.1/gallery/text_labels_and_annotations/date.html
https://www.kite.com/python/answers/how-to-plot-a-line-of-best-fit-in-python
https://stackoverflow.com/questions/17638137/curve-fitting-to-a-time-series-in-the-format-datetime
https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html
https://xplaind.com/268982/portfolio-standard-deviation
https://stackoverflow.com/questions/38828622/calculating-the-stock-price-volatility-from-a-3-columns-csv
https://www.investopedia.com/terms/m/montecarlosimulation.asp
"""

