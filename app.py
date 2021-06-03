import json
import os

import numpy as np
import pandas as pd
from pandas import json_normalize
import streamlit as st

import plotly.graph_objs as go
from plotly.subplots import make_subplots
from pitch_plotly import plot_pitch

from passmap import PassMap
from helpers import get_goalkicks, get_shots, get_prog_passes, get_xT, get_defensive_actions
from helpers import get_physical_fig, get_ball_recoveries, get_aerials_data
from streamlit_plotly_events import plotly_events

## initial page layout section and variables
st.set_page_config(layout="wide")

HOME_COLOR = 'dodgerblue'
AWAY_COLOR = 'red'
COLOR = "silver"
NROWS, NCOLS = 2, 2

st.markdown("# Villarreal Dashboard(Demo)")
teams_widget = st.selectbox("Select Team", options=["Senior Team", "Villarreal B", "Villarreal C", "Women's"])

match_json_files = ['1492142_Villarreal_Getafe.json',
                    '1492157_Villarreal_Osasuna.json',
                    '1492161_Deportivo Alaves_Villarreal.json',
                    '1492202_Eibar_Villarreal.json',
                    '1492221_Villarreal_Barcelona.json',
                    '1492277_Villarreal_Cadiz.json',
                    '1492281_Granada_Villarreal.json'
                    ]


match_fitness_files = ['J34_VIL-GTF.xlsx',
                       'J30_VIL-OSA.xlsx', 
                       'J31_ALV-VIL.xlsx', 
                       'J27_EIB-VIL.xlsx', 
                       'J32_VIL-BAR.xlsx', 
                       'J28_VIL-CAD.xlsx', 
                       'J29_GRA-VIL.xlsx'
                       ]
match_files = [os.path.join(r"static/fitnessdatafirstteam8games", match_file) for match_file in match_json_files]
fitness_dict = dict(zip(match_files, match_fitness_files))    

match_files_dict = {}
for mf in match_files:
    ht, at = mf.split(".json")[0].split("\\")[-1].split("_")[1:]
    match_files_dict[ht+"-"+at] = mf

if teams_widget == "Senior Team":

    match_widget = st.selectbox("Select match to explore", options=sorted(match_files_dict.keys()))
    match_file = match_files_dict[match_widget]

    with open(match_file) as f:
        md = json.load(f)
    
    #fitness_df = pd.read_excel(os.path.join(r"static\fitnessdatafirstteam8games", fitness_dict[match_files_dict['Villarreal-Getafe']]))

    home_team, away_team = md["home"]["name"], md["away"]["name"]
    home_team_id, away_team_id = md["home"]["teamId"], md["away"]["teamId"]

    title = f"{home_team} vs {away_team}"
    st.markdown(f"""<div style="text-align: center"> {title} </div>""", unsafe_allow_html=True)

    ################# get the figures
    metrics = ["Defensive Actions", "Ball Recoveries"]
    plot_titles = [team + " " + metric for metric in metrics for team in [home_team, away_team]]
    fig = make_subplots(rows=NROWS, cols=NCOLS, subplot_titles=plot_titles)

    #ig.add_annotation(row=1, col=1, text=plot_titles[0], showarrow=False, x=50, y=102)
    #ig.add_annotation(row=1, col=2, text=plot_titles[1], showarrow=False, x=50, y=102)


    fig.update_layout(width=800, height=1100, autosize=True, showlegend=False)
    fig.update_yaxes(scaleratio=0.8, showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=1)

    fig.update_yaxes(scaleratio=0.8, showgrid=False, zeroline=False, showticklabels=False, row=1, col=2)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, row=1, col=2)

    ###########
    ##plot events

    ##defensive actions
    home_def = get_defensive_actions(md, "home")
    away_def = get_defensive_actions(md, "away")
    fig = plot_pitch(fig=fig, nr=1, nc=1)
    fig = plot_pitch(fig=fig, nr=1, nc=2)

    fig.add_trace(go.Scatter(x=home_def.x, y=home_def.y, mode='markers', marker={'symbol': 'circle', 'color': HOME_COLOR}, 
                             text=home_def.player_name, hovertemplate="<b>%{text}</b><extra></extra>"),
                             row=1, col=1) 

    fig.add_trace(go.Scatter(x=away_def.x, y=away_def.y, mode='markers', marker={'symbol': 'circle', 'color': AWAY_COLOR}, 
                             text=away_def.player_name, hovertemplate="<b>%{text}</b><extra></extra>"),
                             row=1, col=2)           

    ## plot recoveries
    h_recov = get_ball_recoveries(md, "home")
    fig.add_trace(go.Bar(x=h_recov['player_name'], y=h_recov["index"], orientation='h'), row=2, col=1)

    a_recov = get_ball_recoveries(md, "away")
    fig.add_trace(go.Bar(x=a_recov['player_name'], y=a_recov["index"], orientation='h'), row=2, col=2)

    ##duel matrix
    aerials = get_aerials_data(md)

### in possession

    metrics = ["Shots", "Progressive Passes", "Goalkicks", "Passmap & Average Position"]
    plot_titles = [team + " " + metric for metric in metrics for team in [home_team, away_team]]

    fig_2 = make_subplots(rows=4, cols=2, subplot_titles=plot_titles)

    ##plot shots
    fig_2 = plot_pitch(fig=fig_2, nr=1, nc=1)
    fig_2 = plot_pitch(fig=fig_2, nr=1, nc=2)
    shots_home = get_shots(md)
    trace =  go.Scatter(x=shots_home["x"], y=shots_home["y"], mode='markers', hovertext=shots_home["player_name"], 
                             marker={"color":HOME_COLOR, 'symbol':'circle-open', 'size':10}, 
                             hovertemplate="<b>%{hovertext}</b><extra></extra>")
    fig_2.add_trace(trace, row=1, col=1)

    shots_away = get_shots(md, side="away")
    trace =  go.Scatter(x=shots_away["x"], y=shots_away["y"], mode='markers', hovertext=shots_away["player_name"], 
                             marker={"color":AWAY_COLOR, 'symbol':'circle-open', 'size':10}, 
                             hovertemplate="<b>%{hovertext}</b><extra></extra>")
    fig_2.add_trace(trace, row=1, col=2)

    ##progressive passes
    fig_2 = plot_pitch(fig=fig_2, nr=2, nc=1)
    fig_2 = plot_pitch(fig=fig_2, nr=2, nc=2)
    hprog = get_prog_passes(md)
    for row in hprog.itertuples():
        fig_2.add_trace(go.Scatter(x=[row.x, row.endX], y=[row.y, row.endY], mode='lines', marker={'color':HOME_COLOR}, 
                                 hoverinfo="none"), row=2, col=1)

    fig_2.add_trace(go.Scatter(x=hprog.x, y=hprog.y, mode='markers', marker={'symbol': 'circle', 'color': HOME_COLOR}, 
                             text=hprog.player_name, hovertemplate="<b>%{text}</b><extra></extra>"),
                  row=2, col=1)

    aprog = get_prog_passes(md, side="away")
    for row in aprog.itertuples():
        fig_2.add_trace(go.Scatter(x=[row.x, row.endX], y=[row.y, row.endY], mode='lines', marker={'color':AWAY_COLOR}, 
                                 hoverinfo="none"), row=2, col=2)

    fig_2.add_trace(go.Scatter(x=aprog.x, y=aprog.y, mode='markers', marker={'symbol': 'circle', 'color': AWAY_COLOR}, 
                             text=aprog.player_name, hovertemplate="<b>%{text}</b><extra></extra>"),
                  row=2, col=2)    

    ##goal-kicks
    fig_2 = plot_pitch(fig=fig_2, nr=3, nc=1)
    fig_2 = plot_pitch(fig=fig_2, nr=3, nc=2)
    home_gks = get_goalkicks(md, "home")
    away_gks = get_goalkicks(md, "away")

    for row in home_gks.itertuples():
        fig_2.add_trace(go.Scatter(x=[row.x, row.endX], y=[row.y, row.endY], mode='lines', marker={'color':HOME_COLOR}, 
                             hoverinfo="none"), row=3, col=1)
    fig_2.add_trace(go.Scatter(x=home_gks.x, y=home_gks.y, mode='markers', marker={'symbol': 'circle', 'color': HOME_COLOR}, 
                             text=home_gks.player_name, hovertemplate="<b>%{text}</b><extra></extra>"),
                  row=3, col=1)     

    for row in away_gks.itertuples():
        fig_2.add_trace(go.Scatter(x=[row.x, row.endX], y=[row.y, row.endY], mode='lines', marker={'color':AWAY_COLOR}, 
                         hoverinfo="none"), row=3, col=2)
    fig_2.add_trace(go.Scatter(x=away_gks.x, y=away_gks.y, mode='markers', marker={'symbol': 'circle', 'color': AWAY_COLOR}, 
                             text=away_gks.player_name, hovertemplate="<b>%{text}</b><extra></extra>"),
                  row=3, col=2) 

    ##plot passmap
    fig_2 = plot_pitch(fig=fig_2, nr=4, nc=1)
    fig_2 = plot_pitch(fig=fig_2, nr=4, nc=2)
    fig_2 = PassMap(fig=fig_2, match_dict=md, nr=4, nc=1, color=HOME_COLOR).plot_passmap()
    fig_2 = PassMap(fig=fig_2, match_dict=md, nr=4, nc=2, color=AWAY_COLOR, side="away").plot_passmap()

    fig_2.update_layout(width=800, height=2000, autosize=True, showlegend=False)
    fig_2.update_yaxes(scaleratio=0.8, showgrid=False, zeroline=False, showticklabels=False)
    fig_2.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)   


    ## transitions

    ##layout
    st.markdown("""<div style="text-align: center"> <h1> Out of Possession </h1> </div>""", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    st.markdown("Aerial Duels Matrix")
    st.dataframe(aerials)
    st.markdown("""<div style="text-align: center"> <h1> In Possession </h1> </div>""", unsafe_allow_html=True)
    st.plotly_chart(fig_2, use_container_width=True, config={'displayModeBar': False})
    #st.markdown("""<div style="text-align: center"> <h1> Transitions </h1> </div>""", unsafe_allow_html=True)
    #st.plotly_chart(fig_3, use_container_width=True, config={'displayModeBar': False})


elif teams_widget == "Villarreal B" or teams_widget == "Villarreal C":
    fig = get_physical_fig(teams_widget)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

elif teams_widget == "Women's":
    fig = make_subplots(rows=4, cols=2)
    fig.update_layout(width=800, height=1100, autosize=True, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

