import backtrader as bt

class BollingerBandsStrategy(bt.Strategy):
    def __init__(self, send_message_callback=None):
        self.send_message_callback = send_message_callback
        self.bollinger = bt.indicators.BollingerBands(self.data.close)

    def next(self):
        if self.data.close[0] < self.bollinger.lines.bot[0] and not self.position:
            self.buy()
            if self.send_message_callback:
                self.send_message_callback("trade_info", f"BollingerBandsStrategy 买入信号触发")
        elif self.data.close[0] > self.bollinger.lines.top[0] and self.position:
            self.sell()
            if self.send_message_callback:
                self.send_message_callback("trade_info", f"BollingerBandsStrategy 卖出信号触发")
