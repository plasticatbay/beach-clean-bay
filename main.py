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
from dash import ctx as ctx
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
                prevent_initial_callbacks=True,
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
    total_weight=df['Weight'].sum()
    grouped = df.groupby(['Beach', 'Lat', 'Longit'])[['Weight']].agg('sum').reset_index()
    total_beach=len(grouped)
    total_cleanups=len(df)
    return df, grouped, beaches, total_weight, total_beach, total_cleanups

@cache.memoize(timeout=timeout)
def caching():
    return global_store()

#################### FIGURES ##########################

def Mk_map_weight():
    '''
    Make a map of plastic accumulations
    '''
    _,grouped,_,_,_,_=caching() 
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

def draw_stat_curve(df_beach, fig, beach):
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
        return fig

def Mk_base_map():
    _, grouped,_,_,_,_=caching()
    base_map=go.Figure()
    base_map.add_trace(
        go.Scattermapbox(
            lon=grouped['Longit'],
            lat=grouped['Lat'],
            text=grouped['Beach'],
            hovertemplate=
                    "<b>%{text}</b><br>" +
                    "lat: %{lat:.5f}<br>" +
                    "lon: %{lon:.5f}<br><extra></extra>",
            mode='markers')
                       )

    base_map.update_layout(
        height=300,
        #width=300,
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
    _, grouped,_,_,_,_=caching()
    all_beaches=grouped['Beach'].array
    return [{'label': i,'value': i} for i in all_beaches]

def get_beach_data(beach):
    df,_,_,_,_,_=caching()
    df_beach= df[(df==beach).any(axis=1)].sort_values(by=['Dates']) \
                .groupby(['Dates','Lat', 'Longit'])[['Weight']].agg('sum').reset_index()
    last_entry_dates=pd.to_datetime(df_beach['Dates'])[-50:]
    last_entry_weight=df_beach['Weight'][-50:]
    lon,lat=df_beach['Longit'][0],df_beach['Lat'][0]
    summary=go.Figure(go.Scatter(x=last_entry_dates, y=last_entry_weight))
    summary.update_layout(
        height=200,
        title=f'Last 50 records for {beach}',
        margin=dict(b=1, l=1, r=5, t=30),
        yaxis=dict(title='Weight collected (kg)')
    )
    last_record= 'Last record in {}:   {} --- {} kg.'.format(
        beach,last_entry_dates.iloc[-1].date(),last_entry_weight.iloc[-1] )
    return last_record, summary, lon,lat
    


####### LAYOUTS ###############

def tab1_content(intro):
    _,_,_,total_weight, total_beach, total_cleanups=caching()
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
                            dbc.Col([
                                daq.LEDDisplay(
                                    id='Total_Portal',
                                    label='Total weight of plastic\npollution collected (kg)',
                                    value=round(total_weight),
                                    color='#002255'                                
                                ),
                            ]),
                            dbc.Col([
                                daq.LEDDisplay(
                                    id='Total_records',
                                    label='Total number of cleanups',
                                    value=total_cleanups ,
                                    color='#002255'
                                )
                            ]),
                            dbc.Col([
                                daq.LEDDisplay(
                                    id='Total_sites',
                                    label='Total number of cleaned sites',
                                    value=total_beach ,
                                    color='#002255'
                                )
                            ]),
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
                                 dbc.Card([
                                     dbc.CardHeader('Previous records'),
                                     dbc.CardBody([
                                         dcc.Dropdown(
                                             id='beach-choice-map',
                                             options=mk_beach_dropdown(),
                                             value='Balnakeil'
                                             ),
                                         dcc.Graph(
                                             id='beach_picker',
                                             figure=Mk_base_map()
                                             ),
                                         html.P(id='latest-record'),
                                         dcc.Graph(
                                             id='recent_records',
                                             figure=go.Figure(data={}, layout=dict(
                                                 title='no beach selected',
                                                 height=200,
                                                 margin=dict(b=1, l=1, r=1, t=30),)
                                                              )
                                             ),
                                         ])
                                     ])
                             ], width=6),
                             dbc.Col([
                                 dbc.Card([
                                     dbc.CardHeader('Register your cleanup'),
                                     dbc.CardBody([
                                         dbc.Row([
                                             html.H3('Please select a beach on the map or on the dropdown menu'),
                                             html.P(id='selected_beach'),
                                             ]),
                                         dbc.Row([
                                             html.H3('Choose a collection date'),
                                             dcc.DatePickerSingle(
                                                 id='date_picker',
                                                 date=datetime.now().date()
                                             ),
                                             ]),
                                         dbc.Row([
                                             html.H3('Your registered user name'),
                                             # this should fill up from Google
                                             html.P(
                                                 id='username',
                                                   ),
                                             # this should fill up from the DB
                                             html.P(id='Registered team'),
                                             ]),
                                         dbc.Row([
                                             html.H3('Weight collected during the cleanup'),
                                             dcc.Input(id='collected_weight',
                                                   placeholder='Weight in KG'),
                                             ]),
                                         dbc.Row([
                                             html.Hr(),
                                             dbc.Button(
                                                 'Submit new data',
                                                 id='submit-button',
                                                 n_clicks=0,
                                                 disabled=True,
                                                 size='lg',
                                                 style={'background-color':'#003380',
                                                        'color':'#d5e5ff'}
                                             ),
                                         ]),
                                         ])
                                 ])
                                 ])
                         ]),
                    ]),
                ]),
            dbc.Card([
                dbc.CardHeader('Register a new cleanup site'),
                dbc.CardBody([
                    dcc.Markdown('''
                    Before registering a new place, **check for nearby satisfactory record**. 
                    We tend to record sedimentary systems as one entry as the plastic will travel along the same beach or cove.
                    For linear beaches, try to find if there isn't already a record less than **2 km from your collection point**.
                    If you notice an error please [contact us](mailto:julien.moreau@plasticatbay.org), it is a work in progress.
                    Enter the coordinates of the new cleanup site in **decimal degree** (accuracy of 5 decimals). 
                    **It is easy with the map**, just place the crossair where the clean happened. 
                    Zoom in sufficiently to be able to recognise landmarks on the map.
                    There is an *indicator* showing if you are zoomed enough for accuracy.
                    The coordinates in the form will update as soon as you use the map.
                    For long distance clean, place the crossair in the middle of the cove/beach you cleaned.
                    Please be accurate when providing a place name, use official OSmaps names.
                    If you have difficulties or a doubt, please [contact us](mailto:julien.moreau@plasticatbay.org).
                    '''),
                    html.Hr(),
                    html.A(id='osmap_link',
                           children='Link to OSmap for the selected coordinates',
                           title='Link to OSmap'
                           target='_blank'),
                    html.H3('Indicate the site name'),
                    dcc.Input(type='text', placeholder='Place name'),
                    html.H3('Site coordinates (please use the map above for accuracy)'),
                    dcc.Input(id='lat', type='number', placeholder='latitude',style={'padding':10}),
                    dcc.Input(id='lon', type='number', placeholder='longitude',style={'padding':10}),
                    html.H3('Zoom indicator'),
                    
                    daq.Indicator(
                        label="Not enough Zoom",
                        value=False,
                        color='red',
                    ),
                    html.H3('Nearest recorded beaches'),
                    html.P(id='nearest_records')
                    # make a warning
                                           
                    ]),
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
    df, _,_,_,_,_=caching()
    df_beach= df[(df==beach).any(axis=1)].sort_values(by=['Dates']) \
                .groupby(['Dates'])[['Weight']].agg('sum').reset_index()
    fig= go.Figure()
    if len(df_beach)>1:
        fig= draw_stat_curve(df_beach, fig, beach)
        
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
     #Output('date_picker','disabled_days'),
     Output('recent_records','figure'),
     Output('latest-record','children'),
     Output('selected_beach','children'),
     Output('osmap_link','href')],
    [Input('beach_picker','relayoutData'),    
     Input('beach-choice-map', 'value')],
    State('beach_picker','figure'),   
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
        return lat, lon, state , fig, last_record,selection, href         
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
        return  lat, lon,beachpicker, summary, '', 'No beach selected', href 

@app.callback(
    Output('beach-choice-map', 'value'),
    Input('beach_picker','clickData'),
)
def select_from_map(click):
    return click['points'][0]['text']
       

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080, debug=True)
