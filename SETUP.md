# AI Trading Bot - Complete Setup Guide

## Overview
This guide will walk you through setting up and running your AI Trading Bot from scratch. Follow each step carefully.

---

## Prerequisites

### Required Software
Install these before starting:

1. **Python 3.10 or higher**
   - Windows: Download from [python.org](https://www.python.org/downloads/)
   - Linux: `sudo apt install python3 python3-pip python3-venv`
   - Mac: `brew install python@3.10`

2. **Node.js 18 or higher**
   - Download from [nodejs.org](https://nodejs.org/)
   - Verify: `node --version` (should show v18+)

3. **MetaTrader 5**
   - Download from [metatrader5.com](https://www.metatrader5.com/)
   - Or from your broker's website
   - Create a demo account if you don't have one

### Required API Keys
You'll need these API keys (all have free tiers):

1. **OpenAI API Key** (for AI analysis)
   - Sign up at [platform.openai.com](https://platform.openai.com/signup)
   - Go to API Keys section and create a new key
   - Starts with `sk-...`

2. **News API Key** (for market news)
   - Sign up at [newsapi.org](https://newsapi.org/)
   - Free tier: 100 requests/day
   - Get your API key from the dashboard

3. **Alpha Vantage Key** (optional - for backup data)
   - Sign up at [alphavantage.co](https://www.alphavantage.co/support/#api-key)
   - Free tier available

4. **Finnhub Key** (optional - for additional news)
   - Sign up at [finnhub.io](https://finnhub.io/register)
   - Free tier available

---

## Installation Steps

### Step 1: Download the Project

If you have the project folder already, skip this step. Otherwise:

```bash
# If you cloned from GitHub:
git clone https://github.com/yourusername/ai_trading_bot.git
cd ai_trading_bot
```

### Step 2: Install Dependencies

**Windows:**
```bash
# Open Command Prompt or PowerShell in the project folder
install.bat
```

**Linux/Mac:**
```bash
# Open terminal in the project folder
chmod +x install.sh
./install.sh
```

This will:
- Install Python packages from `backend/requirements.txt`
- Install Node.js packages for the frontend
- Takes 2-3 minutes on first run

---

## Configuration

### Step 3: Configure Backend Environment (.env file)

The backend needs environment variables to work. Here's how to set them up:

#### 3.1 Create the .env file

**Windows (Command Prompt):**
```bash
cd backend
copy .env.example .env
notepad .env
```

**Windows (PowerShell):**
```bash
cd backend
Copy-Item .env.example .env
notepad .env
```

**Linux/Mac:**
```bash
cd backend
cp .env.example .env
nano .env
# Or use your preferred editor: vim, gedit, etc.
```

#### 3.2 Edit the .env file

Open the `.env` file and fill in your information. Here's what each variable means:

**MT5 Configuration:**
```env
MT5_LOGIN=12345678
# Your MT5 account number

MT5_PASSWORD=YourPassword123
# Your MT5 account password

MT5_SERVER=YourBroker-Demo
# Your broker's server name (find it in MT5: Tools → Options → Server)
# Examples: "MetaQuotes-Demo", "Exness-MT5Demo", "ICMarkets-Demo"

MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
# Windows: Usually C:\Program Files\MetaTrader 5\terminal64.exe
# Linux/Mac: Path to your MT5 terminal or use Wine
```

**AI/LLM Configuration:**
```env
OPENAI_API_KEY=sk-proj-abc123xyz...
# Your OpenAI API key (from platform.openai.com)
# IMPORTANT: Keep this secret! Never share it!

ANTHROPIC_API_KEY=sk-ant-...
# (Optional) Anthropic API key if you want to use Claude instead

LLM_PROVIDER=openai
# Which AI to use: "openai" or "anthropic"

LLM_MODEL=gpt-4-turbo-preview
# Model to use:
# - For OpenAI: "gpt-4-turbo-preview" or "gpt-4"
# - For Anthropic: "claude-3-opus-20240229" or "claude-3-sonnet-20240229"
```

**News and Data Sources:**
```env
NEWS_API_KEY=abc123def456...
# Your News API key (from newsapi.org)

ALPHA_VANTAGE_KEY=ABC123XYZ
# (Optional) Alpha Vantage key for backup market data

FINNHUB_API_KEY=abc123
# (Optional) Finnhub key for additional news
```

**Database (Optional - for production):**
```env
MONGODB_URL=mongodb://localhost:27017
# Leave as-is unless you're using MongoDB

REDIS_URL=redis://localhost:6379
# Leave as-is unless you're using Redis
```

**API Configuration:**
```env
API_HOST=0.0.0.0
# Leave as-is (allows connections from any IP)

API_PORT=8000
# Backend will run on this port

CORS_ORIGINS=http://localhost:3000,http://localhost:3001
# Allowed origins for CORS (frontend URLs)
```

**Trading Configuration:**
```env
ENVIRONMENT=demo
# IMPORTANT: Use "demo" for testing, "live" only when ready!

MAX_POSITIONS=3
# Maximum number of trades to open at once
# Start with 1 for testing, increase later

RISK_PER_TRADE=0.02
# Risk per trade as a decimal (0.02 = 2% of account per trade)
# Conservative: 0.01 (1%), Moderate: 0.02 (2%), Aggressive: 0.03 (3%)

MAX_DAILY_LOSS=0.05
# Stop trading if you lose this much in one day (0.05 = 5%)

AI_CONFIDENCE_THRESHOLD=0.65
# Only take trades with confidence above this (0.65 = 65%)
# Higher = fewer but potentially better trades
# Lower = more trades but might be riskier
```

**Monitoring:**
```env
SENTRY_DSN=
# (Optional) Sentry DSN for error tracking - leave empty for now

LOG_LEVEL=INFO
# Logging level: DEBUG, INFO, WARNING, ERROR
# Use INFO for normal operation, DEBUG for troubleshooting
```

#### 3.3 Example Complete .env File

Here's a complete example (replace with your actual values):

```env
# MT5 Configuration
MT5_LOGIN=12345678
MT5_PASSWORD=MySecretPass123
MT5_SERVER=MetaQuotes-Demo
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# AI/LLM API Keys
OPENAI_API_KEY=sk-proj-abc123xyz789...
ANTHROPIC_API_KEY=
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# News and Data Sources
NEWS_API_KEY=abc123def456ghi789
ALPHA_VANTAGE_KEY=ABC123XYZ
FINNHUB_API_KEY=

# Database
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Trading Configuration
ENVIRONMENT=demo
MAX_POSITIONS=1
RISK_PER_TRADE=0.01
MAX_DAILY_LOSS=0.05
AI_CONFIDENCE_THRESHOLD=0.70

# Monitoring
SENTRY_DSN=
LOG_LEVEL=INFO
```

### Step 4: Configure Frontend Environment (Optional)

The frontend usually works out of the box, but if you need to customize:

**Create frontend/.env.local:**

**Windows:**
```bash
cd ..\frontend
copy .env.example .env.local
notepad .env.local
```

**Linux/Mac:**
```bash
cd ../frontend
cp .env.example .env.local
nano .env.local
```

**Edit the file:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

Only change these if you're running the backend on a different port or server.

### Step 5: Configure Trading Strategy (Optional)

Edit `config/strategy_config.json` to customize trading pairs and strategy:

```json
{
  "trading_pairs": ["EURUSD", "GBPUSD", "USDJPY"],
  "primary_timeframe": "M15",
  "max_positions": 3,
  "risk_per_trade": 0.02,
  "ai_confidence_threshold": 0.65
}
```

**Explanation:**
- `trading_pairs`: Which currency pairs to trade
- `primary_timeframe`: Main timeframe for analysis (M15 = 15 minutes)
- Other settings override .env if set here

---

## Running the Bot

### Step 6: Start MetaTrader 5

1. Open MT5
2. Log in to your demo account
3. Go to **Tools → Options → Expert Advisors**
4. Check **"Allow automated trading"**
5. Check **"Allow DLL imports"**
6. Click **OK**
7. Keep MT5 running in the background

### Step 7: Start the Trading Bot

Now start both the backend and frontend:

**Windows:**
```bash
# Open Command Prompt or PowerShell in the project folder
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

The script will:
1. Start the Python backend (FastAPI server)
2. Start the React frontend (dashboard)
3. Open your browser automatically to http://localhost:3000

**You should see:**
- Backend running on `http://localhost:8000`
- Frontend running on `http://localhost:3000`
- Both windows showing logs

### Step 8: Verify Everything is Working

1. **Check Backend:**
   - Open http://localhost:8000 in your browser
   - You should see: `{"status":"running","version":"1.0.0",...}`

2. **Check Dashboard:**
   - Open http://localhost:3000
   - You should see the trading dashboard
   - Connection status should show "Connected" or "Live"

3. **Check MT5 Connection:**
   - Look at the dashboard's account info section
   - It should show your MT5 account balance
   - If you see "MT5 not initialized", check your .env file

---

## Using the Bot

### Manual Analysis

1. In the dashboard, find a trading pair (e.g., EURUSD)
2. Click **"Analyze"** button
3. Wait 10-30 seconds for AI analysis
4. Review the results:
   - Signal (Buy/Sell/Neutral)
   - Confidence percentage
   - AI reasoning
   - Suggested entry, stop-loss, take-profit

### Manual Trading

1. After analyzing a symbol, click **"Execute Trade"**
2. The bot will open a position with proper risk management
3. Watch the "Open Positions" section for live P&L

### Automated Trading

**IMPORTANT: Test manually first for at least a few hours!**

1. Make sure you're comfortable with manual trades
2. Set conservative parameters:
   - `MAX_POSITIONS=1`
   - `RISK_PER_TRADE=0.01`
   - `AI_CONFIDENCE_THRESHOLD=0.70`
3. Click **"Start Trading"** in the dashboard
4. The bot will now:
   - Scan markets every 5 minutes
   - Analyze opportunities
   - Execute trades automatically when confidence is high
5. **Monitor closely for the first day!**

### Stopping the Bot

**Stop Automated Trading:**
- Click **"Stop Trading"** in the dashboard
- This stops auto-trading but keeps the system running

**Stop Everything:**
- Close the command prompt/terminal windows
- Or press `Ctrl+C` in each window

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
cd backend
python -m pip install -r requirements.txt
```

Or run:
```bash
# Windows
.\install.bat

# Linux/Mac
./install.sh
```

### "'pip' is not recognized" error

**Problem:** When running scripts, you see: `'pip' is not recognized as an internal or external command`

**Cause:** Python's Scripts folder is not in your PATH

**Solution 1: Use the fixed scripts (Recommended)**
The install.bat and start.bat scripts have been updated to use `python -m pip` instead of `pip`, which works even without pip in PATH.

Just run:
```bash
.\install.bat
```

**Solution 2: Add Python Scripts to PATH (Optional)**

If you want `pip` to work directly:

1. Find your Python Scripts folder:
   ```bash
   python -c "import sys; print(sys.executable.replace('python.exe', 'Scripts'))"
   ```

2. Copy the path (example: `C:\Users\YourName\AppData\Local\Python\pythoncore-3.14-64\Scripts`)

3. Add to PATH:
   - Press `Win + X` → System
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "User variables", select "Path" → Edit
   - Click "New" and paste the Scripts path
   - Click OK on all windows
   - Restart PowerShell/Command Prompt

4. Test:
   ```bash
   pip --version
   ```

### "MT5 connection failed"

**Possible causes:**
1. MT5 is not running → Start MT5
2. Wrong credentials in .env → Check MT5_LOGIN, MT5_PASSWORD, MT5_SERVER
3. Algo trading not enabled → Enable in MT5 settings (see Step 6)
4. Wrong MT5_PATH → Verify the path to terminal64.exe

**How to find your MT5 server name:**
1. Open MT5
2. Click **Tools → Options**
3. Go to **Server** tab
4. Copy the server name exactly

### "OpenAI API key invalid"

**Possible causes:**
1. Wrong API key → Check your API key at platform.openai.com
2. No credits → Add payment method at platform.openai.com/account/billing
3. Extra spaces in .env → Make sure there are no spaces around the = sign

**Format:**
```env
OPENAI_API_KEY=sk-proj-abc123  # ✓ Correct
OPENAI_API_KEY = sk-proj-abc123  # ✗ Wrong (spaces)
```

### "Port 8000 already in use"

**Solution:**

**Windows:**
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with the number from above)
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

Or change the port in `backend/.env`:
```env
API_PORT=8001
```

### Dashboard shows "Disconnected"

**Solutions:**
1. Check backend is running (visit http://localhost:8000)
2. Check CORS settings in backend/.env
3. Refresh the browser
4. Clear browser cache

### No trades executing

**Check:**
1. Is automated trading started? (click "Start Trading")
2. Is confidence threshold too high? (lower it to 0.60)
3. Check risk manager status in dashboard
4. Review decision log for why trades are rejected
5. Ensure MT5 account has sufficient margin

### Python not found

**Windows:**
- Reinstall Python from python.org
- During installation, check "Add Python to PATH"

**Linux:**
```bash
sudo apt install python3 python3-pip
```

**Mac:**
```bash
brew install python@3.10
```

---

## Safety Recommendations

### For Testing (Demo Account)
- ✓ Use demo account only
- ✓ Set `ENVIRONMENT=demo`
- ✓ Start with `MAX_POSITIONS=1`
- ✓ Use `RISK_PER_TRADE=0.01` (1%)
- ✓ Monitor for several days
- ✓ Understand how it works before going live

### Before Live Trading (Real Money)
- ✓ Test in demo for at least 1 month
- ✓ Understand all settings and their effects
- ✓ Start with minimum position sizes
- ✓ Keep `MAX_DAILY_LOSS` at 5% or lower
- ✓ Monitor daily
- ✓ Only use money you can afford to lose
- ⚠️ Trading involves substantial risk of loss

### Security
- ✓ Never commit .env file to Git
- ✓ Keep API keys secret
- ✓ Use strong MT5 password
- ✓ Regularly review open positions
- ✓ Keep software updated

---

## Understanding the Dashboard

### Account Info Panel
- **Balance**: Your account balance
- **Equity**: Current value including open positions
- **Margin**: Used/available margin
- **Profit**: Current total profit/loss

### Risk Metrics
- **Drawdown**: Current drawdown percentage
- **Daily P&L**: Profit/loss today
- **Open Positions**: Number of active trades

### Market Analysis
- **Signal**: Buy/Sell/Neutral recommendation
- **Confidence**: AI confidence percentage (0-100%)
- **Reasoning**: Why the AI made this recommendation
- **Technical**: Summary of technical indicators
- **Sentiment**: News sentiment analysis

### Decision Log
Real-time log showing:
- What the bot is analyzing
- Current market conditions
- Why it made each decision
- Timestamps for all events

---

## Advanced Configuration

### Using Claude Instead of GPT-4

Edit `backend/.env`:
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus-20240229
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Adding More Trading Pairs

Edit `config/strategy_config.json`:
```json
{
  "trading_pairs": [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "NZDUSD",
    "EURJPY"
  ]
}
```

Make sure your MT5 account supports these pairs!

### Adjusting Scan Frequency

The bot scans markets every 5 minutes by default. To change this, edit `backend/main.py` line 401:
```python
await asyncio.sleep(300)  # 300 seconds = 5 minutes
```

Change 300 to:
- 60 = 1 minute (more frequent)
- 180 = 3 minutes
- 600 = 10 minutes (less frequent)

---

## File Structure

```
ai_trading_bot/
├── backend/                  # Python backend
│   ├── .env                  # Your configuration (create this!)
│   ├── .env.example          # Example configuration
│   ├── requirements.txt      # Python dependencies
│   ├── main.py               # Main FastAPI application
│   ├── mt5_connector/        # MT5 integration
│   ├── ai_engine/            # AI/LLM integration
│   ├── data_sources/         # Market data and news
│   ├── strategy/             # Trading strategies
│   └── risk_management/      # Risk management
├── frontend/                 # React dashboard
│   ├── .env.local            # Frontend config (optional)
│   └── app/                  # Next.js application
├── config/                   # Configuration files
│   ├── mt5_config.example.json
│   └── strategy_config.json
├── install.bat               # Windows install script
├── install.sh                # Linux/Mac install script
├── start.bat                 # Windows start script
├── start.sh                  # Linux/Mac start script
└── README.md                 # Overview and quick start
```

---

## Getting Help

### Check Logs

**Backend logs:**
- Look at the terminal where you ran the backend
- Errors will show up there

**Browser console:**
- Press F12 in your browser
- Check the Console tab for frontend errors

### Common Issues
1. Check all API keys are valid
2. Ensure MT5 is running and logged in
3. Verify all dependencies are installed
4. Make sure ports 3000 and 8000 are free
5. Check .env file has no syntax errors

---

## What's Next?

1. ✓ Complete setup following this guide
2. ✓ Test manual analysis on different pairs
3. ✓ Execute a few manual trades
4. ✓ Monitor for a few hours
5. ✓ Enable automated trading with conservative settings
6. ✓ Monitor daily and adjust settings
7. ✓ Keep testing in demo for at least 1 month
8. ⚠️ Only consider live trading after thorough testing

---

## Disclaimer

⚠️ **IMPORTANT WARNING:**

Trading involves substantial risk of loss. This software is provided for educational and research purposes only.

- Past performance does not guarantee future results
- Always test in demo accounts first
- Never risk more than you can afford to lose
- Trading decisions are your responsibility
- Consult a financial advisor before live trading
- The developers are not responsible for any financial losses

---

## License

MIT License - See LICENSE file for details

---

**Happy Testing! Start with demo, stay safe, and learn from the bot's analysis.** 🚀
