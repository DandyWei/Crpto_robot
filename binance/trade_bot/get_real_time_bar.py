# import websocket, json
import pandas as pd
from get_bar import *
import datetime as dt
import time
# last_datetime = dt.datetime(2021, 6, 7)
#拿10根hr做演算法計算
ago = dt.timedelta(hours=10) #(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
update_time_step = dt.timedelta(hours = 1, seconds = 1) #經過1秒立即更新前一根的hr棒,要+1hr因為當下時間的hr棒會動態更新
last_datetime = dt.datetime(2021, 6, 7) - ago
trade_currency = 'ETHUSDT'
time_period = '1h'
bars_fun = Get_bars(trade_currency, time_period, last_datetime, dt.datetime.now())           # 獲取一小時數據
new_df = bars_fun.get_binance_bars()
while True:
    # last_datetime = dt.datetime(2021, 6, 7)
    # trade_currency = 'ETHUSDT'
    #
    # bars_fun = Get_bars(trade_currency, '1m', last_datetime, dt.datetime.now())           # 獲取一小時數據
    # new_df = bars_fun.get_binance_bars()
    if dt.datetime.now() > new_df.index[-1] + update_time_step:#多10分鐘了
        print('time now : ', dt.datetime.now())
        print('time update : ', new_df.index[-1] + update_time_step)
        print('該更新了')
        new_last_datetime = dt.datetime.now() - ago ##拿到現在前10分鐘前的資料來玩玩
        bars_fun = Get_bars(trade_currency, time_period, new_last_datetime, dt.datetime.now())           # 獲取一小時數據
        new_df = bars_fun.get_binance_bars()
        print(new_df)
        print(new_df.shape)
    else:
        print(new_df)
        print('time now : ', dt.datetime.now())
        print('time update : ', new_df.index[-1] + update_time_step)
        print(bars_fun.get_binance_bars().iloc[-1]['close'])
        print('沒事')
        time.sleep(5)
