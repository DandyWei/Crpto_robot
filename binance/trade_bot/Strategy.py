import backtrader as bt


class MaCrossStrategy(bt.Strategy): #擠壓蹲點法
    def __init__(self):

        self.surely_conditions_long = None
        self.surely_conditions_short = None
        self.longorder = None
        self.shortorder = None
        self.highestprice = 0
        self.lowestprice = 1e10
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
        self.sma_8 = bt.ind.SMA(period = 8, plot = False)
        self.ema_8 = bt.ind.EMA(self.sma_8,period = 8, plot = False)
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
        self.esa = bt.ind.EMA(self.hlc3, period = self.n1)
        self.d = bt.ind.EMA(abs(self.hlc3 - self.esa), period = self.n1)
        self.ci = (self.hlc3 - self.esa) / (0.015 * self.d)
        self.WT1 = bt.ind.EMA(self.ci, period = self.n2)
        self.WT2 = bt.ind.SMA(self.WT1, period = 4)
        self.WTMTM = self.WT1 - self.WT2

        self.WTcrossdown = bt.ind.CrossDown(self.WT1, self.WT2)
        self.WTcrossup = bt.ind.CrossUp(self.WT1, self.WT2)
        #Higest Lowest
        self.highest20 = bt.ind.Highest(period = 20)
        self.lowest20 = bt.ind.Lowest(period = 20)
        #RSI
        # self.k, self.d = bt.ind.Stochastic(period = 8)
        # self.d = bt.ind.StochasticFast(period = 8)
        self.crossover = bt.ind.CrossOver(bt.ind.Stochastic(), bt.LineNum(50.0))

        ##BB BBW short
        self.BB20 = bt.ind.BollingerBands() #20 2
        self.crossbotBB = self.data.close < self.BB20.lines.bot
        self.crossbotBB1 = self.data.open < self.BB20.lines.bot
        self.midstop = self.data.close > self.BB20.lines.mid
        self.BBwidth = self.BB20.lines.top - self.BB20.lines.bot
    def next_open(self):
        self.buy()
        print('{} Send Buy, close {}'.format(
            self.data.datetime.date(),
            self.data.close[0])
        )
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
        self.surely_conditions_long = self.c7 and self.c9  and self.c6 and self.c8 and ( self.c5 or self.c1)


        if not self.position: #如果沒有倉位的話
            if  self.surely_conditions_long:
                print('-'*50,'-'*50)
                print('開單時間')
                print(self.datetime.datetime(ago=0))
                self.longorder = self.buy(size = self.size)
                self.buyprice = self.longorder.created.price #拿到開單時候的價錢

        else:#有倉位
            self.highestprice = max(self.data.high.get()[0], self.buyprice, self.highestprice)
            if self.longorder:
                if (self.WTcrossdown and self.up60):
                    print('方案1')
                    self.close()
                    print('money:date')
                    print(self.broker.getvalue(),self.datetime.datetime(ago=0))
                    print('ratio')
                    print(str(round(self.broker.getvalue()/1000000,2)) + '%')
                    self.highestprice = 0
                    self.lowestprice = 1e100
                    #no pending long
                    self.longorder = None
                    self.way1 += 1
                elif self.highestprice * 0.8 > self.data.close:
                    print('方案2')
                    self.close()
                    print(str(self.broker.getvalue()/1000000) + '%')
                    self.highestprice = 0
                    self.lowestprice = 1e100
                    #no pending long
                    self.longorder = None
                    self.way2 += 1
