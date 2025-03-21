import backtrader as bt

class RSIStrategy(bt.Strategy):
    def __init__(self, send_message_callback=None):
        self.send_message_callback = send_message_callback
        self.rsi = bt.indicators.RSI(self.data.close)

    def next(self):
        if self.rsi < 30 and not self.position:
            self.buy()
            if self.send_message_callback:
                self.send_message_callback("trade_info", f"RSIStrategy 买入信号触发")
        elif self.rsi > 70 and self.position:
            self.sell()
            if self.send_message_callback:
                self.send_message_callback("trade_info", f"RSIStrategy 卖出信号触发")
