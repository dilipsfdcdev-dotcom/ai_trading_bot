"""
Decision Engine

Final decision maker that combines all signals and applies risk management
before executing trades.

Features:
- Multi-signal aggregation
- Risk-aware position sizing
- Trade validation
- Execution management
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    VERY_STRONG = 5
    STRONG = 4
    MODERATE = 3
    WEAK = 2
    VERY_WEAK = 1


class RiskLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    EXTREME = 4


@dataclass
class TradeSignal:
    """Aggregated trade signal"""
    symbol: str
    direction: str  # BUY, SELL, NEUTRAL
    strength: SignalStrength
    confidence: float
    sources: Dict[str, float]  # source -> confidence
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    risk_level: RiskLevel
    timestamp: datetime


@dataclass
class TradeOrder:
    """Trade order to be executed"""
    order_id: str
    symbol: str
    order_type: str  # MARKET, LIMIT
    direction: str  # BUY, SELL
    volume: float
    entry_price: Optional[float]
    stop_loss: float
    take_profit: float
    max_slippage: float
    expire_time: Optional[datetime]
    metadata: Dict[str, Any]


class DecisionEngine:
    """
    Decision Engine

    The final arbiter of trading decisions that:
    - Aggregates signals from all sources
    - Applies risk management rules
    - Validates trades against constraints
    - Generates executable orders
    """

    def __init__(
        self,
        max_daily_trades: int = 10,
        max_concurrent_positions: int = 3,
        min_confidence_threshold: float = 0.6,
        risk_per_trade: float = 0.02,
        max_daily_loss: float = 0.05,
        min_risk_reward: float = 1.5,
        max_spread_pct: float = 0.001,
        trading_hours: Optional[Tuple[int, int]] = None
    ):
        self.max_daily_trades = max_daily_trades
        self.max_concurrent_positions = max_concurrent_positions
        self.min_confidence_threshold = min_confidence_threshold
        self.risk_per_trade = risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.min_risk_reward = min_risk_reward
        self.max_spread_pct = max_spread_pct
        self.trading_hours = trading_hours  # (start_hour, end_hour) in UTC

        # State tracking
        self.daily_trades: int = 0
        self.daily_pnl: float = 0
        self.current_positions: Dict[str, Dict] = {}
        self.pending_orders: Dict[str, TradeOrder] = {}
        self.trade_history: List[Dict] = []
        self.last_reset_date: Optional[datetime] = None

        # Signal weights by source
        self.signal_weights = {
            "lstm": 0.2,
            "transformer": 0.2,
            "pattern": 0.15,
            "sentiment": 0.15,
            "rl": 0.15,
            "technical": 0.1,
            "llm": 0.05
        }

        logger.info("DecisionEngine initialized")

    def _reset_daily_counters(self):
        """Reset daily trading counters"""
        today = datetime.now().date()
        if self.last_reset_date != today:
            self.daily_trades = 0
            self.daily_pnl = 0
            self.last_reset_date = today
            logger.info("Daily counters reset")

    def _is_trading_allowed(self) -> Tuple[bool, str]:
        """Check if trading is currently allowed"""
        self._reset_daily_counters()

        # Check daily trade limit
        if self.daily_trades >= self.max_daily_trades:
            return False, "Daily trade limit reached"

        # Check daily loss limit
        if self.daily_pnl <= -self.max_daily_loss:
            return False, "Daily loss limit reached"

        # Check concurrent positions
        if len(self.current_positions) >= self.max_concurrent_positions:
            return False, "Maximum concurrent positions reached"

        # Check trading hours
        if self.trading_hours:
            current_hour = datetime.utcnow().hour
            start, end = self.trading_hours
            if not (start <= current_hour < end):
                return False, "Outside trading hours"

        return True, "Trading allowed"

    def aggregate_signals(
        self,
        signals: Dict[str, Dict[str, Any]],
        current_price: float,
        symbol: str
    ) -> TradeSignal:
        """Aggregate signals from multiple sources"""
        buy_score = 0
        sell_score = 0
        total_weight = 0
        sources = {}

        for source, signal in signals.items():
            weight = self.signal_weights.get(source, 0.1)
            confidence = signal.get('confidence', 0.5)
            direction = signal.get('direction', signal.get('signal', 'NEUTRAL')).upper()

            if direction in ['BUY', 'LONG', 'UP']:
                buy_score += confidence * weight
            elif direction in ['SELL', 'SHORT', 'DOWN']:
                sell_score += confidence * weight

            total_weight += weight
            sources[source] = confidence

        # Normalize scores
        if total_weight > 0:
            buy_score /= total_weight
            sell_score /= total_weight

        # Determine direction and confidence
        if buy_score > sell_score and buy_score > 0.3:
            direction = "BUY"
            confidence = buy_score
        elif sell_score > buy_score and sell_score > 0.3:
            direction = "SELL"
            confidence = sell_score
        else:
            direction = "NEUTRAL"
            confidence = 0.5

        # Determine signal strength
        if confidence >= 0.8:
            strength = SignalStrength.VERY_STRONG
        elif confidence >= 0.7:
            strength = SignalStrength.STRONG
        elif confidence >= 0.6:
            strength = SignalStrength.MODERATE
        elif confidence >= 0.5:
            strength = SignalStrength.WEAK
        else:
            strength = SignalStrength.VERY_WEAK

        # Get stop loss and take profit from signals
        sl = None
        tp = None
        for source, signal in signals.items():
            if 'stop_loss' in signal and sl is None:
                sl = signal['stop_loss']
            if 'take_profit' in signal and tp is None:
                tp = signal['take_profit']

        # Default SL/TP based on ATR or percentage
        atr = signals.get('technical', {}).get('atr', current_price * 0.01)
        if sl is None:
            if direction == "BUY":
                sl = current_price - atr * 1.5
            else:
                sl = current_price + atr * 1.5

        if tp is None:
            if direction == "BUY":
                tp = current_price + atr * 2.5
            else:
                tp = current_price - atr * 2.5

        # Calculate risk-reward
        if direction == "BUY":
            risk = current_price - sl
            reward = tp - current_price
        else:
            risk = sl - current_price
            reward = current_price - tp

        risk_reward = reward / risk if risk > 0 else 0

        # Determine risk level
        if risk_reward >= 3:
            risk_level = RiskLevel.LOW
        elif risk_reward >= 2:
            risk_level = RiskLevel.MEDIUM
        elif risk_reward >= 1:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.EXTREME

        return TradeSignal(
            symbol=symbol,
            direction=direction,
            strength=strength,
            confidence=confidence,
            sources=sources,
            entry_price=current_price,
            stop_loss=sl,
            take_profit=tp,
            risk_reward=risk_reward,
            risk_level=risk_level,
            timestamp=datetime.now()
        )

    def validate_trade(
        self,
        signal: TradeSignal,
        account_balance: float,
        current_spread: float
    ) -> Tuple[bool, str]:
        """Validate if trade should be taken"""
        # Check trading allowed
        allowed, reason = self._is_trading_allowed()
        if not allowed:
            return False, reason

        # Check signal strength
        if signal.direction == "NEUTRAL":
            return False, "No clear direction signal"

        if signal.confidence < self.min_confidence_threshold:
            return False, f"Confidence {signal.confidence:.2f} below threshold {self.min_confidence_threshold}"

        # Check risk-reward
        if signal.risk_reward < self.min_risk_reward:
            return False, f"Risk-reward {signal.risk_reward:.2f} below minimum {self.min_risk_reward}"

        # Check spread
        spread_pct = current_spread / signal.entry_price
        if spread_pct > self.max_spread_pct:
            return False, f"Spread {spread_pct:.4f} exceeds maximum {self.max_spread_pct}"

        # Check for existing position in same symbol
        if signal.symbol in self.current_positions:
            existing = self.current_positions[signal.symbol]
            if existing['direction'] == signal.direction:
                return False, "Already have position in same direction"

        # Check risk level
        if signal.risk_level == RiskLevel.EXTREME:
            return False, "Risk level too extreme"

        return True, "Trade validated"

    def calculate_position_size(
        self,
        signal: TradeSignal,
        account_balance: float,
        leverage: float = 100
    ) -> float:
        """Calculate position size based on risk management"""
        # Risk amount
        risk_amount = account_balance * self.risk_per_trade

        # Adjust for confidence
        risk_amount *= signal.confidence

        # Price risk
        price_risk = abs(signal.entry_price - signal.stop_loss)
        if price_risk == 0:
            price_risk = signal.entry_price * 0.01

        # Position value
        position_value = risk_amount / (price_risk / signal.entry_price)

        # Apply leverage
        position_volume = position_value / signal.entry_price

        # Cap at reasonable limits
        max_position = account_balance * 0.1 * leverage / signal.entry_price
        position_volume = min(position_volume, max_position)

        # Round to standard lot sizes
        if signal.symbol.startswith("XAU"):
            position_volume = round(position_volume, 2)  # 0.01 lot minimum
        else:
            position_volume = round(position_volume, 2)

        return max(0.01, position_volume)

    def generate_order(
        self,
        signal: TradeSignal,
        volume: float,
        order_type: str = "MARKET"
    ) -> TradeOrder:
        """Generate a trade order from validated signal"""
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        return TradeOrder(
            order_id=order_id,
            symbol=signal.symbol,
            order_type=order_type,
            direction=signal.direction,
            volume=volume,
            entry_price=signal.entry_price if order_type == "LIMIT" else None,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            max_slippage=signal.entry_price * 0.001,  # 0.1% max slippage
            expire_time=datetime.now() + timedelta(minutes=5) if order_type == "LIMIT" else None,
            metadata={
                "confidence": signal.confidence,
                "strength": signal.strength.name,
                "risk_reward": signal.risk_reward,
                "sources": signal.sources,
                "generated_at": datetime.now().isoformat()
            }
        )

    async def make_decision(
        self,
        signals: Dict[str, Dict[str, Any]],
        current_price: float,
        symbol: str,
        account_balance: float,
        current_spread: float = 0
    ) -> Optional[TradeOrder]:
        """Make final trading decision"""
        # Aggregate signals
        signal = self.aggregate_signals(signals, current_price, symbol)

        logger.info(
            f"Aggregated signal: {signal.direction} "
            f"(confidence: {signal.confidence:.2f}, strength: {signal.strength.name})"
        )

        # Validate trade
        is_valid, reason = self.validate_trade(signal, account_balance, current_spread)

        if not is_valid:
            logger.info(f"Trade rejected: {reason}")
            return None

        # Calculate position size
        volume = self.calculate_position_size(signal, account_balance)

        # Generate order
        order = self.generate_order(signal, volume)

        logger.info(
            f"Order generated: {order.order_id} "
            f"{order.direction} {order.volume} {order.symbol}"
        )

        # Store pending order
        self.pending_orders[order.order_id] = order

        return order

    def record_trade_open(
        self,
        order_id: str,
        symbol: str,
        direction: str,
        volume: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ):
        """Record opened trade"""
        self.daily_trades += 1
        self.current_positions[symbol] = {
            "order_id": order_id,
            "direction": direction,
            "volume": volume,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "opened_at": datetime.now()
        }

        if order_id in self.pending_orders:
            del self.pending_orders[order_id]

        logger.info(f"Trade opened: {symbol} {direction} @ {entry_price}")

    def record_trade_close(
        self,
        symbol: str,
        exit_price: float,
        profit_loss: float
    ):
        """Record closed trade"""
        if symbol in self.current_positions:
            position = self.current_positions[symbol]

            self.trade_history.append({
                **position,
                "exit_price": exit_price,
                "profit_loss": profit_loss,
                "closed_at": datetime.now()
            })

            self.daily_pnl += profit_loss
            del self.current_positions[symbol]

            logger.info(f"Trade closed: {symbol} @ {exit_price}, PnL: {profit_loss:.2f}")

    def get_status(self) -> Dict[str, Any]:
        """Get decision engine status"""
        return {
            "trading_allowed": self._is_trading_allowed()[0],
            "daily_trades": self.daily_trades,
            "max_daily_trades": self.max_daily_trades,
            "daily_pnl": self.daily_pnl,
            "current_positions": len(self.current_positions),
            "max_positions": self.max_concurrent_positions,
            "pending_orders": len(self.pending_orders),
            "min_confidence": self.min_confidence_threshold,
            "risk_per_trade": self.risk_per_trade,
            "positions": self.current_positions
        }

    def adjust_thresholds(
        self,
        winning_streak: int = 0,
        losing_streak: int = 0
    ):
        """Dynamically adjust thresholds based on performance"""
        # Increase confidence threshold after losing streak
        if losing_streak >= 3:
            self.min_confidence_threshold = min(0.8, self.min_confidence_threshold + 0.05)
            self.risk_per_trade = max(0.005, self.risk_per_trade * 0.8)
            logger.info(f"Tightened thresholds after {losing_streak} losses")

        # Relax slightly after winning streak
        elif winning_streak >= 5:
            self.min_confidence_threshold = max(0.5, self.min_confidence_threshold - 0.02)
            self.risk_per_trade = min(0.03, self.risk_per_trade * 1.1)
            logger.info(f"Relaxed thresholds after {winning_streak} wins")
