
def get_binance_bars(symbol, interval, startTime, endTime):
 
    url = "https://api.binance.com/api/v3/klines"
 
    startTime = str(int(startTime.timestamp() * 1000))
    endTime = str(int(endTime.timestamp() * 1000))
    limit = '1000'
 
    req_params = {"symbol" : symbol, 'interval' : interval, 'startTime' : startTime, 'endTime' : endTime, 'limit' : limit}
 
    df = pd.DataFrame(json.loads(requests.get(url, params = req_params).text))
 
    if (len(df.index) == 0):
        return None
     
    df = df.iloc[:, 0:6]
    df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
 
    df.open      = df.open.astype("float")
    df.high      = df.high.astype("float")
    df.low       = df.low.astype("float")
    df.close     = df.close.astype("float")
    df.volume    = df.volume.astype("float")
    
    df['adj_close'] = df['close']
     
    df.index = [dt.datetime.fromtimestamp(x / 1000.0) for x in df.datetime]
 
    return df
 
df_list = []
# 数据起点时间
last_datetime = dt.datetime(2019,3, 29)

trade_currency = 'ETHUSDT'

while True:
    new_df = get_binance_bars(trade_currency, '1h', last_datetime, dt.datetime.now()) # 获取1分钟k线数据
    
    if new_df is None:
        break
    df_list.append(new_df)
    last_datetime = max(new_df.index) + dt.timedelta(0, 1)

df = pd.concat(df_list)
df.shape

def printTradeAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    #Get the results we are interested in
    total_open = analyzer.total.open
    total_closed = analyzer.total.closed
    total_won = analyzer.won.total
    total_lost = analyzer.lost.total
    win_streak = analyzer.streak.won.longest
    lose_streak = analyzer.streak.lost.longest
    pnl_net = round(analyzer.pnl.net.total,2)
    strike_rate = round((total_won / total_closed) * 100, 2)
    #Designate the rows
    h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
    h2 = ['Strike Rate','Win Streak', 'Losing Streak', 'PnL Net']
    r1 = [total_open, total_closed,total_won,total_lost]
    r2 = [strike_rate, win_streak, lose_streak, pnl_net]
    #Check which set of headers is the longest.
    if len(h1) > len(h2):
        header_length = len(h1)
    else:
        header_length = len(h2)
    #Print the rows
    print_list = [h1,r1,h2,r2]
    row_format ="{:<15}" * (header_length + 1)
    print("Trade Analysis Results:")
    for row in print_list:
        print(row_format.format('',*row))
class MaCrossStrategy(bt.Strategy): #擠壓蹲點法
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
#         print('%s, %s' % (dt.isoformat(), txt))
    
    def __init__(self):
        self.count = 0
        self.order = None
        self.highestprice = 0
        self.period = 25
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
        self.linregMTM = bt.ind.OLS_BetaN(plot = False) #period = 25 寫在裡面
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

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None
    def next(self):
        self.val_start = self.broker.get_cash() #檢查餘額
        
#         print('餘額')
#         print(self.val_start)
        self.size = (self.broker.getvalue() * 1) / self.data #10趴錢買

        self.c1 = self.OFF.get()[0] > 0 #Nsqz #Y
        self.c2 = self.ON.get()[0] > 0 #sqz

        self.c3 = all(self.ON.get(size=4)[:3]) > 0 # 最近三根開壓

        
        #linreg
        self.c5 = self.MTM.get(size = 1)[0] < 0 #Y
        self.c6 = self.MTM.get(size = 1)[0] > self.MTM.get(size = 2)[0] #Y
        #MA EMA
        self.c7 = self.sma_8 > self.ema_8 #y
        #crossup
        self.c8 =any(self.crossup.get(size=5))>0 #近5根有交叉 #Y
        
        #K candles
        self.c9 = self.data.close>self.sma_8 and self.data.open >self.sma_8 #Y
        
        #WT1
        self.up53 = self.WT1 > 53 and self.WT2 >53
        self.up60 = self.WT1 > 60 and self.WT2 >60
        
        
        #long
        ##                         多頭      開收在線上    動能增加   五根內交叉向上 動能為負 或者 釋放狀態
        self.surely_conditions = self.c7 and self.c9  and self.c6 and self.c8 and ( self.c5 or self.c1)
        self.surely_conditions1 = self.c7 and self.c8 and self.c9 and self.c6 and (self.c1 or self.c5)
        if not self.position: #如果沒有倉位的話
            if  self.surely_conditions:
                self.order = self.buy()
                self.buyprice = self.order.created.price #拿到開單時候的價錢
        
        
        else:#有倉位
            self.highestprice = max(self.data.close.get()[0], self.buyprice,self.highestprice)

            if (self.WTcrossdown and self.up60): 
                print('方案1')
                self.close()
                print('money:date')
                print(self.broker.getvalue(),self.datas[0].datetime.date(0))
                print('ratio')
                print(str(self.broker.getvalue()/1000000) + '%')
                self.highestprice = 0
#             elif self.crossdown:#self.buyprice * 0.6 < self.data.close
#                 print('方案2')
#                 self.close()
#                 print('money:date')
#                 print(self.broker.getvalue(),self.datas[0].datetime.date(0))
#                 print('ratio')
#                 print(str(self.broker.getvalue()/1000000) + '%')
#                 self.highestprice = 0
            elif self.highestprice * 0.8 > self.data.close:
                print('方案3')
                print('open')
                print(self.buyprice)
                print('now')
                print(self.data.close[0])
                print('high')
                print(self.highestprice)
                self.close()
                print('money:date')
                print(self.broker.getvalue(),self.datas[0].datetime.date(0))
                print('ratio')
                print(str(self.broker.getvalue()/1000000) + '%')
                self.highestprice = 0
            


cerebro = bt.Cerebro()
print('k线数量', len(df)) 
data = bt.feeds.PandasData(dataname = df)
cerebro.adddata(data) #data會空16行 [-1]為第15行
    
cerebro.addstrategy(MaCrossStrategy)
cerebro.broker.setcash(1000000.0)
 
cerebro.addsizer(bt.sizers.PercentSizer, percents = 99)
cerebro.addanalyzer(btanalyzers.SharpeRatio, timeframe=bt.TimeFrame.Minutes, _name = "sharpe")
cerebro.addanalyzer(btanalyzers.Transactions, _name = "trans")
#add analyzer

cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
cerebro.broker.setcommission(commission=0.001)

back = cerebro.run()

printTradeAnalysis(back[0].analyzers.ta.get_analysis())

print('最终市值', cerebro.broker.getvalue()) # Ending balance
print('持幣'+str(1000000*1.507))
print(back[0].analyzers.sharpe.get_analysis()) # Sharpe

print(len(back[0].analyzers.trans.get_analysis())) # Number of Trades