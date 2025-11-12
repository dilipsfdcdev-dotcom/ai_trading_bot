"""AI Engine data models"""
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class SignalStrength(str, Enum):
    """Signal strength levels"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class MarketSignal(BaseModel):
    """Individual market signal"""
    source: str  # e.g., "RSI", "MACD", "News", "AI"
    signal: SignalStrength
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.now)


class SentimentAnalysis(BaseModel):
    """News and market sentiment"""
    overall_sentiment: str  # positive, negative, neutral
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    news_count: int
    key_topics: List[str]
    reasoning: str


class TechnicalAnalysis(BaseModel):
    """Technical indicators analysis"""
    trend: str  # uptrend, downtrend, sideways
    trend_strength: float = Field(ge=0.0, le=1.0)
    support_levels: List[float]
    resistance_levels: List[float]
    indicators: Dict[str, float]
    signal: SignalStrength
    reasoning: str


class AnalysisResult(BaseModel):
    """Complete market analysis result"""
    symbol: str
    timestamp: datetime = Field(default_factory=datetime.now)

    # Individual analyses
    technical_analysis: TechnicalAnalysis
    sentiment_analysis: SentimentAnalysis
    ai_reasoning: str

    # All signals combined
    signals: List[MarketSignal]

    # Final recommendation
    final_signal: SignalStrength
    confidence: float = Field(ge=0.0, le=1.0)
    should_trade: bool

    # Trade recommendation details
    suggested_entry: Optional[float] = None
    suggested_stop_loss: Optional[float] = None
    suggested_take_profit: Optional[float] = None
    risk_reward_ratio: Optional[float] = None

    # Explanation for dashboard
    summary: str
    reasoning_steps: List[str]
    risk_factors: List[str]
    opportunity_factors: List[str]
