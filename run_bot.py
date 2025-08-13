import asyncio
import sys
import os
from datetime import datetime
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import AITradingBot

def setup_logging():
    """Setup logging"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

async def main():
    """Main function"""
    setup_logging()
    
    print("=" * 60)
    print(" AI TRADING BOT - LOCAL DEMO MODE")
    print("=" * 60)
    print(" Dashboard: http://127.0.0.1:8050")
    print(" Logs: Check logs/ folder")
    print(" Processing signals every 30 seconds")
    print("=" * 60)
    
    bot = AITradingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n Bot stopped by user (Ctrl+C)")
        bot.stop()
    except Exception as e:
        print(f" Bot error: {e}")
        bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
