# AI Trading Bot - Professional Automated Trading System

🤖 **World-class automated trading bot with MT5 integration, AI/LLM analysis, and real-time dashboard**

## Features

### 🎯 Core Capabilities
- **Fully Automated Trading**: 24/7 automated buy/sell execution via MT5
- **AI-Powered Analysis**: Uses LLM (GPT-4/Claude) for intelligent market analysis
- **Multi-Source Data**: Real-time market data, news, trends, and technical indicators
- **Smart Risk Management**: Balanced approach - not too strict, takes good opportunities
- **Real-time Dashboard**: Live statistics, charts, and decision transparency

### 📊 Data Analysis
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages, ATR, Stochastic
- **Market News**: Real-time news from multiple sources with sentiment analysis
- **Trend Analysis**: Multi-timeframe trend detection
- **Volume Analysis**: Order flow and volume patterns
- **AI Reasoning**: LLM-based market context understanding

### 🔍 Decision Transparency
The dashboard shows exactly what the bot checks before each trade:
- Current market conditions
- Technical indicator signals
- News sentiment impact
- AI reasoning and confidence score
- Risk assessment
- Historical performance context

## Architecture

```
ai_trading_bot/
├── backend/                    # Python FastAPI backend
│   ├── mt5_connector/         # MT5 integration
│   ├── ai_engine/             # LLM and AI analysis
│   ├── data_sources/          # Market data, news, trends
│   ├── strategy/              # Trading strategies
│   ├── risk_management/       # Risk and position management
│   └── api/                   # REST API and WebSocket
├── frontend/                  # React/Next.js dashboard
│   ├── components/            # UI components
│   ├── pages/                 # Dashboard pages
│   └── hooks/                 # Real-time data hooks
├── config/                    # Configuration files
└── data/                      # Historical data and logs
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- MetaTrader 5 installed
- OpenAI API key (or other LLM provider)

### Installation

1. **Clone and setup backend:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your MT5 credentials and API keys
```

2. **Setup frontend:**
```bash
cd frontend
npm install
cp .env.example .env.local
```

3. **Start the system:**
```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

4. **Access dashboard:**
Open http://localhost:3000

## Configuration

### MT5 Setup
Edit `config/mt5_config.json`:
```json
{
  "login": "YOUR_MT5_LOGIN",
  "password": "YOUR_MT5_PASSWORD",
  "server": "YOUR_MT5_SERVER",
  "path": "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
}
```

### Trading Strategy
Edit `config/strategy_config.json`:
```json
{
  "trading_pairs": ["EURUSD", "GBPUSD", "USDJPY"],
  "timeframes": ["M5", "M15", "H1"],
  "max_positions": 3,
  "risk_per_trade": 0.02,
  "ai_confidence_threshold": 0.65
}
```

## How It Works

### 1. Data Collection
- Fetches real-time price data from MT5
- Collects market news from multiple sources
- Calculates technical indicators
- Analyzes market trends

### 2. AI Analysis
- LLM analyzes market context and news sentiment
- Combines technical signals with fundamental analysis
- Generates trade recommendations with confidence scores
- Explains reasoning in human-readable format

### 3. Decision Making
- Evaluates all signals (technical + AI + news)
- Applies risk management rules
- Checks market conditions
- Makes go/no-go decision

### 4. Execution
- Opens positions via MT5
- Sets stop-loss and take-profit
- Monitors positions in real-time
- Adjusts or closes based on conditions

### 5. Dashboard Updates
- Real-time WebSocket updates
- Shows current analysis
- Displays decision reasoning
- Updates charts and statistics

## Safety Features

- **Position Sizing**: Automatic calculation based on account size
- **Stop Loss**: Always set on every trade
- **Max Drawdown**: Stops trading if drawdown exceeds limit
- **Daily Loss Limit**: Stops for the day if limit hit
- **Connection Monitoring**: Handles MT5 disconnections
- **Error Recovery**: Automatic retry and fallback mechanisms

## Dashboard Features

### Live Statistics
- Current P&L
- Win rate
- Active positions
- Daily/Weekly/Monthly performance
- Sharpe ratio

### Decision Log
Real-time log showing:
- What the bot is analyzing
- Current market conditions
- Technical signals
- AI reasoning
- Final decision and confidence

### Charts
- Price charts with indicators
- Equity curve
- Win/loss distribution
- Performance by pair

## API Keys Required

1. **OpenAI API** (for GPT-4 analysis) or **Anthropic** (for Claude)
2. **News API** (for market news)
3. **Alpha Vantage** (backup market data)

## Support

For issues or questions, check the documentation in `/docs` folder.

## Disclaimer

Trading involves risk. This bot is for educational and research purposes. Past performance does not guarantee future results. Always test thoroughly in a demo account before live trading.

## License

MIT License - See LICENSE file
