import backtrader as bt
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
import datetime as dt
from ccxtbt import CCXTStore
import ccxt
import math
import time
from pprint import pprint
from config import *


k = Keys()
api_Key = k.api_Key
secret_Key = k.secret_Key

exchange = ccxt.binance({
    'apiKey': api_Key,
    'secret': secret_Key,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})
exchange.load_markets()
exchange.market('ETH/USDT')
symbol = 'ETH/USDT'
amount = 0.007
order1 = exchange.create_order('ETH/USDT', 'market', 'buy', amount)
order1_price = order1['price']
if order1_price is None:
    order1_price = order1['average']
if order1_price is None:
    cumulative_quote = float(order1['info']['cumQuote'])
    executed_quantity = float(order1['info']['executedQty'])
    order1_price = cumulative_quote / executed_quantity

# pprint(order1)
# time.sleep(0.5)
print('---------------------------------------------------------------------')

stop_loss_params = {'stopPrice': order1_price * 0.999}
order2 = exchange.create_order(symbol, 'stop_market', 'sell', amount, None, stop_loss_params)
# pprint(order2)

print('---------------------------------------------------------------------')

take_profit_params = {'stopPrice': order1_price * 1.001}
order3 = exchange.create_order(symbol, 'take_profit_market', 'sell',
                               amount, None, take_profit_params)
# pprint(order3)
