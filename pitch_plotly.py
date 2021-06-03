import plotly.graph_objs as go
from plotly.subplots import make_subplots

import numpy as np
import pandas as pd

import json

def ellipse_arc(x_center=0, y_center=0, a=1, b =1, start_angle=0, end_angle=2*np.pi, N=100, closed= False):
    t = np.linspace(start_angle, end_angle, N)
    x = x_center + a*np.cos(t)
    y = y_center + b*np.sin(t)
    path = f'M {x[0]}, {y[0]}'
    for k in range(1, len(t)):
        path += f'L{x[k]}, {y[k]}'
    if closed:
        path += ' Z'
    return path    


def plot_pitch(fig, nr, nc, color='silver'):

    points = go.Scatter(x=[50, 11.5, 88.5], y=[50, 50, 50], marker={"color":color}, mode="markers", hoverinfo='none')

    outer_box = go.Scatter(x=[0, 100, 100, 0, 0], y=[0, 0, 100, 100, 0],
                           mode='lines', line={"color":color, "width":1}, hoverinfo='none')

    left_pen = go.Scatter(x=[0, 17, 17, 0, 0], y=[21.1, 21., 78.9, 78.9, 21.1],
                           mode='lines', line={"color":color, "width":1}, hoverinfo='none')
    right_pen = go.Scatter(x=[83, 100, 100, 83, 83], y=[21.1, 21., 78.9, 78.9, 21.1],
                           mode='lines', line={"color":color, "width":1}, hoverinfo='none')

    left_d = go.Scatter(x=[0, 5.8, 5.8, 0, 0], y=[36.8, 36.8, 63.2, 63.2, 36.8],
                           mode='lines', line={"color":color, "width":1}, hoverinfo='none')
    right_d = go.Scatter(x=[94.2, 100, 100, 94.2, 94.2], y=[36.8, 36.8, 63.2, 63.2, 36.8],
                           mode='lines', line={"color":color, "width":1}, hoverinfo='none')

    left_goal = go.Scatter(x=[0, 0, 0], y=[45.2, 54.8, 45.2],
                           mode='lines', line={"color":color, "width":5}, hoverinfo='none')
    right_goal = go.Scatter(x=[100, 100], y=[45.2, 54.8],
                           mode='lines', line={"color":color, "width":5}, hoverinfo='none')
    halfway_line = go.Scatter(x=[50, 50], y=[0, 100], mode='lines',
                              line={"color":color, "width":1}, hoverinfo='none')
    halfway_circle = go.Scatter(x=[50], y=[50], mode='markers',
                              marker={"color":color, 'symbol':'circle-open', 'size':50}, hoverinfo='none')


    traces = [points, outer_box, left_pen, right_pen, left_d, right_d, halfway_line, left_goal, right_goal, halfway_circle]
    [fig.add_trace(trace, row=nr, col=nc) for trace in traces]
    
    fig.add_shape(type = "path", path = ellipse_arc(x_center=17, y_center=50, a=1.2, b=7, start_angle=-np.pi/2, end_angle=np.pi/2, N=60),
                  line_color=color, line_width=1, opacity=1, row=nr, col=nc)
    fig.add_shape(type = "path", path = ellipse_arc(x_center=83, y_center=50, a=1.2, b=7, start_angle=np.pi/2, end_angle=np.pi*1.5, N=60),
                  line_color=color, line_width=1, opacity=1, row=nr, col=nc) 
    

    return fig
