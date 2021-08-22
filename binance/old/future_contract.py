from binance_f import RequestClient
from binance_f.model import *
from binance_f.constant.test import *
from binance_f.base.printobject import *
import time
import pandas as pd
import datetime as dt
'''
#這部分可以拿到
https://www.binance.com/zh-TW/futures/BTCUSDT
的realtimedata
request_client = RequestClient(api_key=g_api_key, secret_key=g_secret_key)

result = request_client.get_symbol_price_ticker('BTCUSDT')
# result = request_client.get_symbol_price_ticker(symbol="BTCUSDT")
while 1:
	print("======= Symbol Price Ticker =======")
	result = request_client.get_symbol_price_ticker('BTCUSDT')
	PrintMix.print_data(result)
	time.sleep(1)
	print("===================================")
'''

request_client = RequestClient(api_key=g_api_key, secret_key=g_secret_key)
req_params = {"symbol" : "BTCUSDT", 'interval' : CandlestickInterval.MIN1, 'startTime' : dt.datetime(2021,1,7), 'endTime' : dt.datetime(2021,1,8), 'limit' : 1000}
result = request_client.get_candlestick_data(req_params)
#
# print("======= Kline/Candlestick Data =======")
# PrintMix.print_data(result)
# print("======================================")
# print(type(result) )
# print(result[1].openTime )

print('-'*50)
print(len(result))
ls = [ [x.openTime, x.open, x.high, x.close, x.low, x.volume ] for x in result]
df  = pd.DataFrame(ls)
df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
df.open      = df.open.astype("float")
df.high      = df.high.astype("float")
df.low       = df.low.astype("float")
df.close     = df.close.astype("float")
df.volume    = df.volume.astype("float")
df['adj_close'] = df['close']
df.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in df.datetime]
print(df)
