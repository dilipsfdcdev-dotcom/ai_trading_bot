#!/usr/bin/env python3
"""
AI Trading Bot Launcher
"""

import asyncio
import sys
import os
import webbrowser
from threading import Timer

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def open_browser():
    """Open browser to dashboard"""
    try:
        webbrowser.open('http://127.0.0.1:8051')
        print("🌐 AI Dashboard opened in browser!")
    except:
        print("📱 Please open: http://127.0.0.1:8051")

async def main():
    print("🤖 AI Trading Bot Launcher")
    print("=" * 40)
    
    # Check if AI files exist
    if not os.path.exists("ai/signal_generator.py"):
        print("❌ AI signal generator not found!")
        print("📝 Run: python setup_ai_bot_fixed.py first")
        return
    
    # Import and start bot
    try:
        from ai_main import AIEnhancedTradingBot
        
        print("🚀 Starting AI-Enhanced Trading Bot...")
        print("📊 AI Dashboard: http://127.0.0.1:8051")
        print("🔄 Press Ctrl+C to stop")
        
        # Open browser after 3 seconds
        Timer(3.0, open_browser).start()
        
        bot = AIEnhancedTradingBot()
        await bot.start()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("📝 Make sure all files are properly created")
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
