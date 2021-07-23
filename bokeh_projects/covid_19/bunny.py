import pandas as pd

from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import (
    Div, SingleIntervalTicker, DatetimeTickFormatter, NumeralTickFormatter, DateRangeSlider, ColumnDataSource
)
from bokeh.layouts import layout


def _get_data(path, name):
    df = pd.read_csv(path)
    df.drop(columns='Province/State', inplace=True)
    df.rename(columns={'Country/Region': 'country', 'Lat': 'lat', 'Long': 'long'}, inplace=True)
    df = df.melt(var_name='date', value_name=name, id_vars=['country', 'lat', 'long'])
    df = df.groupby(by=['country', 'date'], as_index=False, sort=False, dropna=False).sum()
    df['id'] = df.country + df.date
    df['date'] = pd.to_datetime(df['date'], format='%m/%d/%y', infer_datetime_format=True)
    return df


def _merged_data():
    confirmed = _get_data('data/time_series_covid19_confirmed_global.csv', 'confirmed')
    deaths = _get_data('data/time_series_covid19_deaths_global.csv', 'deaths')
    recovered = _get_data('data/time_series_covid19_recovered_global.csv', 'recovered')

    merged = pd.merge(confirmed, deaths[['id', 'deaths']], on='id', validate='1:1')
    merged = merged.merge(recovered[['id', 'recovered']], on='id', validate='1:1')
    merged.drop(columns='id', inplace=True)
    return merged


def line_fig(label, interval, **kwargs):
    fig = figure(
        plot_width=400,
        plot_height=250,
        background_fill_color='#222222',
        y_axis_label=label,
        border_fill_color='#222222',
        outline_line_color='#222222',
        # output_backend="webgl",
        #     sizing_mode="stretch_width",
        **kwargs
    )

    # Fig
    fig.toolbar_location = None
    fig.tools = []

    # Axis
    fig.axis.major_label_text_color = '#bdbdbd'
    fig.axis.major_tick_line_color = '#5c5c5c'
    fig.axis.major_tick_in = 0
    fig.axis.minor_tick_line_color = None
    fig.axis.axis_label_text_color = '#bdbdbd'
    fig.axis.axis_line_color = "#5c5c5c"

    # X-Axis
    fig.xgrid.grid_line_color = "#5c5c5c"
    fig.xgrid.grid_line_width = 1
    fig.xgrid.grid_line_alpha = 0.4
    fig.xgrid.grid_line_dash = [3, 9]

    fig.xaxis.formatter = DatetimeTickFormatter(months="%b %Y")

    # Y-Axis
    fig.ygrid.grid_line_color = "#5c5c5c"
    fig.ygrid.grid_line_width = 1
    fig.ygrid.grid_line_alpha = 0.4
    fig.ygrid.grid_line_dash = [3, 9]

    # fig.yaxis.ticker = SingleIntervalTicker(interval=interval)
    fig.yaxis.formatter = NumeralTickFormatter(format='0a')

    return fig


source = _merged_data()
datacache = ColumnDataSource(source)

style = """
    <style>
        html {
            margin: 0;
            padding: 0;
            background: #222222;
        }
    </style>
"""
style_div = Div(text=style)


def make_chart(label, x, y, interval, **kwargs):
    chart = line_fig(
        label,
        interval=interval,
        # y_range=(0, datacache.data[y].max()),
        # x_range=(datacache.data['date'].min(), datacache.data['date'].max())
    )
    chart.line(x=x, y=y, source=datacache, **kwargs)
    return chart


date = datacache.data['date']
start_date = date.min()
end_date = date.max()
date_slider = DateRangeSlider(start=start_date,
                              end=end_date,
                              value=(start_date, end_date),
                              step=1,
                              show_value=False,
                              default_size=400)
del date


def date_slider_callback(attr, old, new):
    old = pd.to_datetime(date_slider.value_as_date[0], infer_datetime_format=True)
    new = pd.to_datetime(date_slider.value_as_date[1], infer_datetime_format=True)

    cache = source[(source['date'] >= old) & (source['date'] <= new)]
    datacache.data = ColumnDataSource.from_df(cache)


date_slider.on_change('value', date_slider_callback)

confirmed_chart = make_chart('Confirmed Cases', 'date', 'confirmed', interval=10000000.00, color='#D83020')
death_chart = make_chart('Confirmed Deaths', 'date', 'deaths', interval=300000.00, color='#eaeaea')
recovery_chart = make_chart('Confirmed Recovery', 'date', 'recovered', interval=10000000.00, color='#35ac46')

lay_out = layout(
    children=[
        [date_slider],
        [confirmed_chart],
        [death_chart],
        [recovery_chart]
    ]
)

document = curdoc()
# document.add_root(style_div)
document.add_root(lay_out)
