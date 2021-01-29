from datetime import date, timedelta
import datetime
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
import pandas_market_calendars as mcal


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


def overrideDates(monteCarloSimulation: pandas.DataFrame, ticker: str, startDate: str, endDate: str) -> pandas.DataFrame:
    """
    Probably a function that we don't need anymore
    """
    calendar = mcal.get_calendar(ticker)
    dates = calendar.schedule(startDate, endDate)
    if len(monteCarloSimulation)>len(dates):
        monteCarloSimulation.drop(monteCarloSimulation.tail(len(monteCarloSimulation)-len(dates)).index,inplace=True)
    dates=pandas.to_datetime(dates['market_open']).dt.date.unique().tolist()
    monteCarloSimulation["date"] = dates
    #monteCarloSimulation.set_index("date")
    return(monteCarloSimulation)

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

def payoutSinglePeriod(simnum, ul1, ul2, ul3, cal1: str, cal2: str, cal3: str, start, end):
    """returns n/N and prints payout for each underlying between date1 and date2
    accepts dates in form m/d/y
    
        accepts simulation number, monteCarlo simulations, calendar names, and 
        two payout dates
    """
    daterange1=mcal.get_calendar(cal1).schedule(start_date=start, end_date=end)
    daterange2=mcal.get_calendar(cal2).schedule(start_date=start, end_date=end)
    daterange3=mcal.get_calendar(cal3).schedule(start_date=start, end_date=end)
    daterange=[daterange1,daterange2,daterange3]
    
    par1=23723.38
    par2=11079.79
    par3=8846.449
    payoutthresholdlist=[par1*.7,par2*.7,par3*.7]
    payoutlist=[]
    n=0
    N=0
    while not(all(x == datetime.datetime.strptime(end,'%m/%d/%Y').date() for x in [daterange[0]['market_open'].iloc[0].date(), daterange[1]['market_open'].iloc[0].date(), daterange[2]['market_open'].iloc[0].date()])):
        firstdate = [daterange[0]['market_open'].iloc[0].date(), daterange[1]['market_open'].iloc[0].date(), daterange[2]['market_open'].iloc[0].date()]
        while not(all(x == firstdate[0] for x in firstdate)): #while not all days are the same
            lowestrangeindex = firstdate.index(min(firstdate))
            daterange[lowestrangeindex] = daterange[lowestrangeindex].iloc[1:]
            firstdate = [daterange[0]['market_open'].iloc[0].date(), daterange[1]['market_open'].iloc[0].date(), daterange[2]['market_open'].iloc[0].date()]
        ul1price = ul1[simnum][ul1[ul1['date'] == firstdate[0]].index[0]]
        ul2price = ul2[simnum][ul2[ul2['date'] == firstdate[1]].index[0]]
        ul3price = ul3[simnum][ul3[ul3['date'] == firstdate[2]].index[0]]
        firstdateprices=[ul1price, ul2price, ul3price] 
        n+=1*all(firstdateprices[i] >= payoutthresholdlist[i] for i in range(len(firstdateprices)))
        N+=1
        daterange[0]=daterange[0].iloc[1:]
        daterange[1]=daterange[1].iloc[1:]
        daterange[2]=daterange[2].iloc[1:]
    return([n,N])


def payoutPath(simnum:int, ul1, ul2, ul3, pathenddate:str, payoutdates:list, payoutobs:list):
    """ Accepts the simulation number, montecarlo sims, end date, payout dates, payoutobservation list
        Returns payout for [FTSEMIB, HSCEI, NDX]
    """
    par1=23723.38
    par2=11079.79
    par3=8846.449
    #determine final payoutday
    payoutdateslist=[]
    for i in payoutdates:
        payoutdateslist.append(datetime.datetime.strptime(i,'%m/%d/%Y').date())
    #one before the first False will be the last date
    finalpayoutdate=payoutdates[[x < datetime.datetime.strptime(pathenddate,'%m/%d/%Y').date() for x in payoutdateslist].index(False)-1]
    finalpayoutdate=datetime.datetime.strptime(finalpayoutdate,'%m/%d/%Y').date()
    
    #determine final payout period
    payoutobslist=[]
    done=False
    for i in payoutobs:
        period=[]
        if done==True:
            break
        for x in i:
            period.append(datetime.datetime.strptime(x,'%m/%d/%Y').date())
            if datetime.datetime.strptime(x,'%m/%d/%Y').date()>finalpayoutdate:
                done=True
                break
        payoutobslist.append(period)
    payout1=0
    payout2=0
    payout3=0
    for obsperiod in payoutobslist:
        payoutn=payoutSinglePeriod(simnum, ul1, ul2, ul3, 'XETR', 'HKEX', 'NYSE', obsperiod[0].strftime("%m/%d/%Y"), obsperiod[1].strftime("%m/%d/%Y"))
        mult=payoutn[0]/payoutn[1]
        if obsperiod==payoutobslist[0]:
            mult=(payoutn[0]+46)/(payoutn[1]+47)
        payout1+=par1*.068*mult
        payout2+=par2*.068*mult
        payout3+=par3*.068*mult
    print([payout1,payout2,payout3])
    
    
    
    
    
    


if __name__ == "__main__":

    start="24/01/2011"
    end="16/03/2020"
    


    # Get past market prices MILAN
    
    FTSEMIB = getIndexPrice(ticker="FTSE MIB", country="Italy", startDate=start, endDate=end)
    HSCEI = getIndexPrice(ticker="Hang Seng CEI", country="Hong Kong", startDate=start, endDate=end)
    NDX = getIndexPrice(ticker="Nasdaq 100 ", country="United States", startDate=start, endDate=end)

    
    daynum=1030
    simnum=10
    
    
    a=monteCarlo(simnum,daynum, FTSEMIB)
    b=monteCarlo(simnum, daynum, HSCEI)
    c=monteCarlo(simnum, daynum, NDX)
    
    a2=overrideDates(a, 'XETR', '3/16/2020', '1/7/2023')
    b2=overrideDates(b, 'HKEX', '3/16/2020', '1/7/2023')
    c2=overrideDates(c, 'NYSE', '3/16/2020', '1/7/2023')
    
    payoutSinglePeriod(5, a2, b2, c2, 'XETR', 'HKEX', 'NYSE', '3/16/2020', '4/7/2020')
    
    
    #find the n from January 8 to March 16 out of N
    FTSEMIB_pre = list(getIndexPrice(ticker="FTSE MIB", country="Italy", startDate="8/1/2020", endDate="16/3/2020")["Close"])
    HSCEI_pre = list(getIndexPrice(ticker="Hang Seng CEI", country="Hong Kong", startDate="8/1/2020", endDate="16/3/2020")["Close"])
    NDX_pre = list(getIndexPrice(ticker="Nasdaq 100 ", country="United States", startDate="8/1/2020", endDate="16/3/2020")["Close"])
    payoutthreshholdlist=[23723.38*.7,11079.79*.7,8846.449*.7]
    n=0
    for i in range(len(min(FTSEMIB_pre,HSCEI_pre,NDX_pre))):
        daylist=[FTSEMIB_pre[i],HSCEI_pre[i],NDX_pre[i]]
        n+=all(daylist[x] >= payoutthreshholdlist[x] for x in range(len(daylist)))     
    print(n)
    print(len(min(FTSEMIB_pre,HSCEI_pre,NDX_pre)))
    
    
    payoutobsperiod=[['3/16/2020','4/7/2020'], ['4/7/2020','7/7/2020'],['10/7/2020','1/7/2021'],['1/7/2021','4/7/2021'], ['4/7/2021','7/7/2021'],['10/7/2021','1/7/2022'],['1/7/2022','4/7/2022'], ['4/7/2022','7/7/2022'],['10/7/2022','1/9/2023']]
    payoutdates=['4/14/2020','7/14/2020','10/14/2020','1/14/2021','4/14/2021','7/14/2021','10/14/2021','1/14/2022','4/14/2022','7/14/2022','10/14/2022','1/17/2023']
    
    payoutPath(5, a2, b2, c2, '1/7/2021', payoutdates, payoutobsperiod)
    
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

