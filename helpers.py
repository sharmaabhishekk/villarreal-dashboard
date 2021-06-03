import pandas as pd
from pandas import json_normalize
import numpy as np

from PIL import Image
import json

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def prep_df(md):
    """ normalize to df, 
        add player names
        get values in range(0,1)
        change qualifiers to string
    """
    df = json_normalize(md["events"], sep="_")
    d = {float(k):v for k,v in md["playerIdNameDictionary"].items()}
    df["player_name"] = df["playerId"].map(d)
    #df[["x", "y", "endX", "endY"]] = df[["x", "y", "endX", "endY"]]/100
    df["qualifiers"] = df["qualifiers"].astype(str)

    return df

def get_shots(md, side="home"):
    """returns a dataframe containing the shots """
    
    team_id = md[side]["teamId"]    
    df = prep_df(md)
    shot_events = ["ShotOnPost", "MissedShots", "SavedShot", "Goal"]
    
    return df.query("type_displayName == @shot_events & teamId == @team_id")[["x", "y", "player_name", "minute"]]

def get_prog_passes(md, side="home"):
    """ returns a dataframe containing progressive passes
    Definition: 
        minimum length: 10 units
        pass not from defensive 40% of pitch
        pass moves at least 10 units towards goal from pass start
        open-play passes only
    """

    team_id = md[side]["teamId"]
    df = prep_df(md)
    pass_df = df.query("type_displayName == 'Pass' & outcomeType_displayName == 'Successful' &\
                        x>=40 & teamId == @team_id").copy()

    pass_df = pass_df[~pass_df['qualifiers'].str.contains('|'.join(["Corner", "Freekick", "Throw"]), regex=True)].reset_index(drop=True)          
    pass_df["length"] = np.sqrt(np.square(pass_df["x"] - pass_df["endX"]) + np.square(pass_df["y"] - pass_df["endY"]))
    pass_df["start_dist_to_goal"] = np.sqrt(np.square(pass_df["x"] - 100) + np.square(pass_df["y"] - 50)) 
    pass_df["end_dist_to_goal"] = np.sqrt(np.square(pass_df["endX"] - 100) + np.square(pass_df["endY"] - 50)) 
    pass_df["prog"] = pass_df["start_dist_to_goal"] - pass_df["end_dist_to_goal"]

    return pass_df.query("length>=10 & prog>=10")[["player_name", "minute", "x", "y", "endX", "endY"]]

def get_goalkicks(md, side="home"):
    """ returns goalkicks"""

    team_id = md[side]["teamId"]
    df = prep_df(md) 
    df = df.query("teamId == @team_id")
    
    return df[df['qualifiers'].str.contains("GoalKick")].reset_index(drop=True)[["player_name", "minute", "x", "y", "endX", "endY"]] 

def get_xT(md, side="home"):
    """ calculates xT for passes using Karun's xT data and returns dataframe"""

    team_id = md[side]["teamId"]
    df = prep_df(md)

    with open("static/expected_threat.json") as f:
        xtd = np.array(json.load(f))
    n_rows, n_cols = xtd.shape

    pass_df = df.query("type_displayName == 'Pass' & outcomeType_displayName == 'Successful' &\
                        teamId == @team_id")
    pass_df = pass_df[~pass_df['qualifiers'].str.contains('|'.join(["Corner", "Freekick", "Throw"]), regex=True)].reset_index(drop=True)        

    pass_df['x1_bin'] = pass_df["x"].apply(lambda val: int(val/(1/n_cols)) if val != 1 else int(val/(1/n_cols)) - 1 )
    pass_df['x2_bin'] = pass_df["endX"].apply(lambda val: int(val/(1/n_cols)) if val != 1 else int(val/(1/n_cols)) - 1 )

    pass_df['y1_bin'] = pass_df["y"].apply(lambda val: int(val/(1/n_rows)) if val != 1 else int(val/(1/n_rows)) - 1 )
    pass_df['y2_bin'] = pass_df["endY"].apply(lambda val: int(val/(1/n_rows)) if val != 1 else int(val/(1/n_rows)) - 1 )                        

    pass_df['start_zone_value'] = pass_df[['x1_bin', 'y1_bin']].apply(lambda x: xtd[x[1]][x[0]], axis=1)
    pass_df['end_zone_value'] = pass_df[['x2_bin', 'y2_bin']].apply(lambda x: xtd[x[1]][x[0]], axis=1)
    pass_df['pass_xt_value'] = pass_df['end_zone_value'] - pass_df['start_zone_value'] 

    return pass_df.groupby(["player_name"]).agg(xt=("pass_xt_value", "sum")).reset_index().sort_values(by="xt")

def get_defensive_actions(md, side="home"):

    team_id = md[side]["teamId"]
    df = prep_df(md) 

    return df.query("type_displayName == ['Interception', 'Clearance', 'Tackle', 'Foul', 'Challenge'] &\
                     teamId == @team_id")[["player_name", "minute", "x", "y", "endX", "endY"]] 

def get_ball_recoveries(md, side="home"):

    team_id = md[side]["teamId"]
    df = prep_df(md) 

    pdf = df.query("type_displayName == 'BallRecovery' & teamId == @team_id")["player_name"] 
    return pdf.value_counts().reset_index()

def get_aerials_data(md):
    df = prep_df(md)

    cdf = df.query("type_displayName == 'Aerial'").copy()
    aids = cdf.index
    cdf["related_player"] = cdf["player_name"].shift(-1)
    cdf = cdf.loc[aids[::2], ["player_name", "related_player", "outcomeType_value"]]
    d = cdf.groupby(["player_name", "related_player"]).agg(count=("outcomeType_value", "size")).reset_index()
    d = d.pivot(index="player_name", columns="related_player", values="count").fillna(0)

    away_pls = [pl["name"] for pl in md["away"]["players"]]
    home_pls = [pl["name"] for pl in md["home"]["players"]]

    d = d[d.index.isin(home_pls)]
    d = d[[col for col in d.columns if col in away_pls]]
    return d.style.background_gradient(cmap="viridis", low=min(d.min(axis=1)), high=max(d.max(axis=1)))


def get_physical_fig(team):

    fig = make_subplots(rows=3, cols=2)
    fig.update_layout(width=800, height=1200, showlegend=False)

    if team == "Villarreal B":
        df = pd.read_excel("static/Vill B.xlsx")
    else:
        df = pd.read_excel("static/Vill C.xlsx")

    fig.add_trace(go.Scatter(x=df.Accelerations, y=df.Decelerations, mode='markers', marker={'symbol': 'circle'}, 
                             text=df.Player, hovertemplate="<b>%{text}</b><extra></extra>"),
                             row=1, col=1) 

    fig.add_trace(go.Scatter(x=df['Sprint Abs Cnt'], y=df['Sprint Abs (m)'], mode='markers', marker={'symbol': 'circle'}, 
                             text=df.Player, hovertemplate="<b>%{text}</b><extra></extra>"),
                             row=1, col=2) 

    fig.add_trace(go.Scatter(x=df['Player Load (a.u.)'], y=df['Energy Expenditure (kcal)'], mode='markers', marker={'symbol': 'circle'}, 
                             text=df.Player, hovertemplate="<b>%{text}</b><extra></extra>"),
                             row=2, col=1) 

    fig.update_xaxes(title_text="Accelerations", row=1, col=1)
    fig.update_xaxes(title_text="Sprint Abs Cnt", row=1, col=2)
    fig.update_xaxes(title_text="Player Load (a.u.)", row=2, col=1)

    fig.update_yaxes(title_text="Decelerations", row=1, col=1)
    fig.update_yaxes(title_text="Sprint Abs (m)", row=1, col=2)
    fig.update_yaxes(title_text="Energy Expenditure (kcal)", row=2, col=1)

    return fig



