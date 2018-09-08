'''
import pandas as pd
import quandl
quandl.ApiConfig.api_key = "xwsP7NGjMxhm6CYLT7C3"


import argparse
import json
import pprint
import os
import sys
import urllib

'''
import pandas as pd
import requests
import io

# This client code can run on Python 2.x or 3.x.  Your imports can be
# simpler if you only need one of those.
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode

def get_metadata():
    metafile_url = 'WIKI-datasets-codes.csv'
    get_in = True
    if get_in==True:

        meta = pd.read_csv(metafile_url, header=None, names=['code', 'descrip'])
        companylookup = [ (descrip[0:descrip.find(' Prices')], code.split('/')[-1]) 
                for code, descrip in zip(meta.code, meta.descrip) ]
        
        # compile final database accounting for exceptions
        db = {}
        for company, ticker in companylookup:
            if company[-1] != ')':
                company = company + (' (%s)' % ticker)
            
            db[company] = ticker
        return db
    get_in=False
    return None

from bokeh.plotting import figure, output_file, show
from bokeh.embed import components
from bokeh.palettes import Spectral11
from math import log10
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta



def request_api(host, path, api_key, url_params=None):
    """Given your API_KEY, send a GET request to the API.

    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        API_KEY (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.

    Returns:
        dict: The JSON response from the request.

    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }

    print(u'Querying {0} ...'.format(url))
    print('url is',url)
    response = requests.request('GET', url, headers=None, params=url_params)
    return pd.read_csv(io.StringIO(response.text))

API_HOST = "https://www.alphavantage.co/query?"
SEARCH_PATH = ""
use_key='alpha_vantage_api.key'
with open(use_key) as keyfile:
    key_0=keyfile.readlines()
API_KEY= key_0[0][:-1]


def get_alpha_vantage_daily_adjusted(api_key, ticker):
    url_params = {
        'symbol': ticker,
        'function': "TIME_SERIES_DAILY_ADJUSTED",
        'outputsize': "compact",
        'apikey': api_key,
        'datatype': 'csv'
    }
    return request_api(API_HOST, SEARCH_PATH, api_key, url_params=url_params)


    

def build_graph(ticker,show_closing,show_adj_closing,show_opening,show_high,show_low):
    # make a graph of closing prices from previous month

    # Create some data for our plot.
    #data = quandl.get('EOD/' + ticker)
    month_data = get_alpha_vantage_daily_adjusted(API_KEY,ticker)
    month_data.timestamp = pd.to_datetime(month_data.timestamp)
    month_data = month_data.iloc[:31]
    print("Data columns", month_data.columns)
    print("Data x is",month_data.timestamp)
    print("Data y  is",month_data.close)

    x = month_data.timestamp # datatime formatted
    y = month_data.close  # closing prices
 
    # Create a heatmap from our data.
    plot = figure(title='Data from Alpha Vantage API',
              x_axis_label='date',
              x_axis_type='datetime',
              y_axis_label='price')
    y_values = []
    legend_list = []
    color_list = []
    if show_high:
        y_values.append(month_data.high)
        legend_list.append('Daily high')
        color_list.append('red')
    if show_low:
        y_values.append(month_data.low)
        legend_list.append('Daily low')
        color_list.append('green')
    if show_closing:
        y_values.append(month_data.close)
        legend_list.append('Closing')
        color_list.append('black')
    if show_adj_closing:
        y_values.append(month_data.adjusted_close)
        legend_list.append('Adj_closing')
        color_list.append('pink')
    if show_opening:
        y_values.append(month_data.open)
        legend_list.append('Opening')
        color_list.append('blue')

    x_values = [month_data.timestamp]*len(y_values)

    #plot.multi_line()
    for (colr, leg, x, y) in zip(color_list, legend_list, x_values, y_values):
        my_plot = plot.line(x, y, color=colr, legend=leg)
    plot.legend.location='top_left'
    plot.legend.click_policy='hide'
    #plot.multi_line(xs=x_values, ys=y_values, line_color=Spectral11[0:len(y_values)], alpha=1.5, line_width=5, color=color_list, legend=legend_list)
    script, div = components(plot)

    return script, div


from flask import Flask, render_template, request, jsonify, redirect, url_for
#template_dir = os.path.join(os.getcwd(),'templates','startbootstrap-creative-gh-pages')
from flask_bootstrap import Bootstrap
#app = Flask(__name__,template_folder=template_dir)
app = Flask(__name__)
bs_app = Bootstrap(app)

db = get_metadata()
defaultheader = "Company Stock to graph"

@app.route('/')
def render_root():
    return render_template('input.html', header = defaultheader)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search = request.args.get('q')
    results = [k for k in db.keys() if k.lower().find(search) != -1]
    return jsonify(matching_results=results)


@app.route('/graph', methods=['GET', 'POST'])
def graphCompany(company=None):
    if request.method == 'POST':

        company = (request.form['company'])
        show_closing = "show_closing" in request.form
        show_adj_closing = "show_adj_closing" in request.form
        show_opening = "show_opening" in request.form
        show_high = "show_high" in request.form
        show_low = "show_low" in request.form
        #print("show_closing",show_closing)

        if company not in db.keys():
            header = "%s not in database.<br>Reinput company to graph" % company 
            return render_template('input.html', header=header)

        ticker = db[company]

        script, div = build_graph(ticker,show_closing,show_adj_closing,show_opening,show_high,show_low)
        return render_template('graph.html', script=script, div=div, 
        ticker=ticker , company=company)

    else:
        return render_template('input.html', header = defaultheader)

if __name__ == '__main__':
    app.static_folder = 'static'
    app.run(debug=True)
    #app.run(port=33507)
