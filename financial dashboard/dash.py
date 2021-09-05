import pandas as pd
import yfinance as yf

from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, DataTable, Select, TableColumn
from bokeh.layouts import layout
from bokeh.plotting import figure

DEFAULT_TICKERS = ['AAPL', 'GOOG', 'MSFT', 'NFLX', 'TSLA']
START, END = '2018-01-01', '2021-01-01'


def load_tickers(tickers):
    df = yf.download(tickers, start=START, end=END)
    return df['Close'].dropna()


def get_data(t1, t2):
    d = load_tickers(DEFAULT_TICKERS)
    df = d[[t1, t2]]
    returns = df.pct_change().add_suffix('_returns')
    df = pd.concat([df, returns], axis=1)
    df.rename(columns={t1: 't1', t2: 't2', f'{t1}_returns': 't1_returns', f'{t2}_returns': 't2_returns'})
    return df.dropna()


def nix(val, lst):
    return [x for x in lst if x != val]


ticker1 = Select(value='AAPL', options=nix('GOOG', DEFAULT_TICKERS))
ticker2 = Select(value='GOOG', options=nix('AAPL', DEFAULT_TICKERS))

# SOURCE DATA
data = get_data(ticker1.value, ticker2.value)
data.to_csv('data.csv')
