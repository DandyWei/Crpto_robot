import backtrader as bt
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
import datetime as dt
from ccxtbt import CCXTStore
import ccxt
import math
import time
from backtrader.indicators import Indicator, MovAv, RelativeStrengthIndex, Highest, Lowest

api_Key = 'nux5568AFIq0eL63qdQpsFHgG08nKGg3aO3FRDduzxhxOTx3l3FN1kpMTyXbE8it'
secret_Key = 'kgj4GJz65eqaumiBH0Bgu4L7eaG4eVqJc9u6UZ12ykChYaMgbN6fZDzYr5EO0fyl'


class Bianance_Strategy(bt.Strategy):
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('%.2f 趴, %.2f 趴' % (trade.pnl/self.broker.getvalue()
                 * 100, self.broker.getvalue()/10000.0))

    def __init__(self):
        '''ATR!!!!!!!!!!!!!!!'''
        self.ATR_eth = bt.ind.AverageTrueRange(self.data, period=100)
        self.nLoss_eth = self.ATR_eth * 0.5
        self.ATRtracking_eth = 0
        self.lastATRtracking_eth = 0

        self.ATR_bnb = bt.ind.AverageTrueRange(self.data1, period=100)
        self.nLoss_bnb = self.ATR_bnb * 0.5
        self.ATRtracking_bnb = 0
        self.lastATRtracking_bnb = 0

        self.ATR_link = bt.ind.AverageTrueRange(self.data2, period=100)
        self.nLoss_link = self.ATR_link * 0.5
        self.ATRtracking_link = 0
        self.lastATRtracking_link = 0
        '''每組data的數據'''
        self.HA_eth = bt.ind.HeikinAshi(self.data)
        self.sma_eth = bt.ind.SMA(self.HA_eth.ha_close(), period=21)
        self.ema_eth = bt.ind.EMA(self.sma_eth, period=21)
        self.crossdowneth = bt.ind.CrossDown(self.sma_eth, self.ema_eth)
        self.crossupeth = bt.ind.CrossUp(self.sma_eth, self.ema_eth)

        self.HA_bnb = bt.ind.HeikinAshi(self.data1)
        self.sma_bnb = bt.ind.SMA(self.HA_bnb.ha_close(), period=21)
        self.ema_bnb = bt.ind.EMA(self.sma_bnb, period=21)
        self.crossdownbnb = bt.ind.CrossDown(self.sma_bnb, self.ema_bnb)
        self.crossupbnb = bt.ind.CrossUp(self.sma_bnb, self.ema_bnb)

        self.HA_link = bt.ind.HeikinAshi(self.data2)
        self.sma_link = bt.ind.SMA(self.HA_link.ha_close(), period=21)
        self.ema_link = bt.ind.EMA(self.sma_link, period=21)
        self.crossdownlink = bt.ind.CrossDown(self.sma_link, self.ema_link)
        self.crossuplink = bt.ind.CrossUp(self.sma_link, self.ema_link)

        self.isbuying = []
        self.isselling = []
        self.golong = []
        self.goshort = []
        self.trendup = []
        self.trenddown = []
        self.takeprofit_eth = 9999999
        self.takeprofit_bnb = 9999999
        self.takeprofit_link = 9999999
        self.emaeth = 999999
        self.emabnb = 999999
        self.emalink = 999999
    # 基本參數資料
        self.symbol = ['ETH/USDT', 'BNB/USDT', 'LINK/USDT']
        self.symbols = ['ETHUSDT', 'BNBUSDT', 'LINKUSDT']

        self.leverage = 3
        self.amount = 0.005
        self.longside = 'buy'
        self.shortside = 'sell'
        self.exchange = ccxt.binance({
            'apiKey': api_Key,
            'secret': secret_Key,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
        '''下面這行導致訪問出錯的'''
        self.mks = self.exchange.load_markets()
        '''設定各種槓桿倍數'''
        self.market = self.exchange.market(self.symbol[0])
        self.exchange.fapiPrivate_post_leverage({
            'symbol': self.market['id'],
            'leverage': self.leverage,
        })
        self.market = self.exchange.market(self.symbol[1])
        self.exchange.fapiPrivate_post_leverage({
            'symbol': self.market['id'],
            'leverage': self.leverage,
        })
        self.market = self.exchange.market(self.symbol[2])
        self.exchange.fapiPrivate_post_leverage({
            'symbol': self.market['id'],
            'leverage': self.leverage,
        })
        '''
		self.exchange.fapiPrivate_post_margintype({
		    'symbol': self.market['id'],
		    'marginType': 'ISOLATED',
		})
		'''

    def next(self):

        response = self.exchange.fapiPrivateV2_get_positionrisk()
        allcrypto = [x for x in response if x['symbol'] in self.symbols]
        position_size_eth = float([x['positionAmt']
                                  for x in allcrypto if self.symbols[0] == x['symbol']][0])
        entryP_eth = float([x['entryPrice']
                           for x in allcrypto if self.symbols[0] == x['symbol']][0])
        position_size_bnb = float([x['positionAmt']
                                  for x in allcrypto if self.symbols[1] == x['symbol']][0])
        entryP_bnb = float([x['entryPrice']
                           for x in allcrypto if self.symbols[1] == x['symbol']][0])
        position_size_link = float([x['positionAmt']
                                   for x in allcrypto if self.symbols[2] == x['symbol']][0])
        entryP_link = float([x['entryPrice']
                            for x in allcrypto if self.symbols[2] == x['symbol']][0])
        '''拿到台灣的時間'''
        twt = datetime.utcnow() - timedelta(hours=4+12)
        '''統一每種幣種的開高低 +-'''
        close_eth = self.data.close[0]
        high_eth = self.data.high[0]
        low_eth = self.data.low[0]

        close_bnb = self.data1.close[0]
        high_bnb = self.data1.high[0]
        low_bnb = self.data1.low[0]

        close_link = self.data2.close[0]
        high_link = self.data2.high[0]
        low_link = self.data2.low[0]
        '''計算每種幣種的ATRz方向'''
        if close_eth > self.ATRtracking_eth:  # and self.data.close.get(ago=-1)[0] > self.lastATRtracking

            if self.data.close.get(ago=-1)[0] < self.lastATRtracking_eth:
                '''剛好換邊'''
                self.ATRtracking_eth = close_eth - self.nLoss_eth
                while 'eth' in self.isselling:
                    self.isselling.remove('eth')
            else:
                '''正常'''
                self.ATRtracking_eth = max(close_eth - self.nLoss_eth, self.lastATRtracking_eth)
        # and self.data.close.get(ago=-1)[0] < self.lastATRtracking
        if close_eth < self.ATRtracking_eth:
            if self.data.close.get(ago=-1)[0] > self.lastATRtracking_eth:
                self.ATRtracking_eth = close_eth + self.nLoss_eth
                while 'eth' in self.isbuying:
                    self.isbuying.remove('eth')
            else:
                self.ATRtracking_eth = min(close_eth + self.nLoss_eth, self.lastATRtracking_eth)
        '''BNB'''
        if close_bnb > self.ATRtracking_bnb:  # and self.data.close.get(ago=-1)[0] > self.lastATRtracking

            if self.data1.close.get(ago=-1)[0] < self.lastATRtracking_bnb:
                '''剛好換邊'''
                self.ATRtracking_bnb = close_bnb - self.nLoss_bnb
                while 'bnb' in self.isselling:
                    self.isselling.remove('bnb')
            else:
                '''正常'''
                self.ATRtracking_bnb = max(close_bnb - self.nLoss_bnb, self.lastATRtracking_bnb)
        # and self.data.close.get(ago=-1)[0] < self.lastATRtracking
        if close_bnb < self.ATRtracking_bnb:
            if self.data1.close.get(ago=-1)[0] > self.lastATRtracking_bnb:
                self.ATRtracking_bnb = close_bnb + self.nLoss_bnb
                while 'bnb' in self.isbuying:
                    self.isbuying.remove('bnb')
            else:
                self.ATRtracking_bnb = min(close_bnb + self.nLoss_bnb, self.lastATRtracking_bnb)
        '''LINK'''
        if close_link > self.ATRtracking_link:  # and self.data.close.get(ago=-1)[0] > self.lastATRtracking

            if self.data2.close.get(ago=-1)[0] < self.lastATRtracking_link:
                '''剛好換邊'''
                self.ATRtracking_link = close_link - self.nLoss_link
                while 'link' in self.isselling:
                    self.isselling.remove('link')
            else:
                '''正常'''
                self.ATRtracking_link = max(close_link - self.nLoss_link, self.lastATRtracking_link)
        # and self.data.close.get(ago=-1)[0] < self.lastATRtracking
        if close_link < self.ATRtracking_link:
            if self.data2.close.get(ago=-1)[0] > self.lastATRtracking_link:
                self.ATRtracking_link = close_link + self.nLoss_link
                while 'link' in self.isbuying:
                    self.isbuying.remove('link')
            else:
                self.ATRtracking_link = min(close_link + self.nLoss_link, self.lastATRtracking_link)

        self.lastATRtracking_eth = self.ATRtracking_eth
        self.lastATRtracking_bnb = self.ATRtracking_bnb
        self.lastATRtracking_link = self.ATRtracking_link
        '''分isbuyibg上升趨勢向下實力起來，會在趨勢翻轉時被按下去，trendup會在賭錢獲利後被翻轉下去'''
        if close_eth < self.ATRtracking_eth and position_size_eth > 0 and 'eth' not in self.isbuying:
            self.trendup.append('eth')
            self.isbuying.append('eth')
            while 'eth' in self.trenddown:
                self.trenddown.remove('eth')
            while 'eth' in self.isselling:
                self.isselling.remove('eth')
        if close_eth > self.ATRtracking_eth and position_size_eth < 0 and 'eth' not in self.isselling:
            self.trenddown.append('eth')
            self.isselling.append('eth')
            while 'eth' in self.trendup:
                self.trendup.remove('eth')
            while 'eth' in self.isbuying:
                self.isbuying.remove('eth')
        '''bnb'''
        if close_bnb < self.ATRtracking_bnb and position_size_bnb > 0 and 'bnb' not in self.isbuying:
            self.trendup.append('bnb')
            self.isbuying.append('bnb')
            while 'bnb' in self.trenddown:
                self.trenddown.remove('bnb')
            while 'bnb' in self.isselling:
                self.isselling.remove('bnb')
        if close_bnb > self.ATRtracking_bnb and position_size_bnb < 0 and 'bnb' not in self.isselling:
            self.trenddown.append('bnb')
            self.isselling.append('bnb')
            while 'bnb' in self.trendup:
                self.trendup.remove('bnb')
            while 'bnb' in self.isbuying:
                self.isbuying.remove('bnb')
        '''link'''
        if close_link < self.ATRtracking_link and position_size_link > 0 and 'link' not in self.isbuying:
            self.trendup.append('link')
            self.isbuying.append('link')
            while 'link' in self.trenddown:
                self.trenddown.remove('link')
            while 'link' in self.isselling:
                self.isselling.remove('link')
        if close_link > self.ATRtracking_link and position_size_link < 0 and 'link' not in self.isselling:
            self.trenddown.append('link')
            self.isselling.append('link')
            while 'link' in self.trendup:
                self.trendup.remove('link')
            while 'link' in self.isbuying:
                self.isbuying.remove('link')

        '''下面記錄各種幣種的買入賣出'''
        if self.crossupeth and not self.crossdowneth:  # and not self.isbuying
            '''紀錄此時的EMA值做後續短期獲利的計算值，此外發出買入賣出訊號， 如果方向轉換要先清除前面沒有獲利的限價單'''
            gap = abs(self.data.close[0] - self.sma_eth[0])
            self.takeprofit_eth = self.data.close[0] + gap
            self.exchange.cancel_all_orders(self.symbol[0])
            self.emaeth = self.sma_eth[0]
            self.golong.append('eth')
            while 'eth' in self.goshort:
                self.goshort.remove('eth')
            print('開買eth!!,now time : ', self.data.datetime.datetime(), 'close : ', close_eth)

        elif self.crossdowneth and not self.crossupeth:  # and not self.isselling
            gap = abs(self.data.close[0] - self.sma_eth[0])
            self.takeprofit_eth = self.data.close[0] - gap
            self.exchange.cancel_all_orders(self.symbol[0])
            self.emaeth = self.sma_eth[0]
            self.goshort.append('eth')
            while 'eth' in self.golong:
                self.golong.remove('eth')
            print('開賣eth!!,now time : ', self.data.datetime.datetime(), 'close : ', close_eth)
        '''BNB'''
        if self.crossupbnb and not self.crossdownbnb:  # and not self.isbuying
            '''紀錄此時的EMA值做後續短期獲利的計算值，此外發出買入賣出訊號， 如果方向轉換要先清除前面沒有獲利的限價單'''
            gap = abs(self.data1.close[0] - self.sma_bnb[0])
            self.takeprofit_bnb = self.data1.close[0] + gap
            self.exchange.cancel_all_orders(self.symbol[1])
            self.emabnb = self.sma_bnb[0]
            self.golong.append('bnb')
            while 'bnb' in self.goshort:
                self.goshort.remove('bnb')
            print('開買bnb!!,now time : ', self.data.datetime.datetime(), 'close : ', close_bnb)

        elif self.crossdownbnb and not self.crossupbnb:  # and not self.isselling
            gap = abs(self.data1.close[0] - self.sma_bnb[0])
            self.takeprofit_bnb = self.data1.close[0] - gap
            self.exchange.cancel_all_orders(self.symbol[1])
            self.emabnb = self.sma_bnb[0]
            self.goshort.append('bnb')
            while 'bnb' in self.golong:
                self.golong.remove('bnb')
            print('開賣bnb!!,now time : ', self.data.datetime.datetime(), 'close : ', close_bnb)
        '''link'''
        if self.crossuplink and not self.crossdownlink:  # and not self.isbuying
            '''紀錄此時的EMA值做後續短期獲利的計算值，此外發出買入賣出訊號， 如果方向轉換要先清除前面沒有獲利的限價單'''
            gap = abs(self.data2.close[0] - self.sma_link[0])
            self.takeprofit_link = self.data2.close[0] + gap
            self.exchange.cancel_all_orders(self.symbol[2])
            self.emalink = self.sma_link[0]
            self.golong.append('link')
            while 'link' in self.goshort:
                self.goshort.remove('link')
            print('開買link!!,now time : ', self.data.datetime.datetime(), 'close : ', close_link)

        elif self.crossdownlink and not self.crossuplink:  # and not self.isselling
            gap = abs(self.data2.close[0] - self.sma_link[0])
            self.takeprofit_link = self.data2.close[0] - gap
            self.exchange.cancel_all_orders(self.symbol[2])
            self.emalink = self.sma_link[0]
            self.goshort.append('link')
            while 'link' in self.golong:
                self.golong.remove('link')
            print('開賣link!!,now time : ', self.data.datetime.datetime(), 'close : ', close_link)

        print('台灣時間 : ', twt, 'close_eth : ', close_eth, 'position_eth : ', position_size_eth, 'close_bnb : ', close_bnb,
              'position_bnb : ', position_size_bnb, 'close_link : ', close_link, 'position_link : ', position_size_link)

        '''--------------------------------------------------------------------------'''
        if self.live_data:
            print('trendup list', self.trendup, 'trenddown list', self.trenddown,
                  'golong list', self.golong, 'goshort list', self.goshort)
            # balance = self.exchange.fetch_balance()
            div = float(len(self.symbol)) + 0.1

            ''' 拿到餘額  帳戶總額 計算下單數量 先算要買的'''
            cash, value = self.broker.get_wallet_balance('USDT')

            if position_size_eth > 0 and 'eth' in self.golong:
                self.golong.remove('eth')
                print('先不多eth 有了')
            if position_size_eth < 0 and 'eth' in self.goshort:
                self.goshort.remove('eth')
                print('先不空eth 有了')
            '''bnb'''
            if position_size_bnb > 0 and 'bnb' in self.golong:
                self.golong.remove('bnb')
                print('先不多bnb 有了')
            if position_size_bnb < 0 and 'bnb' in self.goshort:
                self.goshort.remove('bnb')
                print('先不空bnb 有了')
            '''link'''
            if position_size_link > 0 and 'link' in self.golong:
                self.golong.remove('link')
                print('先不多link 有了')
            if position_size_link < 0 and 'link' in self.goshort:
                self.goshort.remove('link')
                print('先不空link 有了')
            '''下面為偷跑系統 這裡不用cancle order 因為換邊在cancleorder就好 沒賣到我就掛到爽'''
            if position_size_eth != 0:
                if position_size_eth > 0 and 'eth' in self.trendup:
                    if high_eth > self.takeprofit_eth:
                        try:
                            print('賣出數量 : ', abs(position_size_eth) / 4)
                            if abs(position_size_eth) / 4 * high_eth > 6:
                                print('獲利賣出，台灣時間 : ', twt, 'limit price : ', self.takeprofit)
                                order = self.exchange.create_order(
                                    self.symbol[0], 'limit', self.shortside, abs(position_size_eth) / 4, price=high_eth)
                                gap = abs(self.data.close[0] - self.sma_eth[0])
                                self.takeprofit_eth = self.data.close[0] + gap
                        except:
                            self.log('餘額不夠先不賣了')
                        while 'eth' in self.trendup:
                            self.trendup.remove('eth')
                if position_size_eth < 0 and 'eth' in self.trenddown:
                    if low_eth < self.takeprofit_eth:
                        try:
                            print('購買數量 : ', abs(position_size_eth) / 4)
                            if abs(position_size_eth) / 4 * low_eth > 6:
                                print('獲利買入，台灣時間 : ', twt, 'limit price : ', self.takeprofit)
                                order = self.exchange.create_order(self.symbol[0], 'limit', self.longside, abs(
                                    position_size_eth) / 4, price=low_eth)  # limit + price
                                gap = abs(self.data.close[0] - self.sma_eth[0])
                                self.takeprofit_eth = self.data.close[0] - gap
                        except:
                            self.log('餘額不夠先不賣了')
                        while 'eth' in self.trenddown:
                            self.trenddown.remove('eth')
            '''bnb'''
            if position_size_bnb != 0:
                if position_size_bnb > 0 and 'bnb' in self.trendup:
                    self.takeprofit = entryP_bnb + abs(entryP_bnb - self.ema_bnb)
                    if high_bnb > self.takeprofit_bnb:
                        try:
                            print('賣出數量 : ', abs(position_size_bnb) / 4)
                            if abs(position_size_bnb) / 4 * high_bnb > 6:
                                print('獲利賣出，台灣時間 : ', twt, 'limit price : ', self.takeprofit)
                                order = self.exchange.create_order(
                                    self.symbol[1], 'limit', self.shortside, abs(position_size_bnb) / 4, price=high_bnb)
                                gap = abs(self.data1.close[0] - self.sma_bnb[0])
                                self.takeprofit_bnb = self.data1.close[0] + gap
                        except:
                            self.log('餘額不夠先不賣了')
                        while 'bnb' in self.trendup:
                            self.trendup.remove('bnb')
                if position_size_bnb < 0 and 'bnb' in self.trenddown:
                    self.takeprofit = entryP_bnb - abs(entryP_bnb - self.ema_bnb)
                    if low_bnb < self.takeprofit_bnb:
                        try:
                            print('購買數量 : ', abs(position_size_bnb) / 4)
                            if abs(position_size_bnb) / 4 * low_bnb > 6:
                                print('獲利買入，台灣時間 : ', twt, 'limit price : ', self.takeprofit)
                                order = self.exchange.create_order(self.symbol[1], 'limit', self.longside, abs(
                                    position_size_bnb) / 4, price=low_bnb)  # limit + price
                                gap = abs(self.data1.close[0] - self.sma_bnb[0])
                                self.takeprofit_bnb = self.data1.close[0] - gap
                        except:
                            self.log('餘額不夠先不賣了')
                        while 'bnb' in self.trenddown:
                            self.trenddown.remove('bnb')
            '''link'''
            if position_size_link != 0:
                if position_size_link > 0 and 'link' in self.trendup:
                    if high_link > self.takeprofit_link:
                        print('賣出數量 : ', abs(position_size_link) / 4)
                        if abs(position_size_link) / 4 * high_link > 6:
                            print('獲利賣出，台灣時間 : ', twt, 'limit price : ', self.takeprofit)
                            order = self.exchange.create_order(
                                self.symbol[2], 'limit', self.shortside, abs(position_size_link) / 4, price=high_link)
                            gap = abs(self.data2.close[0] - self.sma_link[0])
                            self.takeprofit_link = self.data2.close[0] + gap
                        while 'link' in self.trendup:
                            self.trendup.remove('link')
                if position_size_link < 0 and 'link' in self.trenddown:
                    if low_link < self.takeprofit_link:
                        print('購買數量 : ', abs(position_size_link) / 4)
                        if abs(position_size_link) / 4 * low_link > 6:
                            print('獲利買入，台灣時間 : ', twt, 'limit price : ', self.takeprofit)
                            order = self.exchange.create_order(self.symbol[2], 'limit', self.longside, abs(
                                position_size_link) / 4, price=low_link)  # limit + price
                            gap = abs(self.data2.close[0] - self.sma_link[0])
                            self.takeprofit_link = self.data2.close[0] - gap
                        while 'link' in self.trenddown:
                            self.trenddown.remove('link')

            '''下面為正常買賣 已存在的部分用市價出掉以免報幹虧錢 一半用market買一半打貪一點'''
            self.amount = float('{:.5f}'.format(math.floor(
                value / div / close_eth * self.leverage * 10000.0) / 10000.0))  # 取道第4位
            if 'eth' in self.golong:
                self.exchange.cancel_all_orders(self.symbol[0])
                try:
                    print('購買eth數量 : ', self.amount + abs(position_size_eth))
                    print('執行買入eth，台灣時間 : ', twt, 'close : ', close_eth)
                    self.exchange.create_order(
                        self.symbol[0], 'Market', self.longside, self.amount / 2 + abs(position_size_eth))
                    # limit + price  #self.amount + position_size
                    order = self.exchange.create_order(
                        self.symbol[0], 'limit', self.longside, self.amount / 2, price=low_eth)
                except:
                    print('錢不夠')
                self.golong.remove('eth')

            if 'eth' in self.goshort:
                self.exchange.cancel_all_orders(self.symbol[0])
                try:
                    print('販賣eth數量 : ', self.amount + abs(position_size_eth))
                    print('執行賣出eth，台灣時間 : ', twt, 'close : ', close_eth)
                    self.exchange.create_order(
                        self.symbol[0], 'Market', self.shortside, self.amount / 2 + abs(position_size_eth))
                    order = self.exchange.create_order(
                        self.symbol[0], 'limit', self.shortside, self.amount / 2, price=high_eth)
                except:
                    print('錢不夠')
                self.goshort.remove('eth')

            '''bnb'''
            self.amount = float('{:.5f}'.format(math.floor(
                value / div / close_bnb * self.leverage * 10000.0) / 10000.0))  # 取道第4位
            if 'bnb' in self.golong:
                self.exchange.cancel_all_orders(self.symbol[1])
                try:
                    print('購買bnb數量 : ', self.amount + abs(position_size_bnb))
                    print('執行買入bnb，台灣時間 : ', twt, 'close : ', close_bnb)
                    self.exchange.create_order(
                        self.symbol[1], 'Market', self.longside, self.amount / 2 + abs(position_size_bnb))
                    # limit + price  #self.amount + position_size
                    order = self.exchange.create_order(
                        self.symbol[1], 'limit', self.longside, self.amount / 2, price=low_bnb)
                except:
                    print('錢不夠')
                self.golong.remove('bnb')

            if 'bnb' in self.goshort:
                self.exchange.cancel_all_orders(self.symbol[1])
                try:
                    print('販賣bnb數量 : ', self.amount + abs(position_size_bnb))
                    print('執行賣出bnb，台灣時間 : ', twt, 'close : ', close_bnb)
                    self.exchange.create_order(
                        self.symbol[1], 'Market', self.shortside, self.amount / 2 + abs(position_size_bnb))
                    order = self.exchange.create_order(
                        self.symbol[1], 'limit', self.shortside, self.amount / 2, price=high_bnb)
                except:
                    print('錢不夠')
                self.goshort.remove('bnb')

            '''link'''
            self.amount = float('{:.5f}'.format(math.floor(
                value / div / close_link * self.leverage * 10000.0) / 10000.0))  # 取道第4位
            if 'link' in self.golong:
                self.exchange.cancel_all_orders(self.symbol[2])
                try:
                    print('購買link數量 : ', self.amount + abs(position_size_link))
                    print('執行買入link，台灣時間 : ', twt, 'close : ', close_link)
                    self.exchange.create_order(
                        self.symbol[2], 'Market', self.longside, self.amount / 2 + abs(position_size_link))
                    # limit + price  #self.amount + position_size
                    order = self.exchange.create_order(
                        self.symbol[2], 'limit', self.longside, self.amount / 2, price=low_link)
                except:
                    print('錢不夠')
                self.golong.remove('link')

            if 'link' in self.goshort:
                self.exchange.cancel_all_orders(self.symbol[2])
                try:
                    print('販賣link數量 : ', self.amount + abs(position_size_link))
                    print('執行賣出link，台灣時間 : ', twt, 'close : ', close_link)
                    self.exchange.create_order(
                        self.symbol[2], 'Market', self.shortside, self.amount / 2 + abs(position_size_link))
                    order = self.exchange.create_order(
                        self.symbol[2], 'limit', self.shortside, self.amount / 2, price=high_link)
                except:
                    print('錢不夠')
                self.goshort.remove('link')
        else:
            # Avoid checking the balance during a backfill. Otherwise, it will
            # Slow things down.
            cash = 'NA'
            return

    def notify_data(self, data, status, *args, **kwargs):
        dn = data._name
        dt = datetime.now()
        msg = 'Data Status: {}'.format(data._getstatusname(status))
        print(dt, dn, msg)
        if data._getstatusname(status) == 'LIVE':
            self.live_data = True
        else:
            self.live_data = False


class Bianance_Strategy_07_26(bt.Strategy):
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('%.2f 趴, %.2f 趴' % (trade.pnl/self.broker.getvalue()
                 * 100, self.broker.getvalue()/10000.0))

    def __init__(self):
        '''WT!!!!!!!!!!!!!!!'''
        self.n1 = 10
        self.n2 = 21
        '''eth'''
        self.hlc3_eth = (self.data.close + self.data.high + self.data.low) / 3
        self.esa_eth = bt.ind.EMA(self.hlc3_eth, period=self.n1, plot=False)
        self.d_eth = bt.ind.EMA(abs(self.hlc3_eth - self.esa_eth), period=self.n1, plot=False)
        self.ci_eth = (self.hlc3_eth - self.esa_eth) / (0.015 * self.d_eth)
        self.WT1_eth = bt.ind.EMA(self.ci_eth, period=self.n2, plot=False)
        self.WT2_eth = bt.ind.SMA(self.WT1_eth, period=4, plot=False)
        self.WTMTM_eth = self.WT1_eth - self.WT2_eth
        '''bnb'''
        self.hlc3_bnb = (self.data1.close + self.data1.high + self.data1.low) / 3
        self.esa_bnb = bt.ind.EMA(self.hlc3_bnb, period=self.n1, plot=False)
        self.d_bnb = bt.ind.EMA(abs(self.hlc3_bnb - self.esa_bnb), period=self.n1, plot=False)
        self.ci_bnb = (self.hlc3_bnb - self.esa_bnb) / (0.015 * self.d_bnb)
        self.WT1_bnb = bt.ind.EMA(self.ci_bnb, period=self.n2, plot=False)
        self.WT2_bnb = bt.ind.SMA(self.WT1_bnb, period=4, plot=False)
        self.WTMTM_bnb = self.WT1_bnb - self.WT2_bnb
        '''link'''
        self.hlc3_link = (self.data2.close + self.data2.high + self.data2.low) / 3
        self.esa_link = bt.ind.EMA(self.hlc3_link, period=self.n1, plot=False)
        self.d_link = bt.ind.EMA(abs(self.hlc3_link - self.esa_link), period=self.n1, plot=False)
        self.ci_link = (self.hlc3_link - self.esa_link) / (0.015 * self.d_link)
        self.WT1_link = bt.ind.EMA(self.ci_link, period=self.n2, plot=False)
        self.WT2_link = bt.ind.SMA(self.WT1_link, period=4, plot=False)
        self.WTMTM_link = self.WT1_link - self.WT2_link

        '''每組data的數據'''
        self.HA_eth = bt.ind.HeikinAshi(self.data)
        self.sma_eth = bt.ind.SMA(self.HA_eth.ha_close(), period=21)
        self.ema_eth = bt.ind.EMA(self.sma_eth, period=21)
        self.crossdowneth = bt.ind.CrossDown(self.sma_eth, self.ema_eth)
        self.crossupeth = bt.ind.CrossUp(self.sma_eth, self.ema_eth)

        self.HA_bnb = bt.ind.HeikinAshi(self.data1)
        self.sma_bnb = bt.ind.SMA(self.HA_bnb.ha_close(), period=21)
        self.ema_bnb = bt.ind.EMA(self.sma_bnb, period=21)
        self.crossdownbnb = bt.ind.CrossDown(self.sma_bnb, self.ema_bnb)
        self.crossupbnb = bt.ind.CrossUp(self.sma_bnb, self.ema_bnb)

        self.HA_link = bt.ind.HeikinAshi(self.data2)
        self.sma_link = bt.ind.SMA(self.HA_link.ha_close(), period=21)
        self.ema_link = bt.ind.EMA(self.sma_link, period=21)
        self.crossdownlink = bt.ind.CrossDown(self.sma_link, self.ema_link)
        self.crossuplink = bt.ind.CrossUp(self.sma_link, self.ema_link)

        self.isbuying = []
        self.isselling = []
        self.golong = []
        self.goshort = []
        self.trendup = []
        self.trenddown = []
        self.takeprofit = 9999999
        self.emaeth = 999999
        self.emabnb = 999999
        self.emalink = 999999
    # 基本參數資料
        self.symbol = ['ETH/USDT', 'BNB/USDT', 'LINK/USDT']
        self.symbols = ['ETHUSDT', 'BNBUSDT', 'LINKUSDT']

        self.leverage = 10
        self.amount = 0.005
        self.longside = 'buy'
        self.shortside = 'sell'
        self.exchange = ccxt.binance({
            'apiKey': api_Key,
            'secret': secret_Key,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
        '''下面這行導致訪問出錯的'''
        self.mks = self.exchange.load_markets()
        '''設定各種槓桿倍數'''
        self.market = self.exchange.market(self.symbol[0])
        self.exchange.fapiPrivate_post_leverage({
            'symbol': self.market['id'],
            'leverage': self.leverage,
        })
        self.market = self.exchange.market(self.symbol[1])
        self.exchange.fapiPrivate_post_leverage({
            'symbol': self.market['id'],
            'leverage': self.leverage,
        })
        self.market = self.exchange.market(self.symbol[2])
        self.exchange.fapiPrivate_post_leverage({
            'symbol': self.market['id'],
            'leverage': self.leverage,
        })
        '''
		self.exchange.fapiPrivate_post_margintype({
		    'symbol': self.market['id'],
		    'marginType': 'ISOLATED',
		})
		'''

    def vali(self, symbol=False):
        if symbol == 'ETH/USDT':
            temp_list = self.WTMTM_eth.get(size=40)
            if self.WTMTM_eth[0] < 0:
                temp_list.pop()
                while temp_list[-1] < 0:
                    if temp_list.pop() < -15:
                        return True
                        break
            elif self.WTMTM_eth[0] > 0:
                temp_list.pop()
                while temp_list[-1] > 0:
                    if temp_list.pop() > 15:
                        return True
                        break
            return False
        elif symbol == 'BNB/USDT':
            return False
            # temp_list = self.WTMTM_bnb.get(size=40)
            # if self.WTMTM_bnb[0] < 0:
            # 	temp_list.pop()
            # 	while temp_list[-1] < 0:
            # 		if temp_list.pop() < -15:
            # 			return True
            # 			break
            # elif self.WTMTM_bnb[0] > 0:
            # 	temp_list.pop()
            # 	while temp_list[-1] > 0:
            # 		if temp_list.pop() > 15:
            # 			return True
            # 			break
            # return False
        elif symbol == 'LINK/USDT':
            temp_list = self.WTMTM_link.get(size=40)
            if self.WTMTM_link[0] < 0:
                temp_list.pop()
                while temp_list[-1] < 0:
                    if temp_list.pop() < -15:
                        return True
                        break
            elif self.WTMTM_link[0] > 0:
                temp_list.pop()
                while temp_list[-1] > 0:
                    if temp_list.pop() > 15:
                        return True
                        break
            return False
        else:
            return False

    def next(self):

        response = self.exchange.fapiPrivateV2_get_positionrisk()
        allcrypto = [x for x in response if x['symbol'] in self.symbols]
        position_size_eth = float([x['positionAmt']
                                  for x in allcrypto if self.symbols[0] == x['symbol']][0])
        entryP_eth = float([x['entryPrice']
                           for x in allcrypto if self.symbols[0] == x['symbol']][0])
        position_size_bnb = float([x['positionAmt']
                                  for x in allcrypto if self.symbols[1] == x['symbol']][0])
        entryP_bnb = float([x['entryPrice']
                           for x in allcrypto if self.symbols[1] == x['symbol']][0])
        position_size_link = float([x['positionAmt']
                                   for x in allcrypto if self.symbols[2] == x['symbol']][0])
        entryP_link = float([x['entryPrice']
                            for x in allcrypto if self.symbols[2] == x['symbol']][0])
        '''拿到台灣的時間'''
        twt = datetime.utcnow() - timedelta(hours=4+12)
        '''統一每種幣種的開高低 +-'''
        close_eth = self.data.close[0]
        high_eth = self.data.high[0]
        low_eth = self.data.low[0]

        close_bnb = self.data1.close[0]
        high_bnb = self.data1.high[0]
        low_bnb = self.data1.low[0]

        close_link = self.data2.close[0]
        high_link = self.data2.high[0]
        low_link = self.data2.low[0]

        '''下面記錄各種幣種的買入賣出'''
        if self.crossupeth and not self.crossdowneth:  # and not self.isbuying
            '''紀錄此時的EMA值做後續短期獲利的計算值，此外發出買入賣出訊號， 如果方向轉換要先清除前面沒有獲利的限價單'''
            if self.vali(self.symbol[0]):
                self.exchange.cancel_all_orders(self.symbol[0])
                self.emaeth = self.sma_eth[0]
                self.golong.append('eth')
                while 'eth' in self.goshort:
                    self.goshort.remove('eth')
                print('開買eth!!,now time : ', self.data.datetime.datetime(), 'close : ', close_eth)

        elif self.crossdowneth and not self.crossupeth:  # and not self.isselling
            if self.vali(self.symbol[0]):
                self.exchange.cancel_all_orders(self.symbol[0])
                self.emaeth = self.sma_eth[0]
                self.goshort.append('eth')
                while 'eth' in self.golong:
                    self.golong.remove('eth')
                print('開賣eth!!,now time : ', self.data.datetime.datetime(), 'close : ', close_eth)
        '''BNB'''
        if self.crossupbnb and not self.crossdownbnb:  # and not self.isbuying
            if self.vali(self.symbol[1]):
                '''紀錄此時的EMA值做後續短期獲利的計算值，此外發出買入賣出訊號， 如果方向轉換要先清除前面沒有獲利的限價單'''
                self.exchange.cancel_all_orders(self.symbol[1])
                self.emabnb = self.sma_bnb[0]
                self.golong.append('bnb')
                while 'bnb' in self.goshort:
                    self.goshort.remove('bnb')
                print('開買bnb!!,now time : ', self.data.datetime.datetime(), 'close : ', close_bnb)

        elif self.crossdownbnb and not self.crossupbnb:  # and not self.isselling
            if self.vali(self.symbol[1]):
                self.exchange.cancel_all_orders(self.symbol[1])
                self.emabnb = self.sma_bnb[0]
                self.goshort.append('bnb')
                while 'bnb' in self.golong:
                    self.golong.remove('bnb')
                print('開賣bnb!!,now time : ', self.data.datetime.datetime(), 'close : ', close_bnb)
        '''link'''
        if self.crossuplink and not self.crossdownlink:  # and not self.isbuying
            if self.vali(self.symbol[2]):
                '''紀錄此時的EMA值做後續短期獲利的計算值，此外發出買入賣出訊號， 如果方向轉換要先清除前面沒有獲利的限價單'''
                self.exchange.cancel_all_orders(self.symbol[2])
                self.emalink = self.sma_link[0]
                self.golong.append('link')
                while 'link' in self.goshort:
                    self.goshort.remove('link')
                print('開買link!!,now time : ', self.data.datetime.datetime(), 'close : ', close_link)

        elif self.crossdownlink and not self.crossuplink:  # and not self.isselling
            if self.vali(self.symbol[2]):
                self.exchange.cancel_all_orders(self.symbol[2])
                self.emalink = self.sma_link[0]
                self.goshort.append('link')
                while 'link' in self.golong:
                    self.golong.remove('link')
                print('開賣link!!,now time : ', self.data.datetime.datetime(), 'close : ', close_link)

        print('台灣時間 : ', twt, 'close_eth : ', close_eth, 'position_eth : ', position_size_eth, 'close_bnb : ', close_bnb,
              'position_bnb : ', position_size_bnb, 'close_link : ', close_link, 'position_link : ', position_size_link)

        '''--------------------------------------------------------------------------'''
        if self.live_data:
            print('golong list : ', self.golong, ', goshort list : ', self.goshort)
            # balance = self.exchange.fetch_balance()
            div = float(len(self.symbol)) + 0.1

            ''' 拿到餘額  帳戶總額 計算下單數量 先算要買的'''
            cash, value = self.broker.get_wallet_balance('USDT')

            if position_size_eth > 0 and 'eth' in self.golong:
                self.golong.remove('eth')
                print('先不多eth 有了')
            if position_size_eth < 0 and 'eth' in self.goshort:
                self.goshort.remove('eth')
                print('先不空eth 有了')
            '''bnb'''
            if position_size_bnb > 0 and 'bnb' in self.golong:
                self.golong.remove('bnb')
                print('先不多bnb 有了')
            if position_size_bnb < 0 and 'bnb' in self.goshort:
                self.goshort.remove('bnb')
                print('先不空bnb 有了')
            '''link'''
            if position_size_link > 0 and 'link' in self.golong:
                self.golong.remove('link')
                print('先不多link 有了')
            if position_size_link < 0 and 'link' in self.goshort:
                self.goshort.remove('link')
                print('先不空link 有了')

            '''下面為正常買賣 已存在的部分用市價出掉以免報幹虧錢 一半用market買一半打貪一點'''
            self.amount = float('{:.5f}'.format(math.floor(
                value / div / close_eth * self.leverage * 10000.0) / 10000.0))  # 取道第4位
            if 'eth' in self.golong:
                self.exchange.cancel_all_orders(self.symbol[0])
                try:
                    print('購買eth數量 : ', self.amount + abs(position_size_eth))
                    print('執行買入eth，台灣時間 : ', twt, 'close : ', close_eth)
                    self.exchange.create_order(
                        self.symbol[0], 'Market', self.longside, self.amount / 2 + abs(position_size_eth))
                    # limit + price  #self.amount + position_size
                    order = self.exchange.create_order(
                        self.symbol[0], 'limit', self.longside, self.amount / 2, price=low_eth)
                except:
                    print('錢不夠')
                self.golong.remove('eth')

            if 'eth' in self.goshort:
                self.exchange.cancel_all_orders(self.symbol[0])
                try:
                    print('販賣eth數量 : ', self.amount + abs(position_size_eth))
                    print('執行賣出eth，台灣時間 : ', twt, 'close : ', close_eth)
                    self.exchange.create_order(
                        self.symbol[0], 'Market', self.shortside, self.amount / 2 + abs(position_size_eth))
                    order = self.exchange.create_order(
                        self.symbol[0], 'limit', self.shortside, self.amount / 2, price=high_eth)
                except:
                    print('錢不夠')
                self.goshort.remove('eth')

            '''bnb'''
            self.amount = float('{:.5f}'.format(math.floor(
                value / div / close_bnb * self.leverage * 10000.0) / 10000.0))  # 取道第4位
            if 'bnb' in self.golong:
                self.exchange.cancel_all_orders(self.symbol[1])
                try:
                    print('購買bnb數量 : ', self.amount + abs(position_size_bnb))
                    print('執行買入bnb，台灣時間 : ', twt, 'close : ', close_bnb)
                    self.exchange.create_order(
                        self.symbol[1], 'Market', self.longside, self.amount / 2 + abs(position_size_bnb))
                    # limit + price  #self.amount + position_size
                    order = self.exchange.create_order(
                        self.symbol[1], 'limit', self.longside, self.amount / 2, price=low_bnb)
                except:
                    print('錢不夠')
                self.golong.remove('bnb')

            if 'bnb' in self.goshort:
                self.exchange.cancel_all_orders(self.symbol[1])
                try:
                    print('販賣bnb數量 : ', self.amount + abs(position_size_bnb))
                    print('執行賣出bnb，台灣時間 : ', twt, 'close : ', close_bnb)
                    self.exchange.create_order(
                        self.symbol[1], 'Market', self.shortside, self.amount / 2 + abs(position_size_bnb))
                    order = self.exchange.create_order(
                        self.symbol[1], 'limit', self.shortside, self.amount / 2, price=high_bnb)
                except:
                    print('錢不夠')
                self.goshort.remove('bnb')

            '''link'''
            self.amount = float('{:.5f}'.format(math.floor(
                value / div / close_link * self.leverage * 10000.0) / 10000.0))  # 取道第4位
            if 'link' in self.golong:
                self.exchange.cancel_all_orders(self.symbol[2])
                try:
                    print('購買link數量 : ', self.amount + abs(position_size_link))
                    print('執行買入link，台灣時間 : ', twt, 'close : ', close_link)
                    self.exchange.create_order(
                        self.symbol[2], 'Market', self.longside, self.amount / 2 + abs(position_size_link))
                    # limit + price  #self.amount + position_size
                    order = self.exchange.create_order(
                        self.symbol[2], 'limit', self.longside, self.amount / 2, price=low_link)
                except:
                    print('錢不夠')
                self.golong.remove('link')

            if 'link' in self.goshort:
                self.exchange.cancel_all_orders(self.symbol[2])
                try:
                    print('販賣link數量 : ', self.amount + abs(position_size_link))
                    print('執行賣出link，台灣時間 : ', twt, 'close : ', close_link)
                    self.exchange.create_order(
                        self.symbol[2], 'Market', self.shortside, self.amount / 2 + abs(position_size_link))
                    order = self.exchange.create_order(
                        self.symbol[2], 'limit', self.shortside, self.amount / 2, price=high_link)
                except:
                    print('錢不夠')
                self.goshort.remove('link')
        else:
            # Avoid checking the balance during a backfill. Otherwise, it will
            # Slow things down.
            cash = 'NA'
            return

    def notify_data(self, data, status, *args, **kwargs):
        dn = data._name
        dt = datetime.now()
        msg = 'Data Status: {}'.format(data._getstatusname(status))
        print(dt, dn, msg)
        if data._getstatusname(status) == 'LIVE':
            self.live_data = True
        else:
            self.live_data = False


class Test(bt.Strategy):
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('%.2f 趴, %.2f 趴' % (trade.pnl/self.broker.getvalue()
                 * 100, self.broker.getvalue()/10000.0))

    def __init__(self):
        '''ATR!!!!!!!!!!!!!!!'''
        self.ATR_eth = bt.ind.AverageTrueRange(self.data, period=100)
        self.nLoss_eth = self.ATR_eth * 0.5
        self.ATRtracking_eth = 0
        self.lastATRtracking_eth = 0

        self.ATR_bnb = bt.ind.AverageTrueRange(self.data1, period=100)
        self.nLoss_bnb = self.ATR_bnb * 0.5
        self.ATRtracking_bnb = 0
        self.lastATRtracking_bnb = 0

        self.ATR_link = bt.ind.AverageTrueRange(self.data2, period=100)
        self.nLoss_link = self.ATR_link * 0.5
        self.ATRtracking_link = 0
        self.lastATRtracking_link = 0
        '''每組data的數據'''
        self.HA_eth = bt.ind.HeikinAshi(self.data)
        self.sma_eth = bt.ind.SMA(self.HA_eth.ha_close(), period=21)
        self.ema_eth = bt.ind.EMA(self.sma_eth, period=21)
        self.crossdowneth = bt.ind.CrossDown(self.sma_eth, self.ema_eth)
        self.crossupeth = bt.ind.CrossUp(self.sma_eth, self.ema_eth)

        self.HA_bnb = bt.ind.HeikinAshi(self.data1)
        self.sma_bnb = bt.ind.SMA(self.HA_bnb.ha_close(), period=21)
        self.ema_bnb = bt.ind.EMA(self.sma_bnb, period=21)
        self.crossdownbnb = bt.ind.CrossDown(self.sma_bnb, self.ema_bnb)
        self.crossupbnb = bt.ind.CrossUp(self.sma_bnb, self.ema_bnb)

        self.HA_link = bt.ind.HeikinAshi(self.data2)
        self.sma_link = bt.ind.SMA(self.HA_link.ha_close(), period=21)
        self.ema_link = bt.ind.EMA(self.sma_link, period=21)
        self.crossdownlink = bt.ind.CrossDown(self.sma_link, self.ema_link)
        self.crossuplink = bt.ind.CrossUp(self.sma_link, self.ema_link)

        self.isbuying = []
        self.isselling = []
        self.golong = []
        self.goshort = []
        self.trendup = []
        self.trenddown = []
        self.takeprofit_eth = 9999999
        self.takeprofit_bnb = 9999999
        self.takeprofit_link = 9999999
        self.emaeth = 999999
        self.emabnb = 999999
        self.emalink = 999999
    # 基本參數資料
        self.symbol = ['ETH/USDT', 'BNB/USDT', 'LINK/USDT']
        self.symbols = ['ETHUSDT', 'BNBUSDT', 'LINKUSDT']

        self.leverage = 3
        self.amount = 0.005
        self.longside = 'buy'
        self.shortside = 'sell'
        self.exchange = ccxt.binance({
            'apiKey': api_Key,
            'secret': secret_Key,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
        '''下面這行導致訪問出錯的'''
        self.mks = self.exchange.load_markets()
        '''設定各種槓桿倍數'''
        self.market = self.exchange.market(self.symbol[0])
        self.exchange.fapiPrivate_post_leverage({
            'symbol': self.market['id'],
            'leverage': self.leverage,
        })
        self.market = self.exchange.market(self.symbol[1])
        self.exchange.fapiPrivate_post_leverage({
            'symbol': self.market['id'],
            'leverage': self.leverage,
        })
        self.market = self.exchange.market(self.symbol[2])
        self.exchange.fapiPrivate_post_leverage({
            'symbol': self.market['id'],
            'leverage': self.leverage,
        })

    def next(self):
        twt = datetime.utcnow() - timedelta(hours=4+12)
        '''統一每種幣種的開高低 +-'''
        print('time : ', twt, ',data : ', self.data.close[0], ',data1 : ', self.data1.close[0],
              ',data2 : ', self.data2.close[0])
        close_eth = self.data.close[0]
        high_eth = self.data.high[0]
        low_eth = self.data.low[0]

        close_bnb = self.data1.close[0]
        high_bnb = self.data1.high[0]
        low_bnb = self.data1.low[0]

        close_link = self.data2.close[0]
        high_link = self.data2.high[0]
        low_link = self.data2.low[0]

        '''--------------------------------------------------------------------------'''
        if self.live_data:
            print('live')
            # balance = self.exchange.fetch_balance()
        else:
            # Avoid checking the balance during a backfill. Otherwise, it will
            # Slow things down.
            cash = 'NA'
            return

    def notify_data(self, data, status, *args, **kwargs):
        dn = data._name
        dt = datetime.now()
        msg = 'Data Status: {}'.format(data._getstatusname(status))
        print(dt, dn, msg)
        if data._getstatusname(status) == 'LIVE':
            self.live_data = True
        else:
            self.live_data = False


'''slef indicators'''


class StochasticRSI(Indicator):
    """
    K - The time period to be used in calculating the %K. 3 is the default.
    D - The time period to be used in calculating the %D. 3 is the default.
    RSI Length - The time period to be used in calculating the RSI
    Stochastic Length - The time period to be used in calculating the Stochastic

    Formula:
    %K = SMA(100 * (RSI(n) - RSI Lowest Low(n)) / (RSI HighestHigh(n) - RSI LowestLow(n)), smoothK)
    %D = SMA(%K, periodD)

    """
    lines = ('fastk', 'fastd',)

    params = (
        ('k_period', 3),
        ('d_period', 3),
        ('rsi_period', 14),
        ('stoch_period', 14),
        ('movav', MovAv.Simple),
        ('rsi', RelativeStrengthIndex),
        ('upperband', 80.0),
        ('lowerband', 20.0),
    )

    plotlines = dict(percD=dict(_name='%D', ls='--'),
                     percK=dict(_name='%K'))

    def _plotlabel(self):
        plabels = [self.p.k_period, self.p.d_period, self.p.rsi_period, self.p.stoch_period]
        plabels += [self.p.movav] * self.p.notdefault('movav')
        return plabels

    def _plotinit(self):
        self.plotinfo.plotyhlines = [self.p.upperband, self.p.lowerband]

    def __init__(self):
        source = (self.data.high + self.data.low + self.data.close) / 3
        rsi = bt.ind.RSI(source, period=self.p.rsi_period)
        rsi_ll = bt.ind.Lowest(rsi, period=self.p.stoch_period)
        rsi_hh = bt.ind.Highest(rsi, period=self.p.stoch_period)
        stochrsi = (rsi - rsi_ll) / (rsi_hh - rsi_ll)

        self.l.fastk = k = self.p.movav(100.0 * stochrsi, period=self.p.k_period)
        self.l.fastd = self.p.movav(k, period=self.p.d_period)
        # rsi = bt.ind.RSI((self.data.open + self.data.close + self.data.high + self.data.low) / 4 ,period = self.p.rsi_period)
        # rsi_ll = bt.ind.Lowest(rsi, period = self.p.rsi_period)
        # rsi_hh = bt.ind.Highest(rsi, period = self.p.rsi_period)
        # stochrsi = (rsi - rsi_ll) / (rsi_hh - rsi_ll)
        #
        # self.l.fastk = k = self.p.movav(100.0 * stochrsi, period = self.p.period)
        # self.l.fastd = self.p.movav(k, period = self.p.period)

        # rsi_hh = Highest(self.p.rsi(period=self.p.rsi_period), period=self.p.stoch_period)
        # rsi_ll = Lowest(self.p.rsi(period=self.p.rsi_period), period=self.p.stoch_period)
        # knum = self.p.rsi(period=self.p.rsi_period) - rsi_ll
        # kden = rsi_hh - rsi_ll
        #
        # self.k = self.p.movav(100.0 * (knum / kden), period=self.p.k_period)
        # self.d = self.p.movav(self.k, period=self.p.d_period)
        #
        # self.lines.fastk = self.k
        # self.lines.fastd = self.d


class Trade_pro(bt.Strategy):
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('%.2f 趴, %.2f 趴' % (trade.pnl/self.broker.getvalue()
                 * 100, self.broker.getvalue()/10000.0))

    def __init__(self):
        '''ATR!!!!!!!!!!!!!!!'''
        self.ATR_eth = bt.ind.AverageTrueRange(self.data, period=5)
        self.take_profit_eth = self.ATR_eth * 2.1
        self.stop_loss_eth = self.ATR_eth * 3.4

        '''EMAs'''
        self.ema_s_eth = bt.ind.EMA(period=7)
        self.ema_m_eth = bt.ind.EMA(period=8)
        self.ema_l_eth = bt.ind.EMA(period=550)
        'RSI'
        self.rsi_filter = bt.ind.RSI_Safe(period=1)
        self.stochRSI_eth = StochasticRSI(k_period=3, d_period=3, rsi_period=11, stoch_period=15)
        self.crossup_eth = bt.ind.CrossUp(self.stochRSI_eth.l.fastk, self.stochRSI_eth.l.fastd)
        self.crossdown_eth = bt.ind.CrossDown(self.stochRSI_eth.l.fastk, self.stochRSI_eth.l.fastd)
    # 基本參數資料
        self.symbol = ['ETH/USDT', 'BNB/USDT', 'LINK/USDT']
        self.symbols = ['ETHUSDT', 'BNBUSDT', 'LINKUSDT']
        self.golong = set()
        self.goshort = set()
        self.leverage = 2
        self.longside = 'buy'
        self.shortside = 'sell'
        self.exchange = ccxt.binance({
            'apiKey': api_Key,
            'secret': secret_Key,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
        '''下面這行導致訪問出錯的'''
        self.mks = self.exchange.load_markets()
        '''設定各種槓桿倍數'''
        self.market = self.exchange.market(self.symbol[0])
        self.exchange.fapiPrivate_post_leverage({
            'symbol': self.market['id'],
            'leverage': self.leverage,
        })
        self.market = self.exchange.market(self.symbol[1])
        self.exchange.fapiPrivate_post_leverage({
            'symbol': self.market['id'],
            'leverage': self.leverage,
        })
        self.market = self.exchange.market(self.symbol[2])
        self.exchange.fapiPrivate_post_leverage({
            'symbol': self.market['id'],
            'leverage': self.leverage,
        })
        '''
		self.exchange.fapiPrivate_post_margintype({
		    'symbol': self.market['id'],
		    'marginType': 'ISOLATED',
		})
		'''
    def set_leverage():
        return

    def next(self):
        response = self.exchange.fapiPrivateV2_get_positionrisk()
        allcrypto = [x for x in response if x['symbol'] in self.symbols]
        position_size_eth = float([x['positionAmt']
                                  for x in allcrypto if self.symbols[0] == x['symbol']][0])
        entryP_eth = float([x['entryPrice']
                           for x in allcrypto if self.symbols[0] == x['symbol']][0])
        # position_size_bnb = float([x['positionAmt']
        #                           for x in allcrypto if self.symbols[1] == x['symbol']][0])
        # entryP_bnb = float([x['entryPrice']
        #                    for x in allcrypto if self.symbols[1] == x['symbol']][0])
        # position_size_link = float([x['positionAmt']
        #                            for x in allcrypto if self.symbols[2] == x['symbol']][0])
        # entryP_link = float([x['entryPrice']
        #                     for x in allcrypto if self.symbols[2] == x['symbol']][0])
        '''拿到台灣的時間'''
        twt = datetime.utcnow() - timedelta(hours=4+12)
        '''統一每種幣種的開高低 +-'''
        close_eth = self.data.close[0]
        high_eth = self.data.high[0]
        low_eth = self.data.low[0]

        # close_bnb = self.data1.close[0]
        # high_bnb = self.data1.high[0]
        # low_bnb = self.data1.low[0]
        #
        # close_link = self.data2.close[0]
        # high_link = self.data2.high[0]
        # low_link = self.data2.low[0]

        '''下面記錄各種幣種的買入賣出'''
        if position_size_eth == 0:
            if close_eth > self.ema_s_eth[0] > self.ema_m_eth[0] > self.ema_l_eth[0] and self.crossup_eth and self.rsi_filter < 50:
                self.golong.add('eth')
                self.goshort.remove('eth')
                # self.exchange.cancel_all_orders(self.symbol[0])  # 以防萬一
            if close_eth < self.ema_s_eth[0] < self.ema_m_eth[0] < self.ema_l_eth[0] and self.crossdown_eth and self.rsi_filter > 50:
                self.goshort.add('eth')
                self.golong.remove('eth')
                # self.exchange.cancel_all_orders(self.symbol[0])  # 以防萬一
        print('台灣時間 : ', twt, 'close_eth : ', close_eth, 'position_eth : ', position_size_eth)
        # print('台灣時間 : ', twt, 'close_eth : ', close_eth, 'position_eth : ', position_size_eth, 'close_bnb : ', close_bnb,
        #       'position_bnb : ', position_size_bnb, 'close_link : ', close_link, 'position_link : ', position_size_link)

        '''--------------------------------------------------------------------------'''
        if self.live_data:
            # balance = self.exchange.fetch_balance()
            # div = float(len(self.symbol)) + 0.1
            ''' 拿到餘額  帳戶總額 計算下單數量 先算要買的'''
            cash, value = self.broker.get_wallet_balance('USDT')
            div = 1
            value = 10

            if position_size_eth > 0 and 'eth' in self.golong:
                self.golong.remove('eth')
                print('先不多eth 有了')
            if position_size_eth < 0 and 'eth' in self.goshort:
                self.goshort.remove('eth')
                print('先不空eth 有了')
            # '''bnb'''
            # if position_size_bnb > 0 and 'bnb' in self.golong:
            #     self.golong.remove('bnb')
            #     print('先不多bnb 有了')
            # if position_size_bnb < 0 and 'bnb' in self.goshort:
            #     self.goshort.remove('bnb')
            #     print('先不空bnb 有了')
            # '''link'''
            # if position_size_link > 0 and 'link' in self.golong:
            #     self.golong.remove('link')
            #     print('先不多link 有了')
            # if position_size_link < 0 and 'link' in self.goshort:
            #     self.goshort.remove('link')
            #     print('先不空link 有了')

            '''下面為正常買賣 先用市價單下單之後再取得成交價，之後用限價單掛單組成獲利指損'''
            self.amount = float('{:.5f}'.format(math.floor(
                value / div / close_eth * self.leverage * 10000.0) / 10000.0))  # 取道第4位
            if 'eth' in self.golong:
                self.exchange.cancel_all_orders(self.symbol[0])
                # try:
                print('購買eth數量 : ', self.amount)
                print('執行買入eth，台灣時間 : ', twt, 'close : ', close_eth)
                order1 = self.exchange.create_order(
                    self.symbol[0], 'market', self.longside, self.amount)
                order1_price = order1['price']
                if order1_price is None:
                    order1_price = order1['average']
                if order1_price is None:
                    cumulative_quote = float(order1['info']['cumQuote'])
                    executed_quantity = float(order1['info']['executedQty'])
                    order1_price = cumulative_quote / executed_quantity
                print('----------------------stop_loss_params-----------------------------------------------')

                stop_loss_params = {'stopPrice': order1_price - self.stop_loss_eth[0]}
                order2 = self.exchange.create_order(
                    self.symbol[0], 'stop_market', self.shortside, self.amount, None, stop_loss_params)
                # pprint(order2)

                print('----------------------take_profit_params-----------------------------------------------')

                take_profit_params = {'stopPrice': order1_price + self.take_profit_eth[0]}
                order3 = self.exchange.create_order(self.symbol[0], 'take_profit_market', self.shortside,
                                                    self.amount, None, take_profit_params)
                # except:
                #     print('錢不夠')
                self.golong.remove('eth')

            if 'eth' in self.goshort:
                self.exchange.cancel_all_orders(self.symbol[0])
                # try:
                print('販賣eth數量 : ', self.amount)
                print('執行賣出eth，台灣時間 : ', twt, 'close : ', close_eth)
                order1 = self.exchange.create_order(
                    self.symbol[0], 'Market', self.shortside, self.amount)
                order1_price = order1['price']
                if order1_price is None:
                    order1_price = order1['average']
                if order1_price is None:
                    cumulative_quote = float(order1['info']['cumQuote'])
                    executed_quantity = float(order1['info']['executedQty'])
                    order1_price = cumulative_quote / executed_quantity
                print('----------------------stop_loss_params-----------------------------------------------')

                stop_loss_params = {'stopPrice': order1_price + self.stop_loss_eth[0]}
                order2 = self.exchange.create_order(
                    self.symbol[0], 'stop_market', self.longside, self.amount, None, stop_loss_params)
                # pprint(order2)

                print('----------------------take_profit_params-----------------------------------------------')

                take_profit_params = {'stopPrice': order1_price - self.take_profit_eth[0]}
                order3 = self.exchange.create_order(self.symbol[0], 'take_profit_market', self.longside,
                                                    self.amount, None, take_profit_params)
                # except:
                # print('錢不夠')
                self.goshort.remove('eth')

            '''bnb
            self.amount = float('{:.5f}'.format(math.floor(
                value / div / close_bnb * self.leverage * 10000.0) / 10000.0))  # 取道第4位
            if 'bnb' in self.golong:
                self.exchange.cancel_all_orders(self.symbol[1])
                try:
                    print('購買bnb數量 : ', self.amount + abs(position_size_bnb))
                    print('執行買入bnb，台灣時間 : ', twt, 'close : ', close_bnb)
                    self.exchange.create_order(
                        self.symbol[1], 'Market', self.longside, self.amount / 2 + abs(position_size_bnb))
                    # limit + price  #self.amount + position_size
                    order = self.exchange.create_order(
                        self.symbol[1], 'limit', self.longside, self.amount / 2, price=low_bnb)
                except:
                    print('錢不夠')
                self.golong.remove('bnb')

            if 'bnb' in self.goshort:
                self.exchange.cancel_all_orders(self.symbol[1])
                try:
                    print('販賣bnb數量 : ', self.amount + abs(position_size_bnb))
                    print('執行賣出bnb，台灣時間 : ', twt, 'close : ', close_bnb)
                    self.exchange.create_order(
                        self.symbol[1], 'Market', self.shortside, self.amount / 2 + abs(position_size_bnb))
                    order = self.exchange.create_order(
                        self.symbol[1], 'limit', self.shortside, self.amount / 2, price=high_bnb)
                except:
                    print('錢不夠')
                self.goshort.remove('bnb')
            '''
            '''link
            self.amount = float('{:.5f}'.format(math.floor(
                value / div / close_link * self.leverage * 10000.0) / 10000.0))  # 取道第4位
            if 'link' in self.golong:
                self.exchange.cancel_all_orders(self.symbol[2])
                try:
                    print('購買link數量 : ', self.amount + abs(position_size_link))
                    print('執行買入link，台灣時間 : ', twt, 'close : ', close_link)
                    self.exchange.create_order(
                        self.symbol[2], 'Market', self.longside, self.amount / 2 + abs(position_size_link))
                    # limit + price  #self.amount + position_size
                    order = self.exchange.create_order(
                        self.symbol[2], 'limit', self.longside, self.amount / 2, price=low_link)
                except:
                    print('錢不夠')
                self.golong.remove('link')

            if 'link' in self.goshort:
                self.exchange.cancel_all_orders(self.symbol[2])
                try:
                    print('販賣link數量 : ', self.amount + abs(position_size_link))
                    print('執行賣出link，台灣時間 : ', twt, 'close : ', close_link)
                    self.exchange.create_order(
                        self.symbol[2], 'Market', self.shortside, self.amount / 2 + abs(position_size_link))
                    order = self.exchange.create_order(
                        self.symbol[2], 'limit', self.shortside, self.amount / 2, price=high_link)
                except:
                    print('錢不夠')
                self.goshort.remove('link')
            '''

        else:
            # Avoid checking the balance during a backfill. Otherwise, it will
            # Slow things down.
            cash = 'NA'
            return
        '''如果沒有於當下執行，下一根就不下單了'''
        self.goshort = set()
        self.golong = set()

    def notify_data(self, data, status, *args, **kwargs):
        dn = data._name
        dt = datetime.now()
        msg = 'Data Status: {}'.format(data._getstatusname(status))
        print(dt, dn, msg)
        if data._getstatusname(status) == 'LIVE':
            self.live_data = True
        else:
            self.live_data = False
