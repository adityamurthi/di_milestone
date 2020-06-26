# -*- coding: utf-8 -*-
"""
Created on Wed Jun 24 09:24:50 2020

@author: aditya
"""

##Libraries to import
from flask import Flask, render_template, request, redirect
import pandas as pd
import requests
from datetime import date
from dateutil.relativedelta import relativedelta
##Bokeh stuff
from bokeh.io import show
from bokeh.plotting import figure##, curdoc
##from bokeh.layouts import column
from bokeh.models import DatetimeTickFormatter, ColumnDataSource
from bokeh.palettes import Spectral11
from bokeh.embed import components

app = Flask(__name__)

app.vars = {}

def displayStock(symbol, params=None):
    """
    Function that gets the stock values from
    the AlphaVantage API and displays them on my apps webpage on Heroku.
    Inputs:
        symbol: The entity for which the stock time-series needs to be displayed.
        The user supplies this in a search tab and if the entity is available, the
        code plots the stock price otherwise it raises an exception.
    Keywords:
        params: Combination of desired ticker options.
        all: diaplay all
    Output:
        Bokeh plot that displays on my Heroku app"""

    ##The alphaVantage API requires a unique key for access.
    ##Will use the requests library to access the API and then
    ##utilize simplejson to extract the fields and create a dataframe
    ##using Pandas and then plot using Bokeh.
    ##Constants
    apikey = 'XGV3L4J5FI9OXSAX'
    if symbol is None:
        symbol = 'GOOG'

    ##use the requests library to access the api and get the data
    url = 'https://www.alphavantage.co/query'
    ##The keys required to read from the AlphaVanatge API.
    keys_ticker = {'function': 'TIME_SERIES_DAILY', 'symbol': symbol, \
                   'outputsize': 'compact',
                   'apikey': apikey}

    ##The keys required to read from the AlphaVanatge API.
    r = requests.get(url, params=keys_ticker)

    ##The requests library has a json() method that automatically decodes
    ##the json object and returns a Python dict object
    tickerjson = r.json()

    try:
        ticker_dict = tickerjson['Time Series (Daily)']

        ##Extract data from the dict and load it into a Pandas dataframe
        dict_keys = ticker_dict.keys()
        ll = []
        for key in dict_keys:
            tsd   = dict()
            tsd['Timestamp'] = pd.to_datetime(key)
            temp  = ticker_dict[key]
            tkeys = {k.split('.')[1].strip():float(v) for k,v in temp.items()}
            res   = {**tsd, **tkeys}
            ll.append(pd.DataFrame(res, index=[0]))

        ##Get the dataframe containing the extracted data from the API
        df = pd.concat(ll)
        df = df.reset_index().drop('index', axis=1)

        ##You only want the data between start and end date
        end     = date.today()
        start   = end - relativedelta(months=2)
        df      = df.loc[(df['Timestamp'] >= pd.to_datetime(start))
                         & (df['Timestamp'] <= pd.to_datetime(end))]

        ##Plot in Bokeh:
        source=ColumnDataSource(df)
        ##Just going to use the simple plotting feature to plot
        p = figure(plot_width=800, plot_height=400, title='Stock Price data from AlphaVantage', x_axis_label='Date', x_axis_type="datetime")
        p.xaxis.formatter = DatetimeTickFormatter(years = ['%Y-%m-%d'],
                                                  months = ['%Y-%m-%d'],
                                                  days = ['%Y-%m-%d'])
        if params is None:
            ##Default display == 'close'
            ##Render the plot
            print('No params, plotting for "close"')
            #p.line(df['Timestamp'], df['close'], legend_label=symbol+' - ' + 'close', line_width=2.5, color='magenta')
            p.line(source=source, x='Timestamp', y='close', legend_label=symbol+' - ' + 'close', line_width=2.5, color='magenta')
        elif len(params) == 1:
            #p.line(df['Timestamp'], df[params[0]], legend_label=symbol+' - ' + params[0], line_width=2.5, color='magenta')
            p.line(source=source, x='Timestamp', y=params[0], legend_label=symbol+' - ' + params[0], line_width=2.5, color='magenta')
        else:##Many lines to plot
            cols = params
            numlines=len(cols)
            mypalette=Spectral11[0:numlines]
            if len(cols) == 2:
                p.line(source=source, x='Timestamp', y=cols[0], legend_label=symbol+' - ' + cols[0], line_width=2.5, color=mypalette[0])
                p.line(source=source, x='Timestamp', y=cols[1], legend_label=symbol+' - ' + cols[1], line_width=2.5, color=mypalette[1])
            elif len(cols) == 3:
                 p.line(source=source, x='Timestamp', y=cols[0], legend_label=symbol+' - ' + cols[0], line_width=2.5, color=mypalette[0])
                 p.line(source=source, x='Timestamp', y=cols[1], legend_label=symbol+' - ' + cols[1], line_width=2.5, color=mypalette[1])
                 p.line(source=source, x='Timestamp', y=cols[2], legend_label=symbol+' - ' + cols[2], line_width=2.5, color=mypalette[2])
            else:
                p.line(source=source, x='Timestamp', y=cols[0], legend_label=symbol+' - ' + cols[0], line_width=2.5, color=mypalette[0])
                p.line(source=source, x='Timestamp', y=cols[1], legend_label=symbol+' - ' + cols[1], line_width=2.5, color=mypalette[1])
                p.line(source=source, x='Timestamp', y=cols[2], legend_label=symbol+' - ' + cols[2], line_width=2.5, color=mypalette[2])
                p.line(source=source, x='Timestamp', y=cols[3], legend_label=symbol+' - ' + cols[0], line_width=2.5, color=mypalette[3])

        return (p)
    except KeyError as e:
        print(e)

@app.route('/', methods=['GET'])
def index():
    return render_template("test1.html")

@app.route('/plot', methods=['POST'])
def plot():
    ##Generate the Bokeh plot
    app.vars['symbol'] = request.form["text"]
    app.vars['params'] = request.form.getlist("ticker")
    print(app.vars['symbol'], app.vars['params'])
    p = displayStock(app.vars['symbol'], app.vars['params'])
    try:
        script, div = components(p)
        return render_template("plot.html", script=script, div=div)
    except ValueError as e:
        return ("That ticker symbol %s is invalid! Try entering another symbol."%app.vars['symbol'])

if __name__ == "__main__":
    app.run(port=33507)
