"""AI Analyzer - The brain of the trading bot"""
import logging
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from openai import OpenAI
import anthropic
from .models import (
    AnalysisResult, MarketSignal, SignalStrength,
    TechnicalAnalysis, SentimentAnalysis
)

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """
    AI-powered market analyzer using LLMs for intelligent trading decisions
    Combines technical analysis, sentiment analysis, and AI reasoning
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4-turbo-preview",
        api_key: Optional[str] = None
    ):
        """
        Initialize AI analyzer

        Args:
            provider: LLM provider ('openai' or 'anthropic')
            model: Model name
            api_key: API key for the provider
        """
        self.provider = provider
        self.model = model

        if provider == "openai":
            self.client = OpenAI(api_key=api_key)
        elif provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def analyze_market(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        technical_signals: Dict,
        news_data: List[Dict],
        current_price: float
    ) -> AnalysisResult:
        """
        Perform comprehensive market analysis

        Args:
            symbol: Trading symbol
            market_data: Historical price data
            technical_signals: Technical indicator signals
            news_data: Recent news articles
            current_price: Current market price

        Returns:
            AnalysisResult: Complete analysis with trading recommendation
        """
        logger.info(f"Analyzing market for {symbol}")

        # Step 1: Analyze technical indicators
        technical_analysis = self._analyze_technical(
            market_data, technical_signals, current_price
        )

        # Step 2: Analyze news sentiment
        sentiment_analysis = self._analyze_sentiment(news_data)

        # Step 3: Get AI reasoning
        ai_reasoning = self._get_ai_reasoning(
            symbol, market_data, technical_analysis, sentiment_analysis, current_price
        )

        # Step 4: Combine all signals
        signals = self._combine_signals(
            technical_analysis, sentiment_analysis, ai_reasoning
        )

        # Step 5: Make final decision
        final_signal, confidence, should_trade = self._make_final_decision(signals)

        # Step 6: Calculate trade parameters
        entry, stop_loss, take_profit, risk_reward = self._calculate_trade_params(
            current_price, final_signal, market_data
        )

        # Step 7: Generate summary and reasoning
        summary, reasoning_steps, risks, opportunities = self._generate_summary(
            symbol, technical_analysis, sentiment_analysis, ai_reasoning,
            final_signal, confidence
        )

        return AnalysisResult(
            symbol=symbol,
            technical_analysis=technical_analysis,
            sentiment_analysis=sentiment_analysis,
            ai_reasoning=ai_reasoning,
            signals=signals,
            final_signal=final_signal,
            confidence=confidence,
            should_trade=should_trade,
            suggested_entry=entry,
            suggested_stop_loss=stop_loss,
            suggested_take_profit=take_profit,
            risk_reward_ratio=risk_reward,
            summary=summary,
            reasoning_steps=reasoning_steps,
            risk_factors=risks,
            opportunity_factors=opportunities
        )

    def _analyze_technical(
        self,
        market_data: pd.DataFrame,
        signals: Dict,
        current_price: float
    ) -> TechnicalAnalysis:
        """Analyze technical indicators"""

        # Determine trend
        if 'trend' in signals:
            trend = signals['trend']
            trend_strength = signals.get('trend_strength', 0.5)
        else:
            # Simple trend detection using moving averages
            if len(market_data) >= 50:
                sma_20 = market_data['close'].rolling(20).mean().iloc[-1]
                sma_50 = market_data['close'].rolling(50).mean().iloc[-1]

                if current_price > sma_20 > sma_50:
                    trend = "uptrend"
                    trend_strength = 0.8
                elif current_price < sma_20 < sma_50:
                    trend = "downtrend"
                    trend_strength = 0.8
                else:
                    trend = "sideways"
                    trend_strength = 0.3
            else:
                trend = "unknown"
                trend_strength = 0.5

        # Find support and resistance
        recent_data = market_data.tail(100)
        highs = recent_data['high'].values
        lows = recent_data['low'].values

        resistance_levels = self._find_levels(highs, current_price, above=True)
        support_levels = self._find_levels(lows, current_price, above=False)

        # Determine signal from indicators
        buy_signals = 0
        sell_signals = 0
        total_signals = 0

        for indicator, value in signals.items():
            if indicator in ['RSI', 'MACD', 'Stochastic', 'CCI']:
                total_signals += 1
                if value > 0:
                    buy_signals += 1
                elif value < 0:
                    sell_signals += 1

        if total_signals > 0:
            score = (buy_signals - sell_signals) / total_signals
            if score > 0.5:
                signal = SignalStrength.STRONG_BUY
            elif score > 0.2:
                signal = SignalStrength.BUY
            elif score < -0.5:
                signal = SignalStrength.STRONG_SELL
            elif score < -0.2:
                signal = SignalStrength.SELL
            else:
                signal = SignalStrength.NEUTRAL
        else:
            signal = SignalStrength.NEUTRAL

        reasoning = self._create_technical_reasoning(
            trend, signals, buy_signals, sell_signals, total_signals
        )

        return TechnicalAnalysis(
            trend=trend,
            trend_strength=trend_strength,
            support_levels=support_levels,
            resistance_levels=resistance_levels,
            indicators=signals,
            signal=signal,
            reasoning=reasoning
        )

    def _find_levels(
        self,
        prices: list,
        current: float,
        above: bool,
        max_levels: int = 3
    ) -> List[float]:
        """Find support or resistance levels"""
        if above:
            levels = [p for p in prices if p > current]
        else:
            levels = [p for p in prices if p < current]

        if not levels:
            return []

        # Cluster similar prices
        levels.sort()
        clustered = []
        current_cluster = [levels[0]]

        for price in levels[1:]:
            if abs(price - current_cluster[-1]) / current_cluster[-1] < 0.002:  # 0.2% threshold
                current_cluster.append(price)
            else:
                clustered.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [price]

        if current_cluster:
            clustered.append(sum(current_cluster) / len(current_cluster))

        return clustered[:max_levels]

    def _analyze_sentiment(self, news_data: List[Dict]) -> SentimentAnalysis:
        """Analyze news sentiment"""
        if not news_data:
            return SentimentAnalysis(
                overall_sentiment="neutral",
                sentiment_score=0.0,
                news_count=0,
                key_topics=[],
                reasoning="No recent news available"
            )

        # Count positive/negative news
        positive = sum(1 for n in news_data if n.get('sentiment', 0) > 0.2)
        negative = sum(1 for n in news_data if n.get('sentiment', 0) < -0.2)
        neutral = len(news_data) - positive - negative

        # Calculate overall sentiment
        total_sentiment = sum(n.get('sentiment', 0) for n in news_data)
        avg_sentiment = total_sentiment / len(news_data) if news_data else 0

        if avg_sentiment > 0.3:
            overall = "positive"
        elif avg_sentiment < -0.3:
            overall = "negative"
        else:
            overall = "neutral"

        # Extract key topics
        topics = []
        for news in news_data[:5]:
            if 'title' in news:
                # Simple keyword extraction
                words = news['title'].lower().split()
                important_words = [w for w in words if len(w) > 5]
                topics.extend(important_words[:2])

        key_topics = list(set(topics))[:5]

        reasoning = f"Analyzed {len(news_data)} news articles: {positive} positive, {negative} negative, {neutral} neutral. Overall sentiment is {overall}."

        return SentimentAnalysis(
            overall_sentiment=overall,
            sentiment_score=avg_sentiment,
            news_count=len(news_data),
            key_topics=key_topics,
            reasoning=reasoning
        )

    def _get_ai_reasoning(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        technical: TechnicalAnalysis,
        sentiment: SentimentAnalysis,
        current_price: float
    ) -> str:
        """Get AI reasoning from LLM"""

        # Prepare market context
        recent_data = market_data.tail(10)
        price_change = ((recent_data['close'].iloc[-1] - recent_data['close'].iloc[0]) /
                       recent_data['close'].iloc[0] * 100)

        prompt = f"""You are an expert forex trader analyzing {symbol}.

Current Market Situation:
- Current Price: {current_price}
- Recent 10-bar change: {price_change:.2f}%
- Trend: {technical.trend} (strength: {technical.trend_strength:.2f})

Technical Analysis:
- Signal: {technical.signal.value}
- Support levels: {', '.join([f'{s:.5f}' for s in technical.support_levels])}
- Resistance levels: {', '.join([f'{r:.5f}' for r in technical.resistance_levels])}
- Indicators: {technical.indicators}

Sentiment Analysis:
- Overall: {sentiment.overall_sentiment}
- Score: {sentiment.sentiment_score:.2f}
- News count: {sentiment.news_count}
- Key topics: {', '.join(sentiment.key_topics)}

Provide a concise trading analysis (2-3 sentences) including:
1. Your overall market assessment
2. Key factors influencing the decision
3. Your recommendation (bullish/bearish/neutral) and why

Be direct and actionable. Focus on the most important factors."""

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert forex trading analyst. Provide concise, actionable insights."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                return response.choices[0].message.content.strip()

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=300,
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"AI reasoning error: {str(e)}")
            return f"Technical analysis shows {technical.signal.value} signal in {technical.trend} with {sentiment.overall_sentiment} sentiment."

    def _create_technical_reasoning(
        self,
        trend: str,
        signals: Dict,
        buy_signals: int,
        sell_signals: int,
        total: int
    ) -> str:
        """Create technical analysis reasoning"""
        reasoning = f"Market is in {trend}. "

        if total > 0:
            reasoning += f"Technical indicators show {buy_signals} buy signals and {sell_signals} sell signals out of {total} total. "

        # Add specific indicator mentions
        important_indicators = []
        for indicator, value in signals.items():
            if indicator in ['RSI', 'MACD']:
                if abs(value) > 0.5:
                    direction = "bullish" if value > 0 else "bearish"
                    important_indicators.append(f"{indicator} is {direction}")

        if important_indicators:
            reasoning += " ".join(important_indicators) + "."

        return reasoning

    def _combine_signals(
        self,
        technical: TechnicalAnalysis,
        sentiment: SentimentAnalysis,
        ai_reasoning: str
    ) -> List[MarketSignal]:
        """Combine all signals"""
        signals = []

        # Technical signal
        confidence = 0.7  # Base confidence for technical
        if technical.trend in ["uptrend", "downtrend"]:
            confidence += technical.trend_strength * 0.2

        signals.append(MarketSignal(
            source="Technical Analysis",
            signal=technical.signal,
            confidence=min(confidence, 0.95),
            reasoning=technical.reasoning
        ))

        # Sentiment signal
        if sentiment.news_count > 0:
            if sentiment.sentiment_score > 0.3:
                sent_signal = SignalStrength.BUY
            elif sentiment.sentiment_score > 0.1:
                sent_signal = SignalStrength.NEUTRAL
            elif sentiment.sentiment_score < -0.3:
                sent_signal = SignalStrength.SELL
            else:
                sent_signal = SignalStrength.NEUTRAL

            signals.append(MarketSignal(
                source="Sentiment Analysis",
                signal=sent_signal,
                confidence=min(abs(sentiment.sentiment_score) + 0.5, 0.9),
                reasoning=sentiment.reasoning
            ))

        # AI signal (extract from reasoning)
        ai_signal = self._extract_signal_from_ai(ai_reasoning)
        signals.append(MarketSignal(
            source="AI Analysis",
            signal=ai_signal,
            confidence=0.75,
            reasoning=ai_reasoning
        ))

        return signals

    def _extract_signal_from_ai(self, reasoning: str) -> SignalStrength:
        """Extract signal from AI reasoning text"""
        reasoning_lower = reasoning.lower()

        # Strong signals
        if any(word in reasoning_lower for word in ['strong buy', 'very bullish', 'excellent opportunity']):
            return SignalStrength.STRONG_BUY
        if any(word in reasoning_lower for word in ['strong sell', 'very bearish', 'high risk']):
            return SignalStrength.STRONG_SELL

        # Regular signals
        if any(word in reasoning_lower for word in ['buy', 'bullish', 'upside', 'long']):
            return SignalStrength.BUY
        if any(word in reasoning_lower for word in ['sell', 'bearish', 'downside', 'short']):
            return SignalStrength.SELL

        return SignalStrength.NEUTRAL

    def _make_final_decision(
        self,
        signals: List[MarketSignal]
    ) -> tuple[SignalStrength, float, bool]:
        """Make final trading decision"""

        # Weight signals by confidence
        signal_scores = {
            SignalStrength.STRONG_BUY: 2,
            SignalStrength.BUY: 1,
            SignalStrength.NEUTRAL: 0,
            SignalStrength.SELL: -1,
            SignalStrength.STRONG_SELL: -2
        }

        weighted_score = 0
        total_weight = 0

        for signal in signals:
            score = signal_scores[signal.signal]
            weighted_score += score * signal.confidence
            total_weight += signal.confidence

        avg_score = weighted_score / total_weight if total_weight > 0 else 0
        avg_confidence = total_weight / len(signals) if signals else 0

        # Determine final signal
        if avg_score > 1.2:
            final_signal = SignalStrength.STRONG_BUY
        elif avg_score > 0.4:
            final_signal = SignalStrength.BUY
        elif avg_score < -1.2:
            final_signal = SignalStrength.STRONG_SELL
        elif avg_score < -0.4:
            final_signal = SignalStrength.SELL
        else:
            final_signal = SignalStrength.NEUTRAL

        # Decide whether to trade
        # Not too strict - trade if confidence > 0.6 and signal is not neutral
        should_trade = (
            avg_confidence > 0.6 and
            final_signal != SignalStrength.NEUTRAL and
            abs(avg_score) > 0.5
        )

        return final_signal, avg_confidence, should_trade

    def _calculate_trade_params(
        self,
        current_price: float,
        signal: SignalStrength,
        market_data: pd.DataFrame
    ) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """Calculate entry, stop loss, and take profit"""

        if signal == SignalStrength.NEUTRAL:
            return None, None, None, None

        # Calculate ATR for stop loss calculation
        if len(market_data) >= 14:
            high_low = market_data['high'] - market_data['low']
            high_close = abs(market_data['high'] - market_data['close'].shift())
            low_close = abs(market_data['low'] - market_data['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            atr = true_range.rolling(14).mean().iloc[-1]
        else:
            # Fallback: use 1% of price
            atr = current_price * 0.01

        entry = current_price

        if signal in [SignalStrength.BUY, SignalStrength.STRONG_BUY]:
            # Buy trade
            stop_loss = current_price - (2 * atr)
            take_profit = current_price + (3 * atr)  # 1.5:1 risk-reward
            risk_reward = 1.5
        else:
            # Sell trade
            stop_loss = current_price + (2 * atr)
            take_profit = current_price - (3 * atr)
            risk_reward = 1.5

        return entry, stop_loss, take_profit, risk_reward

    def _generate_summary(
        self,
        symbol: str,
        technical: TechnicalAnalysis,
        sentiment: SentimentAnalysis,
        ai_reasoning: str,
        signal: SignalStrength,
        confidence: float
    ) -> tuple[str, List[str], List[str], List[str]]:
        """Generate summary and reasoning steps"""

        # Summary
        summary = f"{symbol}: {signal.value} signal with {confidence:.0%} confidence. "
        summary += f"Market in {technical.trend}, sentiment is {sentiment.overall_sentiment}."

        # Reasoning steps
        steps = [
            f"1. Technical Analysis: {technical.signal.value} - {technical.reasoning}",
            f"2. Sentiment Analysis: {sentiment.overall_sentiment.upper()} with {sentiment.news_count} news articles",
            f"3. AI Reasoning: {ai_reasoning}",
            f"4. Final Decision: {signal.value} (confidence: {confidence:.0%})"
        ]

        # Risk factors
        risks = []
        if sentiment.overall_sentiment == "negative":
            risks.append("Negative news sentiment may impact price")
        if technical.trend == "sideways":
            risks.append("Sideways market - low trend strength")
        if confidence < 0.75:
            risks.append("Lower confidence signal - be cautious")
        if not risks:
            risks.append("Normal market risk applies")

        # Opportunity factors
        opportunities = []
        if technical.trend in ["uptrend", "downtrend"] and technical.trend_strength > 0.7:
            opportunities.append(f"Strong {technical.trend} provides clear direction")
        if sentiment.overall_sentiment == "positive" and signal in [SignalStrength.BUY, SignalStrength.STRONG_BUY]:
            opportunities.append("Positive sentiment supports bullish view")
        if confidence > 0.8:
            opportunities.append("High confidence signal from multiple sources")
        if not opportunities:
            opportunities.append("Standard trading opportunity")

        return summary, steps, risks, opportunities
