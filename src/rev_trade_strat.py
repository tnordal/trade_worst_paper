"""rev_trade_strat.py
    Version: 1.0
"""

import os

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

from config import (
    STOCK_DATA,
    TICKER_FILES
)

plt.style.use('fivethirtyeight')



def stock_list(csv_file):
    stocks_ = pd.read_csv(csv_file, header=None)
    return stocks_[0].to_list()

def download_stocks(tickers, start=None, end=None):
    df = yf.download(tickers=tickers, start=start, end=end)
    df.to_csv(os.path.join(STOCK_DATA, 'stock_data_trade.csv'))
    return df

def remove_zero_volume(df: pd.DataFrame, last_rows: int=-20):
    df_volume = df['Volume']
    last_volume = df_volume.iloc[last_rows:]
    tickers = []
    for col in last_volume:
        n = len(last_volume[last_volume[col] == 0])
        if n == 0:
            tickers.append(col)
    return df.loc(axis=1)[:, tickers]
    

def periodic_return(df, period='M'):
    df.index = pd.to_datetime(df.index)
    # Calc daily return
    ret_df = df.pct_change()

    # Cumulate daily return to period (monthly)
    per_ret_ = (ret_df + 1).resample(period).prod()
    return per_ret_

def worst_performers(per_data, date, n, m=10):
    all_ = per_data.loc[date]
    worst_all = all_.nsmallest(m)
    worst = worst_all.nlargest(n)
    # print(worst.index)
    relevant_ret = per_data[worst.name:][1:2][worst.index]
    return relevant_ret.mean(axis=1).values[0]

def tickers_worst_performers(data, date, n, m=10):
    all_ = data.loc[date]
    worst_all = all_.nsmallest(m)
    worst = worst_all.nlargest(n)
    tickers = worst.index.to_list()
    return tickers

def plot_performing(s, cumret, paper):
    plt.figure(figsize=(10, 7))
    plt.plot(s, 'b--')
    plt.autoscale(enable=True)

    cumform = f"{round(cumret, 2)}"

    plt.title(f"Cumulative return: {cumform}")
    plt.ylabel('Cumulative')
    plt.annotate(
        f"Next papers to buy: {paper}", xy=(.5,.98),
        xycoords='figure fraction',
        horizontalalignment='center',
        verticalalignment='top',
        fontsize=16
    )
    plt.show()

def return_worst_performers(per_data, n_stocks):
    returns = []
    for date in per_data.index[:-1]:
        returns.append(worst_performers(per_data, date, n_stocks))
    ret = pd.Series(returns).prod()
    return ret, pd.Series(returns, index=per_data.index[:-1]).cumprod()

def main(csv_file=None, start=None, end=None, n_stocks=3):
    stocks_raw = stock_list(os.path.join(TICKER_FILES, 'oslo_all.csv'))
    if csv_file:
        df = pd.read_csv(os.path.join(STOCK_DATA, csv_file), header=[0,1], index_col=0)
    else:
        df = download_stocks(stocks_raw, start=start, end=end)

    filtered_df = remove_zero_volume(df=df, last_rows=-30)
    print(len(df['Close'].columns))
    print(len(filtered_df['Close'].columns))
    periodic_data = periodic_return(df=filtered_df['Close'], period='W-FRI')
    ret, cum = return_worst_performers(per_data=periodic_data, n_stocks=n_stocks)

    papers_ = tickers_worst_performers(periodic_data, periodic_data.index[-1], n_stocks)

    papers = ""
    for p in papers_:
        papers += p + ", "

    print(f"Cumulative return: {ret}")
    print(f"Next paper to buy {papers_}")

    plot_performing(
        cum,
        ret,
        papers
    )

if __name__ == '__main__':
    # main('stock_data_trade.csv', n_stocks=3)
    main(start='2023-01-01', n_stocks=3)
