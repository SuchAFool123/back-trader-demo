from flask import Flask, render_template, request, send_from_directory
from flask_sock import Sock
import backtrader as bt
import tushare as ts
import pandas as pd
import threading
from strategies.simple_sma_cross import SimpleSMACrossStrategy

app = Flask(__name__, template_folder='./templates/')
sock = Sock(app)

# 手动维护的连接列表
connections = []
# 维护每个机器人的停止事件
stop_events = {}

# 设置 tushare token
ts.set_token('85e76ced5ed9d12e83f7e412305b0566ae65840ed47d064aa04a67ee')
pro = ts.pro_api()


def get_historical_data(symbol, start_date, end_date):
    df = pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
    df = df.sort_values(by='trade_date')
    df['datetime'] = pd.to_datetime(df['trade_date'])
    df.set_index('datetime', inplace=True)
    return df


def run_backtest(initial_cash, commission, stock_code, start_date, end_date):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SimpleSMACrossStrategy)

    data = get_historical_data(stock_code, start_date, end_date)
    data_feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)

    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)

    print('初始资金: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('最终资金: %.2f' % cerebro.broker.getvalue())

    # 绘制回测结果
    cerebro.plot()


@app.route('/backtest')
def backtest():
    initial_cash = float(request.args.get('initialCash', 100000))
    commission = float(request.args.get('commission', 0.001))
    stock_code = request.args.get('stockCode', '000858.SZ')
    start_date = request.args.get('startDate', '20230101')
    end_date = request.args.get('endDate', '20231231')

    run_backtest(initial_cash, commission, stock_code, start_date, end_date)
    return "回测完成，请查看控制台输出和绘图结果。"


@app.route('/')
def index():
    return render_template('app.html')

# 定义路由来服务 style.css 文件
@app.route('/style.css')
def serve_css():
    return send_from_directory('templates', 'style.css')

# ... 其他代码 ...

@sock.route('/ws')
def echo(ws):
    initial_cash = float(request.args.get('initialCash', 100000))
    commission = float(request.args.get('commission', 0.001))
    stock_code = request.args.get('stockCode', '000858.SZ')
    connections.append(ws)
    stop_event = threading.Event()
    stop_events[ws] = stop_event
    try:
        threading.Thread(target=run_trading_bot, args=(initial_cash, commission, stock_code, stop_event)).start()
        while True:
            data = ws.receive()
    except Exception:
        pass
    finally:
        stop_event.set()
        if ws in connections:
            connections.remove(ws)
        if ws in stop_events:
            del stop_events[ws]

# ... 其他代码 ...


if __name__ == '__main__':
    app.run(debug=True)

