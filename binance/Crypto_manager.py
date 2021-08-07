from ccxtbt import CCXTStore
import backtrader as bt
from datetime import datetime, timedelta
import json
import ccxt
import math
from all_crypto import *
from t import *
import threading


def main():
    cerebro = bt.Cerebro(quicknotify=True)

    # Add the strategy
    # cerebro.addstrategy(Bianance_Strategy)

    cerebro.addstrategy(Trade_pro)

    # Create our store
    config = {'apiKey': api_Key,
              'secret': secret_Key,
              'enableRateLimit': True,
              'options': {
                  'defaultType': 'future',  # ←-------------- quotes and 'future'
              },
              }

    # IMPORTANT NOTE - Kraken (and some other exchanges) will not return any values
    # for get cash or value if You have never held any BNB coins in your account.
    # So switch BNB to a coin you have funded previously if you get errors
    store = CCXTStore(exchange='binance', currency='BNB', config=config, retries=5, debug=False)
    # exchange = ccxt.binance(
    #             config
    #           )
    #
    # markets = exchange.load_markets()
    # exchange.verbose = True

    # balance = exchange.fetch_balance()

    # Get the broker and pass any kwargs if needed.
    # ----------------------------------------------
    # Broker mappings have been added since some exchanges expect different values
    # to the defaults. Case in point, Kraken vs Bitmex. NOTE: Broker mappings are not
    # required if the broker uses the same values as the defaults in CCXTBroker.
    broker_mapping = {
        'order_types': {
            bt.Order.Market: 'market',
            bt.Order.Limit: 'limit',
            bt.Order.Stop: 'stop-loss',  # stop-loss for kraken, stop for bitmex
            bt.Order.StopLimit: 'stop limit'
        },
        'mappings': {
            'closed_order': {
                'key': 'status',
                'value': 'closed'
            },
            'canceled_order': {
                'key': 'result',
                'value': 1}
        }
    }

    broker = store.getbroker(broker_mapping=broker_mapping)
    cerebro.setbroker(broker)

    # Get our data
    # Drop newest will prevent us from loading partial data from incomplete candles
    '''檢查點'''
    hist_start_date = datetime.utcnow() - \
        timedelta(
            hours=150)  # days=999999999, hours=23, minutes=59, seconds=59 days=2,hours=23 days=2,hours=23
    data1 = store.getdata(dataname='ETH/USDT', name="ETH/USDT",
                          timeframe=bt.TimeFrame.Minutes, fromdate=hist_start_date,
                          compression=5, ohlcv_limit=9999, drop_newest=True)  # , historical=True)
    # data2 = store.getdata(dataname='BNB/USDT', name="BNB/USDT",
    #                       timeframe=bt.TimeFrame.Minutes, fromdate=hist_start_date,
    #                       compression=15, ohlcv_limit=9999, drop_newest=True)  # , historical=True)
    #
    # data3 = store.getdata(dataname='LINK/USDT', name="LINK/USDT",
    #                       timeframe=bt.TimeFrame.Minutes, fromdate=hist_start_date,
    #                       compression=15, ohlcv_limit=9999, drop_newest=True)  # , historical=True)
    # data4 = store.getdata(dataname='ETH/USDT', name="ETH/USDT",
    #                       timeframe=bt.TimeFrame.Minutes, fromdate=hist_start_date,
    #                       compression=1, ohlcv_limit=9999, drop_newest=True)  # , historical=True)
    # Add the feed
    # cerebro.resampledata(data1, timeframe=bt.TimeFrame.Minutes,compression=30)
    cerebro.adddata(data1)
    # cerebro.adddata(data2)
    # cerebro.adddata(data3)
    # cerebro.adddata(data4)
    # Run the strategy
    cerebro.run()


if __name__ == '__main__':
    worker_thread = threading.Thread(target=cancel_TP_SL)
    worker_thread.start()
    main()
