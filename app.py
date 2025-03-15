from flask import Flask, render_template, request
from flask_sock import Sock
import backtrader as bt
import tushare as ts
import time
import pandas as pd
import threading

app = Flask(__name__, template_folder='./templates/')
sock = Sock(app)

# 全局变量用于控制交易机器人
running = False
stop_event = threading.Event()
# 手动维护的连接列表
connections = []

# 设置 tushare token
ts.set_token('85e76ced5ed9d12e83f7e412305b0566ae65840ed47d064aa04a67ee')
pro = ts.pro_api()


class RealTimeStrategy(bt.Strategy):
    params = (
        ('short_period', 5),
        ('long_period', 20),
        ('max_position_ratio', 0.2),  # 最大仓位比例
        ('stop_loss_ratio', 0.05)  # 止损比例
    )

    def __init__(self):
        self.short_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.short_period)
        self.long_sma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.long_period)
        self.crossover = bt.indicators.CrossOver(self.short_sma, self.long_sma)
        self.stop_loss_price = None

    def next(self):
        if len(self.data) < self.params.long_period:
            return  # 数据量不足，跳过
        current_price = self.data.close[0]
        available_cash = self.broker.getcash()

        if not self.position:
            if self.crossover > 0:
                # 计算可买入的最大数量
                max_amount = available_cash * self.params.max_position_ratio
                size = max_amount // current_price
                self.buy(size=size)
                self.stop_loss_price = current_price * (1 - self.params.stop_loss_ratio)
                message = f"买入信号，价格: {current_price}，买入数量: {size}，止损价格: {self.stop_loss_price}"
                print(message)
                # 向所有连接的客户端发送消息
                for conn in connections:
                    try:
                        conn.send(message)
                    except Exception as e:
                        print(f"发送消息到客户端时出错: {e}")
        else:
            if self.crossover < 0:
                self.sell()
                self.stop_loss_price = None
                message = f"卖出信号，价格: {current_price}"
                print(message)
                # 向所有连接的客户端发送消息
                for conn in connections:
                    try:
                        conn.send(message)
                    except Exception as e:
                        print(f"发送消息到客户端时出错: {e}")
            elif current_price <= self.stop_loss_price:
                self.sell()
                self.stop_loss_price = None
                message = f"止损卖出，价格: {current_price}"
                print(message)
                # 向所有连接的客户端发送消息
                for conn in connections:
                    try:
                        conn.send(message)
                    except Exception as e:
                        print(f"发送消息到客户端时出错: {e}")


def get_realtime_data(symbol):
    buffer = []
    min_period = 20  # 最小数据周期
    while not stop_event.is_set():
        try:
            # 获取当前日期
            today = pd.Timestamp.now().strftime('%Y%m%d')
            df = pro.daily(ts_code=symbol, start_date=today, end_date=today)
            if not df.empty:
                data = df.iloc[0]
                item = {
                    'datetime': pd.Timestamp.now(),
                    'open': float(data['open']),
                    'high': float(data['high']),
                    'low': float(data['low']),
                    'close': float(data['close']),
                    'volume': float(data['vol'])
                }
                buffer.append(item)
                if len(buffer) >= min_period:
                    yield buffer.pop(0)
            time.sleep(60)  # 每分钟获取一次数据
        except Exception as e:
            message = f"获取数据出错: {e}，股票代码: {symbol}"
            print(message)
            # 向所有连接的客户端发送消息
            for conn in connections:
                try:
                    conn.send(message)
                except Exception as e:
                    print(f"发送消息到客户端时出错: {e}")
            time.sleep(60)


def run_trading_bot(initial_cash, commission, stock_code):
    global running
    running = True

    # 创建 Cerebro 引擎
    cerebro = bt.Cerebro()

    # 添加策略
    cerebro.addstrategy(RealTimeStrategy)

    # 创建自定义数据馈送
    data_feed = bt.feeds.PandasData(dataname=pd.DataFrame(get_realtime_data(stock_code)))
    cerebro.adddata(data_feed)

    # 设置初始资金
    cerebro.broker.setcash(initial_cash)

    # 设置佣金
    cerebro.broker.setcommission(commission=commission)

    print('初始资金: %.2f' % cerebro.broker.getvalue())

    # 运行回测
    cerebro.run()

    print('最终资金: %.2f' % cerebro.broker.getvalue())
    running = False


@app.route('/')
def index():
    return render_template('app.html')


@sock.route('/ws')
def echo(ws):
    global running
    if not running:
        stop_event.clear()
        initial_cash = float(request.args.get('initialCash', 100000))
        commission = float(request.args.get('commission', 0.001))
        stock_code = request.args.get('stockCode', '000858.SZ')
        threading.Thread(target=run_trading_bot, args=(initial_cash, commission, stock_code)).start()
    try:
        connections.append(ws)
        while True:
            data = ws.receive()
    except Exception:
        stop_event.set()
    finally:
        if ws in connections:
            connections.remove(ws)


if __name__ == '__main__':
    app.run(debug=True)
