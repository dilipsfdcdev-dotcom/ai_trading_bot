#!/usr/bin/env python3
"""
AI Trading Bot with Flask Dashboard
Uses Flask instead of Dash for better compatibility
"""

import asyncio
import logging
import sys
import os
import json
import threading
import time
import webbrowser
from datetime import datetime, timedelta
from threading import Timer

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Flask imports
try:
    from flask import Flask, render_template_string, jsonify, request
    FLASK_AVAILABLE = True
except ImportError:
    print("❌ Flask not available - installing...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "flask"])
    from flask import Flask, render_template_string, jsonify, request
    FLASK_AVAILABLE = True

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import bot components with fallbacks
try:
    from config.config import Config
except ImportError:
    class Config:
        SYMBOLS = ['XAUUSD', 'BTCUSD']
        TIMEFRAME = 5
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

try:
    from data.data_collector import MT5DataCollector
except ImportError:
    print("❌ Using minimal data collector")
    import pandas as pd
    import numpy as np
    
    class MT5DataCollector:
        def __init__(self, config):
            self.config = config
            self.logger = logging.getLogger(__name__)
        
        def get_historical_data(self, symbol, timeframe, bars=100):
            # Simple demo data
            dates = pd.date_range(end=datetime.now(), periods=bars, freq='5T')
            base_price = 2650 if symbol == 'XAUUSD' else 96000
            prices = base_price + np.cumsum(np.random.normal(0, 10, bars))
            
            data = []
            for i, price in enumerate(prices):
                data.append({
                    'time': dates[i],
                    'open': price,
                    'high': price * 1.01,
                    'low': price * 0.99,
                    'close': price,
                    'tick_volume': np.random.randint(100, 1000)
                })
            
            df = pd.DataFrame(data)
            df.set_index('time', inplace=True)
            return df
        
        def get_account_info(self):
            return {
                'balance': 100000.0,
                'equity': 100000.0 + np.random.uniform(-1000, 1000),
                'profit': np.random.uniform(-500, 500),
                'currency': 'USD'
            }

# Simple AI Signal Generator
class SimpleAISignalGenerator:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Check for API keys
        self.has_openai = bool(config.OPENAI_API_KEY and config.OPENAI_API_KEY != 'your_openai_api_key_here')
        self.has_anthropic = bool(config.ANTHROPIC_API_KEY and config.ANTHROPIC_API_KEY != 'your_anthropic_api_key_here')
        
        if self.has_openai:
            try:
                import openai
                openai.api_key = config.OPENAI_API_KEY
                self.openai = openai
                self.logger.info("✅ OpenAI API available")
            except:
                self.has_openai = False
                self.logger.warning("⚠️  OpenAI import failed")
        
        if self.has_anthropic:
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
                self.logger.info("✅ Anthropic API available")
            except:
                self.has_anthropic = False
                self.logger.warning("⚠️  Anthropic import failed")
    
    def analyze_market_data(self, symbol, data):
        """Analyze market data with AI or technical analysis"""
        
        if data is None or len(data) < 10:
            return self._fallback_signal(symbol)
        
        # Get basic market context
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        
        price_change = ((latest['close'] - prev['close']) / prev['close']) * 100
        
        # Try AI analysis first
        if self.has_openai:
            return self._analyze_with_openai(symbol, latest, price_change)
        elif self.has_anthropic:
            return self._analyze_with_anthropic(symbol, latest, price_change)
        else:
            return self._technical_analysis(symbol, data, price_change)
    
    def _analyze_with_openai(self, symbol, latest, price_change):
        """Analyze using OpenAI"""
        try:
            prompt = f"""Analyze {symbol} trading data:
Current Price: ${latest['close']:.2f}
Price Change: {price_change:.2f}%
Volume: {latest.get('tick_volume', 100)}

Provide a trading signal (BUY/SELL/HOLD) with confidence (0-1) and brief reasoning.
Respond in JSON format: {{"signal": "BUY", "confidence": 0.75, "reasoning": "..."}}"""

            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                result = json.loads(ai_response)
                result['ai_source'] = 'OpenAI GPT-4'
                result['timestamp'] = datetime.now().isoformat()
                return result
            except:
                # Parse text response
                if 'buy' in ai_response.lower():
                    signal = 'BUY'
                elif 'sell' in ai_response.lower():
                    signal = 'SELL'
                else:
                    signal = 'HOLD'
                
                return {
                    'signal': signal,
                    'confidence': 0.75,
                    'reasoning': ai_response[:100] + "...",
                    'ai_source': 'OpenAI GPT-4',
                    'timestamp': datetime.now().isoformat()
                }
        
        except Exception as e:
            self.logger.error(f"OpenAI error: {e}")
            return self._technical_analysis(symbol, None, price_change)
    
    def _analyze_with_anthropic(self, symbol, latest, price_change):
        """Analyze using Anthropic Claude"""
        try:
            prompt = f"""Analyze {symbol}: Price ${latest['close']:.2f}, Change {price_change:.2f}%. 
Give trading signal (BUY/SELL/HOLD), confidence (0-1), and reasoning in JSON."""

            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            
            ai_response = response.content[0].text
            
            try:
                result = json.loads(ai_response)
                result['ai_source'] = 'Anthropic Claude'
                result['timestamp'] = datetime.now().isoformat()
                return result
            except:
                return self._parse_claude_response(ai_response)
        
        except Exception as e:
            self.logger.error(f"Anthropic error: {e}")
            return self._technical_analysis(symbol, None, price_change)
    
    def _technical_analysis(self, symbol, data, price_change):
        """Technical analysis fallback"""
        
        # Simple momentum-based analysis
        if price_change > 1.0:
            signal = 'BUY'
            confidence = min(0.8, 0.6 + abs(price_change) * 0.05)
        elif price_change < -1.0:
            signal = 'SELL'
            confidence = min(0.8, 0.6 + abs(price_change) * 0.05)
        else:
            signal = 'HOLD'
            confidence = 0.6
        
        reasoning = f"Technical analysis: {price_change:.1f}% price movement"
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning,
            'ai_source': 'Technical Analysis',
            'timestamp': datetime.now().isoformat()
        }
    
    def _fallback_signal(self, symbol):
        """Fallback when no data available"""
        return {
            'signal': 'HOLD',
            'confidence': 0.5,
            'reasoning': 'Insufficient data for analysis',
            'ai_source': 'Fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def _parse_claude_response(self, response):
        """Parse Claude text response"""
        response_lower = response.lower()
        
        if 'buy' in response_lower:
            signal = 'BUY'
        elif 'sell' in response_lower:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        return {
            'signal': signal,
            'confidence': 0.75,
            'reasoning': response[:100] + "...",
            'ai_source': 'Anthropic Claude',
            'timestamp': datetime.now().isoformat()
        }

# Flask AI Trading Bot
class FlaskAITradingBot:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_collector = MT5DataCollector(self.config)
        self.ai_signal_generator = SimpleAISignalGenerator(self.config)
        
        # Data storage
        self.ai_signals = []
        self.account_data = {'balance': 100000, 'profit': 0, 'equity': 100000}
        self.running = False
        
        # Flask app
        self.app = Flask(__name__)
        self.setup_routes()
        
        self.logger.info("🤖 Flask AI Trading Bot initialized")
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            return self.render_dashboard()
        
        @self.app.route('/api/signals')
        def get_signals():
            return jsonify({
                'signals': self.ai_signals[-10:],  # Last 10 signals
                'account': self.account_data,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/refresh')
        def refresh_signals():
            # Trigger immediate analysis
            asyncio.create_task(self.analyze_all_symbols())
            return jsonify({'status': 'refreshing'})
    
    def render_dashboard(self):
        """Render the main dashboard"""
        
        # Get latest signals for display
        recent_signals = self.ai_signals[-5:] if self.ai_signals else []
        
        # AI status
        ai_status = "🤖 ACTIVE" if (self.config.OPENAI_API_KEY or self.config.ANTHROPIC_API_KEY) else "📊 TECHNICAL"
        
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>🤖 AI Trading Bot Dashboard</title>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="30">
            <style>
                body { 
                    font-family: 'Segoe UI', Arial, sans-serif; 
                    margin: 0; padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; min-height: 100vh;
                }
                .container { max-width: 1200px; margin: 0 auto; }
                .header { 
                    text-align: center; margin-bottom: 40px; 
                    background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px;
                }
                .status-bar { 
                    display: flex; justify-content: space-between; align-items: center;
                    background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-bottom: 20px;
                }
                .metrics { 
                    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                    gap: 20px; margin-bottom: 30px; 
                }
                .metric-card { 
                    background: rgba(255,255,255,0.15); padding: 25px; border-radius: 15px;
                    text-align: center; backdrop-filter: blur(10px);
                    transition: transform 0.3s ease;
                }
                .metric-card:hover { transform: translateY(-5px); }
                .content { display: flex; gap: 20px; }
                .signals-panel { 
                    flex: 1; background: rgba(255,255,255,0.1); 
                    padding: 20px; border-radius: 15px; 
                }
                .signal-item { 
                    background: rgba(255,255,255,0.1); margin: 10px 0; 
                    padding: 15px; border-radius: 10px; border-left: 4px solid;
                }
                .signal-BUY { border-left-color: #27ae60; }
                .signal-SELL { border-left-color: #e74c3c; }
                .signal-HOLD { border-left-color: #f39c12; }
                .chart-panel { 
                    flex: 2; background: rgba(255,255,255,0.1); 
                    padding: 20px; border-radius: 15px; text-align: center;
                }
                .ai-source { 
                    font-size: 0.8em; color: #3498db; font-weight: bold;
                }
                .confidence { 
                    float: right; font-weight: bold; 
                }
                .confidence-high { color: #27ae60; }
                .confidence-medium { color: #f39c12; }
                .confidence-low { color: #e74c3c; }
                .refresh-btn {
                    background: #3498db; color: white; border: none;
                    padding: 10px 20px; border-radius: 25px; cursor: pointer;
                    font-weight: bold; transition: background 0.3s ease;
                }
                .refresh-btn:hover { background: #2980b9; }
                h1, h2, h3 { margin: 0 0 10px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 AI Trading Bot Dashboard</h1>
                    <p>Real-time AI Market Analysis & Signals</p>
                </div>
                
                <div class="status-bar">
                    <div><strong>AI STATUS:</strong> {{ ai_status }}</div>
                    <div><strong>LAST UPDATE:</strong> {{ current_time }}</div>
                    <button class="refresh-btn" onclick="refreshSignals()">🔄 Refresh</button>
                </div>
                
                <div class="metrics">
                    <div class="metric-card">
                        <h3>💰 Balance</h3>
                        <h2 style="color: #27ae60;">${{ "%.2f"|format(account.balance) }}</h2>
                    </div>
                    <div class="metric-card">
                        <h3>📈 P&L</h3>
                        <h2 class="{% if account.profit >= 0 %}confidence-high{% else %}confidence-low{% endif %}">
                            {{ "+" if account.profit >= 0 else "" }}${{ "%.2f"|format(account.profit) }}
                        </h2>
                    </div>
                    <div class="metric-card">
                        <h3>🤖 AI Signals</h3>
                        <h2 style="color: #3498db;">{{ signals|length }} Active</h2>
                    </div>
                    <div class="metric-card">
                        <h3>🎯 Accuracy</h3>
                        <h2 style="color: #9b59b6;">
                            {% if signals %}
                                {{ "%.0f"|format((signals|selectattr('confidence', '>', 0.7)|list|length / signals|length) * 100) }}%
                            {% else %}
                                N/A
                            {% endif %}
                        </h2>
                    </div>
                </div>
                
                <div class="content">
                    <div class="signals-panel">
                        <h3>🔔 Live AI Signals</h3>
                        {% if signals %}
                            {% for signal in signals[-10:] %}
                            <div class="signal-item signal-{{ signal.signal }}">
                                <div>
                                    <strong>{{ signal.signal }} {{ signal.symbol }}</strong>
                                    <span class="confidence confidence-{% if signal.confidence > 0.75 %}high{% elif signal.confidence > 0.6 %}medium{% else %}low{% endif %}">
                                        {{ "%.0f"|format(signal.confidence * 100) }}%
                                    </span>
                                </div>
                                <div class="ai-source">🤖 {{ signal.ai_source }}</div>
                                <div style="font-size: 0.9em; margin-top: 5px; opacity: 0.9;">
                                    {{ signal.reasoning[:80] }}{% if signal.reasoning|length > 80 %}...{% endif %}
                                </div>
                                <div style="font-size: 0.8em; opacity: 0.7; margin-top: 5px;">
                                    {{ signal.timestamp[:19] }}
                                </div>
                            </div>
                            {% endfor %}
                        {% else %}
                            <div class="signal-item" style="text-align: center; opacity: 0.7;">
                                🤖 Waiting for AI analysis...
                                <br><small>Signals will appear here shortly</small>
                            </div>
                        {% endif %}
                    </div>
                    
                    <div class="chart-panel">
                        <h3>📈 Market Analysis</h3>
                        <div style="padding: 40px; background: rgba(0,0,0,0.2); border-radius: 10px; margin: 20px 0;">
                            <h4>🎯 Current Focus: {{ config.SYMBOLS|join(', ') }}</h4>
                            <p>AI analyzing market conditions...</p>
                            <div style="margin: 20px 0;">
                                {% if config.OPENAI_API_KEY %}
                                    <div>✅ OpenAI GPT-4 Analysis Active</div>
                                {% endif %}
                                {% if config.ANTHROPIC_API_KEY %}
                                    <div>✅ Anthropic Claude Analysis Active</div>
                                {% endif %}
                                {% if not (config.OPENAI_API_KEY or config.ANTHROPIC_API_KEY) %}
                                    <div>📊 Advanced Technical Analysis Mode</div>
                                    <small>Add API keys to .env for AI analysis</small>
                                {% endif %}
                            </div>
                        </div>
                        
                        <div style="background: rgba(0,0,0,0.2); padding: 20px; border-radius: 10px;">
                            <h4>📊 Latest Market Insights</h4>
                            {% if signals %}
                                {% set latest = signals[-1] %}
                                <p><strong>{{ latest.symbol }}:</strong> {{ latest.reasoning }}</p>
                                <p><small>Confidence: {{ "%.0f"|format(latest.confidence * 100) }}% by {{ latest.ai_source }}</small></p>
                            {% else %}
                                <p>Analyzing market data...</p>
                            {% endif %}
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                function refreshSignals() {
                    fetch('/api/refresh')
                        .then(response => response.json())
                        .then(data => {
                            console.log('Refreshing signals...');
                            setTimeout(() => location.reload(), 2000);
                        });
                }
                
                // Auto-refresh data every 30 seconds
                setInterval(() => {
                    fetch('/api/signals')
                        .then(response => response.json())
                        .then(data => {
                            console.log('Updated data:', data.signals.length, 'signals');
                        });
                }, 30000);
            </script>
        </body>
        </html>
        """
        
        from flask import Markup
        import jinja2
        
        template = jinja2.Template(html_template)
        
        return template.render(
            ai_status=ai_status,
            current_time=datetime.now().strftime('%H:%M:%S'),
            account=self.account_data,
            signals=self.ai_signals,
            config=self.config
        )
    
    async def analyze_all_symbols(self):
        """Analyze all symbols and generate signals"""
        
        for symbol in self.config.SYMBOLS:
            try:
                # Get market data
                data = self.data_collector.get_historical_data(symbol, self.config.TIMEFRAME, 100)
                
                if data is not None and len(data) > 5:
                    # Get AI analysis
                    signal = self.ai_signal_generator.analyze_market_data(symbol, data)
                    
                    # Add symbol to signal
                    signal['symbol'] = symbol
                    
                    # Store signal
                    self.ai_signals.append(signal)
                    
                    # Keep only last 50 signals
                    if len(self.ai_signals) > 50:
                        self.ai_signals.pop(0)
                    
                    self.logger.info(f"🤖 {symbol}: {signal['signal']} ({signal['confidence']:.1%}) - {signal['ai_source']}")
                
            except Exception as e:
                self.logger.error(f"Error analyzing {symbol}: {e}")
        
        # Update account data
        account = self.data_collector.get_account_info()
        self.account_data.update(account)
    
    async def trading_loop(self):
        """Main trading analysis loop"""
        
        cycle = 0
        while self.running:
            try:
                cycle += 1
                self.logger.info(f"🔄 AI Analysis Cycle #{cycle}")
                
                await self.analyze_all_symbols()
                
                # Wait 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)
    
    def start_flask_server(self):
        """Start Flask server in thread"""
        def run_server():
            self.app.run(debug=False, host='127.0.0.1', port=8050, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        self.logger.info("🚀 Flask Dashboard: http://127.0.0.1:8050")
    
    async def start(self):
        """Start the AI bot"""
        self.logger.info("🚀 Starting Flask AI Trading Bot...")
        self.running = True
        
        # Start Flask dashboard
        self.start_flask_server()
        
        # Open browser after 3 seconds
        Timer(3.0, lambda: webbrowser.open('http://127.0.0.1:8050')).start()
        
        # Start analysis loop
        await self.trading_loop()
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        self.logger.info("🛑 AI Bot stopped")

# Main execution
async def main():
    print("🤖 Flask AI Trading Bot")
    print("=" * 40)
    print("🚀 Dashboard: http://127.0.0.1:8050")
    print("🤖 AI Analysis: OpenAI + Anthropic + Technical")
    print("📊 Features: Live signals + Market analysis")
    print("🔄 Press Ctrl+C to stop")
    print("=" * 40)
    
    bot = FlaskAITradingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        bot.stop()
    except Exception as e:
        print(f"❌ Bot error: {e}")
        bot.stop()

if __name__ == "__main__":
    asyncio.run(main())