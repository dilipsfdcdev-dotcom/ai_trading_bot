"""
Autonomous AI Brain

The central intelligence that coordinates all AI models and makes autonomous trading decisions.

Features:
- Multi-model ensemble (LSTM, Transformer, CNN, RL)
- Chain-of-thought reasoning
- Self-reflection and improvement
- Autonomous decision making
- Risk-aware trading
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import os

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ThinkingMode(Enum):
    FAST = "fast"  # Quick decisions for scalping
    BALANCED = "balanced"  # Normal analysis
    DEEP = "deep"  # Extended analysis for major decisions


class MarketRegime(Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"


@dataclass
class ThoughtProcess:
    """A single thought in the chain"""
    step: int
    thought: str
    conclusion: str
    confidence: float
    timestamp: datetime


@dataclass
class TradingDecision:
    """Final trading decision"""
    symbol: str
    action: str  # BUY, SELL, HOLD, CLOSE
    confidence: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    position_size: float
    reasoning: str
    thought_chain: List[ThoughtProcess]
    risk_assessment: str
    market_regime: str
    time_horizon: str
    model_contributions: Dict[str, float]
    timestamp: datetime

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "action": self.action,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "position_size": self.position_size,
            "reasoning": self.reasoning,
            "thought_chain": [
                {
                    "step": t.step,
                    "thought": t.thought,
                    "conclusion": t.conclusion,
                    "confidence": t.confidence
                } for t in self.thought_chain
            ],
            "risk_assessment": self.risk_assessment,
            "market_regime": self.market_regime,
            "time_horizon": self.time_horizon,
            "model_contributions": self.model_contributions,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MarketContext:
    """Current market context for decision making"""
    symbol: str
    current_price: float
    price_data: pd.DataFrame
    technical_indicators: Dict[str, float]
    pattern_analysis: Dict[str, Any]
    sentiment_data: Dict[str, Any]
    news_summary: List[Dict]
    economic_events: List[Dict]
    current_position: Optional[Dict]
    account_balance: float
    timestamp: datetime


class AutonomousAIBrain:
    """
    Autonomous AI Trading Brain

    The central intelligence that:
    - Thinks autonomously about markets
    - Coordinates multiple AI models
    - Makes and executes trading decisions
    - Learns from outcomes
    - Manages risk dynamically
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        thinking_mode: ThinkingMode = ThinkingMode.BALANCED,
        risk_tolerance: float = 0.02,  # 2% per trade
        max_position_size: float = 0.1,  # 10% of account
        model_dir: str = "./models"
    ):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.thinking_mode = thinking_mode
        self.risk_tolerance = risk_tolerance
        self.max_position_size = max_position_size
        self.model_dir = model_dir

        # Initialize LLM clients
        self.openai_client = None
        self.anthropic_client = None
        self.llm_provider = "none"

        if OPENAI_AVAILABLE and self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
            self.llm_provider = "openai"
        if ANTHROPIC_AVAILABLE and self.anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_api_key)
            if not self.openai_client:
                self.llm_provider = "anthropic"

        # Neural network models (initialized later)
        self.price_predictor = None
        self.transformer_predictor = None
        self.pattern_cnn = None
        self.rl_agent = None

        # State
        self.is_thinking = False
        self.current_regime: MarketRegime = MarketRegime.RANGING
        self.decision_history: List[TradingDecision] = []
        self.performance_metrics: Dict[str, float] = {}
        self.model_weights: Dict[str, float] = {
            "lstm": 0.25,
            "transformer": 0.25,
            "pattern": 0.2,
            "sentiment": 0.15,
            "rl": 0.15
        }

        logger.info(f"AutonomousAIBrain initialized with LLM provider: {self.llm_provider}")

    async def initialize_models(self):
        """Initialize all neural network models"""
        try:
            from neural_networks import (
                PricePredictor,
                TransformerPredictor,
                PatternRecognitionCNN,
                TradingRLAgent
            )

            self.price_predictor = PricePredictor(model_dir=self.model_dir)
            self.transformer_predictor = TransformerPredictor(model_dir=self.model_dir)
            self.pattern_cnn = PatternRecognitionCNN(model_dir=self.model_dir)
            self.rl_agent = TradingRLAgent(model_dir=self.model_dir)

            # Try to load pre-trained models
            try:
                self.price_predictor.load_model("best_lstm_model.pt")
            except:
                logger.info("No pre-trained LSTM model found")

            try:
                self.transformer_predictor.load_model("best_transformer_model.pt")
            except:
                logger.info("No pre-trained Transformer model found")

            try:
                self.rl_agent.load_model("rl_agent_dqn.pt")
            except:
                logger.info("No pre-trained RL model found")

            logger.info("Neural network models initialized")

        except ImportError as e:
            logger.warning(f"Could not import neural network models: {e}")

    def _detect_market_regime(
        self,
        df: pd.DataFrame,
        indicators: Dict[str, float]
    ) -> MarketRegime:
        """Detect current market regime"""
        if len(df) < 20:
            return MarketRegime.RANGING

        close = df['close'].values
        returns = np.diff(close) / close[:-1]

        # Trend detection
        sma20 = np.mean(close[-20:])
        sma50 = np.mean(close[-50:]) if len(close) >= 50 else sma20
        current = close[-1]

        # Volatility
        volatility = np.std(returns[-20:])
        avg_volatility = np.std(returns)

        # ADX-like trend strength
        if len(close) >= 20:
            high_range = np.max(close[-20:]) - np.min(close[-20:])
            trend_strength = abs(close[-1] - close[-20]) / high_range if high_range > 0 else 0
        else:
            trend_strength = 0

        # RSI for overbought/oversold
        rsi = indicators.get('rsi', 50)

        # Determine regime
        if volatility > avg_volatility * 1.5:
            return MarketRegime.HIGH_VOLATILITY
        elif volatility < avg_volatility * 0.5:
            return MarketRegime.LOW_VOLATILITY
        elif trend_strength > 0.7 and current > sma20 > sma50:
            return MarketRegime.TRENDING_UP
        elif trend_strength > 0.7 and current < sma20 < sma50:
            return MarketRegime.TRENDING_DOWN
        elif (rsi > 70 and current > sma20) or (rsi < 30 and current < sma20):
            return MarketRegime.REVERSAL
        elif abs(close[-1] - close[-5]) / close[-5] > 0.02:
            return MarketRegime.BREAKOUT
        else:
            return MarketRegime.RANGING

    async def _chain_of_thought(
        self,
        context: MarketContext
    ) -> List[ThoughtProcess]:
        """Generate chain-of-thought reasoning"""
        thoughts = []

        # Thought 1: Market Overview
        thoughts.append(ThoughtProcess(
            step=1,
            thought=f"Analyzing {context.symbol} at price {context.current_price:.2f}",
            conclusion=f"Market regime: {self.current_regime.value}",
            confidence=0.8,
            timestamp=datetime.now()
        ))

        # Thought 2: Technical Analysis
        rsi = context.technical_indicators.get('rsi', 50)
        macd = context.technical_indicators.get('macd', 0)
        bb_pos = context.technical_indicators.get('bb_position', 0.5)

        if rsi > 70:
            tech_conclusion = "Overbought conditions"
        elif rsi < 30:
            tech_conclusion = "Oversold conditions"
        else:
            tech_conclusion = "Neutral RSI"

        thoughts.append(ThoughtProcess(
            step=2,
            thought=f"RSI: {rsi:.1f}, MACD: {macd:.4f}, BB Position: {bb_pos:.2f}",
            conclusion=tech_conclusion,
            confidence=0.75,
            timestamp=datetime.now()
        ))

        # Thought 3: Pattern Analysis
        if context.pattern_analysis:
            pattern_signal = context.pattern_analysis.get('overall_signal', 'NEUTRAL')
            pattern_conf = context.pattern_analysis.get('overall_confidence', 0.5)
            thoughts.append(ThoughtProcess(
                step=3,
                thought=f"Pattern analysis shows {context.pattern_analysis.get('pattern_count', 0)} patterns",
                conclusion=f"Pattern signal: {pattern_signal}",
                confidence=pattern_conf,
                timestamp=datetime.now()
            ))

        # Thought 4: Sentiment Analysis
        if context.sentiment_data:
            sentiment = context.sentiment_data.get('overall_sentiment', 'neutral')
            sentiment_score = context.sentiment_data.get('sentiment_score', 0)
            thoughts.append(ThoughtProcess(
                step=4,
                thought=f"Market sentiment score: {sentiment_score:.2f}",
                conclusion=f"Sentiment: {sentiment}",
                confidence=abs(sentiment_score),
                timestamp=datetime.now()
            ))

        # Thought 5: News Impact
        if context.news_summary:
            high_impact_news = [n for n in context.news_summary if n.get('importance') == 'high']
            thoughts.append(ThoughtProcess(
                step=5,
                thought=f"Found {len(high_impact_news)} high-impact news items",
                conclusion="News may affect volatility" if high_impact_news else "No significant news",
                confidence=0.6 if high_impact_news else 0.8,
                timestamp=datetime.now()
            ))

        # Thought 6: Risk Assessment
        if context.current_position:
            pnl = context.current_position.get('unrealized_pnl', 0)
            thoughts.append(ThoughtProcess(
                step=6,
                thought=f"Current position PnL: {pnl:.2f}",
                conclusion="Manage existing position" if abs(pnl) > 0 else "No position",
                confidence=0.9,
                timestamp=datetime.now()
            ))

        return thoughts

    async def _llm_deep_reasoning(
        self,
        context: MarketContext,
        thoughts: List[ThoughtProcess]
    ) -> Dict[str, Any]:
        """Use LLM for deep market reasoning"""
        if not self.openai_client and not self.anthropic_client:
            return self._fallback_reasoning(context, thoughts)

        thought_summary = "\n".join([
            f"Step {t.step}: {t.thought} -> {t.conclusion} (Conf: {t.confidence:.2f})"
            for t in thoughts
        ])

        prompt = f"""You are an expert autonomous trading AI. Analyze the market and provide a trading decision.

## Current Market Context
- Symbol: {context.symbol}
- Current Price: {context.current_price}
- Account Balance: {context.account_balance}
- Risk Tolerance: {self.risk_tolerance * 100}% per trade

## Technical Indicators
{json.dumps(context.technical_indicators, indent=2)}

## Current Analysis Chain
{thought_summary}

## Pattern Analysis
{json.dumps(context.pattern_analysis, indent=2) if context.pattern_analysis else "No patterns detected"}

## Market Sentiment
{json.dumps(context.sentiment_data, indent=2) if context.sentiment_data else "No sentiment data"}

## Your Task
Provide your trading decision as JSON:
{{
    "action": "BUY" or "SELL" or "HOLD",
    "confidence": <0.0 to 1.0>,
    "entry_price": <suggested entry or null>,
    "stop_loss": <stop loss price>,
    "take_profit": <take profit price>,
    "position_size_pct": <0.01 to 0.1>,
    "reasoning": "<detailed reasoning>",
    "risk_assessment": "<risk analysis>",
    "time_horizon": "scalp" or "intraday" or "swing"
}}

Be conservative and protect capital. Only trade with high confidence."""

        try:
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an autonomous trading AI that makes rational, risk-aware decisions."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )
                result_text = response.choices[0].message.content

            elif self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text

            # Parse response
            result_text = result_text.strip()
            if "```" in result_text:
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            return json.loads(result_text)

        except Exception as e:
            logger.error(f"LLM reasoning error: {e}")
            return self._fallback_reasoning(context, thoughts)

    def _fallback_reasoning(
        self,
        context: MarketContext,
        thoughts: List[ThoughtProcess]
    ) -> Dict[str, Any]:
        """Fallback reasoning without LLM"""
        # Simple rule-based decision
        rsi = context.technical_indicators.get('rsi', 50)
        macd = context.technical_indicators.get('macd', 0)
        momentum = context.technical_indicators.get('momentum_20', 0)

        # Scoring
        buy_score = 0
        sell_score = 0

        if rsi < 30:
            buy_score += 2
        elif rsi > 70:
            sell_score += 2

        if macd > 0:
            buy_score += 1
        elif macd < 0:
            sell_score += 1

        if momentum > 0:
            buy_score += 1
        elif momentum < 0:
            sell_score += 1

        # Pattern analysis
        if context.pattern_analysis:
            if context.pattern_analysis.get('overall_signal') == 'BUY':
                buy_score += 2
            elif context.pattern_analysis.get('overall_signal') == 'SELL':
                sell_score += 2

        # Sentiment
        if context.sentiment_data:
            sentiment_score = context.sentiment_data.get('sentiment_score', 0)
            if sentiment_score > 0.3:
                buy_score += 1
            elif sentiment_score < -0.3:
                sell_score += 1

        # Decision
        if buy_score > sell_score + 2:
            action = "BUY"
            confidence = min(0.8, (buy_score - sell_score) * 0.15)
        elif sell_score > buy_score + 2:
            action = "SELL"
            confidence = min(0.8, (sell_score - buy_score) * 0.15)
        else:
            action = "HOLD"
            confidence = 0.5

        atr = context.technical_indicators.get('atr', context.current_price * 0.01)

        return {
            "action": action,
            "confidence": confidence,
            "entry_price": context.current_price,
            "stop_loss": context.current_price - atr * 1.5 if action == "BUY" else context.current_price + atr * 1.5,
            "take_profit": context.current_price + atr * 2 if action == "BUY" else context.current_price - atr * 2,
            "position_size_pct": self.risk_tolerance * confidence,
            "reasoning": f"Buy score: {buy_score}, Sell score: {sell_score}",
            "risk_assessment": "Standard risk parameters applied",
            "time_horizon": "intraday"
        }

    async def _get_model_predictions(
        self,
        context: MarketContext
    ) -> Dict[str, Any]:
        """Get predictions from all neural network models"""
        predictions = {}

        # LSTM prediction
        if self.price_predictor and self.price_predictor.is_trained:
            try:
                lstm_pred = await self.price_predictor.predict(
                    context.price_data,
                    context.symbol
                )
                predictions['lstm'] = {
                    'predicted_price': lstm_pred.predicted_price,
                    'direction': lstm_pred.predicted_direction,
                    'confidence': lstm_pred.confidence
                }
            except Exception as e:
                logger.error(f"LSTM prediction error: {e}")

        # Transformer prediction
        if self.transformer_predictor and self.transformer_predictor.is_trained:
            try:
                trans_pred = await self.transformer_predictor.predict(
                    context.price_data,
                    context.symbol
                )
                predictions['transformer'] = {
                    'predicted_price': trans_pred.predicted_price,
                    'direction': trans_pred.predicted_direction,
                    'confidence': trans_pred.confidence
                }
            except Exception as e:
                logger.error(f"Transformer prediction error: {e}")

        # RL agent
        if self.rl_agent and self.rl_agent.is_trained:
            try:
                from neural_networks.rl_agent import TradingState
                state = TradingState(
                    prices=context.price_data['close'].values[-20:],
                    position=0 if not context.current_position else (
                        1 if context.current_position.get('type') == 'buy' else -1
                    ),
                    entry_price=context.current_position.get('entry_price', 0) if context.current_position else 0,
                    unrealized_pnl=context.current_position.get('unrealized_pnl', 0) if context.current_position else 0,
                    balance=context.account_balance,
                    indicators=context.technical_indicators
                )
                rl_decision = self.rl_agent.get_trading_decision(state)
                predictions['rl'] = {
                    'signal': rl_decision['signal'],
                    'confidence': rl_decision['confidence']
                }
            except Exception as e:
                logger.error(f"RL prediction error: {e}")

        return predictions

    async def think(
        self,
        context: MarketContext
    ) -> TradingDecision:
        """
        Main thinking process - the brain's decision-making loop

        This is where the AI "thinks" about the market and makes decisions.
        """
        self.is_thinking = True
        logger.info(f"Brain starting to think about {context.symbol}...")

        try:
            # Step 1: Detect market regime
            self.current_regime = self._detect_market_regime(
                context.price_data,
                context.technical_indicators
            )

            # Step 2: Chain of thought reasoning
            thoughts = await self._chain_of_thought(context)

            # Step 3: Get neural network predictions
            model_predictions = await self._get_model_predictions(context)

            # Step 4: Deep reasoning with LLM
            if self.thinking_mode == ThinkingMode.DEEP:
                llm_decision = await self._llm_deep_reasoning(context, thoughts)
            else:
                llm_decision = self._fallback_reasoning(context, thoughts)

            # Step 5: Ensemble the decisions
            final_action, final_confidence = self._ensemble_decisions(
                llm_decision,
                model_predictions,
                context
            )

            # Step 6: Calculate position size based on risk
            position_size = self._calculate_position_size(
                final_confidence,
                context.account_balance,
                context.current_price,
                llm_decision.get('stop_loss', context.current_price * 0.99)
            )

            # Step 7: Create final decision
            decision = TradingDecision(
                symbol=context.symbol,
                action=final_action,
                confidence=final_confidence,
                entry_price=llm_decision.get('entry_price'),
                stop_loss=llm_decision.get('stop_loss'),
                take_profit=llm_decision.get('take_profit'),
                position_size=position_size,
                reasoning=llm_decision.get('reasoning', ''),
                thought_chain=thoughts,
                risk_assessment=llm_decision.get('risk_assessment', ''),
                market_regime=self.current_regime.value,
                time_horizon=llm_decision.get('time_horizon', 'intraday'),
                model_contributions={
                    k: self.model_weights.get(k, 0.1)
                    for k in model_predictions.keys()
                },
                timestamp=datetime.now()
            )

            self.decision_history.append(decision)
            logger.info(f"Brain decision: {final_action} with confidence {final_confidence:.2f}")

            return decision

        finally:
            self.is_thinking = False

    def _ensemble_decisions(
        self,
        llm_decision: Dict,
        model_predictions: Dict,
        context: MarketContext
    ) -> Tuple[str, float]:
        """Combine all model predictions into final decision"""
        votes = {"BUY": 0, "SELL": 0, "HOLD": 0}
        total_weight = 0

        # LLM decision
        llm_action = llm_decision.get('action', 'HOLD').upper()
        llm_confidence = llm_decision.get('confidence', 0.5)
        votes[llm_action] += llm_confidence * 0.3
        total_weight += 0.3

        # LSTM prediction
        if 'lstm' in model_predictions:
            direction = model_predictions['lstm']['direction']
            conf = model_predictions['lstm']['confidence']
            weight = self.model_weights.get('lstm', 0.2)

            if direction == "UP":
                votes["BUY"] += conf * weight
            elif direction == "DOWN":
                votes["SELL"] += conf * weight
            else:
                votes["HOLD"] += conf * weight
            total_weight += weight

        # Transformer prediction
        if 'transformer' in model_predictions:
            direction = model_predictions['transformer']['direction']
            conf = model_predictions['transformer']['confidence']
            weight = self.model_weights.get('transformer', 0.2)

            if direction == "UP":
                votes["BUY"] += conf * weight
            elif direction == "DOWN":
                votes["SELL"] += conf * weight
            else:
                votes["HOLD"] += conf * weight
            total_weight += weight

        # RL agent
        if 'rl' in model_predictions:
            signal = model_predictions['rl']['signal']
            conf = model_predictions['rl']['confidence']
            weight = self.model_weights.get('rl', 0.15)

            if signal in votes:
                votes[signal] += conf * weight
            total_weight += weight

        # Pattern analysis
        if context.pattern_analysis:
            signal = context.pattern_analysis.get('overall_signal', 'NEUTRAL')
            conf = context.pattern_analysis.get('overall_confidence', 0.5)
            weight = self.model_weights.get('pattern', 0.15)

            if signal == "BUY":
                votes["BUY"] += conf * weight
            elif signal == "SELL":
                votes["SELL"] += conf * weight
            else:
                votes["HOLD"] += conf * weight
            total_weight += weight

        # Normalize votes
        if total_weight > 0:
            for key in votes:
                votes[key] /= total_weight

        # Get final action
        final_action = max(votes, key=votes.get)
        final_confidence = votes[final_action]

        # Apply minimum confidence threshold
        if final_confidence < 0.55:
            final_action = "HOLD"
            final_confidence = 0.5

        return final_action, final_confidence

    def _calculate_position_size(
        self,
        confidence: float,
        balance: float,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """Calculate position size based on risk management"""
        risk_amount = balance * self.risk_tolerance * confidence

        price_risk = abs(entry_price - stop_loss)
        if price_risk == 0:
            price_risk = entry_price * 0.01

        position_value = risk_amount / (price_risk / entry_price)
        max_position = balance * self.max_position_size

        return min(position_value, max_position)

    def get_brain_status(self) -> Dict[str, Any]:
        """Get current brain status"""
        return {
            "is_thinking": self.is_thinking,
            "thinking_mode": self.thinking_mode.value,
            "current_regime": self.current_regime.value,
            "llm_provider": self.llm_provider,
            "model_weights": self.model_weights,
            "decisions_made": len(self.decision_history),
            "last_decision": self.decision_history[-1].to_dict() if self.decision_history else None,
            "models_loaded": {
                "lstm": self.price_predictor is not None and self.price_predictor.is_trained if self.price_predictor else False,
                "transformer": self.transformer_predictor is not None and self.transformer_predictor.is_trained if self.transformer_predictor else False,
                "pattern_cnn": self.pattern_cnn is not None,
                "rl_agent": self.rl_agent is not None and self.rl_agent.is_trained if self.rl_agent else False
            }
        }

    def update_model_weights(
        self,
        performance_data: Dict[str, float]
    ):
        """Update model weights based on performance"""
        total = sum(performance_data.values())
        if total > 0:
            for model, perf in performance_data.items():
                if model in self.model_weights:
                    self.model_weights[model] = perf / total

        logger.info(f"Updated model weights: {self.model_weights}")
