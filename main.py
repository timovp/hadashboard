import numpy as np
import pandas as pd
import json
import sqlite3
from pathlib import Path
import time 
import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

folder  = Path('/dbfolder')
db_file = folder / 'home-assistant_v2.db'

def load_db(db_file):
    # global daterange
    # global min_date
    # global max_date
    cnxn    = sqlite3.connect(database=db_file)
    df       = pd.read_sql(   con = cnxn, 
                        sql='SELECT entity_id, state, last_changed FROM states WHERE entity_id = "sensor.slaapkamer_sensor_temperature" or entity_id = "sensor.werkkamer_sensor_temperature" or entity_id = "sensor.woonkamer_sensor_temperature"', 
                        parse_dates=['last_changed']
                    )
    df = df[df.state!= 'unknown']
    daterange = df['last_changed']
    min_date = min(df['last_changed'])
    max_date = max(df['last_changed'])
    print('i just reloaded the db')
    return df, min_date, max_date,daterange

df,min_date,max_date,daterange = load_db(db_file)


list_of_entities= df.entity_id.unique()
pretty_names    = ['Slaapkamer','Werkkamer','Woonkamer']
name_dict       = dict(zip(list_of_entities,pretty_names))



def make_slider_filter(min_date,max_date):
    df, dontuse,dontuse2,daterange = load_db(db_file)
    slider_filter = dict()
    temp = dict()
    for i in list_of_entities:
        temp[i] = df.entity_id==i
        slider_filter[i]    = (df['last_changed'] > min_date) & (df['last_changed'] < max_date) & temp[i]
    return slider_filter

def unixTimeMillis(dt):
    ''' Convert datetime to unix timestamp '''
    return int(time.mktime(dt.timetuple()))

def unixToDatetime(unix):
    ''' Convert unix timestamp to datetime. '''
    return pd.to_datetime(unix,unit='s')

def getMarks(start, end, Nth=1):
    ''' Returns the marks for labeling. 
        Every Nth value will be used.
    '''
    result = {}
    for i, date in enumerate(daterange):
            # Append value to dict
            if str(date.strftime('%m-%d')) not in result.values():
                result[unixTimeMillis(date)] = str(date.strftime('%m-%d'))
    return result

def make_fig(df, slider_filter,name_dict,list_of_entities):
    fig_slaapkamer = go.Figure(data =  [go.Scatter( 
                                                    x   = df[slider_filter[i]]['last_changed'],
                                                    y   = df[slider_filter[i]]['state'],
                                                    name= name_dict[i],
                                                )
                                    for i in list_of_entities],
                                layout = {'legend_orientation': 'h'})
    return fig_slaapkamer

go.Figure()
# initial figure and slider at startup
slider_filter = make_slider_filter(min_date,max_date) #df['last_changed'] == df['last_changed']

fig_slaapkamer = make_fig(df, slider_filter,name_dict,list_of_entities)

app = dash.Dash()
app.css.config.serve_locally = False
app.scripts.config.serve_locally = False

app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

def serve_layout():
    df,min_date,max_date,daterange = load_db(db_file)
    slider_filter = make_slider_filter(min_date,max_date)
    fig_slaapkamer = make_fig(df, slider_filter, name_dict,list_of_entities)
    return  html.Div(children=  [
                                html.Div(
                                    [
                                        dcc.Graph(id = 'grafiek_slaapkamer',figure = fig_slaapkamer),
                                        dcc.RangeSlider(    
                                            id      ='year_slider',
                                            min     = unixTimeMillis(daterange.min()),
                                            max     = unixTimeMillis(daterange.max()),
                                            value   =   [   
                                                            unixTimeMillis(daterange.min()),
                                                            unixTimeMillis(daterange.max())
                                                        ],
                                            marks   = getMarks(daterange.min(),
                                                        daterange.max()),
                                        ),
                                        html.Button(id='reset', children='Reset',n_clicks=0),
                                        html.Button(id='set_72h', children='last 72h',n_clicks=0),
                                        html.Button(id='set_24h', children='last 24h',n_clicks=0),
                                    ]),
                                ])

app.layout = serve_layout

@app.callback(dash.dependencies.Output('grafiek_slaapkamer', 'figure'),
              [dash.dependencies.Input('year_slider', 'value')])
def _update_time_range_label(year_range):#,n_clicks,n_clicks2):
    ctx = dash.callback_context
    df,min_date,max_date,daterange = load_db(db_file)

    if not ctx.triggered:        
        #takes the 'value' and enters it into this function as year_range
        slider_filter = make_slider_filter(unixToDatetime(year_range[0]),unixToDatetime(year_range[1]))
        fig_slaapkamer = make_fig(df, slider_filter,name_dict,list_of_entities)
    if ctx.triggered[0]['value'] == 0:
        slider_filter   = make_slider_filter(unixToDatetime(year_range[0]),unixToDatetime(year_range[1]))
        fig_slaapkamer  = make_fig(df, slider_filter,name_dict,list_of_entities)
    elif ctx.triggered[0]['prop_id'] == 'set_24h.n_clicks':
        print(ctx.triggered)
        #takes the 'value' and enters it into this function as year_range
        slider_filter   = make_slider_filter(max_date-datetime.timedelta(1),max_date)
        fig_slaapkamer  = make_fig(df, slider_filter,name_dict,list_of_entities)
    elif ctx.triggered[0]['prop_id'] == 'set_72h.n_clicks':
        slider_filter   = make_slider_filter(max_date-datetime.timedelta(3),max_date)
        fig_slaapkamer  = make_fig(df, slider_filter,name_dict,list_of_entities)
    else:
        slider_filter   = make_slider_filter(unixToDatetime(year_range[0]),unixToDatetime(year_range[1]))
        fig_slaapkamer  = make_fig(df, slider_filter,name_dict,list_of_entities)
    return fig_slaapkamer

@app.callback(dash.dependencies.Output('year_slider', 'value'),
              [dash.dependencies.Input('set_24h', 'n_clicks')
              ,dash.dependencies.Input('set_72h','n_clicks')
              ,dash.dependencies.Input('reset','n_clicks')])
def _update_slider(n_clicks,n_clicks2,n_clicks3):
    global df 
    df,min_date,max_date,daterange = load_db(db_file)
    year_range = [None,None]
    ctx = dash.callback_context
    if not ctx.triggered:
        print(ctx.triggered)
        # normal first render
        year_range[0] = unixTimeMillis(min_date)
        year_range[1] = unixTimeMillis(max_date)
    if ctx.triggered[0]['value'] == 0:
        print(ctx.triggered)

        year_range[0] = unixTimeMillis(min_date)
        year_range[1] = unixTimeMillis(max_date)
        # normal first render
    elif ctx.triggered[0]['prop_id'] == 'set_24h.n_clicks':
        print(ctx.triggered)
        #takes the 'value' and enters it into this function as year_range
        year_range[0] = unixTimeMillis(max_date-datetime.timedelta(1))
        year_range[1] = unixTimeMillis(max_date)
    elif ctx.triggered[0]['prop_id'] == 'set_72h.n_clicks':
        year_range[0] = unixTimeMillis(max_date-datetime.timedelta(3))
        year_range[1] = unixTimeMillis(max_date)
    elif ctx.triggered[0]['prop_id'] == 'reset.n_clicks':
        year_range[0] = unixTimeMillis(min_date)
        year_range[1] = unixTimeMillis(max_date)
    
    return year_range



if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port = 8050,debug=True)
