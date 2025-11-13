# AI Trading Bot

Professional automated trading system with MT5 integration, AI-powered analysis, and real-time dashboard.

## Features

- **Fully Automated Trading**: 24/7 automated trading with MT5
- **AI-Powered Analysis**: Uses GPT-4 or Claude for intelligent market analysis
- **Multi-Source Data**: Technical indicators, news sentiment, and market trends
- **Smart Risk Management**: Automatic position sizing, stop-loss, and daily limits
- **Real-time Dashboard**: Live monitoring with full decision transparency
- **Educational**: See exactly what the bot analyzes and why it makes each decision

## Quick Start

### Prerequisites

1. **Python 3.10+** - [Download](https://www.python.org/downloads/)
2. **Node.js 18+** - [Download](https://nodejs.org/)
3. **MetaTrader 5** - [Download](https://www.metatrader5.com/)

### Installation (3 Steps)

**Step 1: Install dependencies**

Windows:
```bash
install.bat
```

Linux/Mac:
```bash
chmod +x install.sh
./install.sh
```

**Step 2: Configure environment**

Create your `.env` file:
```bash
cd backend
copy .env.example .env    # Windows
# or
cp .env.example .env      # Linux/Mac
```

Edit `backend/.env` with your credentials:
- MT5 login, password, and server
- OpenAI API key (get from [platform.openai.com](https://platform.openai.com/))
- News API key (get from [newsapi.org](https://newsapi.org/))

**See [SETUP.md](SETUP.md) for detailed .env configuration guide!**

**Step 3: Start the bot**

Windows:
```bash
start.bat
```

Linux/Mac:
```bash
./start.sh
```

Access the dashboard at: **http://localhost:3000**

## Need Help?

**For detailed setup instructions, troubleshooting, and .env configuration:**

📖 **Read the [Complete Setup Guide (SETUP.md)](SETUP.md)**

The setup guide includes:
- Step-by-step installation
- Detailed .env file explanation (every variable explained!)
- How to get API keys
- MT5 configuration
- Troubleshooting common issues
- Safety recommendations

## Configuration Files

### backend/.env
Main configuration file (you must create this!):
- MT5 credentials
- API keys (OpenAI, News API, etc.)
- Risk management settings
- Trading parameters

**Example:**
```env
MT5_LOGIN=12345678
MT5_PASSWORD=yourpassword
MT5_SERVER=YourBroker-Demo
OPENAI_API_KEY=sk-proj-...
NEWS_API_KEY=...
ENVIRONMENT=demo
MAX_POSITIONS=1
RISK_PER_TRADE=0.01
```

**See [SETUP.md](SETUP.md) for complete .env guide with all variables explained!**

### config/strategy_config.json
Trading strategy configuration:
```json
{
  "trading_pairs": ["EURUSD", "GBPUSD", "USDJPY"],
  "primary_timeframe": "M15",
  "max_positions": 3,
  "risk_per_trade": 0.02,
  "ai_confidence_threshold": 0.65
}
```

## How It Works

1. **Data Collection**: Fetches real-time data from MT5, news sources, and market data APIs
2. **Technical Analysis**: Calculates RSI, MACD, Bollinger Bands, and other indicators
3. **AI Analysis**: LLM analyzes market context and generates recommendations
4. **Risk Management**: Calculates position size and validates trade against risk rules
5. **Execution**: Opens positions via MT5 with automatic stop-loss and take-profit
6. **Monitoring**: Real-time dashboard shows all decisions and positions

## Dashboard Features

- **Account Info**: Balance, equity, margin, profit/loss
- **Open Positions**: Live trades with current P&L
- **Market Analysis**: AI analysis for each trading pair with confidence scores
- **Decision Log**: Real-time log showing bot's reasoning
- **Risk Metrics**: Drawdown, daily P&L, position usage
- **Trading Controls**: Start/stop automated trading

## Project Structure

```
ai_trading_bot/
├── backend/                   # Python FastAPI backend
│   ├── .env                   # YOUR CONFIG (create this!)
│   ├── .env.example           # Example config
│   ├── requirements.txt       # Python dependencies
│   ├── main.py                # Main application
│   ├── mt5_connector/         # MT5 integration
│   ├── ai_engine/             # AI/LLM analysis
│   ├── data_sources/          # Market data & news
│   ├── strategy/              # Trading strategies
│   └── risk_management/       # Risk management
├── frontend/                  # React/Next.js dashboard
│   └── app/                   # Dashboard UI
├── config/                    # Configuration files
│   └── strategy_config.json   # Trading strategy config
├── install.bat / install.sh   # Installation scripts
├── start.bat / start.sh       # Startup scripts
├── README.md                  # This file
└── SETUP.md                   # Complete setup guide
```

## Common Issues

### "ModuleNotFoundError: No module named 'fastapi'"
**Solution**: Run the install script
```bash
# Windows
install.bat

# Linux/Mac
./install.sh
```

### "MT5 connection failed"
**Solution**:
1. Make sure MT5 is running
2. Check your credentials in `backend/.env`
3. Enable algo trading in MT5: Tools → Options → Expert Advisors → Allow automated trading

### "OpenAI API key invalid"
**Solution**:
1. Get your API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Make sure you have credits: [platform.openai.com/account/billing](https://platform.openai.com/account/billing)
3. Update `OPENAI_API_KEY` in `backend/.env`

**For more troubleshooting, see [SETUP.md](SETUP.md)**

## Safety & Warnings

⚠️ **IMPORTANT:**
- Always start with a **DEMO account**
- Test thoroughly for at least 1 month before considering live trading
- Trading involves substantial risk of loss
- Never risk more than you can afford to lose
- This is for educational purposes
- Past performance does not guarantee future results

### Recommended Settings for Testing
```env
ENVIRONMENT=demo
MAX_POSITIONS=1
RISK_PER_TRADE=0.01
MAX_DAILY_LOSS=0.05
AI_CONFIDENCE_THRESHOLD=0.70
```

## API Keys Required

1. **OpenAI API** - [Get it here](https://platform.openai.com/api-keys)
   - Required for AI analysis
   - Free tier available with pay-as-you-go

2. **News API** - [Get it here](https://newsapi.org/)
   - Required for market news
   - Free tier: 100 requests/day

3. **Alpha Vantage** - [Get it here](https://www.alphavantage.co/support/#api-key) (Optional)
   - Backup market data
   - Free tier available

**See [SETUP.md](SETUP.md) for detailed instructions on getting API keys!**

## Technical Stack

- **Backend**: Python 3.10+, FastAPI, MetaTrader5
- **Frontend**: React, Next.js, TailwindCSS
- **AI**: OpenAI GPT-4 or Anthropic Claude
- **Data**: NewsAPI, Alpha Vantage, Finnhub

## What's Included

✅ Full MT5 integration
✅ AI-powered market analysis (GPT-4/Claude)
✅ Technical indicators (RSI, MACD, Bollinger Bands, etc.)
✅ News sentiment analysis
✅ Risk management system
✅ Real-time dashboard
✅ WebSocket updates
✅ Decision transparency
✅ Automated trading
✅ Manual trading mode

## Performance & Monitoring

- Scans markets every 5 minutes (configurable)
- Real-time WebSocket updates to dashboard
- Comprehensive logging
- Trade history tracking
- Performance metrics

## Advanced Configuration

### Using Claude Instead of GPT-4
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus-20240229
ANTHROPIC_API_KEY=sk-ant-...
```

### Adding More Trading Pairs
Edit `config/strategy_config.json`:
```json
{
  "trading_pairs": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
}
```

## Documentation

- **[SETUP.md](SETUP.md)** - Complete setup guide with detailed .env instructions
- **[LICENSE](LICENSE)** - MIT License

## Support

For issues and questions:
1. Check [SETUP.md](SETUP.md) troubleshooting section
2. Review backend logs in terminal
3. Check browser console (F12) for frontend errors
4. Ensure all API keys are valid and have credits

## Development

### Running in Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Disclaimer

⚠️ **Trading involves substantial risk of loss.** This software is provided for educational and research purposes only. The developers are not responsible for any financial losses. Always:
- Test thoroughly in demo accounts
- Understand all risks
- Never invest more than you can afford to lose
- Consult a financial advisor before live trading
- Follow local regulations

## License

MIT License - See [LICENSE](LICENSE) file for details

---

## Quick Links

- 📖 **[Complete Setup Guide](SETUP.md)** - Detailed instructions
- 🔑 **[Get OpenAI API Key](https://platform.openai.com/api-keys)**
- 📰 **[Get News API Key](https://newsapi.org/)**
- 📊 **[Download MT5](https://www.metatrader5.com/)**

---

**Ready to start? Follow the [Complete Setup Guide (SETUP.md)](SETUP.md)!** 🚀
