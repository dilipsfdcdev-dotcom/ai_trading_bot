#!/usr/bin/env python3
"""
Quick Fix Script for AI Trading Bot - Windows Compatible
Fixes common issues and prepares the bot for running
"""

import os
import sys
import shutil
from pathlib import Path

def create_missing_directories():
    """Create missing directories"""
    directories = ['logs', 'models', 'data', 'config', 'dashboard', 'trading', 'utils']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        init_file = Path(directory) / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Package init file\n", encoding='utf-8')
    
    print("Created missing directories and __init__.py files")

def fix_dashboard_method():
    """Fix the dashboard run_server method issue"""
    dashboard_file = Path("dashboard/web_dashboard.py")
    
    if dashboard_file.exists():
        try:
            content = dashboard_file.read_text(encoding='utf-8')
            
            # Fix the run_server method call
            if "self.app.run(" in content and "run_server" not in content:
                content = content.replace(
                    "self.app.run(debug=debug, host=host, port=port, use_reloader=False)",
                    "self.app.run_server(debug=debug, host=host, port=port, use_reloader=False)"
                )
                dashboard_file.write_text(content, encoding='utf-8')
                print("Fixed dashboard run_server method")
            else:
                print("Dashboard method already correct or using new fixed version")
        except Exception as e:
            print(f"Error fixing dashboard: {e}")

def fix_imports():
    """Fix common import issues"""
    
    # Create a fallback for talib if not available
    utils_dir = Path("utils")
    utils_dir.mkdir(exist_ok=True)
    
    fallback_talib = utils_dir / "fallback_talib.py"
    if not fallback_talib.exists():
        fallback_content = '''
# Fallback for TA-Lib if not installed
import numpy as np
import pandas as pd

def RSI(prices, timeperiod=14):
    """Simple RSI calculation"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=timeperiod).mean()
    avg_loss = loss.rolling(window=timeperiod).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9):
    """Simple MACD calculation"""
    ema_fast = prices.ewm(span=fastperiod).mean()
    ema_slow = prices.ewm(span=slowperiod).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signalperiod).mean()
    histogram = macd - signal
    return macd, signal, histogram

def BBANDS(prices, timeperiod=20, nbdevup=2, nbdevdn=2):
    """Simple Bollinger Bands calculation"""
    middle = prices.rolling(window=timeperiod).mean()
    std = prices.rolling(window=timeperiod).std()
    upper = middle + (std * nbdevup)
    lower = middle - (std * nbdevdn)
    return upper, middle, lower
'''
        fallback_talib.write_text(fallback_content, encoding='utf-8')
    
    print("Created fallback TA-Lib functions")

def fix_config_paths():
    """Fix configuration file paths"""
    
    # Ensure .env file exists with safe defaults
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# MT5 Configuration (Optional for demo)
# MT5_PATH=
# MT5_LOGIN=
# MT5_PASSWORD=
# MT5_SERVER=

# API Keys (Optional for demo)
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=

# Trading Settings
DEMO_MODE=true
AUTO_TRADING=false
"""
        env_file.write_text(env_content, encoding='utf-8')
        print("Created .env file with safe defaults")

def create_simple_launcher():
    """Create a simple launcher script"""
    
    launcher_content = '''#!/usr/bin/env python3
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main import AITradingBot
except ImportError:
    print("Cannot import AITradingBot. Checking files...")
    if os.path.exists("enhanced_main.py"):
        from enhanced_main import EnhancedAITradingBot as AITradingBot
    else:
        print("No valid bot file found")
        sys.exit(1)

async def main():
    print("Starting AI Trading Bot...")
    print("Dashboard: http://127.0.0.1:8050")
    print("Press Ctrl+C to stop")
    
    bot = AITradingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\\nBot stopped by user")
        bot.stop()
    except Exception as e:
        print(f"Error: {e}")
        bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    launcher_file = Path("run_bot_simple.py")
    launcher_file.write_text(launcher_content, encoding='utf-8')
    print("Created simple launcher script")

def check_and_install_packages():
    """Check and install required packages"""
    
    try:
        import subprocess
        
        # Try to install critical packages
        critical_packages = [
            "dash>=2.14.0",
            "plotly>=5.15.0", 
            "pandas>=1.5.0",
            "numpy>=1.21.0",
            "scikit-learn>=1.0.0",
            "python-dotenv>=1.0.0"
        ]
        
        print("Installing critical packages...")
        for package in critical_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                                    capture_output=True)
                print(f"Installed {package.split('>=')[0]}")
            except subprocess.CalledProcessError:
                print(f"Could not install {package.split('>=')[0]}")
        
    except Exception as e:
        print(f"Package installation failed: {e}")

def create_simple_test():
    """Create a simple test dashboard"""
    
    test_content = '''import dash
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
'''
    
    test_file = Path("test_dashboard.py")
    test_file.write_text(test_content, encoding='utf-8')
    print("Created test dashboard")

def main():
    """Main fix function"""
    print("AI Trading Bot - Quick Fix")
    print("=" * 40)
    
    # Run all fixes
    create_missing_directories()
    fix_dashboard_method()
    fix_imports()
    fix_config_paths()
    create_simple_launcher()
    create_simple_test()
    check_and_install_packages()
    
    print("=" * 40)
    print("All fixes applied!")
    print("Test with: python test_dashboard.py")
    print("Or run: python start_demo.py")
    print("Dashboard will be at: http://127.0.0.1:8050")

if __name__ == "__main__":
    main()