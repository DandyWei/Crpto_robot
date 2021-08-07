from ccxtbt import CCXTStore
import backtrader as bt
from datetime import datetime, timedelta
import json
import ccxt
api_Key = 'nux5568AFIq0eL63qdQpsFHgG08nKGg3aO3FRDduzxhxOTx3l3FN1kpMTyXbE8it'
secret_Key ='kgj4GJz65eqaumiBH0Bgu4L7eaG4eVqJc9u6UZ12ykChYaMgbN6fZDzYr5EO0fyl'

#下單
'''
exchange.create_market_buy_order('BTC/USDT', 0.01)
'''
class TestStrategy(bt.Strategy):


	def __init__(self):

		self.sma = bt.indicators.SMA(self.data,period=21)
		self.isbuy = False

	def next(self):
		print(1)

        # Get cash and balance
        # New broker method that will let you get the cash and balance for
        # any wallet. It also means we can disable the getcash() and getvalue()
        # rest calls before and after next which slows things down.

        # NOTE: If you try to get the wallet balance from a wallet you have
        # never funded, a KeyError will be raised! Change LTC below as approriate
		print('condition: ',self.isbuy)
		if self.live_data:
			cash, value = self.broker.get_wallet_balance('BNB')
			if self.isbuy:

				self.order = self.close(size=0.02,exectype=bt.Order.Limit, price=300)
				self.isbuy = False
			elif not self.isbuy:
				self.order = self.buy(size=0.02,exectype=bt.Order.Limit, price=300)
				self.isbuy = True

			# self.order_target_percent( target = 0.9, exectype=bt.Order.Limit, price=300)
			# cash1, value1 = self.broker.get_wallet_balance('USDT')
		else:
            # Avoid checking the balance during a backfill. Otherwise, it will
            # Slow things down.
			cash = 'NA'
			return # 仍然处于历史数据回填阶段，不执行逻辑，返回

		for data in self.datas:
			print('{} - {} | Value {} | Cash {} | O: {} H: {} L: {} C: {} V:{} SMA:{}'.format(data.datetime.datetime(),
                                                                                   data._name,value, cash, data.open[0], data.high[0], data.low[0], data.close[0], data.volume[0],
                                                                                   self.sma[0]))
	def notify_data(self, data, status, *args, **kwargs):
		dn = data._name
		dt = datetime.now()
		msg= 'Data Status: {}'.format(data._getstatusname(status))
		print(dt,dn,msg)
		if data._getstatusname(status) == 'LIVE':
			self.live_data = True
		else:
			self.live_data = False


def main():
	cerebro = bt.Cerebro(quicknotify=True)


	# Add the strategy
	cerebro.addstrategy(TestStrategy)

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
	exchange = ccxt.binance(
	            config
	          )


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
	        bt.Order.Stop: 'stop-loss', #stop-loss for kraken, stop for bitmex
	        bt.Order.StopLimit: 'stop limit'
	    },
	    'mappings':{
	        'closed_order':{
	            'key': 'status',
	            'value':'closed'
	        },
	        'canceled_order':{
	            'key': 'result',
	            'value':1}
	    }
	}

	broker = store.getbroker(broker_mapping=broker_mapping)
	cerebro.setbroker(broker)

	# Get our data
	# Drop newest will prevent us from loading partial data from incomplete candles
	hist_start_date = datetime.utcnow() - timedelta(minutes=50)
	data = store.getdata(dataname='BNB/USDT', name="BNBUSDT",
	                     timeframe=bt.TimeFrame.Minutes, fromdate=hist_start_date,
	                     compression=1, ohlcv_limit=50, drop_newest=True) #, historical=True)

	# Add the feed
	cerebro.adddata(data)

	# Run the strategy
	cerebro.run()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('手動關閉，時間為 : ',dt.datetime.now().strftime("%d-%m-%y %H:%M"))
