import eventlet

eventlet.monkey_patch()

from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO
import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta
import tushare as ts

app = Flask(__name__, template_folder='./templates/')
socketio = SocketIO(app)

# 设置 tushare token
ts.set_token('85e76ced5ed9d12e83f7e412305b0566ae65840ed47d064aa04a67ee')
pro = ts.pro_api()

# 策略类导入
from strategies.default_strategy import DefaultStrategy
from strategies.macd_strategy import MACDStrategy

# 策略映射
STRATEGIES = {
    'default': DefaultStrategy,
    'macd': MACDStrategy
}


def get_historical_data(symbol):
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    df = pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
    if df.empty:
        print(f"未获取到 {symbol} 的历史数据，请检查股票代码或数据接口。")
        return None
    df = df.sort_values(by='trade_date')
    df['datetime'] = pd.to_datetime(df['trade_date'])
    df.set_index('datetime', inplace=True)
    return df


# ... 现有代码 ...

def run_backtest(initial_cash, commission, stock_code, strategy_name, send_message_callback):
    cerebro = bt.Cerebro()
    strategy_class = STRATEGIES.get(strategy_name)
    if not strategy_class:
        print(f"未知策略: {strategy_name}")
        return
    cerebro.addstrategy(strategy_class, send_message_callback=send_message_callback)
    data = get_historical_data(stock_code)
    if data is None:
        return
    data_feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    print('初始资金: %.2f' % cerebro.broker.getvalue())
    initial_value = cerebro.broker.getvalue()

    class TradeObserver(bt.Observer):
        lines = ('total_value', 'profit',)

        def __init__(self):
            self.initial_value = initial_value

        def next(self):
            total_value = self._owner.broker.getvalue()
            profit = total_value - self.initial_value
            self.lines.total_value[0] = total_value
            self.lines.profit[0] = profit
            send_message_callback("total_info", f"当前总金额: {total_value:.2f}，总收益: {profit:.2f}")

    cerebro.addobserver(TradeObserver)

    cerebro.run()
    final_value = cerebro.broker.getvalue()
    profit = final_value - initial_value
    send_message_callback("total_info", f"当前总金额: {final_value:.2f}，总收益: {profit:.2f}")
    return final_value, profit

    # ... 现有代码 ...

    def on_trade(trade):
        if trade.isclosed:
            total_value = cerebro.broker.getvalue()
            profit = total_value - initial_value
            send_message_callback("total_info", f"当前总金额: {total_value:.2f}，总收益: {profit:.2f}")

    cerebro.addobserver(bt.observers.Trades)
    cerebro.addcallback('on_trade', on_trade)

    cerebro.run()
    final_value = cerebro.broker.getvalue()
    profit = final_value - initial_value
    send_message_callback("total_info", f"当前总金额: {final_value:.2f}，总收益: {profit:.2f}")
    return final_value, profit


@app.route('/')
def index():
    return render_template('app.html')


@app.route('/backtest')
def backtest():
    strategy = request.args.get('strategy', 'default')
    initial_cash = float(request.args.get('initialCash', 100000))
    commission = float(request.args.get('commission', 0.001))
    stock_code = request.args.get('stockCode', '000858.SZ')

    def send_message(event_type, message):
        socketio.emit(event_type, message)

    final_value, profit = run_backtest(initial_cash, commission, stock_code, strategy, send_message)
    socketio.emit('stop_info', f"当前总金额: {final_value:.2f}，总收益: {profit:.2f}")
    return "Backtest completed"


# 定义路由来服务 style.css 文件
@app.route('/style.css')
def serve_css():
    return send_from_directory('templates', 'style.css')


if __name__ == '__main__':
    socketio.run(app, debug=True)
