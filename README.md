# 🤖 AI Trading Robot

A fully automated, 24/7 AI-powered trading robot that uses neural networks, LLMs, and reinforcement learning to make autonomous trading decisions.

## 🌟 Features

### Neural Network Models
- **LSTM with Attention** - Price prediction using bidirectional LSTM with self-attention
- **Transformer** - Price prediction using transformer architecture
- **Pattern Recognition CNN** - Detects candlestick and chart patterns
- **Reinforcement Learning Agent** - DQN/PPO-based trading agent

### AI Analysis
- **LLM-Powered Reasoning** - Uses GPT-4 or Claude for deep market analysis
- **Chain-of-Thought** - Step-by-step reasoning process
- **Multi-Model Ensemble** - Combines predictions from all models
- **Autonomous Decision Making** - Thinks and trades independently

### Live Data
- **Real-Time Market Data** - MT5, Polygon, Finnhub integration
- **News Aggregation** - Multiple news sources with relevance scoring
- **Sentiment Analysis** - LLM-based and rule-based sentiment
- **Economic Calendar** - High-impact event awareness

### Risk Management
- **Dynamic Position Sizing** - Based on confidence and volatility
- **Stop Loss/Take Profit** - Automatic level calculation
- **Maximum Drawdown Protection** - Stops trading on large losses
- **Daily Loss Limits** - Prevents overtrading

### 24/7 Operation
- **Self-Healing** - Automatic recovery from failures
- **Health Monitoring** - Continuous component health checks
- **Auto-Reconnection** - Recovers from connection issues
- **Session Management** - Tracks performance per session

## 📁 Project Structure

```
ai_trading_bot/
├── backend/
│   ├── neural_networks/          # Deep learning models
│   │   ├── price_predictor.py    # LSTM & Transformer models
│   │   ├── pattern_recognition.py # CNN for patterns
│   │   └── rl_agent.py           # Reinforcement learning
│   ├── live_data/                # Real-time data handling
│   │   ├── stream_manager.py     # Market data streams
│   │   ├── news_aggregator.py    # News collection
│   │   └── sentiment_analyzer.py # Sentiment analysis
│   ├── ai_brain/                 # Autonomous AI system
│   │   ├── autonomous_brain.py   # Central AI coordinator
│   │   ├── memory_system.py      # Learning & memory
│   │   └── decision_engine.py    # Trade decisions
│   ├── trading_orchestrator.py   # 24/7 coordinator
│   ├── signal_generator.py       # Signal generation
│   ├── main_robot.py             # Main entry point
│   └── requirements.txt          # Python dependencies
├── config/
│   └── orchestrator_config.json  # Robot configuration
├── frontend/                     # Dashboard (React)
└── .env.example                  # Environment variables
```

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ (for dashboard)
- MetaTrader 5 (optional, for live trading)
- API keys for OpenAI/Anthropic, NewsAPI, etc.

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai_trading_bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API keys
```

### 3. Configuration

Edit `.env` with your API keys:
```env
OPENAI_API_KEY=sk-your-key
NEWS_API_KEY=your-news-key
FINNHUB_API_KEY=your-finnhub-key
MT5_LOGIN=your-mt5-login
MT5_PASSWORD=your-mt5-password
MT5_SERVER=your-broker-server
```

### 4. Run the Robot

```bash
# Paper trading mode (recommended to start)
python backend/main_robot.py --paper

# With custom config
python backend/main_robot.py --paper --config ./config/orchestrator_config.json

# Debug mode
python backend/main_robot.py --paper --log-level DEBUG
```

## 🧠 How It Works

### 1. Data Collection
The robot continuously collects:
- Real-time price ticks from MT5/other sources
- News articles from multiple sources
- Economic calendar events
- Market sentiment from analysis

### 2. Analysis Pipeline
```
Market Data → Technical Indicators → Pattern Recognition
                    ↓
                LSTM/Transformer Predictions
                    ↓
                Sentiment Analysis
                    ↓
                LLM Deep Reasoning
                    ↓
                RL Agent Decision
                    ↓
              Ensemble Decision Engine
                    ↓
               Final Trading Signal
```

### 3. Decision Making
The AI Brain uses chain-of-thought reasoning:
1. Analyze current market regime
2. Review technical indicators
3. Check pattern signals
4. Evaluate sentiment
5. Consider news impact
6. Combine all model predictions
7. Apply risk management
8. Generate final decision

### 4. Trade Execution
If signal passes validation:
- Calculate position size based on risk
- Set stop loss and take profit
- Execute trade via MT5
- Record in memory system
- Monitor for exit conditions

## ⚙️ Configuration

### `orchestrator_config.json`

```json
{
  "trading": {
    "symbols": ["XAUUSD"],
    "paper_trading": true
  },
  "risk_management": {
    "risk_per_trade": 0.02,
    "max_daily_trades": 10,
    "min_confidence": 0.65
  },
  "ai_settings": {
    "thinking_mode": "balanced",
    "llm_provider": "openai"
  }
}
```

## 📊 Dashboard

Start the dashboard:
```bash
cd frontend
npm install
npm run dev
```

Access at: http://localhost:3000

Features:
- Account overview
- Open positions
- Trade history
- AI analysis view
- Risk metrics
- Trading controls

## 🔒 Risk Warnings

⚠️ **IMPORTANT: Trading involves significant risk of loss.**

- Always start with paper trading
- Never trade with money you can't afford to lose
- Past performance doesn't guarantee future results
- The AI can and will make mistakes
- Monitor the robot regularly
- Use appropriate risk settings

## 🛠️ Training Neural Networks

To train the models on your data:

```python
from neural_networks import PricePredictor, TradingRLAgent

# Train LSTM model
predictor = PricePredictor()
await predictor.train(historical_data, epochs=100)

# Train RL agent
agent = TradingRLAgent(algorithm="dqn")
await agent.train(historical_data, episodes=1000)
```

## 🔧 Customization

### Add New Trading Symbol
Edit `orchestrator_config.json`:
```json
"symbols": ["XAUUSD", "EURUSD", "GBPUSD"]
```

### Adjust Risk Parameters
```json
"risk_management": {
  "risk_per_trade": 0.01,  // 1% per trade
  "max_positions": 2,
  "min_risk_reward": 2.0
}
```

### Change AI Provider
```json
"ai_settings": {
  "llm_provider": "anthropic"  // or "openai"
}
```

## 📈 Performance Tracking

The robot tracks:
- Win rate
- Profit factor
- Sharpe ratio
- Maximum drawdown
- Consecutive wins/losses
- Model performance by source

Access via:
```python
from ai_brain import TradingMemory
memory = TradingMemory()
insights = memory.get_learning_insights()
```

## 🐛 Troubleshooting

### MT5 Connection Failed
- Ensure MT5 terminal is running
- Check login credentials in .env
- Verify server name is correct

### No Trading Signals
- Check if confidence threshold is too high
- Verify data streams are receiving ticks
- Check API keys are valid

### High Memory Usage
- Reduce buffer sizes in config
- Clear old memory data
- Restart the robot periodically

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📞 Support

- Issues: GitHub Issues
- Documentation: See /docs folder
- Questions: Open a discussion

---

Built with 🤖 AI and ❤️ for traders
