"""
Live Data Module

Real-time data streaming and aggregation:
- Market data streams
- News aggregation
- Sentiment analysis
"""

from .stream_manager import LiveDataStreamManager
from .news_aggregator import RealTimeNewsAggregator
from .sentiment_analyzer import LiveSentimentAnalyzer

__all__ = [
    'LiveDataStreamManager',
    'RealTimeNewsAggregator',
    'LiveSentimentAnalyzer'
]
