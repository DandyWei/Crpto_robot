# import websocket, json
import pandas as pd
from get_bar import *
import datetime as dt
import time
# last_datetime = dt.datetime(2021, 6, 7)
ago = dt.timedelta(hours=10) #(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
update_time_step = dt.timedelta(hours = 1, seconds = 5) #經過五秒立即更新前一根的hr棒
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
# print(dt.datetime.now().replace(microsecond=0))
# print(new_df.index[-1] + dt.timedelta(1, 60)) #day, sec
#以下拿到realtime資料
# cc = 'ethusdt'
# interval = '1m'
# socket = f'wss://stream.binance.com:9443/ws/{cc}@kline_{interval}'
#
# closes, highs, lows = [], [], []
# temp = []
# print('old')
# print(new_df.iloc[-1])
# print('new')


# def on_message(ws, message):
#     json_message = json.loads(message)
#     # print(json_message)
#     candle = json_message['k']
#     is_candle_closed = candle['x']
#     datatime = candle['t'] #大T是最後一根時間
#     open = candle['o']
#     close = candle['c']
#     high = candle['h']
#     low = candle['l']
#     vol = candle['v']
#     # adj_close = candle['c']
#     temp_df = pd.DataFrame([[datatime,open,high,low,close,vol,close]], columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'adj_close'])
#     temp_df.index = [dt.datetime.fromtimestamp(datatime / 1000.0)]
#     temp.append(temp_df)
#     # print(new_df)
#     # new_df.loc[-1] = temp_df
#     print(111)
#     print(222)
#     print(temp_df)
#     if new_df['datetime'][-1] < temp_df['datetime'][0]:
#         print('bang')
#         new_df = pd.concat([new_df, temp_df])
#         print(new_df.loc[-1])
#     elif new_df['datetime'][-1] == temp_df['datetime'][0]:
#         print('怎麼會一樣')
#     else:
#         print('出事了阿伯')
#     # print(new_df)
#
#     if is_candle_closed:
#         temp_df = pd.DataFrame([[datatime,open,high,low,close,vol,close]], columns=['datetime', 'open', 'high', 'low', 'close', 'volume', 'adj_close'])
#         temp_df.index = [dt.datetime.fromtimestamp(datatime / 1000.0)]
#         if new_df['datetime'][-1] < temp_df['datetime'][-1]:
#             print('bangbangbangbang')
#             new_df.append(temp_df)
#             print(new_df)
#         elif new_df['datetime'][-1] == temp_df['datetime'][-1]:
#             print('怎麼會一樣')
#         else:
#             print('出事了阿伯')
#         # closes.append(float(close))
#         # highs.append(float(high))
#         # lows.append(float(low))
#         # print(closes)
#         # print(highs)
#         # print(lows)
#
#
# def on_close(ws):
#     print("### Connection closed ###")
#
#
# ws = websocket.WebSocketApp(url = socket, on_message = on_message, on_close = on_close)
# print(1)
# ws.run()
# print(2)
