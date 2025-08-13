import subprocess
import sys
import os
import time
import webbrowser
from threading import Timer

def open_browser():
    """Open browser after a delay"""
    time.sleep(3)
    try:
        webbrowser.open('http://127.0.0.1:8050')
        print("🌐 Browser opened automatically!")
    except:
        print("📱 Please open: http://127.0.0.1:8050 in your browser")

def start_demo():
    """Start the trading bot demo"""
    
    print("🤖 AI Trading Bot - Quick Start Demo")
    print("=" * 40)
    
    # Check if requirements are installed
    try:
        import dash
        import pandas 
        import numpy
        import sklearn
        print("✅ Required packages found")
    except ImportError as e:
        print("❌ Missing packages. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Packages installed successfully")
        except:
            print("❌ Failed to install packages automatically")
            print("📦 Please run: pip install -r requirements.txt")
            return
    
    # Start the bot
    print("🚀 Starting AI Trading Bot...")
    print("📊 Dashboard will open at: http://127.0.0.1:8050")
    print("🔄 Press Ctrl+C to stop")
    print("=" * 40)
    
    # Open browser after delay
    Timer(3.0, open_browser).start()
    
    # Start the bot
    try:
        subprocess.run([sys.executable, "run_bot.py"])
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    start_demo()
