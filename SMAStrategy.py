import backtrader as bt


class SMAStrategy(bt.Strategy):
    params = (
        ('short_period', 5),
        ('long_period', 20)
    )

    def __init__(self):
        self.short_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.short_period)
        self.long_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.long_period)
        self.crossover = bt.indicators.CrossOver(self.short_sma, self.long_sma)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.sell()
