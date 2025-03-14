import backtrader as bt


class BollingerBandsStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('devfactor', 2)
    )

    def __init__(self):
        self.bollinger = bt.indicators.BollingerBands(
            self.data.close, period=self.params.period, devfactor=self.params.devfactor)

    def next(self):
        if not self.position:
            if self.data.close[0] < self.bollinger.lines.bot[0]:
                self.buy()
        else:
            if self.data.close[0] > self.bollinger.lines.top[0]:
                self.sell()