"""
Live Data Stream Manager

Handles real-time market data from multiple sources:
- MetaTrader 5 tick data
- WebSocket price feeds
- Alternative data sources (Polygon, Alpha Vantage, etc.)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json
import os

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Tick:
    """Single price tick"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    timestamp: datetime

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def spread(self) -> float:
        return self.ask - self.bid

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "bid": self.bid,
            "ask": self.ask,
            "last": self.last,
            "volume": self.volume,
            "mid": self.mid,
            "spread": self.spread,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class OHLCV:
    """OHLCV candle"""
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MarketDepth:
    """Order book depth"""
    symbol: str
    bids: List[Tuple[float, float]]  # (price, volume)
    asks: List[Tuple[float, float]]
    timestamp: datetime


@dataclass
class StreamConfig:
    """Configuration for data streams"""
    mt5_enabled: bool = True
    polygon_enabled: bool = False
    polygon_api_key: str = ""
    alpha_vantage_enabled: bool = False
    alpha_vantage_key: str = ""
    finnhub_enabled: bool = False
    finnhub_key: str = ""
    symbols: List[str] = field(default_factory=lambda: ["XAUUSD"])
    tick_buffer_size: int = 10000
    candle_buffer_size: int = 1000
    reconnect_delay: float = 5.0
    max_reconnect_attempts: int = 10


class DataAggregator:
    """Aggregates ticks into OHLCV candles"""

    def __init__(self, timeframe_minutes: int = 1):
        self.timeframe_minutes = timeframe_minutes
        self.current_candles: Dict[str, OHLCV] = {}
        self.completed_candles: Dict[str, deque] = {}

    def process_tick(self, tick: Tick) -> Optional[OHLCV]:
        """Process tick and return completed candle if any"""
        symbol = tick.symbol

        # Initialize if needed
        if symbol not in self.completed_candles:
            self.completed_candles[symbol] = deque(maxlen=1000)

        # Calculate candle timestamp
        candle_time = tick.timestamp.replace(
            second=0, microsecond=0,
            minute=(tick.timestamp.minute // self.timeframe_minutes) * self.timeframe_minutes
        )

        if symbol not in self.current_candles:
            # Start new candle
            self.current_candles[symbol] = OHLCV(
                symbol=symbol,
                timeframe=f"M{self.timeframe_minutes}",
                open=tick.last,
                high=tick.last,
                low=tick.last,
                close=tick.last,
                volume=tick.volume,
                timestamp=candle_time
            )
            return None

        current = self.current_candles[symbol]

        # Check if new candle should start
        if candle_time > current.timestamp:
            # Complete current candle
            completed = current
            self.completed_candles[symbol].append(completed)

            # Start new candle
            self.current_candles[symbol] = OHLCV(
                symbol=symbol,
                timeframe=f"M{self.timeframe_minutes}",
                open=tick.last,
                high=tick.last,
                low=tick.last,
                close=tick.last,
                volume=tick.volume,
                timestamp=candle_time
            )

            return completed

        # Update current candle
        current.high = max(current.high, tick.last)
        current.low = min(current.low, tick.last)
        current.close = tick.last
        current.volume += tick.volume

        return None

    def get_candles(self, symbol: str, count: int = 100) -> List[OHLCV]:
        """Get recent completed candles"""
        if symbol not in self.completed_candles:
            return []
        candles = list(self.completed_candles[symbol])
        return candles[-count:]

    def get_dataframe(self, symbol: str, count: int = 100) -> pd.DataFrame:
        """Get candles as DataFrame"""
        candles = self.get_candles(symbol, count)
        if not candles:
            return pd.DataFrame()

        data = [c.to_dict() for c in candles]
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        return df


class LiveDataStreamManager:
    """
    Manages real-time data streams from multiple sources

    Features:
    - Multi-source data aggregation
    - Automatic reconnection
    - Tick-to-candle aggregation
    - Event-driven callbacks
    - Buffer management
    """

    def __init__(self, config: Optional[StreamConfig] = None):
        self.config = config or StreamConfig()
        self.is_running = False
        self.connections: Dict[str, Any] = {}
        self.tick_buffers: Dict[str, deque] = {}
        self.callbacks: List[Callable[[Tick], None]] = []
        self.candle_callbacks: List[Callable[[OHLCV], None]] = []

        # Aggregators for different timeframes
        self.aggregators: Dict[int, DataAggregator] = {
            1: DataAggregator(1),   # 1 minute
            5: DataAggregator(5),   # 5 minutes
            15: DataAggregator(15), # 15 minutes
            60: DataAggregator(60)  # 1 hour
        }

        self.mt5_connector = None
        self._tasks: List[asyncio.Task] = []
        self._reconnect_counts: Dict[str, int] = {}

        # Statistics
        self.stats = {
            "ticks_received": 0,
            "candles_completed": 0,
            "reconnections": 0,
            "errors": 0,
            "start_time": None
        }

        logger.info("LiveDataStreamManager initialized")

    def add_tick_callback(self, callback: Callable[[Tick], None]):
        """Add callback for tick events"""
        self.callbacks.append(callback)

    def add_candle_callback(self, callback: Callable[[OHLCV], None]):
        """Add callback for candle completion events"""
        self.candle_callbacks.append(callback)

    async def _emit_tick(self, tick: Tick):
        """Emit tick to all callbacks"""
        self.stats["ticks_received"] += 1

        # Store in buffer
        if tick.symbol not in self.tick_buffers:
            self.tick_buffers[tick.symbol] = deque(maxlen=self.config.tick_buffer_size)
        self.tick_buffers[tick.symbol].append(tick)

        # Process through aggregators
        for timeframe, aggregator in self.aggregators.items():
            completed_candle = aggregator.process_tick(tick)
            if completed_candle:
                self.stats["candles_completed"] += 1
                for callback in self.candle_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(completed_candle)
                        else:
                            callback(completed_candle)
                    except Exception as e:
                        logger.error(f"Candle callback error: {e}")

        # Notify tick callbacks
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(tick)
                else:
                    callback(tick)
            except Exception as e:
                logger.error(f"Tick callback error: {e}")

    async def _stream_mt5(self):
        """Stream ticks from MetaTrader 5"""
        if not self.config.mt5_enabled:
            return

        try:
            # Import MT5 connector
            from mt5_connector.connector import MT5Connector
            self.mt5_connector = MT5Connector()

            if not await self.mt5_connector.connect():
                logger.error("Failed to connect to MT5")
                return

            logger.info("MT5 tick streaming started")

            while self.is_running:
                for symbol in self.config.symbols:
                    try:
                        tick_data = await self.mt5_connector.get_tick(symbol)
                        if tick_data:
                            tick = Tick(
                                symbol=symbol,
                                bid=tick_data.get('bid', 0),
                                ask=tick_data.get('ask', 0),
                                last=tick_data.get('last', (tick_data.get('bid', 0) + tick_data.get('ask', 0)) / 2),
                                volume=tick_data.get('volume', 0),
                                timestamp=datetime.now()
                            )
                            await self._emit_tick(tick)
                    except Exception as e:
                        logger.error(f"MT5 tick error for {symbol}: {e}")
                        self.stats["errors"] += 1

                await asyncio.sleep(0.1)  # 100ms between tick polls

        except Exception as e:
            logger.error(f"MT5 streaming error: {e}")
            self.stats["errors"] += 1

    async def _stream_polygon(self):
        """Stream ticks from Polygon.io WebSocket"""
        if not self.config.polygon_enabled or not WEBSOCKETS_AVAILABLE:
            return

        url = f"wss://socket.polygon.io/forex"
        source = "polygon"

        while self.is_running:
            try:
                async with websockets.connect(url) as ws:
                    # Authenticate
                    await ws.send(json.dumps({
                        "action": "auth",
                        "params": self.config.polygon_api_key
                    }))

                    # Subscribe to symbols
                    symbols = [f"C.{s.replace('/', '')}" for s in self.config.symbols]
                    await ws.send(json.dumps({
                        "action": "subscribe",
                        "params": ",".join(symbols)
                    }))

                    logger.info("Polygon WebSocket connected")
                    self._reconnect_counts[source] = 0

                    while self.is_running:
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=30)
                            data = json.loads(message)

                            for item in data:
                                if item.get('ev') == 'C':  # Forex quote
                                    tick = Tick(
                                        symbol=item.get('p', '').replace('C.', ''),
                                        bid=item.get('b', 0),
                                        ask=item.get('a', 0),
                                        last=(item.get('b', 0) + item.get('a', 0)) / 2,
                                        volume=0,
                                        timestamp=datetime.fromtimestamp(item.get('t', 0) / 1000)
                                    )
                                    await self._emit_tick(tick)

                        except asyncio.TimeoutError:
                            await ws.ping()

            except Exception as e:
                logger.error(f"Polygon WebSocket error: {e}")
                self.stats["errors"] += 1
                self._reconnect_counts[source] = self._reconnect_counts.get(source, 0) + 1

                if self._reconnect_counts[source] >= self.config.max_reconnect_attempts:
                    logger.error(f"Max reconnect attempts reached for {source}")
                    break

                self.stats["reconnections"] += 1
                await asyncio.sleep(self.config.reconnect_delay)

    async def _stream_finnhub(self):
        """Stream ticks from Finnhub WebSocket"""
        if not self.config.finnhub_enabled or not WEBSOCKETS_AVAILABLE:
            return

        url = f"wss://ws.finnhub.io?token={self.config.finnhub_key}"
        source = "finnhub"

        while self.is_running:
            try:
                async with websockets.connect(url) as ws:
                    # Subscribe to symbols
                    for symbol in self.config.symbols:
                        await ws.send(json.dumps({
                            "type": "subscribe",
                            "symbol": f"OANDA:{symbol.replace('/', '_')}"
                        }))

                    logger.info("Finnhub WebSocket connected")
                    self._reconnect_counts[source] = 0

                    while self.is_running:
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=30)
                            data = json.loads(message)

                            if data.get('type') == 'trade':
                                for trade in data.get('data', []):
                                    symbol = trade.get('s', '').replace('OANDA:', '').replace('_', '/')
                                    tick = Tick(
                                        symbol=symbol,
                                        bid=trade.get('p', 0),
                                        ask=trade.get('p', 0),
                                        last=trade.get('p', 0),
                                        volume=trade.get('v', 0),
                                        timestamp=datetime.fromtimestamp(trade.get('t', 0) / 1000)
                                    )
                                    await self._emit_tick(tick)

                        except asyncio.TimeoutError:
                            pass

            except Exception as e:
                logger.error(f"Finnhub WebSocket error: {e}")
                self.stats["errors"] += 1
                self._reconnect_counts[source] = self._reconnect_counts.get(source, 0) + 1

                if self._reconnect_counts[source] >= self.config.max_reconnect_attempts:
                    break

                self.stats["reconnections"] += 1
                await asyncio.sleep(self.config.reconnect_delay)

    async def _poll_alpha_vantage(self):
        """Poll Alpha Vantage for forex data"""
        if not self.config.alpha_vantage_enabled or not AIOHTTP_AVAILABLE:
            return

        base_url = "https://www.alphavantage.co/query"

        while self.is_running:
            for symbol in self.config.symbols:
                try:
                    # Parse symbol (e.g., "XAUUSD" -> "XAU", "USD")
                    from_currency = symbol[:3]
                    to_currency = symbol[3:6] if len(symbol) >= 6 else "USD"

                    async with aiohttp.ClientSession() as session:
                        params = {
                            "function": "CURRENCY_EXCHANGE_RATE",
                            "from_currency": from_currency,
                            "to_currency": to_currency,
                            "apikey": self.config.alpha_vantage_key
                        }

                        async with session.get(base_url, params=params) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                rate_data = data.get("Realtime Currency Exchange Rate", {})

                                if rate_data:
                                    bid = float(rate_data.get("8. Bid Price", 0))
                                    ask = float(rate_data.get("9. Ask Price", 0))

                                    tick = Tick(
                                        symbol=symbol,
                                        bid=bid,
                                        ask=ask,
                                        last=(bid + ask) / 2,
                                        volume=0,
                                        timestamp=datetime.now()
                                    )
                                    await self._emit_tick(tick)

                except Exception as e:
                    logger.error(f"Alpha Vantage error: {e}")
                    self.stats["errors"] += 1

            # Alpha Vantage has rate limits
            await asyncio.sleep(12)  # ~5 calls per minute for free tier

    async def start(self):
        """Start all data streams"""
        if self.is_running:
            logger.warning("Stream manager already running")
            return

        self.is_running = True
        self.stats["start_time"] = datetime.now()

        logger.info("Starting live data streams...")

        # Start all stream tasks
        self._tasks = [
            asyncio.create_task(self._stream_mt5()),
            asyncio.create_task(self._stream_polygon()),
            asyncio.create_task(self._stream_finnhub()),
            asyncio.create_task(self._poll_alpha_vantage())
        ]

        logger.info("All data streams started")

    async def stop(self):
        """Stop all data streams"""
        self.is_running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Close MT5 connection
        if self.mt5_connector:
            await self.mt5_connector.disconnect()

        self._tasks = []
        logger.info("All data streams stopped")

    def get_latest_tick(self, symbol: str) -> Optional[Tick]:
        """Get the most recent tick for a symbol"""
        if symbol in self.tick_buffers and self.tick_buffers[symbol]:
            return self.tick_buffers[symbol][-1]
        return None

    def get_recent_ticks(self, symbol: str, count: int = 100) -> List[Tick]:
        """Get recent ticks for a symbol"""
        if symbol not in self.tick_buffers:
            return []
        return list(self.tick_buffers[symbol])[-count:]

    def get_candles(
        self,
        symbol: str,
        timeframe: int = 1,
        count: int = 100
    ) -> pd.DataFrame:
        """Get OHLCV candles as DataFrame"""
        if timeframe not in self.aggregators:
            timeframe = 1
        return self.aggregators[timeframe].get_dataframe(symbol, count)

    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics"""
        stats = self.stats.copy()
        if stats["start_time"]:
            runtime = datetime.now() - stats["start_time"]
            stats["runtime_seconds"] = runtime.total_seconds()
            stats["ticks_per_second"] = (
                stats["ticks_received"] / runtime.total_seconds()
                if runtime.total_seconds() > 0 else 0
            )
        return stats

    def get_market_snapshot(self) -> Dict[str, Any]:
        """Get current market snapshot for all symbols"""
        snapshot = {}
        for symbol in self.config.symbols:
            tick = self.get_latest_tick(symbol)
            if tick:
                snapshot[symbol] = {
                    "tick": tick.to_dict(),
                    "candles_1m": len(self.aggregators[1].get_candles(symbol)),
                    "candles_5m": len(self.aggregators[5].get_candles(symbol)),
                    "candles_15m": len(self.aggregators[15].get_candles(symbol)),
                    "candles_1h": len(self.aggregators[60].get_candles(symbol))
                }
        return snapshot
