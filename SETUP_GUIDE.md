# AI Trading Bot - Complete Setup Guide

## 🚀 Quick Start Guide

This guide will walk you through setting up your AI trading bot from scratch.

## Prerequisites

### Required Software
1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **MetaTrader 5** - [Download](https://www.metatrader5.com/)
4. **Git** - [Download](https://git-scm.com/)

### Required API Keys
1. **OpenAI API Key** - [Get it here](https://platform.openai.com/api-keys)
2. **News API Key** - [Get it here](https://newsapi.org/)
3. **Alpha Vantage Key** (optional) - [Get it here](https://www.alphavantage.co/)
4. **Finnhub Key** (optional) - [Get it here](https://finnhub.io/)

### MT5 Account
- Demo or Live MT5 trading account
- Account number, password, and server name

---

## Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/ai_trading_bot.git
cd ai_trading_bot
```

---

## Step 2: Backend Setup

### 2.1 Create Virtual Environment

```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 2.2 Install Dependencies

```bash
pip install -r requirements.txt
```

### 2.3 Configure Environment Variables

Copy the example env file and edit it:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# MT5 Configuration
MT5_LOGIN=12345678
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Demo
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# AI/LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# News and Data Sources
NEWS_API_KEY=your_news_api_key
ALPHA_VANTAGE_KEY=your_alpha_vantage_key
FINNHUB_API_KEY=your_finnhub_key

# Database (optional - for production)
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Trading Configuration
ENVIRONMENT=demo
MAX_POSITIONS=3
RISK_PER_TRADE=0.02
MAX_DAILY_LOSS=0.05
AI_CONFIDENCE_THRESHOLD=0.65

# Monitoring
LOG_LEVEL=INFO
```

### 2.4 Configure Trading Strategy

Edit `config/strategy_config.json`:

```json
{
  "trading_pairs": ["EURUSD", "GBPUSD", "USDJPY"],
  "primary_timeframe": "M15",
  "max_positions": 3,
  "risk_per_trade": 0.02,
  "ai_confidence_threshold": 0.65
}
```

---

## Step 3: Frontend Setup

### 3.1 Install Dependencies

```bash
cd ../frontend
npm install
```

### 3.2 Configure Environment

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

---

## Step 4: MetaTrader 5 Setup

### 4.1 Install MT5

1. Download and install MetaTrader 5 from your broker
2. Login to your demo or live account

### 4.2 Enable Algo Trading

1. Open MT5
2. Go to **Tools → Options → Expert Advisors**
3. Check **"Allow automated trading"**
4. Check **"Allow DLL imports"**
5. Click **OK**

### 4.3 Verify Connection

The bot will automatically connect when you start it.

---

## Step 5: Start the System

### Option A: Development Mode (Recommended for testing)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access the dashboard:** http://localhost:3000

### Option B: Production Mode with Docker

```bash
docker-compose up -d
```

---

## Step 6: First Run Verification

### 6.1 Check Backend Health

Open your browser: http://localhost:8000

You should see:
```json
{
  "status": "running",
  "version": "1.0.0",
  "timestamp": "2024-..."
}
```

### 6.2 Check Dashboard

Open: http://localhost:3000

You should see:
- ✅ Account information
- ✅ Connection status (Live)
- ✅ Trading controls

### 6.3 Test Analysis

1. Click on any trading pair in the dashboard
2. Click **"Analyze"**
3. Wait for AI analysis (10-30 seconds)
4. Review the analysis results

---

## Step 7: Start Trading

### 7.1 Demo Trading (Recommended First)

1. Ensure you're using a **DEMO account**
2. Set `ENVIRONMENT=demo` in `.env`
3. Start with small position sizes
4. Set `MAX_POSITIONS=1` initially

### 7.2 Enable Automated Trading

In the dashboard:
1. Review risk settings
2. Click **"Start Trading"** button
3. Monitor the decision log
4. Watch for first trade execution

### 7.3 Monitor Performance

The bot will:
- Scan markets every 5 minutes (configurable)
- Analyze technical indicators, news, and AI reasoning
- Execute trades when confidence > threshold
- Respect risk management rules
- Update dashboard in real-time

---

## Configuration Options

### Risk Management

Edit `.env` to adjust risk:

```env
MAX_POSITIONS=3          # Max concurrent trades
RISK_PER_TRADE=0.02     # 2% risk per trade
MAX_DAILY_LOSS=0.05     # Stop if 5% daily loss
AI_CONFIDENCE_THRESHOLD=0.65  # Min confidence to trade
```

### Trading Pairs

Edit `config/strategy_config.json`:

```json
{
  "trading_pairs": [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD"
  ]
}
```

### AI Model

Change LLM provider in `.env`:

```env
# Use OpenAI GPT-4
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# Or use Anthropic Claude
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus-20240229
```

---

## Monitoring & Logs

### View Logs

```bash
# Backend logs
cd backend
tail -f logs/trading_bot.log

# Or check terminal output
```

### Dashboard Features

1. **Account Info** - Balance, equity, profit
2. **Risk Metrics** - Drawdown, daily P&L, position usage
3. **Open Positions** - Live trades with P&L
4. **Market Analysis** - AI analysis for each pair
5. **Decision Log** - Real-time decision reasoning
6. **Trading Controls** - Start/stop trading

---

## Troubleshooting

### MT5 Connection Failed

**Problem:** "MT5 connection failed"

**Solutions:**
1. Check MT5 is running
2. Verify credentials in `.env`
3. Enable algo trading in MT5 settings
4. Check firewall isn't blocking MT5

### API Key Errors

**Problem:** "OpenAI API key invalid"

**Solutions:**
1. Verify API key in `.env`
2. Check API key has credits
3. Try with different LLM provider

### No Trades Executing

**Problem:** Bot analyzes but doesn't trade

**Solutions:**
1. Lower `AI_CONFIDENCE_THRESHOLD` (try 0.6)
2. Check risk manager isn't blocking (review dashboard)
3. Verify MT5 account has enough margin
4. Check trading hours (bot avoids weekends)

### WebSocket Disconnected

**Problem:** Dashboard shows "Disconnected"

**Solutions:**
1. Check backend is running
2. Verify ports 8000 and 3000 are available
3. Check CORS settings in `.env`
4. Refresh the browser

---

## Safety Recommendations

### For Demo Trading
- ✅ Start with demo account
- ✅ Test for at least 1 week
- ✅ Monitor all decisions
- ✅ Understand AI reasoning

### Before Live Trading
- ✅ Successful demo trading for 1+ month
- ✅ Understand all risk parameters
- ✅ Start with minimum position sizes
- ✅ Set strict `MAX_DAILY_LOSS`
- ✅ Monitor daily
- ✅ Have emergency stop plan

### Risk Management
- ❌ Never risk more than 2% per trade
- ❌ Never exceed 5% total exposure
- ❌ Don't ignore drawdown warnings
- ❌ Don't modify SL/TP manually
- ✅ Review performance weekly
- ✅ Keep emergency fund separate

---

## Advanced Configuration

### Custom Indicators

Add custom indicators in `backend/strategy/indicators.py`

### Trading Strategy

Modify strategy logic in `backend/strategy/strategy_engine.py`

### AI Prompts

Customize AI prompts in `backend/ai_engine/analyzer.py`

---

## Support & Updates

### Getting Help
- Check logs for errors
- Review decision log in dashboard
- Read code comments
- Consult MT5 documentation

### Keeping Updated
```bash
git pull origin main
pip install -r requirements.txt --upgrade
npm install
```

---

## Performance Optimization

### For Better Results
1. Use higher confidence threshold (0.70-0.75)
2. Monitor during high-volatility sessions
3. Avoid trading during major news
4. Focus on major pairs (EUR, GBP, JPY)
5. Review and adjust based on performance

### System Resources
- Minimum: 4GB RAM, 2 CPU cores
- Recommended: 8GB RAM, 4 CPU cores
- Network: Stable internet (critical!)

---

## Legal Disclaimer

⚠️ **Important:** Trading involves substantial risk. This bot is for educational purposes. Past performance does not guarantee future results. Always:
- Test thoroughly in demo
- Understand all risks
- Never invest more than you can afford to lose
- Consult a financial advisor
- Follow local regulations

---

## Next Steps

1. ✅ Complete setup
2. ✅ Run in demo mode
3. ✅ Monitor for 1 week
4. ✅ Analyze results
5. ✅ Adjust parameters
6. ✅ Continue testing
7. ⚠️ Consider live trading (at your own risk)

**Good luck with your automated trading journey!** 🚀
