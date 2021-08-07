import backtrader as bt
import numpy as np
import pandas as pd
from datetime import datetime, date
import datetime
from backtrader.indicators import Indicator, MovAv, RelativeStrengthIndex, Highest, Lowest
# from tqdm.auto import tqdm
# opt_count_total = cerebro.get_opt_runcount()
# pbar = tqdm(desc='Opt runs', leave=True, position=1, unit='run', total=opt_count_total)
#
#
# def bt_opt_callback(cb):
#     pbar.update()


'''
self-write indicators
'''


class SuperTrendBand(bt.Indicator):
    """
    Helper inidcator for Supertrend indicator
    """
    params = (('period', 7), ('multiplier', 3))
    lines = ('basic_ub', 'basic_lb', 'final_ub', 'final_lb')

    def __init__(self):
        self.atr = bt.indicators.AverageTrueRange(period=self.p.period)
        self.l.basic_ub = ((self.data.high + self.data.low) / 2) + (self.atr * self.p.multiplier)
        self.l.basic_lb = ((self.data.high + self.data.low) / 2) - (self.atr * self.p.multiplier)

    def next(self):
        if len(self)-1 == self.p.period:
            self.l.final_ub[0] = self.l.basic_ub[0]
            self.l.final_lb[0] = self.l.basic_lb[0]
        else:
            # =IF(OR(basic_ub<final_ub*,close*>final_ub*),basic_ub,final_ub*)
            if self.l.basic_ub[0] < self.l.final_ub[-1] or self.data.close[-1] > self.l.final_ub[-1]:
                self.l.final_ub[0] = self.l.basic_ub[0]
            else:
                self.l.final_ub[0] = self.l.final_ub[-1]

            # =IF(OR(baisc_lb > final_lb *, close * < final_lb *), basic_lb *, final_lb *)
            if self.l.basic_lb[0] > self.l.final_lb[-1] or self.data.close[-1] < self.l.final_lb[-1]:
                self.l.final_lb[0] = self.l.basic_lb[0]
            else:
                self.l.final_lb[0] = self.l.final_lb[-1]


class SuperTrend(bt.Indicator):
    """
    Super Trend indicator
    """
    params = (('period', 7), ('multiplier', 3))
    lines = ('super_trend',)
    plotinfo = dict(subplot=False)

    def __init__(self):
        self.stb = SuperTrendBand(period=self.p.period, multiplier=self.p.multiplier)

    def next(self):
        if len(self) - 1 == self.p.period:
            self.l.super_trend[0] = self.stb.final_ub[0]
            return

        if self.l.super_trend[-1] == self.stb.final_ub[-1]:
            if self.data.close[0] <= self.stb.final_ub[0]:
                self.l.super_trend[0] = self.stb.final_ub[0]
            else:
                self.l.super_trend[0] = self.stb.final_lb[0]

        if self.l.super_trend[-1] == self.stb.final_lb[-1]:
            if self.data.close[0] >= self.stb.final_lb[0]:
                self.l.super_trend[0] = self.stb.final_lb[0]
            else:
                self.l.super_trend[0] = self.stb.final_ub[0]


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
        source = self.data.close
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


'''

self-write indicators - End

'''


class MaCrossStrategy(bt.Strategy):  # 擠壓蹲點法

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        # 有交易提交/被接受，啥也不做
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 交易完成，报告结果
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("交易成功")
                self.comm += order.executed.comm
            else:

                self.comm += order.executed.comm
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("交易失敗")
        self.order = None

    def __init__(self):
        self.comm = 0
        # 開槓桿瞜
        self.order = None
        # self.leverage = 4

        self.way1 = 0
        self.way2 = 0
        self.way3 = 0
        self.way4 = 0
        self.way5 = 0
        self.way6 = 0
        self.way7 = 0
        self.way8 = 0

        self.surely_conditions_long = None
        self.surely_conditions_short = None
        self.longorder = None
        self.shortorder = None
        self.highestprice = 0
        self.lowestprice = 1e10
        self.longATRstopTrailing = 0
        self.shortATRstopTrailing = 1e10

        self.period = 25
        self.pnl = 1.0
        # EMA array
        self.ema_20 = bt.ind.EMA(period=20, plot=False)
        self.ema_25 = bt.ind.EMA(period=25, plot=False)
        self.ema_30 = bt.ind.EMA(period=30, plot=False)
        self.ema_35 = bt.ind.EMA(period=35, plot=False)
        self.ema_40 = bt.ind.EMA(period=40, plot=False)
        self.ema_45 = bt.ind.EMA(period=45, plot=False)
        self.ema_50 = bt.ind.EMA(period=50, plot=False)
        self.ema_55 = bt.ind.EMA(period=55, plot=False)
        # Bullish Bearish
        # > self.ema_30 > self.ema_35 > self.ema_40 > self.ema_45 > self.ema_50 > self.ema_55
        self.bulllish = self.ema_20 > self.ema_55
        # < self.ema_30 < self.ema_35 < self.ema_40 < self.ema_45 < self.ema_50 < self.ema_55
        self.bearish = self.ema_20 < self.ema_55
        #
        self.sma_8 = bt.ind.SMA(period=21)
        self.ema_8 = bt.ind.EMA(self.sma_8, period=21)
#         self.MTM = bt.ind.AccelerationDecelerationOscillator(period = 25)
#         self.close = self.data.close
        # BB
        self.multKC = 1.5
        self.ma = bt.ind.SMA(period=self.period, plot=False)
        self.dev = bt.ind.StandardDeviation(period=self.period, plot=False) * self.multKC
        self.upperBB = self.ma + self.dev
        self.lowerBB = self.ma - self.dev
        # KC
        self.rangeMA = bt.ind.AverageTrueRange(period=25, plot=False)
        self.upperKC = self.ma + self.rangeMA * self.multKC
        self.lowerKC = self.ma - self.rangeMA * self.multKC
        # conditions
        # 8_MA & SMA
        self.crossup = bt.ind.CrossUp(self.sma_8, self.ema_8, plot=False)
        self.crossdown = bt.ind.CrossDown(self.sma_8, self.ema_8, plot=False)
        # squeeze LZ Once
        self.squzOff = bt.ind.CrossUp(self.upperKC, self.upperBB, plot=False)  # squzOff
        self.squzOn = bt.ind.CrossDown(self.upperKC, self.upperBB, plot=False)  # squzOn

        self.ON = self.upperKC > self.upperBB
        self.OFF = self.upperKC < self.upperBB
        # MTM
        self.MTM = bt.ind.AccelerationDecelerationOscillator(period=self.period, plot=False)
#         self.linregMTM = bt.ind.OLS_BetaN(plot = False) #period = 25 寫在裡面
        # WT
        self.hlc3 = (self.data.close + self.data.high + self.data.low) / 3
        self.n1 = 10
        self.n2 = 21
        self.esa = bt.ind.EMA(self.hlc3, period=self.n1, plot=False)
        self.d = bt.ind.EMA(abs(self.hlc3 - self.esa), period=self.n1, plot=False)
        self.ci = (self.hlc3 - self.esa) / (0.015 * self.d)
        self.WT1 = bt.ind.EMA(self.ci, period=self.n2, plot=False)
        self.WT2 = bt.ind.SMA(self.WT1, period=4, plot=False)
        self.WTMTM = self.WT1 - self.WT2

        self.WTcrossdown = bt.ind.CrossDown(self.WT1, self.WT2)
        self.WTcrossup = bt.ind.CrossUp(self.WT1, self.WT2)
        # Higest Lowest
        self.highest20 = bt.ind.Highest(period=20,  plot=False)
        self.lowest20 = bt.ind.Lowest(period=20,  plot=False)
        # RSI
        # self.k, self.d = bt.ind.Stochastic(period = 8)
        # self.d = bt.ind.StochasticFast(period = 8)
        self.crossover = bt.ind.CrossOver(bt.ind.Stochastic(), bt.LineNum(50.0),  plot=False)

        # BB BBW short
        self.BB20 = bt.ind.BollingerBands(plot=False)  # 20 2
        self.crossbotBB = self.data.close < self.BB20.lines.bot
        self.crossbotBB1 = self.data.open < self.BB20.lines.bot
        self.midstop = self.data.close > self.BB20.lines.mid
        self.BBwidth = self.BB20.lines.top - self.BB20.lines.bot

        # ATR stop
        self.ATR = bt.ind.AverageTrueRange(period=5) * 4.5
        self.lowestATR = bt.ind.Lowest(self.ATR, period=360)
        self.highestATR = bt.ind.Highest(self.ATR, period=360)

    def next(self):
        self.ATRratio = 1 - (self.ATR - self.lowestATR) / (self.highestATR - self.lowestATR)
        self.val_start = self.broker.get_cash()  # 檢查餘額
        self.RSIcro = self.crossover.get(size=3)
        self.size = (self.broker.getvalue() * self.ATRratio) / self.data  # 100趴錢買
        self.longsize = self.size * 0.9
        self.shortsize = self.size * 0.3
        # long
        self.c1 = self.OFF.get()[0] > 0  # Nsqz #Y
        self.c2 = self.ON.get()[0] > 0  # sqz

        self.c3 = all(self.ON.get(size=4)[:3]) > 0  # 最近三根開壓

        # linreg
        self.c5 = self.MTM.get(size=1)[0] < 0  # Y
        self.sc5 = self.MTM.get(size=1)[0] > 0  # 動能為正
        self.c6 = self.MTM.get(size=1)[0] > self.MTM.get(size=2)[0]  # Y #動能遞增
        self.sc6 = self.MTM.get(size=1)[0] < self.MTM.get(size=2)[0]  # Y #動能遞減
        # MA EMA
        self.c7 = self.sma_8 > self.ema_8  # y 多頭
        self.sc7 = self.sma_8 < self.ema_8  # 空頭
        # crossup
        self.c8 = any(self.crossup.get(size=5)) > 0  # 近5根有交叉 #Y
        self.sc8 = any(self.crossdown.get(size=5)) > 0  # 近5根有交叉 #Y
        # K candles
        self.c9 = self.data.close > self.sma_8 and self.data.open > self.sma_8  # Y 開收於sma均線上
        self.sc9 = self.data.close < self.ema_8 and self.data.open < self.ema_8  # Y 開收於ema均線下

        # WT1
        self.up53 = self.WT1 > 53 and self.WT2 > 53
        self.up60 = self.WT1 > 60 and self.WT2 > 60

        self.down53 = self.WT1 < -53 and self.WT2 < -53
        self.down60 = self.WT1 < -60 and self.WT2 < -60
        self.down25 = self.WT1 < -25 and self.WT2 < -25
        # short
        self.narrow3 = self.BBwidth.get(size=3)[0] <= self.BBwidth.get(size=2)[
            0] <= self.BBwidth.get(size=1)[0]

        # 收於20根最低點

        # 多頭      開收在線上    動能增加   五根內交叉向上 動能為負 或者 釋放狀態
        self.surely_conditions_long = self.c7 and self.c9 and self.c6 and self.crossup and (
            self.c5 or self.c1)
        # 空頭      開收在線下    動能遞減               非多頭 或者     最近有東西交叉
        self.surely_conditions_short = self.sc7 and self.sc9 and self.sc6 and not self.bulllish and self.RSIcro and (
            self.sc5 or self.c1) and self.crossdown  # self.lowest20 (self.sc5 or self.c1) and self.sc8
        # self.surely_conditions_short = self.narrow3 and self.crossbotBB and self.crossbotBB1

        # print('money:date')
        # print(self.broker.getvalue(),self.datetime.datetime(ago=0))
        # print('sc7 : ,',self.sc7,'sc9 : ,',self.sc9,'sc6 : ,',self.sc6,'sc8 : ,',self.sc8,'bulllish : ,',self.bulllish.get(),'RSIcro : ,',self.RSIcro)
        # print('time : ', self.datetime.datetime(ago=0), 'hour time frame : ',self.data.close[0])
        # print('time : ', self.datetime.datetime(ago=0), 'day time frame : ',self.data1.close[0])

        if not self.position:  # 如果沒有倉位的話
            if self.surely_conditions_long:

                # print('-'*50,bt.CommissionInfo().getsize(self.data, self.val_start),'-'*50)
                # print('開單時間', self.datetime.datetime(ago=0))
                # print('多頭 : ', self.c7 ,'--開收在線上 : ', self.c9  ,'--動能增加 : ', self.c6, '--五根內交叉向上 : ', self.c8, '--動能為負 或者 釋放狀態 : ', ( self.c5 or self.c1))

                self.longorder = self.order_target_percent(
                    target=0.9, exectype=bt.Order.Limit, price=self.data.close)  # self.size
                self.buyprice = self.data.close  # 拿到開單時候的價錢
                if self.order:
                    return
            elif self.surely_conditions_short:
                # print('開單時間')
                # print(self.datetime.datetime(ago=0))
                #                 print('-' * 50)
                # print('{} Send Buy, close {}'.format(
                #     self.data.datetime.date(),
                #     self.data.close[0])
                # )
                # print('最近三根BB寬度 : ',self.BBwidth.get(size = 3))
                self.shortorder = self.order_target_percent(
                    size=-0.9, exectype=bt.Order.Limit, price=self.data.close)
                self.buyprice = self.data.close  # 拿到開單時候的價錢
        if self.position:
            # 有倉位
            self.highestprice = max(self.data.high.get()[0], self.buyprice, self.highestprice)
            self.lowestprice = min(self.data.low.get()[0], self.buyprice, self.lowestprice)
            self.longATRstopTrailing = max(self.longATRstopTrailing, self.data.close-self.ATR)
            self.shortATRstopTrailing = min(self.shortATRstopTrailing, self.data.close+self.ATR)
            if self.longorder:
                if (self.WTcrossdown and self.up60):
                    print('方案1 60上方交叉')
                    self.close()
                    print('money:date')
                    print(self.broker.getvalue(), self.datetime.datetime(ago=0))
                    print('ratio')
                    print(str(round(self.broker.getvalue()/1000000, 2)) + '%')
                    self.highestprice = 0
                    self.lowestprice = 1e100
                    self.longATRstopTrailing = 0
                    # no pending long
                    self.longorder = None
                    self.way1 += 1
                elif self.longATRstopTrailing > self.data.close:  # self.highestprice *0.8 > self.data.close
                    print('方案2 ATR指損')
                    print('ATR : ', self.longATRstopTrailing)

                    self.close()
                    print(str(self.broker.getvalue()/1000000) + '%')
                    self.highestprice = 0
                    self.lowestprice = 1e100
                    self.longATRstopTrailing = 0
                    # no pending long
                    self.longorder = None
                    self.way2 += 1
            elif self.shortorder:

                if (self.WTcrossup and self.down53):
                    print('-' * 50)
                    print('方案3 WT指標')
                    self.close()
                    print('money : ', self.broker.getvalue(), 'date : ', self.datetime.datetime(
                        ago=0), 'ratio', str(self.broker.getvalue()/1000000), '%')
                    # print(self.broker.getvalue(),self.datetime.datetime(ago=0))
                    # print('ratio')
                    # print(str(self.broker.getvalue()/1000000) + '%')
                    print('pnl')
                    if (self.pnl - self.broker.getvalue()/1000000) < 0:
                        print('賺 ' + str(self.pnl - self.broker.getvalue()/1000000) + '%')
                        self.pnl = self.broker.getvalue()/1000000
                    else:
                        print('虧 ' + str(self.pnl - self.broker.getvalue()/1000000) + '%')
                        self.pnl = self.broker.getvalue()/1000000
                    print('-' * 50)
                    self.highestprice = 0
                    self.lowestprice = 1e100
                    self.shortATRstopTrailing = 1e100
                    # no pending short
                    self.shortorder = None
                    self.way3 += 1
                elif self.shortATRstopTrailing < self.data.close:

                    print('-' * 50)
                    print('方案4 ATR停損')
                    self.close()
                    print('money : ', self.broker.getvalue(), 'date : ', self.datetime.datetime(
                        ago=0), 'ratio', str(self.broker.getvalue()/1000000), '%')
                    # print(self.broker.getvalue(),self.datetime.datetime(ago=0))
                    # print('ratio')
                    # print(str(self.broker.getvalue()/1000000) + '%')
                    print('pnl')
                    if (self.pnl - self.broker.getvalue()/1000000) < 0:
                        print('賺 ' + str(self.pnl - self.broker.getvalue()/1000000) + '%')
                        self.pnl = self.broker.getvalue()/1000000
                    else:
                        print('虧 ' + str(self.pnl - self.broker.getvalue()/1000000) + '%')
                        self.pnl = self.broker.getvalue()/1000000
                    print('-' * 50)
                    self.highestprice = 0
                    self.lowestprice = 1e100
                    self.shortATRstopTrailing = 1e100
                    # no pending short
                    self.shortorder = None
                    self.way4 += 1
                elif self.crossup and self.data.close[0] > self.buyprice * 0.95:
                    print('方案5 MA停損')
                    self.close()
                    print('money:date')
                    print(self.broker.getvalue(), self.datas[0].datetime.date(0))
                    print(str(self.broker.getvalue()/1000000) + '%')
                    self.lowestprice = 1e10
                    # no pending short
                    self.shortorder = None
                    self.way5 += 1
                # elif self.midstop:
                #
                #     print('-' * 50)
                #     print('方案5 under  mid')
                #     self.close()
                #     print('money : ',self.broker.getvalue(),'date : ',self.datetime.datetime(ago=0), 'ratio', str(self.broker.getvalue()/1000000), '%')
                #     # print(self.broker.getvalue(),self.datetime.datetime(ago=0))
                #     # print('ratio')
                #     # print(str(self.broker.getvalue()/1000000) + '%')
                #     print('pnl')
                #     if (self.pnl - self.broker.getvalue()/1000000) < 0:
                #         print('賺 ' + str(self.pnl - self.broker.getvalue()/1000000) + '%')
                #         self.pnl = self.broker.getvalue()/1000000
                #     else:
                #         print('虧 ' + str(self.pnl - self.broker.getvalue()/1000000) + '%')
                #         self.pnl = self.broker.getvalue()/1000000
                #     print('-' * 50)
                #     self.highestprice = 0
                #     self.lowestprice = 1e100
                #     self.shortATRstopTrailing = 1e100
                #     #no pending short
                #     self.shortorder = None
                #     self.way5 += 1

                elif self.surely_conditions_long:
                    print('方案6 換倉')

                    self.close()
                    print('money:date')
                    print(self.broker.getvalue(), self.datetime.datetime(ago=0))
                    print(str(self.broker.getvalue()/1000000) + '%')
                    if (self.pnl - self.broker.getvalue()/1000000) < 0:
                        print('賺 ' + str(self.pnl - self.broker.getvalue()/1000000) + '%')
                        self.pnl = self.broker.getvalue()/1000000
                    else:
                        print('虧 ' + str(self.pnl - self.broker.getvalue()/1000000) + '%')
                        self.pnl = self.broker.getvalue()/1000000
                    self.highestprice = 0
                    self.lowestprice = 1e100
                    self.shortATRstopTrailing = 1e100
                    # no pending short
                    self.shortorder = None
                    self.way6 += 1

                    print('$'*500)


class GridStrategy(bt.Strategy):  # 網格

    def __init__(self):
        # 開槓桿瞜
        self.total_gain = 0
        self.gridnumber = 30  # 30
        self.cut_ratio = 0.9
        self.weight = None
        self.gridcount = 0
        self.record_last_price = []
        self.comm = 0.0
        self.lower = True
        self.total_size = 0

        self.sell_size = 0
        self.cutting = False
        self.profit, self.n_profit, self.t_profit = 0, 0, 0

        self.surely_conditions_long = None
        self.longorder = None
        self.longATRstopTrailing = 0
        self.shortATRstopTrailing = 1e10

        self.period = 8
        self.pnl = 1.0
        # EMA array
        self.ema_20 = bt.ind.EMA(period=20, plot=False)
        self.ema_25 = bt.ind.EMA(period=25, plot=False)
        self.ema_30 = bt.ind.EMA(period=30, plot=False)
        self.ema_35 = bt.ind.EMA(period=35, plot=False)
        self.ema_40 = bt.ind.EMA(period=40, plot=False)
        self.ema_45 = bt.ind.EMA(period=45, plot=False)
        self.ema_50 = bt.ind.EMA(period=50, plot=False)
        self.ema_55 = bt.ind.EMA(period=55, plot=False)
        #
        self.sma_8 = bt.ind.SMA(period=8)
        self.ema_8 = bt.ind.EMA(self.sma_8, period=8)
        # Bullish Bearish
        # > self.ema_30 > self.ema_35 > self.ema_40 > self.ema_45 > self.ema_50 > self.ema_55
        self.bulllish = self.sma_8 > self.ema_8
        # < self.ema_30 < self.ema_35 < self.ema_40 < self.ema_45 < self.ema_50 < self.ema_55
        self.bearish = self.sma_8 < self.ema_8

#         self.MTM = bt.ind.AccelerationDecelerationOscillator(period = 25)
#         self.close = self.data.close
        # BB
        self.multKC = 1.5
        self.ma = bt.ind.SMA(period=self.period, plot=False)
        self.dev = bt.ind.StandardDeviation(period=self.period, plot=False) * self.multKC
        self.upperBB = self.ma + self.dev
        self.lowerBB = self.ma - self.dev
        # KC
        self.rangeMA = bt.ind.AverageTrueRange(period=25, plot=False)
        self.upperKC = self.ma + self.rangeMA * self.multKC
        self.lowerKC = self.ma - self.rangeMA * self.multKC
        # conditions
        # 8_MA & SMA
        self.crossup = bt.ind.CrossUp(self.sma_8, self.ema_8, plot=False)
        self.crossdown = bt.ind.CrossDown(self.sma_8, self.ema_8, plot=False)
        # squeeze LZ Once
        self.squzOff = bt.ind.CrossUp(self.upperKC, self.upperBB, plot=False)  # squzOff
        self.squzOn = bt.ind.CrossDown(self.upperKC, self.upperBB, plot=False)  # squzOn

        self.ON = self.upperKC > self.upperBB
        self.OFF = self.upperKC < self.upperBB
        # MTM
        self.MTM = bt.ind.AccelerationDecelerationOscillator(period=self.period, plot=False)
#         self.linregMTM = bt.ind.OLS_BetaN(plot = False) #period = 25 寫在裡面
        # WT
        self.hlc3 = (self.data.close + self.data.high + self.data.low) / 3
        self.n1 = 14
        self.n2 = 17
        self.esa = bt.ind.EMA(self.hlc3, period=self.n1, plot=False)
        self.d = bt.ind.EMA(abs(self.hlc3 - self.esa), period=self.n1, plot=False)
        self.ci = (self.hlc3 - self.esa) / (0.015 * self.d)
        self.WT1 = bt.ind.EMA(self.ci, period=self.n2, plot=False)
        self.WT2 = bt.ind.SMA(self.WT1, period=4, plot=False)
        self.WTMTM = self.WT1 - self.WT2

        self.WTcrossdown = bt.ind.CrossDown(self.WT1, self.WT2)
        self.WTcrossup = bt.ind.CrossUp(self.WT1, self.WT2)
        # Higest Lowest
        self.highest60 = bt.ind.Highest(period=60,  plot=False)
        self.lowest60 = bt.ind.Lowest(period=60,  plot=False)
        # RSI
        # self.k, self.d = bt.ind.Stochastic(period = 8)
        # self.d = bt.ind.StochasticFast(period = 8)
        # self.crossover = bt.ind.CrossOver(bt.ind.Stochastic(), bt.LineNum(50.0),  plot = False)

        # BB BBW short
        self.BB20 = bt.ind.BollingerBands(plot=False)  # 20 2
        self.crossbotBB = self.data.close < self.BB20.lines.bot
        self.crossbotBB1 = self.data.open < self.BB20.lines.bot
        self.midstop = self.data.close > self.BB20.lines.mid
        self.BBwidth = self.BB20.lines.top - self.BB20.lines.bot

        # ATR stop
        self.ATR = bt.ind.AverageTrueRange(period=5, plot=True) * 1.2
        self.longATRstopTrailing = 0

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        # 有交易提交/被接受，啥也不做
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 交易完成，报告结果
        if order.status in [order.Completed]:
            if order.isbuy():

                self.comm += order.executed.comm
            else:

                self.comm += order.executed.comm
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("交易失敗")
        self.order = None

    def next(self):
        self.val_start = self.broker.get_cash()  # 檢查餘額
        self.total_value = self.broker.getvalue()
        # 1趴買多少量
        self.size_buy = self.total_value / self.gridnumber / self.data.close
        # long
        self.c1 = self.OFF.get()[0] > 0  # Nsqz #Y

        # linreg
        self.c5 = self.MTM.get(size=1)[0] < 0  # Y
        self.c6 = self.MTM.get(size=1)[0] > self.MTM.get(size=2)[0]  # Y #動能遞增

        # MA EMA
        self.c7 = self.sma_8 > self.ema_8  # y 多頭
        # crossup
        self.c8 = any(self.crossup.get(size=3)) > 0  # 近3根有交叉 #Y
        # K candles
        self.c9 = self.data.close > self.sma_8 and self.data.open > self.sma_8  # Y 開收於sma均線上

        # WT1
        self.up53 = self.WT1 > 53 and self.WT2 > 53
        self.down53 = self.WT1 < -53 and self.WT2 < -53
        self.down60 = self.WT1 < -60 and self.WT2 < -60
        # WTMTM
        self.c10 = self.WTMTM.get(size=1)[0] > self.WTMTM.get(size=2)[0]
        # short
        self.narrow3 = self.BBwidth.get(size=3)[0] <= self.BBwidth.get(size=2)[
            0] <= self.BBwidth.get(size=1)[0]
        # lower low
        self.lowerlow = (self.lowest60[0] < self.lowest60[-1]) and (self.lowest60[-1]
                                                                    < self.lowest60[-2]) and (self.lowest60[-2] < self.lowest60[-3])
        # don't buy in the same Position
        # if self.record_last_price:
        #     self.updown5 = self.data.close > self.record_last_price[-1][0] * 1.005 or self.data.close < self.record_last_price[-1][0] * 0.095
        # else:
        #     self.updown5 = True

        # 多頭      開收在線上    動能增加   五根內交叉向上 動能為負 或者 釋放狀態     並且多頭 並且不林帶變寬
        # self.surely_conditions_long = self.c7 and self.c9  and self.c6 and self.c8 and ( self.c5 or self.c1) and self.narrow3 and self.updown5
        self.buy_condition = self.c7 and self.c9 and self.c8 and self.c10 and not self.lowerlow
        self.sell_condition = self.WTcrossdown and self.up53
        # 50% or
        self.cutting = ((self.total_value - self.val_start) / self.total_value) > self.cut_ratio

        if self.buy_condition and len(self.record_last_price) < self.gridnumber:
            self.record_last_price.append(
                [self.data.close[0], self.size_buy, 2.5 * self.data.close[0] - 1.5 * self.data.low[-1]])
            self.record_last_price.sort(reverse=True)
            # aim
            self.total_size = self.position.size
            # print('After aim--', self.total_size )

            self.total_size += self.size_buy
            # self.buy(size = self.size, exectype=bt.Order.Limit, price=self.data.close)
            self.longorder = self.buy(
                size=self.size_buy, exectype=bt.Order.Limit, price=self.data.close)
            self.log('buy point')
            # print('after buy--',self.total_size)
            # print('現金餘額 : ',str(self.val_start))
            # print('Positions size : ', str(self.position.size),'Position price : ', str(self.position.price))
            # print('買到持倉數量 : ', self.total_size)

        self.longATRstopTrailing = max(self.longATRstopTrailing, self.data.close-self.ATR)
        while len(self.record_last_price) > 1:
            # print('-cross-:',self.WTcrossdown,'-60-',self.up60,'-lastprice-',self.record_last_price[-1][0] * 1.01)
            # print(self.data.close[0] > self.record_last_price[-1][0] * 1.01, 'close-',self.data.close[0],'-lowest-',self.record_last_price[-1][0] )
            # self.log('sell point')
            if self.sell_condition and self.data.close > self.record_last_price[-1][0] * 1.08:
                # print(float(self.data.close[0]-self.record_last_price[-1][0]) * 0.998)
                self.log('條件達成')
                self.log((self.data.close[0]-self.record_last_price[-1][0]) * 0.998)
                self.sell_size += self.record_last_price[-1][1]
                self.profit += self.record_last_price[-1][1] * \
                    float(self.data.close - self.record_last_price[-1][0]) * 0.998
                # pop the lowest price out
                self.record_last_price.pop()
            elif self.data.close > self.record_last_price[-1][0] * 1.1 and self.data.close < self.longATRstopTrailing:
                self.log('ATR10趴')
                self.log((self.data.close[0]-self.record_last_price[-1][0]) * 0.998)
                self.sell_size += self.record_last_price[-1][1]
                self.profit += self.record_last_price[-1][1] * \
                    (self.data.close - self.record_last_price[-1][0]) * 0.998
                # pop the lowest price out
                self.record_last_price.pop()
            elif self.data.close > self.record_last_price[-1][2]:
                self.log('白瞟')
                self.log((self.data.close[0]-self.record_last_price[-1][2]) * 0.998)
                self.sell_size += self.record_last_price[-1][1]
                self.profit += self.record_last_price[-1][1] * \
                    (self.data.close - self.record_last_price[-1][0]) * 0.998
                self.record_last_price.pop()

            else:
                break

        # check if > 50 % we cutting the high price order

        # print('cutting ratio : ',( ( self.total_value - self.val_start ) / self.total_value ))
        # sell size
        if self.sell_size > 0 and not self.cutting:
            # normal sell
            self.total_size -= self.sell_size
            # self.longorder = self.buy(size=self.size_buy, exectype=bt.Order.Limit, price=self.data.close)

            self.close(size=self.sell_size, exectype=bt.Order.Limit, price=self.data.close)
            print('total gain : ', self.profit)
            self.total_gain += self.profit
            # Returned
            self.sell_size = 0
            self.n_profit = 0
            self.profit = 0
            # #aim
            # self.total_size = self.position.size
            # print('After aim--', self.total_size )
        # 如果正要賣的話              且正要開剪       且沒有一次賣光還有高點可以剪的話
        elif self.sell_size > 0 and self.cutting and len(self.record_last_price) > 1:
            # < 10 就算了
            while self.profit > 10 and len(self.record_last_price) > 0:
                # print('0--',self.record_last_price[0][0], '1--', self.record_last_price[0][1])
                self.n_profit += self.record_last_price[0][1] * \
                    (self.record_last_price[0][0] - self.data.close)
                # 如果可以斬掉
                if self.profit >= self.n_profit:
                    self.sell_size += self.record_last_price[0][1]
                    self.profit -= self.n_profit

                    # pop the first element out
                    self.record_last_price.pop(0)
                    continue
                # 斬一部分
                elif self.profit < self.n_profit:
                    # 計算可以斬幾個
                    self.cut_size = self.profit / (self.record_last_price[0][0] - self.data.close)
                    self.sell_size += self.cut_size
                    # change size
                    self.record_last_price[0][1] -= self.cut_size
                    self.profit = 0
                    continue
                else:
                    break
            # cutting sell
            self.total_size -= self.sell_size
            # self.order_target_size( target = self.total_size )
            self.close(size=self.sell_size, exectype=bt.Order.Limit, price=self.data.close)
            print('Afer cutted, total gain : ', self.profit)
            print('n profit : ', self.n_profit)
            # Returned
            self.cut_size = 0
            self.sell_size = 0
            self.n_profit = 0
            self.profit = 0
            # #aim
            # self.total_size = self.position.size
            # print('After aim--', self.total_size )

    def stop(self):
        self.log("手续费:%.2f 成本比例:%.5f" % (self.comm, self.comm/self.broker.getvalue()))
        print('網格獲利', self.total_gain)


class TestStrategy(bt.Strategy):  # 測試

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0)
        print('%s, %s' % (dt.isoformat(), txt))

    def next(self):
        print('order_target_percent')
        self.longorder = self.order_target_size(target=0.5555555)
        print('Positions size : ', str(self.position.size),
              'Position price : ', str(self.position.price))


class min_49_Strategy(bt.Strategy):  # 網格
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        # 有交易提交/被接受，啥也不做
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 交易完成，报告结果
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("交易成功")
                self.comm += order.executed.comm
            else:

                self.comm += order.executed.comm
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("交易失敗")
        self.order = None

    def __init__(self):
        self.comm = 0
        self.ATR = bt.ind.AverageTrueRange(period=30)
        self.body = abs(self.data.close - self.data.open)
        self.body_avg = bt.ind.EMA(self.body, period=14)
        self.ema200 = bt.ind.EMA(period=200)
        self.rsi = bt.ind.RSI_Safe()
        # self.above200ema = self.data.close > self.ema200 and self.data.open > self.ema200

    def next(self):
        # 吞沒指標
        self.body_high = max(self.data.close[0], self.data.open[0])
        self.body_high_pre = max(self.data.close[-1], self.data.open[-1])
        self.body_low = min(self.data.close[0], self.data.open[0])
        self.body_low_pre = min(self.data.close[-1], self.data.open[-1])

        self.smallbody = self.body[0] < self.body_avg[0]
        self.smallbody_pre = self.body[-1] < self.body_avg[-1]

        self.longbody = self.body > self.body_avg
        self.upshadow = self.data.high[0] - self.body_high
        self.downshadow = self.body_low - self.data.low[0]
        self.hasupshadow = self.upshadow > 5.0 / 100 * self.body
        self.hasdownshadow = self.downshadow > 5.0 / 100 * self.body
        self.whitebody = self.data.open[0] < self.data.close[0]
        self.blackbody = self.data.open[0] > self.data.close[0]
        self.blackbody_pre = self.data.open[-1] > self.data.close[-1]
        self.range = self.data.high[0] - self.data.low[0]
        self.isinsidebar = self.body_high_pre > self.body_high and self.body_low_pre < self.body_low
        self.body_mid = (self.body / 2) + self.body_low
        self.shadowequqls = self.upshadow == self.downshadow or (abs(self.upshadow - self.downshadow) / np.clip(
            self.upshadow, 1e-10, 1e10) * 100) < 100.0 and (abs(self.downshadow - self.upshadow) / np.clip(self.upshadow, 1e-10, 1e10) * 100) < 100.0
        self.isdojibody = self.range > 0 and self.body <= self.range * (5.0 / 100)
        self.doji = self.shadowequqls and self.isdojibody
        self.patternLabelPosLow = self.data.low[0] - self.ATR * 0.6
        self.patternLabelPosHigh = self.data.high - self.ATR * 0.6
        # 能用 多頭方向
        self.EngulfingBullish = self.whitebody and self.longbody and self.blackbody_pre and self.smallbody_pre and self.data.close[
            0] >= self.data.open[-1] and self.data.open[0] <= self.data.close[-1] and (self.data.close[0] > self.data.open[-1] or self.data.open[0] < self.data.close[-1])
        # 能用 多頭方向
        # if self.EngulfingBullish:
        #     self.log(self.EngulfingBullish)
        self.above200ema = self.data.close > self.ema200 and self.data.open > self.ema200
        self.ema10 = all([ema < self.data.close[0] for ema in self.ema200.get(size=10)])
        self.buycondition = self.EngulfingBullish and self.rsi > 50 and self.above200ema and self.ema10
        self.getprofit = self.data.close - self.data.open
        self.pricelist = []
        self.buysize = 20

        self.stopprice = min(self.data.low[-1], self.data.low[0])
        self.limitprice = self.data.close[0] + self.getprofit * 1

        if self.buycondition:
            # self.buy(size = self.buysize, exectype=bt.Order.Limit, price=self.data.close)
            # self.buy_bracket(limitprice=self.limitprice, price=self.data.close[0], stopprice=self.stopprice,size = self.buysize , exectype=bt.Order.Limit)
            self.buy(size=self.buysize, exectype=bt.Order.Limit, price=self.data.close)
            self.sell(size=self.buysize, exectype=bt.Order.StopTrail, trailamount=self.getprofit)

            self.log(self.data.close[0])

    def stop(self):
        print('堪用')
        # self.log("手续费:%.2f 成本比例:%.5f" % (self.comm, self.comm/self.broker.getvalue()))


class Heikun_Ashi_Double_E_Strategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        # 有交易提交/被接受，啥也不做
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 交易完成，报告结果
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("成功買入")
                self.log(order.executed.price)
                self.comm += order.executed.comm
            else:
                self.log("成功賣出")
                self.log(order.executed.price)
                self.comm += order.executed.comm
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("交易失敗")
        self.order = None

    def __init__(self):
        self.open = 0
        self.new_open = False
        self.goshort = False
        self.golong = False
        self.comm = 0
        self.current_open = 0
        self.emaperiod = 1
        self.span = self.emaperiod + 1
        self.candles = 0
        self.EMAshift = 0
        self.SMAshift = 0
        self.start11 = False
        self.diff = 0
        self.new3hopen = 0
        self.current_high = 0
        self.currnet_low = 0
        self.h3ls = [2, 5, 8, 11, 14, 17, 20, 23]
        self.wfk = False
        self.h3queue = []
        self.h3haqueue = []
        self.red_shift = 0
        self.oopp = True
        # HA indicators
        self.HA_min = bt.ind.HeikinAshi(self.data)
        self.HA_hour = bt.ind.HeikinAshi(self.data1)
        self.HA_3hour = bt.ind.HeikinAshi(self.data2)

    def sma(self, candles, period=30):
        self.candles = candles
        self.period = period
        self.new_ema_list = self.HA_hour.ha_close.get(
            size=1, ago=-1) * 30 + self.HA_hour.ha_close.get() * 60
        # print('min檢查 : ', self.candles)
        self.ema = pd.DataFrame(self.new_ema_list).ewm(
            span=self.period + 1).mean()[0].loc[self.candles + 30]
        return self.ema

    def next(self):
        # if c<500:
        #     c += 1
        #     self.start11 = False
        # else:
        #     self.start11 = True

        self.val_start = self.broker.get_cash()  # 檢查餘額
        self.size = (self.broker.getvalue() * 0.9) / self.data  # 100趴錢買
        self.mincandles = self.data.datetime.time().minute
        if self.oopp:
            self.open = self.data.open[0]
            self.oopp = False

        if self.data.datetime.datetime().hour in self.h3ls and self.data.datetime.datetime().minute == 0:

            if self.wfk:
                self.h3queue.append([self.current_open, self.current_high,
                                    self.currnet_low, self.data.close.get(ago=-1)[0]])
            if len(self.h3queue) > 0:
                close = sum(self.h3queue[-1])*0.25
                self.h3haqueue.append([self.open, max(self.current_high, self.open, close), min(
                    self.currnet_low, self.open, close), close])
                # next Open
                self.open = (self.h3haqueue[-1][0] + self.h3haqueue[-1][3]) * 0.5

            # 第一次先拿到open
            self.current_open = self.data.open[0]
            self.new3hopen = self.data.datetime.datetime()
            self.start11 = True

        if self.start11:
            self.candles = (datetime.combine(date.min, self.data.datetime.time()) -
                            datetime.combine(date.min, self.new3hopen.time())).seconds // 60
            # self.log('candles--')
            # self.log(self.candles)
            self.current_high = max(self.data.high.get(size=self.candles + 1))
            self.currnet_low = min(self.data.low.get(size=self.candles + 1))
            # print('len : ', len(self.data.low.get(size = self.candles + 1 )))
            # self.HA_open_now = 0.5 * ( self.h3haqueue[-1][0] + self.h3haqueue[-1][-1] )
            # print(self.current_high)
            # print(self.currnet_low)
            self.HA_close_now = 0.25 * \
                (self.current_open + self.current_high + self.currnet_low + self.data.close[0])

            # self.HA_high_now = max(self.current_high,self.HA_open_now, self.HA_close_now)
            # self.HA_low_now = min(self.currnet_low,self.HA_open_now, self.HA_close_now)
            # if self.EMAshift:
            sma = self.sma(candles=self.mincandles, period=1)
            # print('time : ', self.datetime.datetime(), '1h sma : ', sma)

            if len(self.h3haqueue) > 0:
                crossup = self.diff < 0 and self.EMAshift > self.red_shift
                crossdown = self.diff > 0 and self.EMAshift < self.red_shift
                if crossup and not self.golong:
                    # self.buy(size = self.size,exectype=bt.Order.Market)
                    self.order_target_percent(target=0.9, exectype=bt.Order.Market)
                    have_cross = True
                    self.golong = True
                    self.goshort = False
                elif crossdown and not self.goshort:
                    # self.sell(size = self.size,exectype=bt.Order.Market)
                    self.order_target_percent(target=-0.9, exectype=bt.Order.Market)
                    # print(self.diff, self.EMAshift, self.SMAshift)
                    self.goshort = True
                    self.golong = False

            self.diff = self.EMAshift - self.red_shift

            self.SMAshift = sma
            print('time : ', self.datetime.datetime())
            if len(self.h3haqueue) > 0:
                print('3h open', self.h3haqueue[-1][0], '3hclose', self.h3haqueue[-1][3])
                print('newest open - ', self.open)
            # self.log(self.h3queue[-1])
            # print(crossup, crossdown)
            # print('藍色--', self.EMAshift,'綠色--',self.HA_close_now,'橘色30--',sma,'橘色1--', self.red_shift,'紅色--', self.HA_hour.ha_close[0])
            self.red_shift = self.HA_hour.ha_close[0]
            self.EMAshift = self.HA_close_now
            self.wfk = True
            print(self.open)
            # print('HAopen--',self.HA_open_now)
            # print('high--',self.current_high,'low--',self.currnet_low,'open--',self.current_open ,'close--',self.data.close[0])
            # print('-' * 50)


class Double_MA(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        # 有交易提交/被接受，啥也不做
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 交易完成，报告结果
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("成功買入")
                self.log(order.executed.price)
                self.comm += order.executed.comm
            else:
                self.log("成功賣出")
                self.log(order.executed.price)
                self.comm += order.executed.comm
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("交易失敗")
        self.order = None

    def __init__(self):

        self.comm = 0

        # Bullish Bearish
        # self.bulllish = self.ema_20 > self.ema_55 #> self.ema_30 > self.ema_35 > self.ema_40 > self.ema_45 > self.ema_50 > self.ema_55
        # self.bearish = self.ema_20 < self.ema_55 #< self.ema_30 < self.ema_35 < self.ema_40 < self.ema_45 < self.ema_50 < self.ema_55
        #
        self.ATR = bt.ind.AverageTrueRange(period=5)
        self.lowestATR = bt.ind.Lowest(self.ATR, period=360)
        self.highestATR = bt.ind.Highest(self.ATR, period=360)

        self.HA_30min = bt.ind.HeikinAshi(self.data)
        self.HA_hour = bt.ind.HeikinAshi(self.data1)

        self.sma_8 = bt.ind.SMA(self.HA_30min.ha_close(), period=21)
        self.ema_8 = bt.ind.EMA(self.sma_8, period=21)
        self.crossdown = bt.ind.CrossDown(self.sma_8, self.ema_8)
        self.crossup = bt.ind.CrossUp(self.sma_8, self.ema_8)

    def next(self):
        '''比例'''
        self.ATRratio = 1 - (self.ATR - self.lowestATR) / (self.highestATR - self.lowestATR)
        self.val_start = self.broker.get_cash()  # 檢查餘額
        '''ATR用了獲利爆幹爛'''
        self.size = (self.broker.getvalue() * 0.9) / self.data.close[0]  # 100趴錢買
        if self.crossup and not self.crossdown:

            # self.order_target_percent(target=0.9, exectype=bt.Order.Market)
            tsize = self.size + abs(self.position.size)
            self.buy(size=tsize, exectype=bt.Order.Limit, price=self.data.low[0])

        if self.crossdown and not self.crossup:

            # self.order_target_percent(target=-0.9, exectype=bt.Order.Market)
            tsize = self.size + abs(self.position.size)
            self.sell(size=-tsize, exectype=bt.Order.Limit, price=self.data.high[0])


class ATR_tracking(bt.Strategy):  # 垃圾

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        # 有交易提交/被接受，啥也不做
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 交易完成，报告结果
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("成功買入")
                self.log(order.executed.price)
                self.comm += order.executed.comm
            else:
                self.log("成功賣出")
                self.log(order.executed.price)
                self.comm += order.executed.comm
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("交易失敗")
        self.order = None

    def __init__(self):
        self.delay = False

        self.comm = 0
        self.golong = False
        self.goshort = False
        self.isbuying = False
        self.isselling = False
        self.condition_l = False
        self.condition_s = False
        self.green = set()
        self.red = set()
        # WT
        self.hlc3 = (self.data.close + self.data.high + self.data.low) / 3
        self.n1 = 10
        self.n2 = 21
        self.esa = bt.ind.EMA(self.hlc3, period=self.n1, plot=False)
        self.d = bt.ind.EMA(abs(self.hlc3 - self.esa), period=self.n1, plot=False)
        self.ci = (self.hlc3 - self.esa) / (0.015 * self.d)
        self.WT1 = bt.ind.EMA(self.ci, period=self.n2, plot=False)
        self.WT2 = bt.ind.SMA(self.WT1, period=4, plot=False)
        self.WTMTM = self.WT1 - self.WT2

        self.WTcrossdown = bt.ind.CrossDown(self.WT1, self.WT2)
        self.WTcrossup = bt.ind.CrossUp(self.WT1, self.WT2)

        self.ema_200 = bt.ind.SMA(period=200)

        self.supertrend_s = SuperTrend(multiplier=1, period=10)
        self.supertrend_m = SuperTrend(multiplier=2, period=11)
        self.supertrend_l = SuperTrend(multiplier=3, period=12)

        self.long_condition = False
        self.short_condition = False
        # self.ATRtracking_s = 0
        # self.ATRtracking_m = 0
        # self.ATRtracking_l = 0
        # self.lastATRtracking_s = 0
        # self.lastATRtracking_m = 0
        # self.lastATRtracking_l = 0
        # self.lowestATR = bt.ind.Lowest(self.ATR, period = 360)
        # self.highestATR = bt.ind.Highest(self.ATR, period = 360)
        # self.HA_30min = bt.ind.HeikinAshi(self.data)

    def green_color_count(self):
        temp = [self.supertrend_s[0], self.supertrend_m[0], self.supertrend_l[0]]
        return len([True for x in temp if x < self.data.close[0]])

    def vali(self):
        temp_list = self.WTMTM.get(size=40)
        if self.WTMTM[0] < 0:
            temp_list.pop()
            while temp_list[-1] < 0:
                if temp_list.pop() < -15:
                    return True
                    break
        elif self.WTMTM[0] < 0:
            temp_list.pop()
            while temp_list[-1] > 0:
                if temp_list.pop() > 15:
                    return True
                    break
        return False

    def next(self):
        '''下面是在改三組ATRTracking方向 +-'''
        close = self.data.close[0]
        # print('time : ',self.data.datetime.datetime(),',clsoe : ',self.data.close[0])
        # print(self.supertrend_s[0], self.supertrend_m[0], self.supertrend_l[0])
        if self.WTcrossup and self.WT1[0] < 0:
            self.long_condition = True
            self.short_condition = False
        if self.WTcrossdown and self.WT1[0] > 0:
            self.short_condition = True
            self.long_condition = False

        if self.green_color_count() >= 2 and self.long_condition and not self.position:
            if close > self.ema_200[0]:
                self.buy()
                '''golong'''
        if self.green_color_count() <= 1 and self.short_condition and not self.position:
            if close < self.ema_200[0]:
                self.sell()
                '''goshort'''

        if self.position.size > 0:
            if self.green_color_count() <= 1:
                self.close()
        elif self.position.size < 0:
            if self.green_color_count() >= 2:
                self.close()

        '''比例'''
        # self.ATRratio = 1 - ( self.ATR - self.lowestATR ) / ( self.highestATR - self.lowestATR )
        self.val_start = self.broker.get_cash()  # 檢查餘額
        '''ATR用了獲利爆幹爛，故先用0.9，槓改最高開1.68'''
        self.size = (self.broker.getvalue() * 0.9) / self.data.close[0]  # 100趴錢買


class up70gg(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        # 有交易提交/被接受，啥也不做
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 交易完成，报告结果
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("成功買入")
                self.log(order.executed.price)
                self.comm += order.executed.comm
            else:
                self.log("成功賣出")
                self.log(order.executed.price)
                self.comm += order.executed.comm
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("交易失敗")
        self.order = None

    def __init__(self):
        self.delay = False

        self.comm = 0
        self.golong = False
        self.goshort = False
        self.isbuying = False
        self.isselling = False
        self.longorder = None

        self.ATR = bt.ind.AverageTrueRange(period=100)
        self.nLoss = self.ATR * 0.5
        self.ATRtracking = 0
        self.lastATRtracking = 0
        self.lowestATR = bt.ind.Lowest(self.ATR, period=360)
        self.highestATR = bt.ind.Highest(self.ATR, period=360)
        self.HA_30min = bt.ind.HeikinAshi(self.data)
        # BB%B
        self.basis = bt.ind.SMA(self.data1.close, period=20)
        self.dev = 2.0 * bt.ind.StandardDeviation(self.data1.close, period=20)
        self.upper = self.basis + self.dev
        self.lower = self.basis - self.dev
        self.bbr = (self.data1.close - self.lower) / (self.upper - self.data1.close)
        # AO
        self.ao = bt.ind.SMA((self.data1.high + self.data1.low) / 2, period=5) - \
            bt.ind.SMA((self.data1.high + self.data1.low) / 2, period=34)
        # ADX
        self.adx = bt.ind.AverageDirectionalMovementIndex()
        # 看看最近的低點
        self.lowerpoint = bt.ind.Lowest(self.data1.close, period=10)
        self.profit = 0
        # EMA
        self.ema5 = bt.ind.EMA(self.data1.close, period=5)
        self.ema21 = bt.ind.EMA(self.data1.close, period=21)
        self.ema50 = bt.ind.EMA(self.data1.close, period=50)
        self.ema100 = bt.ind.EMA(self.data1.close, period=100)
        self.emacondition1 = self.ema5 > self.ema21
        self.emacondition2 = self.ema50 > self.ema100
        self.emacondition3 = self.ema5 < self.ema21
        self.emacondition4 = self.ema50 < self.ema100

        self.crossdown = bt.ind.CrossDown(self.ema5, self.ema21)
        self.crossup = bt.ind.CrossUp(self.ema5, self.ema21)
        self.c8 = False
        self.sc8 = False

    def next(self):
        '''下面是在改ATRTracking方向 +-'''

        # and self.data.close.get(ago=-1)[0] > self.lastATRtracking
        if self.data.close[0] > self.ATRtracking:
            if self.data.close.get(ago=-1)[0] < self.lastATRtracking:
                '''剛好換邊'''
                self.ATRtracking = self.data.close[0] - self.nLoss
            else:
                '''正常'''
                self.ATRtracking = max(self.data.close[0] - self.nLoss, self.lastATRtracking)
        # and self.data.close.get(ago=-1)[0] < self.lastATRtracking
        if self.data.close[0] < self.ATRtracking:
            if self.data.close.get(ago=-1)[0] > self.lastATRtracking:
                '''剛好換邊'''
                self.ATRtracking = self.data.close[0] + self.nLoss
            else:
                '''正常'''
                self.ATRtracking = min(self.data.close[0] + self.nLoss, self.lastATRtracking)

        '''比例'''
        self.ATRratio = 1 - (self.ATR - self.lowestATR) / (self.highestATR - self.lowestATR)
        self.val_start = self.broker.get_cash()  # 檢查餘額
        '''ATR用了獲利爆幹爛，故先用0.9，槓改最高開1.68'''
        self.size = (self.broker.getvalue() * 0.1) / self.data.close[0]  # 100趴錢買

        self.c8 = any(self.crossup.get(size=10)) > 0  # 近5根有交叉 #Y
        self.sc8 = any(self.crossdown.get(size=10)) > 0  # 近5根有交叉 #Y
        # print('此時的ATR : ', self.ATRtracking,',time : ',self.data.datetime.datetime(),',clsoe : ',self.data.close[0])
        # print('此時的BBR,AO,ADX', (self.bbr[0],self.ao[0],self.adx[0]))
        if self.val_start > 100000:

            if self.bbr[0] > 0.75 and self.ao[0] > 2 and self.adx[0] > 15 and self.emacondition1 and self.emacondition2 and not self.isbuying and self.c8:
                self.profit = abs(self.data1.close[0] - self.lowerpoint[0])
                self.cancel(self.longorder)
                print('===')
                print('此時的BBR,AO,ADX', (self.bbr[0], self.ao[0], self.adx[0]))
                self.isbuying = True
                self.isselling = False
                # self.order_target_percent(target=0.9, exectype=bt.Order.Market)
                tsize = self.size  # + abs(self.position.size)
                print('stop and limit', (self.profit, self.data1.close[0] + self.profit))
                self.mainside = self.buy(
                    price=self.data1.close[0], exectype=bt.Order.Limit, transmit=False)
                lowside = self.sell(price=self.data1.close[0] - self.profit, size=self.mainside.size, exectype=bt.Order.Stop,
                                    transmit=False, parent=self.mainside)
                highside = self.sell(trailamount=self.profit * 0.5, size=self.mainside.size, exectype=bt.Order.StopTrail,
                                     transmit=True, parent=self.mainside)
            # self.buy(size= tsize, exectype=bt.Order.Market)

            if self.bbr[0] < 0.25 and self.ao[0] < -2 and self.adx[0] > 15 and self.emacondition3 and self.emacondition4 and not self.isselling:
                print('此時的BBR,AO,ADX', (self.bbr[0], self.ao[0], self.adx[0]))
                self.isbuying = False
                self.isselling = True

                # tsize = self.size# + abs(self.position.size)
                # print('stop and limit',(self.profit, self.data.close[0] + self.profit))
                # self.mainside = self.sell(price=self.data.close[0], exectype=bt.Order.Limit, transmit=False)
                # lowside  = self.buy(price=self.data.close[0] + self.profit, size=self.mainside.size, exectype=bt.Order.Stop,
                #                      transmit=False, parent=self.mainside)
                # highside = self.buy(trailamount=self.profit * 2, size=self.mainside.size, exectype=bt.Order.StopTrail,
                #                      transmit=True, parent=self.mainside)

        self.lastATRtracking = self.ATRtracking  # 垃圾


class DaulMA_ATR_tracking(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.mouthly_count = self.broker.getvalue()/10000.0

    ''''''
    # def notify_order(self, order):
    #     # 有交易提交/被接受，啥也不做
    #     if order.status in [order.Submitted, order.Accepted]:
    #         return
    #     # 交易完成，报告结果
    #     if order.status in [order.Completed]:
    #         if order.isbuy():
    #             self.log("成功買入")
    #             self.log(order.executed.price)
    #             self.comm += order.executed.comm
    #         else:
    #             self.log("成功賣出")
    #             self.log(order.executed.price)
    #             self.comm += order.executed.comm
    #     elif order.status in [order.Canceled, order.Margin, order.Rejected]:
    #         self.log("交易失敗")
    #     self.order = None

    def __init__(self):
        # self.leverage = self.broker.getcommissioninfo(self.data).get_leverage()
        self.leverage = 0.3
        self.run = 4
        print(self.leverage)
        self.initclose = False
        self.delay = False
        self.greedy = True
        self.greedyH = bt.ind.Highest(self.data.high, period=3)
        self.greedyL = bt.ind.Lowest(self.data.low, period=3)
        '''添加'''
        self.order = None
        self.takeprofitorder = None
        self.comm = 0
        self.golong = False
        self.goshort = False
        self.isbuying = False
        self.isselling = False
        self.trendup = False
        self.trenddown = False
        self.takeprofit = None
        self.mainside = False
        self.lowside = False
        '''plus'''
        # WT
        self.hlc3 = (self.data.close + self.data.high + self.data.low) / 3
        self.n1 = 10
        self.n2 = 21
        self.esa = bt.ind.EMA(self.hlc3, period=self.n1, plot=False)
        self.d = bt.ind.EMA(abs(self.hlc3 - self.esa), period=self.n1, plot=False)
        self.ci = (self.hlc3 - self.esa) / (0.015 * self.d)
        self.WT1 = bt.ind.EMA(self.ci, period=self.n2, plot=False)
        self.WT2 = bt.ind.SMA(self.WT1, period=4, plot=False)
        self.WTMTM = self.WT1 - self.WT2

        self.WTcrossdown = bt.ind.CrossDown(self.WT1, self.WT2)
        self.WTcrossup = bt.ind.CrossUp(self.WT1, self.WT2)
        # Higest Lowest
        self.highestWT = bt.ind.Highest(self.WT1, period=35)
        self.lowestWT = bt.ind.Lowest(self.WT1, period=35)
        '''plus'''
        self.ATR = bt.ind.AverageTrueRange(period=100)
        self.nLoss = self.ATR * 0.5
        self.ATRtracking = 0
        self.lastATRtracking = 0
        self.lowestATR = bt.ind.Lowest(self.ATR, period=360)
        self.highestATR = bt.ind.Highest(self.ATR, period=360)

        self.HA_30min = bt.ind.HeikinAshi(self.data)
        '''DaulMA'''
        self.sma_8 = bt.ind.SMA(self.HA_30min.ha_close(), period=21)
        self.ema_8 = bt.ind.EMA(self.sma_8, period=21)
        self.crossdown = bt.ind.CrossDown(self.sma_8, self.ema_8)
        self.crossup = bt.ind.CrossUp(self.sma_8, self.ema_8)

    def vali(self):
        temp_list = self.WTMTM.get(size=40)
        if self.WTMTM[0] < 0:
            temp_list.pop()
            while temp_list[-1] < 0:
                if temp_list.pop() < -15:
                    return True
                    break
        elif self.WTMTM[0] > 0:
            temp_list.pop()
            while temp_list[-1] > 0:
                if temp_list.pop() > 15:
                    return True
                    break
        return False

    def next(self):
        date = self.datetime.datetime()
        if date.day == 1 and date.hour == 0 and date.minute == 0:
            print('=' * 30, '月總結 : ', self.mouthly_count, '=' * 30)
        close = self.data.close[0]
        if not self.initclose:
            self.initclose = self.data.close[0]
        '''下面是在改ATRTracking方向 +-'''
        if self.data.close[0] > self.ATRtracking:  # and self.data.close.get(ago=-1)[0] > self.lastATRtracking
            if self.data.close.get(ago=-1)[0] < self.lastATRtracking:
                '''剛好換邊'''
                self.ATRtracking = self.data.close[0] - self.nLoss
                self.isselling = False
            else:
                '''正常'''
                self.ATRtracking = max(self.data.close[0] - self.nLoss, self.lastATRtracking)
        # and self.data.close.get(ago=-1)[0] < self.lastATRtracking
        if self.data.close[0] < self.ATRtracking:
            if self.data.close.get(ago=-1)[0] > self.lastATRtracking:
                '''剛好換邊'''
                self.ATRtracking = self.data.close[0] + self.nLoss
                self.isbuying = False
            else:
                '''正常'''
                self.ATRtracking = min(self.data.close[0] + self.nLoss, self.lastATRtracking)

        '''比例'''
        self.ATRratio = 1 - (self.ATR - self.lowestATR) / (self.highestATR - self.lowestATR)
        self.val_start = self.broker.get_cash()  # 檢查餘額

        '''ATR用了獲利爆幹爛，故先用0.9，槓改最高開1.68 當勝率>40趴'''
        self.size = (self.broker.getvalue() * 0.9) / self.data.close[0] * self.leverage  # 100趴錢買

        if self.data.close[0] < self.ATRtracking and self.position.size > 0 and not self.isbuying:
            self.trendup = True
            self.trenddown = False
            self.isbuying = True
            self.isselling = False
        if self.data.close[0] > self.ATRtracking and self.position.size < 0 and not self.isselling:
            self.trendup = False
            self.trenddown = True
            self.isbuying = False
            self.isselling = True

        '''偷跑系統'''
        if self.position.size != 0:
            if self.position.size > 0 and self.data.close[0] > self.takeprofit and self.trendup:
                self.cancel(self.takeprofitorder)
                if self.greedy:
                    self.takeprofitorder = self.sell(
                        size=-self.position.size/self.run, exectype=bt.Order.Limit, price=self.data.high[0])
                else:
                    self.takeprofitorder = self.sell(
                        size=-self.position.size/self.run, exectype=bt.Order.Market)
                gap = abs(self.data.close[0] - self.sma_8[0])
                self.takeprofit = self.data.close[0] + gap
                self.trendup = False
            if self.position.size < 0 and self.data.close[0] < self.takeprofit and self.trenddown:
                self.cancel(self.takeprofitorder)
                if self.greedy:
                    self.takeprofitorder = self.buy(
                        size=self.position.size/self.run, exectype=bt.Order.Limit, price=self.data.low[0])
                else:
                    self.takeprofitorder = self.buy(
                        size=self.position.size/self.run, exectype=bt.Order.Market)
                gap = abs(self.data.close[0] - self.sma_8[0])
                self.takeprofit = self.data.close[0] + gap
                self.trenddown = False

        '''DaulMA系統'''
        if self.crossup and not self.crossdown:

            # if self.vali():
            self.cancel(self.takeprofitorder)
            # self.cancel(self.order)
            # self.cancel(self.lowside)
            # if self.vali():
            gap = abs(self.data.close[0] - self.sma_8[0])
            self.takeprofit = self.data.close[0] + gap
            # self.order_target_percent(target=0.9, exectype=bt.Order.Market)
            tsize = self.size + abs(self.position.size)
            if self.greedy:
                self.buy(size=(abs(self.position.size) + self.size / 2), exectype=bt.Order.Market)
                self.order = self.buy(size=(self.size / 2),
                                      exectype=bt.Order.Limit, price=self.data.low[0])
                # self.lowside = self.sell(size=self.order.size, exectype=bt.Order.StopTrail, price=self.data.close[0], trailamount=gap)
            else:
                self.buy(size=tsize, exectype=bt.Order.Market)

        if self.crossdown and not self.crossup:
            # if self.vali():
            self.cancel(self.takeprofitorder)
            # self.cancel(self.order)
            # self.cancel(self.lowside)
            # if self.vali():
            gap = abs(self.data.close[0] - self.sma_8[0])
            self.takeprofit = self.data.close[0] - gap
            # self.order_target_percent(target=-0.9, exectype=bt.Order.Market)
            tsize = self.size + abs(self.position.size)
            if self.greedy:
                self.sell(size=(abs(self.position.size) + self.size / 2), exectype=bt.Order.Market)
                self.order = self.sell(size=(self.size / 2),
                                       exectype=bt.Order.Limit, price=self.data.high[0])
                # self.lowside = self.buy(size=self.order.size, exectype=bt.Order.StopTrail, price=self.data.close[0], trailamount=gap)
            else:
                self.sell(size=tsize, exectype=bt.Order.Market)
        # print('if I hold', self.data.close[0] / self.initclose * 1000000.0)

        '''Wtsystem'''
        '''
        last_3_candles_h = self.WT1.get(ago = -1)[0] == self.highestWT[0] or self.WT1.get(
            ago = -2)[0] == self.highestWT[0] or self.WT1.get(ago = -3)[0] == self.highestWT[0]
        last_3_candles_l = self.WT1.get(ago = -1)[0] == self.lowestWT[0] or self.WT1.get(
            ago = -2)[0] == self.lowestWT[0] or self.WT1.get(ago = -3)[0] == self.lowestWT[0]

        if self.WTcrossup and last_3_candles_l and self.WT1[0] < -30: #and self.WT1[0] < -30
            print('-'*15)
            print('now time for buy: ',self.datetime.datetime(ago=0))
            print('-'*15)
            if self.position.size < 0:
                self.cancel(self.lowside)
                self.close()
            if self.vali():
                gap = abs(self.data.close[0] - self.sma_8[0])
                print(self.data.low[0] - gap)
                self.mainside = self.buy(size = 10)
                self.lowside = self.sell(
                    size=self.mainside.size, exectype=bt.Order.StopTrail, price=self.data.close[0], trailamount=gap)

        if self.WTcrossdown and last_3_candles_h and self.WT1[0] > 30: #and self.WT1[0] > 30
            print('-'*15)
            print('now time for sell: ',self.datetime.datetime(ago=0))
            print('-'*15)
            if self.position.size > 0:
                self.cancel(self.lowside)
                self.close()
            if self.vali():

                gap = abs(self.data.close[0] - self.sma_8[0])
                print(self.data.low[0] + gap)
                self.mainside = self.sell(size = 10)
                self.lowside = self.buy(
                    size=self.mainside.size, exectype=bt.Order.StopTrail, price=self.data.close[0], trailamount=gap)
        '''

        self.lastATRtracking = self.ATRtracking


class Supertrend_WT(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0)
        print('%s, %s' % (dt.isoformat(), txt))

    # def notify_trade(self, trade):
    #     if not trade.isclosed:
    #         return
    #     self.log('%.2f 趴, %.2f 趴' %(trade.pnl/self.broker.getvalue() * 100, self.broker.getvalue()/10000.0))

    ''''''

    def notify_order(self, order):
        # 有交易提交/被接受，啥也不做
        if order.status in [order.Submitted, order.Accepted]:
            return
        # 交易完成，报告结果
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("成功買入")
                self.log(order.executed.price)
                self.comm += order.executed.comm
            else:
                self.log("成功賣出")
                self.log(order.executed.price)
                self.comm += order.executed.comm
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("交易失敗")
        self.order = None

    def __init__(self):
        self.leverage = self.broker.getcommissioninfo(self.data).get_leverage()
        self.run = 4
        print(self.leverage)
        self.initclose = False
        self.delay = False
        self.greedy = True
        self.greedyH = bt.ind.Highest(self.data.high, period=3)
        self.greedyL = bt.ind.Lowest(self.data.low, period=3)
        '''添加'''
        self.order = None
        self.takeprofitorder = None
        self.comm = 0
        self.golong = False
        self.goshort = False
        self.isbuying = False
        self.isselling = False
        self.trendup = False
        self.trenddown = False
        self.takeprofit = None
        self.mainside = False
        self.lowside = False
        '''plus'''
        # WT
        self.hlc3 = (self.data.close + self.data.high + self.data.low) / 3
        self.n1 = 10
        self.n2 = 21
        self.esa = bt.ind.EMA(self.hlc3, period=self.n1, plot=False)
        self.d = bt.ind.EMA(abs(self.hlc3 - self.esa), period=self.n1, plot=False)
        self.ci = (self.hlc3 - self.esa) / (0.015 * self.d)
        self.WT1 = bt.ind.EMA(self.ci, period=self.n2, plot=False)
        self.WT2 = bt.ind.SMA(self.WT1, period=4, plot=False)
        self.WTMTM = self.WT1 - self.WT2

        self.WTcrossdown = bt.ind.CrossDown(self.WT1, self.WT2)
        self.WTcrossup = bt.ind.CrossUp(self.WT1, self.WT2)
        # Higest Lowest
        self.highestWT = bt.ind.Highest(self.WT1, period=35)
        self.lowestWT = bt.ind.Lowest(self.WT1, period=35)
        '''plus'''
        self.ATR = bt.ind.AverageTrueRange(period=100)
        self.nLoss = self.ATR * 0.5
        self.ATRtracking = 0
        self.lastATRtracking = 0
        self.lowestATR = bt.ind.Lowest(self.ATR, period=360)
        self.highestATR = bt.ind.Highest(self.ATR, period=360)

        self.HA_30min = bt.ind.HeikinAshi(self.data)
        '''DaulMA'''
        self.sma_8 = bt.ind.SMA(self.HA_30min.ha_close(), period=21)
        self.ema_8 = bt.ind.EMA(self.sma_8, period=21)
        self.crossdown = bt.ind.CrossDown(self.sma_8, self.ema_8)
        self.crossup = bt.ind.CrossUp(self.sma_8, self.ema_8)

    def vali(self):
        temp_list = self.WTMTM.get(size=40)
        if self.WTMTM[0] < 0:
            temp_list.pop()
            while temp_list[-1] < 0:
                if temp_list.pop() < -15:
                    return True
                    break
        elif self.WTMTM[0] > 0:
            temp_list.pop()
            while temp_list[-1] > 0:
                if temp_list.pop() > 15:
                    return True
                    break
        return False

    def next(self):
        if not self.initclose:
            self.initclose = self.data.close[0]
        '''下面是在改ATRTracking方向 +-'''
        if self.data.close[0] > self.ATRtracking:  # and self.data.close.get(ago=-1)[0] > self.lastATRtracking
            if self.data.close.get(ago=-1)[0] < self.lastATRtracking:
                '''剛好換邊'''
                self.ATRtracking = self.data.close[0] - self.nLoss
                self.isselling = False
            else:
                '''正常'''
                self.ATRtracking = max(self.data.close[0] - self.nLoss, self.lastATRtracking)
        # and self.data.close.get(ago=-1)[0] < self.lastATRtracking
        if self.data.close[0] < self.ATRtracking:
            if self.data.close.get(ago=-1)[0] > self.lastATRtracking:
                '''剛好換邊'''
                self.ATRtracking = self.data.close[0] + self.nLoss
                self.isbuying = False
            else:
                '''正常'''
                self.ATRtracking = min(self.data.close[0] + self.nLoss, self.lastATRtracking)

        '''比例'''
        self.ATRratio = 1 - (self.ATR - self.lowestATR) / (self.highestATR - self.lowestATR)
        self.val_start = self.broker.get_cash()  # 檢查餘額

        '''ATR用了獲利爆幹爛，故先用0.9，槓改最高開1.68 當勝率>40趴'''
        self.size = (self.broker.getvalue() * 0.9) / self.data.close[0] * self.leverage  # 100趴錢買

        if self.data.close[0] < self.ATRtracking and self.position.size > 0 and not self.isbuying:
            self.trendup = True
            self.trenddown = False
            self.isbuying = True
            self.isselling = False
        if self.data.close[0] > self.ATRtracking and self.position.size < 0 and not self.isselling:
            self.trendup = False
            self.trenddown = True
            self.isbuying = False
            self.isselling = True

        '''偷跑系統'''
        if self.position.size != 0:
            if self.position.size > 0 and self.data.close[0] > self.takeprofit and self.trendup:
                self.cancel(self.takeprofitorder)
                if self.greedy:
                    self.takeprofitorder = self.sell(
                        size=-self.position.size/self.run, exectype=bt.Order.Limit, price=self.data.high[0])
                else:
                    self.takeprofitorder = self.sell(
                        size=-self.position.size/self.run, exectype=bt.Order.Market)
                gap = abs(self.data.close[0] - self.sma_8[0])
                self.takeprofit = self.data.close[0] + gap
                self.trendup = False
            if self.position.size < 0 and self.data.close[0] < self.takeprofit and self.trenddown:
                self.cancel(self.takeprofitorder)
                if self.greedy:
                    self.takeprofitorder = self.buy(
                        size=self.position.size/self.run, exectype=bt.Order.Limit, price=self.data.low[0])
                else:
                    self.takeprofitorder = self.buy(
                        size=self.position.size/self.run, exectype=bt.Order.Market)
                gap = abs(self.data.close[0] - self.sma_8[0])
                self.takeprofit = self.data.close[0] + gap
                self.trenddown = False

        '''DaulMA系統'''
        if self.crossup and not self.crossdown:

            # if self.vali():
            self.cancel(self.takeprofitorder)
            # self.cancel(self.order)
            # self.cancel(self.lowside)
            # if self.vali():
            gap = abs(self.data.close[0] - self.sma_8[0])
            self.takeprofit = self.data.close[0] + gap
            # self.order_target_percent(target=0.9, exectype=bt.Order.Market)
            tsize = self.size + abs(self.position.size)
            if self.greedy:
                self.buy(size=(abs(self.position.size) + self.size / 2), exectype=bt.Order.Market)
                self.order = self.buy(size=(self.size / 2),
                                      exectype=bt.Order.Limit, price=self.data.low[0])
                # self.lowside = self.sell(size=self.order.size, exectype=bt.Order.StopTrail, price=self.data.close[0], trailamount=gap)
            else:
                self.buy(size=tsize, exectype=bt.Order.Market)

        if self.crossdown and not self.crossup:
            # if self.vali():
            self.cancel(self.takeprofitorder)
            # self.cancel(self.order)
            # self.cancel(self.lowside)
            # if self.vali():
            gap = abs(self.data.close[0] - self.sma_8[0])
            self.takeprofit = self.data.close[0] - gap
            # self.order_target_percent(target=-0.9, exectype=bt.Order.Market)
            tsize = self.size + abs(self.position.size)
            if self.greedy:
                self.sell(size=(abs(self.position.size) + self.size / 2), exectype=bt.Order.Market)
                self.order = self.sell(size=(self.size / 2),
                                       exectype=bt.Order.Limit, price=self.data.high[0])
                # self.lowside = self.buy(size=self.order.size, exectype=bt.Order.StopTrail, price=self.data.close[0], trailamount=gap)
            else:
                self.sell(size=tsize, exectype=bt.Order.Market)
        # print('if I hold', self.data.close[0] / self.initclose * 1000000.0)

        '''Wtsystem'''
        '''
        last_3_candles_h = self.WT1.get(ago = -1)[0] == self.highestWT[0] or self.WT1.get(
            ago = -2)[0] == self.highestWT[0] or self.WT1.get(ago = -3)[0] == self.highestWT[0]
        last_3_candles_l = self.WT1.get(ago = -1)[0] == self.lowestWT[0] or self.WT1.get(
            ago = -2)[0] == self.lowestWT[0] or self.WT1.get(ago = -3)[0] == self.lowestWT[0]

        if self.WTcrossup and last_3_candles_l and self.WT1[0] < -30: #and self.WT1[0] < -30
            print('-'*15)
            print('now time for buy: ',self.datetime.datetime(ago=0))
            print('-'*15)
            if self.position.size < 0:
                self.cancel(self.lowside)
                self.close()
            if self.vali():
                gap = abs(self.data.close[0] - self.sma_8[0])
                print(self.data.low[0] - gap)
                self.mainside = self.buy(size = 10)
                self.lowside = self.sell(
                    size=self.mainside.size, exectype=bt.Order.StopTrail, price=self.data.close[0], trailamount=gap)

        if self.WTcrossdown and last_3_candles_h and self.WT1[0] > 30: #and self.WT1[0] > 30
            print('-'*15)
            print('now time for sell: ',self.datetime.datetime(ago=0))
            print('-'*15)
            if self.position.size > 0:
                self.cancel(self.lowside)
                self.close()
            if self.vali():

                gap = abs(self.data.close[0] - self.sma_8[0])
                print(self.data.low[0] + gap)
                self.mainside = self.sell(size = 10)
                self.lowside = self.buy(
                    size=self.mainside.size, exectype=bt.Order.StopTrail, price=self.data.close[0], trailamount=gap)
        '''

        self.lastATRtracking = self.ATRtracking


class trade_pro(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0)
        print('%s, %s' % (dt.isoformat(), txt))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.mouthly_count = self.broker.getvalue()/10000.0
        # self.log('%.2f 趴, %.2f 趴' % (trade.pnl/self.broker.getvalue()
        #          * 100, self.mouthly_count))

    ''''''

    # def notify_order(self, order):
    #     # 有交易提交/被接受，啥也不做
    #     if order.status in [order.Submitted, order.Accepted]:
    #         return
    #     # 交易完成，报告结果
    #     if order.status in [order.Completed]:
    #         if order.isbuy():
    #             self.log("成功買入")
    #             self.log(order.executed.price)
    #             self.comm += order.executed.comm
    #         else:
    #             self.log("成功賣出")
    #             self.log(order.executed.price)
    #             self.comm += order.executed.comm
    #     elif order.status in [order.Canceled, order.Margin, order.Rejected]:
    #         self.log("交易失敗")
    #     self.order = None

    def __init__(self):
        self.comm = 0
        self.mainside = None
        self.leverage = self.broker.getcommissioninfo(self.data).get_leverage()
        self.mouthly_count = 1.0
        self.brackets_long = None
        self.brackets_short = None
        '''EMAs'''
        self.ema_s = bt.ind.EMA(period=7)
        self.ema_m = bt.ind.EMA(period=13)
        self.ema_l = bt.ind.EMA(period=400)

        '''plus'''
        self.ATR = bt.ind.AverageTrueRange(period=16)
        # self.nLoss = self.ATR * 0.5
        '''
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
        '''
        '''trade pro'''
        self.rsi_filter = bt.ind.RSI_Safe(period=1)
        self.s3 = StochasticRSI(k_period=3, d_period=3, rsi_period=15, stoch_period=15)
        self.crossup = bt.ind.CrossUp(self.s3.l.fastk, self.s3.l.fastd)
        self.crossdown = bt.ind.CrossDown(self.s3.l.fastk, self.s3.l.fastd)

    def next(self):
        date = self.datetime.datetime()
        if date.day == 1 and date.hour == 0 and date.minute == 0:
            print('=' * 30, '月總結 : ', self.mouthly_count, '=' * 30)
        close = self.data.close[0]
        # print(self.position.size, self.s3.l.fastk[0])
        if not self.position:
            if close > self.ema_s[0] > self.ema_m[0] > self.ema_l[0] and (self.crossup and self.rsi_filter < 50):
                if self.mainside:
                    self.close()
                    self.cancel(self.mainside)
                self.mainside = self.buy(transmit=False)
                lowside = self.sell(
                    price=close - 3 * self.ATR[0], size=self.mainside.size, exectype=bt.Order.Stop, transmit=False, parent=self.mainside)
                highside = self.sell(
                    price=close + 2 * self.ATR[0], size=self.mainside.size, exectype=bt.Order.Limit, transmit=True, parent=self.mainside)
                # trailside = self.sell(size=self.mainside.size, exectype=bt.Order.StopTrail, trailamount=100, transmit=True, parent=self.mainside)
            if close < self.ema_s[0] < self.ema_m[0] < self.ema_l[0] and (self.crossdown and self.rsi_filter > 50):
                if self.mainside:
                    self.close()
                    self.cancel(self.mainside)
                self.mainside = self.sell(transmit=False)
                lowside = self.buy(
                    price=close + 3 * self.ATR[0], size=self.mainside.size, exectype=bt.Order.Stop, transmit=False, parent=self.mainside)
                highside = self.buy(
                    price=close - 2 * self.ATR[0], size=self.mainside.size, exectype=bt.Order.Limit, transmit=True, parent=self.mainside)
                # trailside = self.buy(size=self.mainside.size, exectype=bt.Order.StopTrail, trailamount=100, transmit=True, parent=self.mainside)


class trade_pro_ETH(bt.Strategy):
    ''' parameter for turning'''
    params = (
        ('sma_slow', 7),
        ('sma_mid', 8),
        ('sma_fast', 550),
        ('atr', 5),
        ('lowside', 3.4),
        ('highside', 2.1),
        ('rsi_filter', 1),
        ('k_period', 3),
        ('d_period', 3),
        ('rsi_period', 11),
        ('stoch_period', 15),
        ('sma_filter', 1600),

    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0) + datetime.timedelta(minutes=15)
        print('%s, %s' % (dt.isoformat(), txt))

    # def notify_trade(self, trade):
    #     if not trade.isclosed:
    #         return
    #     self.mouthly_count = self.broker.getvalue()/10000.0
        # self.log('%.2f 趴, %.2f 趴' % (trade.pnl/self.broker.getvalue()
        #          * 100, self.mouthly_count))

    ''''''

    def __init__(self):
        self.comm = 0
        self.mainside = None
        self.leverage = self.broker.getcommissioninfo(self.data).get_leverage()
        self.mouthly_count = 1.0
        self.brackets_long = None
        self.brackets_short = None
        '''EMAs'''
        self.ema_s = bt.ind.EMA(period=self.params.sma_slow)
        self.ema_m = bt.ind.EMA(period=self.params.sma_mid)
        self.ema_l = bt.ind.EMA(period=self.params.sma_fast)

        '''plus'''
        self.ATR = bt.ind.AverageTrueRange(period=self.params.atr)
        self.lowside = self.params.lowside
        self.highside = self.params.highside
        # self.nLoss = self.ATR * 0.5
        '''
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
        '''
        '''trade pro'''
        self.rsi_filter = bt.ind.RSI_Safe(period=self.params.rsi_filter)
        self.s3 = StochasticRSI(k_period=self.params.k_period, d_period=self.params.d_period,
                                rsi_period=self.params.rsi_period, stoch_period=self.params.stoch_period)
        self.crossup = bt.ind.CrossUp(self.s3.l.fastk, self.s3.l.fastd)
        self.crossdown = bt.ind.CrossDown(self.s3.l.fastk, self.s3.l.fastd)
        '''if cross ma'''
        self.ma = bt.ind.SMA(period=self.params.sma_filter)

    def next(self):
        # date = self.datetime.datetime()
        # print(date, 'crossup : ', self.crossup[0], 'crossdown : ', self.crossdown[0], 'rsi_filter : ',
        #       self.rsi_filter[0], 'ema_s : ', self.ema_s[0], 'ema_m : ', self.ema_m[0], 'ema_l : ', self.ema_l[0], 'k : ', self.s3.l.fastk[0], 'd : ', self.s3.l.fastd[0])
        # if date.day == 1 and date.hour == 0 and date.minute == 0:
        #     print('date : ', date, '=' * 30, '月總結 : ', self.mouthly_count, '=' * 30)
        close = self.data.close[0]
        # print(self.position.size, self.s3.l.fastk[0])
        if not self.position:
            if close > self.ema_s[0] > self.ema_m[0] > self.ema_l[0] and (self.crossup and self.rsi_filter < 50):
                if self.mainside:
                    self.close()
                    self.cancel(self.mainside)
                self.mainside = self.buy(transmit=False)
                lowside = self.sell(
                    price=close - self.lowside * self.ATR[0], size=self.mainside.size, exectype=bt.Order.Stop, transmit=False, parent=self.mainside)
                highside = self.sell(
                    price=close + self.highside * self.ATR[0], size=self.mainside.size, exectype=bt.Order.Limit, transmit=True, parent=self.mainside)
                # trailside = self.sell(size=self.mainside.size, exectype=bt.Order.StopTrail, trailamount=100, transmit=True, parent=self.mainside)
            if close < self.ema_s[0] < self.ema_m[0] < self.ema_l[0] and (self.crossdown and self.rsi_filter > 50):
                if self.mainside:
                    self.close()
                    self.cancel(self.mainside)
                self.mainside = self.sell(transmit=False)
                lowside = self.buy(
                    price=close + self.lowside * self.ATR[0], size=self.mainside.size, exectype=bt.Order.Stop, transmit=False, parent=self.mainside)
                highside = self.buy(
                    price=close - self.highside * self.ATR[0], size=self.mainside.size, exectype=bt.Order.Limit, transmit=True, parent=self.mainside)
                # trailside = self.buy(size=self.mainside.size, exectype=bt.Order.StopTrail, trailamount=100, transmit=True, parent=self.mainside)
        # elif self.position:
        #     if close < self.ma[0] and self.position.size > 0:
        #         self.data.close()
        #     if close > self.ma[0] and self.position.size < 0:
        #         self.data.close()


class trade_pro_BTC(bt.Strategy):
    ''' parameter for turning'''
    params = (
        ('sma_slow', 9),
        ('sma_mid', 10),
        ('sma_fast', 300),
        ('atr', 8),
        ('lowside', 4),
        ('highside', 2),
        ('rsi_filter', 12),
        ('k_period', 3),
        ('d_period', 3),
        ('rsi_period', 16),
        ('stoch_period', 7),
        ('sma_filter', 350),

    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datetime.datetime(ago=0) + datetime.timedelta(minutes=15)
        print('%s, %s' % (dt.isoformat(), txt))

    # def notify_trade(self, trade):
    #     if not trade.isclosed:
    #         return
    #     self.mouthly_count = self.broker.getvalue()/10000.0
    #     self.log('%.2f 趴, %.2f 趴' % (trade.pnl/self.broker.getvalue()
    #              * 100, self.mouthly_count))

    ''''''

    def __init__(self):
        self.comm = 0
        self.mainside = None
        self.leverage = self.broker.getcommissioninfo(self.data).get_leverage()
        self.mouthly_count = 1.0
        self.brackets_long = None
        self.brackets_short = None
        '''EMAs'''
        self.ema_s = bt.ind.EMA(period=self.params.sma_slow)
        self.ema_m = bt.ind.EMA(period=self.params.sma_mid)
        self.ema_l = bt.ind.EMA(period=self.params.sma_fast)

        '''plus'''
        self.ATR = bt.ind.AverageTrueRange(period=self.params.atr)
        self.lowside = self.params.lowside
        self.highside = self.params.highside
        # self.nLoss = self.ATR * 0.5
        '''
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
        '''
        '''trade pro'''
        self.rsi_filter = bt.ind.RSI_Safe(period=self.params.rsi_filter)
        self.s3 = StochasticRSI(k_period=self.params.k_period, d_period=self.params.d_period,
                                rsi_period=self.params.rsi_period, stoch_period=self.params.stoch_period)
        self.crossup = bt.ind.CrossUp(self.s3.l.fastk, self.s3.l.fastd)
        self.crossdown = bt.ind.CrossDown(self.s3.l.fastk, self.s3.l.fastd)
        '''if cross ma'''
        self.ma = bt.ind.SMA(period=self.params.sma_filter)

    def next(self):
        date = self.datetime.datetime()
        # print(date, 'crossup : ', self.crossup[0], 'crossdown : ', self.crossdown[0], 'rsi_filter : ',
        #       self.rsi_filter[0], 'ema_s : ', self.ema_s[0], 'ema_m : ', self.ema_m[0], 'ema_l : ', self.ema_l[0], 'k : ', self.s3.l.fastk[0], 'd : ', self.s3.l.fastd[0])
        # if date.day == 1 and date.hour == 0 and date.minute == 0:
        #     print('date : ', date, '=' * 30, '月總結 : ', self.mouthly_count, '=' * 30)
        close = self.data.close[0]
        # print('times : ', date, 'emas : ', self.ema_s[0], self.ema_m[0], self.ema_l[0], 'RSI_KD : ',
        #       self.s3.l.fastk[0], self.s3.l.fastd[0], 'FILTER :', self.rsi_filter[0])
        # close1 = self.data1.close[0]
        # print('1m : ', date, close)
        # print('6m : ', date, close1)
        # print('-------------------')
        # print(self.position.size, self.s3.l.fastk[0])
        if not self.position:
            if close > self.ema_s[0] > self.ema_m[0] > self.ema_l[0] and (self.crossup and self.rsi_filter > 60):
                if self.s3.l.fastk[0] < 57 and self.s3.l.fastd[0] < 57:
                    # print('下單 : ', date, close)
                    if self.mainside:
                        self.close()
                        self.cancel(self.mainside)
                    self.mainside = self.buy(transmit=False)
                    lowside = self.sell(
                        price=close - self.lowside * self.ATR[0], size=self.mainside.size, exectype=bt.Order.Stop, transmit=False, parent=self.mainside)
                    highside = self.sell(
                        price=close + self.highside * self.ATR[0], size=self.mainside.size, exectype=bt.Order.Limit, transmit=True, parent=self.mainside)
                    # trailside = self.sell(size=self.mainside.size, exectype=bt.Order.StopTrail, trailamount=100, transmit=True, parent=self.mainside)
            if close < self.ema_s[0] < self.ema_m[0] < self.ema_l[0] and (self.crossdown and self.rsi_filter < 40):
                if self.s3.l.fastk[0] > 74 and self.s3.l.fastd[0] > 74:
                    # print('下單 : ', date, close)
                    if self.mainside:
                        self.close()
                        self.cancel(self.mainside)
                    self.mainside = self.sell(transmit=False)
                    lowside = self.buy(
                        price=close + self.lowside * self.ATR[0], size=self.mainside.size, exectype=bt.Order.Stop, transmit=False, parent=self.mainside)
                    highside = self.buy(
                        price=close - self.highside * self.ATR[0], size=self.mainside.size, exectype=bt.Order.Limit, transmit=True, parent=self.mainside)
                    # trailside = self.buy(size=self.mainside.size, exectype=bt.Order.StopTrail, trailamount=100, transmit=True, parent=self.mainside)
        # elif self.position:
        #     if close < self.ma[0] and self.position.size > 0:
        #         self.data.close()
        #     if close > self.ma[0] and self.position.size < 0:
        #         self.data.close()
