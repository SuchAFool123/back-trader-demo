import backtrader as bt

class SmaCross(bt.Strategy):
    def __init__(self, send_message_callback=None):
        self.send_message_callback = send_message_callback
        sma1 = bt.indicators.SimpleMovingAverage(self.data.close, period=5)
        sma2 = bt.indicators.SimpleMovingAverage(self.data.close, period=20)
        self.crossover = bt.indicators.CrossOver(sma1, sma2)

    def next(self):
        if self.crossover > 0 and not self.position:
            self.buy()
            if self.send_message_callback:
                self.send_message_callback("trade_info", f"SmaCross 买入信号触发")
        elif self.crossover < 0 and self.position:
            self.sell()
            if self.send_message_callback:
                self.send_message_callback("trade_info", f"SmaCross 卖出信号触发")
