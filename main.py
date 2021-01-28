from datetime import date
import investpy
import pandas
from matplotlib import pyplot as plt 
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
import numpy as np
from pandas.core.frame import DataFrame
from scipy import stats
import math as m
import time
import random
import numpy as np
import pandas_market_calendars as mcal
from simulatedELI import *

def getFinalRedemption(price1: float, price2: float, price3: float):
    
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

def oneTSeries(days:int, count: int, daily_vol: int, price: int, tseries):
    "Run a single simulation and returns one simulation 'run'."
    for day in range(days):
        if count==(days-1):
            break
        price=tseries[count]*(1+np.random.normal(0,daily_vol))
        tseries.append(price)
        count+=1
        
    return tseries

def monteCarlo(iterations: int, days: int, underlying: pandas.DataFrame):
    """
    Return a monte carlo simulation dataframe of one underlying
    Example: monteCarlo(500, 252, FTSEMIB)
    
    Adapted from https://www.youtube.com/watch?v=_T0l015ecK4

    Crucially, Monte Carlo simulations ignore everything that is not built into the price movement (macro trends, company leadership, hype, cyclical factors); in other words, they assume perfectly efficient markets.
    """
    ul=underlying['Close']
    

    ul_last_price = ul.iloc[-1]
    
    ulreturns = ul.pct_change()

    ul_price_df=pandas.DataFrame()
    
    for sim in range(iterations):
        ul_daily_vol = ulreturns.std()
        ul_tseries = []
        
        ulprice = ul_last_price*(1+np.random.normal(0, ul_daily_vol))
        ul_tseries.append(ulprice)
        
        "run a single simulation"
        ul_tseries=oneTSeries(days, 0, ul_daily_vol, ulprice, ul_tseries)
            
        ul_price_df[sim]=(ul_tseries)
        
    return ul_price_df

def daysAfter(start, end):
    """ accepts format m/d/y"""
    start=pandas.to_datetime(start,format= '%m/%d/%Y')
    end=pandas.to_datetime(end,format='%m/%d/%Y')
    return (end-start).days


def notepath(ul1, ul2, ul3, payoutperiod):
    """returns in the form of simulation, payout period, n/N
    
        accepts monteCarlo simulations and a payout period in the form of days
        within payout period. ex. [93,90,91,92...]
    """
    par1=23723.38
    par2=11079.79
    par3=8846.449 
    payoutthreshholdlist=[par1*.7,par2*.7,par3*.7]
    payoutlist=[]
    
    for sim in range(len(ul1.columns)): #for every sim
        periodcounter=0
        timeinpayoutperiod=payoutperiod[0]
        n=0
        N=0
        done=False
        for day in range(len(ul1[sim])): #for every day in sim x
            if timeinpayoutperiod==0: #end of the period
                noverN=[sim,periodcounter,n/N]
                payoutlist.append(noverN)
                periodcounter+=1 #go to next period
                if periodcounter>len(payoutperiod)-1: #go to next simulation if we are at end of period
                    done = True
                    break
                timeinpayoutperiod=payoutperiod[periodcounter]
                n=0
                N=0
            if done==True:
                break
            daylist=[ul1[sim][day], ul2[sim][day], ul3[sim][day]]
            n+=1*all(daylist[i] >= payoutthreshholdlist[i] for i in range(len(daylist)))
                
            N+=1
            timeinpayoutperiod-=1
    return(payoutlist)

def allTriggered(ELIs: list, redemptionDate: pandas.DatetimeIndex) ->  bool:
    allTriggered = False
    for ELI in ELIs:
        if not(redemptionDate in ELI.triggerRedemptionDates):
            return(False)
    return(True)
            


def earlyRedeem(ELIs: list, underlying: pandas.DataFrame, startDate: pandas.DatetimeIndex, observationDates: list, redemptionDates: list) -> pandas.DatetimeIndex:
    """
    Returns the earliest trigger date (an index not an actual date)
    """
    for ELI in ELIs:
        ELI.setTriggerObservationDates(observationDates)
        ELI.setObservationDates(redemptionDates)
        ELI.generateTriggerIndexes(startDate)
        ELI.getTriggerDates()
    
    for redemptionDate in ELIs[0].triggerRedemptionDates:
        if allTriggered(ELIs, redemptionDate):
            return(redemptionDate)
    return(-1)

def overrideDates(monteCarloSimulation: pandas.DataFrame, ticker: str, startDate: str, endDate: str) -> pandas.DataFrame:
    """
    Probably a function that we don't need anymore
    """
    calendar = mcal.get_calendar(ticker)
    dates = calendar.schedule(startDate)
    monteCarloSimulation["date"] = dates
    monteCarloSimulation.set_index("date")
    return(monteCarloSimulation)



def valueELI(issuePrice: float, intialFixingDate: date, finalFixingDate: date, finalRedemptionDate: date) -> float:
    return(0)


if __name__ == "__main__":
    random.seed(2021) # set seed for random number generator for monte carlo

    start="24/01/2011"
    end="16/03/2020"
    names = ["FTSE MIB", "Hang Seng CEI", "Nasdaq 100"]
    calendarTickers = ["", "", ""]
    observationDates = ["7/7/2020", "10/7/2020", "1/7/2021", "4/7/2021", "7/7/2021", "10/7/2021", "1/7/2022", "4/7/2022", "7/7/2022", "10/7/2022"]
    redemptionDates = ["7/14/2020", "10/14/2020", "1/14/2021", "4/14/2021", "7/14/2021", "10/14/2021", "1/14/2022", "4/14/2022", "7/14/2022", "10/14/2022"]
    interestRate = 0.068

    # Get past market prices MILAN
    FTSEMIB = getIndexPrice(ticker="FTSE MIB", country="Italy", startDate=start, endDate=end)
    HSCEI = getIndexPrice(ticker="Hang Seng CEI", country="Hong Kong", startDate=start, endDate=end)
    NDX = getIndexPrice(ticker="Nasdaq 100 ", country="United States", startDate=start, endDate=end)

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

    #Example Test
    f=monteCarlo(500, 252, HSCEI)
    
    
    fig=plt.figure()
    plt.plot(f)
    plt.show()

    daynum=1029
    simnum=10
    
    payoutperiod=[daysAfter('3/16/2020', '4/7/2020'), daysAfter('4/7/2020', '7/7/2020'),daysAfter('7/7/2020', '10/7/2020'),daysAfter('10/7/2020', '1/7/2021'),daysAfter('1/7/2021', '4/7/2021'),daysAfter('4/7/2021', '7/7/2021'),daysAfter('7/7/2021', '10/7/2021'),daysAfter('10/7/2021', '1/7/2022'),daysAfter('1/7/2022', '4/7/2022'),daysAfter('4/7/2022', '7/7/2022'),daysAfter('7/7/2022', '10/7/2022'),daysAfter('10/7/2022', '1/9/2023')]
    
    a=monteCarlo(simnum,daynum, FTSEMIB)
    b=monteCarlo(simnum, daynum, HSCEI)
    c=monteCarlo(simnum, daynum, NDX)
    
    notepath(a,b,c)
    
    
    """fig=plt.figure()
    plt.plot(a)
    plt.show()"""
    
    #if you want to see the distribution of final prices
    #plt.hist(b.iloc[-1],bins='auto')

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
https://pypi.org/project/pandas-market-calendars/
"""

"""
Trading days are not the same in each country
"""
