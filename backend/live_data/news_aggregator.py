"""
Real-Time News Aggregator

Aggregates news from multiple sources:
- NewsAPI
- Finnhub
- RSS feeds
- Social media (Twitter/Reddit)
- Economic calendars
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json
import os
import re
import hashlib

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """News article data"""
    id: str
    title: str
    description: str
    content: str
    source: str
    url: str
    published_at: datetime
    symbols: List[str]
    categories: List[str]
    sentiment_score: Optional[float] = None
    importance: str = "normal"  # low, normal, high, critical

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "content": self.content[:500] if self.content else "",
            "source": self.source,
            "url": self.url,
            "published_at": self.published_at.isoformat(),
            "symbols": self.symbols,
            "categories": self.categories,
            "sentiment_score": self.sentiment_score,
            "importance": self.importance
        }


@dataclass
class EconomicEvent:
    """Economic calendar event"""
    id: str
    title: str
    country: str
    currency: str
    impact: str  # low, medium, high
    forecast: Optional[float]
    previous: Optional[float]
    actual: Optional[float]
    event_time: datetime
    description: str

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "country": self.country,
            "currency": self.currency,
            "impact": self.impact,
            "forecast": self.forecast,
            "previous": self.previous,
            "actual": self.actual,
            "event_time": self.event_time.isoformat(),
            "description": self.description
        }


@dataclass
class NewsAggregatorConfig:
    """Configuration for news aggregator"""
    newsapi_key: str = ""
    finnhub_key: str = ""
    twitter_bearer_token: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    fetch_interval: int = 60  # seconds
    max_articles_per_source: int = 50
    buffer_size: int = 1000
    keywords: List[str] = field(default_factory=lambda: [
        "gold", "XAUUSD", "forex", "fed", "interest rate",
        "inflation", "USD", "dollar", "economy", "market"
    ])
    rss_feeds: List[str] = field(default_factory=lambda: [
        "https://feeds.finance.yahoo.com/rss/2.0/headline",
        "https://www.investing.com/rss/news.rss",
        "https://www.forexlive.com/feed/news"
    ])


class RealTimeNewsAggregator:
    """
    Real-Time News Aggregator

    Features:
    - Multi-source news collection
    - Deduplication
    - Relevance scoring
    - Real-time updates
    - Economic calendar integration
    """

    def __init__(self, config: Optional[NewsAggregatorConfig] = None):
        self.config = config or NewsAggregatorConfig()
        self.is_running = False
        self.articles: deque = deque(maxlen=self.config.buffer_size)
        self.events: deque = deque(maxlen=500)
        self.seen_ids: set = set()
        self.callbacks: List[Callable[[NewsArticle], None]] = []
        self.event_callbacks: List[Callable[[EconomicEvent], None]] = []
        self._tasks: List[asyncio.Task] = []

        # Keywords for relevance
        self.bullish_keywords = [
            "surge", "rally", "gain", "rise", "bullish", "support",
            "breakout", "optimistic", "growth", "strong", "buy"
        ]
        self.bearish_keywords = [
            "drop", "fall", "decline", "bearish", "resistance",
            "breakdown", "pessimistic", "weak", "sell", "crash"
        ]
        self.high_impact_keywords = [
            "fed", "fomc", "rate decision", "nfp", "payroll",
            "inflation", "cpi", "gdp", "central bank", "emergency"
        ]

        # Symbol mapping
        self.symbol_keywords = {
            "XAUUSD": ["gold", "xau", "precious metal", "bullion"],
            "EURUSD": ["euro", "eur/usd", "eurozone"],
            "GBPUSD": ["pound", "sterling", "gbp", "cable"],
            "USDJPY": ["yen", "jpy", "japan"],
            "USDCHF": ["swiss", "chf", "franc"]
        }

        logger.info("RealTimeNewsAggregator initialized")

    def add_callback(self, callback: Callable[[NewsArticle], None]):
        """Add callback for new articles"""
        self.callbacks.append(callback)

    def add_event_callback(self, callback: Callable[[EconomicEvent], None]):
        """Add callback for economic events"""
        self.event_callbacks.append(callback)

    def _generate_id(self, title: str, source: str) -> str:
        """Generate unique ID for article"""
        content = f"{title}{source}"
        return hashlib.md5(content.encode()).hexdigest()

    def _extract_symbols(self, text: str) -> List[str]:
        """Extract relevant trading symbols from text"""
        text_lower = text.lower()
        symbols = []

        for symbol, keywords in self.symbol_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if symbol not in symbols:
                        symbols.append(symbol)
                    break

        return symbols

    def _calculate_importance(self, text: str) -> str:
        """Calculate news importance based on keywords"""
        text_lower = text.lower()

        for keyword in self.high_impact_keywords:
            if keyword in text_lower:
                return "high"

        # Count impact words
        bullish_count = sum(1 for kw in self.bullish_keywords if kw in text_lower)
        bearish_count = sum(1 for kw in self.bearish_keywords if kw in text_lower)

        if bullish_count + bearish_count >= 3:
            return "high"
        elif bullish_count + bearish_count >= 1:
            return "normal"

        return "low"

    async def _emit_article(self, article: NewsArticle):
        """Emit article to callbacks"""
        # Check for duplicates
        if article.id in self.seen_ids:
            return

        self.seen_ids.add(article.id)
        self.articles.append(article)

        # Notify callbacks
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(article)
                else:
                    callback(article)
            except Exception as e:
                logger.error(f"Article callback error: {e}")

    async def _fetch_newsapi(self):
        """Fetch news from NewsAPI"""
        if not self.config.newsapi_key or not AIOHTTP_AVAILABLE:
            return

        base_url = "https://newsapi.org/v2/everything"

        while self.is_running:
            try:
                async with aiohttp.ClientSession() as session:
                    for keyword in self.config.keywords[:5]:  # Limit to avoid rate limits
                        params = {
                            "q": keyword,
                            "apiKey": self.config.newsapi_key,
                            "language": "en",
                            "sortBy": "publishedAt",
                            "pageSize": 10
                        }

                        async with session.get(base_url, params=params) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                articles = data.get("articles", [])

                                for item in articles:
                                    title = item.get("title", "")
                                    description = item.get("description", "")
                                    content = item.get("content", "")

                                    article = NewsArticle(
                                        id=self._generate_id(title, "newsapi"),
                                        title=title,
                                        description=description,
                                        content=content,
                                        source=item.get("source", {}).get("name", "NewsAPI"),
                                        url=item.get("url", ""),
                                        published_at=datetime.fromisoformat(
                                            item.get("publishedAt", "").replace("Z", "+00:00")
                                        ) if item.get("publishedAt") else datetime.now(),
                                        symbols=self._extract_symbols(f"{title} {description}"),
                                        categories=[keyword],
                                        importance=self._calculate_importance(f"{title} {description}")
                                    )

                                    await self._emit_article(article)

                        await asyncio.sleep(1)  # Rate limiting

            except Exception as e:
                logger.error(f"NewsAPI error: {e}")

            await asyncio.sleep(self.config.fetch_interval)

    async def _fetch_finnhub(self):
        """Fetch news from Finnhub"""
        if not self.config.finnhub_key or not AIOHTTP_AVAILABLE:
            return

        base_url = "https://finnhub.io/api/v1/news"

        while self.is_running:
            try:
                async with aiohttp.ClientSession() as session:
                    params = {
                        "category": "forex",
                        "token": self.config.finnhub_key
                    }

                    async with session.get(base_url, params=params) as resp:
                        if resp.status == 200:
                            articles = await resp.json()

                            for item in articles[:self.config.max_articles_per_source]:
                                headline = item.get("headline", "")
                                summary = item.get("summary", "")

                                article = NewsArticle(
                                    id=self._generate_id(headline, "finnhub"),
                                    title=headline,
                                    description=summary,
                                    content=summary,
                                    source=item.get("source", "Finnhub"),
                                    url=item.get("url", ""),
                                    published_at=datetime.fromtimestamp(
                                        item.get("datetime", 0)
                                    ),
                                    symbols=self._extract_symbols(f"{headline} {summary}"),
                                    categories=["forex"],
                                    importance=self._calculate_importance(f"{headline} {summary}")
                                )

                                await self._emit_article(article)

            except Exception as e:
                logger.error(f"Finnhub news error: {e}")

            await asyncio.sleep(self.config.fetch_interval)

    async def _fetch_finnhub_calendar(self):
        """Fetch economic calendar from Finnhub"""
        if not self.config.finnhub_key or not AIOHTTP_AVAILABLE:
            return

        base_url = "https://finnhub.io/api/v1/calendar/economic"

        while self.is_running:
            try:
                async with aiohttp.ClientSession() as session:
                    today = datetime.now()
                    params = {
                        "from": today.strftime("%Y-%m-%d"),
                        "to": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
                        "token": self.config.finnhub_key
                    }

                    async with session.get(base_url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            events = data.get("economicCalendar", [])

                            for item in events:
                                event = EconomicEvent(
                                    id=f"finnhub_{item.get('id', '')}",
                                    title=item.get("event", ""),
                                    country=item.get("country", ""),
                                    currency=item.get("currency", ""),
                                    impact=item.get("impact", "low"),
                                    forecast=item.get("estimate"),
                                    previous=item.get("prev"),
                                    actual=item.get("actual"),
                                    event_time=datetime.strptime(
                                        item.get("time", "00:00:00"),
                                        "%H:%M:%S"
                                    ).replace(
                                        year=today.year,
                                        month=today.month,
                                        day=today.day
                                    ),
                                    description=item.get("event", "")
                                )

                                # Check if already seen
                                if event.id not in self.seen_ids:
                                    self.seen_ids.add(event.id)
                                    self.events.append(event)

                                    for callback in self.event_callbacks:
                                        try:
                                            if asyncio.iscoroutinefunction(callback):
                                                await callback(event)
                                            else:
                                                callback(event)
                                        except Exception as e:
                                            logger.error(f"Event callback error: {e}")

            except Exception as e:
                logger.error(f"Finnhub calendar error: {e}")

            await asyncio.sleep(300)  # Update every 5 minutes

    async def _fetch_rss_feeds(self):
        """Fetch news from RSS feeds"""
        if not FEEDPARSER_AVAILABLE:
            logger.warning("feedparser not available, skipping RSS feeds")
            return

        while self.is_running:
            for feed_url in self.config.rss_feeds:
                try:
                    # Use aiohttp to fetch, then parse
                    if AIOHTTP_AVAILABLE:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                                if resp.status == 200:
                                    content = await resp.text()
                                    feed = feedparser.parse(content)
                    else:
                        feed = feedparser.parse(feed_url)

                    for entry in feed.entries[:20]:
                        title = entry.get("title", "")
                        description = entry.get("description", entry.get("summary", ""))

                        # Parse published date
                        published = entry.get("published_parsed") or entry.get("updated_parsed")
                        if published:
                            published_at = datetime(*published[:6])
                        else:
                            published_at = datetime.now()

                        article = NewsArticle(
                            id=self._generate_id(title, feed_url),
                            title=title,
                            description=description,
                            content=description,
                            source=feed.feed.get("title", "RSS"),
                            url=entry.get("link", ""),
                            published_at=published_at,
                            symbols=self._extract_symbols(f"{title} {description}"),
                            categories=["rss"],
                            importance=self._calculate_importance(f"{title} {description}")
                        )

                        await self._emit_article(article)

                except Exception as e:
                    logger.error(f"RSS feed error for {feed_url}: {e}")

                await asyncio.sleep(1)

            await asyncio.sleep(self.config.fetch_interval * 2)

    async def start(self):
        """Start news aggregation"""
        if self.is_running:
            return

        self.is_running = True
        logger.info("Starting news aggregator...")

        self._tasks = [
            asyncio.create_task(self._fetch_newsapi()),
            asyncio.create_task(self._fetch_finnhub()),
            asyncio.create_task(self._fetch_finnhub_calendar()),
            asyncio.create_task(self._fetch_rss_feeds())
        ]

        logger.info("News aggregator started")

    async def stop(self):
        """Stop news aggregation"""
        self.is_running = False

        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._tasks = []
        logger.info("News aggregator stopped")

    def get_recent_articles(
        self,
        count: int = 50,
        symbols: Optional[List[str]] = None,
        min_importance: Optional[str] = None
    ) -> List[NewsArticle]:
        """Get recent articles with optional filtering"""
        articles = list(self.articles)

        # Filter by symbols
        if symbols:
            articles = [
                a for a in articles
                if any(s in a.symbols for s in symbols)
            ]

        # Filter by importance
        if min_importance:
            importance_order = ["low", "normal", "high", "critical"]
            min_idx = importance_order.index(min_importance)
            articles = [
                a for a in articles
                if importance_order.index(a.importance) >= min_idx
            ]

        # Sort by time and return
        articles.sort(key=lambda x: x.published_at, reverse=True)
        return articles[:count]

    def get_upcoming_events(
        self,
        hours: int = 24,
        min_impact: Optional[str] = None
    ) -> List[EconomicEvent]:
        """Get upcoming economic events"""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)

        events = [
            e for e in self.events
            if now <= e.event_time <= cutoff
        ]

        if min_impact:
            impact_order = ["low", "medium", "high"]
            min_idx = impact_order.index(min_impact)
            events = [
                e for e in events
                if impact_order.index(e.impact) >= min_idx
            ]

        events.sort(key=lambda x: x.event_time)
        return events

    def get_news_summary(self) -> Dict[str, Any]:
        """Get summary of current news state"""
        articles = list(self.articles)
        events = list(self.events)

        return {
            "total_articles": len(articles),
            "total_events": len(events),
            "articles_last_hour": len([
                a for a in articles
                if a.published_at > datetime.now() - timedelta(hours=1)
            ]),
            "high_importance_count": len([
                a for a in articles
                if a.importance in ["high", "critical"]
            ]),
            "upcoming_high_impact_events": len([
                e for e in events
                if e.impact == "high" and e.event_time > datetime.now()
            ]),
            "sources": list(set(a.source for a in articles)),
            "last_update": datetime.now().isoformat()
        }
