"""Main FastAPI application with WebSocket support for real-time dashboard"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict
import os
from dotenv import load_dotenv
import json

from mt5_connector import MT5Connector
from ai_engine import AIAnalyzer
from data_sources import NewsFetcher, MarketDataFetcher
from strategy import StrategyEngine
from risk_management import RiskManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="AI Trading Bot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
mt5_connector: Optional[MT5Connector] = None
ai_analyzer: Optional[AIAnalyzer] = None
news_fetcher: Optional[NewsFetcher] = None
market_data_fetcher: Optional[MarketDataFetcher] = None
strategy_engine: Optional[StrategyEngine] = None
risk_manager: Optional[RiskManager] = None

# WebSocket connections
active_connections: List[WebSocket] = []

# Trading state
is_trading_active = False
current_analyses = {}
recent_trades = []


class TradeRequest(BaseModel):
    """Manual trade request"""
    symbol: str
    action: str  # 'analyze' or 'execute'
    volume: Optional[float] = None


class ConfigUpdate(BaseModel):
    """Configuration update"""
    max_positions: Optional[int] = None
    risk_per_trade: Optional[float] = None
    trading_pairs: Optional[List[str]] = None


@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup"""
    global mt5_connector, ai_analyzer, news_fetcher, market_data_fetcher
    global strategy_engine, risk_manager

    logger.info("Starting AI Trading Bot...")

    try:
        # Initialize MT5
        mt5_connector = MT5Connector(
            login=int(os.getenv("MT5_LOGIN")),
            password=os.getenv("MT5_PASSWORD"),
            server=os.getenv("MT5_SERVER"),
            path=os.getenv("MT5_PATH")
        )

        if not mt5_connector.connect():
            logger.error("Failed to connect to MT5")
            raise Exception("MT5 connection failed")

        # Initialize AI
        ai_analyzer = AIAnalyzer(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-4-turbo-preview"),
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # Initialize data sources
        news_fetcher = NewsFetcher(
            news_api_key=os.getenv("NEWS_API_KEY"),
            finnhub_key=os.getenv("FINNHUB_API_KEY")
        )

        market_data_fetcher = MarketDataFetcher(
            alpha_vantage_key=os.getenv("ALPHA_VANTAGE_KEY")
        )

        # Initialize strategy engine
        strategy_engine = StrategyEngine(
            mt5_connector=mt5_connector,
            ai_analyzer=ai_analyzer,
            news_fetcher=news_fetcher,
            market_data_fetcher=market_data_fetcher
        )

        # Initialize risk manager
        risk_manager = RiskManager(
            mt5_connector=mt5_connector,
            max_positions=int(os.getenv("MAX_POSITIONS", 3)),
            risk_per_trade=float(os.getenv("RISK_PER_TRADE", 0.02)),
            max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", 0.05))
        )

        logger.info("All components initialized successfully")

        # Start background task for auto-trading
        asyncio.create_task(trading_loop())

    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global mt5_connector, is_trading_active

    logger.info("Shutting down AI Trading Bot...")
    is_trading_active = False

    if mt5_connector:
        mt5_connector.disconnect()


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket connected. Total connections: {len(active_connections)}")

    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Echo or process messages if needed
            await websocket.send_text(json.dumps({"status": "received", "data": data}))

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining: {len(active_connections)}")


async def broadcast_update(data: dict):
    """Broadcast update to all connected WebSocket clients"""
    if not active_connections:
        return

    message = json.dumps(data)
    for connection in active_connections[:]:  # Copy list to avoid modification during iteration
        try:
            await connection.send_text(message)
        except Exception as e:
            logger.error(f"Error sending to websocket: {str(e)}")
            active_connections.remove(connection)


# REST API Endpoints

@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/account")
async def get_account_info():
    """Get current account information"""
    if not mt5_connector:
        raise HTTPException(status_code=500, detail="MT5 not initialized")

    account_info = mt5_connector.get_account_info()
    if not account_info:
        raise HTTPException(status_code=500, detail="Failed to get account info")

    return account_info.dict()


@app.get("/positions")
async def get_positions():
    """Get open positions"""
    if not mt5_connector:
        raise HTTPException(status_code=500, detail="MT5 not initialized")

    positions = mt5_connector.get_open_positions()
    return [pos.dict() for pos in positions]


@app.get("/risk")
async def get_risk_summary():
    """Get risk management summary"""
    if not risk_manager:
        raise HTTPException(status_code=500, detail="Risk manager not initialized")

    return risk_manager.get_risk_summary()


@app.post("/analyze")
async def analyze_symbol(request: TradeRequest):
    """Analyze a symbol and return recommendation"""
    if not strategy_engine:
        raise HTTPException(status_code=500, detail="Strategy engine not initialized")

    from mt5_connector.models import TimeFrame

    analysis = strategy_engine.analyze_symbol(
        symbol=request.symbol,
        timeframe=TimeFrame.M15
    )

    if not analysis:
        raise HTTPException(status_code=500, detail="Analysis failed")

    # Store analysis
    current_analyses[request.symbol] = analysis

    # Broadcast to WebSocket clients
    await broadcast_update({
        "type": "analysis",
        "data": analysis.dict()
    })

    return analysis.dict()


@app.post("/trade")
async def execute_trade(request: TradeRequest):
    """Execute a trade based on analysis"""
    if not strategy_engine or not risk_manager:
        raise HTTPException(status_code=500, detail="Components not initialized")

    # Get or create analysis
    if request.symbol not in current_analyses:
        from mt5_connector.models import TimeFrame
        analysis = strategy_engine.analyze_symbol(
            symbol=request.symbol,
            timeframe=TimeFrame.M15
        )
        if not analysis:
            raise HTTPException(status_code=500, detail="Analysis failed")
        current_analyses[request.symbol] = analysis
    else:
        analysis = current_analyses[request.symbol]

    # Calculate position size if not provided
    if not request.volume:
        if analysis.suggested_stop_loss:
            request.volume = risk_manager.calculate_position_size(
                request.symbol,
                analysis.suggested_entry or 0,
                analysis.suggested_stop_loss
            )
        else:
            request.volume = 0.01  # Minimum

    # Execute trade
    trade = strategy_engine.execute_analysis_trade(
        analysis=analysis,
        volume=request.volume,
        risk_manager=risk_manager
    )

    if not trade:
        raise HTTPException(status_code=400, detail="Trade not executed")

    # Store and broadcast
    recent_trades.append(trade)
    await broadcast_update({
        "type": "trade",
        "data": trade.dict()
    })

    return trade.dict()


@app.post("/trading/start")
async def start_trading():
    """Start automated trading"""
    global is_trading_active
    is_trading_active = True
    logger.info("Automated trading started")
    return {"status": "started", "timestamp": datetime.now().isoformat()}


@app.post("/trading/stop")
async def stop_trading():
    """Stop automated trading"""
    global is_trading_active
    is_trading_active = False
    logger.info("Automated trading stopped")
    return {"status": "stopped", "timestamp": datetime.now().isoformat()}


@app.get("/trading/status")
async def get_trading_status():
    """Get trading status"""
    return {
        "is_active": is_trading_active,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/analyses")
async def get_analyses():
    """Get recent analyses"""
    return {
        symbol: analysis.dict()
        for symbol, analysis in current_analyses.items()
    }


async def trading_loop():
    """Main automated trading loop"""
    global is_trading_active, current_analyses

    # Trading pairs to monitor
    trading_pairs = os.getenv("TRADING_PAIRS", "EURUSD,GBPUSD,USDJPY").split(",")
    from mt5_connector.models import TimeFrame

    logger.info(f"Trading loop started. Monitoring: {trading_pairs}")

    while True:
        try:
            if is_trading_active and strategy_engine and risk_manager:
                logger.info("Scanning markets...")

                # Scan all trading pairs
                analyses = strategy_engine.scan_multiple_symbols(
                    symbols=trading_pairs,
                    timeframe=TimeFrame.M15
                )

                # Update current analyses
                current_analyses.update(analyses)

                # Broadcast analyses
                await broadcast_update({
                    "type": "market_scan",
                    "data": {
                        symbol: analysis.dict()
                        for symbol, analysis in analyses.items()
                    }
                })

                # Find best opportunity
                best = strategy_engine.get_best_trading_opportunity(analyses)

                if best and risk_manager.can_open_trade(best.symbol):
                    logger.info(f"Found opportunity: {best.symbol}")

                    # Calculate position size
                    volume = risk_manager.calculate_position_size(
                        best.symbol,
                        best.suggested_entry or 0,
                        best.suggested_stop_loss or 0
                    )

                    # Execute trade
                    trade = strategy_engine.execute_analysis_trade(
                        analysis=best,
                        volume=volume,
                        risk_manager=risk_manager
                    )

                    if trade:
                        recent_trades.append(trade)
                        await broadcast_update({
                            "type": "trade",
                            "data": trade.dict()
                        })

            # Wait before next iteration (e.g., 5 minutes)
            await asyncio.sleep(300)

        except Exception as e:
            logger.error(f"Error in trading loop: {str(e)}")
            await asyncio.sleep(60)  # Wait 1 minute on error


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=False
    )
