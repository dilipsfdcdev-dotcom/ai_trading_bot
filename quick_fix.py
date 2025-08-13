#!/usr/bin/env python3
"""
Quick Fix Script for AI Trading Bot
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
            init_file.write_text("# Package init file\n")
    
    print("✅ Created missing directories and __init__.py files")

def fix_dashboard_method():
    """Fix the dashboard run_server method issue"""
    dashboard_file = Path("dashboard/web_dashboard.py")
    
    if dashboard_file.exists():
        content = dashboard_file.read_text()
        
        # Fix the run_server method call
        if "self.app.run(" in content and "run_server" not in content:
            content = content.replace(
                "self.app.run(debug=debug, host=host, port=port, use_reloader=False)",
                "self.app.run_server(debug=debug, host=host, port=port, use_reloader=False)"
            )
            dashboard_file.write_text(content)
            print("✅ Fixed dashboard run_server method")
        else:
            print("ℹ️  Dashboard method already correct or using new fixed version")

def fix_imports():
    """Fix common import issues"""
    
    # Create a fallback for talib if not available
    utils_dir = Path("utils")
    utils_dir.mkdir(exist_ok=True)
    
    fallback_talib = utils_dir / "fallback_talib.py"
    if not fallback_talib.exists():
        fallback_talib.write_text("""
# Fallback for TA-Lib if not installed
import numpy as np
import pandas as pd

def RSI(prices, timeperiod=14):
    \"\"\"Simple RSI calculation\"\"\"
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=timeperiod).mean()
    avg_loss = loss.rolling(window=timeperiod).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9):
    \"\"\"Simple MACD calculation\"\"\"
    ema_fast = prices.ewm(span=fastperiod).mean()
    ema_slow = prices.ewm(span=slowperiod).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signalperiod).mean()
    histogram = macd - signal
    return macd, signal, histogram

def BBANDS(prices, timeperiod=20, nbdevup=2, nbdevdn=2):
    \"\"\"Simple Bollinger Bands calculation\"\"\"
    middle = prices.rolling(window=timeperiod).mean()
    std = prices.rolling(window=timeperiod).std()
    upper = middle + (std * nbdevup)
    lower = middle - (std * nbdevdn)
    return upper, middle, lower
""")
    
    print("✅ Created fallback TA-Lib functions")

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
"""
        env_file.write_text(env_content)
        print("✅ Created .env file with safe defaults")

def create_simple_launcher():
    """Create a simple launcher script"""
    
    launcher_content = """#!/usr/bin/env python3
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main import AITradingBot
except ImportError:
    print("❌ Cannot import AITradingBot. Checking files...")
    if os.path.exists("enhanced_main.py"):
        from enhanced_main import EnhancedAITradingBot as AITradingBot
    else:
        print("❌ No valid bot file found")
        sys.exit(1)

async def main():
    print("🤖 Starting AI Trading Bot...")
    print("📊 Dashboard: http://127.0.0.1:8050")
    print("🔄 Press Ctrl+C to stop")
    
    bot = AITradingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\\n🛑 Bot stopped by user")
        bot.stop()
    except Exception as e:
        print(f"❌ Error: {e}")
        bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
"""
    
    launcher_file = Path("run_bot_simple.py")
    launcher_file.write_text(launcher_content)
    print("✅ Created simple launcher script")

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
        
        print("📦 Installing critical packages...")
        for package in critical_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                                    capture_output=True)
                print(f"✅ Installed {package.split('>=')[0]}")
            except subprocess.CalledProcessError:
                print(f"⚠️  Could not install {package.split('>=')[0]}")
        
    except Exception as e:
        print(f"⚠️  Package installation failed: {e}")

def main():
    """Main fix function"""
    print("🔧 AI Trading Bot - Quick Fix")
    print("=" * 40)
    
    # Run all fixes
    create_missing_directories()
    fix_dashboard_method()
    fix_imports()
    fix_config_paths()
    create_simple_launcher()
    check_and_install_packages()
    
    print("=" * 40)
    print("✅ All fixes applied!")
    print("🚀 Try running: python start_demo.py")
    print("🚀 Or: python run_bot_simple.py")

if __name__ == "__main__":
    main()