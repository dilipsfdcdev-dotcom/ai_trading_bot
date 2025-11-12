"""Data sources for market data, news, and trends"""
from .news_fetcher import NewsFetcher
from .market_data import MarketDataFetcher

__all__ = ['NewsFetcher', 'MarketDataFetcher']
