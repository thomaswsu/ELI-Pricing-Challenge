import datetime
import investpy
from numpy.lib.function_base import average
import pandas
from matplotlib import pyplot as plt 
import numpy as np
import pandas_market_calendars as mcal
from simulatedNana import * 
import pickle

def HKDtoUSD(hkd: float) -> float:
    """
    https://www.exchange-rates.org/Rate/HKD/USD/1-7-2020
    """
    return(hkd * 0.12860)

def EUROtoUSD(euro: float) -> float:
    """
    https://www.exchange-rates.org/Rate/USD/EUR/1-7-2020
    """
    return(euro * 1.1149514996)

def getFinalRedemption(price1: float, price2: float, price3: float):
    global abovestrikecount
    finalLevel=np.array([price1,price2,price3])
    par=np.array([23723.38,11079.79, 8846.449])
    strike=par*.7

    #if all 3 are above strike, we return par
    if (finalLevel[0]>strike[0] and finalLevel[1]>strike[1] and finalLevel[2]>par[2]):
        abovestrikecount = 1
        return par
    else:
    #if 1 is below then find the worst performing stock
        performance=finalLevel/strike
        worstPerformance=np.min(performance)

        #return par with finalLeve(worst)/strike(worst)
        return worstPerformance*par

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


def payoutPath(simnum:int, ul1, ul2, ul3, pathenddate:str, payoutdates:list, payoutobs:list, earlyTrig=bool):
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
        
    for i in payoutobslist:
        if len(i)<2:
            payoutobslist.remove(i)
        
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
    if earlyTrig==True:
        return([payout1+par1,payout2+par2,payout3+par3])
    else:
        return([payout1,payout2,payout3])

def getTriggerDates(simnum, ul1, ul2, ul3, triggerobsdates:list, triggerpayoutdates:list):
    """Outputs first trigger date
    """
    triggerthreshold=[23011.6786, 10747.3963, 8581.0555]
    triggerobsdatelist=[]
    triggerdateindex=-1
    for i in triggerobsdates:
        triggerobsdatelist.append(datetime.datetime.strptime(i,'%m/%d/%Y').date())
    for i in range(len(triggerobsdatelist)):
        date=triggerobsdatelist[i]
        ul1price = ul1[simnum][ul1[ul1['date'] == date].index[0]]
        ul2price = ul2[simnum][ul2[ul3['date'] == date].index[0]]
        ul3price = ul3[simnum][ul3[ul3['date'] == date].index[0]]
        pricelist=[ul1price,ul2price,ul3price]
        if all(pricelist[x] >= triggerthreshold[x] for x in range(len(pricelist))):
            triggerdateindex=i
            break
    if triggerdateindex==-1:
        return -1
    else:
        return triggerpayoutdates[triggerdateindex]
    
def convertHKDtoUSD(payoutlist: list) -> list:
    for i in range(len(payoutlist)):
        payoutlist[i] = HKDtoUSD(payoutlist[i])
    return(payoutlist)

def convertEUROtoUSD(payoutlist: list) -> list:
    for i in range(len(payoutlist)):
        payoutlist[i] = EUROtoUSD(payoutlist[i])
    return(payoutlist)

def calculateAveragePayout(df: pandas.DataFrame) -> float:
    total = 0

    for index in df.index:
        total += HKDtoUSD(df['FTSEMIB payout'][index])
        total += EUROtoUSD(df['HSCEI payout'][index]) 
        total += df['NDX payout'][index]
    
    return(round(total / df.shape[0], 2))

if __name__ == "__main__":

    start="24/01/2011"
    end="16/03/2020"

    # Get past market prices MILAN
    
    FTSEMIB = getIndexPrice(ticker="FTSE MIB", country="Italy", startDate=start, endDate=end)
    HSCEI = getIndexPrice(ticker="Hang Seng CEI", country="Hong Kong", startDate=start, endDate=end)
    NDX = getIndexPrice(ticker="Nasdaq 100", country="United States", startDate=start, endDate=end)

    

    payoutobsperiod=[['3/16/2020','4/7/2020'], ['4/7/2020','7/7/2020'],['10/7/2020','1/7/2021'],['1/7/2021','4/7/2021'], ['4/7/2021','7/7/2021'],['10/7/2021','1/7/2022'],['1/7/2022','4/7/2022'], ['4/7/2022','7/7/2022'],['10/7/2022','1/9/2023']]
    payoutdates=['4/14/2020','7/14/2020','10/14/2020','1/14/2021','4/14/2021','7/14/2021','10/14/2021','1/14/2022','4/14/2022','7/14/2022','10/14/2022','1/17/2023']
    
    triggerobsdates=['7/7/2020','10/7/2020','1/7/2021','4/7/2021','7/7/2021','10/7/2021','1/7/2022','4/7/2022','7/7/2022','10/7/2022']
    triggerreddates=['7/14/2020','10/14/2020','1/14/2021','4/14/2021','7/14/2021','10/14/2021','1/14/2022','4/14/2022','7/14/2022','10/14/2022']
    
    daynum=1030
    simnum=10
    
    a=monteCarlo(simnum,daynum, FTSEMIB)
    b=monteCarlo(simnum, daynum, HSCEI)
    c=monteCarlo(simnum, daynum, NDX)
    
    a2=overrideDates(a, 'XETR', '3/16/2020', '1/17/2023')
    b2=overrideDates(b, 'HKEX', '3/16/2020', '1/17/2023')
    c2=overrideDates(c, 'NYSE', '3/16/2020', '1/17/2023')
     
    global abovestrikecount
    
    redeemedDates = [] 
    for i in range(len(a2.columns)-1):
        redeemedDates.append(getTriggerDates(i, a2, b2, c2, triggerobsdates, triggerreddates))


    #to see tests being generated
    for i in range(len(redeemedDates)):
        if redeemedDates[i] != -1:
            print("TRIGGER", redeemedDates[i], payoutPath(i, a2, b2, c2, redeemedDates[i], payoutdates, payoutobsperiod, earlyTrig=True))
        else:
            finalredemptionlist=getFinalRedemption(a2[i][a2[a2['date'] == datetime.datetime.strptime('1/9/2023','%m/%d/%Y').date()].index], b2[i][b2[b2['date'] == datetime.datetime.strptime('1/9/2023','%m/%d/%Y').date()].index], c2[i][c2[c2['date'] == datetime.datetime.strptime('1/9/2023','%m/%d/%Y').date()].index])
            finalpayoutlist=payoutPath(i, a2, b2, c2, '1/17/2023', payoutdates, payoutobsperiod, earlyTrig=False)
            print("FINAL", [finalredemptionlist[i]+finalpayoutlist[i] for i in range(len(finalredemptionlist))])
    
    #to create a list of outputs
    outputlist=[]
    for i in range(len(redeemedDates)):
        print(i)
        if redeemedDates[i] != -1:
            triggerpricelist=payoutPath(i, a2, b2, c2, redeemedDates[i], payoutdates, payoutobsperiod, earlyTrig=True)
            triggerpricelist.append(1)
            triggerpricelist.append(0)#above strike count
            outputlist.append(triggerpricelist)
        else:
            abovestrikecount=0
            finalredemptionlist=getFinalRedemption(a2[i][a2[a2['date'] == datetime.datetime.strptime('1/9/2023','%m/%d/%Y').date()].index], b2[i][b2[b2['date'] == datetime.datetime.strptime('1/9/2023','%m/%d/%Y').date()].index], c2[i][c2[c2['date'] == datetime.datetime.strptime('1/9/2023','%m/%d/%Y').date()].index])
            finalpayoutlist=payoutPath(i, a2, b2, c2, '1/17/2023', payoutdates, payoutobsperiod, earlyTrig=False)
            finalpricelist=[finalredemptionlist[i]+finalpayoutlist[i] for i in range(len(finalredemptionlist))]
            finalpricelist.append(0)
            if abovestrikecount==1:
                finalpricelist.append(1)
            else:
                finalpricelist.append(0)
            outputlist.append(finalpricelist)
            abovestrikecount=0
            
    print(outputlist)
    
    payout1list=[]
    payout2list=[]
    payout3list=[]
    triggered=[]
    abovestrikecountlist=[]
    outputdf=pandas.DataFrame({})
    for simnum in range(len(outputlist)):
        payout1list.append(outputlist[simnum][0])
        payout2list.append(outputlist[simnum][1])
        payout3list.append(outputlist[simnum][2])
        triggered.append(outputlist[simnum][3])
        abovestrikecountlist.append(outputlist[simnum][4])
    outputdf['FTSEMIB payout']= payout1list
    outputdf['HSCEI payout']=payout2list
    outputdf['NDX payout']=payout3list
    outputdf['Triggered']=triggered
    outputdf['Above Strike Lvl']=abovestrikecountlist

    print(calculateAveragePayout(outputdf))
            
    safestore=outputdf
    
    
    
    plotsim=0

    fig=plt.figure()
    plt.plot(a2[plotsim])
    plt.show()
    fig=plt.figure()
    plt.plot(b2[plotsim])
    plt.show()
    fig=plt.figure()
    plt.plot(c2[plotsim])
    plt.show()
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

