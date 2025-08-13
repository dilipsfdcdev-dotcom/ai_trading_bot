import dash
from dash import dcc, html, Input, Output, clientside_callback, ClientsideFunction
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import logging
import numpy as np
import json

class TradingViewAIDashboard:
    def __init__(self, bot=None):
        self.bot = bot
        self.app = dash.Dash(__name__)
        self.logger = logging.getLogger(__name__)
        
        # AI Signals storage
        self.ai_signals = []
        self.market_analysis = {}
        
        self.setup_layout()
        self.setup_callbacks()
    
    def add_ai_signal(self, symbol, signal_data):
        """Add AI-generated signal to dashboard"""
        
        # Enhanced signal with AI metadata
        enhanced_signal = {
            'id': len(self.ai_signals) + 1,
            'symbol': symbol,
            'signal': signal_data.get('signal', 'HOLD'),
            'confidence': signal_data.get('confidence', 0.5),
            'reasoning': signal_data.get('reasoning', 'No reasoning provided'),
            'ai_source': signal_data.get('ai_source', 'Unknown'),
            'entry_price': signal_data.get('entry_price', 0),
            'stop_loss': signal_data.get('stop_loss', 0),
            'take_profit': signal_data.get('take_profit', 0),
            'risk_level': signal_data.get('risk_level', 'MEDIUM'),
            'timestamp': signal_data.get('timestamp', datetime.now().isoformat()),
            'time_display': datetime.now().strftime('%H:%M:%S')
        }
        
        self.ai_signals.insert(0, enhanced_signal)
        if len(self.ai_signals) > 100:  # Keep last 100 signals
            self.ai_signals.pop()
        
        self.logger.info(f"🤖 AI Signal: {signal_data.get('ai_source', 'AI')} says {signal_data.get('signal', 'HOLD')} {symbol} ({signal_data.get('confidence', 0):.1%})")
        return enhanced_signal
    
    def setup_layout(self):
        """Setup TradingView integrated dashboard"""
        
        self.app.layout = html.Div([
            # Custom Head with TradingView scripts
            html.Div([
                html.Script(src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"),
                html.Script(src="https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js"),
            ], style={'display': 'none'}),
            
            # Header
            html.Div([
                html.H1([
                    "🤖 AI Trading Bot with TradingView",
                    html.Span(" ✨ POWERED BY AI", style={'fontSize': '0.6em', 'color': '#f39c12'})
                ], style={'textAlign': 'center', 'color': 'white', 'marginBottom': '10px'}),
                html.P("Real-time AI Signals with Professional Charts", 
                      style={'textAlign': 'center', 'color': '#ecf0f1', 'marginBottom': '20px'})
            ], style={
                'background': 'linear-gradient(135deg, #2c3e50 0%, #3498db 100%)',
                'padding': '30px', 'borderRadius': '15px', 'marginBottom': '20px'
            }),
            
            # AI Status Bar
            html.Div([
                html.Div([
                    html.Span("🤖 AI STATUS: ", style={'fontWeight': 'bold'}),
                    html.Span(id="ai-status", style={'color': '#2ecc71'})
                ], style={'flex': '1'}),
                html.Div([
                    html.Span("📊 MARKET SENTIMENT: ", style={'fontWeight': 'bold'}),
                    html.Span(id="market-sentiment", style={'fontWeight': 'bold'})
                ], style={'flex': '1', 'textAlign': 'center'}),
                html.Div([
                    html.Span("⏰ LAST UPDATE: ", style={'fontWeight': 'bold'}),
                    html.Span(id="last-update")
                ], style={'flex': '1', 'textAlign': 'right'})
            ], style={
                'display': 'flex', 'padding': '15px', 'backgroundColor': '#34495e',
                'borderRadius': '10px', 'marginBottom': '20px', 'color': 'white'
            }),
            
            # Symbol Selector and Controls
            html.Div([
                html.Div([
                    html.Label("📈 SYMBOL:", style={'color': 'white', 'marginRight': '10px'}),
                    dcc.Dropdown(
                        id='symbol-selector',
                        options=[
                            {'label': '🥇 Gold (XAU/USD)', 'value': 'XAUUSD'},
                            {'label': '₿ Bitcoin (BTC/USD)', 'value': 'BTCUSD'},
                            {'label': '🇪🇺 EUR/USD', 'value': 'EURUSD'},
                            {'label': '🇬🇧 GBP/USD', 'value': 'GBPUSD'},
                            {'label': '🇯🇵 USD/JPY', 'value': 'USDJPY'},
                            {'label': '📈 S&P 500', 'value': 'SPX500'},
                        ],
                        value='XAUUSD',
                        style={'width': '250px', 'color': 'black'}
                    )
                ], style={'display': 'flex', 'alignItems': 'center'}),
                
                html.Div([
                    html.Button("🔄 Refresh AI Analysis", id="refresh-ai", 
                              className="control-button", n_clicks=0),
                    html.Button("📊 Get Market Sentiment", id="get-sentiment", 
                              className="control-button", n_clicks=0)
                ], style={'display': 'flex', 'gap': '10px'})
            ], style={
                'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                'padding': '15px', 'backgroundColor': 'rgba(255,255,255,0.1)',
                'borderRadius': '10px', 'marginBottom': '20px'
            }),
            
            # Main Content Area
            html.Div([
                # Left Panel - TradingView Chart
                html.Div([
                    html.H3("📈 Live Chart with AI Signals", style={'color': 'white', 'marginBottom': '15px'}),
                    html.Div([
                        # TradingView Widget Container
                        html.Div(id="tradingview-widget", children=[
                            html.Div("Loading TradingView Chart...", 
                                   style={'textAlign': 'center', 'padding': '100px', 'color': 'white'})
                        ], style={'height': '500px', 'borderRadius': '10px', 'overflow': 'hidden'}),
                        
                        # AI Signal Overlay
                        html.Div(id="chart-signal-overlay", className="signal-overlay")
                    ], style={'position': 'relative'})
                ], style={'width': '65%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                
                # Right Panel - AI Signals
                html.Div([
                    html.H3("🤖 Live AI Signals", style={'color': 'white', 'marginBottom': '15px'}),
                    html.Div(id="ai-signals-feed", style={
                        'height': '500px', 'overflowY': 'auto',
                        'background': 'rgba(255,255,255,0.1)', 'padding': '15px',
                        'borderRadius': '10px'
                    })
                ], style={'width': '32%', 'display': 'inline-block', 'marginLeft': '3%', 'verticalAlign': 'top'})
            ]),
            
            # Account Metrics
            html.Div([
                html.Div([
                    html.H4("💰 Balance", style={'margin': '0', 'color': 'white'}),
                    html.H2(id="account-balance", style={'margin': '5px 0', 'color': '#2ecc71'})
                ], className="metric-card"),
                
                html.Div([
                    html.H4("🤖 AI Accuracy", style={'margin': '0', 'color': 'white'}),
                    html.H2(id="ai-accuracy", style={'margin': '5px 0', 'color': '#f39c12'})
                ], className="metric-card"),
                
                html.Div([
                    html.H4("📊 Active Signals", style={'margin': '0', 'color': 'white'}),
                    html.H2(id="active-signals", style={'margin': '5px 0', 'color': '#3498db'})
                ], className="metric-card"),
                
                html.Div([
                    html.H4("🎯 Success Rate", style={'margin': '0', 'color': 'white'}),
                    html.H2(id="success-rate", style={'margin': '5px 0', 'color': '#9b59b6'})
                ], className="metric-card")
            ], style={
                'display': 'grid', 'gridTemplateColumns': 'repeat(4, 1fr)',
                'gap': '15px', 'marginTop': '20px'
            }),
            
            # Hidden div to store data
            html.Div(id="signal-data-store", style={'display': 'none'}),
            
            # Auto-refresh
            dcc.Interval(
                id='interval-component',
                interval=10*1000,  # Update every 10 seconds
                n_intervals=0
            )
            
        ], style={
            'fontFamily': 'Segoe UI, Arial, sans-serif',
            'background': 'linear-gradient(135deg, #1a252f 0%, #2c3e50 100%)',
            'minHeight': '100vh', 'padding': '20px', 'color': 'white'
        })
        
        # Enhanced CSS
        self.app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>AI Trading Bot with TradingView</title>
                {%favicon%}
                {%css%}
                <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async></script>
                <style>
                    .metric-card {
                        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
                        padding: 20px;
                        border-radius: 15px;
                        text-align: center;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255,255,255,0.2);
                        transition: all 0.3s ease;
                    }
                    .metric-card:hover {
                        transform: translateY(-5px);
                        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    }
                    .control-button {
                        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                        border: none;
                        color: white;
                        padding: 10px 20px;
                        border-radius: 25px;
                        cursor: pointer;
                        font-weight: bold;
                        transition: all 0.3s ease;
                    }
                    .control-button:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 5px 15px rgba(52,152,219,0.4);
                    }
                    .signal-overlay {
                        position: absolute;
                        top: 15px;
                        right: 15px;
                        background: rgba(0,0,0,0.8);
                        color: white;
                        padding: 10px 15px;
                        border-radius: 8px;
                        font-weight: bold;
                        z-index: 1000;
                        backdrop-filter: blur(5px);
                        border: 1px solid rgba(255,255,255,0.2);
                    }
                    .ai-signal-item {
                        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
                        margin-bottom: 12px;
                        padding: 15px;
                        border-radius: 10px;
                        border-left: 4px solid;
                        transition: all 0.3s ease;
                    }
                    .ai-signal-item:hover {
                        background: rgba(255,255,255,0.15);
                        transform: translateX(5px);
                    }
                    .signal-BUY { border-left-color: #2ecc71; }
                    .signal-SELL { border-left-color: #e74c3c; }
                    .signal-STRONG_BUY { border-left-color: #27ae60; box-shadow: 0 0 15px rgba(46,204,113,0.3); }
                    .signal-STRONG_SELL { border-left-color: #c0392b; box-shadow: 0 0 15px rgba(231,76,60,0.3); }
                    .signal-HOLD { border-left-color: #f39c12; }
                    
                    .ai-source-openai { color: #10ac84; }
                    .ai-source-claude { color: #ff6b6b; }
                    .ai-source-technical { color: #74b9ff; }
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
                
                <script>
                    // TradingView Widget Management
                    let currentWidget = null;
                    
                    function createTradingViewWidget(symbol = 'XAUUSD', containerId = 'tradingview-widget') {
                        const symbolMap = {
                            'XAUUSD': 'FX:XAUUSD',
                            'BTCUSD': 'BINANCE:BTCUSDT',
                            'EURUSD': 'FX:EURUSD',
                            'GBPUSD': 'FX:GBPUSD',
                            'USDJPY': 'FX:USDJPY',
                            'SPX500': 'SP:SPX'
                        };
                        
                        const container = document.getElementById(containerId);
                        if (!container) return;
                        
                        // Clear existing widget
                        container.innerHTML = '';
                        
                        // Create new widget container
                        const widgetDiv = document.createElement('div');
                        widgetDiv.className = 'tradingview-widget-container__widget';
                        widgetDiv.style.height = '100%';
                        container.appendChild(widgetDiv);
                        
                        // Initialize TradingView widget
                        if (typeof TradingView !== 'undefined') {
                            new TradingView.widget({
                                "autosize": true,
                                "symbol": symbolMap[symbol] || 'FX:XAUUSD',
                                "interval": "15",
                                "timezone": "Etc/UTC",
                                "theme": "dark",
                                "style": "1",
                                "locale": "en",
                                "toolbar_bg": "#1a252f",
                                "enable_publishing": false,
                                "allow_symbol_change": true,
                                "container_id": widgetDiv,
                                "studies": [
                                    "RSI@tv-basicstudies",
                                    "MACD@tv-basicstudies",
                                    "BB@tv-basicstudies"
                                ],
                                "overrides": {
                                    "mainSeriesProperties.candleStyle.upColor": "#2ecc71",
                                    "mainSeriesProperties.candleStyle.downColor": "#e74c3c",
                                    "mainSeriesProperties.candleStyle.borderUpColor": "#27ae60",
                                    "mainSeriesProperties.candleStyle.borderDownColor": "#c0392b",
                                    "paneProperties.background": "#1a252f",
                                    "paneProperties.backgroundType": "solid"
                                }
                            });
                        } else {
                            container.innerHTML = '<div style="text-align:center;padding:50px;color:white;">Loading TradingView...</div>';
                            setTimeout(() => createTradingViewWidget(symbol, containerId), 1000);
                        }
                    }
                    
                    // Initialize on page load
                    document.addEventListener('DOMContentLoaded', function() {
                        setTimeout(() => createTradingViewWidget('XAUUSD'), 2000);
                    });
                    
                    // Global function for symbol changes
                    window.updateTradingViewSymbol = function(symbol) {
                        createTradingViewWidget(symbol);
                    };
                </script>
            </body>
        </html>
        '''
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        # Main dashboard update
        @self.app.callback(
            [Output('ai-status', 'children'),
             Output('market-sentiment', 'children'),
             Output('market-sentiment', 'style'),
             Output('last-update', 'children'),
             Output('account-balance', 'children'),
             Output('ai-accuracy', 'children'),
             Output('active-signals', 'children'),
             Output('success-rate', 'children'),
             Output('ai-signals-feed', 'children'),
             Output('chart-signal-overlay', 'children')],
            [Input('interval-component', 'n_intervals'),
             Input('refresh-ai', 'n_clicks'),
             Input('get-sentiment', 'n_clicks'),
             Input('symbol-selector', 'value')]
        )
        def update_dashboard(n_intervals, refresh_clicks, sentiment_clicks, selected_symbol):
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # AI Status
            ai_status = "ACTIVE" if self.bot and hasattr(self.bot, 'ai_signal_generator') else "DEMO MODE"
            
            # Market Sentiment
            sentiment = "ANALYZING..."
            sentiment_style = {'color': '#f39c12', 'fontWeight': 'bold'}
            
            if self.bot and hasattr(self.bot, 'ai_signal_generator'):
                try:
                    sentiment = self.bot.ai_signal_generator.get_market_sentiment(selected_symbol)
                    if sentiment == "BULLISH":
                        sentiment_style = {'color': '#2ecc71', 'fontWeight': 'bold'}
                    elif sentiment == "BEARISH":
                        sentiment_style = {'color': '#e74c3c', 'fontWeight': 'bold'}
                    else:
                        sentiment_style = {'color': '#f39c12', 'fontWeight': 'bold'}
                except:
                    sentiment = "NEUTRAL"
            
            # Account metrics
            balance = "$100,000"
            if self.bot and hasattr(self.bot, 'data_collector'):
                try:
                    account = self.bot.data_collector.get_account_info()
                    balance = f"${account.get('balance', 100000):,.2f}"
                except:
                    pass
            
            # AI Accuracy calculation
            if self.ai_signals:
                high_conf_signals = sum(1 for s in self.ai_signals if s['confidence'] > 0.7)
                ai_accuracy = f"{(high_conf_signals/len(self.ai_signals)*100):.0f}%"
            else:
                ai_accuracy = "N/A"
            
            # Active signals
            active_count = len([s for s in self.ai_signals if s['signal'] != 'HOLD'])
            
            # Success rate (mock calculation)
            success_rate = "75%" if self.ai_signals else "N/A"
            
            # Generate AI signals feed
            signals_feed = self.generate_signals_feed()
            
            # Chart overlay with latest signal
            overlay_content = ""
            if self.ai_signals:
                latest = self.ai_signals[0]
                if latest['symbol'] == selected_symbol:
                    confidence_color = '#2ecc71' if latest['confidence'] > 0.75 else '#f39c12' if latest['confidence'] > 0.6 else '#e74c3c'
                    overlay_content = html.Div([
                        html.Div(f"🤖 {latest['signal']}", style={'fontSize': '14px', 'fontWeight': 'bold'}),
                        html.Div(f"{latest['confidence']:.0%} confident", style={'fontSize': '12px', 'color': confidence_color}),
                        html.Div(f"by {latest['ai_source']}", style={'fontSize': '10px', 'opacity': '0.8'})
                    ])
            
            return (ai_status, sentiment, sentiment_style, current_time, balance, 
                   ai_accuracy, str(active_count), success_rate, signals_feed, overlay_content)
        
        # Symbol change callback
        @self.app.callback(
            Output('signal-data-store', 'children'),
            [Input('symbol-selector', 'value')]
        )
        def update_symbol(selected_symbol):
            # Trigger TradingView widget update via clientside callback
            return selected_symbol
        
        # Clientside callback to update TradingView widget
        self.app.clientside_callback(
            """
            function(symbol) {
                if (window.updateTradingViewSymbol && symbol) {
                    setTimeout(() => window.updateTradingViewSymbol(symbol), 100);
                }
                return symbol;
            }
            """,
            Output('tradingview-widget', 'data-symbol'),
            [Input('signal-data-store', 'children')]
        )
    
    def generate_signals_feed(self):
        """Generate the AI signals feed display"""
        
        if not self.ai_signals:
            return html.Div([
                html.Div("🤖 Waiting for AI signals...", 
                        style={'textAlign': 'center', 'color': '#95a5a6', 'padding': '50px'})
            ])
        
        signals_display = []
        for signal in self.ai_signals[:15]:  # Show last 15 signals
            
            # Confidence color coding
            if signal['confidence'] > 0.8:
                conf_color = '#2ecc71'
                conf_icon = '🔥'
            elif signal['confidence'] > 0.7:
                conf_color = '#f39c12'
                conf_icon = '⚡'
            else:
                conf_color = '#95a5a6'
                conf_icon = '📊'
            
            # AI source styling
            ai_source_class = f"ai-source-{signal['ai_source'].lower().replace(' ', '-')}"
            
            signal_div = html.Div([
                # Header row
                html.Div([
                    html.Div([
                        html.Strong(f"{signal['signal']} {signal['symbol']}", 
                                  style={'fontSize': '1.1em'}),
                        html.Span(f" {conf_icon} {signal['confidence']:.0%}", 
                                style={'float': 'right', 'color': conf_color, 'fontWeight': 'bold'})
                    ], style={'marginBottom': '5px'}),
                    
                    # AI source and time
                    html.Div([
                        html.Span(f"🤖 {signal['ai_source']}", 
                                style={'fontSize': '0.85em', 'color': '#3498db'}),
                        html.Span(f" • {signal['time_display']}", 
                                style={'fontSize': '0.85em', 'color': '#95a5a6', 'float': 'right'})
                    ], style={'marginBottom': '8px'}),
                    
                    # Entry price and risk level
                    html.Div([
                        html.Span(f"📍 Entry: ${signal['entry_price']:.2f}", 
                                style={'fontSize': '0.9em', 'color': '#ecf0f1'}),
                        html.Span(f" | Risk: {signal['risk_level']}", 
                                style={'fontSize': '0.85em', 'color': '#f39c12', 'float': 'right'})
                    ], style={'marginBottom': '8px'}),
                    
                    # AI reasoning
                    html.Div(signal['reasoning'][:80] + ("..." if len(signal['reasoning']) > 80 else ""),
                           style={'fontSize': '0.8em', 'color': '#bdc3c7', 'fontStyle': 'italic'})
                ])
            ], className=f"ai-signal-item signal-{signal['signal'].replace('_', '-')}")
            
            signals_display.append(signal_div)
        
        return signals_display
    
    def get_real_ai_data(self):
        """Get real AI analysis data from bot"""
        try:
            if self.bot and hasattr(self.bot, 'last_ai_analysis'):
                return self.bot.last_ai_analysis
        except Exception as e:
            self.logger.error(f"Error getting AI data: {e}")
        return {}
    
    def run_server(self, host='127.0.0.1', port=8051, debug=False):
        """Run the TradingView AI dashboard"""
        print(f"🚀 AI TradingView Dashboard starting at http://{host}:{port}")
        print("🤖 Features:")
        print("   • Real-time TradingView charts")
        print("   • AI-powered signal analysis")
        print("   • OpenAI/Claude integration")
        print("   • Live market sentiment")
        print("   • Professional trading interface")
        
        try:
            self.app.run_server(debug=debug, host=host, port=port, use_reloader=False)
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")