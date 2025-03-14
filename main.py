import backtrader as bt
import pandas as pd
from SmaCross import SmaCross
from SMAStrategy import SMAStrategy
from BollingerBandsStrategy import BollingerBandsStrategy
from RSIStrategy import RSIStrategy
from SMAVolumeStrategy import SMAVolumeStrategy


def run_backtest(strategy):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy)

    try:
        data = pd.read_csv('your_stock_data.csv', parse_dates=True, index_col=0)
        data = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(data)
    except FileNotFoundError:
        print("错误：未找到数据文件 'your_stock_data.csv'，请检查文件路径。")
        return

    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)

    print('初始资金: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('最终资金: %.2f' % cerebro.broker.getvalue())
    try:
        cerebro.plot()
    except Exception as e:
        print(f"绘制图表时出错: {e}")


# 运行不同策略的回测
strategies = [SmaCross, SMAStrategy, BollingerBandsStrategy, RSIStrategy, SMAVolumeStrategy]
for strategy in strategies:
    print(f"正在运行 {strategy.__name__} 策略回测...")
    run_backtest(strategy)
