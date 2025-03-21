import backtrader as bt

class SMAStrategy(bt.Strategy):
    def __init__(self, send_message_callback=None):
        self.send_message_callback = send_message_callback
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=10)

    def next(self):
        if self.data.close[0] > self.sma[0] and not self.position:
            self.buy()
            if self.send_message_callback:
                self.send_message_callback("trade_info", f"SMAStrategy 买入信号触发")
        elif self.data.close[0] < self.sma[0] and self.position:
            self.sell()
            if self.send_message_callback:
                self.send_message_callback("trade_info", f"SMAStrategy 卖出信号触发")
