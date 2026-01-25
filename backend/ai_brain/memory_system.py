"""
Trading Memory System

Long-term and short-term memory for the trading AI:
- Trade history and outcomes
- Pattern memory
- Market regime memory
- Performance tracking
- Learning from past decisions
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json
import os
import pickle
import hashlib

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class TradeMemory:
    """Memory of a single trade"""
    trade_id: str
    symbol: str
    action: str
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime]
    exit_price: Optional[float]
    profit_loss: Optional[float]
    profit_loss_pct: Optional[float]
    market_regime: str
    confidence: float
    reasoning: str
    technical_state: Dict[str, float]
    sentiment_state: Dict[str, float]
    pattern_detected: List[str]
    outcome: str  # win, loss, breakeven, open

    def to_dict(self) -> Dict:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "action": self.action,
            "entry_time": self.entry_time.isoformat(),
            "entry_price": self.entry_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_price": self.exit_price,
            "profit_loss": self.profit_loss,
            "profit_loss_pct": self.profit_loss_pct,
            "market_regime": self.market_regime,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "technical_state": self.technical_state,
            "sentiment_state": self.sentiment_state,
            "pattern_detected": self.pattern_detected,
            "outcome": self.outcome
        }


@dataclass
class PatternMemory:
    """Memory of pattern occurrences and outcomes"""
    pattern_type: str
    occurrences: int
    success_rate: float
    avg_profit_when_success: float
    avg_loss_when_failure: float
    best_market_regime: str
    avg_confidence_when_detected: float


@dataclass
class PerformanceMetrics:
    """Performance tracking metrics"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_profit: float = 0
    total_loss: float = 0
    max_drawdown: float = 0
    current_drawdown: float = 0
    peak_balance: float = 0
    sharpe_ratio: float = 0
    win_rate: float = 0
    profit_factor: float = 0
    avg_win: float = 0
    avg_loss: float = 0
    expectancy: float = 0
    best_trade: float = 0
    worst_trade: float = 0
    consecutive_wins: int = 0
    consecutive_losses: int = 0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0

    def to_dict(self) -> Dict:
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "total_profit": self.total_profit,
            "total_loss": self.total_loss,
            "max_drawdown": self.max_drawdown,
            "current_drawdown": self.current_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "expectancy": self.expectancy,
            "best_trade": self.best_trade,
            "worst_trade": self.worst_trade,
            "max_consecutive_wins": self.max_consecutive_wins,
            "max_consecutive_losses": self.max_consecutive_losses
        }


class TradingMemory:
    """
    Trading Memory System

    Provides:
    - Short-term memory (recent trades and decisions)
    - Long-term memory (persistent trade history)
    - Pattern memory (pattern success rates)
    - Performance tracking
    - Learning from past outcomes
    """

    def __init__(
        self,
        memory_dir: str = "./memory",
        short_term_size: int = 100,
        auto_save_interval: int = 300  # seconds
    ):
        self.memory_dir = memory_dir
        self.short_term_size = short_term_size
        self.auto_save_interval = auto_save_interval

        # Memory stores
        self.short_term: deque = deque(maxlen=short_term_size)
        self.long_term: List[TradeMemory] = []
        self.pattern_memory: Dict[str, PatternMemory] = {}
        self.regime_memory: Dict[str, Dict] = {}
        self.performance = PerformanceMetrics()

        # State
        self.daily_returns: List[float] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self._last_save_time = datetime.now()

        os.makedirs(memory_dir, exist_ok=True)

        # Load existing memory
        self._load_memory()

        logger.info("TradingMemory initialized")

    def _load_memory(self):
        """Load memory from disk"""
        try:
            # Load long-term memory
            lt_path = os.path.join(self.memory_dir, "long_term_memory.json")
            if os.path.exists(lt_path):
                with open(lt_path, 'r') as f:
                    data = json.load(f)
                    for trade_data in data:
                        trade = TradeMemory(
                            trade_id=trade_data['trade_id'],
                            symbol=trade_data['symbol'],
                            action=trade_data['action'],
                            entry_time=datetime.fromisoformat(trade_data['entry_time']),
                            entry_price=trade_data['entry_price'],
                            exit_time=datetime.fromisoformat(trade_data['exit_time']) if trade_data['exit_time'] else None,
                            exit_price=trade_data['exit_price'],
                            profit_loss=trade_data['profit_loss'],
                            profit_loss_pct=trade_data['profit_loss_pct'],
                            market_regime=trade_data['market_regime'],
                            confidence=trade_data['confidence'],
                            reasoning=trade_data['reasoning'],
                            technical_state=trade_data['technical_state'],
                            sentiment_state=trade_data['sentiment_state'],
                            pattern_detected=trade_data['pattern_detected'],
                            outcome=trade_data['outcome']
                        )
                        self.long_term.append(trade)

            # Load pattern memory
            pm_path = os.path.join(self.memory_dir, "pattern_memory.json")
            if os.path.exists(pm_path):
                with open(pm_path, 'r') as f:
                    data = json.load(f)
                    for pattern_type, pm_data in data.items():
                        self.pattern_memory[pattern_type] = PatternMemory(**pm_data)

            # Load performance metrics
            perf_path = os.path.join(self.memory_dir, "performance.json")
            if os.path.exists(perf_path):
                with open(perf_path, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self.performance, key):
                            setattr(self.performance, key, value)

            logger.info(f"Loaded {len(self.long_term)} trades from memory")

        except Exception as e:
            logger.error(f"Error loading memory: {e}")

    def _save_memory(self):
        """Save memory to disk"""
        try:
            # Save long-term memory
            lt_path = os.path.join(self.memory_dir, "long_term_memory.json")
            with open(lt_path, 'w') as f:
                json.dump([t.to_dict() for t in self.long_term], f, indent=2)

            # Save pattern memory
            pm_path = os.path.join(self.memory_dir, "pattern_memory.json")
            with open(pm_path, 'w') as f:
                json.dump(
                    {k: v.__dict__ for k, v in self.pattern_memory.items()},
                    f, indent=2
                )

            # Save performance
            perf_path = os.path.join(self.memory_dir, "performance.json")
            with open(perf_path, 'w') as f:
                json.dump(self.performance.to_dict(), f, indent=2)

            self._last_save_time = datetime.now()
            logger.info("Memory saved to disk")

        except Exception as e:
            logger.error(f"Error saving memory: {e}")

    def remember_trade(
        self,
        trade_id: str,
        symbol: str,
        action: str,
        entry_price: float,
        market_regime: str,
        confidence: float,
        reasoning: str,
        technical_state: Dict[str, float],
        sentiment_state: Dict[str, float],
        patterns: List[str]
    ) -> TradeMemory:
        """Remember a new trade entry"""
        trade = TradeMemory(
            trade_id=trade_id,
            symbol=symbol,
            action=action,
            entry_time=datetime.now(),
            entry_price=entry_price,
            exit_time=None,
            exit_price=None,
            profit_loss=None,
            profit_loss_pct=None,
            market_regime=market_regime,
            confidence=confidence,
            reasoning=reasoning,
            technical_state=technical_state,
            sentiment_state=sentiment_state,
            pattern_detected=patterns,
            outcome="open"
        )

        self.short_term.append(trade)
        self.long_term.append(trade)

        # Auto-save if needed
        if (datetime.now() - self._last_save_time).seconds > self.auto_save_interval:
            self._save_memory()

        return trade

    def update_trade_outcome(
        self,
        trade_id: str,
        exit_price: float,
        profit_loss: float
    ):
        """Update trade with exit information"""
        for trade in reversed(self.long_term):
            if trade.trade_id == trade_id:
                trade.exit_time = datetime.now()
                trade.exit_price = exit_price
                trade.profit_loss = profit_loss
                trade.profit_loss_pct = (exit_price - trade.entry_price) / trade.entry_price * 100

                if trade.action == "SELL":
                    trade.profit_loss_pct *= -1

                if profit_loss > 0:
                    trade.outcome = "win"
                    self._update_win(profit_loss)
                elif profit_loss < 0:
                    trade.outcome = "loss"
                    self._update_loss(abs(profit_loss))
                else:
                    trade.outcome = "breakeven"

                # Update pattern memory
                for pattern in trade.pattern_detected:
                    self._update_pattern_memory(
                        pattern,
                        trade.outcome == "win",
                        trade.profit_loss_pct or 0,
                        trade.market_regime,
                        trade.confidence
                    )

                self._save_memory()
                break

    def _update_win(self, profit: float):
        """Update metrics for a winning trade"""
        self.performance.total_trades += 1
        self.performance.winning_trades += 1
        self.performance.total_profit += profit
        self.performance.consecutive_wins += 1
        self.performance.consecutive_losses = 0
        self.performance.max_consecutive_wins = max(
            self.performance.max_consecutive_wins,
            self.performance.consecutive_wins
        )

        if profit > self.performance.best_trade:
            self.performance.best_trade = profit

        self._recalculate_metrics()

    def _update_loss(self, loss: float):
        """Update metrics for a losing trade"""
        self.performance.total_trades += 1
        self.performance.losing_trades += 1
        self.performance.total_loss += loss
        self.performance.consecutive_losses += 1
        self.performance.consecutive_wins = 0
        self.performance.max_consecutive_losses = max(
            self.performance.max_consecutive_losses,
            self.performance.consecutive_losses
        )

        if -loss < self.performance.worst_trade:
            self.performance.worst_trade = -loss

        self._recalculate_metrics()

    def _recalculate_metrics(self):
        """Recalculate performance metrics"""
        if self.performance.total_trades > 0:
            self.performance.win_rate = (
                self.performance.winning_trades / self.performance.total_trades
            )

        if self.performance.winning_trades > 0:
            self.performance.avg_win = (
                self.performance.total_profit / self.performance.winning_trades
            )

        if self.performance.losing_trades > 0:
            self.performance.avg_loss = (
                self.performance.total_loss / self.performance.losing_trades
            )

        if self.performance.total_loss > 0:
            self.performance.profit_factor = (
                self.performance.total_profit / self.performance.total_loss
            )

        # Expectancy
        if self.performance.total_trades > 0:
            self.performance.expectancy = (
                (self.performance.win_rate * self.performance.avg_win) -
                ((1 - self.performance.win_rate) * self.performance.avg_loss)
            )

    def _update_pattern_memory(
        self,
        pattern_type: str,
        was_successful: bool,
        pnl_pct: float,
        market_regime: str,
        confidence: float
    ):
        """Update pattern memory with trade outcome"""
        if pattern_type not in self.pattern_memory:
            self.pattern_memory[pattern_type] = PatternMemory(
                pattern_type=pattern_type,
                occurrences=0,
                success_rate=0.5,
                avg_profit_when_success=0,
                avg_loss_when_failure=0,
                best_market_regime="unknown",
                avg_confidence_when_detected=0
            )

        pm = self.pattern_memory[pattern_type]
        pm.occurrences += 1

        # Update success rate (running average)
        old_rate = pm.success_rate
        pm.success_rate = (old_rate * (pm.occurrences - 1) + (1 if was_successful else 0)) / pm.occurrences

        # Update profit/loss averages
        if was_successful:
            old_avg = pm.avg_profit_when_success
            successful_count = int(pm.success_rate * (pm.occurrences - 1)) + 1
            pm.avg_profit_when_success = (
                old_avg * (successful_count - 1) + pnl_pct
            ) / successful_count
        else:
            old_avg = pm.avg_loss_when_failure
            failed_count = pm.occurrences - int(pm.success_rate * pm.occurrences)
            if failed_count > 0:
                pm.avg_loss_when_failure = (
                    old_avg * (failed_count - 1) + abs(pnl_pct)
                ) / failed_count

        # Update best regime
        if market_regime not in self.regime_memory:
            self.regime_memory[market_regime] = {}
        if pattern_type not in self.regime_memory[market_regime]:
            self.regime_memory[market_regime][pattern_type] = {
                'occurrences': 0, 'successes': 0
            }

        self.regime_memory[market_regime][pattern_type]['occurrences'] += 1
        if was_successful:
            self.regime_memory[market_regime][pattern_type]['successes'] += 1

        # Find best regime for this pattern
        best_regime = None
        best_success_rate = 0
        for regime, patterns in self.regime_memory.items():
            if pattern_type in patterns:
                rate = patterns[pattern_type]['successes'] / patterns[pattern_type]['occurrences']
                if rate > best_success_rate:
                    best_success_rate = rate
                    best_regime = regime

        if best_regime:
            pm.best_market_regime = best_regime

        # Update average confidence
        old_conf = pm.avg_confidence_when_detected
        pm.avg_confidence_when_detected = (
            old_conf * (pm.occurrences - 1) + confidence
        ) / pm.occurrences

    def get_similar_trades(
        self,
        technical_state: Dict[str, float],
        market_regime: str,
        top_k: int = 5
    ) -> List[TradeMemory]:
        """Find similar historical trades"""
        if not NUMPY_AVAILABLE:
            return []

        # Filter by regime
        regime_trades = [t for t in self.long_term if t.market_regime == market_regime]

        if not regime_trades:
            regime_trades = self.long_term

        # Calculate similarity scores
        scored_trades = []
        for trade in regime_trades:
            if trade.outcome == "open":
                continue

            similarity = 0
            count = 0

            for key in technical_state:
                if key in trade.technical_state:
                    diff = abs(technical_state[key] - trade.technical_state[key])
                    similarity += 1 / (1 + diff)
                    count += 1

            if count > 0:
                similarity /= count
                scored_trades.append((trade, similarity))

        # Sort by similarity
        scored_trades.sort(key=lambda x: x[1], reverse=True)

        return [t[0] for t in scored_trades[:top_k]]

    def get_pattern_success_rate(self, pattern_type: str) -> float:
        """Get historical success rate for a pattern"""
        if pattern_type in self.pattern_memory:
            return self.pattern_memory[pattern_type].success_rate
        return 0.5  # Default neutral

    def get_regime_performance(self, market_regime: str) -> Dict[str, Any]:
        """Get performance metrics for a market regime"""
        regime_trades = [t for t in self.long_term if t.market_regime == market_regime]

        if not regime_trades:
            return {"trades": 0, "win_rate": 0, "avg_pnl": 0}

        completed = [t for t in regime_trades if t.outcome != "open"]
        wins = [t for t in completed if t.outcome == "win"]

        return {
            "trades": len(completed),
            "win_rate": len(wins) / len(completed) if completed else 0,
            "avg_pnl": sum(t.profit_loss_pct or 0 for t in completed) / len(completed) if completed else 0,
            "best_patterns": self.regime_memory.get(market_regime, {})
        }

    def get_learning_insights(self) -> Dict[str, Any]:
        """Generate insights from memory for learning"""
        insights = {
            "total_trades_analyzed": len(self.long_term),
            "performance_summary": self.performance.to_dict(),
            "pattern_insights": [],
            "regime_insights": [],
            "recommendations": []
        }

        # Pattern insights
        for pattern_type, pm in self.pattern_memory.items():
            if pm.occurrences >= 5:  # Minimum sample size
                insights["pattern_insights"].append({
                    "pattern": pattern_type,
                    "success_rate": pm.success_rate,
                    "occurrences": pm.occurrences,
                    "best_regime": pm.best_market_regime,
                    "avg_profit": pm.avg_profit_when_success,
                    "avg_loss": pm.avg_loss_when_failure
                })

        # Sort by success rate
        insights["pattern_insights"].sort(
            key=lambda x: x["success_rate"],
            reverse=True
        )

        # Regime insights
        for regime in set(t.market_regime for t in self.long_term):
            perf = self.get_regime_performance(regime)
            if perf["trades"] >= 3:
                insights["regime_insights"].append({
                    "regime": regime,
                    **perf
                })

        # Generate recommendations
        if self.performance.win_rate < 0.4:
            insights["recommendations"].append(
                "Win rate is low. Consider increasing confidence threshold."
            )

        if self.performance.max_consecutive_losses > 5:
            insights["recommendations"].append(
                "Long losing streaks detected. Review risk management."
            )

        if self.performance.profit_factor < 1:
            insights["recommendations"].append(
                "Profit factor below 1. Losses exceed profits."
            )

        # Best patterns to focus on
        good_patterns = [
            p for p in insights["pattern_insights"]
            if p["success_rate"] > 0.6 and p["occurrences"] >= 10
        ]
        if good_patterns:
            insights["recommendations"].append(
                f"Focus on: {', '.join(p['pattern'] for p in good_patterns[:3])}"
            )

        return insights

    def clear_short_term(self):
        """Clear short-term memory"""
        self.short_term.clear()

    def get_recent_decisions(self, count: int = 10) -> List[Dict]:
        """Get recent trading decisions"""
        return [t.to_dict() for t in list(self.short_term)[-count:]]

    def export_memory(self, filepath: str):
        """Export full memory to file"""
        data = {
            "long_term": [t.to_dict() for t in self.long_term],
            "pattern_memory": {k: v.__dict__ for k, v in self.pattern_memory.items()},
            "performance": self.performance.to_dict(),
            "regime_memory": self.regime_memory,
            "export_time": datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Memory exported to {filepath}")
