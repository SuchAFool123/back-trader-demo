import backtrader as bt

class SimpleSMACrossStrategy(bt.Strategy):
    def __init__(self, send_message_callback=None):
        self.send_message_callback = send_message_callback
        # 其他初始化代码
        self.sma_fast = bt.indicators.SimpleMovingAverage(self.data.close, period=5)
        self.sma_slow = bt.indicators.SimpleMovingAverage(self.data.close, period=20)

    def next(self):
        if self.sma_fast[0] > self.sma_slow[0] and self.sma_fast[-1] <= self.sma_slow[-1]:
            self.buy()
            if self.send_message_callback:
                self.send_message_callback("trade_info", f"买入信号触发，当前策略: {self.__class__.__name__}")
        elif self.sma_fast[0] < self.sma_slow[0] and self.sma_fast[-1] >= self.sma_slow[-1]:
            self.sell()
            if self.send_message_callback:
                self.send_message_callback("trade_info", f"卖出信号触发，当前策略: {self.__class__.__name__}")

