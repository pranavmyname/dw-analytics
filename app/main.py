import os
import sys
import subprocess
from flask import Flask, render_template, session
from flask import request, escape, redirect, url_for
import configparser
import json
from matplotlib.figure import Figure
import base64
from io import BytesIO
import numpy as np
import plotly
import pandas as pd
import plotly.express as px

app = Flask(__name__)
app.secret_key = 'Plots'

def get_json_image(df):
    fig = px.line(df, x = 'year', y = 'areas', color = 'month')
    graphJSON = json.dumps(fig,  cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

@app.route("/", methods=['GET', 'POST'])
def index():
    image_data = []
    bands = ['built', 'crops', 'flooded_vegetation', 'trees', 'water']
    for band in bands:
        feature_list = json.load(open(f'data/Bangalore Urban/{band}/areas.json', 'r'))
        areas = (np.array([i.get('properties').get(band) for i in feature_list])*20)**2
        month_data = np.array([i.get('properties').get('month') for i in feature_list])
        year_data = np.array([i.get('properties').get('year') for i in feature_list])
        df = pd.DataFrame({"year": year_data, "month": month_data, "areas": areas})
        image_buff = get_json_image(df)
        image_data.append(image_buff)
    return render_template('index.html', image_data = image_data, bands = bands)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)