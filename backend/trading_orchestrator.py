"""
24/7 Trading Orchestrator

The main orchestrator that runs the trading robot 24/7:
- Coordinates all components
- Self-healing and auto-recovery
- Continuous market monitoring
- Automated trade execution
- Health monitoring and alerts
"""

import asyncio
import logging
import signal
import sys
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import traceback
import os
import json

logger = logging.getLogger(__name__)


class OrchestratorState(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    RECOVERING = "recovering"
    SHUTDOWN = "shutdown"


class ComponentStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result for a component"""
    component: str
    status: ComponentStatus
    last_check: datetime
    error_message: Optional[str] = None
    response_time_ms: float = 0
    consecutive_failures: int = 0


@dataclass
class TradingSession:
    """Trading session statistics"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    trades_opened: int = 0
    trades_closed: int = 0
    total_pnl: float = 0
    signals_generated: int = 0
    errors_encountered: int = 0
    uptime_seconds: float = 0


class TradingOrchestrator:
    """
    24/7 Trading Orchestrator

    The main controller that:
    - Initializes and coordinates all components
    - Runs continuous trading loops
    - Handles errors and recovers automatically
    - Monitors system health
    - Manages trading sessions
    """

    def __init__(
        self,
        config_path: str = "./config/orchestrator_config.json",
        auto_recovery: bool = True,
        max_recovery_attempts: int = 5,
        health_check_interval: int = 60,
        analysis_interval: int = 300,  # 5 minutes
        enable_paper_trading: bool = True
    ):
        self.config_path = config_path
        self.auto_recovery = auto_recovery
        self.max_recovery_attempts = max_recovery_attempts
        self.health_check_interval = health_check_interval
        self.analysis_interval = analysis_interval
        self.enable_paper_trading = enable_paper_trading

        # State
        self.state = OrchestratorState.INITIALIZING
        self.recovery_attempts = 0
        self.session: Optional[TradingSession] = None
        self._shutdown_event = asyncio.Event()
        self._tasks: List[asyncio.Task] = []

        # Component health
        self.health_status: Dict[str, HealthCheck] = {}

        # Components (initialized later)
        self.ai_brain = None
        self.data_stream = None
        self.news_aggregator = None
        self.sentiment_analyzer = None
        self.pattern_recognition = None
        self.decision_engine = None
        self.memory_system = None
        self.mt5_connector = None

        # Callbacks
        self.on_trade_opened: List[Callable] = []
        self.on_trade_closed: List[Callable] = []
        self.on_signal_generated: List[Callable] = []
        self.on_error: List[Callable] = []

        # Load configuration
        self.config = self._load_config()

        logger.info("TradingOrchestrator initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load orchestrator configuration"""
        default_config = {
            "symbols": ["XAUUSD"],
            "timeframes": ["M5", "M15", "H1"],
            "risk_per_trade": 0.02,
            "max_daily_trades": 10,
            "max_positions": 3,
            "min_confidence": 0.65,
            "trading_hours": None,
            "llm_provider": "openai",
            "enable_notifications": True,
            "log_level": "INFO"
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Error loading config: {e}")

        return default_config

    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing trading components...")

        try:
            # Initialize MT5 Connector
            try:
                from mt5_connector.connector import MT5Connector
                self.mt5_connector = MT5Connector()
                connected = await self.mt5_connector.connect()
                if connected:
                    self._update_health("mt5", ComponentStatus.HEALTHY)
                else:
                    self._update_health("mt5", ComponentStatus.DEGRADED, "Not connected")
            except Exception as e:
                logger.warning(f"MT5 initialization failed: {e}")
                self._update_health("mt5", ComponentStatus.FAILED, str(e))

            # Initialize Data Stream Manager
            try:
                from live_data.stream_manager import LiveDataStreamManager, StreamConfig
                stream_config = StreamConfig(
                    symbols=self.config.get("symbols", ["XAUUSD"]),
                    mt5_enabled=self.mt5_connector is not None
                )
                self.data_stream = LiveDataStreamManager(stream_config)
                self._update_health("data_stream", ComponentStatus.HEALTHY)
            except Exception as e:
                logger.warning(f"Data stream initialization failed: {e}")
                self._update_health("data_stream", ComponentStatus.FAILED, str(e))

            # Initialize News Aggregator
            try:
                from live_data.news_aggregator import RealTimeNewsAggregator, NewsAggregatorConfig
                news_config = NewsAggregatorConfig(
                    newsapi_key=os.getenv("NEWS_API_KEY", ""),
                    finnhub_key=os.getenv("FINNHUB_API_KEY", "")
                )
                self.news_aggregator = RealTimeNewsAggregator(news_config)
                self._update_health("news", ComponentStatus.HEALTHY)
            except Exception as e:
                logger.warning(f"News aggregator initialization failed: {e}")
                self._update_health("news", ComponentStatus.DEGRADED, str(e))

            # Initialize Sentiment Analyzer
            try:
                from live_data.sentiment_analyzer import LiveSentimentAnalyzer
                self.sentiment_analyzer = LiveSentimentAnalyzer(
                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
                )
                self._update_health("sentiment", ComponentStatus.HEALTHY)
            except Exception as e:
                logger.warning(f"Sentiment analyzer initialization failed: {e}")
                self._update_health("sentiment", ComponentStatus.DEGRADED, str(e))

            # Initialize Pattern Recognition
            try:
                from neural_networks.pattern_recognition import PatternRecognitionCNN
                self.pattern_recognition = PatternRecognitionCNN()
                self._update_health("pattern", ComponentStatus.HEALTHY)
            except Exception as e:
                logger.warning(f"Pattern recognition initialization failed: {e}")
                self._update_health("pattern", ComponentStatus.DEGRADED, str(e))

            # Initialize AI Brain
            try:
                from ai_brain.autonomous_brain import AutonomousAIBrain, ThinkingMode
                self.ai_brain = AutonomousAIBrain(
                    thinking_mode=ThinkingMode.BALANCED,
                    risk_tolerance=self.config.get("risk_per_trade", 0.02)
                )
                await self.ai_brain.initialize_models()
                self._update_health("ai_brain", ComponentStatus.HEALTHY)
            except Exception as e:
                logger.warning(f"AI Brain initialization failed: {e}")
                self._update_health("ai_brain", ComponentStatus.DEGRADED, str(e))

            # Initialize Memory System
            try:
                from ai_brain.memory_system import TradingMemory
                self.memory_system = TradingMemory()
                self._update_health("memory", ComponentStatus.HEALTHY)
            except Exception as e:
                logger.warning(f"Memory system initialization failed: {e}")
                self._update_health("memory", ComponentStatus.DEGRADED, str(e))

            # Initialize Decision Engine
            try:
                from ai_brain.decision_engine import DecisionEngine
                self.decision_engine = DecisionEngine(
                    max_daily_trades=self.config.get("max_daily_trades", 10),
                    max_concurrent_positions=self.config.get("max_positions", 3),
                    min_confidence_threshold=self.config.get("min_confidence", 0.65),
                    risk_per_trade=self.config.get("risk_per_trade", 0.02)
                )
                self._update_health("decision", ComponentStatus.HEALTHY)
            except Exception as e:
                logger.warning(f"Decision engine initialization failed: {e}")
                self._update_health("decision", ComponentStatus.FAILED, str(e))

            # Check overall health
            failed_critical = [
                h for h in self.health_status.values()
                if h.status == ComponentStatus.FAILED and h.component in ["ai_brain", "decision"]
            ]

            if failed_critical:
                raise Exception(f"Critical components failed: {[h.component for h in failed_critical]}")

            self.state = OrchestratorState.RUNNING
            logger.info("All components initialized successfully")

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self.state = OrchestratorState.ERROR
            raise

    def _update_health(
        self,
        component: str,
        status: ComponentStatus,
        error: Optional[str] = None,
        response_time: float = 0
    ):
        """Update component health status"""
        if component not in self.health_status:
            self.health_status[component] = HealthCheck(
                component=component,
                status=status,
                last_check=datetime.now(),
                error_message=error,
                response_time_ms=response_time
            )
        else:
            h = self.health_status[component]
            h.status = status
            h.last_check = datetime.now()
            h.error_message = error
            h.response_time_ms = response_time

            if status == ComponentStatus.FAILED:
                h.consecutive_failures += 1
            else:
                h.consecutive_failures = 0

    async def _health_check_loop(self):
        """Continuous health checking"""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(10)

    async def _perform_health_checks(self):
        """Perform health checks on all components"""
        # Check MT5
        if self.mt5_connector:
            try:
                account = await self.mt5_connector.get_account_info()
                if account:
                    self._update_health("mt5", ComponentStatus.HEALTHY)
                else:
                    self._update_health("mt5", ComponentStatus.DEGRADED, "No account info")
            except Exception as e:
                self._update_health("mt5", ComponentStatus.FAILED, str(e))

        # Check Data Stream
        if self.data_stream:
            stats = self.data_stream.get_stats()
            if stats.get("ticks_received", 0) > 0:
                self._update_health("data_stream", ComponentStatus.HEALTHY)
            elif self.data_stream.is_running:
                self._update_health("data_stream", ComponentStatus.DEGRADED, "No ticks")

        # Check AI Brain
        if self.ai_brain:
            status = self.ai_brain.get_brain_status()
            if status.get("is_thinking") or status.get("decisions_made", 0) >= 0:
                self._update_health("ai_brain", ComponentStatus.HEALTHY)

        # Auto-recovery for failed components
        if self.auto_recovery:
            await self._auto_recover()

    async def _auto_recover(self):
        """Attempt to recover failed components"""
        failed = [
            h.component for h in self.health_status.values()
            if h.status == ComponentStatus.FAILED and h.consecutive_failures >= 3
        ]

        if not failed:
            return

        if self.recovery_attempts >= self.max_recovery_attempts:
            logger.error("Max recovery attempts reached, stopping orchestrator")
            self.state = OrchestratorState.ERROR
            await self.stop()
            return

        self.state = OrchestratorState.RECOVERING
        self.recovery_attempts += 1
        logger.info(f"Attempting recovery for: {failed}")

        for component in failed:
            try:
                if component == "mt5":
                    if self.mt5_connector:
                        await self.mt5_connector.disconnect()
                        await asyncio.sleep(5)
                        await self.mt5_connector.connect()

                elif component == "data_stream":
                    if self.data_stream:
                        await self.data_stream.stop()
                        await asyncio.sleep(2)
                        await self.data_stream.start()

                logger.info(f"Recovery attempted for {component}")

            except Exception as e:
                logger.error(f"Recovery failed for {component}: {e}")

        self.state = OrchestratorState.RUNNING

    async def _analysis_loop(self):
        """Main analysis and trading loop"""
        while not self._shutdown_event.is_set():
            try:
                if self.state != OrchestratorState.RUNNING:
                    await asyncio.sleep(5)
                    continue

                for symbol in self.config.get("symbols", ["XAUUSD"]):
                    await self._analyze_and_trade(symbol)

                await asyncio.sleep(self.analysis_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Analysis loop error: {e}")
                traceback.print_exc()
                await asyncio.sleep(30)

    async def _analyze_and_trade(self, symbol: str):
        """Analyze market and make trading decisions"""
        try:
            # Get market data
            price_data = None
            current_price = None

            if self.data_stream:
                price_data = self.data_stream.get_candles(symbol, 5, 200)
                tick = self.data_stream.get_latest_tick(symbol)
                if tick:
                    current_price = tick.mid

            if price_data is None or price_data.empty:
                if self.mt5_connector:
                    price_data = await self.mt5_connector.get_ohlcv(symbol, "M5", 200)
                    tick_data = await self.mt5_connector.get_tick(symbol)
                    if tick_data:
                        current_price = (tick_data.get('bid', 0) + tick_data.get('ask', 0)) / 2

            if price_data is None or price_data.empty or current_price is None:
                logger.warning(f"No price data for {symbol}")
                return

            # Get technical indicators
            technical_indicators = self._calculate_indicators(price_data)

            # Get pattern analysis
            pattern_analysis = None
            if self.pattern_recognition:
                pattern_analysis = await self.pattern_recognition.detect_patterns(price_data, symbol)

            # Get sentiment
            sentiment_data = None
            if self.sentiment_analyzer:
                sentiment_data = self.sentiment_analyzer.get_aggregated_sentiment(symbol).to_dict()

            # Get news
            news_summary = []
            if self.news_aggregator:
                articles = self.news_aggregator.get_recent_articles(count=10, symbols=[symbol])
                news_summary = [a.to_dict() for a in articles]

            # Get account info
            account_balance = 10000  # Default for paper trading
            current_position = None

            if self.mt5_connector:
                account = await self.mt5_connector.get_account_info()
                if account:
                    account_balance = account.get('balance', 10000)

                positions = await self.mt5_connector.get_positions()
                for pos in positions:
                    if pos.get('symbol') == symbol:
                        current_position = pos
                        break

            # Create market context
            from ai_brain.autonomous_brain import MarketContext
            context = MarketContext(
                symbol=symbol,
                current_price=current_price,
                price_data=price_data,
                technical_indicators=technical_indicators,
                pattern_analysis=pattern_analysis,
                sentiment_data=sentiment_data,
                news_summary=news_summary,
                economic_events=[],
                current_position=current_position,
                account_balance=account_balance,
                timestamp=datetime.now()
            )

            # AI Brain thinking
            if self.ai_brain:
                decision = await self.ai_brain.think(context)

                if self.session:
                    self.session.signals_generated += 1

                # Notify callbacks
                for callback in self.on_signal_generated:
                    try:
                        await callback(decision)
                    except:
                        pass

                # Make trading decision
                if decision.action in ["BUY", "SELL"] and self.decision_engine:
                    signals = {
                        "brain": {
                            "direction": decision.action,
                            "confidence": decision.confidence,
                            "stop_loss": decision.stop_loss,
                            "take_profit": decision.take_profit
                        },
                        "technical": technical_indicators
                    }

                    if pattern_analysis:
                        signals["pattern"] = {
                            "signal": pattern_analysis.get("overall_signal"),
                            "confidence": pattern_analysis.get("overall_confidence")
                        }

                    if sentiment_data:
                        signals["sentiment"] = {
                            "direction": "BUY" if sentiment_data.get("sentiment_score", 0) > 0.3 else "SELL" if sentiment_data.get("sentiment_score", 0) < -0.3 else "NEUTRAL",
                            "confidence": abs(sentiment_data.get("sentiment_score", 0))
                        }

                    order = await self.decision_engine.make_decision(
                        signals=signals,
                        current_price=current_price,
                        symbol=symbol,
                        account_balance=account_balance,
                        current_spread=0.001 * current_price
                    )

                    if order:
                        await self._execute_order(order)

            logger.info(f"Analysis completed for {symbol}")

        except Exception as e:
            logger.error(f"Analysis error for {symbol}: {e}")
            traceback.print_exc()
            if self.session:
                self.session.errors_encountered += 1

    def _calculate_indicators(self, df) -> Dict[str, float]:
        """Calculate technical indicators"""
        indicators = {}

        try:
            close = df['close']

            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = float(100 - (100 / (1 + rs)).iloc[-1])

            # MACD
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            indicators['macd'] = float(macd.iloc[-1])
            indicators['macd_signal'] = float(signal.iloc[-1])
            indicators['macd_hist'] = float((macd - signal).iloc[-1])

            # Bollinger Bands
            sma20 = close.rolling(window=20).mean()
            std20 = close.rolling(window=20).std()
            bb_upper = sma20 + (std20 * 2)
            bb_lower = sma20 - (std20 * 2)
            indicators['bb_position'] = float(
                (close.iloc[-1] - bb_lower.iloc[-1]) /
                (bb_upper.iloc[-1] - bb_lower.iloc[-1])
            )

            # ATR
            high = df['high']
            low = df['low']
            tr = high - low
            indicators['atr'] = float(tr.rolling(window=14).mean().iloc[-1])

            # Momentum
            indicators['momentum_10'] = float(close.iloc[-1] / close.iloc[-10] - 1) if len(close) >= 10 else 0
            indicators['momentum_20'] = float(close.iloc[-1] / close.iloc[-20] - 1) if len(close) >= 20 else 0

        except Exception as e:
            logger.warning(f"Indicator calculation error: {e}")

        return indicators

    async def _execute_order(self, order):
        """Execute a trade order"""
        try:
            if self.enable_paper_trading:
                logger.info(f"[PAPER] Executing order: {order.direction} {order.volume} {order.symbol}")
                self.decision_engine.record_trade_open(
                    order.order_id,
                    order.symbol,
                    order.direction,
                    order.volume,
                    order.entry_price or 0,
                    order.stop_loss,
                    order.take_profit
                )

                if self.memory_system:
                    self.memory_system.remember_trade(
                        trade_id=order.order_id,
                        symbol=order.symbol,
                        action=order.direction,
                        entry_price=order.entry_price or 0,
                        market_regime=self.ai_brain.current_regime.value if self.ai_brain else "unknown",
                        confidence=order.metadata.get("confidence", 0.5),
                        reasoning=str(order.metadata),
                        technical_state={},
                        sentiment_state={},
                        patterns=[]
                    )

                if self.session:
                    self.session.trades_opened += 1

                for callback in self.on_trade_opened:
                    await callback(order)

            elif self.mt5_connector:
                # Real trading
                result = await self.mt5_connector.place_order(
                    symbol=order.symbol,
                    order_type=order.direction.lower(),
                    volume=order.volume,
                    sl=order.stop_loss,
                    tp=order.take_profit
                )

                if result and result.get('success'):
                    self.decision_engine.record_trade_open(
                        order.order_id,
                        order.symbol,
                        order.direction,
                        order.volume,
                        result.get('price', 0),
                        order.stop_loss,
                        order.take_profit
                    )

                    if self.session:
                        self.session.trades_opened += 1

                    logger.info(f"Order executed: {order.order_id}")

        except Exception as e:
            logger.error(f"Order execution error: {e}")

    async def start(self):
        """Start the trading orchestrator"""
        logger.info("Starting Trading Orchestrator...")

        # Initialize components
        await self.initialize()

        # Create session
        import uuid
        self.session = TradingSession(
            session_id=f"SESSION-{uuid.uuid4().hex[:8].upper()}",
            start_time=datetime.now()
        )

        # Start data streams
        if self.data_stream:
            await self.data_stream.start()

        # Start news aggregator
        if self.news_aggregator:
            await self.news_aggregator.start()

        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._analysis_loop())
        ]

        logger.info(f"Trading Orchestrator started - Session: {self.session.session_id}")

        # Wait for shutdown
        await self._shutdown_event.wait()

    async def stop(self):
        """Stop the trading orchestrator"""
        logger.info("Stopping Trading Orchestrator...")

        self._shutdown_event.set()
        self.state = OrchestratorState.SHUTDOWN

        # Cancel tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Stop components
        if self.data_stream:
            await self.data_stream.stop()

        if self.news_aggregator:
            await self.news_aggregator.stop()

        if self.mt5_connector:
            await self.mt5_connector.disconnect()

        # Finalize session
        if self.session:
            self.session.end_time = datetime.now()
            self.session.uptime_seconds = (
                self.session.end_time - self.session.start_time
            ).total_seconds()

            logger.info(f"Session {self.session.session_id} ended - "
                       f"Trades: {self.session.trades_opened}, "
                       f"Signals: {self.session.signals_generated}")

        logger.info("Trading Orchestrator stopped")

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            "state": self.state.value,
            "session": {
                "id": self.session.session_id if self.session else None,
                "start_time": self.session.start_time.isoformat() if self.session else None,
                "trades_opened": self.session.trades_opened if self.session else 0,
                "signals_generated": self.session.signals_generated if self.session else 0,
                "errors": self.session.errors_encountered if self.session else 0
            },
            "health": {
                name: {
                    "status": h.status.value,
                    "last_check": h.last_check.isoformat(),
                    "error": h.error_message,
                    "failures": h.consecutive_failures
                }
                for name, h in self.health_status.items()
            },
            "recovery_attempts": self.recovery_attempts,
            "config": self.config
        }


async def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    orchestrator = TradingOrchestrator(
        enable_paper_trading=True  # Start with paper trading
    )

    # Handle shutdown signals
    def signal_handler():
        asyncio.create_task(orchestrator.stop())

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await orchestrator.start()
    except KeyboardInterrupt:
        await orchestrator.stop()


if __name__ == "__main__":
    asyncio.run(main())
