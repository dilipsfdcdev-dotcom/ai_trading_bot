#!/usr/bin/env python3
"""
Simple Dashboard Test
"""

try:
    import dash
    from dash import dcc, html, Input, Output
    import plotly.express as px
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    print("📊 Starting Simple Test Dashboard...")
    
    # Create app
    app = dash.Dash(__name__)
    
    # Generate sample data
    dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='H')
    prices = 2650 + np.cumsum(np.random.normal(0, 10, len(dates)))
    df = pd.DataFrame({'date': dates, 'price': prices})
    
    # Layout
    app.layout = html.Div([
        html.H1("🤖 AI Trading Bot - Test Dashboard", 
                style={'textAlign': 'center', 'color': 'green', 'marginBottom': '30px'}),
        
        html.Div([
            html.H3("✅ Dashboard is working!", style={'color': 'green'}),
            html.P("If you can see this, the dashboard server is running correctly."),
            html.Hr(),
        ], style={'textAlign': 'center', 'margin': '20px'}),
        
        html.Div([
            html.Div([
                html.H4("💰 Balance", style={'color': '#2c3e50'}),
                html.H2("$100,000", style={'color': '#27ae60'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 
                     'borderRadius': '10px', 'margin': '10px', 'width': '200px', 'display': 'inline-block'}),
            
            html.Div([
                html.H4("📈 Signals", style={'color': '#2c3e50'}),
                html.H2("5 Active", style={'color': '#3498db'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 
                     'borderRadius': '10px', 'margin': '10px', 'width': '200px', 'display': 'inline-block'}),
            
            html.Div([
                html.H4("🎯 Accuracy", style={'color': '#2c3e50'}),
                html.H2("78%", style={'color': '#e74c3c'})
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 
                     'borderRadius': '10px', 'margin': '10px', 'width': '200px', 'display': 'inline-block'})
        ], style={'textAlign': 'center', 'marginBottom': '30px'}),
        
        # Chart
        dcc.Graph(
            figure=px.line(df, x='date', y='price', 
                          title='Sample Trading Data (Demo)',
                          labels={'price': 'Price ($)', 'date': 'Time'})
        ),
        
        html.Div([
            html.H3("📝 Test Results:"),
            html.Ul([
                html.Li("✅ Dash framework working"),
                html.Li("✅ Plotly charts working"), 
                html.Li("✅ Web server running"),
                html.Li("✅ Browser can connect"),
                html.Li("🚀 Ready for full AI dashboard!")
            ])
        ], style={'margin': '30px', 'padding': '20px', 'backgroundColor': '#e8f5e8', 'borderRadius': '10px'}),
        
        # Auto-refresh
        dcc.Interval(
            id='interval-component',
            interval=5*1000,  # Update every 5 seconds
            n_intervals=0
        )
    ], style={'fontFamily': 'Arial, sans-serif', 'margin': '20px'})
    
    # Callback for updates
    @app.callback(
        Output('interval-component', 'n_intervals'),
        Input('interval-component', 'n_intervals')
    )
    def update_data(n):
        return n
    
    # Run server
    if __name__ == '__main__':
        print("🚀 Test Dashboard URL: http://127.0.0.1:8050")
        print("✅ If this works, your dashboard setup is correct!")
        print("🔄 Press Ctrl+C to stop")
        
        try:
            app.run_server(debug=True, host='127.0.0.1', port=8050, use_reloader=False)
        except Exception as e:
            print(f"❌ Dashboard failed to start: {e}")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📦 Please install: pip install dash plotly pandas numpy")
except Exception as e:
    print(f"❌ Error: {e}")
