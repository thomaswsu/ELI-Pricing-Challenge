class simulatedELI(object):
    def __init__(self, tickerName: str, calendarTicker: str, country: str, priceHistory: list) -> None:
        self.tickerName = tickerName
        self.calendarTicker = calendarTicker
        self.country = country
        self.priceHistory = priceHistory