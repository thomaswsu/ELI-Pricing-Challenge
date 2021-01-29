import pandas
import pandas_market_calendars as mcal
 
class simulatedNana(object):
    def __init__(self, tickerName: str, calendarTicker: str, country: str, priceHistory: list) -> None:
        self.tickerName = tickerName
        self.calendarTicker = calendarTicker
        self.country = country
        self.priceHistory = priceHistory

        # generated features
        self.calendar = mcal.get_calendar(calendarTicker)
        self.intialPrice= self.priceHistory[0]
        self.triggeredIndexDates = []
        self.triggerRedemptionDates = []
    
    def setTriggerObservationDates(self, dates: list):
        self.triggerObservationDates = pandas.Series(dates)

    def setObservationDates(self, dates: list): 
        self.observationDates = pandas.Series(dates)
    
    def generateTriggerIndexes(self, startDate: pandas.DatetimeIndex):
        self.triggerIndexes = []
        for day in self.triggerObservationDates:
            self.triggerIndexes.append(len(self.calendar.schedule(startDate, day)))

    def getTriggerDates(self):
        i = 0 # hack
        for indexDay in self.triggerIndexes:
            if self.priceHistory[indexDay] >= self.intialPrice * 0.97:
                self.triggeredIndexDates.append(indexDay)
                self.triggerRedemptionDates.append(self.observationDates[i])
            i += 1