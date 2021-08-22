import datetime as dt
import pandas as pd
import backtrader as bt
from get_bar import *
from Strategy import *




if __name__ == '__main__':

    df_list = []
    # 数据起点时间
    last_datetime = dt.datetime(2021, 6, 1)

    trade_currency = 'LINKUSDT'

    while True:
#        new_df = get_binance_bars(trade_currency, '1h', last_datetime, dt.datetime.now())           # 獲取一小時數據
        bars_fun = Get_bars(trade_currency, '1h', last_datetime, dt.datetime.now())           # 獲取一小時數據
        new_df = bars_fun.get_binance_bars()

        if new_df is None:
            break
        df_list.append(new_df)
        last_datetime = max(new_df.index) + dt.timedelta(0, 1)

    df = pd.concat(df_list)
    df.shape

    cerebro = bt.Cerebro()
    print('k线数量', len(df))
    data = bt.feeds.PandasData(dataname = df)
    cerebro.adddata(data) #data會空16行 [-1]為第15行


    cerebro.addstrategy(MaCrossStrategy)
    cerebro.broker.setcash(1000000.0)

    # cerebro.addsizer(bt.sizers.PercentSizer, percents = 99)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Minutes, _name = "sharpe")
    cerebro.addanalyzer(bt.analyzers.Transactions, _name = "trans")
    #add analyzer

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.broker.setcommission(commission=0.0003) #,margin=False, mult = 2
    # cerebro.broker.set_coc(True)
    back = cerebro.run()
    cerebro.plot()
