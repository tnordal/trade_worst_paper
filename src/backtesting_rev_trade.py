"""backtesting_rev_trade.py

    Version: 0.31

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

from pathlib import Path
from os.path import dirname
from os.path import join
import logging
import pandas as pd
import yfinance as yf

from rev_trade_strat import remove_zero_volume
from rev_trade_strat import periodic_return
from rev_trade_strat import tickers_worst_performers

from config import (
    STOCK_DATA,
    TICKER_FILES,
    REPORTS_DIR
)

logger = logging.getLogger('backtesting_rev_trade')
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.FileHandler('backtesting_rev_trade.log')
fh.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# add the handlers to logger
logger.addHandler(ch)
logger.addHandler(fh)


def stock_list(csv_file: str) -> list:
    stocks_ = pd.read_csv(csv_file, header=None)
    return stocks_[0].to_list()


def download_stocks(
        tickers: list, start: str=None, end: str=None
) -> pd.DataFrame:
    _df = yf.download(tickers=tickers, start=start, end=end)
    _df.to_csv(join(STOCK_DATA,  'stock_data.csv'))
    _df.to_parquet(join(STOCK_DATA, 'stock_data.prq'))
    return _df


def read_data_file(prq_file: str=None, csv_file: str=None) -> pd.DataFrame:
    if prq_file:
        _df = pd.read_parquet(path=prq_file)  # , header=[0,1], index_col=0)
    else:
        _df = pd.read_csv(csv_file, header=[0, 1], index_col=0)
    return _df


def get_number_tot(price: float, amount: float, cost: float=0):
    num = round(amount/price)
    tot = num * price + cost
    return num, tot


def trade_dict_buy(paper_prices: pd.Series, date: str, invest: float=10000) -> list:
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


def trade_dict_sell(paper_prices: pd.Series, paper_number: dict, date: str):
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
    papers = stock_list(join(TICKER_FILES, 'oslo_all.csv'))
    download_stocks(papers, start='2023-01-01')
    df = read_data_file(prq_file=join(STOCK_DATA, 'stock_data.prq'))
    df['Close'].to_csv(join(STOCK_DATA, 'stock_data.csv'))
    filtered_df = remove_zero_volume(df=df, date='2023-03-31')
    per_ret = periodic_return(df=filtered_df['Close'], period='W-FRI')
    df_open = df['Open']

    trades_df = pd.DataFrame()
    buy_serie = pd.Series()
    last_df = pd.DataFrame()
    return_trades = list()
    for date in per_ret.index:
        if not date == per_ret.index[-1]:
            if len(buy_serie) == 0:
                next_papers_to_buy = tickers_worst_performers(per_ret, date, n=3, m=10)
                buy_serie = df_open.loc[df_open.index > date].head(1)[next_papers_to_buy].squeeze()
                last_df = pd.DataFrame(trade_dict_buy(buy_serie, date))
                trades_df = pd.concat([trades_df, last_df])
                return_trades.append({'date': date, 'return': 10000*3})
                logger.debug("First Buy: %s", len(trades_df))
            else:
                # Sell last_df
                last_df_sell = last_df[['paper', 'number']]
                last_df_sell.set_index('paper', inplace=True)
                sell_serie = df_open.loc[df_open.index > date].head(1)[last_df_sell.index].squeeze()
                last_df_sell, return_trade = trade_dict_sell(
                    sell_serie, last_df_sell.to_dict()['number'],
                    date
                )
                last_df_sell = pd.DataFrame(last_df_sell)
                trades_df = pd.concat([trades_df, last_df_sell])
                return_trades.append({'date': date, 'return': return_trade})
                logger.debug("Sell: %s", len(trades_df))

                # Buy Next paper
                next_papers_to_buy = tickers_worst_performers(per_ret, date, n=3, m=10)
                buy_serie = df_open.loc[df_open.index > date] \
                    .head(1)[next_papers_to_buy].squeeze()
                last_df = pd.DataFrame(
                    trade_dict_buy(buy_serie, date, round(return_trade/3))
                )
                trades_df = pd.concat([trades_df, last_df])
                logger.debug("Buy: %s", len(trades_df))


    pd.DataFrame(return_trades).to_csv(join(REPORTS_DIR, 'total_returns.csv'))
    trades_df.reset_index(inplace=True)
    trades_df.drop(trades_df.columns[0], inplace=True, axis=1)
    trades_df.to_csv(join(REPORTS_DIR, 'backtesting_trades.csv'))
    logger.info('Finish')


if __name__ == '__main__':
    test_01()
