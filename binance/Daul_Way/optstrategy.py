import datetime as dt
import pandas as pd
import backtrader as bt
from get_bar import *
from Strategy import *
import time
import csv
from tqdm.auto import tqdm


def rangebound(n=None):
    if n - 2 < 0:
        return range(0, n + 3)
    return range(n - 2, n + 3)


def tt_count(list=None):
    total = 1
    for i in list:
        if isinstance(i, int):
            total *= i
        else:
            total *= len(i)
    return total


class opt_parameters:
    def __init__(self, cerebro, stadegy):
        self.sma_slow = range(2, 10, 1)
        self.sma_mid = range(10, 30, 2)
        self.sma_fast = range(180, 550, 30)
        self.k_period = range(3, 5, 1)
        self.d_period = range(3, 5, 1)
        self.rsi_period = range(7, 30, 4)
        self.stoch_period = range(7, 30, 4)
        self.rsi_filter = range(1, 20, 1)
        self.sma_filter = range(200, 550, 50)
        self.atr = range(1, 20, 1)
        self.lowside = range(1, 15, 1)
        self.highside = range(1, 15, 1)
        self.cerebro = cerebro
        self.stadegy = stadegy
        self.back = None

    def opt(self,):
        print(type(self.sma_fast), type(self.atr))
        self.cerebro.optstrategy(self.stadegy,
                                 # sma_slow=self.sma_slow,
                                 # sma_mid=self.sma_mid,
                                 sma_fast=self.sma_fast,
                                 # atr=self.atr,
                                 # lowside=self.lowside,
                                 # highside=self.highside,
                                 # rsi_filter=self.rsi_filter,
                                 # k_period=self.k_period,
                                 # d_period=self.d_period,
                                 # rsi_period=self.rsi_period,
                                 # stoch_period=self.stoch_period,
                                 # sma_filter=self.sma_filter,
                                 )
        '''setup for our callback funtion and Tqdm then run the optimized function for results'''
        global pbar

        totol = len(self.atr) * len(self.lowside) * len(self.highside)

        pbar = tqdm(desc='Opt runs', leave=True, position=1, unit='run', total=totol)

        self.cerebro.optcallback(cb=bt_opt_callback)

        self.back = self.cerebro.run(stdstats=False, optreturn=True, optdatas=True, maxcpus=None)

    def record(self):
        '''write into csv file'''
        final_results_list = []
        step = 'test'
        now = dt.datetime.now()

        with open('params_{}_{}_{}_{}.csv'.format(step, now.year, now.month, now.day), 'w', newline='') as csvfile:

            writer = csv.writer(csvfile)
            writer.writerow(['sma_slow', 'sma_mid', 'sma_fast', 'atr', 'lowside', 'highside', 'rsi_filter',
                            'k_period', 'd_period', 'rsi_period', 'stoch_period', 'sma_filter', 'Drawd', 'Total trade', 'PnL', 'SQN'])
            for run in self.back:
                for strategy in run:
                    # print('---------------', strategy.params, strategy)
                    PnL = round(cerebro.broker.getvalue() - 1000000.0, 8)
                    SQN = strategy.analyzers.sqn.get_analysis()
                    Max_down = strategy.analyzers.drawd.get_analysis()['max']['drawdown']
                    total_trade = len(strategy.analyzers.trans.get_analysis()) / 2
                    final_results_list.append([strategy.params.sma_slow, strategy.params.sma_mid, strategy.params.sma_fast, strategy.params.atr, strategy.params.lowside, strategy.params.highside, strategy.params.rsi_filter, strategy.params.k_period, strategy.params.d_period, strategy.params.rsi_period, strategy.params.stoch_period, strategy.params.sma_filter,
                                               Max_down, total_trade, PnL, SQN['sqn']])
                    writer.writerow([strategy.params.sma_slow, strategy.params.sma_mid, strategy.params.sma_fast, strategy.params.atr, strategy.params.lowside, strategy.params.highside, strategy.params.rsi_filter,
                                    strategy.params.k_period, strategy.params.d_period, strategy.params.rsi_period, strategy.params.stoch_period, strategy.params.sma_filter, Max_down, total_trade, PnL, SQN['sqn']])
                    print('開始寫入')

        sort_by_SQN = sorted(final_results_list, key=lambda x: x[-1],
                             reverse=True)
        for line in sort_by_SQN[:5]:
            # final_return.add(line)
            print(line)
        return final_return


class opt_smas(opt_parameters):
    def __init__(self, stadegy, df):
        self.sma_fast = range(3, 9, 1)  # range(3, 9, 1)
        self.sma_mid = range(10, 20, 1)  # range(10, 20, 1)
        self.sma_slow = range(200, 400, 50)
        self.cerebro = None
        self.stadegy = stadegy
        self.back = None
        self.data = None
        self.df = df

    def opt(self):
        self.cerebro = bt.Cerebro(quicknotify=True, preload=True)
        self.data = bt.feeds.PandasData(dataname=self.df)
        self.cerebro.resampledata(self.data, timeframe=bt.TimeFrame.Minutes,
                                  compression=6, boundoff=1)  # rightedge=False

        self.cerebro.broker.setcash(1000000.0)

        self.cerebro.addsizer(bt.sizers.PercentSizer, percents=99)
        # add analyzer
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                                 timeframe=bt.TimeFrame.Minutes, _name="sharpe")
        self.cerebro.addanalyzer(bt.analyzers.Transactions, _name="trans")
        self.cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawd")
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
        self.cerebro.broker.setcommission(commission=0.001, leverage=3,
                                          stocklike=False)  # ,margin=False, mult = 2

        self.cerebro.addstrategy(self.stadegy)
        self.cerebro.optstrategy(self.stadegy,
                                 sma_slow=self.sma_fast,
                                 sma_mid=self.sma_mid,
                                 sma_fast=self.sma_slow,
                                 # atr=self.atr,
                                 # lowside=self.lowside,
                                 # highside=self.highside,
                                 # rsi_filter=self.rsi_filter,
                                 # k_period=self.k_period,
                                 # d_period=self.d_period,
                                 # rsi_period=self.rsi_period,
                                 # stoch_period=self.stoch_period,
                                 # sma_filter=self.sma_filter,
                                 )
        '''setup for our callback funtion and Tqdm then run the optimized function for results'''
        global pbar
        totol = tt_count([self.sma_slow, self.sma_mid, self.sma_fast])

        pbar = tqdm(desc='Opt runs', leave=True, position=1, unit='run', total=totol)

        self.cerebro.optcallback(cb=bt_opt_callback)

        self.back = self.cerebro.run(stdstats=False, optreturn=True, optdatas=True, maxcpus=None)
        self.record()

    def record(self):
        '''write into csv file'''
        final_results_list = []
        step = 'smas'
        now = dt.datetime.now()
        with open('params_{}_{}_{}_{}.csv'.format(step, now.year, now.month, now.day), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['sma_fast', 'sma_mid', 'sma_slow', 'atr', 'lowside', 'highside', 'rsi_filter',
                            'k_period', 'd_period', 'rsi_period', 'stoch_period', 'sma_filter', 'Drawd', 'Total trade', 'PnL', 'SQN'])
            for run in self.back:
                for strategy in run:
                    PnL = round(self.cerebro.broker.getvalue() - 1000000.0, 8)
                    SQN = strategy.analyzers.sqn.get_analysis()
                    Max_down = strategy.analyzers.drawd.get_analysis()['max']['drawdown']
                    total_trade = len(strategy.analyzers.trans.get_analysis()) / 2
                    final_results_list.append([strategy.params.sma_slow, strategy.params.sma_mid, strategy.params.sma_fast, strategy.params.atr, strategy.params.lowside, strategy.params.highside, strategy.params.rsi_filter, strategy.params.k_period, strategy.params.d_period, strategy.params.rsi_period, strategy.params.stoch_period, strategy.params.sma_filter,
                                               Max_down, total_trade, PnL, SQN['sqn']])
                    writer.writerow([strategy.params.sma_fast, strategy.params.sma_mid, strategy.params.sma_slow, strategy.params.atr, strategy.params.lowside, strategy.params.highside, strategy.params.rsi_filter,
                                    strategy.params.k_period, strategy.params.d_period, strategy.params.rsi_period, strategy.params.stoch_period, strategy.params.sma_filter, Max_down, total_trade, PnL, SQN['sqn']])

        sort_by_SQN = sorted(final_results_list, key=lambda x: x[-1],
                             reverse=True)
        for line in sort_by_SQN[:3]:
            # final_return.add(line)
            print(line)
        '''range is 5'''
        if self.sma_fast == rangebound(sort_by_SQN[0][0]):
            self.sma_fast = sort_by_SQN[0][0]
        elif self.sma_fast == sort_by_SQN[0][0]:
            pass
        else:
            self.sma_fast = rangebound(sort_by_SQN[0][0])

        if self.sma_mid == rangebound(sort_by_SQN[0][1]):
            self.sma_mid = sort_by_SQN[0][1]
        elif self.sma_mid == sort_by_SQN[0][1]:
            pass
        else:
            self.sma_mid = rangebound(sort_by_SQN[0][1])

        if self.sma_slow == rangebound(sort_by_SQN[0][2]):
            self.sma_slow = sort_by_SQN[0][2]
        elif self.sma_slow == sort_by_SQN[0][2]:
            pass
        else:
            self.sma_slow = rangebound(sort_by_SQN[0][2])

        if isinstance(self.sma_fast, int) and isinstance(self.sma_mid, int) and isinstance(self.sma_slow, int):
            return self.sma_fast, self.sma_mid, self.sma_slow,
        else:
            print('smas : ', self.sma_slow, self.sma_mid, self.sma_fast)
        self.opt()


class opt_rsis(opt_parameters):
    def __init__(self, stadegy, df, f, m, s):
        self.sma_fast = range(f, f+1)
        self.sma_mid = range(m, m+1)
        self.sma_slow = range(s, s+1)

        self.k_period = range(3, 5, 1)
        self.d_period = range(3, 5, 1)
        self.rsi_period = range(7, 30, 4)
        self.stoch_period = range(7, 30, 4)
        self.cerebro = None
        self.stadegy = stadegy
        self.back = None
        self.data = None
        self.df = df

    def opt(self):
        self.cerebro = bt.Cerebro(quicknotify=True, preload=True)
        self.data = bt.feeds.PandasData(dataname=self.df)
        self.cerebro.resampledata(self.data, timeframe=bt.TimeFrame.Minutes,
                                  compression=6, boundoff=1)  # rightedge=False

        self.cerebro.broker.setcash(1000000.0)

        self.cerebro.addsizer(bt.sizers.PercentSizer, percents=99)
        # add analyzer
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                                 timeframe=bt.TimeFrame.Minutes, _name="sharpe")
        self.cerebro.addanalyzer(bt.analyzers.Transactions, _name="trans")
        self.cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawd")
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
        self.cerebro.broker.setcommission(commission=0.001, leverage=3,
                                          stocklike=False)  # ,margin=False, mult = 2

        self.cerebro.addstrategy(self.stadegy)
        self.cerebro.optstrategy(self.stadegy,
                                 sma_slow=self.sma_fast,
                                 sma_mid=self.sma_mid,
                                 sma_fast=self.sma_slow,
                                 # atr=self.atr,
                                 # lowside=self.lowside,
                                 # highside=self.highside,
                                 # rsi_filter=self.rsi_filter,
                                 k_period=self.k_period,
                                 d_period=self.d_period,
                                 rsi_period=self.rsi_period,
                                 stoch_period=self.stoch_period,
                                 # sma_filter=self.sma_filter,
                                 )
        '''setup for our callback funtion and Tqdm then run the optimized function for results'''
        global pbar
        totol = tt_count([self.k_period, self.d_period, self.rsi_period, self.stoch_period])

        pbar = tqdm(desc='Opt runs', leave=True, position=1, unit='run', total=totol)

        self.cerebro.optcallback(cb=bt_opt_callback)

        self.back = self.cerebro.run(stdstats=False, optreturn=True, optdatas=True, maxcpus=None)
        self.record()

    def record(self):
        '''write into csv file'''
        final_results_list = []
        step = 'rsis'
        now = dt.datetime.now()
        with open('params_{}_{}_{}_{}.csv'.format(step, now.year, now.month, now.day), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['sma_fast', 'sma_mid', 'sma_slow', 'atr', 'lowside', 'highside', 'rsi_filter',
                            'k_period', 'd_period', 'rsi_period', 'stoch_period', 'sma_filter', 'Drawd', 'Total trade', 'PnL', 'SQN'])
            for run in self.back:
                for strategy in run:
                    PnL = round(self.cerebro.broker.getvalue() - 1000000.0, 8)
                    SQN = strategy.analyzers.sqn.get_analysis()
                    Max_down = strategy.analyzers.drawd.get_analysis()['max']['drawdown']
                    total_trade = len(strategy.analyzers.trans.get_analysis()) / 2
                    final_results_list.append([strategy.params.sma_slow, strategy.params.sma_mid, strategy.params.sma_fast, strategy.params.atr, strategy.params.lowside, strategy.params.highside, strategy.params.rsi_filter, strategy.params.k_period, strategy.params.d_period, strategy.params.rsi_period, strategy.params.stoch_period, strategy.params.sma_filter,
                                               Max_down, total_trade, PnL, SQN['sqn']])
                    writer.writerow([strategy.params.sma_fast, strategy.params.sma_mid, strategy.params.sma_slow, strategy.params.atr, strategy.params.lowside, strategy.params.highside, strategy.params.rsi_filter,
                                    strategy.params.k_period, strategy.params.d_period, strategy.params.rsi_period, strategy.params.stoch_period, strategy.params.sma_filter, Max_down, total_trade, PnL, SQN['sqn']])

        sort_by_SQN = sorted(final_results_list, key=lambda x: x[-1],
                             reverse=True)
        for line in sort_by_SQN[:3]:
            # final_return.add(line)
            print(line)
        '''range is 5'''
        if self.k_period == rangebound(sort_by_SQN[0][7]):
            self.k_period = sort_by_SQN[0][7]
        elif self.k_period == sort_by_SQN[0][7]:
            pass
        else:
            self.k_period = rangebound(sort_by_SQN[0][7])

        if self.d_period == rangebound(sort_by_SQN[0][8]):
            self.d_period = sort_by_SQN[0][8]
        elif self.d_period == sort_by_SQN[0][8]:
            pass
        else:
            self.d_period = rangebound(sort_by_SQN[0][8])

        if self.rsi_period == rangebound(sort_by_SQN[0][9]):
            self.rsi_period = sort_by_SQN[0][9]
        elif self.rsi_period == sort_by_SQN[0][9]:
            pass
        else:
            self.rsi_period = rangebound(sort_by_SQN[0][9])

        if self.stoch_period == rangebound(sort_by_SQN[0][10]):
            self.stoch_period = sort_by_SQN[0][10]
        elif self.stoch_period == sort_by_SQN[0][10]:
            pass
        else:
            self.stoch_period = rangebound(sort_by_SQN[0][10])

        if isinstance(self.k_period, int) and isinstance(self.d_period, int) and isinstance(self.rsi_period, int) and isinstance(self.stoch_period, int):
            return self.k_period, self.d_period, self.rsi_period, self.stoch_period
        else:
            print('rsis : ', self.k_period, self.d_period, self.rsi_period, self.stoch_period)
        self.opt()


class opt_atrs(opt_parameters):
    def __init__(self, stadegy, df, f, m, s, k, d, rsi, stoch):
        self.sma_fast = range(f, f + 1)
        self.sma_mid = range(m, m + 1)
        self.sma_slow = range(s, s + 1)
        self.k_period = range(k, k + 1)
        self.d_period = range(d, d + 1)
        self.rsi_period = range(rsi, rsi + 1)
        self.stoch_period = range(stoch, stoch + 1)

        self.atr = range(1, 20, 1)
        self.lowside = range(1, 15, 1)
        self.highside = range(1, 15, 1)
        self.cerebro = None
        self.stadegy = stadegy
        self.back = None
        self.data = None
        self.df = df

    def opt(self):
        self.cerebro = bt.Cerebro(quicknotify=True, preload=True)
        self.data = bt.feeds.PandasData(dataname=self.df)
        self.cerebro.resampledata(self.data, timeframe=bt.TimeFrame.Minutes,
                                  compression=6, boundoff=1)  # rightedge=False

        self.cerebro.broker.setcash(1000000.0)

        self.cerebro.addsizer(bt.sizers.PercentSizer, percents=99)
        # add analyzer
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                                 timeframe=bt.TimeFrame.Minutes, _name="sharpe")
        self.cerebro.addanalyzer(bt.analyzers.Transactions, _name="trans")
        self.cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawd")
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
        self.cerebro.broker.setcommission(commission=0.001, leverage=3,
                                          stocklike=False)  # ,margin=False, mult = 2

        self.cerebro.addstrategy(self.stadegy)
        self.cerebro.optstrategy(self.stadegy,
                                 sma_slow=self.sma_fast,
                                 sma_mid=self.sma_mid,
                                 sma_fast=self.sma_slow,
                                 atr=self.atr,
                                 lowside=self.lowside,
                                 highside=self.highside,
                                 # rsi_filter=self.rsi_filter,
                                 k_period=self.k_period,
                                 d_period=self.d_period,
                                 rsi_period=self.rsi_period,
                                 stoch_period=self.stoch_period,
                                 # sma_filter=self.sma_filter,
                                 )
        '''setup for our callback funtion and Tqdm then run the optimized function for results'''
        global pbar
        totol = tt_count([self.atr, self.lowside, self.highside])

        pbar = tqdm(desc='Opt runs', leave=True, position=1, unit='run', total=totol)

        self.cerebro.optcallback(cb=bt_opt_callback)

        self.back = self.cerebro.run(stdstats=False, optreturn=True, optdatas=True, maxcpus=None)
        self.record()

    def record(self):
        '''write into csv file'''
        final_results_list = []
        step = 'atr'
        now = dt.datetime.now()
        with open('params_{}_{}_{}_{}.csv'.format(step, now.year, now.month, now.day), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['sma_fast', 'sma_mid', 'sma_slow', 'atr', 'lowside', 'highside', 'rsi_filter',
                            'k_period', 'd_period', 'rsi_period', 'stoch_period', 'sma_filter', 'Drawd', 'Total trade', 'PnL', 'SQN'])
            for run in self.back:
                for strategy in run:
                    PnL = round(self.cerebro.broker.getvalue() - 1000000.0, 8)
                    SQN = strategy.analyzers.sqn.get_analysis()
                    Max_down = strategy.analyzers.drawd.get_analysis()['max']['drawdown']
                    total_trade = len(strategy.analyzers.trans.get_analysis()) / 2
                    final_results_list.append([strategy.params.sma_slow, strategy.params.sma_mid, strategy.params.sma_fast, strategy.params.atr, strategy.params.lowside, strategy.params.highside, strategy.params.rsi_filter, strategy.params.k_period, strategy.params.d_period, strategy.params.rsi_period, strategy.params.stoch_period, strategy.params.sma_filter,
                                               Max_down, total_trade, PnL, SQN['sqn']])
                    writer.writerow([strategy.params.sma_fast, strategy.params.sma_mid, strategy.params.sma_slow, strategy.params.atr, strategy.params.lowside, strategy.params.highside, strategy.params.rsi_filter,
                                    strategy.params.k_period, strategy.params.d_period, strategy.params.rsi_period, strategy.params.stoch_period, strategy.params.sma_filter, Max_down, total_trade, PnL, SQN['sqn']])

        sort_by_SQN = sorted(final_results_list, key=lambda x: x[-1],
                             reverse=True)
        for line in sort_by_SQN[:3]:
            # final_return.add(line)
            print(line)
        '''range is 5'''
        if self.atr == rangebound(sort_by_SQN[0][3]):
            self.atr = sort_by_SQN[0][3]
        elif self.atr == sort_by_SQN[0][3]:
            pass
        else:
            self.atr = rangebound(sort_by_SQN[0][3])

        if self.lowside == rangebound(sort_by_SQN[0][4]):
            self.lowside = sort_by_SQN[0][4]
        elif self.lowside == sort_by_SQN[0][4]:
            pass
        else:
            self.lowside = rangebound(sort_by_SQN[0][4])

        if self.highside == rangebound(sort_by_SQN[0][5]):
            self.highside = sort_by_SQN[0][5]
        elif self.highside == sort_by_SQN[0][5]:
            pass
        else:
            self.highside = rangebound(sort_by_SQN[0][5])

        if isinstance(self.atr, int) and isinstance(self.lowside, int) and isinstance(self.highside, int):
            return self.atr, self.highside, self.lowside
        else:
            print('atr, lowside, highside : ', self.atr, self.lowside, self.highside)
        self.opt()


class opt_both_filter(opt_parameters):
    def __init__(self, stadegy, df, f, m, s, k, d, rsi, stoch, atr, high, low):
        self.sma_fast = range(f, f + 1)
        self.sma_mid = range(m, m + 1)
        self.sma_slow = range(s, s + 1)
        self.k_period = range(k, k + 1)
        self.d_period = range(d, d + 1)
        self.rsi_period = range(rsi, rsi + 1)
        self.stoch_period = range(stoch, stoch + 1)
        self.atr = range(atr, atr + 1)
        self.lowside = range(low, low + 1)
        self.highside = range(high, high + 1)

        self.rsi_filter = range(1, 20, 1)
        self.sma_filter = range(200, 550, 50)
        self.cerebro = None
        self.stadegy = stadegy
        self.back = None
        self.data = None
        self.df = df

    def opt(self):
        self.cerebro = bt.Cerebro(quicknotify=True, preload=True)
        self.data = bt.feeds.PandasData(dataname=self.df)
        self.cerebro.resampledata(self.data, timeframe=bt.TimeFrame.Minutes,
                                  compression=6, boundoff=1)  # rightedge=False

        self.cerebro.broker.setcash(1000000.0)

        self.cerebro.addsizer(bt.sizers.PercentSizer, percents=99)
        # add analyzer
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                                 timeframe=bt.TimeFrame.Minutes, _name="sharpe")
        self.cerebro.addanalyzer(bt.analyzers.Transactions, _name="trans")
        self.cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawd")
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
        self.cerebro.broker.setcommission(commission=0.001, leverage=3,
                                          stocklike=False)  # ,margin=False, mult = 2

        self.cerebro.addstrategy(self.stadegy)
        self.cerebro.optstrategy(self.stadegy,
                                 sma_slow=self.sma_fast,
                                 sma_mid=self.sma_mid,
                                 sma_fast=self.sma_slow,
                                 atr=self.atr,
                                 lowside=self.lowside,
                                 highside=self.highside,
                                 rsi_filter=self.rsi_filter,
                                 k_period=self.k_period,
                                 d_period=self.d_period,
                                 rsi_period=self.rsi_period,
                                 stoch_period=self.stoch_period,
                                 sma_filter=self.sma_filter,
                                 )
        '''setup for our callback funtion and Tqdm then run the optimized function for results'''
        global pbar
        totol = tt_count([self.rsi_filter, self.sma_filter])
        # if isinstance(self.sma_slow, int):
        #     total *= self.sma_slow
        # else:
        #     total *= len(self.sma_slow)
        # totol = len(self.sma_slow) * len(self.sma_mid) * len(self.sma_fast)

        pbar = tqdm(desc='Opt runs', leave=True, position=1, unit='run', total=totol)

        self.cerebro.optcallback(cb=bt_opt_callback)

        self.back = self.cerebro.run(stdstats=False, optreturn=True, optdatas=True, maxcpus=None)
        self.record()

    def record(self):
        '''write into csv file'''
        final_results_list = []
        step = 'both_filter'
        now = dt.datetime.now()
        with open('params_{}_{}_{}_{}.csv'.format(step, now.year, now.month, now.day), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['sma_fast', 'sma_mid', 'sma_slow', 'atr', 'lowside', 'highside', 'rsi_filter',
                            'k_period', 'd_period', 'rsi_period', 'stoch_period', 'sma_filter', 'Drawd', 'Total trade', 'PnL', 'SQN'])
            for run in self.back:
                for strategy in run:
                    PnL = round(self.cerebro.broker.getvalue() - 1000000.0, 8)
                    SQN = strategy.analyzers.sqn.get_analysis()
                    Max_down = strategy.analyzers.drawd.get_analysis()['max']['drawdown']
                    total_trade = len(strategy.analyzers.trans.get_analysis()) / 2
                    final_results_list.append([strategy.params.sma_slow, strategy.params.sma_mid, strategy.params.sma_fast, strategy.params.atr, strategy.params.lowside, strategy.params.highside, strategy.params.rsi_filter, strategy.params.k_period, strategy.params.d_period, strategy.params.rsi_period, strategy.params.stoch_period, strategy.params.sma_filter,
                                               Max_down, total_trade, PnL, SQN['sqn']])
                    writer.writerow([strategy.params.sma_fast, strategy.params.sma_mid, strategy.params.sma_slow, strategy.params.atr, strategy.params.lowside, strategy.params.highside, strategy.params.rsi_filter,
                                    strategy.params.k_period, strategy.params.d_period, strategy.params.rsi_period, strategy.params.stoch_period, strategy.params.sma_filter, Max_down, total_trade, PnL, SQN['sqn']])

        sort_by_SQN = sorted(final_results_list, key=lambda x: x[-1],
                             reverse=True)
        for line in sort_by_SQN[:3]:
            # final_return.add(line)
            print(line)
        '''range is 5'''
        if self.rsi_filter == rangebound(sort_by_SQN[0][6]):
            self.rsi_filter = sort_by_SQN[0][6]
        elif self.rsi_filter == sort_by_SQN[0][6]:
            pass
        else:
            self.rsi_filter = rangebound(sort_by_SQN[0][6])

        if self.sma_filter == rangebound(sort_by_SQN[0][11]):
            self.sma_filter = sort_by_SQN[0][11]
        elif self.sma_filter == sort_by_SQN[0][11]:
            pass
        else:
            self.sma_filter = rangebound(sort_by_SQN[0][11])

        if isinstance(self.rsi_filter, int) and isinstance(self.sma_filter, int):
            return
        else:
            print('filters : ', self.rsi_filter, self.sma_filter)
        self.opt()


def bt_opt_callback(cb):
    pbar.update()


def printTradeAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    # Get the results we are interested in
    total_open = analyzer.total.open
    total_closed = analyzer.total.closed
    total_won = analyzer.won.total
    total_lost = analyzer.lost.total
    win_streak = analyzer.streak.won.longest
    lose_streak = analyzer.streak.lost.longest
    pnl_net = round(analyzer.pnl.net.total, 2)
    strike_rate = round((total_won / total_closed) * 100, 2)
    # Designate the rows
    h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
    h2 = ['Strike Rate', 'Win Streak', 'Losing Streak', 'PnL Net']
    r1 = [total_open, total_closed, total_won, total_lost]
    r2 = [strike_rate, win_streak, lose_streak, pnl_net]
    # Check which set of headers is the longest.
    if len(h1) > len(h2):
        header_length = len(h1)
    else:
        header_length = len(h2)
    # Print the rows
    print_list = [h1, r1, h2, r2]
    row_format = "{:<15}" * (header_length + 1)
    print("Trade Analysis Results:")
    for row in print_list:
        print(row_format.format('', *row))


def main(**kwargs):
    '''get data from binance port'''
    df_list = []
    final_time = dt.datetime.now()
    last_datetime = final_time - dt.timedelta(days=90)  # 第一筆資料 2019,12,8
    trade_currency = 'BTCUSDT'

    while True:
        #        new_df = get_binance_bars(trade_currency, '1h', last_datetime, dt.datetime.now())           # 獲取一小時數據
        bars_fun = Get_bars(trade_currency, '1m', last_datetime, final_time,
                            contract=True)           # 獲取一小時數據 dt.datetime.now()
        new_df = bars_fun.get_binance_bars()

        if new_df is None:
            break
        df_list.append(new_df)
        last_datetime = new_df.index[-1] + dt.timedelta(0, 1)
        if (last_datetime.timestamp() - 28800) > final_time.timestamp():
            break
    week_list
    df = pd.concat(df_list)
    df.to_csv(r'.\Daul_Way\export_dataframe.csv', index=False, header=True)
    '''set parameter for init our stradegy'''
    # cerebro = bt.Cerebro(quicknotify=True, preload=True)
    print('the number if k lines', len(df))

    '''
    這邊設定初始的參數範圍
    優化順序為下
    1.SMA找趨勢
    2.RSI找買點
    3.ATR 找進出的量
    4.rsi_filter 以及SMA FILTER
    '''

    # smas = opt_smas(trade_pro_BTC, df)
    # f, m, s = smas.opt()
    # f, m, s = 8, 9, 302
    # rsi = opt_rsis(trade_pro_BTC, df, f, m, s)
    # k, d, rsi, stoch = rsi.opt()
    # atr = opt_atrs(trade_pro_BTC, df, f, m, s, k, d, rsi, stoch)
    # atr, high, low = atr.opt()
    # b_filter = opt_both_filter(trade_pro_BTC, df, f, m, s, k, d, rsi, stoch, atr, high, low)
    # b_filter.opt()

    '''
    1.6 - 1.9 Below average

    2.0 - 2.4 Average

    2.5 - 2.9 Good

    3.0 - 5.0 Excellent

    5.1 - 6.9 Superb

    7.0 - Holy Grail?

    '''


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('手動關閉，時間為 : ', dt.datetime.now().strftime("%d-%m-%y %H:%M"))
