"""backtesting_rev_trade.py

    Version: 0.1

    Backtesting strategy
    ---------------------
    1. Find next 3-5 worst paper to invest based on closing price.
    2. Buy on opening price next exchange day (mondays if weekly).
    3. Sell on opening price next exchange day (mondays if weekly).
    4. Calculate win/loss plus cost for each trade
    5. Calculate accumulated win/loss

    Programming tasks
    ------------------
    * Find next exchange day
    * Make a dataframe with periodic returns (Closing price).
    * Find the opening price for the paper to sell.
    * Find opening price for the new paper to buy.
    * Download the daily prices for the backtesting period.
    * Save daily prices to csv (or an other type).

"""

import logging
import pandas as pd
import yfinance as yf

from rev_trade_strat import remove_zero_volume
from rev_trade_strat import periodic_return
from rev_trade_strat import tickers_worst_performers


logger = logging.getLogger('backtesting_rev_trade')
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.FileHandler('backtesting_rev_trade.log')
fh.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# add the handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)

def stock_list(csv_file):
    stocks_ = pd.read_csv(csv_file, header=None)
    return stocks_[0].to_list()


def download_stocks(tickers, start=None, end=None):
    _df = yf.download(tickers=tickers, start=start, end=end)
    _df.to_csv('stock_data.csv')
    _df.to_parquet('stock_data.prq')
    return _df


def read_data_file(prq_file=None, csv_file=None):
    if prq_file:
        _df = pd.read_parquet(path=prq_file)  # , header=[0,1], index_col=0)
    else:
        _df = pd.read_csv(csv_file, header=[0, 1], index_col=0)
    return _df


def get_number_tot(price, amount, cost=0):
    num = round(amount/price)
    tot = num * price + cost
    return num, tot


def trade_dict_buy(paper_prices, date, invest=10000):
    trades = list()
    for key, value in paper_prices.items():
        trade = dict()
        trade['date'] = date
        trade['action'] = 'buy'
        trade['paper'] = key
        trade['price'] = value
        num, tot = get_number_tot(value, invest)
        trade['number'] = num
        trade['total'] = tot
        trades.append(trade)
    return trades


def trade_dict_sell(paper_prices, paper_number, date):
    trades = list()
    tot_return = 0
    for key, value in paper_prices.items():
        trade = dict()
        trade['date'] = date
        trade['action'] = 'sell'
        trade['paper'] = key
        trade['number'] = paper_number[key]
        trade['price'] = value
        trade['total'] = value * paper_number[key]

        trades.append(trade)
        tot_return += trade['total']

    return trades, tot_return


def test_01():
    # papers = stock_list('./ticker_lists/oslo_all.csv')
    # download_stocks(papers, start='2023-01-01')
    df = read_data_file(prq_file='stock_data.prq')
    filtered_df = remove_zero_volume(df=df, resample=None)
    per_ret = periodic_return(df=filtered_df['Close'], period='W-FRI')
    df_open = df['Open']

    trades_df = pd.DataFrame()
    buy_serie = pd.Series()
    last_df = pd.DataFrame()
    for date in per_ret.index:
        if not date == per_ret.index[-1]:
            if len(buy_serie) == 0:
                next_papers_to_buy = tickers_worst_performers(
                    per_ret, date, n=3, m=10)
                buy_serie = df_open.loc[df_open.index > date].head(
                    1)[next_papers_to_buy].squeeze()
                last_df = pd.DataFrame(trade_dict_buy(buy_serie, date))
                trades_df = pd.concat([trades_df, last_df])
                logger.debug("First Buy: %s", len(trades_df))
            else:
                # Sell last_df
                last_df_sell = last_df[['paper', 'number']]
                last_df_sell.set_index('paper', inplace=True)
                sell_serie = df_open.loc[df_open.index > date].head(
                    1)[last_df_sell.index].squeeze()
                last_df_sell, return_trade = trade_dict_sell(
                    sell_serie, last_df_sell.to_dict()['number'], date)
                last_df_sell = pd.DataFrame(last_df_sell)
                trades_df = pd.concat([trades_df, last_df_sell])
                logger.debug("Sell: %s", len(trades_df))

                # Buy Next paper
                next_papers_to_buy = tickers_worst_performers(
                    per_ret, date, n=3, m=10)
                buy_serie = df_open.loc[df_open.index > date].head(
                    1)[next_papers_to_buy].squeeze()
                last_df = pd.DataFrame(trade_dict_buy(
                    buy_serie, date, round(return_trade/3)))
                trades_df = pd.concat([trades_df, last_df])
                logger.debug("Buy: %s", len(trades_df))

    trades_df.to_csv('backtesting_trades.csv', index='date')


if __name__ == '__main__':
    test_01()
