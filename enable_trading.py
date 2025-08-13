# enable_trading.py - Enable/disable auto trading
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from main import AITradingBot

def main():
    print("🤖 AI Trading Bot - Auto Trading Control")
    print("=" * 50)
    
    choice = input("Enable auto trading? (y/n): ").lower().strip()
    
    if choice == 'y':
        print("⚠️  AUTO TRADING WILL BE ENABLED!")
        print("⚠️  This will execute REAL trades in your MT5 account!")
        print("⚠️  Make sure you're using a DEMO account first!")
        
        confirm = input("Are you sure? Type 'YES' to confirm: ").strip()
        
        if confirm == 'YES':
            # Create a file flag to enable auto trading
            with open('AUTO_TRADING_ENABLED.txt', 'w') as f:
                f.write('AUTO_TRADING_ENABLED\n')
                f.write(f'Enabled at: {datetime.now()}\n')
            
            print("✅ Auto trading ENABLED!")
            print("🚀 Start your bot with: python start_demo.py")
            print("💰 Trades will execute automatically on high confidence signals!")
        else:
            print("❌ Auto trading NOT enabled")
    else:
        # Remove the flag file
        if os.path.exists('AUTO_TRADING_ENABLED.txt'):
            os.remove('AUTO_TRADING_ENABLED.txt')
        print("❌ Auto trading DISABLED")

if __name__ == "__main__":
    from datetime import datetime
    main()
