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
from colorcet import fire
# from datashader import transfer_functions as tf
from datetime import datetime, timedelta
# import os.path
# from pyproj import Proj
import dash
from dash import dcc as dcc
from dash import html as html
from dash import dash_table as d_t
import dash_daq as daq
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from flask_caching import Cache

from db import init_db


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

app = dash.Dash(__name__,
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
    grouped = df.groupby(['Beach', 'Lat', 'Longit'])[['Weight']].agg('sum').reset_index()
    return df, grouped, beaches

@cache.memoize(timeout=timeout)
def caching():
    return global_store()

#################### FIGURES ##########################

def Mk_map_weight():
    '''
    Make a map of plastic accumulations
    '''
    _,grouped,_=caching() 
    plastic_map=go.Figure(go.Scattermapbox(
                     lon=grouped['Longit'],
                     lat=grouped['Lat'],
                     text=grouped['Beach'],
                     hovertemplate=
                    "<b>%{text}</b><br><br>" +
                    "Weight: %{marker.size:.2f}<br>",
                     marker=dict(
                            size=grouped['Weight'].values.astype('float'),
                            color='orange',
                            sizemode='area',
                            sizeref=10)))

    plastic_map.update_layout(
        #height=700,
        hovermode='closest',
        margin=dict(b=1, l=1, r=1, t=1),
        mapbox=dict(
                    bearing=0,
                    center=dict(
                        lat=55,
                        lon=-3,
                    ),
                    pitch=0,
                    zoom=4,
                    style="stamen-toner",))
    return plastic_map


def Mk_base_map():
    _, grouped,_=caching()
    base_map=go.Figure()
    base_map.add_trace(go.Scattermapbox(lon=grouped['Longit'],
                     lat=grouped['Lat'],
                     text=grouped['Beach'],
                     mode='markers')
                       )

    base_map.update_layout(
        height=300,
        width=300,
        hovermode='closest',
        showlegend=False,
        margin=dict(b=1, l=1, r=1, t=1),
        mapbox=dict(
                    bearing=0,
                    center=dict(
                        lat=55,
                        lon=-3,
                    ),
                    pitch=0,
                    zoom=4,
                    style="open-street-map",))
   # base_map=mk_crossair(base_map)
    base_map.add_trace(go.Scattermapbox())
    base_map.add_trace(go.Scattermapbox())
                  
    return base_map

def mk_crossair(stream, fig):
    '''
    Make a crossair in the middle of the map to locate precisely.
    '''
    center=stream['mapbox.center']
    width=stream['mapbox._derived']['coordinates'][0][0]-stream['mapbox._derived']['coordinates'][1][0]
    height=stream['mapbox._derived']['coordinates'][0][1]-stream['mapbox._derived']['coordinates'][2][1]
    color='black'
    
    # vertical
    fig['data'][1]=go.Scattermapbox(
        lon=[center['lon'],center['lon']],
        lat=[center['lat']-0.1*height,center['lat']+0.1*height],
        mode='lines',
        marker={'color':color},
    )
    # horizontal
    fig['data'][2]=go.Scattermapbox(
        lon=[center['lon']-0.1*width,center['lon']+0.1*width],
        lat=[center['lat'],center['lat']],
        mode='lines',
        marker={'color':color},
    )
    # in the future add a 5km circle in UTM.
    return center['lat'],center['lon'],fig
    

def mk_beach_dropdown():
    '''
    Get the name of all the beaches and collect them in a dictionary
    '''
    _, grouped,_=caching()
    all_beaches=grouped['Beach'].array
    return [{'label': i,'value': i} for i in all_beaches]

def get_beach_data(beach):
    df,_,_=caching()
    df_beach= df[(df==beach).any(axis=1)].sort_values(by=['Dates']) \
                .groupby(['Dates','Lat', 'Longit'])[['Weight']].agg('sum').reset_index()
    last_entry_dates=pd.to_datetime(df_beach['Dates'])[-50:]
    last_entry_weight=df_beach['Weight'][-50:]
    lon,lat=df_beach['Longit'][0],df_beach['Lat'][0]
    summary=go.Figure(go.Scatter(x=last_entry_dates, y=last_entry_weight))
    return last_entry_dates, summary, lon,lat
    


####### LAYOUTS ###############

def tab1_content(intro):
    tab1_layout=dbc.Card([        
        dbc.CardBody([
            dbc.Row([
                html.P(intro),]),
            dbc.Row([
                dbc.Card([
                    dbc.CardHeader('Map of the amount of plastic pollution collected'),
                    dbc.CardBody([
                        dcc.Graph(
                            id='weight-map',
                            figure=Mk_map_weight()
                        )
                    ])
                ]),
                dbc.Card([
                    dbc.CardHeader('Portal statistics'),
                    dbc.CardBody([
                        dbc.Row([
                            daq.LEDDisplay(
                                id='Total_Portal',
                                label='Total weight of plastic\npollution collected (kg)',
                                value=999,
                                color='#002255'                                
                            ),
                            daq.LEDDisplay(
                                id='Total_records',
                                label='Total number of cleanups',
                                value=666 ,
                                color='#002255'
                            )
                        ])
                    ])
                ])
            ]),
            
        ])

    ])
    return tab1_layout

def tab2_content():
    return dbc.Card([
        dbc.CardHeader('Individual beach statistics'),
        dbc.CardBody([
            dbc.Row([
                dcc.Dropdown(
                    id='beach-choice',
                    options=mk_beach_dropdown(),
                    value='Balnakeil'
                ),
                dcc.Graph(
                    id='beach-statistic',
                )
            ])
        ])
    ])

def tab3_content():
    return dbc.Card([
        dbc.CardHeader('Submission form'),
        dbc.CardBody([
            dbc.Row([
                html.P(intro_submit),
            ]),      
            dbc.Card([                    
                    dbc.CardHeader('Add data to a registered place'),
                    dbc.CardBody([
                         dbc.Row([
                             dbc.Col([
                                 dcc.Dropdown(
                                     id='beach-choice-map',
                                     options=mk_beach_dropdown(),
                                     value='Balnakeil'
                                     ),
                                 dcc.Graph(
                                     id='beach_picker',
                                     figure=Mk_base_map()
                                     ),
                                 ]),
                             dbc.Col([
                                 html.P('Showing last 50 entries. You cannot select the same date as a previous record for now.'),
                                 html.P(id='latest-record'),
                                 dcc.Graph(
                                     id='recent_records',
                                     ),
                                 dcc.DatePickerSingle(
                                     id='date_picker',
                                     placeholder='Select a collection date',
                                     date=datetime.now().date()
                                     ),
                                 ])
                         ]),
                    ]),
                ]),
            dbc.Card([
                dbc.CardHeader('Register a new beach or river'),
                dbc.CardBody([
                    html.P('''
                    Please only register a new place if there isn't already a satisfactory record nearby. 
                    We tend to record sedimentary systems as one entry as the plastic will travel along the same beach or cove.
                    For linear beaches, try to find if there isn't already a record less than 5 km from your collection point.
                    '''),
                    dcc.Input(type='text', placeholder='Place name'),
                    dcc.Input(id='lat', type='number', placeholder='latitude'),
                    dcc.Input(id='lon', type='number', placeholder='longitude'),
                    html.P('Distance to nearest beach: xxx km'),
                    # make a warning
                                           
                    ]),
                ]),
            
            dbc.Row([
                dbc.Button(
                    'Submit new data',
                    id='submit-button',
                    n_clicks=0,
                    size='lg',
                ),
            ]),
        ])
    ])

def tab4_content(user_obj):
    return dbc.Card([
        dbc.CardHeader('Welcome '+user_obj['name']),
        dbc.CardBody([
            dbc.Row([
                dbc.Card([
                    dbc.CardHeader('Last entries'),
                    dbc.CardBody([
                        dbc.Row([
                            #table with 10 last entries
                        ]),
                        dbc.Row([
                            #graph with weight collection evolution with selection of beaches and cumulative curves.
                        ])
                    ]),
                ])
            ])
        ])
    ])

def footer_content():
    return dbc.Row([
                dbc.Col([html.P('contact us')], width=2),
                dbc.Col([
                    html.P('Copyright Plastic@Bay CIC 2022'),
                    html.P('source code'),
                    ], width=3),
                dbc.Col([html.Img(src='assets/logo3.png'),
                         ], width=1),
                dbc.Col([html.P('Hosted and supported by Adaptable.io')], width=3),
                dbc.Col([html.Img(src='assets/Adaptable-Light-Logomark.png')],width=1),
                ],justify='end', align='center')



intro= '''
We want to give voice to the anonymous beach cleaners that achieve incommensurable
efforts to protect our coastline. This portal is yours, you can use it as a
record book, as an activist tool or just to contribute to the solution. These data
show the extent of the plastic problem in the UK and beyond.'''

intro_submit='''
This form is intended to be helping the collection of coastal pollution data.
Many people are involved in regular beach cleaning activities. All together,
we collect tons and tons of pollution, keeping places safe and beautiful.
This could sometimes give the impression that no plastic is washed up, hiding
the scale of the problem. In particular in remote areas, it could seem difficult
to report to authorities and get support and recognition. Plastic@Bay report
to national and international institutions. By feeding these databases, you help
finding solutions to marine pollution. All our data are open access and could be
requested at any time.
'''

default_user={'name':'Anonymous'}


app.title="Beach Clean Bay"
app.layout = dbc.Container([
    dbc.Card([
        dbc.CardHeader(['Plastic@Bay CIC citizen science portal'], className='main-title'),
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

#@app.callback(
#    Output('weight-map','figure'),
#    Input('none', 'children')
#)
#def Mk_main_map():
    # in the future distinguish by teams?
#    _, grouped=caching()
#    return Mk_map_weight(grouped)


@app.callback(
    Output('beach-statistic', 'figure'),
    Input('beach-choice', 'value'),
    #State()
)
def update_cum_curve(beach):
    '''
    Make a curve of the cumulative weight collected on a beach
    Calculate the rate of pollution
    '''
    df, _,_=caching()
    df_beach= df[(df==beach).any(axis=1)].sort_values(by=['Dates']) \
                .groupby(['Dates'])[['Weight']].agg('sum').reset_index()
    fig= go.Figure()
    if len(df_beach)>1:
        ## need to account for several weights on the same day or rates will have divisions by 0
        df_beach['Dates']=pd.to_datetime(df_beach['Dates'])
        df_beach['Cum_weight']=df_beach['Weight'].cumsum()
        fig.add_trace(go.Scatter(
                x=df_beach['Dates'],
                y=df_beach['Cum_weight'],
                line=dict(shape='hv', color='navy'),
                hovertemplate=
                    "<b>%{x}</b><br>" +
                    "Cumulative Weight: %{y:.2f}<br>",
                name='Kg',
                mode='lines'))
       # df.groupby(['Beach', 'Lat', 'Longit'])[['Weight']].agg('sum').reset_index()
        rates=  pd.Series(df_beach['Weight'].values, index=df_beach['Dates'])
        New_Dates=df_beach['Dates'][:-1]+df_beach['Dates'].diff()[1:].values/2
        daily_rate=rates.values[1:]/(df_beach['Dates'].diff()[1:].values.astype('float')/(1e9*3600*24))
        fig.add_trace(go.Scatter(x= New_Dates,
                             y=daily_rate,
                             line=dict(color='firebrick'),
                             yaxis='y2',
                             name= 'kg/d',
                             hovertemplate=
                            "<b>%{x}</b><br>" +
                            "Pollution rate: %{y:.2f}<br>",
                            ),
                 )
        fig.update_yaxes(showgrid=False)
        fig.update_layout(
        title=beach,
        showlegend=False,
        yaxis1=dict(title='Cumulative weight (kg)',
                    titlefont=dict(color=fig.data[0].line.color),
                    tickfont=dict(color=fig.data[0].line.color)),

        yaxis2=dict(title='pollution rate(kg/d)',
                    anchor="x",
                    overlaying="y",
                    side="right",
                    titlefont=dict(color=fig.data[1].line.color),
                    tickfont=dict(color=fig.data[1].line.color),
                    )
        )
    else:
        fig.update_layout(
            {
                "title": {
                    "text": "Only one measure, cannot draw the figure",
                },
                "font": {
                    "size": 28
                }}
        )

    return fig

#check coordinates of the map
@app.callback(
    [Output('lat', 'placeholder'),
     Output('lon', 'placeholder'),
     Output('beach_picker', 'figure'),
     Output('date_picker','disabled_days'),
     Output('recent_records','figure')],
    [Input('beach_picker','relayoutData'),
     Input('beach-choice-map', 'value')],
    State('beach_picker','figure'),
    
)
def read_coord(stream, beach,state):
    #print(stream['mapbox._derived'])
    last_entry_dates, fig, lon,lat=get_beach_data(beach)
    state['layout']['mapbox']['center']=dict(
                        lat=lat,
                        lon=lon,)
    state['layout']['mapbox']['zoom']=10
    lat, lon,beachpicker= mk_crossair(stream, state)
                    
    return  lat, lon,beachpicker,last_entry_dates, fig


# switch tab with submit button
@app.callback(
    Output('main-tabs','active_tab'),
    Input('submit-button', 'n_clicks'),
)
def Switch_tab(click):
    if click:
        return 'tab-submit'
    else:
        return 'tab-main'

# @app.callback(
#     Output('click-data', 'children'),
#     Input('basic-interactions', 'clickData'))
# def display_click_data(clickData):
#     return json.dumps(clickData, indent=2)
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080, debug=True)
