import pandas as pd

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.models.formatters import NumeralTickFormatter
from bokeh.models import Span, Slider, Label, HoverTool, Div, ResetTool
from bokeh.models.tickers import SingleIntervalTicker
from bokeh.models.widgets import DataTable, TableColumn, NumberFormatter
from bokeh.io import curdoc
from bokeh.layouts import layout, Column


def millions_formatter(n):
    millions = round(n / 1000000, 2)
    return f'${millions}M'


def get_data():
    overview = pd.read_excel('data.xlsx')
    overview.drop(columns=[
        'Unnamed: 9', 'Unnamed: 10',
        'Unnamed: 11', 'Unnamed: 12', 'Unnamed: 13', 'Unnamed: 14',
        'Unnamed: 15', 'Unnamed: 16', 'Unnamed: 17', 'Unnamed: 18',
        'Unnamed: 19', 'Unnamed: 20', 'Unnamed: 21', 'Unnamed: 22'
    ], inplace=True)
    financials = pd.read_excel('data.xlsx', sheet_name=1)
    financials.drop(columns=['Unnamed: 13', 'Unnamed: 14', 'Unnamed: 15', 'Unnamed: 16'], inplace=True)
    df = pd.merge(overview, financials, on=['ID', 'Name'], validate='1:1')
    df.dropna(inplace=True)
    df.columns = map(lambda x: x.lower().replace(' ', '_'), df.columns)
    df.rename(columns={'2015_growth_%': '2015_growth'}, inplace=True)
    return df[['id', 'name', 'industry', 'description', 'year_founded', 'employees',
               'state', 'city', 'metro_area', '2015_revenue', '2015_expenses',
               '2015_profit', '2015_growth']]


def set_color(df):
    tq, t = df['target_quadrant'], df['target']
    if t:
        return '#C65E69'
    elif tq:
        return '#4E79A7'
    return '#ACA899'


def rev_slider_cb(attr, old, new):
    rev_thresh = new
    exp_thresh = exp_cutoff_slider.value
    growth = growth_cuttoff_slider.value
    revenue_reference_line.location = rev_thresh
    # expense_reference_line.location = exp_thresh
    rev_sl_lb.x = rev_thresh
    rev_sl_lb.text = millions_formatter(rev_thresh)
    data_cache = get_data_cache(rev_thresh, exp_thresh, growth)
    source.data = ColumnDataSource.from_df(data_cache)


def exp_slider_cb(attr, old, new):
    rev_thresh = rev_cutoff_slider.value
    exp_thresh = new
    growth = growth_cuttoff_slider.value
    # revenue_reference_line.location = rev_thresh
    exp_sl_lb.y = exp_thresh
    exp_sl_lb.text = millions_formatter(exp_thresh)
    expense_reference_line.location = exp_thresh
    data_cache = get_data_cache(rev_thresh, exp_thresh, growth)
    source.data = ColumnDataSource.from_df(data_cache)


def growth_slider_cb(attr, old, new):
    rev_thresh = rev_cutoff_slider.value
    exp_thresh = exp_cutoff_slider.value
    growth = new
    data_cache = get_data_cache(rev_thresh, exp_thresh, growth)
    source.data = ColumnDataSource.from_df(data_cache)


def make_fig():
    fig = figure(
        plot_width=800,
        plot_height=600,
        y_axis_label='Expenses',
        x_axis_label='Revenue',
        x_range=(0, source.data['2015_revenue'].max() + 1000000),
    )

    hover = HoverTool(tooltips="""
        <div>
            <div>
                <span style="font-size: 14px; font-weight: bold;">@name</span>
            </div>
            <div>
                <span style="font-size: 13px; color: black; font-weight: bold;">Industry: </span>
                <span style="font-size: 13px;">@industry</span><br>

                <span style="font-size: 13px; color: black; font-weight: bold;">Year Founded: </span>
                <span style="font-size: 13px;">@year_founded</span><br>

                <span style="font-size: 13px; color: black; font-weight: bold;">2015 Revenue: </span>
                <span style="font-size: 13px;">@2015_revenue{$0.0a}</span><br>

                <span style="font-size: 13px; color: black; font-weight: bold;">2015 Expenses: </span>
                <span style="font-size: 13px;">@2015_expenses{$0.0a}</span><br>

                <span style="font-size: 13px; color: black; font-weight: bold;">2015 Growth: </span>
                <span style="font-size: 13px;">@2015_growth{0%}</span><br>

                <span style="font-size: 13px; color: black; font-weight: bold;">Summary: </span>
                <span style="font-size: 13px;">@description</span><br>
            </div>
        </div>
    """)
    fig.tools = [ResetTool()]
    fig.toolbar.logo = None
    fig.add_tools(hover)
    fig.scatter(source=source, x='2015_revenue', y='2015_expenses', size='size', alpha=0.85, marker='marker',
                color='color')

    fig.axis.minor_tick_line_color = None
    fig.axis.major_tick_in = 0
    fig.axis.major_label_text_color = '#646464'
    fig.axis.major_tick_line_color = "#e5e5e5"
    fig.axis.major_tick_line_alpha = 0.3
    fig.axis.major_label_text_font_size = '13px'
    fig.axis.axis_line_color = "#e5e5e5"
    fig.axis.axis_label_text_font_size = '14px'
    fig.axis.axis_label_text_font_style = 'bold'

    fig.yaxis.formatter = NumeralTickFormatter(format='0a')
    fig.y_range.flipped = True
    fig.ygrid.grid_line_width = 1
    fig.ygrid.grid_line_alpha = 0.4

    fig.xaxis.formatter = NumeralTickFormatter(format='0a')
    fig.xaxis.ticker = SingleIntervalTicker(interval=2000000)
    fig.xgrid.grid_line_width = 1
    fig.xgrid.grid_line_alpha = 0.4
    return fig


def get_data_cache(rev_thresh, exp_thresh, growth_thresh):
    df = original_source.copy()
    df['revenue_cutoff'] = df['2015_revenue'] > rev_thresh
    df['expense_cutoff'] = df['2015_expenses'] < exp_thresh
    df['target_quadrant'] = (df['revenue_cutoff'] == True) & (df['expense_cutoff'] == True)
    top_growth = df.nlargest(growth_thresh, columns='2015_growth')
    df['top_growth'] = df['id'].isin(top_growth['id'])
    df['target'] = (df['target_quadrant'] == True) & (df['top_growth'] == True)
    df['marker'] = df['target'].apply(lambda x: 'diamond' if x else 'circle')
    df['color'] = df[['target_quadrant', 'target']].apply(set_color, axis=1)
    df['size'] = df['marker'].apply(lambda x: 11 if x == 'circle' else 15)
    return df.sort_values(by='2015_growth', ascending=False)


original_source = get_data()
source = ColumnDataSource(get_data_cache(9000000, 5000000, 50))

rev_sl_end = int(source.data['2015_revenue'].max())
rev_cutoff_slider = Slider(start=0, end=rev_sl_end, value=9000000, step=100000, title="Revenue Cutoff",
                           format='($0.0a)', width=210)
exp_sl_end = int(source.data['2015_expenses'].max())
exp_cutoff_slider = Slider(start=0, end=exp_sl_end, value=5000000, step=100000, title="Expenses Cutoff",
                           format='($0.0a)', width=210)
growth_sl_end = len(source.data['id'])
growth_cuttoff_slider = Slider(start=0, end=growth_sl_end, value=20, title='Top Growth Cuttoff', width=210)

exp_thresh, rev_thresh = exp_cutoff_slider.value, rev_cutoff_slider.value

revenue_reference_line = Span(location=rev_thresh, dimension='height', line_color='black',
                              line_width=2, line_alpha=0.4)
expense_reference_line = Span(location=exp_thresh, dimension='width', line_color='black',
                              line_width=2, line_alpha=0.4)
rev_sl_lb = Label(x=rev_thresh, y=source.data['2015_expenses'].max(), x_offset=5, text=millions_formatter(rev_thresh))
exp_sl_lb = Label(x=0, y=exp_thresh, y_offset=5, x_offset=5, text=millions_formatter(exp_thresh))
columns = [
    TableColumn(field="name", title="Company", width=150),
    TableColumn(field="2015_growth", title="2015 Growth",
                formatter=NumberFormatter(format='0%', text_align='right'), width=60),
]
data_table = DataTable(source=source, columns=columns, sortable=False, index_position=None, fit_columns=True, width=210)

fig = make_fig()
fig.add_layout(revenue_reference_line)
fig.add_layout(expense_reference_line)
fig.add_layout(rev_sl_lb)
fig.add_layout(exp_sl_lb)

rev_cutoff_slider.on_change('value_throttled', rev_slider_cb)
exp_cutoff_slider.on_change('value_throttled', exp_slider_cb)
growth_cuttoff_slider.on_change('value_throttled', growth_slider_cb)

lay_out = layout(
    children=[
        [fig, Column(rev_cutoff_slider, exp_cutoff_slider, growth_cuttoff_slider, data_table)]
    ]
)

style = Div(text="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>The Startup Quadrant</title>
    <style>
        html {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        .bk {
            font-family: inherit;
            font-size: 12px !important;
        }
        
        .bk-root .slick-column-name, .bk-root .slick-sort-indicator {
            display: inline-block;
            margin-bottom: 100px;
            font-weight: bold;
            font-size: 12px;
            text-align: center !important;
            float: inline-start !important;
        }
        
        .bk-root .bk-slider-title {
            font-weight: bold;
        }
    </style>
</head>
<body>

</body>
</html>
""")

document = curdoc()
document.add_root(style)
document.add_root(lay_out)
