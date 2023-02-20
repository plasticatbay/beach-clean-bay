from dash import dcc as dcc
from dash import html as html
import dash_daq as daq
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import plotly.graph_objects as go
import pandas as pd

####### LAYOUTS ###############

def toast_content():
    minyear, maxyear= 2017,2023
    marks={y:{'label': str(y)} for y in range(minyear, maxyear+1)}
    child= dbc.Card([
        dbc.CardHeader("Change the map settings"),
        dbc.CardBody([
             dbc.Row([
                 dbc.Col([
                     daq.BooleanSwitch(
                         id='switch_all_years',
                         on=True,
                         label="Use all the years"),
                     daq.BooleanSwitch(
                         id='switch_all_teams',
                         on=True,
                         label="Use all the teams"),
                     ], xs=6, md=2),
                 dbc.Col([
                     dcc.Slider(
                         id='year_slider',
                         min=minyear,
                         max=maxyear,
                         value=2022,
                         marks=marks,
                         step=1,
                         disabled=True ),
                     dcc.Dropdown(
                         id='team_selection',
                         placeholder='Select a team',
                         disabled=True),
                     ]),
                 ])
             ])
        ])
    return child

def tab1_content(intro):

    tab1_layout=dbc.Card([        
        dbc.CardBody([
            dbc.Row([
                html.P(intro),]),
            
            dbc.Collapse(
                     toast_content(),
                     id='toast',
                     is_open=True),
            dbc.Row([
                dbc.Card([
                    dbc.CardHeader('Map of the amount of plastic pollution collected'),
                    dbc.CardBody([
                        dcc.Graph(
                            id='weight-map',
                            #figure=Mk_map_weight()
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
                                    # value=round(total_weight),
                                    color='#002255'                                
                                ),
                            ]),
                            dbc.Col([
                                daq.LEDDisplay(
                                    id='Total_records',
                                    label='Total number of cleanups',
                                    #value=total_cleanups ,
                                    color='#002255'
                                )
                            ]),
                            dbc.Col([
                                daq.LEDDisplay(
                                    id='Total_sites',
                                    label='Total number of cleaned sites',
                                    #value=total_beach ,
                                    color='#002255'
                                )
                            ]),
                        ])
                    ])
                ]),
                dbc.Card([
                    dbc.CardHeader('Trend of cleanups'),
                    dbc.CardBody([
                        dcc.Graph(id="curve_trend")
                        ])
                    ]),
            ]),
            
        ])

    ])
    return tab1_layout

def Mk_map_weight(grouped):
    '''
    Make a map of plastic accumulations
    '''
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
        paper_bgcolor='#003380',
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

def mk_general_curves(df):
    new_df=df.set_index('Dates')
    Gm=new_df.groupby(pd.Grouper(freq="M")).sum()
    Gy=new_df.groupby(pd.Grouper(freq="Y")).sum()
    # Gr["year"]=datetime(year=Gr.index.get_level_values(0))
    minx,maxx=datetime(year=2017,month=9,day=1),datetime.now()
    fig=go.Figure()    
    fig.add_trace(go.Bar(
         x=Gy.index,
         y=Gy.Weight,
         name="yearly collection",
         marker=dict(color='#003380'),
         width=1000 * 3600 * 24 * 365,
         xperiod="M12",
         xperiodalignment="middle"
        ))
    fig.add_trace(go.Bar(
         x=Gm.index,
         y=Gm.Weight,
         name="monthly collection",
         marker=dict(color='#d5e5ff'),
         width=1000 * 3600 * 24 * 28,
         xperiod="M1",
         xperiodalignment="middle"
        ))
    fig.update_layout(
        xaxis=dict(range=[minx,maxx], 
             color='orange',
             ticklabelmode="period"),
        yaxis=dict(color='orange'),
        font=dict(color='orange'),
        legend=dict(orientation='h'),
         )
    return fig

def tab2_content():
    return dbc.Card([
        dbc.CardHeader('Individual beach statistics'),
        dbc.CardBody([
            dbc.Row([
                dcc.Dropdown(
                    id='beach-choice',
                    # options=mk_beach_dropdown(),
                    value='Balnakeil'
                ),
                dcc.Graph(
                    id='beach-statistic',
                    figure=go.Figure(),
                   
                )
            ])
        ])
    ])

def draw_stat_curve(df_beach, fig, beach):
        #df_beach['Dates']=pd.to_datetime(df_beach['Dates'])
        df_beach['Cum_weight']=df_beach['Weight'].cumsum()
        fig.add_trace(go.Scatter(
            x=df_beach['Dates'],
            y=df_beach['Cum_weight'],
            line=dict(shape='hv', color='white'),
            fill='tozeroy',
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
            title=f'Recorded plastic pollution evolution at {beach}',
            showlegend=False,
            yaxis1=dict(title='Cumulative weight (kg)',
                titlefont=dict(color=fig.data[0].line.color),
                tickfont=dict(color=fig.data[0].line.color)),
            #paper_bgcolor='#d5e5ff',
            yaxis2=dict(title='pollution rate(kg/d)',
                anchor="x",
                overlaying="y",
                side="right",
                titlefont=dict(color=fig.data[1].line.color),
                tickfont=dict(color=fig.data[1].line.color),
                        ),
            xaxis=dict(color='orange')
        )
        return fig


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
                                             #options=mk_beach_dropdown(),
                                             value='Balnakeil'
                                             ),
                                         dcc.Graph(
                                             id='beach_picker',
                                             #figure=Mk_base_map()
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
                    Before registering a new place, **check for nearby satisfactory records**. 
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
                           title='Link to OSmap',
                           target='_blank'),
                    html.H3('Indicate the site name'),
                    dcc.Input(type='text', placeholder='Place name'),
                    html.H3('Site coordinates (please use the map above for accuracy)'),
                    dcc.Input(id='lat', type='number', placeholder='latitude',style={'padding':10}),
                    dcc.Input(id='lon', type='number', placeholder='longitude',style={'padding':10}),
                    html.H3('Zoom indicator'),
                    
                    daq.Indicator(
                        id='zoom-indicator',
                        label="Not enough Zoom",
                        value=False,
                        #color='red',
                    ),
                    html.H3('Nearest recorded beaches'),
                    html.P(id='nearest_records')
                    # make a warning
                                           
                    ]),
                ]),
            
            
        ])
    ])

def Mk_base_map(grouped):
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
    base_map.add_trace(go.Scattermapbox())
    base_map.add_trace(go.Scattermapbox())
                  
    return base_map
    
def mk_crossair(stream, fig):
    '''
    Make a crossair in the middle of the map to locate precisely.
    '''
    try:
        center=stream['mapbox.center']
        width=stream['mapbox._derived']['coordinates'][0][0]-stream['mapbox._derived']['coordinates'][1][0]
        height=stream['mapbox._derived']['coordinates'][0][1]-stream['mapbox._derived']['coordinates'][2][1]
    except:
        center={'lon':-3,'lat':55}
        width=1
        height=1
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
If you enter data that don't conform or seem suspicious, or redundant, they will be deleted.
'''
