"""Data models for MT5 trading"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class OrderType(str, Enum):
    """Order types"""
    BUY = "BUY"
    SELL = "SELL"
    BUY_LIMIT = "BUY_LIMIT"
    SELL_LIMIT = "SELL_LIMIT"
    BUY_STOP = "BUY_STOP"
    SELL_STOP = "SELL_STOP"


class TradeStatus(str, Enum):
    """Trade status"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class TimeFrame(str, Enum):
    """Supported timeframes"""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
    W1 = "W1"


class TickData(BaseModel):
    """Real-time tick data"""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    time: datetime
    spread: float = Field(default=0.0)


class Trade(BaseModel):
    """Trade model"""
    ticket: Optional[int] = None
    symbol: str
    order_type: OrderType
    volume: float
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: str = ""
    magic_number: int = 12345
    status: TradeStatus = TradeStatus.PENDING
    open_time: Optional[datetime] = None
    close_time: Optional[datetime] = None
    profit: Optional[float] = None
    commission: Optional[float] = None


class Position(BaseModel):
    """Open position model"""
    ticket: int
    symbol: str
    order_type: OrderType
    volume: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    profit: float
    swap: float = 0.0
    commission: float = 0.0
    open_time: datetime
    comment: str = ""


class AccountInfo(BaseModel):
    """Account information"""
    balance: float
    equity: float
    margin: float
    free_margin: float
    margin_level: float
    profit: float
    currency: str
    leverage: int
    name: str
    server: str


class MarketData(BaseModel):
    """Market data with OHLCV"""
    symbol: str
    timeframe: TimeFrame
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    tick_volume: int
