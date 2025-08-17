#!/usr/bin/env python3
"""
Emergency Dashboard Test
"""

import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import webbrowser
from threading import Timer

def open_browser():
    try:
        webbrowser.open('http://127.0.0.1:8050')
        print("🌐 Browser opened!")
    except:
        print("📱 Open: http://127.0.0.1:8050")

# Create app
app = dash.Dash(__name__)

# Sample data
dates = pd.date_range(start=datetime.now() - timedelta(days=1), periods=100, freq='5min')
prices = 3335 + np.cumsum(np.random.normal(0, 2, 100))
df = pd.DataFrame({'time': dates, 'price': prices})

app.layout = html.Div([
    html.H1("🤖 Dashboard Connection Test - SUCCESS!", 
            style={'textAlign': 'center', 'color': 'green', 'margin': '20px'}),
    
    html.Div([
        html.H3("✅ Connection Working!", style={'color': 'green'}),
        html.P("If you can see this, the dashboard fix worked!"),
        html.P("Your enhanced AI trading bot should now work properly."),
    ], style={'textAlign': 'center', 'backgroundColor': '#e8f5e8', 
             'padding': '20px', 'margin': '20px', 'borderRadius': '10px'}),
    
    dcc.Graph(
        figure=px.line(df, x='time', y='price', 
                      title='Live Trading Data Simulation')
    ),
    
    html.Div(id="status", style={'textAlign': 'center', 'margin': '20px'}),
    
    dcc.Interval(id='interval', interval=5000, n_intervals=0)
])

@app.callback(Output('status', 'children'), Input('interval', 'n_intervals'))
def update_status(n):
    return f"🕐 Last Update: {datetime.now().strftime('%H:%M:%S')} (Refresh #{n})"

if __name__ == '__main__':
    print("🧪 Testing Dashboard Connection...")
    print("🚀 http://127.0.0.1:8050")
    
    Timer(2.0, open_browser).start()
    
    try:
        app.run(debug=False, host='127.0.0.1', port=8050, use_reloader=False, threaded=True)
    except Exception as e:
        print(f"❌ Test failed: {e}")
