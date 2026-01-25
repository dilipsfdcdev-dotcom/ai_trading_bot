"""
Live Sentiment Analyzer

Real-time sentiment analysis using:
- LLM-based analysis
- Keyword scoring
- Social media sentiment
- News sentiment aggregation
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import os
import re

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

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    """Result of sentiment analysis"""
    text: str
    source: str
    sentiment: str  # bullish, bearish, neutral
    score: float  # -1 to 1
    confidence: float  # 0 to 1
    key_topics: List[str]
    market_impact: str  # low, medium, high
    trading_signal: str  # buy, sell, hold
    reasoning: str
    timestamp: datetime

    def to_dict(self) -> Dict:
        return {
            "text": self.text[:200],
            "source": self.source,
            "sentiment": self.sentiment,
            "score": self.score,
            "confidence": self.confidence,
            "key_topics": self.key_topics,
            "market_impact": self.market_impact,
            "trading_signal": self.trading_signal,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MarketSentiment:
    """Aggregated market sentiment"""
    symbol: str
    overall_sentiment: str
    sentiment_score: float  # -1 to 1
    confidence: float
    bullish_percentage: float
    bearish_percentage: float
    neutral_percentage: float
    news_count: int
    social_score: float
    key_themes: List[str]
    market_mood: str  # fear, greed, neutral
    volatility_expectation: str  # low, medium, high
    timestamp: datetime

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "overall_sentiment": self.overall_sentiment,
            "sentiment_score": self.sentiment_score,
            "confidence": self.confidence,
            "bullish_percentage": self.bullish_percentage,
            "bearish_percentage": self.bearish_percentage,
            "neutral_percentage": self.neutral_percentage,
            "news_count": self.news_count,
            "social_score": self.social_score,
            "key_themes": self.key_themes,
            "market_mood": self.market_mood,
            "volatility_expectation": self.volatility_expectation,
            "timestamp": self.timestamp.isoformat()
        }


class LiveSentimentAnalyzer:
    """
    Live Sentiment Analyzer

    Features:
    - LLM-powered sentiment analysis
    - Real-time news sentiment
    - Social media sentiment tracking
    - Market mood indicators
    - Multi-source aggregation
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        use_llm: bool = True
    ):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.use_llm = use_llm

        # Initialize LLM clients
        self.openai_client = None
        self.anthropic_client = None

        if self.use_llm:
            if OPENAI_AVAILABLE and self.openai_api_key:
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
            if ANTHROPIC_AVAILABLE and self.anthropic_api_key:
                self.anthropic_client = AsyncAnthropic(api_key=self.anthropic_api_key)

        # Sentiment history
        self.sentiment_history: Dict[str, deque] = {}
        self.analysis_cache: Dict[str, SentimentResult] = {}

        # Keyword dictionaries for rule-based analysis
        self.bullish_keywords = {
            "strong": ["bullish", "surge", "rally", "breakout", "soar", "jump",
                       "gain", "rise", "upward", "buy", "long", "optimistic",
                       "growth", "boom", "recovery", "support", "accumulation"],
            "moderate": ["positive", "up", "higher", "advance", "improve",
                        "increase", "lift", "climb", "stable", "hold"],
        }

        self.bearish_keywords = {
            "strong": ["bearish", "crash", "plunge", "collapse", "tumble",
                       "drop", "fall", "decline", "sell", "short", "pessimistic",
                       "recession", "crisis", "breakdown", "resistance", "dump"],
            "moderate": ["negative", "down", "lower", "weaken", "decrease",
                        "slide", "dip", "slip", "uncertain", "cautious"],
        }

        self.high_impact_indicators = [
            "fed", "fomc", "rate", "inflation", "cpi", "gdp", "employment",
            "nfp", "payroll", "central bank", "monetary policy", "quantitative"
        ]

        logger.info("LiveSentimentAnalyzer initialized")

    def _rule_based_sentiment(self, text: str) -> SentimentResult:
        """Analyze sentiment using keyword rules"""
        text_lower = text.lower()

        # Count keyword occurrences
        bullish_strong = sum(text_lower.count(kw) for kw in self.bullish_keywords["strong"])
        bullish_moderate = sum(text_lower.count(kw) for kw in self.bullish_keywords["moderate"])
        bearish_strong = sum(text_lower.count(kw) for kw in self.bearish_keywords["strong"])
        bearish_moderate = sum(text_lower.count(kw) for kw in self.bearish_keywords["moderate"])

        # Calculate weighted score
        bullish_score = bullish_strong * 2 + bullish_moderate
        bearish_score = bearish_strong * 2 + bearish_moderate

        total = bullish_score + bearish_score
        if total == 0:
            score = 0
            sentiment = "neutral"
            confidence = 0.3
        else:
            score = (bullish_score - bearish_score) / total
            if score > 0.3:
                sentiment = "bullish"
            elif score < -0.3:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            confidence = min(0.8, 0.3 + (abs(score) * 0.5))

        # Determine market impact
        high_impact = any(ind in text_lower for ind in self.high_impact_indicators)
        market_impact = "high" if high_impact else ("medium" if total > 3 else "low")

        # Extract key topics
        key_topics = []
        for indicator in self.high_impact_indicators:
            if indicator in text_lower:
                key_topics.append(indicator)

        # Trading signal
        if score > 0.4:
            trading_signal = "buy"
        elif score < -0.4:
            trading_signal = "sell"
        else:
            trading_signal = "hold"

        return SentimentResult(
            text=text,
            source="rule_based",
            sentiment=sentiment,
            score=score,
            confidence=confidence,
            key_topics=key_topics[:5],
            market_impact=market_impact,
            trading_signal=trading_signal,
            reasoning=f"Bullish signals: {bullish_score}, Bearish signals: {bearish_score}",
            timestamp=datetime.now()
        )

    async def _llm_sentiment(self, text: str, symbol: str = "XAUUSD") -> SentimentResult:
        """Analyze sentiment using LLM"""
        prompt = f"""Analyze the following market news/text for trading sentiment related to {symbol}.

Text: "{text}"

Provide your analysis in the following JSON format:
{{
    "sentiment": "bullish" or "bearish" or "neutral",
    "score": <float from -1 (very bearish) to 1 (very bullish)>,
    "confidence": <float from 0 to 1>,
    "key_topics": ["topic1", "topic2"],
    "market_impact": "low" or "medium" or "high",
    "trading_signal": "buy" or "sell" or "hold",
    "reasoning": "brief explanation"
}}

Only respond with the JSON, no other text."""

        try:
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are a financial sentiment analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                result_text = response.choices[0].message.content

            elif self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                result_text = response.content[0].text

            else:
                return self._rule_based_sentiment(text)

            # Parse JSON response
            import json
            # Clean potential markdown
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            data = json.loads(result_text)

            return SentimentResult(
                text=text,
                source="llm",
                sentiment=data.get("sentiment", "neutral"),
                score=float(data.get("score", 0)),
                confidence=float(data.get("confidence", 0.5)),
                key_topics=data.get("key_topics", []),
                market_impact=data.get("market_impact", "medium"),
                trading_signal=data.get("trading_signal", "hold"),
                reasoning=data.get("reasoning", ""),
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"LLM sentiment error: {e}")
            return self._rule_based_sentiment(text)

    async def analyze(
        self,
        text: str,
        symbol: str = "XAUUSD",
        use_cache: bool = True
    ) -> SentimentResult:
        """Analyze sentiment of text"""
        # Check cache
        cache_key = f"{symbol}_{hash(text)}"
        if use_cache and cache_key in self.analysis_cache:
            cached = self.analysis_cache[cache_key]
            if datetime.now() - cached.timestamp < timedelta(minutes=30):
                return cached

        # Analyze
        if self.use_llm and (self.openai_client or self.anthropic_client):
            result = await self._llm_sentiment(text, symbol)
        else:
            result = self._rule_based_sentiment(text)

        # Cache result
        self.analysis_cache[cache_key] = result

        # Add to history
        if symbol not in self.sentiment_history:
            self.sentiment_history[symbol] = deque(maxlen=1000)
        self.sentiment_history[symbol].append(result)

        return result

    async def analyze_batch(
        self,
        texts: List[str],
        symbol: str = "XAUUSD"
    ) -> List[SentimentResult]:
        """Analyze multiple texts concurrently"""
        tasks = [self.analyze(text, symbol) for text in texts]
        return await asyncio.gather(*tasks)

    def get_aggregated_sentiment(
        self,
        symbol: str,
        hours: int = 4
    ) -> MarketSentiment:
        """Get aggregated sentiment for a symbol"""
        if symbol not in self.sentiment_history:
            return MarketSentiment(
                symbol=symbol,
                overall_sentiment="neutral",
                sentiment_score=0,
                confidence=0,
                bullish_percentage=33.3,
                bearish_percentage=33.3,
                neutral_percentage=33.4,
                news_count=0,
                social_score=0,
                key_themes=[],
                market_mood="neutral",
                volatility_expectation="low",
                timestamp=datetime.now()
            )

        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [
            s for s in self.sentiment_history[symbol]
            if s.timestamp > cutoff
        ]

        if not recent:
            return MarketSentiment(
                symbol=symbol,
                overall_sentiment="neutral",
                sentiment_score=0,
                confidence=0,
                bullish_percentage=33.3,
                bearish_percentage=33.3,
                neutral_percentage=33.4,
                news_count=0,
                social_score=0,
                key_themes=[],
                market_mood="neutral",
                volatility_expectation="low",
                timestamp=datetime.now()
            )

        # Calculate aggregates
        bullish = [s for s in recent if s.sentiment == "bullish"]
        bearish = [s for s in recent if s.sentiment == "bearish"]
        neutral = [s for s in recent if s.sentiment == "neutral"]

        total = len(recent)
        bullish_pct = len(bullish) / total * 100
        bearish_pct = len(bearish) / total * 100
        neutral_pct = len(neutral) / total * 100

        # Weighted score
        avg_score = sum(s.score * s.confidence for s in recent) / sum(s.confidence for s in recent) if recent else 0

        # Confidence
        avg_confidence = sum(s.confidence for s in recent) / total

        # Overall sentiment
        if avg_score > 0.3:
            overall = "bullish"
        elif avg_score < -0.3:
            overall = "bearish"
        else:
            overall = "neutral"

        # Key themes
        all_topics = []
        for s in recent:
            all_topics.extend(s.key_topics)
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        key_themes = sorted(topic_counts.keys(), key=lambda x: topic_counts[x], reverse=True)[:5]

        # Market mood
        if avg_score > 0.5:
            mood = "greed"
        elif avg_score < -0.5:
            mood = "fear"
        else:
            mood = "neutral"

        # Volatility expectation
        high_impact = [s for s in recent if s.market_impact == "high"]
        if len(high_impact) > total * 0.3:
            volatility = "high"
        elif len(high_impact) > total * 0.1:
            volatility = "medium"
        else:
            volatility = "low"

        return MarketSentiment(
            symbol=symbol,
            overall_sentiment=overall,
            sentiment_score=avg_score,
            confidence=avg_confidence,
            bullish_percentage=bullish_pct,
            bearish_percentage=bearish_pct,
            neutral_percentage=neutral_pct,
            news_count=total,
            social_score=avg_score,  # Simplified
            key_themes=key_themes,
            market_mood=mood,
            volatility_expectation=volatility,
            timestamp=datetime.now()
        )

    def get_sentiment_trend(
        self,
        symbol: str,
        periods: int = 12,
        period_hours: int = 1
    ) -> List[Dict]:
        """Get sentiment trend over time"""
        if symbol not in self.sentiment_history:
            return []

        trend = []
        now = datetime.now()

        for i in range(periods):
            start = now - timedelta(hours=(i + 1) * period_hours)
            end = now - timedelta(hours=i * period_hours)

            period_results = [
                s for s in self.sentiment_history[symbol]
                if start <= s.timestamp < end
            ]

            if period_results:
                avg_score = sum(s.score for s in period_results) / len(period_results)
            else:
                avg_score = 0

            trend.append({
                "period": i,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "sentiment_score": avg_score,
                "sample_count": len(period_results)
            })

        trend.reverse()
        return trend

    def get_trading_recommendation(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """Get trading recommendation based on sentiment"""
        sentiment = self.get_aggregated_sentiment(symbol)

        # Determine recommendation
        if sentiment.sentiment_score > 0.5 and sentiment.confidence > 0.6:
            recommendation = "STRONG_BUY"
            action = "Consider opening long position"
        elif sentiment.sentiment_score > 0.3 and sentiment.confidence > 0.5:
            recommendation = "BUY"
            action = "Bullish sentiment, watch for entry"
        elif sentiment.sentiment_score < -0.5 and sentiment.confidence > 0.6:
            recommendation = "STRONG_SELL"
            action = "Consider opening short position"
        elif sentiment.sentiment_score < -0.3 and sentiment.confidence > 0.5:
            recommendation = "SELL"
            action = "Bearish sentiment, watch for entry"
        else:
            recommendation = "NEUTRAL"
            action = "Wait for clearer signals"

        return {
            "symbol": symbol,
            "recommendation": recommendation,
            "action": action,
            "sentiment": sentiment.to_dict(),
            "confidence_level": "high" if sentiment.confidence > 0.7 else "medium" if sentiment.confidence > 0.4 else "low",
            "timestamp": datetime.now().isoformat()
        }
