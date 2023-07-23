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

def get_json_image(df, x= 'year', color = 'month'):
    if(x=='month'):
        color = 'year'
    fig = px.line(df, x = x, y = 'areas', color = color)
    graphJSON = json.dumps(fig,  cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

def get_json_image_xy(x, y):
    fig = px.line(x=x, y=y)
    graphJSON = json.dumps(fig,  cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

bands = ['built', 'crops', 'flooded_vegetation', 'trees', 'water']
df_list = []
for band in bands:
    feature_list = json.load(open(f'data/Bangalore Urban/{band}/areas.json', 'r'))
    areas = (np.array([i.get('properties').get('label') for i in feature_list])*20)**2
    month_data = np.array([i.get('properties').get('month') for i in feature_list])
    year_data = np.array([i.get('properties').get('year') for i in feature_list])
    df = pd.DataFrame({"year": year_data, "month": month_data, "areas": areas})
    df['date'] = pd.to_datetime(dict(year=df.year, month=df.month, day = 1))
    df.set_index('date', inplace=True)
    df = df.resample('MS').asfreq()
    df.fillna(method='ffill', inplace=True)
    df.month = df.index.month
    df.year = df.index.year
    df_list.append(df)

unique_year = np.sort(np.unique(year_data))[1:]
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
def get_months_box_bool(checkboxes):
    bool_aray = []
    for month in month_names:
        if month in checkboxes:
            bool_aray.append(True)
        else:
            bool_aray.append(False)
    return bool_aray

@app.route("/", methods=['GET', 'POST'])
def index():
    months_box = [True, True, True, True, True, True, False, False, False, False, False, False]
    image_data = []
    selected_option = 'year'
    kwargs = {
                "months_list": month_names,
                "bands": bands
              }
    is_run_files = request.args.get("view","")
    print(is_run_files)
    if(is_run_files!=""):
        selected_option = request.args.get('x_axis', "")
        print(selected_option)
        months_box = get_months_box_bool(request.args.getlist("month", None))
    if(is_run_files=="Advanced"):
        for idx, band in enumerate(bands):
            df = df_list[idx]
            df = df[df.month.isin([i+1 for i, x in enumerate(months_box) if x])]
            image_buff = get_json_image(df, x = selected_option)
            image_data.append(image_buff)
        return render_template('index.html', image_data = image_data, months_box = months_box, x_axis = selected_option, **kwargs)
    for idx, band in enumerate(bands):
        df = df_list[idx]
        yearly_data = [np.mean(df[df.year==i].areas[months_box[0:(df.year==i).sum()]]) for i in unique_year]
        image_buff = get_json_image_xy(unique_year, yearly_data)
        image_data.append(image_buff)
    return render_template('index.html', image_data = image_data, months_box = months_box, x_axis = selected_option, **kwargs)

@app.route("/advanced", methods=['GET', 'POST'])
def advanced_view():
    image_data = []
    months_box = session['months_box']
    for idx, band in enumerate(bands):
        df = df_list[idx]
        image_buff = get_json_image(df)
        image_data.append(image_buff)
    return render_template('index.html', image_data = image_data, bands = bands, months_box = months_box)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)