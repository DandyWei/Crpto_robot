import json
import requests 
import pandas as pd
import datetime as dt



class Get_bars:
    # 建構式
    def __init__(self, symbol, interval, startTime, endTime):
        self.symbol = symbol
        self.interval = interval
        self.startTime = startTime
        self.endTime = endTime
    
    def get_binance_bars(self):
        
        url = "https://api.binance.com/api/v3/klines"
        
        startTime = str(int(self.startTime.timestamp() * 1000))
        endTime = str(int(self.endTime.timestamp() * 1000))
        limit = '1000'
        
        req_params = {"symbol" : self.symbol, 'interval' : self.interval, 'startTime' : startTime, 'endTime' : endTime, 'limit' : limit}
        
        df = pd.DataFrame(json.loads(requests.get(url, params = req_params).text))
        
        if (len(df.index) == 0):
            return None
        
        
        df = df.iloc[:, 0:6]
        df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
     
        df.open      = df.open.astype("float")
        df.high      = df.high.astype("float")
        df.low       = df.low.astype("float")
        df.close     = df.close.astype("float")
        df.volume    = df.volume.astype("float")
        
        df['adj_close'] = df['close']
        
        df.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in df.datetime]

        return df




#if __name__ == '__main__':
#    
#    
#    df_list = []
#    # 数据起点时间
#    last_datetime = dt.datetime(2021, 1, 1)
#    
#    trade_currency = 'ETHUSDT'
#    
#    while True:
##        new_df = get_binance_bars(trade_currency, '1h', last_datetime, dt.datetime.now())           # 獲取一小時數據
#        bars_fun = Get_bars(trade_currency, '1h', last_datetime, dt.datetime.now())           # 獲取一小時數據
#        new_df = bars_fun.get_binance_bars()
#        
#        if new_df is None:
#            break
#        df_list.append(new_df)
#        last_datetime = max(new_df.index) + dt.timedelta(0, 1)
#    
#    df = pd.concat(df_list)
#    df.shape
#    
#    print('k线数量\n', len(df)) 
#    
#    print(df)