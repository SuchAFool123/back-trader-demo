import backtrader as bt
import pandas as pd
import numpy as np
from SmaCross import SmaCross


# 生成模拟数据
def generate_mock_data():
    start_date = pd.Timestamp('2020-01-01')
    end_date = pd.Timestamp('2021-01-01')
    dates = pd.date_range(start=start_date, end=end_date)
    num_days = len(dates)

    # 模拟开盘价、最高价、最低价、收盘价和成交量
    open_prices = np.random.uniform(10, 20, num_days)
    high_prices = open_prices + np.random.uniform(0, 2, num_days)
    low_prices = open_prices - np.random.uniform(0, 2, num_days)
    close_prices = np.random.uniform(low_prices, high_prices)
    volumes = np.random.randint(100000, 1000000, num_days)

    data = {
        'open': open_prices,
        'high': high_prices,
        'low': low_prices,
        'close': close_prices,
        'volume': volumes
    }

    df = pd.DataFrame(data, index=dates)
    return df


# 主函数
def main():
    # 创建 Cerebro 引擎
    cerebro = bt.Cerebro()

    # 添加策略
    cerebro.addstrategy(SmaCross)

    # 生成模拟数据
    mock_data = generate_mock_data()
    data = bt.feeds.PandasData(dataname=mock_data)

    # 将数据添加到 Cerebro 引擎
    cerebro.adddata(data)

    # 设置初始资金
    cerebro.broker.setcash(100000.0)

    # 设置佣金
    cerebro.broker.setcommission(commission=0.001)

    # 打印初始资金
    print('初始资金: %.2f' % cerebro.broker.getvalue())

    # 运行回测
    cerebro.run()

    # 打印最终资金
    print('最终资金: %.2f' % cerebro.broker.getvalue())

    # 绘制回测结果
    cerebro.plot()


if __name__ == '__main__':
    main()
