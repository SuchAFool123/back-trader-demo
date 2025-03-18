import backtrader as bt

class DefaultStrategy(bt.Strategy):
    def __init__(self, send_message_callback=None):
        self.send_message_callback = send_message_callback

    def next(self):
        if len(self.data) < 3:
            return
        if not self.position:
            if self.data.close[0] > self.data.close[-1] and self.data.close[-1] > self.data.close[-2]:
                self.buy()
                message = f"买入信号，日期: {self.data.datetime.date(0)}，价格: {self.data.close[0]}"
                if self.send_message_callback:
                    self.send_message_callback("trade_info", message)
        else:
            if self.data.close[0] < self.data.close[-1] and self.data.close[-1] < self.data.close[-2]:
                self.sell()
                message = f"卖出信号，日期: {self.data.datetime.date(0)}，价格: {self.data.close[0]}"
                if self.send_message_callback:
                    self.send_message_callback("trade_info", message)

