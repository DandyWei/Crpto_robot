import backtrader as bt


class MaCrossStrategy(bt.Strategy): #擠壓蹲點法
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
#         print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        #開槓桿瞜
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
        #EMA array
        self.ema_20 = bt.ind.EMA(period = 20, plot = False)
        self.ema_25 = bt.ind.EMA(period = 25, plot = False)
        self.ema_30 = bt.ind.EMA(period = 30, plot = False)
        self.ema_35 = bt.ind.EMA(period = 35, plot = False)
        self.ema_40 = bt.ind.EMA(period = 40, plot = False)
        self.ema_45 = bt.ind.EMA(period = 45, plot = False)
        self.ema_50 = bt.ind.EMA(period = 50, plot = False)
        self.ema_55 = bt.ind.EMA(period = 55, plot = False)
        # Bullish Bearish
        self.bulllish = self.ema_20 > self.ema_55 #> self.ema_30 > self.ema_35 > self.ema_40 > self.ema_45 > self.ema_50 > self.ema_55
        self.bearish = self.ema_20 < self.ema_55 #< self.ema_30 < self.ema_35 < self.ema_40 < self.ema_45 < self.ema_50 < self.ema_55
        #
        self.sma_8 = bt.ind.SMA(period = 8)
        self.ema_8 = bt.ind.EMA(self.sma_8,period = 8)
#         self.MTM = bt.ind.AccelerationDecelerationOscillator(period = 25)
#         self.close = self.data.close
        #BB
        self.multKC = 1.5
        self.ma = bt.ind.SMA(period = self.period, plot = False)
        self.dev = bt.ind.StandardDeviation(period = self.period, plot = False) * self.multKC
        self.upperBB = self.ma + self.dev
        self.lowerBB = self.ma - self.dev
        #KC
        self.rangeMA = bt.ind.AverageTrueRange(period = 25, plot = False)
        self.upperKC = self.ma + self.rangeMA * self.multKC
        self.lowerKC = self.ma - self.rangeMA * self.multKC
        #conditions
        #8_MA & SMA
        self.crossup = bt.ind.CrossUp(self.sma_8, self.ema_8, plot = False)
        self.crossdown = bt.ind.CrossDown(self.sma_8, self.ema_8, plot = False)
        #squeeze LZ Once
        self.squzOff = bt.ind.CrossUp(self.upperKC,self.upperBB, plot = False) #squzOff
        self.squzOn = bt.ind.CrossDown(self.upperKC,self.upperBB, plot = False) #squzOn

        self.ON = self.upperKC > self.upperBB
        self.OFF = self.upperKC < self.upperBB
        #MTM
        self.MTM = bt.ind.AccelerationDecelerationOscillator(period = self.period, plot = False)
#         self.linregMTM = bt.ind.OLS_BetaN(plot = False) #period = 25 寫在裡面
        #WT
        self.hlc3 = (self.data.close + self.data.high + self.data.low) / 3
        self.n1 = 10
        self.n2 = 21
        self.esa = bt.ind.EMA(self.hlc3, period = self.n1, plot = False)
        self.d = bt.ind.EMA(abs(self.hlc3 - self.esa), period = self.n1, plot = False)
        self.ci = (self.hlc3 - self.esa) / (0.015 * self.d)
        self.WT1 = bt.ind.EMA(self.ci, period = self.n2, plot = False)
        self.WT2 = bt.ind.SMA(self.WT1, period = 4, plot = False)
        self.WTMTM = self.WT1 - self.WT2

        self.WTcrossdown = bt.ind.CrossDown(self.WT1, self.WT2)
        self.WTcrossup = bt.ind.CrossUp(self.WT1, self.WT2)
        #Higest Lowest
        self.highest20 = bt.ind.Highest(period = 20,  plot = False)
        self.lowest20 = bt.ind.Lowest(period = 20,  plot = False)
        #RSI
        # self.k, self.d = bt.ind.Stochastic(period = 8)
        # self.d = bt.ind.StochasticFast(period = 8)
        self.crossover = bt.ind.CrossOver(bt.ind.Stochastic(), bt.LineNum(50.0),  plot = False)

        ##BB BBW short
        self.BB20 = bt.ind.BollingerBands(plot = False) #20 2
        self.crossbotBB = self.data.close < self.BB20.lines.bot
        self.crossbotBB1 = self.data.open < self.BB20.lines.bot
        self.midstop = self.data.close > self.BB20.lines.mid
        self.BBwidth = self.BB20.lines.top - self.BB20.lines.bot

        ## ATR stop
        self.ATR = bt.ind.AverageTrueRange(period = 5) * 4.5
    def next(self):
        self.val_start = self.broker.get_cash() #檢查餘額
        self.RSIcro = self.crossover.get(size = 3)
        self.size = (self.broker.getvalue() * 0.9) / self.data #100趴錢買
        self.longsize = self.size * 0.9
        self.shortsize = self.size * 0.3
        #long
        self.c1 = self.OFF.get()[0] > 0 #Nsqz #Y
        self.c2 = self.ON.get()[0] > 0 #sqz

        self.c3 = all(self.ON.get(size=4)[:3]) > 0 # 最近三根開壓


        #linreg
        self.c5 = self.MTM.get(size = 1)[0] < 0 #Y
        self.sc5 = self.MTM.get(size = 1)[0] > 0 #動能為正
        self.c6 = self.MTM.get(size = 1)[0] > self.MTM.get(size = 2)[0] #Y #動能遞增
        self.sc6 = self.MTM.get(size = 1)[0] < self.MTM.get(size = 2)[0] #Y #動能遞減
        #MA EMA
        self.c7 = self.sma_8 > self.ema_8 #y 多頭
        self.sc7 = self.sma_8 < self.ema_8 #空頭
        #crossup
        self.c8 =any(self.crossup.get(size=5)) > 0 #近5根有交叉 #Y
        self.sc8 =any(self.crossdown.get(size=5)) > 0 #近5根有交叉 #Y
        #K candles
        self.c9 = self.data.close > self.sma_8 and self.data.open > self.sma_8 #Y 開收於sma均線上
        self.sc9 = self.data.close < self.ema_8 and self.data.open < self.ema_8 #Y 開收於ema均線下

        #WT1
        self.up53 = self.WT1 > 53 and self.WT2 > 53
        self.up60 = self.WT1 > 60 and self.WT2 > 60

        self.down53 = self.WT1 < -53 and self.WT2 < -53
        self.down60 = self.WT1 < -60 and self.WT2 < -60
        self.down25 = self.WT1 < -25 and self.WT2 < -25
        #short
        self.narrow3 = self.BBwidth.get(size = 3)[0] <= self.BBwidth.get(size = 2)[0] <=self.BBwidth.get(size = 1)[0]

        #收於20根最低點

        ##                             多頭      開收在線上    動能增加   五根內交叉向上 動能為負 或者 釋放狀態
        # self.surely_conditions_long = self.c7 and self.c9  and self.c6 and self.c8 and ( self.c5 or self.c1)
        ##                             空頭      開收在線下    動能遞減               非多頭 或者     最近有東西交叉
        # self.surely_conditions_short = self.sc7 and self.sc9  and self.sc6  and not self.bulllish and self.RSIcro and (self.sc5 or self.c1) and self.sc8#self.lowest20 (self.sc5 or self.c1) and self.sc8
        self.surely_conditions_short = self.narrow3 and self.crossbotBB and self.crossbotBB1

        # print('money:date')
        # print(self.broker.getvalue(),self.datetime.datetime(ago=0))
        # print('sc7 : ,',self.sc7,'sc9 : ,',self.sc9,'sc6 : ,',self.sc6,'sc8 : ,',self.sc8,'bulllish : ,',self.bulllish.get(),'RSIcro : ,',self.RSIcro)


        if not self.position: #如果沒有倉位的話
            if  self.surely_conditions_long:
                print('-'*50,bt.CommissionInfo().getsize(self.data, self.val_start),'-'*50)
                print('開單時間', self.datetime.datetime(ago=0))
                print('多頭 : ', self.c7 ,'--開收在線上 : ', self.c9  ,'--動能增加 : ', self.c6, '--五根內交叉向上 : ', self.c8, '--動能為負 或者 釋放狀態 : ', ( self.c5 or self.c1))
                self.longorder = self.buy(size = self.size, exectype=bt.Order.Limit, price=self.data.close)
                self.buyprice = self.longorder.created.price #拿到開單時候的價錢
            elif self.surely_conditions_short:
                # print('開單時間')
                # print(self.datetime.datetime(ago=0))
    #                 print('-' * 50)
                print('{} Send Buy, close {}'.format(
                    self.data.datetime.date(),
                    self.data.close[0])
                )
                print('最近三根BB寬度 : ',self.BBwidth.get(size = 3))
                self.shortorder = self.sell(size = self.size)
                self.buyprice = self.shortorder.created.price #拿到開單時候的價錢
        if self.position:
        #有倉位
            self.highestprice = max(self.data.high.get()[0], self.buyprice, self.highestprice)
            self.lowestprice = min(self.data.low.get()[0], self.buyprice, self.lowestprice)
            self.longATRstopTrailing = max(self.longATRstopTrailing,self.data.close-self.ATR)
            self.shortATRstopTrailing = min(self.shortATRstopTrailing,self.data.close+self.ATR)
            if self.longorder:
                if (self.WTcrossdown and self.up60):
                    print('方案1 60上方交叉')
                    self.close()
                    print('money:date')
                    print(self.broker.getvalue(),self.datetime.datetime(ago=0))
                    print('ratio')
                    print(str(round(self.broker.getvalue()/1000000,2)) + '%')
                    self.highestprice = 0
                    self.lowestprice = 1e100
                    self.longATRstopTrailing = 0
                    #no pending long
                    self.longorder = None
                    self.way1 += 1
                elif self.longATRstopTrailing > self.data.close: #self.highestprice *0.8 > self.data.close
                    print('方案2 20趴指損')
                    print('ATR : ', self.longATRstopTrailing)

                    self.close()
                    print(str(self.broker.getvalue()/1000000) + '%')
                    self.highestprice = 0
                    self.lowestprice = 1e100
                    self.longATRstopTrailing = 0
                    #no pending long
                    self.longorder = None
                    self.way2 += 1
            elif self.shortorder:

                if (self.WTcrossup and self.down53):
                    print('-' * 50)
                    print('方案3 WT指標')
                    self.close()
                    print('money : ',self.broker.getvalue(),'date : ',self.datetime.datetime(ago=0), 'ratio', str(self.broker.getvalue()/1000000), '%')
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
                    #no pending short
                    self.shortorder = None
                    self.way3 += 1
                elif self.shortATRstopTrailing < self.data.close:

                    print('-' * 50)
                    print('方案4 ATR停損')
                    self.close()
                    print('money : ',self.broker.getvalue(),'date : ',self.datetime.datetime(ago=0), 'ratio', str(self.broker.getvalue()/1000000), '%')
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
                    #no pending short
                    self.shortorder = None
                    self.way4 += 1
                # elif self.crossup:
                #     print('方案5 MA停損')
                #     self.close()
                #     print('money:date')
                #     print(self.broker.getvalue(),self.datas[0].datetime.date(0))
                #     print(str(self.broker.getvalue()/1000000) + '%')
                #     self.lowestprice = 1e10
                #     #no pending short
                #     self.shortorder = None
                #     self.way5 += 1
                elif self.midstop:

                    print('-' * 50)
                    print('方案5 under  mid')
                    self.close()
                    print('money : ',self.broker.getvalue(),'date : ',self.datetime.datetime(ago=0), 'ratio', str(self.broker.getvalue()/1000000), '%')
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
                    #no pending short
                    self.shortorder = None
                    self.way5 += 1

                elif self.surely_conditions_long:
                    print('方案6 換倉')

                    self.close()
                    print('money:date')
                    print(self.broker.getvalue(),self.datetime.datetime(ago=0))
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
                    #no pending short
                    self.shortorder = None
                    self.way6 += 1

                    print('$'*500)
                #     #換開多單
                #     self.longorder = self.buy(size = 500)
                #     self.buyprice = self.longorder.created.price #拿到開單時候的價錢
            # print('法1 : ', str(self.way1), '法2 : ', str(self.way2),
            #  '法3 WTindicators: ', (self.way3), '法4 10%停損: ',str(self.way4),
            #   '法5 MA停損: ', str(self.way5), '法6 change position: ', str(self.way6))
