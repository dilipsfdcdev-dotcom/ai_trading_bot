import subprocess
import time
import webbrowser
import os

def start_bot_with_ngrok():
    print("🚀 Starting AI Trading Bot with Ngrok...")
    print("=" * 50)
    
    # Start the bot in background
    print("1. Starting trading bot...")
    bot_process = subprocess.Popen([
        "python", "start_demo.py"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for bot to start
    print("2. Waiting for bot to initialize...")
    time.sleep(5)
    
    # Start ngrok
    print("3. Starting ngrok tunnel...")
    try:
        ngrok_process = subprocess.Popen([
            "ngrok", "http", "8050"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Ngrok started!")
        print("📱 Your dashboard is now accessible worldwide!")
        print("🌐 Check ngrok terminal for public URL")
        
        # Keep running
        input("Press Enter to stop everything...")
        
    except FileNotFoundError:
        print("❌ Ngrok not found. Please:")
        print("1. Download from https://ngrok.com")
        print("2. Add to PATH or put in project folder")
    
    finally:
        # Cleanup
        bot_process.terminate()
        if 'ngrok_process' in locals():
            ngrok_process.terminate()

if __name__ == "__main__":
    start_bot_with_ngrok()