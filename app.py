import eventlet

eventlet.monkey_patch()

from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO
import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta
import tushare as ts
import importlib
import os

app = Flask(__name__, template_folder='./templates/')
socketio = SocketIO(app)

# 设置 tushare token
ts.set_token('85e76ced5ed9d12e83f7e412305b0566ae65840ed47d064aa04a67ee')
pro = ts.pro_api()

# 动态导入 strategies 目录下的所有策略类
STRATEGIES = {}
strategies_dir = os.path.join(os.path.dirname(__file__), 'strategies')
for filename in os.listdir(strategies_dir):
    if filename.endswith('.py') and not filename.startswith('__'):
        module_name = f'strategies.{filename[:-3]}'
        module = importlib.import_module(module_name)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, bt.Strategy) and attr != bt.Strategy:
                strategy_name = attr.__name__.lower()
                STRATEGIES[strategy_name] = attr


def get_historical_data(symbol):
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=365 * 2)).strftime('%Y%m%d')
    df = pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
    if df.empty:
        print(f"未获取到 {symbol} 的历史数据，请检查股票代码或数据接口。")
        return None
    df = df.sort_values(by='trade_date')
    df['datetime'] = pd.to_datetime(df['trade_date'])
    df.set_index('datetime', inplace=True)
    return df


# ... 已有代码 ...

def run_backtest(initial_cash, commission, stock_code, strategy_name, send_message_callback):
    cerebro = bt.Cerebro()
    strategy_class = STRATEGIES.get(strategy_name)
    if not strategy_class:
        print(f"未知策略: {strategy_name}")
        return
    # 传入 send_message_callback
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
            if self._owner.position:
                total_value = self._owner.broker.getvalue()
                profit = total_value - self.initial_value
                send_message_callback("total_info", f"当前总金额: {total_value:.2f}，总收益: {profit:.2f}")

    cerebro.addobserver(TradeObserver)

    # 发送历史数据
    data_str = data.to_csv(sep='\t', na_rep='nan')
    send_message_callback("historical_data", data_str)

    cerebro.run()
    final_value = cerebro.broker.getvalue()
    profit = final_value - initial_value
    send_message_callback("total_info", f"当前总金额: {final_value:.2f}，总收益: {profit:.2f}")
    return final_value, profit

# ... 已有代码 ...



@app.route('/')
def index():
    # 获取所有策略名称
    strategy_names = list(STRATEGIES.keys())
    return render_template('app.html', strategies=strategy_names)



# ... 之前的代码 ...

@app.route('/backtest')
def backtest():
    strategy = request.args.get('strategy', 'default')
    initial_cash = float(request.args.get('initialCash', 100000))
    commission = float(request.args.get('commission', 0.001))
    stock_code = request.args.get('stockCode', '000858.SZ')

    def send_message(event_type, message):
        socketio.emit(event_type, message)

    result = run_backtest(initial_cash, commission, stock_code, strategy, send_message)
    if result is not None:
        final_value, profit = result
        socketio.emit('stop_info', f"当前总金额: {final_value:.2f}，总收益: {profit:.2f}")
        return "Backtest completed"
    else:
        return "Backtest failed due to data retrieval issue."

    # ... 后续代码 ...


# ... 之前的代码 ...

# 定义路由来服务 style.css 文件
@app.route('/style.css')
def serve_css():
    return send_from_directory('templates', 'style.css')


if __name__ == '__main__':
    socketio.run(app, debug=True)
