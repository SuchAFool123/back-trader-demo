import backtrader as bt


class RSIStrategy(bt.Strategy):
    params = (
        ('period', 14),
        ('oversold', 30),
        ('overbought', 70)
    )

    def __init__(self):
        self.rsi = bt.indicators.RelativeStrengthIndex(
            self.data.close, period=self.params.period)

    def next(self):
        if not self.position:
            if self.rsi < self.params.oversold:
                self.buy()
        else:
            if self.rsi > self.params.overbought:
                self.sell()
