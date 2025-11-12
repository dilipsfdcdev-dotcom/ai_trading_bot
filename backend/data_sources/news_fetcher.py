"""News fetcher for market sentiment analysis"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from newsapi import NewsApiClient
import re

logger = logging.getLogger(__name__)


class NewsFetcher:
    """
    Fetches financial news from multiple sources
    Provides sentiment analysis for trading decisions
    """

    def __init__(self, news_api_key: Optional[str] = None, finnhub_key: Optional[str] = None):
        """
        Initialize news fetcher

        Args:
            news_api_key: NewsAPI key
            finnhub_key: Finnhub API key
        """
        self.news_api_key = news_api_key
        self.finnhub_key = finnhub_key
        self.newsapi_client = NewsApiClient(api_key=news_api_key) if news_api_key else None

    def get_forex_news(
        self,
        symbol: str,
        hours_ago: int = 24,
        max_articles: int = 20
    ) -> List[Dict]:
        """
        Get forex-related news

        Args:
            symbol: Currency pair (e.g., 'EURUSD')
            hours_ago: How many hours back to fetch news
            max_articles: Maximum number of articles

        Returns:
            List of news articles with sentiment
        """
        # Extract currencies from symbol
        base_currency = symbol[:3]
        quote_currency = symbol[3:6] if len(symbol) >= 6 else "USD"

        # Build search queries
        queries = [
            f"{base_currency} {quote_currency}",
            f"{base_currency} forex",
            base_currency,
            "forex market"
        ]

        all_articles = []

        # Fetch from NewsAPI
        if self.newsapi_client:
            all_articles.extend(self._fetch_newsapi(queries, hours_ago, max_articles))

        # Fetch from Finnhub
        if self.finnhub_key:
            all_articles.extend(self._fetch_finnhub(symbol, hours_ago))

        # Fetch from RSS feeds (free sources)
        all_articles.extend(self._fetch_rss_feeds(queries, hours_ago))

        # Remove duplicates
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            title = article.get('title', '').lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_articles.append(article)

        # Sort by date and limit
        unique_articles.sort(key=lambda x: x.get('published_at', datetime.now()), reverse=True)

        return unique_articles[:max_articles]

    def _fetch_newsapi(
        self,
        queries: List[str],
        hours_ago: int,
        max_articles: int
    ) -> List[Dict]:
        """Fetch news from NewsAPI"""
        articles = []

        try:
            from_date = (datetime.now() - timedelta(hours=hours_ago)).isoformat()

            for query in queries[:2]:  # Limit queries to avoid rate limits
                try:
                    response = self.newsapi_client.get_everything(
                        q=query,
                        from_param=from_date,
                        language='en',
                        sort_by='publishedAt',
                        page_size=min(max_articles // len(queries), 10)
                    )

                    if response.get('status') == 'ok':
                        for article in response.get('articles', []):
                            articles.append({
                                'title': article.get('title', ''),
                                'description': article.get('description', ''),
                                'content': article.get('content', ''),
                                'url': article.get('url', ''),
                                'source': article.get('source', {}).get('name', 'Unknown'),
                                'published_at': datetime.fromisoformat(
                                    article.get('publishedAt', '').replace('Z', '+00:00')
                                ) if article.get('publishedAt') else datetime.now(),
                                'sentiment': self._analyze_sentiment_simple(
                                    article.get('title', '') + ' ' + article.get('description', '')
                                )
                            })
                except Exception as e:
                    logger.warning(f"NewsAPI query failed for '{query}': {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"NewsAPI fetch error: {str(e)}")

        return articles

    def _fetch_finnhub(self, symbol: str, hours_ago: int) -> List[Dict]:
        """Fetch news from Finnhub"""
        articles = []

        if not self.finnhub_key:
            return articles

        try:
            from_date = (datetime.now() - timedelta(hours=hours_ago)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')

            url = f"https://finnhub.io/api/v1/news"
            params = {
                'category': 'forex',
                'from': from_date,
                'to': to_date,
                'token': self.finnhub_key
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    articles.append({
                        'title': item.get('headline', ''),
                        'description': item.get('summary', ''),
                        'content': item.get('summary', ''),
                        'url': item.get('url', ''),
                        'source': item.get('source', 'Finnhub'),
                        'published_at': datetime.fromtimestamp(item.get('datetime', 0)),
                        'sentiment': self._analyze_sentiment_simple(
                            item.get('headline', '') + ' ' + item.get('summary', '')
                        )
                    })

        except Exception as e:
            logger.error(f"Finnhub fetch error: {str(e)}")

        return articles

    def _fetch_rss_feeds(self, queries: List[str], hours_ago: int) -> List[Dict]:
        """Fetch news from free RSS feeds"""
        articles = []

        # Popular free forex news sources
        rss_sources = [
            "https://www.forexlive.com/feed/news",
            "https://www.fxstreet.com/rss/news",
            "https://www.dailyfx.com/feeds/market-news"
        ]

        try:
            import feedparser

            cutoff_time = datetime.now() - timedelta(hours=hours_ago)

            for feed_url in rss_sources:
                try:
                    feed = feedparser.parse(feed_url)

                    for entry in feed.entries[:10]:
                        # Parse published date
                        pub_date = datetime.now()
                        if hasattr(entry, 'published_parsed'):
                            pub_date = datetime(*entry.published_parsed[:6])

                        # Check if within time range
                        if pub_date < cutoff_time:
                            continue

                        # Check if relevant to queries
                        text = (entry.get('title', '') + ' ' + entry.get('summary', '')).lower()
                        if not any(q.lower() in text for q in queries):
                            continue

                        articles.append({
                            'title': entry.get('title', ''),
                            'description': entry.get('summary', ''),
                            'content': entry.get('summary', ''),
                            'url': entry.get('link', ''),
                            'source': feed.feed.get('title', 'RSS Feed'),
                            'published_at': pub_date,
                            'sentiment': self._analyze_sentiment_simple(text)
                        })

                except Exception as e:
                    logger.warning(f"RSS feed fetch failed for {feed_url}: {str(e)}")
                    continue

        except ImportError:
            logger.warning("feedparser not installed, skipping RSS feeds")
        except Exception as e:
            logger.error(f"RSS fetch error: {str(e)}")

        return articles

    def _analyze_sentiment_simple(self, text: str) -> float:
        """
        Simple rule-based sentiment analysis
        Returns score between -1 (negative) and 1 (positive)
        """
        if not text:
            return 0.0

        text_lower = text.lower()

        # Positive keywords
        positive_keywords = [
            'surge', 'rally', 'gain', 'rise', 'jump', 'climb', 'boost',
            'bullish', 'optimistic', 'positive', 'strong', 'growth',
            'advance', 'soar', 'breakthrough', 'recovery', 'improve'
        ]

        # Negative keywords
        negative_keywords = [
            'fall', 'drop', 'decline', 'plunge', 'crash', 'sink', 'tumble',
            'bearish', 'pessimistic', 'negative', 'weak', 'concern',
            'worry', 'fear', 'risk', 'threat', 'crisis', 'recession'
        ]

        # Count occurrences
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)

        # Calculate sentiment score
        total = positive_count + negative_count
        if total == 0:
            return 0.0

        sentiment = (positive_count - negative_count) / total

        # Normalize to -1 to 1
        return max(-1.0, min(1.0, sentiment))

    def get_economic_calendar(self, date: Optional[datetime] = None) -> List[Dict]:
        """
        Get economic calendar events (high-impact news)

        Args:
            date: Date to fetch events for (default: today)

        Returns:
            List of economic events
        """
        if date is None:
            date = datetime.now()

        events = []

        # Try to fetch from investing.com API (unofficial)
        try:
            # This is a placeholder - you would need to implement
            # actual calendar fetching from a reliable source
            # Options: Forex Factory, Investing.com, Trading Economics

            # For now, return empty list
            # In production, implement proper calendar integration
            pass

        except Exception as e:
            logger.error(f"Economic calendar fetch error: {str(e)}")

        return events

    def get_market_sentiment_summary(self, news_articles: List[Dict]) -> Dict:
        """
        Generate overall market sentiment summary

        Args:
            news_articles: List of news articles

        Returns:
            Sentiment summary dictionary
        """
        if not news_articles:
            return {
                'overall': 'neutral',
                'score': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'total_count': 0
            }

        sentiments = [article.get('sentiment', 0.0) for article in news_articles]
        avg_sentiment = sum(sentiments) / len(sentiments)

        positive = sum(1 for s in sentiments if s > 0.2)
        negative = sum(1 for s in sentiments if s < -0.2)
        neutral = len(sentiments) - positive - negative

        if avg_sentiment > 0.3:
            overall = 'positive'
        elif avg_sentiment < -0.3:
            overall = 'negative'
        else:
            overall = 'neutral'

        return {
            'overall': overall,
            'score': avg_sentiment,
            'positive_count': positive,
            'negative_count': negative,
            'neutral_count': neutral,
            'total_count': len(news_articles)
        }
