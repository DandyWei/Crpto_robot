import os
import sys
from pprint import pprint

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

import ccxt  # noqa: E402
api_Key = 'nux5568AFIq0eL63qdQpsFHgG08nKGg3aO3FRDduzxhxOTx3l3FN1kpMTyXbE8it'
secret_Key ='kgj4GJz65eqaumiBH0Bgu4L7eaG4eVqJc9u6UZ12ykChYaMgbN6fZDzYr5EO0fyl'
print('CCXT Version:', ccxt.__version__)



def table(values):
    first = values[0]
    keys = list(first.keys()) if isinstance(first, dict) else range(0, len(first))
    widths = [max([len(str(v[k])) for v in values]) for k in keys]
    string = ' | '.join(['{:<' + str(w) + '}' for w in widths])
    return "\n".join([string.format(*[str(v[k]) for k in keys]) for v in values])


exchange = ccxt.binance({
    'apiKey': api_Key,
    'secret': secret_Key,
    'enableRateLimit': True, # required https://github.com/ccxt/ccxt/wiki/Manual#rate-limit
    'options': {
        'defaultType': 'future',
    },
})

markets = exchange.load_markets()

symbol = 'ETH/USDT'  # YOUR SYMBOL HERE
market = exchange.market(symbol)

exchange.verbose = True  # UNCOMMENT THIS AFTER LOADING THE MARKETS FOR DEBUGGING

print('----------------------------------------------------------------------')

print('Fetching your balance:')
# response = exchange.fetch_balance()
# for i in response['free']:
#     pprint(i)  # make sure you have enough futures margin...
# pprint(response['info'])  # more details

print('----------------------------------------------------------------------')

# https://binance-docs.github.io/apidocs/futures/en/#position-information-v2-user_data

print('Getting your positions:')
response = exchange.fapiPrivateV2_get_positionrisk()
# for i in response:
symbols = ['ETHUSDT','BNBUSDT','LINKUSDT']
allcrypto = [x for x in response if x['symbol'] in symbols]
# print(allcrypto)
position_size_eth = [x['positionAmt'] for x in allcrypto if symbols[0] == x['symbol'] ][0]
entryP_eth = [x['entryPrice'] for x in allcrypto if symbols[0] == x['symbol'] ][0]
print(position_size_eth, entryP_eth)
    # if i['entryPrice'] != 0:
    #     print(i['entryPrice'] )
# exchange.cancel_all_orders('ETH/USDT')
print('----------------------------------------------------------------------')

# https://binance-docs.github.io/apidocs/futures/en/#change-position-mode-trade

# print('Getting your current position mode (One-way or Hedge Mode):')
# response = exchange.fapiPrivate_get_positionside_dual()
# if response['dualSidePosition']:
#     print('You are in Hedge Mode')
# else:
#     print('You are in One-way Mode')
#
# print('----------------------------------------------------------------------')

# print('Setting your position mode to One-way:')
# response = exchange.fapiPrivate_post_positionside_dual({
#     'dualSidePosition': False,
# })
# print(response)

# print('Setting your positions to Hedge mode:')
# response = exchange.fapiPrivate_post_positionside_dual({
#     'dualSidePosition': True,
# })
# print(response)

# print('----------------------------------------------------------------------')

# # https://binance-docs.github.io/apidocs/futures/en/#change-margin-type-trade

# print('Changing your', symbol, 'position margin mode to CROSSED:')
# response = exchange.fapiPrivate_post_margintype({
#     'symbol': market['id'],
#     'marginType': 'CROSSED',
# })
# print(response)

# print('Changing your', symbol, 'position margin mode to ISOLATED:')
# response = exchange.fapiPrivate_post_margintype({
#     'symbol': market['id'],
#     'marginType': 'ISOLATED',
# })
# print(response)

# print('----------------------------------------------------------------------')

# # https://binance-docs.github.io/apidocs/spot/en/#new-future-account-transfer-futures

# code = 'USDT'
# amount = 123.45
# currency = exchange.currency(code)

# print('Moving', code, 'funds from your spot account to your futures account:')

# response = exchange.sapi_post_futures_transfer({
#     'asset': currency['id'],
#     'amount': exchange.currency_to_precision(code, amount),
#     # 1: transfer from spot account to USDT-Ⓜ futures account.
#     # 2: transfer from USDT-Ⓜ futures account to spot account.
#     # 3: transfer from spot account to COIN-Ⓜ futures account.
#     # 4: transfer from COIN-Ⓜ futures account to spot account.
#     'type': 1,
# })

# print('----------------------------------------------------------------------')

# # for ISOLATED positions only
# print('Modifying your ISOLATED', symbol, 'position margin:')
# response = exchange.fapiPrivate_post_positionmargin({
#     'symbol': market['id'],
#     'amount': 123.45,  # ←-------------- YOUR AMOUNT HERE
#     'positionSide': 'BOTH',  # use BOTH for One-way positions, LONG or SHORT for Hedge Mode
#     'type': 1,  # 1 = add position margin, 2 = reduce position margin
# })

# print('----------------------------------------------------------------------')
