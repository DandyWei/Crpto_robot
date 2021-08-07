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
		'''ATR'''
		self.ATR = bt.ind.AverageTrueRange(period = 100)
		self.nLoss = self.ATR * 0.5
		self.ATRtracking = 0
		self.lastATRtracking = 0
		'''DMA'''
		self.HA_30min = bt.ind.HeikinAshi(self.data)
		self.sma_8 = bt.ind.SMA(self.HA_30min.ha_close(), period = 21)
		self.ema_8 = bt.ind.EMA(self.sma_8,period = 21)
		self.crossdown = bt.ind.CrossDown(self.sma_8, self.ema_8)
		self.crossup = bt.ind.CrossUp(self.sma_8, self.ema_8)
		# self.isbuying = False
		# self.isselling = False
		self.golong = False
		self.goshort = False
		self.trendup = False
		self.trenddown = False
		self.takeprofit = None
        # 基本參數資料
		self.symbol = 'LINK/USDT'
		self.symbols = 'LINKUSDT'
		self.price = 100
		self.leverage = 2
		self.amount = 0.005
		self.type = 'market'  # or market or limit
		self.longside = 'buy'
		self.shortside = 'sell'
		self.exchange = ccxt.binance({
		     'apiKey': api_Key,
		     'secret': secret_Key,
		     'enableRateLimit': True,
		     'options': {'defaultType': 'future'}
		})
		self.mks = self.exchange.load_markets()
		self.market = self.exchange.market(self.symbol)
		self.exchange.fapiPrivate_post_leverage({
		    'symbol': self.market['id'],
		    'leverage': self.leverage,
		})

	def closecurrent(self):
		balance = self.exchange.fetch_balance()
		positions = balance['info']['positions']
		for position in positions:

			if position['symbol'] == self.symbols:
				return float(position['positionAmt'])
			    # print(position)
	# symbol = 'BNB/USDT'
	# market = exchange.market(symbol)
	# balance = exchange.fetch_balance()
	# positions = balance['info']['positions']
	# usdt = balance['free']['USDT']
	def next(self):
		'''拿到台灣的時間'''
		twt = datetime.utcnow() - timedelta(hours=4)
		'''下面是在改ATRTracking方向 +-'''

		if self.data.close[0] > self.ATRtracking: #and self.data.close.get(ago=-1)[0] > self.lastATRtracking

			if self.data.close.get(ago=-1)[0] < self.lastATRtracking:
				'''剛好換邊'''
				self.ATRtracking = self.data.close[0] - self.nLoss
			else :
				'''正常'''
				self.ATRtracking = max(self.data.close[0] - self.nLoss, self.lastATRtracking)
		if self.data.close[0] < self.ATRtracking : #and self.data.close.get(ago=-1)[0] < self.lastATRtracking
			if self.data.close.get(ago=-1)[0] > self.lastATRtracking:
				'''剛好換邊'''
				self.ATRtracking = self.data.close[0] + self.nLoss
			else:
				'''正常'''
				self.ATRtracking = min(self.data.close[0] + self.nLoss, self.lastATRtracking)
		print('time : ',self.data.datetime.datetime(),'close : ',self.data.close[0])

		# print(cash, value)
		price = self.data.close[0]
		# cash, value = self.broker.get_wallet_balance('BNB')
		if self.crossup and not self.crossdown :# and not self.isbuying
			'''計算偷跑值'''
			self.takeprofit = self.data.close[0] + abs(self.data.close[0] - self.sma_8[0])
			print('開買!!,now time : ',self.data.datetime.datetime(),'close : ', self.data.close[0],'sma : ',self.sma_8[0],'ema : ',self.ema_8[0])

			# self.isbuying = True
			# self.isselling = False
			'''是否發出買賣信號'''
			self.golong = True
			self.goshort = False

		elif self.crossdown and not self.crossup :# and not self.isselling
			'''計算偷跑值'''
			self.takeprofit = self.data.close[0] - abs(self.data.close[0] - self.sma_8[0])
			print('開賣!!,now time : ',self.data.datetime.datetime(),'close : ', self.data.close[0],'sma : ',self.sma_8[0],'ema : ',self.ema_8[0])

			# self.isbuying = False
			# self.isselling = True
			'''是否發出買賣信號'''
			self.goshort = True
			self.golong = False

		'''--------------------------------------------------------------------------'''
		if self.live_data:
			''' 拿到餘額  帳戶總額 計算下單數量 '''
			position_size = self.closecurrent()
			cash, value = self.broker.get_wallet_balance('USDT')
			if cash > value/3:
				self.amount = float('{:.3f}'.format(value / 3 / self.data.close[0] * self.leverage)) #取道第三位
			else:
				self.amount = 0

			'''下面為偷跑系統'''
			if position_size != 0:
				if position_size > 0 and self.data.close[0] > self.takeprofit and self.trendup:
					print('賣出數量 : ',abs(position_size) / 4 )
					print('獲利賣出，台灣時間 : ',twt,'close : ', self.data.close[0],'sma : ',self.sma_8[0],'ema : ',self.ema_8[0])
					order = self.exchange.create_order(self.symbol, self.type, self.shortside, position_size / 4 )
					self.trendup = False
				if position_size < 0 and self.data.close[0] < self.takeprofit and self.trenddown:
					print('購買數量 : ',abs(position_size) / 4 )
					print('獲利買入，台灣時間 : ',twt,'close : ', self.data.close[0],'sma : ',self.sma_8[0],'ema : ',self.ema_8[0])
					order = self.exchange.create_order(self.symbol, self.type, self.longside, position_size / 4 )# limit + price
					self.trenddown = False
			'''下面為正常買賣'''
			if self.golong:
				print('購買數量 : ',self.amount + abs(position_size))
				print('執行買入，台灣時間 : ',twt,'close : ', self.data.close[0],'sma : ',self.sma_8[0],'ema : ',self.ema_8[0])
				order = self.exchange.create_order(self.symbol, self.type, self.longside,self.amount + position_size )# limit + price  #self.amount + position_size
				self.golong = False
			if self.goshort:
				print('販賣數量 : ',self.amount + abs(position_size))
				print('執行賣出，台灣時間 : ',twt,'close : ', self.data.close[0],'sma : ',self.sma_8[0],'ema : ',self.ema_8[0])
				order = self.exchange.create_order(self.symbol, self.type, self.shortside, self.amount + position_size)
				self.goshort = False


			# self.order_target_percent( target = 0.9, exectype=bt.Order.Limit, price=300)
			# cash1, value1 = self.broker.get_wallet_balance('USDT')
		else:
            # Avoid checking the balance during a backfill. Otherwise, it will
            # Slow things down.
			cash = 'NA'
			return # 仍然处于历史数据回填阶段，不执行逻辑，返回
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
	'''檢查點'''
	hist_start_date = datetime.utcnow() - timedelta(days=2,hours=23)# days=999999999, hours=23, minutes=59, seconds=59 days=2,hours=23
	data = store.getdata(dataname='LINK/USDT', name="LINK/USDT",
	                     timeframe=bt.TimeFrame.Minutes, fromdate=hist_start_date,
	                     compression=30, ohlcv_limit=9999, drop_newest=True) #, historical=True)

	# Add the feed
	cerebro.adddata(data)
	# Run the strategy
	cerebro.run()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('手動關閉，時間為 : ',dt.datetime.now().strftime("%d-%m-%y %H:%M"))
