import dash
from dash import dcc, html
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Simple test dashboard
app = dash.Dash(__name__)

# Generate sample data
dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='H')
prices = 2650 + np.cumsum(np.random.normal(0, 10, len(dates)))
df = pd.DataFrame({'date': dates, 'price': prices})

app.layout = html.Div([
    html.H1("AI Trading Bot Dashboard - TEST", style={'textAlign': 'center', 'color': 'green'}),
    html.Div([
        html.H3("Balance: $100,000", style={'color': 'blue'}),
        html.H3("P&L: +$1,250", style={'color': 'green'}),
        html.H3("Signals: 15", style={'color': 'orange'}),
    ], style={'display': 'flex', 'justifyContent': 'space-around', 'margin': '20px'}),
    
    dcc.Graph(
        figure=px.line(df, x='date', y='price', title='Account Performance (Demo)')
    ),
    
    html.Div("If you see this, the dashboard is working correctly!", 
             style={'textAlign': 'center', 'fontSize': '18px', 'margin': '20px'})
])

if __name__ == '__main__':
    print("Test Dashboard: http://127.0.0.1:8050")
    try:
        app.run_server(debug=True, port=8050)
    except Exception as e:
        print(f"Error: {e}")
