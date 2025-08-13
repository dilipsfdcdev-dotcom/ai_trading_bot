#!/usr/bin/env python3
"""
AI Trading Bot Setup Script - Fixed for Python 3.13
Creates all necessary files and installs dependencies
"""

import os
import sys
import subprocess
from pathlib import Path

def create_ai_signal_generator():
    """Create the AI signal generator file"""
    
    ai_dir = Path("ai")
    ai_dir.mkdir(exist_ok=True)
    
    # Create __init__.py
    init_file = ai_dir / "__init__.py"
    init_file.write_text("# AI package\n", encoding='utf-8')
    
    # Create signal_generator.py (copy from the artifact above)
    signal_file = ai_dir / "signal_generator.py"
    
    if not signal_file.exists():
        print("📝 Creating AI signal generator...")
        print("⚠️  You need to copy the AISignalGenerator code from the artifact above")
        print(f"   into {signal_file}")
        
        # Create placeholder
        placeholder_content = '''# AI Signal Generator
# Copy the full AISignalGenerator class from the artifact above

import logging
from datetime import datetime

class AISignalGenerator:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.logger.info("AI Signal Generator initialized (placeholder)")
    
    def analyze_market_data(self, symbol, data):
        """Placeholder - replace with full implementation"""
        return {
            'signal': 'HOLD',
            'confidence': 0.60,
            'reasoning': 'Placeholder AI analysis',
            'ai_source': 'Placeholder',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_market_sentiment(self, symbol):
        """Placeholder sentiment analysis"""
        return "NEUTRAL"
'''
        signal_file.write_text(placeholder_content, encoding='utf-8')
        print(f"✅ Created placeholder {signal_file}")
        print("   Replace with full implementation from artifact")

def create_tradingview_dashboard():
    """Create the TradingView dashboard file"""
    
    dashboard_dir = Path("dashboard")
    dashboard_dir.mkdir(exist_ok=True)
    
    # Create __init__.py
    init_file = dashboard_dir / "__init__.py"
    init_file.write_text("# Dashboard package\n", encoding='utf-8')
    
    # Create tradingview_dashboard.py
    tv_dashboard_file = dashboard_dir / "tradingview_dashboard.py"
    
    if not tv_dashboard_file.exists():
        print("📝 Creating TradingView dashboard...")
        print("⚠️  You need to copy the TradingViewAIDashboard code from the artifact above")
        print(f"   into {tv_dashboard_file}")
        
        # Create placeholder
        placeholder_content = '''# TradingView AI Dashboard
# Copy the full TradingViewAIDashboard class from the artifact above

import dash
from dash import html
import logging

class TradingViewAIDashboard:
    def __init__(self, bot=None):
        self.bot = bot
        self.app = dash.Dash(__name__)
        self.logger = logging.getLogger(__name__)
        self.ai_signals = []
        
        # Simple placeholder layout
        self.app.layout = html.Div([
            html.H1("AI Trading Dashboard - Placeholder"),
            html.P("Replace this with the full TradingView implementation")
        ])
        
        self.logger.info("TradingView Dashboard initialized (placeholder)")
    
    def add_ai_signal(self, symbol, signal_data):
        """Placeholder - replace with full implementation"""
        self.ai_signals.append(signal_data)
        return signal_data
    
    def run_server(self, host='127.0.0.1', port=8051, debug=False):
        """Placeholder server"""
        print(f"📊 Placeholder dashboard at http://{host}:{port}")
        try:
            self.app.run_server(debug=debug, host=host, port=port, use_reloader=False)
        except Exception as e:
            print(f"Dashboard error: {e}")
'''
        tv_dashboard_file.write_text(placeholder_content, encoding='utf-8')
        print(f"✅ Created placeholder {tv_dashboard_file}")
        print("   Replace with full implementation from artifact")

def install_ai_dependencies():
    """Install AI-specific dependencies - Fixed for Python 3.13"""
    
    ai_packages = [
        "openai",
        "anthropic", 
        "dash",
        "plotly"
    ]
    
    print("📦 Installing AI dependencies...")
    
    for package in ai_packages:
        try:
            print(f"Installing {package}...")
            # Fixed subprocess call for Python 3.13
            result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True)
            
            if result.returncode == 0:
                print(f"✅ Installed {package}")
            else:
                print(f"⚠️  Could not install {package}: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️  Error installing {package}: {e}")

def update_env_file():
    """Update .env file with AI API key placeholders"""
    
    env_file = Path(".env")
    
    if env_file.exists():
        content = env_file.read_text(encoding='utf-8')
    else:
        content = ""
    
    # Add AI API key sections if not present
    if "OPENAI_API_KEY" not in content:
        content += "\n# OpenAI API Key for GPT-4 analysis\n"
        content += "# Get from: https://platform.openai.com/api-keys\n"
        content += "OPENAI_API_KEY=your_openai_api_key_here\n"
    
    if "ANTHROPIC_API_KEY" not in content:
        content += "\n# Anthropic API Key for Claude analysis\n"
        content += "# Get from: https://console.anthropic.com/\n"
        content += "ANTHROPIC_API_KEY=your_anthropic_api_key_here\n"
    
    env_file.write_text(content, encoding='utf-8')
    print("✅ Updated .env file with AI API key placeholders")

def create_ai_launcher():
    """Create AI bot launcher script"""
    
    launcher_content = '''#!/usr/bin/env python3
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
        print("\\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    launcher_file = Path("start_ai_bot.py")
    launcher_file.write_text(launcher_content, encoding='utf-8')
    print("✅ Created AI bot launcher: start_ai_bot.py")

def create_api_key_setup():
    """Create API key setup instructions"""
    
    instructions = '''# 🤖 AI API Keys Setup Guide

## 📋 Required API Keys

### 1. OpenAI API Key (for GPT-4 analysis)
1. Go to: https://platform.openai.com/api-keys
2. Sign up/login to your OpenAI account
3. Click "Create new secret key"
4. Copy the key (starts with sk-...)
5. Add to .env file: `OPENAI_API_KEY=sk-your-key-here`

### 2. Anthropic API Key (for Claude analysis)
1. Go to: https://console.anthropic.com/
2. Sign up/login to your Anthropic account
3. Go to API Keys section
4. Create new key
5. Copy the key (starts with sk-ant-...)
6. Add to .env file: `ANTHROPIC_API_KEY=sk-ant-your-key-here`

## 💰 Pricing (as of 2024)
- **OpenAI GPT-4o-mini**: ~$0.15/1M tokens (very affordable)
- **Anthropic Claude Haiku**: ~$0.25/1M tokens
- **Daily usage**: Typically $0.10-$1.00 for trading signals

## 🚀 Quick Start
1. Get at least one API key (OpenAI recommended)
2. Add to .env file
3. Run: `python start_ai_bot.py`
4. Bot will use AI for market analysis!

## 🔄 Fallback
If no API keys: Bot uses advanced technical analysis instead.
'''
    
    readme_file = Path("AI_SETUP.md")
    readme_file.write_text(instructions, encoding='utf-8')
    print("✅ Created API key setup guide: AI_SETUP.md")

def create_simple_test():
    """Create a simple test to verify installation"""
    
    test_content = '''#!/usr/bin/env python3
"""
Simple test to verify AI dependencies
"""

def test_dependencies():
    """Test if AI packages are installed"""
    
    packages = {
        'dash': 'Dash web framework',
        'plotly': 'Plotly charts',
        'openai': 'OpenAI API (optional)',
        'anthropic': 'Anthropic API (optional)'
    }
    
    print("🧪 Testing AI Dependencies")
    print("=" * 30)
    
    all_good = True
    
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"✅ {package}: {description}")
        except ImportError:
            if package in ['openai', 'anthropic']:
                print(f"⚠️  {package}: {description} (optional)")
            else:
                print(f"❌ {package}: {description} (required)")
                all_good = False
    
    print("=" * 30)
    if all_good:
        print("✅ All required dependencies installed!")
        print("🚀 Ready to run AI bot!")
    else:
        print("❌ Some dependencies missing")
        print("📦 Run: pip install dash plotly")
    
    return all_good

if __name__ == "__main__":
    test_dependencies()
'''
    
    test_file = Path("test_ai_setup.py")
    test_file.write_text(test_content, encoding='utf-8')
    print("✅ Created dependency test: test_ai_setup.py")

def main():
    """Main setup function"""
    print("🤖 AI Trading Bot Setup (Python 3.13 Compatible)")
    print("=" * 50)
    
    # Create directories and files
    create_ai_signal_generator()
    create_tradingview_dashboard()
    create_ai_launcher()
    update_env_file()
    create_api_key_setup()
    create_simple_test()
    
    # Install dependencies (fixed for Python 3.13)
    install_ai_dependencies()
    
    print("=" * 50)
    print("✅ AI Trading Bot Setup Complete!")
    print()
    print("📋 Next Steps:")
    print("1. 🧪 Test: python test_ai_setup.py")
    print("2. 📝 Copy AI code from artifacts to:")
    print("   • ai/signal_generator.py")
    print("   • dashboard/tradingview_dashboard.py")  
    print("   • ai_main.py (root directory)")
    print("3. 🔑 Add API keys to .env file (see AI_SETUP.md)")
    print("4. 🚀 Run: python start_ai_bot.py")
    print()
    print("💡 Pro tip: Get OpenAI API key first (easiest setup)")
    print("📖 Read AI_SETUP.md for detailed instructions")

if __name__ == "__main__":
    main()