from flask import Flask, render_template, request ,send_from_directory
from flask_sock import Sock
import backtrader as bt
import tushare as ts
import time
import pandas as pd
import threading
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='./templates/')
sock = Sock(app)

# 手动维护的连接列表
connections = []
# 维护每个机器人的停止事件
stop_events = {}

# 设置 tushare token
ts.set_token('85e76ced5ed9d12e83f7e412305b0566ae65840ed47d064aa04a67ee')
pro = ts.pro_api()


class SMACross(bt.Strategy):
    params = (
        ('fast', 5),
        ('slow', 20),
    )

    def __init__(self):
        self.sma_fast = bt.indicators.SMA(self.data.close, period=self.p.fast)
        self.sma_slow = bt.indicators.SMA(self.data.close, period=self.p.slow)
        self.crossover = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)

    def next(self):
        print(f"当前收盘价: {self.data.close[0]}, 快速均线: {self.sma_fast[0]}, 慢速均线: {self.sma_slow[0]}")
        if not self.position:
            if self.crossover > 0:
                print("发出买入信号")
                self.buy()
        elif self.crossover < 0:
            print("发出卖出信号")
            self.sell()


class MACD(bt.Strategy):
    params = (
        ('fast', 12),
        ('slow', 26),
        ('signal', 9),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.p.fast,
            period_me2=self.p.slow,
            period_signal=self.p.signal
        )
        self.macd_crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

    def next(self):
        print(f"当前 MACD: {self.macd.macd[0]}, 信号线: {self.macd.signal[0]}")
        if not self.position:
            if self.macd_crossover > 0:
                print("发出买入信号")
                self.buy()
        elif self.macd_crossover < 0:
            print("发出卖出信号")
            self.sell()


class StrategySwitcher(bt.Strategy):
    params = (
        ('strategy_name', 'smacross'),
    )

    def __init__(self):
        strategy_map = {
            'smacross': SMACross,
            'macd': MACD
        }
        self.strategy = strategy_map[self.p.strategy_name](self.data)

    def next(self):
        self.strategy.next()


# ... 已有代码 ...

def get_realtime_data(symbol, stop_event):
    buffer = []
    min_period = 26  # 考虑MACD最大周期
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
    try:
        print(f"Fetching data for {symbol} from {start_date} to {end_date}")
        df = pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
        if not df.empty:
            df = df.sort_values(by='trade_date')
            for _, row in df.iterrows():
                item = {
                    'datetime': pd.Timestamp(row['trade_date']),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['vol'])
                }
                buffer.append(item)
                data_str = f"日期: {item['datetime']}, 开盘价: {item['open']}, 最高价: {item['high']}, 最低价: {item['low']}, 收盘价: {item['close']}, 成交量: {item['volume']}"
                print(data_str)
                # 向所有连接的客户端发送数据
                for conn in connections:
                    try:
                        conn.send(data_str)
                    except Exception as e:
                        print(f"发送消息到客户端时出错: {e}")
            while len(buffer) >= min_period:
                yield buffer.pop(0)
    except Exception as e:
        message = f"获取数据出错: {e}，股票代码: {symbol}"
        print(message)
        # 向所有连接的客户端发送消息
        for conn in connections:
            try:
                conn.send(message)
            except Exception as e:
                print(f"发送消息到客户端时出错: {e}")

# ... 已有代码 ...


def run_trading_bot(initial_cash, commission, stock_code, stop_event, strategy_name):
    try:
        print(f"Starting trading bot with strategy: {strategy_name}")
        # 创建 Cerebro 引擎
        cerebro = bt.Cerebro()

        # 添加策略
        cerebro.addstrategy(StrategySwitcher, strategy_name=strategy_name)

        # 创建自定义数据馈送
        data_feed = bt.feeds.PandasData(dataname=pd.DataFrame(get_realtime_data(stock_code, stop_event)))
        cerebro.adddata(data_feed)

        # 设置初始资金
        cerebro.broker.setcash(initial_cash)

        # 设置佣金
        cerebro.broker.setcommission(commission=commission)

        print('初始资金: %.2f' % cerebro.broker.getvalue())

        # 运行回测
        cerebro.run()

        print('最终资金: %.2f' % cerebro.broker.getvalue())
    except Exception as e:
        print(f"Error in run_trading_bot: {e}")


@sock.route('/ws')
def echo(ws):
    try:
        initial_cash = float(request.args.get('initialCash', 100000))
        commission = float(request.args.get('commission', 0.001))
        stock_code = request.args.get('stockCode', '000858.SZ')
        strategy_name = request.args.get('strategy', 'smacross')

        connections.append(ws)
        stop_event = threading.Event()
        stop_events[ws] = stop_event

        print(f"New WebSocket connection. Strategy: {strategy_name}, Stock: {stock_code}")
        threading.Thread(target=run_trading_bot, args=(initial_cash, commission, stock_code, stop_event, strategy_name)).start()
        while True:
            data = ws.receive()
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        stop_event.set()
        if ws in connections:
            connections.remove(ws)
        if ws in stop_events:
            del stop_events[ws]

# 定义路由来服务 style.css 文件
@app.route('/style.css')
def serve_css():
    return send_from_directory('templates', 'style.css')


@app.route('/')
def index():
    return render_template('app.html')


if __name__ == '__main__':
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"Flask app error: {e}")

