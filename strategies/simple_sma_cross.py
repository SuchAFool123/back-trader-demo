import backtrader as bt

class SimpleSMACrossStrategy(bt.Strategy):
    """
    简单移动平均线交叉策略
    当短期 SMA 线从下向上穿过长期 SMA 线时，产生买入信号
    当短期 SMA 线从上向下穿过长期 SMA 线时，产生卖出信号
    """
    params = (
        ('short_period', 5),
        ('long_period', 20),
    )

    def __init__(self):
        """
        初始化策略指标
        """
        self.short_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.short_period)
        self.long_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.long_period)
        self.crossover = bt.indicators.CrossOver(self.short_sma, self.long_sma)

    def next(self):
        """
        每个数据点执行的逻辑
        """
        if not self.position:
            if self.crossover > 0:
                self.buy()
                print(f"买入信号，价格: {self.data.close[0]}")
        else:
            if self.crossover < 0:
                self.sell()
                print(f"卖出信号，价格: {self.data.close[0]}")

