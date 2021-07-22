import pandas as pd

from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models.formatters import DatetimeTickFormatter, NumeralTickFormatter


def get_data(path, name):
    df = pd.read_csv(path)
    df.drop(columns='Province/State', inplace=True)
    df.rename(columns={'Country/Region': 'country', 'Lat': 'lat', 'Long': 'long'}, inplace=True)
    df = df.melt(var_name='date', value_name=name, id_vars=['country', 'lat', 'long'])
    df = df.groupby(by=['country', 'date'], as_index=False, sort=False, dropna=False).sum()
    df['id'] = df.country + df.date
    df['date'] = pd.to_datetime(df['date'], format='%m/%d/%y', infer_datetime_format=True)
    return df


def merge_data():
    confirmed = get_data('data/time_series_covid19_confirmed_global.csv', 'confirmed')
    deaths = get_data('data/time_series_covid19_deaths_global.csv', 'deaths')
    recovered = get_data('data/time_series_covid19_recovered_global.csv', 'recovered')

    merged = pd.merge(confirmed, deaths[['id', 'deaths']], on='id', validate='1:1')
    merged = merged.merge(recovered[['id', 'recovered']], on='id', validate='1:1')
    merged.drop(columns='id', inplace=True)
    return merged


covid_df = merge_data()

fig = figure()
x = covid_df['date']
y = covid_df['confirmed']
fig.line(x=x, y=y)
fig.xaxis.formatter = DatetimeTickFormatter()
fig.yaxis.formatter = NumeralTickFormatter(format='0a')


document = curdoc()
document.add_root(fig)
