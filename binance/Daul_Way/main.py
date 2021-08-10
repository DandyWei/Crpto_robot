import datetime as dt
import pandas as pd
import backtrader as bt
from get_bar import *
from Strategy import *
import time
import csv
from tqdm.auto import tqdm


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


# pbar = tqdm(desc='Opt runs', leave=True, position=1, unit='run')


# def bt_opt_callback(cb):
# pbar.update()


def main(**kwargs):

    df_list = []
    # 数据起点时间
    last_datetime = dt.datetime(2021, 8, 1)  # 第一筆資料 2019,12,8
    final_time = dt.datetime.now()
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
    df = pd.concat(df_list)

    cerebro = bt.Cerebro(quicknotify=True, preload=False)
    print('k线数量', len(df))
    data = bt.feeds.PandasData(dataname=df)
    # cerebro.adddata(data)  # data會空16行DaulMA_ATR_tracking [-1]為第15行
    # resample

    cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes,
                         compression=6, boundoff=1)  # rightedge=False
    # cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes,compression=180)

    # cerebro.addstrategy(MaCrossStrategy)
    # cerebro.addstrategy(GridStrategy)
    # cerebro.addstrategy(min_49_Strategy)
    # cerebro.addstrategy(TestStrategy)
    # cerebro.addstrategy(Heikun_Ashi_Double_E_Strategy)
    # cerebro.addstrategy(Double_MA)
    # cerebro.addstrategy(ATR_tracking)
    # cerebro.addstrategy(DaulMA_ATR_tracking)
    # cerebro.addstrategy(up70)
    # cerebro.addstrategy(trade_pro_ETH)
    cerebro.addstrategy(trade_pro_BTC)
    # cerebro.addstrategy(trade_pro)
    '''opt'''
    '''
    1.SMA找趨勢
    2.RSI找買點
    3.ATR 找進出的量
    4.rsi_filter 以及SMA FILTER
    '''
    # k_period = range(3, 5, 1)
    # d_period = range(3, 5, 1)
    # rsi_period = range(7, 30, 4)
    # stoch_period = range(7, 30, 4)
    # rsi_filter = range(1, 20, 1)
    # sma_filter = range(200, 550, 50)
    # atr = range(1, 3, 1)
    # lowside = range(1, 15, 1)
    # highside = range(1, 15, 1)
    # cerebro.optstrategy(trade_pro_ETH,
    #                     # sma_slow=range(2, 10, 1),
    #                     # sma_mid=range(10, 30, 2),
    #                     # sma_fast=range(180, 550, 30),
    #                     atr=atr,
    #                     # lowside=lowside,
    #                     # highside=highside,
    #                     # rsi_filter=rsi_filter,
    #                     # k_period=k_period,
    #                     # d_period=d_period,
    #                     # rsi_period=rsi_period,
    #                     # stoch_period=stoch_period,
    #                     # sma_filter=sma_filter,
    #
    #                     )
    # totol = len(atr) * len(lowside) * len(highside)
    cerebro.broker.setcash(1000000.0)

    cerebro.addsizer(bt.sizers.PercentSizer, percents=99)
    # add analyzer
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Minutes, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.Transactions, _name="trans")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawd")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    # for i in range(1,30):
    cerebro.broker.setcommission(commission=0.001, leverage=3,
                                 stocklike=False)  # ,margin=False, mult = 2
    # cerebro.broker.set_coc(True)
    # total = np.prod([len(value) for key, value in kwargs.items()])
    # global pbar
    # pbar = tqdm(desc='Opt runs', leave=True, position=1, unit='run', total=totol)
    # cerebro.optcallback(cb=bt_opt_callback)
    back = cerebro.run(optreturn=False, maxcpus=None)
    '''write into csv file
    final_results_list = []
    with open('params_ATR_2021_08_08.csv', 'w', newline='') as csvfile:
        print('開始寫入')

        writer = csv.writer(csvfile)
        writer.writerow(['sma_slow', 'sma_mid', 'sma_fast', 'atr', 'lowside', 'highside', 'rsi_filter',
                        'k_period', 'd_period', 'rsi_period', 'stoch_period', 'sma_filter', 'Drawd', 'Total trade', 'PnL', 'SQN'])
        for run in back:
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
        print(line)
    '''
    i = 0

    print('sharp ratio : ', back[i].analyzers.sharpe.get_analysis())  # Sharpe

    # Number of Trades
    print('total trade : ', len(back[i].analyzers.trans.get_analysis()) / 2)

    print('sqn score : ', back[i].analyzers.sqn.get_analysis()['sqn'])

    print('max drawd : ', back[i].analyzers.drawd.get_analysis()['max']['drawdown'])
    #     i += 1
    # except:
    #     break

    # print('持幣'+str(1000000*1.507))
    cerebro.plot(style='candle', volume=False,
                 fmt_x_ticks='%Y-%b-%d %H:%M', fmt_x_data='%Y-%b-%d %H:%M')
    print('最终市值', cerebro.broker.getvalue())  # Ending balance

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
