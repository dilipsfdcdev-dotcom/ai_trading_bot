"""Main strategy engine orchestrating the trading bot"""
import logging
from datetime import datetime
from typing import Optional, Dict, List
import pandas as pd
from ..mt5_connector import MT5Connector, Trade, OrderType, TimeFrame
from ..ai_engine import AIAnalyzer, AnalysisResult
from ..data_sources import NewsFetcher, MarketDataFetcher
from .indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


class StrategyEngine:
    """
    Main strategy engine that coordinates:
    - Data collection (MT5, news, market data)
    - Technical analysis
    - AI/LLM analysis
    - Trade execution
    """

    def __init__(
        self,
        mt5_connector: MT5Connector,
        ai_analyzer: AIAnalyzer,
        news_fetcher: NewsFetcher,
        market_data_fetcher: MarketDataFetcher
    ):
        """
        Initialize strategy engine

        Args:
            mt5_connector: MT5 connector instance
            ai_analyzer: AI analyzer instance
            news_fetcher: News fetcher instance
            market_data_fetcher: Market data fetcher instance
        """
        self.mt5 = mt5_connector
        self.ai = ai_analyzer
        self.news = news_fetcher
        self.market_data = market_data_fetcher
        self.indicators_calc = TechnicalIndicators()

    def analyze_symbol(
        self,
        symbol: str,
        timeframe: TimeFrame = TimeFrame.M15,
        bars: int = 1000
    ) -> Optional[AnalysisResult]:
        """
        Perform complete analysis for a symbol

        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            bars: Number of bars to analyze

        Returns:
            AnalysisResult with trading recommendation
        """
        logger.info(f"Analyzing {symbol} on {timeframe.value}")

        try:
            # Step 1: Get market data from MT5
            market_data = self.mt5.get_market_data(symbol, timeframe, bars)
            if market_data is None or len(market_data) < 200:
                logger.error(f"Insufficient market data for {symbol}")
                return None

            # Step 2: Get current price
            tick = self.mt5.get_tick_data(symbol)
            if tick is None:
                logger.error(f"Failed to get tick data for {symbol}")
                return None

            current_price = tick.bid

            # Step 3: Calculate technical indicators
            technical_signals = self.indicators_calc.calculate_all_indicators(market_data)

            # Step 4: Fetch news
            news_articles = self.news.get_forex_news(symbol, hours_ago=24, max_articles=20)

            # Step 5: Perform AI analysis
            analysis = self.ai.analyze_market(
                symbol=symbol,
                market_data=market_data,
                technical_signals=technical_signals,
                news_data=news_articles,
                current_price=current_price
            )

            logger.info(
                f"Analysis complete for {symbol}: {analysis.final_signal.value} "
                f"(confidence: {analysis.confidence:.2%})"
            )

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {str(e)}")
            return None

    def execute_analysis_trade(
        self,
        analysis: AnalysisResult,
        volume: float,
        risk_manager=None
    ) -> Optional[Trade]:
        """
        Execute a trade based on analysis result

        Args:
            analysis: Analysis result
            volume: Trade volume (lots)
            risk_manager: Risk manager instance (optional)

        Returns:
            Executed trade or None
        """
        if not analysis.should_trade:
            logger.info(f"Analysis for {analysis.symbol} says not to trade")
            return None

        # Check with risk manager if provided
        if risk_manager and not risk_manager.can_open_trade(analysis.symbol):
            logger.info(f"Risk manager blocked trade for {analysis.symbol}")
            return None

        # Determine order type
        if analysis.final_signal.value in ['BUY', 'STRONG_BUY']:
            order_type = OrderType.BUY
        elif analysis.final_signal.value in ['SELL', 'STRONG_SELL']:
            order_type = OrderType.SELL
        else:
            logger.info(f"Neutral signal for {analysis.symbol}, not trading")
            return None

        # Execute trade
        trade = self.mt5.open_trade(
            symbol=analysis.symbol,
            order_type=order_type,
            volume=volume,
            stop_loss=analysis.suggested_stop_loss,
            take_profit=analysis.suggested_take_profit,
            comment=f"AI Bot: {analysis.final_signal.value} @ {analysis.confidence:.0%}",
            magic_number=12345
        )

        if trade:
            logger.info(
                f"Trade executed: {trade.ticket} - {analysis.symbol} "
                f"{order_type.value} {volume} lots"
            )
        else:
            logger.error(f"Failed to execute trade for {analysis.symbol}")

        return trade

    def scan_multiple_symbols(
        self,
        symbols: List[str],
        timeframe: TimeFrame = TimeFrame.M15
    ) -> Dict[str, AnalysisResult]:
        """
        Scan multiple symbols and return analyses

        Args:
            symbols: List of trading symbols
            timeframe: Chart timeframe

        Returns:
            Dictionary of symbol -> AnalysisResult
        """
        results = {}

        for symbol in symbols:
            try:
                analysis = self.analyze_symbol(symbol, timeframe)
                if analysis:
                    results[symbol] = analysis
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {str(e)}")
                continue

        return results

    def get_best_trading_opportunity(
        self,
        analyses: Dict[str, AnalysisResult]
    ) -> Optional[AnalysisResult]:
        """
        Find the best trading opportunity from multiple analyses

        Args:
            analyses: Dictionary of analyses

        Returns:
            Best analysis or None
        """
        tradeable = [
            (symbol, analysis)
            for symbol, analysis in analyses.items()
            if analysis.should_trade
        ]

        if not tradeable:
            return None

        # Sort by confidence
        tradeable.sort(key=lambda x: x[1].confidence, reverse=True)

        return tradeable[0][1]
