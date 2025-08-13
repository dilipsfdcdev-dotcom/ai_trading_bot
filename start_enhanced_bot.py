import asyncio
import sys
import os
from datetime import datetime
import logging
import subprocess
import webbrowser
from threading import Timer

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_main import EnhancedAITradingBot

def setup_logging():
    """Setup logging"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/enhanced_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def check_dependencies():
    """Check if all required packages are installed"""
    required_packages = [
        'pandas', 'numpy', 'scikit-learn', 'dash', 'plotly', 
        'MetaTrader5', 'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            elif package == 'scikit-learn':
                import sklearn
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("\n📦 Installing missing packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("✅ Packages installed successfully")
        except Exception as e:
            print(f"❌ Failed to install packages: {e}")
            print("💡 Please run manually: pip install -r requirements.txt")
            return False
    
    return True

def open_browser():
    """Open browser after a delay"""
    try:
        webbrowser.open('http://127.0.0.1:8050')
        print("🌐 Dashboard opened in browser!")
    except:
        print("📱 Please open: http://127.0.0.1:8050 in your browser")

def show_banner():
    """Show startup banner"""
    print("=" * 70)
    print("🤖 ENHANCED AI TRADING BOT v2.0")
    print("=" * 70)
    print("✨ Features:")
    print("  📊 Live MT5 Data Integration")
    print("  🧠 Advanced ML Models")
    print("  💰 Intelligent Position Sizing")
    print("  🛡️  Dynamic Risk Management")
    print("  📈 Real-time Dashboard")
    print("  🎯 Automated Trading")
    print("=" * 70)

def check_mt5_connection():
    """Check MT5 connection status"""
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            print("✅ MT5 Available")
            mt5.shutdown()
            return True
        else:
            print("⚠️  MT5 Available but not connected")
            return False
    except:
        print("❌ MT5 Not Available - Will use demo data")
        return False

def check_auto_trading():
    """Check if auto trading is enabled"""
    if os.path.exists('AUTO_TRADING_ENABLED.txt'):
        print("⚡ AUTO TRADING: ENABLED")
        print("💰 Bot will execute real trades!")
        return True
    else:
        print("📊 AUTO TRADING: DISABLED")
        print("🔍 Dashboard mode only - no real trades")
        return False

async def main():
    """Main function"""
    show_banner()
    setup_logging()
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Check MT5
    mt5_available = check_mt5_connection()
    
    # Check auto trading
    auto_trading = check_auto_trading()
    
    print("\n🚀 Starting Enhanced AI Trading Bot...")
    print("📊 Dashboard: http://127.0.0.1:8050")
    
    # Open browser after 3 seconds
    Timer(3.0, open_browser).start()
    
    bot = EnhancedAITradingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user (Ctrl+C)")
        bot.stop()
    except Exception as e:
        print(f"❌ Bot error: {e}")
        logging.exception("Bot error details:")
        bot.stop()

def enable_auto_trading():
    """Enable auto trading"""
    print("🤖 Auto Trading Control")
    print("=" * 30)
    
    choice = input("Enable auto trading? (y/n): ").lower().strip()
    
    if choice == 'y':
        print("⚠️  WARNING: AUTO TRADING WILL BE ENABLED!")
        print("⚠️  This will execute REAL trades in your MT5 account!")
        print("⚠️  Make sure you're using a DEMO account first!")
        print("⚠️  Ensure you have proper risk management settings!")
        
        confirm = input("\nType 'YES' to confirm: ").strip()
        
        if confirm == 'YES':
            with open('AUTO_TRADING_ENABLED.txt', 'w') as f:
                f.write(f'AUTO_TRADING_ENABLED\nEnabled at: {datetime.now()}\n')
            
            print("✅ Auto trading ENABLED!")
            print("🚀 Start bot with: python start_enhanced_bot.py")
        else:
            print("❌ Auto trading NOT enabled")
    else:
        if os.path.exists('AUTO_TRADING_ENABLED.txt'):
            os.remove('AUTO_TRADING_ENABLED.txt')
        print("❌ Auto trading DISABLED")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--enable-trading":
        enable_auto_trading()
    else:
        asyncio.run(main())