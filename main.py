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

# import googlecloudprofiler
#
# # Profiler initialization. It starts a daemon thread which continuously
# # collects and uploads profiles. Best done as early as possible.
# try:
#     # service and service_version can be automatically inferred when
#     # running on App Engine. project_id must be set if not running
#     # on GCP.
#     googlecloudprofiler.start(verbose=3)
# except (ValueError, NotImplementedError) as exc:
#     print(exc)  # Handle errors here

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
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from flask_caching import Cache
import sqlalchemy


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

def Mk_map_weight(grouped):
    '''
    Make a map of plastic accumulations
    '''
    plastic_map=go.Figure(go.Scattermapbox(lon=grouped['Longit'],
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
        height=700,
        hovermode='closest',
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
    _, grouped=global_store()
    fig=go.Scattermapbox(lon=grouped['Longit'],
                     lat=grouped['Lat'],
                     text=grouped['Beach'],
                     mode='markers')
    fig.update_layout(
        height=400,
        width=400,
        hovermode='closest',
        mapbox=dict(
                    bearing=0,
                    center=dict(
                        lat=55,
                        lon=-3,
                    ),
                    pitch=0,
                    zoom=4,
                    style="open-street-map",))
    return fig

####### layouts ###############

def tab1_content(intro):
    tab1_layout=dbc.Card([
        dbc.CardHeader('Map of amount of plastic pollution collected'),
        dbc.CardBody([
            dbc.Row([
                html.Button(
                    'Submit new data',
                    id='submit-button',
                    n_clicks=0,
                ),
                html.Div(id='none',children=[],style={'display': 'none'})
            ]),
            dbc.Row([
                html.P(intro),
                dcc.Graph(
                    id='weight-map',
                    figure=go.Figure(),
                )
            ])
        ])

    ])

def tab2_content():
    return dbc.Card([
        dbc.CardHeader('Individual beach statistics'),
        dbc.CardBody([
            dbc.Row([
                dcc.Dropdown(
                    id='beach-choice',
                    #options=[mk_beach_dropdown()],
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
    dbc.CardHeader('Submission form')])

###### SQL ####

def global_store():
    print('Using global store')
    with engine.connect() as cnx:
        df= pd.read_sql_table('WeightData', cnx)
        #cursor = cnx.execute('SELECT * FROM `WeightData`')
        #df =cursor.fetchall()
    df['Weight']=df['Weight'].astype('float')
    grouped = df.groupby(['Beach', 'Lat', 'Longit'])[['Weight']].agg('sum').reset_index()
    return df, grouped


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

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
server=app.server
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': '/tmp'
})
timeout = 300

@server.route('/_ah/warmup')
def warmup():
    """Warm up an instance of the app."""
    db_user = os.environ.get('CLOUD_SQL_USERNAME')
    db_password = os.environ.get('CLOUD_SQL_PASSWORD')
    db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
    db_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
    # When deployed to App Engine, the `GAE_ENV` environment variable will be
    # set to `standard`
    if os.environ.get('GAE_ENV') == 'standard':
        # If deployed, use the local socket interface for accessing Cloud SQL
        unix_socket = '/cloudsql/{}'.format(db_connection_name)
        engine_url = 'mysql+pymysql://{}:{}@/{}?unix_socket={}'.format(
            db_user, db_password, db_name, unix_socket)
    else:
        # If running locally, use the TCP connections instead
        # Set up Cloud SQL Proxy (cloud.google.com/sql/docs/mysql/sql-proxy)
        # so that your application can use 127.0.0.1:3306 to connect to your
        # Cloud SQL instance
        host = '127.0.0.1'
        engine_url = 'mysql+pymysql://{}:{}@{}/{}'.format(
            db_user, db_password, host, db_name)

    # The Engine object returned by create_engine() has a QueuePool integrated
    # See https://docs.sqlalchemy.org/en/latest/core/pooling.html for more
    # information
    engine = sqlalchemy.create_engine(engine_url, pool_size=3)
    return '', 200
    # Handle your warmup logic here, e.g. set up a database connection pool


app.title="Beach Clean Bay"
app.layout = dbc.Container([
    #header
    html.Div([
        html.H1('Plastic@Bay CIC citizen science portal'),
        html.P(intro),
        ]),
    # Define tabs
    html.Div([
        dbc.Tabs([
            dbc.Tab(tab1_content(intro),label='Plastic map',tab_id='tab-main',),
            dbc.Tab(tab2_content(),label='Beach stats',tab_id='tab-curves',),
            dbc.Tab(tab3_content(),label='Submit data',tab_id='tab-submit',)
            ],
            id="main-tabs",
            active_tab="tab-main",)
    ])
])

@cache.memoize(timeout=timeout)
def caching():
    return global_store()

@app.callback(
    Output('weight-map','figure'),
    Input('none', 'children')
)
def Mk_main_map():
    # in the future distinguish by teams?
    _, grouped=caching()
    return Mk_map_weight(grouped)

@app.callback(
    Output('beach-choice','options'),
    Input('none', 'children')
)
def mk_beach_dropdown():
    '''
    Get the name of all the beaches and collect them in a dictionary
    '''
    _, grouped=global_store()
    all_beaches=[groubed['Beach']] #<= some query
    return [{'label':All_names[i],'value': All_names[i]} for i in range(len(All_names))]

@app.callback(
    Output('beach-statistic', 'figure'),
    Input('beach-output', 'value'),
    #State()
)
def update_cum_curve(beach):
    '''
    Make a curve of the cumulative weight collected on a beach
    '''
    df, _=global_store()
    df_beach= df[(df==beach).any(axis=1)].sort_values(by=['Dates'])
    fig= go.Figure()
    if len(df_beach)>1:
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
    else:
        fig.update_layout(
            {
                    "text": "Only one measure, cannot draw a figure",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {
                        "size": 28
                    }}
        )

    return fig

# switch tab with submit button
@app.callback(
    Output('main-tabs','active_tab'),
    Input('submit-button', 'n_clicks'),
)
def Switch_tab(active_tab):
    return 'tab-submit'

# @app.callback(
#     Output('click-data', 'children'),
#     Input('basic-interactions', 'clickData'))
# def display_click_data(clickData):
#     return json.dumps(clickData, indent=2)
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8080, debug=True)
