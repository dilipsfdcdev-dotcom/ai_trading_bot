#!/usr/bin/env python3
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
        print("\nBot stopped by user")
        bot.stop()
    except Exception as e:
        print(f"Error: {e}")
        bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
