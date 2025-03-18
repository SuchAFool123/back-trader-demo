import backtrader as bt

class MACDStrategy(bt.Strategy):
    def __init__(self, send_message_callback=None):
        self.macd = bt.indicators.MACD(self.data)
        self.send_message_callback = send_message_callback

    def next(self):
        if not self.position:
            if self.macd.macd[0] > self.macd.signal[0]:
                self.buy()
                message = f"MACD 买入信号，日期: {self.data.datetime.date(0)}，价格: {self.data.close[0]}"
                if self.send_message_callback:
                    self.send_message_callback("trade_info", message)
        else:
            if self.macd.macd[0] < self.macd.signal[0]:
                self.sell()
                message = f"MACD 卖出信号，日期: {self.data.datetime.date(0)}，价格: {self.data.close[0]}"
                if self.send_message_callback:
                    self.send_message_callback("trade_info", message)

