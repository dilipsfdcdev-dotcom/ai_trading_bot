"""
Advanced Signal Generator

Combines all AI models and data sources to generate high-quality trading signals.

Features:
- Multi-timeframe analysis
- Model ensemble with dynamic weighting
- Signal filtering and validation
- Confidence scoring
- Risk-adjusted recommendations
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class SignalType(Enum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WEAK_BUY = "weak_buy"
    NEUTRAL = "neutral"
    WEAK_SELL = "weak_sell"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class TimeHorizon(Enum):
    SCALP = "scalp"  # Minutes
    INTRADAY = "intraday"  # Hours
    SWING = "swing"  # Days
    POSITION = "position"  # Weeks


@dataclass
class TradingSignal:
    """Complete trading signal"""
    symbol: str
    signal_type: SignalType
    direction: str  # BUY, SELL, NEUTRAL
    confidence: float  # 0-1
    strength: float  # 0-1
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    position_size_pct: float
    time_horizon: TimeHorizon
    expiry: datetime
    sources: Dict[str, Dict[str, Any]]
    reasoning: str
    metadata: Dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "direction": self.direction,
            "confidence": self.confidence,
            "strength": self.strength,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_reward": self.risk_reward,
            "position_size_pct": self.position_size_pct,
            "time_horizon": self.time_horizon.value,
            "expiry": self.expiry.isoformat(),
            "sources": self.sources,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MultiTimeframeAnalysis:
    """Analysis across multiple timeframes"""
    symbol: str
    timeframes: Dict[str, Dict[str, Any]]  # M1, M5, M15, H1, H4, D1
    dominant_trend: str
    trend_alignment: float  # 0-1, how aligned are timeframes
    key_levels: List[float]
    timestamp: datetime


class AdvancedSignalGenerator:
    """
    Advanced Signal Generator

    Generates high-quality trading signals by:
    - Combining multiple AI models
    - Analyzing multiple timeframes
    - Incorporating news and sentiment
    - Applying strict filtering
    """

    def __init__(
        self,
        min_confidence: float = 0.6,
        min_risk_reward: float = 1.5,
        max_correlation: float = 0.8,
        signal_expiry_minutes: int = 30
    ):
        self.min_confidence = min_confidence
        self.min_risk_reward = min_risk_reward
        self.max_correlation = max_correlation
        self.signal_expiry_minutes = signal_expiry_minutes

        # Model weights (dynamically adjusted)
        self.model_weights = {
            "lstm": 0.20,
            "transformer": 0.20,
            "pattern": 0.15,
            "rl": 0.15,
            "sentiment": 0.10,
            "technical": 0.10,
            "llm": 0.10
        }

        # Signal history for filtering
        self.recent_signals: List[TradingSignal] = []
        self.signal_stats: Dict[str, Dict] = {}

        logger.info("AdvancedSignalGenerator initialized")

    async def generate_signal(
        self,
        symbol: str,
        price_data: Dict[str, Any],  # Timeframe -> DataFrame
        predictions: Dict[str, Any],  # Model -> prediction
        pattern_analysis: Optional[Dict] = None,
        sentiment_data: Optional[Dict] = None,
        news_data: Optional[List[Dict]] = None,
        current_price: float = 0,
        account_balance: float = 10000
    ) -> Optional[TradingSignal]:
        """Generate a complete trading signal"""

        # Multi-timeframe analysis
        mtf_analysis = self._analyze_timeframes(symbol, price_data)

        # Aggregate model predictions
        aggregated = self._aggregate_predictions(
            predictions,
            pattern_analysis,
            sentiment_data
        )

        direction = aggregated["direction"]
        confidence = aggregated["confidence"]

        # Check minimum confidence
        if confidence < self.min_confidence:
            logger.info(f"Signal rejected: confidence {confidence:.2f} < {self.min_confidence}")
            return None

        # Check trend alignment
        if mtf_analysis.trend_alignment < 0.5:
            # Reduce confidence for misaligned trends
            confidence *= 0.8
            logger.info(f"Reduced confidence due to trend misalignment")

        # Calculate stop loss and take profit
        sl, tp = self._calculate_levels(
            direction,
            current_price,
            price_data,
            mtf_analysis
        )

        # Calculate risk-reward
        if direction == "BUY":
            risk = current_price - sl
            reward = tp - current_price
        elif direction == "SELL":
            risk = sl - current_price
            reward = current_price - tp
        else:
            return None

        if risk <= 0:
            return None

        risk_reward = reward / risk

        # Check minimum risk-reward
        if risk_reward < self.min_risk_reward:
            logger.info(f"Signal rejected: R:R {risk_reward:.2f} < {self.min_risk_reward}")
            return None

        # Calculate position size
        position_size = self._calculate_position_size(
            confidence,
            risk_reward,
            account_balance,
            current_price,
            sl
        )

        # Determine signal type
        signal_type = self._determine_signal_type(direction, confidence, risk_reward)

        # Determine time horizon
        time_horizon = self._determine_time_horizon(price_data, mtf_analysis)

        # Generate reasoning
        reasoning = self._generate_reasoning(
            direction,
            aggregated,
            mtf_analysis,
            pattern_analysis,
            sentiment_data,
            news_data
        )

        # Check for duplicate/correlated signals
        if self._is_duplicate_signal(symbol, direction):
            logger.info("Signal rejected: duplicate signal")
            return None

        signal = TradingSignal(
            symbol=symbol,
            signal_type=signal_type,
            direction=direction,
            confidence=confidence,
            strength=aggregated["strength"],
            entry_price=current_price,
            stop_loss=sl,
            take_profit=tp,
            risk_reward=risk_reward,
            position_size_pct=position_size,
            time_horizon=time_horizon,
            expiry=datetime.now() + timedelta(minutes=self.signal_expiry_minutes),
            sources=aggregated["sources"],
            reasoning=reasoning,
            metadata={
                "mtf_alignment": mtf_analysis.trend_alignment,
                "dominant_trend": mtf_analysis.dominant_trend,
                "key_levels": mtf_analysis.key_levels[:5]
            },
            timestamp=datetime.now()
        )

        # Store signal
        self.recent_signals.append(signal)
        self._update_stats(signal)

        return signal

    def _analyze_timeframes(
        self,
        symbol: str,
        price_data: Dict[str, Any]
    ) -> MultiTimeframeAnalysis:
        """Analyze multiple timeframes"""
        timeframes = {}
        trends = []

        for tf, df in price_data.items():
            if df is None or df.empty or len(df) < 20:
                continue

            close = df['close'].values

            # Simple trend detection
            sma20 = np.mean(close[-20:])
            sma50 = np.mean(close[-50:]) if len(close) >= 50 else sma20
            current = close[-1]

            if current > sma20 > sma50:
                trend = "bullish"
                trend_score = 1
            elif current < sma20 < sma50:
                trend = "bearish"
                trend_score = -1
            else:
                trend = "neutral"
                trend_score = 0

            # Momentum
            momentum = (close[-1] / close[-10] - 1) if len(close) >= 10 else 0

            # Volatility
            returns = np.diff(close) / close[:-1]
            volatility = np.std(returns) if len(returns) > 0 else 0

            timeframes[tf] = {
                "trend": trend,
                "trend_score": trend_score,
                "momentum": momentum,
                "volatility": volatility,
                "current": current,
                "sma20": sma20
            }

            trends.append(trend_score)

        # Calculate trend alignment
        if trends:
            avg_trend = np.mean(trends)
            if avg_trend > 0.5:
                dominant = "bullish"
            elif avg_trend < -0.5:
                dominant = "bearish"
            else:
                dominant = "neutral"

            # Alignment is how much trends agree
            alignment = 1 - np.std(trends) / 2 if len(trends) > 1 else 0.5
        else:
            dominant = "neutral"
            alignment = 0.5

        # Find key levels
        key_levels = self._find_key_levels(price_data)

        return MultiTimeframeAnalysis(
            symbol=symbol,
            timeframes=timeframes,
            dominant_trend=dominant,
            trend_alignment=alignment,
            key_levels=key_levels,
            timestamp=datetime.now()
        )

    def _find_key_levels(self, price_data: Dict[str, Any]) -> List[float]:
        """Find key support/resistance levels"""
        levels = []

        for tf, df in price_data.items():
            if df is None or df.empty:
                continue

            high = df['high'].values
            low = df['low'].values

            # Find swing highs and lows
            for i in range(2, len(high) - 2):
                if high[i] > max(high[i-2:i]) and high[i] > max(high[i+1:i+3]):
                    levels.append(high[i])
                if low[i] < min(low[i-2:i]) and low[i] < min(low[i+1:i+3]):
                    levels.append(low[i])

        # Cluster levels
        if levels:
            levels = sorted(set(levels))

        return levels

    def _aggregate_predictions(
        self,
        predictions: Dict[str, Any],
        pattern_analysis: Optional[Dict],
        sentiment_data: Optional[Dict]
    ) -> Dict[str, Any]:
        """Aggregate predictions from all sources"""
        buy_score = 0
        sell_score = 0
        total_weight = 0
        sources = {}

        # Process model predictions
        for model, pred in predictions.items():
            if pred is None:
                continue

            weight = self.model_weights.get(model, 0.1)
            direction = pred.get("direction", pred.get("predicted_direction", "NEUTRAL")).upper()
            conf = pred.get("confidence", 0.5)

            if direction in ["UP", "BUY", "LONG"]:
                buy_score += conf * weight
            elif direction in ["DOWN", "SELL", "SHORT"]:
                sell_score += conf * weight

            sources[model] = {"direction": direction, "confidence": conf}
            total_weight += weight

        # Add pattern analysis
        if pattern_analysis:
            weight = self.model_weights.get("pattern", 0.15)
            signal = pattern_analysis.get("overall_signal", "NEUTRAL")
            conf = pattern_analysis.get("overall_confidence", 0.5)

            if signal == "BUY":
                buy_score += conf * weight
            elif signal == "SELL":
                sell_score += conf * weight

            sources["pattern"] = {"direction": signal, "confidence": conf}
            total_weight += weight

        # Add sentiment
        if sentiment_data:
            weight = self.model_weights.get("sentiment", 0.1)
            score = sentiment_data.get("sentiment_score", 0)

            if score > 0.3:
                buy_score += abs(score) * weight
                sources["sentiment"] = {"direction": "BUY", "confidence": abs(score)}
            elif score < -0.3:
                sell_score += abs(score) * weight
                sources["sentiment"] = {"direction": "SELL", "confidence": abs(score)}

            total_weight += weight

        # Normalize
        if total_weight > 0:
            buy_score /= total_weight
            sell_score /= total_weight

        # Determine direction
        if buy_score > sell_score and buy_score > 0.3:
            direction = "BUY"
            confidence = buy_score
        elif sell_score > buy_score and sell_score > 0.3:
            direction = "SELL"
            confidence = sell_score
        else:
            direction = "NEUTRAL"
            confidence = 0.5

        # Calculate strength
        strength = abs(buy_score - sell_score)

        return {
            "direction": direction,
            "confidence": confidence,
            "strength": strength,
            "buy_score": buy_score,
            "sell_score": sell_score,
            "sources": sources
        }

    def _calculate_levels(
        self,
        direction: str,
        current_price: float,
        price_data: Dict[str, Any],
        mtf: MultiTimeframeAnalysis
    ) -> Tuple[float, float]:
        """Calculate stop loss and take profit levels"""
        # Use ATR for volatility-based levels
        atr = current_price * 0.01  # Default 1%

        for tf, df in price_data.items():
            if df is not None and not df.empty and len(df) >= 14:
                high = df['high'].values
                low = df['low'].values
                close = df['close'].values

                tr = np.maximum(high - low,
                               np.maximum(np.abs(high - np.roll(close, 1)),
                                         np.abs(low - np.roll(close, 1))))
                atr = np.mean(tr[-14:])
                break

        # Find nearby key levels
        nearby_support = None
        nearby_resistance = None

        for level in mtf.key_levels:
            if level < current_price and (nearby_support is None or level > nearby_support):
                nearby_support = level
            if level > current_price and (nearby_resistance is None or level < nearby_resistance):
                nearby_resistance = level

        if direction == "BUY":
            # Stop loss below support or ATR-based
            if nearby_support and current_price - nearby_support < atr * 2:
                sl = nearby_support - atr * 0.5
            else:
                sl = current_price - atr * 1.5

            # Take profit at resistance or ATR-based
            if nearby_resistance and nearby_resistance - current_price < atr * 3:
                tp = nearby_resistance - atr * 0.2
            else:
                tp = current_price + atr * 2.5

        else:  # SELL
            # Stop loss above resistance
            if nearby_resistance and nearby_resistance - current_price < atr * 2:
                sl = nearby_resistance + atr * 0.5
            else:
                sl = current_price + atr * 1.5

            # Take profit at support
            if nearby_support and current_price - nearby_support < atr * 3:
                tp = nearby_support + atr * 0.2
            else:
                tp = current_price - atr * 2.5

        return sl, tp

    def _calculate_position_size(
        self,
        confidence: float,
        risk_reward: float,
        account_balance: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Calculate position size as percentage of account"""
        # Base risk: 2%
        base_risk = 0.02

        # Adjust for confidence
        risk_adjusted = base_risk * confidence

        # Adjust for risk-reward
        if risk_reward >= 3:
            risk_adjusted *= 1.2
        elif risk_reward < 1.5:
            risk_adjusted *= 0.8

        # Cap at 5%
        return min(0.05, max(0.005, risk_adjusted))

    def _determine_signal_type(
        self,
        direction: str,
        confidence: float,
        risk_reward: float
    ) -> SignalType:
        """Determine signal type based on strength"""
        if direction == "NEUTRAL":
            return SignalType.NEUTRAL

        # Strong signals
        if confidence >= 0.8 and risk_reward >= 2.5:
            return SignalType.STRONG_BUY if direction == "BUY" else SignalType.STRONG_SELL

        # Regular signals
        if confidence >= 0.65:
            return SignalType.BUY if direction == "BUY" else SignalType.SELL

        # Weak signals
        return SignalType.WEAK_BUY if direction == "BUY" else SignalType.WEAK_SELL

    def _determine_time_horizon(
        self,
        price_data: Dict[str, Any],
        mtf: MultiTimeframeAnalysis
    ) -> TimeHorizon:
        """Determine recommended time horizon"""
        # Based on which timeframes show strongest signals
        aligned_tfs = []

        for tf, data in mtf.timeframes.items():
            if data["trend"] != "neutral":
                aligned_tfs.append(tf)

        # Map timeframes to horizons
        if "H4" in aligned_tfs or "D1" in aligned_tfs:
            return TimeHorizon.SWING
        elif "H1" in aligned_tfs:
            return TimeHorizon.INTRADAY
        else:
            return TimeHorizon.SCALP

    def _generate_reasoning(
        self,
        direction: str,
        aggregated: Dict,
        mtf: MultiTimeframeAnalysis,
        pattern_analysis: Optional[Dict],
        sentiment_data: Optional[Dict],
        news_data: Optional[List[Dict]]
    ) -> str:
        """Generate human-readable reasoning"""
        parts = []

        # Direction reasoning
        parts.append(f"{direction} signal generated with {aggregated['confidence']:.0%} confidence.")

        # Model consensus
        buy_sources = [s for s, d in aggregated['sources'].items() if d['direction'] in ['BUY', 'UP']]
        sell_sources = [s for s, d in aggregated['sources'].items() if d['direction'] in ['SELL', 'DOWN']]

        if buy_sources:
            parts.append(f"Bullish signals from: {', '.join(buy_sources)}.")
        if sell_sources:
            parts.append(f"Bearish signals from: {', '.join(sell_sources)}.")

        # Trend alignment
        parts.append(f"Multi-timeframe trend: {mtf.dominant_trend} ({mtf.trend_alignment:.0%} alignment).")

        # Patterns
        if pattern_analysis:
            count = pattern_analysis.get('pattern_count', 0)
            if count > 0:
                parts.append(f"Detected {count} chart patterns.")

        # Sentiment
        if sentiment_data:
            sent = sentiment_data.get('overall_sentiment', 'neutral')
            parts.append(f"Market sentiment: {sent}.")

        # News
        if news_data:
            high_impact = [n for n in news_data if n.get('importance') == 'high']
            if high_impact:
                parts.append(f"Note: {len(high_impact)} high-impact news events.")

        return " ".join(parts)

    def _is_duplicate_signal(self, symbol: str, direction: str) -> bool:
        """Check if this is a duplicate of recent signal"""
        cutoff = datetime.now() - timedelta(minutes=10)

        for signal in self.recent_signals[-10:]:
            if (signal.symbol == symbol and
                signal.direction == direction and
                signal.timestamp > cutoff):
                return True

        return False

    def _update_stats(self, signal: TradingSignal):
        """Update signal statistics"""
        key = f"{signal.symbol}_{signal.direction}"
        if key not in self.signal_stats:
            self.signal_stats[key] = {
                "count": 0,
                "avg_confidence": 0,
                "avg_rr": 0
            }

        stats = self.signal_stats[key]
        n = stats["count"]
        stats["count"] += 1
        stats["avg_confidence"] = (stats["avg_confidence"] * n + signal.confidence) / (n + 1)
        stats["avg_rr"] = (stats["avg_rr"] * n + signal.risk_reward) / (n + 1)

    def update_weights(self, model_performance: Dict[str, float]):
        """Update model weights based on performance"""
        total = sum(model_performance.values())
        if total > 0:
            for model, perf in model_performance.items():
                if model in self.model_weights:
                    # Blend with existing weight
                    new_weight = perf / total
                    self.model_weights[model] = (
                        self.model_weights[model] * 0.7 + new_weight * 0.3
                    )

        # Normalize
        total_weight = sum(self.model_weights.values())
        for model in self.model_weights:
            self.model_weights[model] /= total_weight

        logger.info(f"Updated model weights: {self.model_weights}")

    def get_active_signals(self) -> List[TradingSignal]:
        """Get currently active (non-expired) signals"""
        now = datetime.now()
        return [s for s in self.recent_signals if s.expiry > now]

    def get_stats(self) -> Dict[str, Any]:
        """Get signal generator statistics"""
        return {
            "total_signals": len(self.recent_signals),
            "active_signals": len(self.get_active_signals()),
            "model_weights": self.model_weights,
            "signal_stats": self.signal_stats
        }
