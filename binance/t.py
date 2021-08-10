from unicorn_binance_websocket_api.unicorn_binance_websocket_api_manager import BinanceWebSocketApiManager
import logging
import time
import threading
import os
import json
import ccxt
# https://docs.python.org/3/library/logging.html#logging-levels
from config import *


k = Keys()
api_Key = k.api_Key
secret_Key = k.secret_Key


class info_trade:
    def __init__(self,):
        logging.basicConfig(level=logging.INFO,
                            filename=os.path.basename(__file__) + '.log',
                            format="{asctime} [{levelname:8}] {process} {thread} {module}: {message}",
                            style="{")
        self.__api_key = api_Key
        self.__api_secret = secret_Key
        self.exchange = ccxt.binance({
            'apiKey': self.__api_key,
            'secret': self.__api_secret,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
        self.exchange.load_markets()

    def print_stream_data_from_stream_buffer(self, binance_websocket_api_manager):
        while True:
            if binance_websocket_api_manager.is_manager_stopping():
                exit(0)
            oldest_stream_data_from_stream_buffer = binance_websocket_api_manager.pop_stream_data_from_stream_buffer()
            if oldest_stream_data_from_stream_buffer is False:
                time.sleep(1)
            else:
                # oldest_stream_data_from_stream_buffer
                print(oldest_stream_data_from_stream_buffer)

    def run(self,):
        # configure api key and secret for binance.com

        # exchange = ccxt.binance({
        #     'apiKey': api_key,
        #     'secret': api_secret,
        #     'enableRateLimit': True,
        #     'options': {'defaultType': 'future'}
        # })
        # exchange.load_markets()

        # create instances of BinanceWebSocketApiManager
        ubwa_com = BinanceWebSocketApiManager(exchange="binance.com-futures")

        # create the userData streams
        user_stream_id = ubwa_com.create_stream(
            'arr', '!userData', api_key=self.__api_key, api_secret=self.__api_secret)

        # start a worker process to move the received stream_data from the stream_buffer to a print function
        # worker_thread = threading.Thread(
        #     target=self.print_stream_data_from_stream_buffer, args=(ubwa_com,))
        # worker_thread.start()

        # monitor the streams
        dict = {
            "ETHUSDT": 'ETH/USDT',
            "BNBUSDT": 'BNB/USDT',
            "LINKUSDT": 'LINK/USDT',

        }
        while True:
            oldest_stream_data_from_stream_buffer = ubwa_com.pop_stream_data_from_stream_buffer()
            if oldest_stream_data_from_stream_buffer:
                data = json.loads(oldest_stream_data_from_stream_buffer)
                if data['e'] == "ACCOUNT_UPDATE":  # 下單市顯示 ORDER_TRADE_UPDATE
                    print('成交')
                if data['e'] == "ORDER_TRADE_UPDATE":
                    if data['o']['o'] in ["STOP_MARKET", 'TAKE_PROFIT_MARKET']:
                        print('設置TP/SL單')
                        Symbol = dict[data['o']['s']]
                        print('symbol', Symbol)
                        Execution_Type = data['o']['x']  # "NEW"  "CANCELED"
                        print('Execution_Type', Execution_Type)
                        if Execution_Type == 'EXPIRED':
                            print('觸發 : ', data['o']['o'])
                            self.exchange.cancel_all_orders(Symbol)
                print('Im alive')
            time.sleep(1)


def cancel_TP_SL():
    info_trade().run()


# if __name__ == '__main__':
#     cancel_TP_SL()
