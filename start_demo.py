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

def install_requirements():
    """Install required packages"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to install packages: {e}")
        # Try installing individual packages that are most critical
        critical_packages = ["dash", "plotly", "pandas", "numpy", "scikit-learn", "python-dotenv"]
        for package in critical_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ Installed {package}")
            except:
                print(f"❌ Failed to install {package}")
        return False

def check_dependencies():
    """Check if required packages are available"""
    required_packages = {
        'dash': 'dash',
        'plotly': 'plotly', 
        'pandas': 'pandas',
        'numpy': 'numpy',
        'sklearn': 'scikit-learn',
        'dotenv': 'python-dotenv'
    }
    
    missing = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    return missing

def start_demo():
    """Start the trading bot demo"""
    
    print("🤖 AI Trading Bot - Quick Start Demo")
    print("=" * 40)
    
    # Check dependencies
    missing_packages = check_dependencies()
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Installing missing packages...")
        install_requirements()
        
        # Check again
        missing_packages = check_dependencies()
        if missing_packages:
            print(f"❌ Still missing: {', '.join(missing_packages)}")
            print("💡 Please install manually: pip install " + " ".join(missing_packages))
            return
        
    print("✅ Required packages found")
    
    # Start the bot
    print("🚀 Starting AI Trading Bot...")
    print("📊 Dashboard will open at: http://127.0.0.1:8050")
    print("🔄 Press Ctrl+C to stop")
    print("=" * 40)
    
    # Open browser after delay
    Timer(3.0, open_browser).start()
    
    # Start the bot
    try:
        # Try enhanced version first, fallback to main
        if os.path.exists("enhanced_main.py"):
            subprocess.run([sys.executable, "enhanced_main.py"])
        elif os.path.exists("main.py"):
            subprocess.run([sys.executable, "main.py"])
        else:
            print("❌ Bot files not found")
    except KeyboardInterrupt:
        print("\n🛑 Demo stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    start_demo()