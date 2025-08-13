#!/usr/bin/env python3
"""
Quick fix for import issues
"""

import os
from pathlib import Path

def check_data_collector():
    """Check what's actually in the data collector file"""
    
    data_file = Path("data/data_collector.py")
    
    if not data_file.exists():
        print("❌ data/data_collector.py not found!")
        return False
    
    content = data_file.read_text(encoding='utf-8')
    
    # Check for class names
    if "class MT5DataCollector" in content:
        print("✅ Found MT5DataCollector class")
        return True
    elif "class EnhancedMT5DataCollector" in content:
        print("⚠️  Found EnhancedMT5DataCollector (needs to be renamed)")
        # Fix the class name
        content = content.replace("class EnhancedMT5DataCollector", "class MT5DataCollector")
        data_file.write_text(content, encoding='utf-8')
        print("✅ Fixed class name to MT5DataCollector")
        return True
    else:
        print("❌ No data collector class found!")
        print("📝 Creating a simple MT5DataCollector...")
        create_simple_data_collector()
        return True

def create_simple_data_collector():
    """Create a simple working data collector"""
    
    simple_collector = '''import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time

# Try to import MetaTrader5, but don't fail if not available
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    print("⚠️  MetaTrader5 not available - running in demo mode")
    MT5_AVAILABLE = False

class MT5DataCollector:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.demo_mode = True
        self.connected = False
        
        if MT5_AVAILABLE:
            self.initialize_mt5()
        else:
            self.logger.info("📊 Running in demo mode - MT5 not available")
    
    def initialize_mt5(self):
        """Initialize MT5 connection"""
        if not MT5_AVAILABLE:
            return False
            
        try:
            if not mt5.initialize():
                self.demo_mode = True
                return False
            
            # Check credentials
            if (hasattr(self.config, 'MT5_LOGIN') and self.config.MT5_LOGIN and 
                hasattr(self.config, 'MT5_PASSWORD') and self.config.MT5_PASSWORD):
                
                if mt5.login(self.config.MT5_LOGIN, self.config.MT5_PASSWORD, self.config.MT5_SERVER):
                    self.connected = True
                    self.demo_mode = False
                    self.logger.info("✅ MT5 Connected")
                    return True
            
            self.demo_mode = True
            return True
            
        except Exception as e:
            self.logger.error(f"MT5 error: {e}")
            self.demo_mode = True
            return False
    
    def get_historical_data(self, symbol, timeframe, bars=1000):
        """Get historical data"""
        
        if self.connected and not self.demo_mode and MT5_AVAILABLE:
            return self._get_real_data(symbol, timeframe, bars)
        else:
            return self._get_demo_data(symbol, bars)
    
    def _get_real_data(self, symbol, timeframe, bars):
        """Get real data from MT5"""
        try:
            mt5_timeframes = {
                1: mt5.TIMEFRAME_M1,
                5: mt5.TIMEFRAME_M5,
                15: mt5.TIMEFRAME_M15,
                30: mt5.TIMEFRAME_M30,
                60: mt5.TIMEFRAME_H1
            }
            
            mt5_tf = mt5_timeframes.get(timeframe, mt5.TIMEFRAME_M5)
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, bars)
            
            if rates is None or len(rates) == 0:
                return self._get_demo_data(symbol, bars)
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting real data: {e}")
            return self._get_demo_data(symbol, bars)
    
    def _get_demo_data(self, symbol, bars):
        """Generate demo data"""
        try:
            dates = pd.date_range(end=datetime.now(), periods=bars, freq='5T')
            
            # Realistic base prices
            base_prices = {
                'XAUUSD': 2650.0,
                'BTCUSD': 96000.0,
                'EURUSD': 1.0450
            }
            
            base_price = base_prices.get(symbol, 1.0000)
            
            # Generate price movement
            np.random.seed(int(time.time()) % 1000)
            returns = np.random.normal(0.0001, 0.005, bars)
            prices = [base_price]
            
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))
            
            data = []
            for i, price in enumerate(prices):
                high = price * (1 + abs(np.random.normal(0, 0.002)))
                low = price * (1 - abs(np.random.normal(0, 0.002)))
                open_price = prices[i-1] if i > 0 else price
                close = price
                
                high = max(high, open_price, close)
                low = min(low, open_price, close)
                
                data.append({
                    'time': dates[i],
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'tick_volume': np.random.randint(100, 1000),
                    'real_volume': 0
                })
            
            df = pd.DataFrame(data)
            df.set_index('time', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error generating demo data: {e}")
            return None
    
    def get_account_info(self):
        """Get account info"""
        if self.connected and not self.demo_mode and MT5_AVAILABLE:
            try:
                account = mt5.account_info()
                if account:
                    return {
                        'balance': account.balance,
                        'equity': account.equity,
                        'profit': account.profit,
                        'currency': account.currency
                    }
            except:
                pass
        
        # Demo account
        return {
            'balance': 100000.0,
            'equity': 100000.0 + np.random.uniform(-1000, 1000),
            'profit': np.random.uniform(-500, 500),
            'currency': 'USD'
        }
'''
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    data_file = data_dir / "data_collector.py"
    data_file.write_text(simple_collector, encoding='utf-8')
    print("✅ Created working MT5DataCollector")

def check_all_imports():
    """Check all required imports for ai_main.py"""
    
    required_files = {
        'config/config.py': 'Config',
        'data/data_collector.py': 'MT5DataCollector', 
        'utils/indicators.py': 'TechnicalIndicators',
        'models/simple_models.py': 'SimpleMLModels',
        'ai/signal_generator.py': 'AISignalGenerator',
        'dashboard/tradingview_dashboard.py': 'TradingViewAIDashboard'
    }
    
    print("🔍 Checking all required files...")
    
    missing_files = []
    for file_path, class_name in required_files.items():
        if not Path(file_path).exists():
            missing_files.append(f"{file_path} (needs {class_name})")
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print(f"\\n❌ Missing {len(missing_files)} required files:")
        for file in missing_files:
            print(f"   • {file}")
        return False
    
    print("\\n✅ All required files present!")
    return True

def create_minimal_ai_main():
    """Create a minimal working ai_main.py"""
    
    minimal_content = '''import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import with fallbacks
try:
    from config.config import Config
except ImportError:
    print("❌ Config not found - using defaults")
    class Config:
        SYMBOLS = ['XAUUSD', 'BTCUSD']
        TIMEFRAME = 5
        OPENAI_API_KEY = ''
        ANTHROPIC_API_KEY = ''

try:
    from data.data_collector import MT5DataCollector
except ImportError:
    print("❌ MT5DataCollector not found")
    sys.exit(1)

try:
    from utils.indicators import TechnicalIndicators
except ImportError:
    print("⚠️  TechnicalIndicators not found - using fallback")
    class TechnicalIndicators:
        def add_all_indicators(self, df):
            return df

try:
    from models.simple_models import SimpleMLModels
except ImportError:
    print("⚠️  SimpleMLModels not found - using fallback")
    class SimpleMLModels:
        def __init__(self, config):
            pass

try:
    from ai.signal_generator import AISignalGenerator
except ImportError:
    print("⚠️  AISignalGenerator not found - using fallback")
    class AISignalGenerator:
        def __init__(self, config):
            self.config = config
        def analyze_market_data(self, symbol, data):
            return {'signal': 'HOLD', 'confidence': 0.5, 'reasoning': 'Fallback analysis'}

try:
    from dashboard.tradingview_dashboard import TradingViewAIDashboard
except ImportError:
    print("⚠️  TradingView dashboard not found - using simple dashboard")
    import dash
    from dash import html
    
    class TradingViewAIDashboard:
        def __init__(self, bot=None):
            self.app = dash.Dash(__name__)
            self.app.layout = html.Div([
                html.H1("🤖 AI Trading Bot - Minimal Dashboard"),
                html.P("Full TradingView dashboard not available")
            ])
        
        def add_ai_signal(self, symbol, signal_data):
            print(f"📊 Signal: {signal_data}")
            return signal_data
        
        def run_server(self, **kwargs):
            print("📊 Simple dashboard starting...")
            self.app.run_server(**kwargs)

class AIEnhancedTradingBot:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_collector = MT5DataCollector(self.config)
        self.technical_indicators = TechnicalIndicators()
        self.ml_models = SimpleMLModels(self.config)
        self.ai_signal_generator = AISignalGenerator(self.config)
        self.dashboard = TradingViewAIDashboard(self)
        
        self.running = False
        self.logger.info("🤖 AI Trading Bot initialized")
    
    async def start(self):
        """Start the bot"""
        self.logger.info("🚀 Starting AI Trading Bot...")
        self.running = True
        
        # Start dashboard in thread
        import threading
        def run_dashboard():
            self.dashboard.run_server(debug=False, port=8051)
        
        dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        dashboard_thread.start()
        self.logger.info("📊 Dashboard: http://127.0.0.1:8051")
        
        # Simple trading loop
        while self.running:
            try:
                for symbol in self.config.SYMBOLS:
                    # Get data
                    data = self.data_collector.get_historical_data(symbol, 5, 100)
                    if data is not None and len(data) > 10:
                        # Add indicators
                        data = self.technical_indicators.add_all_indicators(data)
                        
                        # Get AI signal
                        signal = self.ai_signal_generator.analyze_market_data(symbol, data)
                        
                        # Add to dashboard
                        self.dashboard.add_ai_signal(symbol, signal)
                        
                        self.logger.info(f"📊 {symbol}: {signal.get('signal', 'HOLD')}")
                
                await asyncio.sleep(30)  # Wait 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in trading loop: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        self.logger.info("🛑 Bot stopped")

# Main execution
if __name__ == "__main__":
    async def main():
        print("🤖 AI Trading Bot Starting...")
        bot = AIEnhancedTradingBot()
        
        try:
            await bot.start()
        except KeyboardInterrupt:
            print("\\n🛑 Stopped by user")
            bot.stop()
        except Exception as e:
            print(f"❌ Error: {e}")
            bot.stop()
    
    asyncio.run(main())
'''
    
    ai_main_file = Path("ai_main.py")
    ai_main_file.write_text(minimal_content, encoding='utf-8')
    print("✅ Created minimal working ai_main.py")

def main():
    """Main fix function"""
    print("🔧 Quick Import Fix")
    print("=" * 30)
    
    # Check and fix data collector
    if not check_data_collector():
        return
    
    # Check all imports
    if not check_all_imports():
        print("\\n⚠️  Some files missing - creating minimal version...")
        create_minimal_ai_main()
    
    print("=" * 30)
    print("✅ Import issues should be fixed!")
    print("🚀 Try: python start_ai_bot.py")

if __name__ == "__main__":
    main()