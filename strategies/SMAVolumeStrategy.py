import backtrader as bt


class SMAVolumeStrategy(bt.Strategy):
    params = (
        ('short_period', 5),
        ('long_period', 20),
        ('volume_multiplier', 1.5)
    )

    def __init__(self):
        self.short_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.short_period)
        self.long_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.long_period)
        self.crossover = bt.indicators.CrossOver(self.short_sma, self.long_sma)
        self.volume_ma = bt.indicators.SimpleMovingAverage(
            self.data.volume, period=5)

    def next(self):
        if not self.position:
            if self.crossover > 0 and self.data.volume[0] > self.volume_ma[0] * self.params.volume_multiplier:
                self.buy()
        elif self.crossover < 0 and self.data.volume[0] > self.volume_ma[0] * self.params.volume_multiplier:
            self.sell()
