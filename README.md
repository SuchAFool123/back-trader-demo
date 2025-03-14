# A 股交易策略回测项目

## 项目简介
本项目基于 Backtrader 库实现了多种 A 股交易策略的回测，包括简单移动平均策略、布林带策略、相对强弱指数策略等。

## 功能特性
- 支持多种交易策略的回测
- 可自定义策略参数
- 可视化回测结果

## 安装依赖pip install -r requirements.txt
## 使用方法
1. 准备 A 股数据，保存为 CSV 文件
2. 修改 `a_share_backtest/main.py` 中的数据文件路径
3. 运行 `python a_share_backtest/main.py` 进行回测

## 代码结构
- `a_share_backtest/strategies/`: 包含各种交易策略的实现
- `a_share_backtest/main.py`: 主程序，负责运行回测和绘制结果

## 贡献
如果你有任何建议或改进，欢迎提交 Pull Request。    