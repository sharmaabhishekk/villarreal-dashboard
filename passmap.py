import pandas as pd
import numpy as np
from pandas import json_normalize

from sklearn.preprocessing import MinMaxScaler
import plotly.graph_objs as go

class PassMap():
    """ draw a passmap using the whoscored data"""

    def __init__(self, fig, match_dict, nr, nc, color="dodgerblue", side=None):
        self.fig = fig
        self.md = match_dict
        self.nr = nr
        self.nc = nc
        if not side:
            self.side = "home"
        else:
            self.side = side
        self.team_id = self.md[self.side]["teamId"]

        self.start_XI_ids = [pl["playerId"] for pl in self.md[self.side]["players"] if "isFirstEleven" in pl]
        self.start_XI_names = [pl["name"] for pl in self.md[self.side]["players"] if "isFirstEleven" in pl]
        
        self.color = color
        self.id_name_dict = dict(zip(self.start_XI_ids, self.start_XI_names))
    
    def __get_receiver(self, df):
        """get receivers for succesful passes between starters"""
        
        df["receiver_id"] = df["playerId"].shift(-1)
        df = df.query("type_displayName == 'Pass' & outcomeType_displayName == 'Successful' &\
                       playerId == @self.start_XI_ids & receiver_id == @self.start_XI_ids").copy() 
        df["qualifiers"] = df["qualifiers"].astype(str)
        return df[~df['qualifiers'].str.contains('|'.join(["Corner", "Freekick", "Throw"]), regex=True)].reset_index(drop=True)

    def __get_final_df(self):
        """wrangle the data to get out final form"""
        
        df = json_normalize(self.md["events"], sep="_")
        #df[["x", "y", "endX", "endY"]] = df[["x", "y", "endX", "endY"]]/100
        df["qualifiers"] = df["qualifiers"].astype(str)
        pass_df = self.__get_receiver(df)
        avg = pass_df.groupby("playerId").agg(x=("x", "mean"), y=("y", "mean"), num=("x", "count")).reset_index()
        pass_df[["playerId", "receiver_id"]] = np.sort(pass_df[["playerId", "receiver_id"]].copy(), axis=1)
        links = pass_df.groupby(["playerId", "receiver_id"]).agg(count=("x", "size")).reset_index()
        
        final_df = avg.merge(links, left_on='playerId', right_on='playerId').merge(avg, left_on='receiver_id', right_on='playerId')
        final_df.columns=["player_id", "px", "py", "num", "receiver_id", "count", "receiver_id", "rx", "ry", "rnum"]
        final_df = final_df[["player_id", "px", "py", "num", "count", "receiver_id", "rx", "ry"]] ##num -> total passes by player | count -> links b/w 2 players
        avg["player_name"] = avg["playerId"].map(self.id_name_dict)

        final_df["num"] = MinMaxScaler(feature_range=(0.1, 0.9)).fit_transform(final_df["num"].values.reshape(-1,1))
        final_df["count"] = MinMaxScaler(feature_range=(0.1, 0.9)).fit_transform(final_df["count"].values.reshape(-1,1))

        return final_df, avg

    def plot_passmap(self):
        """plot the network"""
        final_df, avg = self.__get_final_df()
        traces = []
        for row in final_df.itertuples(index=False):
            traces.append(go.Scatter(x=[row.px, row.rx], y=[row.py, row.ry], mode='lines', opacity=row.count, 
                                     line={"color":self.color, "width":row.count*5}, hoverinfo="none")) 
                                     
        traces.append(go.Scatter(x=avg["x"], y=avg["y"], mode='markers', text=avg["player_name"],
                                 marker={"color":self.color, 'symbol':'circle', 'size':avg["num"]/2, 'line':{"width":2, "color":"white"}}, 
                                 hovertemplate="<b>%{text}</b><extra></extra>"))    

        _ = [self.fig.add_trace(trace, row=self.nr, col=self.nc) for trace in traces]
        self.fig.update_layout(showlegend=False)
        return self.fig
       