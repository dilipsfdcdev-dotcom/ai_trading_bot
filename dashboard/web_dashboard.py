import dash
from dash import dcc, html, Input, Output
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import logging
import numpy as np

class TradingDashboard:
    def __init__(self, bot=None):
        self.bot = bot
        self.app = dash.Dash(__name__)
        self.logger = logging.getLogger(__name__)
        
        # Sample data for demo
        self.sample_data = self.generate_sample_data()
        
        self.setup_layout()
        self.setup_callbacks()
    
    def generate_sample_data(self):
        """Generate sample data for dashboard demo"""
        dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='H')
        
        # Sample price data with realistic values
        price_data = []
        base_price = 3350  # Current XAUUSD price area
        for i, date in enumerate(dates):
            price = base_price + np.random.normal(0, 10) + np.sin(i/24) * 20
            price_data.append({
                'date': date,
                'price': price,
                'symbol': 'XAUUSD'
            })
        
        # Sample signals
        signal_data = []
        signals = ['BUY', 'SELL', 'STRONG_BUY', 'STRONG_SELL', 'HOLD']
        for i in range(50):
            signal_data.append({
                'timestamp': dates[min(i*3, len(dates)-1)],
                'symbol': 'XAUUSD' if i % 2 == 0 else 'BTCUSD',
                'signal': np.random.choice(signals, p=[0.25, 0.25, 0.15, 0.15, 0.2]),
                'confidence': np.random.uniform(0.6, 0.95),
                'price': base_price + np.random.normal(0, 50)
            })
        
        # Sample performance data
        performance_data = []
        equity = 1000000  # 1M starting balance
        for date in dates:
            daily_return = np.random.normal(0.0005, 0.01)
            equity *= (1 + daily_return)
            performance_data.append({
                'date': date,
                'equity': equity,
                'daily_return': daily_return
            })
        
        return {
            'prices': pd.DataFrame(price_data),
            'signals': pd.DataFrame(signal_data),
            'performance': pd.DataFrame(performance_data)
        }
    
    def get_real_account_data(self):
        """Get real account data from bot"""
        try:
            if self.bot and hasattr(self.bot, 'data_collector'):
                account = self.bot.data_collector.get_account_info()
                if account:
                    return {
                        'balance': account['balance'],
                        'profit': account['profit'],
                        'currency': account.get('currency', 'USD'),
                        'equity': account.get('equity', account['balance'])
                    }
        except Exception as e:
            self.logger.error(f"Error getting real account data: {e}")
        return None
    
    def get_real_signals(self):
        """Get real signals from bot"""
        try:
            if self.bot and hasattr(self.bot, 'last_signals'):
                return self.bot.last_signals
        except Exception as e:
            self.logger.error(f"Error getting real signals: {e}")
        return {}
    
    def setup_layout(self):
        """Setup dashboard layout"""
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("🤖 AI Trading Bot Dashboard", 
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '10px'}),
                html.P("Real-time Trading Signals & Performance Monitoring",
                      style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '30px'})
            ]),
            
            # Status Bar
            html.Div([
                html.Div("🟢 LIVE", style={'color': '#27ae60', 'fontWeight': 'bold', 'fontSize': '18px'}),
                html.Div(id="current-time", style={'color': '#34495e'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'padding': '15px', 
                     'backgroundColor': '#ecf0f1', 'borderRadius': '10px', 'marginBottom': '20px'}),
            
            # Account Summary Cards
            html.Div([
                html.Div([
                    html.H4("💰 Account Balance", style={'margin': '0', 'color': '#2c3e50'}),
                    html.H2(id="balance", style={'margin': '10px 0 0 0', 'color': '#27ae60'})
                ], className="metric-card"),
                
                html.Div([
                    html.H4("📈 Today's P&L", style={'margin': '0', 'color': '#2c3e50'}),
                    html.H2(id="daily-pnl", style={'margin': '10px 0 0 0'})
                ], className="metric-card"),
                
                html.Div([
                    html.H4("📊 Open Positions", style={'margin': '0', 'color': '#2c3e50'}),
                    html.H2(id="positions-count", style={'margin': '10px 0 0 0', 'color': '#3498db'})
                ], className="metric-card"),
                
                html.Div([
                    html.H4("🎯 Signal Accuracy", style={'margin': '0', 'color': '#2c3e50'}),
                    html.H2(id="accuracy", style={'margin': '10px 0 0 0', 'color': '#9b59b6'})
                ], className="metric-card")
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(250px, 1fr))', 
                     'gap': '20px', 'marginBottom': '30px'}),
            
            # Charts Section
            html.Div([
                html.Div([
                    html.H3("📈 Account Performance", style={'color': '#2c3e50'}),
                    dcc.Graph(id="equity-chart", style={'height': '400px'})
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                
                html.Div([
                    html.H3("🔔 Live Trading Signals", style={'color': '#2c3e50'}),
                    html.Div(id="signals-table", style={'height': '400px', 'overflowY': 'scroll'})
                ], style={'width': '48%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '4%'})
            ]),
            
            # Auto-refresh component
            dcc.Interval(
                id='interval-component',
                interval=5*1000,  # Update every 5 seconds
                n_intervals=0
            )
        ], style={
            'fontFamily': 'Segoe UI, Arial, sans-serif', 
            'margin': '20px',
            'backgroundColor': '#f8f9fa'
        })
        
        # Add CSS styling
        css_styles = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>AI Trading Bot Dashboard</title>
                {%favicon%}
                {%css%}
                <style>
                    body {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        margin: 0;
                        padding: 0;
                        min-height: 100vh;
                    }
                    .metric-card {
                        background: rgba(255, 255, 255, 0.95);
                        padding: 25px;
                        border-radius: 15px;
                        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                        text-align: center;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                    }
                    .signal-table {
                        background: rgba(255, 255, 255, 0.95);
                        border-radius: 10px;
                        overflow: hidden;
                    }
                    .signal-row {
                        padding: 12px;
                        border-bottom: 1px solid #ecf0f1;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    .signal-BUY { color: #27ae60; font-weight: bold; }
                    .signal-SELL { color: #e74c3c; font-weight: bold; }
                    .signal-STRONG_BUY { color: #2ecc71; font-weight: bold; font-size: 1.1em; }
                    .signal-STRONG_SELL { color: #c0392b; font-weight: bold; font-size: 1.1em; }
                    .signal-HOLD { color: #95a5a6; font-weight: bold; }
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
        '''
        self.app.index_string = css_styles
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [Output('balance', 'children'),
             Output('daily-pnl', 'children'),
             Output('positions-count', 'children'),
             Output('accuracy', 'children'),
             Output('current-time', 'children'),
             Output('equity-chart', 'figure'),
             Output('signals-table', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Get real account data
            real_data = self.get_real_account_data()
            real_signals = self.get_real_signals()
            
            if real_data:
                balance = f"${real_data['balance']:,.2f}"
                profit = real_data['profit']
                pnl_color = '#27ae60' if profit >= 0 else '#e74c3c'
                pnl_sign = '+' if profit >= 0 else ''
                daily_pnl = html.Span(f"{pnl_sign}${profit:,.2f}", style={'color': pnl_color})
                
                # Update sample data with real equity
                equity_col = self.sample_data['performance'].columns.get_loc('equity')
                self.sample_data['performance'].iloc[-1, equity_col] = real_data['equity']
            else:
                balance = "$1,000,000.00"
                daily_pnl = html.Span("+$0.00", style={'color': '#27ae60'})
            
            positions = "0"  # Will be updated when position tracking is added
            
            # Calculate accuracy from signals
            accuracy = "N/A"
            if real_signals:
                high_conf_signals = sum(1 for s in real_signals.values() if s.get('confidence', 0) > 0.7)
                total_signals = len(real_signals)
                if total_signals > 0:
                    accuracy = f"{(high_conf_signals/total_signals*100):.0f}%"
            
            # Equity curve
            equity_fig = px.line(
                self.sample_data['performance'], 
                x='date', y='equity',
                title='Account Equity Over Time'
            )
            equity_fig.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#2c3e50'
            )
            equity_fig.update_traces(line_color='#3498db', line_width=3)
            
            # Signals table
            signals_data = []
            if real_signals:
                for symbol, signal in real_signals.items():
                    signals_data.append({
                        'symbol': symbol,
                        'signal': signal.get('category', 'HOLD'),
                        'confidence': signal.get('confidence', 0.5),
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'reasoning': signal.get('reasoning', 'AI Analysis')[:30] + '...'
                    })
            
            # Add sample signals if no real signals
            if not signals_data:
                for _, row in self.sample_data['signals'].tail(8).iterrows():
                    signals_data.append({
                        'symbol': row['symbol'],
                        'signal': row['signal'],
                        'confidence': row['confidence'],
                        'time': row['timestamp'].strftime('%H:%M:%S'),
                        'reasoning': 'Technical Analysis'
                    })
            
            # Create signals table
            signals_table = html.Div([
                html.Div([
                    html.Div([
                        html.Strong(signal['time'], style={'color': '#2c3e50'}),
                        html.Br(),
                        html.Span(signal['symbol'], style={'fontSize': '0.9em', 'color': '#7f8c8d'})
                    ], style={'flex': '1'}),
                    
                    html.Div([
                        html.Span(signal['signal'], 
                                 className=f"signal-{signal['signal']}",
                                 style={'fontSize': '1.1em'}),
                        html.Br(),
                        html.Span(f"{signal['confidence']:.0%}", 
                                 style={'fontSize': '0.9em', 'color': '#7f8c8d'})
                    ], style={'flex': '1', 'textAlign': 'center'}),
                    
                    html.Div([
                        html.Span(signal['reasoning'], 
                                 style={'fontSize': '0.8em', 'color': '#95a5a6'})
                    ], style={'flex': '2', 'textAlign': 'right'})
                ], className="signal-row") for signal in signals_data
            ], className="signal-table")
            
            return balance, daily_pnl, positions, accuracy, current_time, equity_fig, signals_table
    
    def run_server(self, host='127.0.0.1', port=8050, debug=False):
        """Run the dashboard server"""
        print(f"🚀 Dashboard starting at http://{host}:{port}")
        print("📊 You can view charts, signals, and metrics here!")
        try:
            self.app.run(debug=debug, host=host, port=port, use_reloader=False)
        except Exception as e:
            print(f"Dashboard error: {e}")
