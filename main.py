from datetime import date
import investpy
import pandas
from matplotlib import pyplot as plt 
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter
#import pandas_datareader.data as pdr
import numpy as np
from scipy import stats
import math as m
import time


def getIndexPrice(ticker: str, country: str, startDate: str, endDate: str) -> pandas.DataFrame:
    """
    Examples: 
    getIndexPrice(ticker="FTSE MIB", country="Italy", startDate="24/01/2011", endDate="24/01/2021")
    getIndexPrice(ticker="Hang Seng CEI", country="Hong Kong", startDate="24/01/2011", endDate="24/01/2021")
    getIndexPrice(ticker="Nasdaq 100 ", country="United States", startDate="24/01/2011", endDate="24/01/2021")
    """
    return(investpy.indices.get_index_historical_data(index = ticker, country=country, from_date=startDate, to_date=endDate))

def valueELI(issuePrice: float, intialFixingDate: date, finalFixingDate: date, finalRedemptionDate: date) -> float:
    return(0)

def oneTSeries(days:int, count: int, daily_vol: int, price: int, tseries):
    "Run a single simulation and returns one simulation 'run'."
    for day in range(days):
        if count==(days-1):
            break
        price=tseries[count]*(1+np.random.normal(0,daily_vol))
        tseries.append(price)
        count+=1
        
    return tseries

def monteCarlo(iterations: int, days: int, underlying):
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



if __name__ == "__main__":

    start="24/01/2011"
    end="16/03/2020"
    


    # Get past market prices MILAN
    
    FTSEMIB = getIndexPrice(ticker="FTSE MIB", country="Italy", startDate=start, endDate=end)
    HSCEI = getIndexPrice(ticker="Hang Seng CEI", country="Hong Kong", startDate=start, endDate=end)
    NDX = getIndexPrice(ticker="Nasdaq 100 ", country="United States", startDate=start, endDate=end)
        
    

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
"""

