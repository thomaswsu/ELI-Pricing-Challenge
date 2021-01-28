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
import numpy as np

def getFinalRedemption(price1: float, price2: float, price: float):
    
    finalLevel=np.array([price1,price2,price3])
    par=np.array([23723.38,11079.79, 8846.449])
    strike=par*.7
   
    #if all 3 are above strike, we get all at par
    if (finalLevel[0]>strike[0] and finalLevel[1]>strike[1] and finalLevel[2]>par[2]):
        print('all above strike')
        return par
    else:
    #if 1 is below then find the worst performing stock
        performance=finalLevel/strike
        worstPerformance=np.min(performance)
        
        #multiply the Final level by finalLeve(worst)/strike(worst)
        return worstPerformance*finalLevel





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

    # Get past market prices MILAN
    FTSEMIB = getIndexPrice(ticker="FTSE MIB", country="Italy", startDate="24/01/2011", endDate="24/01/2021")
    HSCEI = getIndexPrice(ticker="Hang Seng CEI", country="Hong Kong", startDate="24/01/2011", endDate="24/01/2021")
    NDX = getIndexPrice(ticker="Nasdaq 100 ", country="United States", startDate="24/01/2011", endDate="24/01/2021")

    # Convert price data to list because I know how to use lists 
    FTSEMIB_priceList = list(FTSEMIB["Open"])
    HSCEI_priceList = list(HSCEI["Open"])
    NDX_priceList = list(NDX["Open"])

    # Get dates for each index
    FTSEMIB_dates = list(pandas.DatetimeIndex.to_pydatetime(FTSEMIB.index))
    HSCEI_dates = list(pandas.DatetimeIndex.to_pydatetime(HSCEI.index))
    NDX_dates = list(pandas.DatetimeIndex.to_pydatetime(NDX.index))

    # Plot FTSEMIB for visual context 
    fig, ax = plt.subplots()

    # Format xaxis
    years = mdates.YearLocator()   # every year
    months = mdates.MonthLocator()  # every month
    years_fmt = mdates.DateFormatter('%Y')

    plt.plot_date(FTSEMIB_dates, FTSEMIB_priceList, 'b-')
    formatter = DateFormatter('%m/%d/%y')
    ax.xaxis.set_major_locator(years)
    ax.xaxis.set_major_formatter(years_fmt)
    ax.xaxis.set_minor_locator(months)
    ax.grid(True)

    # Make best fit line 
    FTSEMIB_xAxis = range(0, len(FTSEMIB_dates)) # We need this to calculate line of best line 
    FTSEMIB_m, FTSEMIB_b, FTSEMIB_r_value, FTSEMIB_p_value, FTSEMIB_std_err = stats.linregress(FTSEMIB_xAxis, FTSEMIB_priceList)
    plt.plot(FTSEMIB_dates, FTSEMIB_m * FTSEMIB_xAxis + FTSEMIB_b)
    
    FTSEMIB_std_dev = FTSEMIB_std_err * m.sqrt(len(FTSEMIB_dates))

    # Actually plot
    #fig.autofmt_xdate()
    #plt.show()

    # Calculate Standard Deviation of the remaining two assets in portfolio
    HSCEI_xAxis = range(0, len(HSCEI_dates))
    HSCEI_m, HSCEI_b, HSCEI_r_value, HSCEI_p_value, HSCEI_std_err = stats.linregress(HSCEI_xAxis, HSCEI_priceList)
    HSCEI_std_dev = HSCEI_std_err * m.sqrt(len(HSCEI_dates))

    NDX_xAxis = range(0, len(NDX_dates))
    NDX_m, NDX_b, NDX_r_value, NDX_p_value, NDX_std_err = stats.linregress(NDX_xAxis, NDX_priceList)
    NDX_std_dev = NDX_std_err * m.sqrt(len(NDX_dates))

    # Print some stats for now
    print("FTSEMIB Slope: {}, FTSEMIB Standard Deviation: {}".format(FTSEMIB_m, FTSEMIB_std_dev))
    print("HSCEI Slope: {}, HSCEI Standard Deviation: {}".format(HSCEI_m, HSCEI_std_dev))
    print("NDX Slope: {}, NDX Standard Deviation: {}".format(NDX_m, NDX_std_dev))




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

