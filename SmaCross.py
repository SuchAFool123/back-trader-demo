import backtrader as bt


# 定义双均线交叉策略
class SmaCross(bt.Strategy):
    params = (
        ('pfast', 5),  # 短期均线周期
        ('pslow', 20),  # 长期均线周期
    )

    def __init__(self):
        sma1 = bt.ind.SMA(period=self.p.pfast)  # 短期均线
        sma2 = bt.ind.SMA(period=self.p.pslow)  # 长期均线
        self.crossover = bt.ind.CrossOver(sma1, sma2)  # 交叉信号

    def next(self):
        if not self.position:  # 如果没有持仓
            if self.crossover > 0:  # 短期均线上穿长期均线
                self.buy()  # 买入
        elif self.crossover < 0:  # 短期均线下穿长期均线
            self.sell()  # 卖出
