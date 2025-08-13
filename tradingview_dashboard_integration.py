# tradingview_dashboard_integration.py
import dash
from dash import dcc, html, Input, Output, clientside_callback
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
import threading
import time
from flask import Flask, render_template_string

class TradingViewDashboardIntegration:
    def __init__(self, trading_bot=None):
        self.trading_bot = trading_bot
        self.app = dash.Dash(__name__)
        self.logger = logging.getLogger(__name__)
        
        # AI Signals storage
        self.ai_signals = []
        self.account_data = {
            'balance': 1000000,
            'daily_pnl': 0,
            'accuracy': 0,
            'active_signals': 0
        }
        
        self.setup_layout()
        self.setup_callbacks()
        
    def add_ai_signal(self, symbol, signal_type, price, confidence, reasoning=""):
        """Add a new AI signal to the dashboard"""
        signal = {
            'id': len(self.ai_signals) + 1,
            'symbol': symbol,
            'type': signal_type,
            'price': price,
            'confidence': confidence,
            'time': datetime.now().strftime('%H:%M:%S'),
            'timestamp': datetime.now().isoformat(),
            'reasoning': reasoning,
            'source': 'AI_Bot'
        }
        
        self.ai_signals.insert(0, signal)  # Add to beginning
        if len(self.ai_signals) > 50:  # Keep only last 50 signals
            self.ai_signals.pop()
            
        self.logger.info(f"📊 New signal added: {signal_type} {symbol} @ {price}")
        return signal
    
    def get_tradingview_widget_config(self, symbol="XAUUSD", container_id="tradingview_chart"):
        """Generate TradingView widget configuration"""
        return {
            "autosize": True,
            "symbol": self.get_tradingview_symbol(symbol),
            "interval": "15",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#1e3c72",
            "enable_publishing": False,
            "allow_symbol_change": True,
            "container_id": container_id,
            "studies": [
                "RSI@tv-basicstudies",
                "MACD@tv-basicstudies",
                "BB@tv-basicstudies"
            ],
            "overrides": {
                "mainSeriesProperties.candleStyle.upColor": "#00ff88",
                "mainSeriesProperties.candleStyle.downColor": "#ff4444",
                "mainSeriesProperties.candleStyle.borderUpColor": "#00ff88",
                "mainSeriesProperties.candleStyle.borderDownColor": "#ff4444",
                "paneProperties.background": "#1e3c72",
                "paneProperties.backgroundType": "solid"
            }
        }
    
    def get_tradingview_symbol(self, symbol):
        """Convert bot symbol to TradingView symbol format"""
        symbol_map = {
            'XAUUSD': 'FX:XAUUSD',
            'BTCUSD': 'BINANCE:BTCUSDT',
            'EURUSD': 'FX:EURUSD',
            'GBPUSD': 'FX:GBPUSD',
            'USDJPY': 'FX:USDJPY',
            'SPX500': 'SP:SPX',
            'NASDAQ': 'NASDAQ:NDX',
            'CRUDE': 'NYMEX:CL1!',
            'SILVER': 'FX:XAGUSD'
        }
        return symbol_map.get(symbol, f'FX:{symbol}')
    
    def setup_layout(self):
        """Setup the dashboard layout with TradingView integration"""
        
        # Generate JavaScript for TradingView widgets
        tradingview_js = self.generate_tradingview_javascript()
        
        self.app.layout = html.Div([
            # Custom CSS and JavaScript
            html.Head([
                html.Script(src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"),
                html.Style("""
                    .tradingview-widget-container {
                        height: 500px;
                        border-radius: 10px;
                        overflow: hidden;
                        background: #1e3c72;
                    }
                    .signal-overlay {
                        position: absolute;
                        top: 10px;
                        right: 10px;
                        background: rgba(0,0,0,0.8);
                        color: white;
                        padding: 8px 12px;
                        border-radius: 6px;
                        font-size: 0.9em;
                        z-index: 1000;
                        backdrop-filter: blur(5px);
                    }
                """)
            ]),
            
            # Header
            html.Div([
                html.H1("🤖 AI Trading Bot Dashboard", style={
                    'textAlign': 'center', 'color': 'white', 'marginBottom': '10px'
                }),
                html.P("Real-time Trading Signals with TradingView Integration", style={
                    'textAlign': 'center', 'color': '#cccccc', 'marginBottom': '20px'
                })
            ], style={
                'background': 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
                'padding': '30px', 'borderRadius': '15px', 'marginBottom': '20px'
            }),
            
            # Status and Controls
            html.Div([
                html.Div([
                    html.Div("🟢 LIVE", style={'color': '#00ff00', 'fontWeight': 'bold'}),
                    html.Div(id="status-time")
                ], style={'display': 'flex', 'justifyContent': 'space-between'}),
                
                html.Div([
                    html.Label("Symbol: "),
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
                        style={'width': '200px', 'color': 'black'}
                    ),
                    
                    html.Label("Timeframe: ", style={'marginLeft': '20px'}),
                    dcc.Dropdown(
                        id='timeframe-selector',
                        options=[
                            {'label': '1m', 'value': '1'},
                            {'label': '5m', 'value': '5'},
                            {'label': '15m', 'value': '15'},
                            {'label': '1h', 'value': '60'},
                            {'label': '4h', 'value': '240'},
                            {'label': '1D', 'value': 'D'},
                        ],
                        value='15',
                        style={'width': '100px', 'color': 'black'}
                    )
                ], style={'display': 'flex', 'alignItems': 'center', 'marginTop': '10px'})
            ], style={
                'background': 'rgba(255,255,255,0.1)', 'padding': '15px',
                'borderRadius': '10px', 'marginBottom': '20px', 'color': 'white'
            }),
            
            # Metrics Cards
            html.Div([
                html.Div([
                    html.H4("💰 Balance", style={'margin': '0', 'color': 'white'}),
                    html.H2(id="balance-display", style={'margin': '5px 0', 'color': '#00ff88'})
                ], className="metric-card"),
                
                html.Div([
                    html.H4("📈 Daily P&L", style={'margin': '0', 'color': 'white'}),
                    html.H2(id="pnl-display", style={'margin': '5px 0'})
                ], className="metric-card"),
                
                html.Div([
                    html.H4("🎯 Accuracy", style={'margin': '0', 'color': 'white'}),
                    html.H2(id="accuracy-display", style={'margin': '5px 0', 'color': '#9b59b6'})
                ], className="metric-card"),
                
                html.Div([
                    html.H4("📊 Active Signals", style={'margin': '0', 'color': 'white'}),
                    html.H2(id="signals-count", style={'margin': '5px 0', 'color': '#3498db'})
                ], className="metric-card")
            ], style={
                'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(200px, 1fr))',
                'gap': '15px', 'marginBottom': '20px'
            }),
            
            # Main Chart Section
            html.Div([
                html.Div([
                    html.H3("📈 Primary Chart with AI Signals", style={'color': 'white', 'marginBottom': '15px'}),
                    html.Div([
                        # TradingView Chart Container
                        html.Div(id="tradingview-primary", style={'height': '500px'}),
                        # Signal Overlay
                        html.Div(id="signal-overlay", className="signal-overlay")
                    ], style={'position': 'relative'})
                ], style={'width': '70%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                
                html.Div([
                    html.H3("🔔 Live AI Signals", style={'color': 'white', 'marginBottom': '15px'}),
                    html.Div(id="signals-feed", style={
                        'height': '500px', 'overflowY': 'auto',
                        'background': 'rgba(255,255,255,0.1)', 'padding': '10px',
                        'borderRadius': '10px'
                    })
                ], style={'width': '28%', 'display': 'inline-block', 'marginLeft': '2%', 'verticalAlign': 'top'})
            ], style={'marginBottom': '20px'}),
            
            # Multi-Symbol Charts
            html.Div([
                html.H3("📊 Multi-Symbol Analysis", style={'color': 'white', 'marginBottom': '15px'}),
                html.Div([
                    html.Div([
                        html.H4("Bitcoin (BTC/USD)", style={'color': 'white', 'textAlign': 'center'}),
                        html.Div(id="tradingview-btc", style={'height': '300px'})
                    ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '2%'}),
                    
                    html.Div([
                        html.H4("EUR/USD", style={'color': 'white', 'textAlign': 'center'}),
                        html.Div(id="tradingview-eur", style={'height': '300px'})
                    ], style={'width': '32%', 'display': 'inline-block', 'marginRight': '2%'}),
                    
                    html.Div([
                        html.H4("S&P 500", style={'color': 'white', 'textAlign': 'center'}),
                        html.Div(id="tradingview-spx", style={'height': '300px'})
                    ], style={'width': '32%', 'display': 'inline-block'})
                ])
            ], style={'marginBottom': '20px'}),
            
            # Auto-refresh component
            dcc.Interval(
                id='interval-component',
                interval=5000,  # Update every 5 seconds
                n_intervals=0
            ),
            
            # Store component for data
            dcc.Store(id='signals-store'),
            dcc.Store(id='account-store')
            
        ], style={
            'fontFamily': 'Segoe UI, Arial, sans-serif',
            'background': 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
            'minHeight': '100vh', 'padding': '20px'
        })
        
        # Add custom CSS
        self.app.index_string = '''
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>AI Trading Bot with TradingView</title>
                {%favicon%}
                {%css%}
                <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"></script>
                <style>
                    .metric-card {
                        background: rgba(255, 255, 255, 0.1);
                        padding: 20px;
                        border-radius: 10px;
                        text-align: center;
                        backdrop-filter: blur(10px);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        transition: transform 0.3s ease;
                    }
                    .metric-card:hover {
                        transform: translateY(-3px);
                        box-shadow: 0 5px 20px rgba(0,0,0,0.3);
                    }
                    .signal-item {
                        background: rgba(255, 255, 255, 0.1);
                        margin-bottom: 8px;
                        padding: 12px;
                        border-radius: 8px;
                        border-left: 4px solid;
                        color: white;
                        transition: all 0.3s ease;
                    }
                    .signal-item:hover {
                        background: rgba(255, 255, 255, 0.2);
                        transform: translateX(3px);
                    }
                    .signal-buy { border-left-color: #00ff88; }
                    .signal-sell { border-left-color: #ff4444; }
                    .signal-strong-buy { border-left-color: #00ff00; }
                    .signal-strong-sell { border-left-color: #ff0000; }
                    .signal-hold { border-left-color: #ffaa00; }
                    
                    /* TradingView container styling */
                    .tradingview-widget-container {
                        background: #1e3c72;
                        border-radius: 10px;
                        overflow: hidden;
                    }
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
                    // Initialize TradingView Widgets
                    function initTradingViewWidget(containerId, symbol, height = 500) {
                        if (typeof TradingView !== 'undefined') {
                            new TradingView.widget({
                                "autosize": true,
                                "symbol": symbol,
                                "interval": "15",
                                "timezone": "Etc/UTC",
                                "theme": "dark",
                                "style": "1",
                                "locale": "en",
                                "toolbar_bg": "#1e3c72",
                                "enable_publishing": false,
                                "allow_symbol_change": true,
                                "container_id": containerId,
                                "height": height,
                                "studies": [
                                    "RSI@tv-basicstudies",
                                    "MACD@tv-basicstudies"
                                ],
                                "overrides": {
                                    "mainSeriesProperties.candleStyle.upColor": "#00ff88",
                                    "mainSeriesProperties.candleStyle.downColor": "#ff4444",
                                    "mainSeriesProperties.candleStyle.borderUpColor": "#00ff88",
                                    "mainSeriesProperties.candleStyle.borderDownColor": "#ff4444",
                                    "paneProperties.background": "#1e3c72",
                                    "paneProperties.backgroundType": "solid"
                                }
                            });
                        }
                    }
                    
                    // Initialize widgets when page loads
                    document.addEventListener('DOMContentLoaded', function() {
                        setTimeout(function() {
                            initTradingViewWidget('tradingview-primary', 'FX:XAUUSD', 500);
                            initTradingViewWidget('tradingview-btc', 'BINANCE:BTCUSDT', 300);
                            initTradingViewWidget('tradingview-eur', 'FX:EURUSD', 300);
                            initTradingViewWidget('tradingview-spx', 'SP:SPX', 300);
                        }, 1000);
                    });
                </script>
            </body>
        </html>
        '''
    
    def setup_callbacks(self):
        """Setup dashboard callbacks"""
        
        @self.app.callback(
            [Output('balance-display', 'children'),
             Output('pnl-display', 'children'),
             Output('pnl-display', 'style'),
             Output('accuracy-display', 'children'),
             Output('signals-count', 'children'),
             Output('signals-feed', 'children'),
             Output('signal-overlay', 'children'),
             Output('status-time', 'children')],
            [Input('interval-component', 'n_intervals')]
        )
        def update_dashboard(n):
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Get real account data if available
            if self.trading_bot and hasattr(self.trading_bot, 'get_account_info'):
                try:
                    account = self.trading_bot.get_account_info()
                    if account:
                        self.account_data.update(account)
                except Exception as e:
                    self.logger.error(f"Error getting account data: {e}")
            
            # Update account display
            balance = f"${self.account_data['balance']:,.2f}"
            pnl = self.account_data['daily_pnl']
            pnl_display = f"{'+'if pnl >= 0 else ''}${pnl:,.2f}"
            pnl_style = {'margin': '5px 0', 'color': '#00ff88' if pnl >= 0 else '#ff4444'}
            
            # Calculate accuracy
            if self.ai_signals:
                high_conf_signals = sum(1 for s in self.ai_signals if s['confidence'] > 0.75)
                accuracy = f"{(high_conf_signals/len(self.ai_signals)*100):.0f}%" if self.ai_signals else "N/A"
            else:
                accuracy = "N/A"
            
            # Active signals count
            active_signals = len([s for s in self.ai_signals if s['type'] != 'HOLD'])
            
            # Generate signals feed
            signals_feed = []
            for signal in self.ai_signals[:10]:  # Show last 10 signals
                signals_feed.append(html.Div([
                    html.Div([
                        html.Strong(f"{signal['type']} {signal['symbol']}", 
                                  style={'fontSize': '1.1em'}),
                        html.Span(f" {signal['confidence']:.0%}", 
                                style={'float': 'right', 'opacity': '0.8'})
                    ]),
                    html.Div(f"${signal['price']:,.2f} @ {signal['time']}", 
                           style={'fontSize': '0.9em', 'opacity': '0.7'}),
                    html.Div(signal['reasoning'][:50] + "...", 
                           style={'fontSize': '0.8em', 'opacity': '0.6', 'marginTop': '5px'})
                ], className=f"signal-item signal-{signal['type'].lower().replace('_', '-')}"))
            
            # Current signal overlay
            latest_signal = self.ai_signals[0] if self.ai_signals else None
            overlay_content = ""
            if latest_signal:
                overlay_content = f"🤖 {latest_signal['type']} {latest_signal['symbol']} ({latest_signal['confidence']:.0%})"
            
            return (balance, pnl_display, pnl_style, accuracy, str(active_signals), 
                   signals_feed, overlay_content, current_time)
    
    def generate_tradingview_javascript(self):
        """Generate JavaScript code for TradingView widgets"""
        return """
        // TradingView Widget Integration
        window.aiSignals = [];
        
        function updateTradingViewSignals(signals) {
            window.aiSignals = signals;
            // Update signal overlays on charts
            updateSignalOverlays();
        }
        
        function updateSignalOverlays() {
            // Add visual indicators for AI signals on TradingView charts
            const overlayElement = document.getElementById('signal-overlay');
            if (overlayElement && window.aiSignals.length > 0) {
                const latestSignal = window.aiSignals[0];
                overlayElement.innerHTML = `🤖 ${latestSignal.type} ${latestSignal.symbol} (${(latestSignal.confidence * 100).toFixed(0)}%)`;
            }
        }
        """
    
    def simulate_ai_signals(self):
        """Simulate AI trading signals for demo"""
        symbols = ['XAUUSD', 'BTCUSD', 'EURUSD', 'GBPUSD']
        signal_types = ['BUY', 'SELL', 'STRONG_BUY', 'STRONG_SELL', 'HOLD']
        
        while True:
            try:
                symbol = np.random.choice(symbols)
                signal_type = np.random.choice(signal_types, p=[0.25, 0.25, 0.15, 0.15, 0.2])
                
                # Simulate realistic prices
                base_prices = {'XAUUSD': 2050, 'BTCUSD': 43000, 'EURUSD': 1.09, 'GBPUSD': 1.25}
                price = base_prices[symbol] + np.random.normal(0, base_prices[symbol] * 0.01)
                
                confidence = np.random.uniform(0.6, 0.95)
                
                reasoning_templates = {
                    'BUY': 'Bullish momentum detected with RSI oversold recovery',
                    'SELL': 'Bearish divergence on technical indicators',
                    'STRONG_BUY': 'Multiple confluences: Golden cross + breakout + high volume',
                    'STRONG_SELL': 'Death cross pattern with high selling pressure',
                    'HOLD': 'Mixed signals, awaiting clearer market direction'
                }
                
                reasoning = reasoning_templates[signal_type]
                
                # Add the signal
                self.add_ai_signal(symbol, signal_type, price, confidence, reasoning)
                
                # Update account data randomly
                if np.random.random() < 0.3:  # 30% chance
                    daily_change = np.random.normal(0, 1000)
                    self.account_data['daily_pnl'] += daily_change
                    self.account_data['balance'] += daily_change
                
                time.sleep(np.random.uniform(5, 15))  # Random interval between signals
                
            except Exception as e:
                self.logger.error(f"Error in signal simulation: {e}")
                time.sleep(5)
    
    def integrate_with_trading_bot(self, bot):
        """Integrate with existing trading bot"""
        self.trading_bot = bot
        
        # Hook into bot's signal generation
        if hasattr(bot, 'add_signal_callback'):
            bot.add_signal_callback(self.add_ai_signal)
        
        self.logger.info("✅ Integrated with trading bot")
    
    def run_server(self, host='127.0.0.1', port=8050, debug=False):
        """Run the dashboard server"""
        print(f"🚀 TradingView Dashboard starting at http://{host}:{port}")
        print("📊 Features:")
        print("   • Real-time TradingView charts")
        print("   • AI signal overlays")
        print("   • Multi-symbol analysis")
        print("   • Live account metrics")
        
        # Start signal simulation in background
        signal_thread = threading.Thread(target=self.simulate_ai_signals, daemon=True)
        signal_thread.start()
        
        try:
            self.app.run(debug=debug, host=host, port=port, use_reloader=False)
        except Exception as e:
            self.logger.error(f"Dashboard error: {e}")

# Usage example and integration
if __name__ == "__main__":
    # Create the TradingView integrated dashboard
    tv_dashboard = TradingViewDashboardIntegration()
    
    # If you have an existing trading bot, integrate it:
    # tv_dashboard.integrate_with_trading_bot(your_existing_bot)
    
    # Add some initial demo signals
    demo_signals = [
        ("XAUUSD", "STRONG_BUY", 2048.50, 0.92, "Golden cross + RSI oversold recovery + breakout above resistance"),
        ("BTCUSD", "SELL", 42850.00, 0.78, "Bearish divergence on RSI + rejection at major resistance"),
        ("EURUSD", "BUY", 1.0925, 0.85, "Bullish flag pattern completion + ECB policy supportive"),
        ("XAUUSD", "HOLD", 2045.30, 0.65, "Consolidation phase with mixed technical signals"),
    ]
    
    for symbol, signal_type, price, confidence, reasoning in demo_signals:
        tv_dashboard.add_ai_signal(symbol, signal_type, price, confidence, reasoning)
    
    # Run the dashboard
    tv_dashboard.run_server(host='127.0.0.1', port=8050, debug=False)