# This file is part of Beach Clean Bay.
#
# This app is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3
#
# The app is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details., see
# <https://www.gnu.org/licenses/>.
#
# Copyright 2022, Julien Moreau, Plastic@Bay CIC

import os
import pandas as pd
# import datashader as DS
import plotly.graph_objects as go
import plotly.io as pio
# from colorcet import fire
# from datashader import transfer_functions as tf
from datetime import datetime, timedelta
# import os.path
# from pyproj import Proj
import dash
from dash import dcc as dcc
from dash import html as html
from dash import dash_table as d_t
from dash import ctx as ctx
import dash_daq as daq
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from flask_caching import Cache

from db import init_db
from layout import *

# mysql> show tables;
# +--------------------------+
# | Tables_in_ocean-plastics |
# +--------------------------+
# | Beach2coord              |
# | Team_members             |
# | WeightData               |
# +--------------------------+

# SELECT * FROM `WeightData` LIMIT 0, 100
#     -> ;
# +----+----------+-----------+---------+----------+--------+------------+--------------+--------+
# | Id | RecordNb | Beach     | Lat     | Longit   | Weight | Dates      | team         | person |
# +----+----------+-----------+---------+----------+--------+------------+--------------+--------+
# |  4 |        0 | Balnakeil | 58.5802 | -4.76575 |    500 | 2017-05-04 | PlasticatBay | Julien |
# |  5 |        0 | Balnakeil | 58.5802 | -4.76575 |    7.4 | 2017-05-08 | PlasticatBay | Julien |
# |  6 |        0 | Balnakeil | 58.5802 | -4.76575 |    6.4 | 2017-05-13 | PlasticatBay | Julien |
# |  7 |        0 | Balnakeil | 58.5802 | -4.76575 |    8.7 | 2017-05-21 | PlasticatBay | Julien |
# |  8 |        0 | Balnakeil | 58.5802 | -4.76575 |   16.8 | 2017-06-06 | PlasticatBay | Julien |
# |  9 |        0 | Balnakeil | 58.5802 | -4.76575 |   14.4 | 2017-06-07 | PlasticatBay | Julien |

# mysql> SELECT * FROM `Team_members` LIMIT 0, 55
#     -> ;
# +----+--------------------------------+--------------+
# | Id | Name                           | Team         |
# +----+--------------------------------+--------------+
# |  1 | moreau.juli1@gmail.com         | PlasticatBay |
# |  2 | julien.moreau@plasticatbay.org | PlasticatBay |
# |  3 | joan.darcy@plasticatbay.org    | PlasticatBay |
# |  4 | conor.drummond@yahoo.co.uk     | PlasticatBay |
# |  5 | catriona.spink@me.com          | OceanGives   |

# mysql> SELECT * FROM `Beach2coord` LIMIT 0, 100
#     -> ;
# +----+-----------------------------+---------+----------+----------+------------+
# | Id | Beach                       | Lat     | Lon      | Country  | State      |
# +----+-----------------------------+---------+----------+----------+------------+
# |  1 | Balnakeil                   | 58.5802 | -4.76575 | Scotland | Sutherland |
# |  2 | Ard Neackie                 | 58.4976 | -4.66321 | Scotland |            |
# |  3 | Keoldale                    | 58.5515 | -4.77859 | Scotland |            |
# |  4 | Kyle of Durness (Old Grudy) | 58.5267 | -4.81157 | Scotland |            |

### color management
pio.templates['custom'] = go.layout.Template(
    layout_paper_bgcolor='#003380',
    layout_plot_bgcolor='#002255',
    layout=dict(xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
                title=dict(font=dict(color='orange'))
                ),    
    )
pio.templates.default = 'plotly+custom'


### app setup
app = dash.Dash(__name__,
               # prevent_initial_callbacks=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP, 'assets/style.css'],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
server=app.server
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': '/tmp'
})
timeout = 300

##################### CACHE  #########################

def global_store():
    print('Using global store')
    engine = init_db()
    with engine.connect() as cnx:
        df= pd.read_sql_table('WeightData', cnx)
        beaches=pd.read_sql_table('Beach2coord', cnx)

    df['Weight']=df['Weight'].astype('float')
    df.Dates=pd.to_datetime(df.Dates)
    grouped = df.groupby(['Beach', 'Lat', 'Longit'])['Weight'].sum().reset_index()
    return df, grouped, beaches

@cache.memoize(timeout=timeout)
def caching():
    return global_store()


def get_beach_data(beach):
    df,_,_=caching()
    df_beach= df[(df==beach).any(axis=1)].sort_values(by=['Dates']) \
                .groupby(['Dates','Lat', 'Longit'])[['Weight']].agg('sum').reset_index()
    last_entry_dates=pd.to_datetime(df_beach['Dates'])[-50:]
    last_entry_weight=df_beach['Weight'][-50:]
    if len(df_beach['Longit'])>0:
        lon,lat=df_beach['Longit'][0],df_beach['Lat'][0]
        last_record= 'Last record in {}:   {} --- {} kg.'.format(
            beach,last_entry_dates.iloc[-1].date(),
            last_entry_weight.iloc[-1] )
    else:
        lon, lat=None, None
        last_record= 'No record'
    summary=go.Figure(go.Scatter(x=last_entry_dates, y=last_entry_weight))
    summary.update_layout(
        height=200,
        title=f'Last 50 records for {beach}',
        margin=dict(b=1, l=1, r=5, t=30),
        yaxis=dict(title='Weight collected (kg)')
    )
    return last_record, summary, lon,lat
    
def mk_beach_dropdown():
    '''
    Get the name of all the beaches and collect them in a dictionary
    '''
    _, grouped,_=caching()
    return grouped['Beach'].array


default_user={'name':'Anonymous'}


app.title="Beach Clean Bay"
header=dcc.Markdown('Beach Clean Bay, _Science with beach and river cleaners_')
app.layout = dbc.Container([
    dcc.Store(id='tab3_map', storage_type='session'),
    dbc.Card([
        dbc.CardHeader([header], className='main-title'),
        ]),
        dbc.CardBody([
            dbc.Tabs([
                dbc.Tab(tab1_content(intro),label='Plastic data',tab_id='tab-main',),
                dbc.Tab(tab2_content(),label='Beach stats',tab_id='tab-curves',),
                dbc.Tab(tab3_content(),label='Submit data',tab_id='tab-submit',),
                dbc.Tab(tab4_content(default_user),label='Your data',tab_id='tab-user',)
                ],
                id="main-tabs",
                active_tab="tab-main",)
            ]),
        dbc.CardFooter([
            footer_content()], className='main-footer')
])




###################### CALLBACKS ##########################
@app.callback(
    Output('team_selection', 'options'),#populate dropdown
    Input('toast', 'is_open'),
    )
def initialise_dropdown(toast):
    if toast:
        df,_,_= caching()
        return df.Teams.explode().unique()

@app.callback(
    Output('year_slider', 'disabled'),
    Input('switch_all_years','on'),
    )
def activate_year(switch):
    return switch
   
@app.callback(
    Output('team_selection', 'disabled'),
    Input('switch_all_teams','on'),
    )
def activate_team(switch):
    return switch
   
@app.callback(
    Output('weight-map', 'figure'),
    Output('Total_Portal','value'),
    Output('Total_sites','value'),
    Output('Total_records','value'),
    Output("curve_trend", 'figure'),
    Input('year_slider', 'value'),# slider year
    Input('switch_all_years', 'on'),# all years
    Input('team_selection', 'value'),#dropdown teams
    Input('switch_all_teams','on'),# all teams
)
def Mk_main_map(year, sw_year, team,sw_team):
   df,_,_= caching()
   if not sw_year:
       df= df[df.Dates.dt.year== year]   
   if not sw_team:
       df= df[df.Teams.apply(lambda x: team in x)]       
   grouped = df.groupby(['Beach', 'Lat', 'Longit'])[['Weight']].agg('sum').reset_index()
   
   return [Mk_map_weight(grouped), 
          round(df['Weight'].sum()), 
          len(grouped), len(df), 
          mk_general_curves(df)]

@app.callback(
    Output('beach-choice', 'options'),
    Output('beach-choice-map', 'options'),
    Input('toast', 'is_open'),
    )
def populate_beach(toast):
    _, grouped,_=caching()
    return grouped['Beach'].array, grouped['Beach'].array

@app.callback(
    Output('beach-statistic', 'figure'),
    Input('beach-choice', 'value'),
    #State('beach-choice', 'value')
)
def update_cum_curve(beach):
    '''
    Make a curve of the cumulative weight collected on a beach
    Calculate the rate of pollution
    '''
    df, _,_=caching()
    df_beach= df[(df==beach).any(axis=1)].sort_values(by=['Dates']) \
                .groupby(['Dates'])[['Weight']].agg('sum').reset_index()
    fig=make_subplots(rows=3, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05)
    if len(df_beach)>1:
        fig= draw_stat_curve(df_beach, fig, beach)        
    else:
        fig.update_layout(
            {"title": {"text": "Only one measure, cannot draw the figure",},
             "font": {"size": 28 }}
        )
    return fig

@app.callback(
    Output('tab3_map','data'),
    Input('toast', 'is_open')
    )
def generate_base_map(toast):
    _, grouped,_=caching()
    return Mk_base_map(grouped)


#check coordinates of the map
@app.callback(
     Output('lat', 'placeholder'),
     Output('lon', 'placeholder'),
     Output('beach_picker', 'figure'),
     Output('recent_records','figure'),
     Output('latest-record','children'),
     Output('selected_beach','children'),
     Output('osmap_link','href'),
     Output('zoom-indicator', 'value'),
     Input('beach_picker','relayoutData'),    
     Input('beach-choice-map', 'value'),
     Input('tab3_map','data'),   
)
def read_coord(stream, beach,state):
    #print(stream['mapbox._derived'])
    if ctx.triggered_id == 'beach-choice-map':
        last_record, fig, lon,lat=get_beach_data(beach)
        state['layout']['mapbox']['center']=dict(
                        lat=lat,
                        lon=lon,)
        state['layout']['mapbox']['zoom']=10
        selection=f'You have selected: {beach}'
        href=f'https://explore.osmaps.com/?lat={lat}&lon={lon}&zoom=14&overlays=&style=Standard&type=2d&placesCategory='
        return lat, lon, state , fig, last_record,selection, href, False         
    else:
        #print('stream: ',stream)
        lat, lon,beachpicker= mk_crossair(stream, state)
        summary= go.Figure()
        summary.update_layout(
            title='no beach selected',
            height=200,
            margin=dict(b=1, l=1, r=1, t=30),
        )
        href=f'https://explore.osmaps.com/?lat={lat}&lon={lon}&zoom=14&overlays=&style=Standard&type=2d&placesCategory='
        if state['layout']['mapbox']['zoom']>11:
            indic=True
        else:
            indic=False
        return  lat, lon,beachpicker, summary, '', 'No beach selected', href,indic 

@app.callback(
    Output('beach-choice-map', 'value'),
    Input('beach_picker','clickData'),
)
def select_from_map(click):
    if click is not None:
        return click['points'][0]['text']
       

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080, debug=True)
