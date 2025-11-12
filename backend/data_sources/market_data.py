"""Market data fetcher for additional data sources"""
import logging
from typing import Optional, Dict, List
import pandas as pd
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MarketDataFetcher:
    """
    Fetches market data from multiple sources
    Provides backup and complementary data to MT5
    """

    def __init__(self, alpha_vantage_key: Optional[str] = None):
        """
        Initialize market data fetcher

        Args:
            alpha_vantage_key: Alpha Vantage API key
        """
        self.alpha_vantage_key = alpha_vantage_key

    def get_forex_data(
        self,
        from_symbol: str,
        to_symbol: str,
        interval: str = "5min"
    ) -> Optional[pd.DataFrame]:
        """
        Get forex data from Alpha Vantage

        Args:
            from_symbol: Base currency (e.g., 'EUR')
            to_symbol: Quote currency (e.g., 'USD')
            interval: Time interval (1min, 5min, 15min, 30min, 60min)

        Returns:
            DataFrame with OHLCV data
        """
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not provided")
            return None

        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "FX_INTRADAY",
                "from_symbol": from_symbol,
                "to_symbol": to_symbol,
                "interval": interval,
                "apikey": self.alpha_vantage_key,
                "outputsize": "compact"
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            # Check for errors
            if "Error Message" in data:
                logger.error(f"Alpha Vantage error: {data['Error Message']}")
                return None

            if "Note" in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                return None

            # Parse time series data
            time_series_key = f"Time Series FX ({interval})"
            if time_series_key not in data:
                logger.error("No time series data in response")
                return None

            time_series = data[time_series_key]

            # Convert to DataFrame
            df_data = []
            for timestamp, values in time_series.items():
                df_data.append({
                    'timestamp': pd.to_datetime(timestamp),
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close'])
                })

            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error fetching forex data: {str(e)}")
            return None

    def get_market_status(self) -> Dict:
        """
        Get current market status (open/closed) for major forex sessions

        Returns:
            Dictionary with session status
        """
        now = datetime.utcnow()
        hour = now.hour
        weekday = now.weekday()

        # Forex market is closed on weekends
        is_weekend = weekday >= 5

        # Trading sessions (UTC times - approximate)
        sessions = {
            'sydney': {'open': 22, 'close': 7, 'active': False},
            'tokyo': {'open': 0, 'close': 9, 'active': False},
            'london': {'open': 8, 'close': 17, 'active': False},
            'new_york': {'open': 13, 'close': 22, 'active': False}
        }

        if not is_weekend:
            # Check which sessions are active
            if 22 <= hour or hour < 7:
                sessions['sydney']['active'] = True
            if 0 <= hour < 9:
                sessions['tokyo']['active'] = True
            if 8 <= hour < 17:
                sessions['london']['active'] = True
            if 13 <= hour < 22:
                sessions['new_york']['active'] = True

        active_sessions = [name for name, data in sessions.items() if data['active']]

        return {
            'is_open': not is_weekend and len(active_sessions) > 0,
            'active_sessions': active_sessions,
            'is_weekend': is_weekend,
            'timestamp': now.isoformat()
        }

    def get_volatility_index(self, symbol: str) -> Optional[float]:
        """
        Get volatility index for symbol
        Higher volatility = higher risk/opportunity

        Args:
            symbol: Trading pair

        Returns:
            Volatility index (0-100)
        """
        # This would typically fetch from a volatility data provider
        # For now, return None as placeholder
        # In production, integrate with actual volatility data source
        return None

    def get_economic_indicators(self, country: str) -> Dict:
        """
        Get economic indicators for a country

        Args:
            country: Country code (e.g., 'US', 'EU', 'GB')

        Returns:
            Dictionary with economic indicators
        """
        indicators = {
            'gdp_growth': None,
            'inflation_rate': None,
            'unemployment_rate': None,
            'interest_rate': None,
            'last_updated': None
        }

        # This would fetch from economic data providers
        # Options: Trading Economics, FRED, World Bank API
        # For now, return placeholder

        return indicators

    def get_correlation_matrix(self, symbols: List[str]) -> Optional[pd.DataFrame]:
        """
        Get correlation matrix for multiple currency pairs

        Args:
            symbols: List of currency pairs

        Returns:
            Correlation matrix DataFrame
        """
        # This would calculate correlations from historical data
        # Useful for portfolio diversification
        # Placeholder for now

        return None

    def get_spread_info(self, symbol: str) -> Optional[Dict]:
        """
        Get typical spread information for a symbol

        Args:
            symbol: Trading pair

        Returns:
            Spread information
        """
        # Typical spreads for major pairs (in pips)
        typical_spreads = {
            'EURUSD': 0.1,
            'GBPUSD': 0.2,
            'USDJPY': 0.1,
            'USDCHF': 0.2,
            'AUDUSD': 0.3,
            'USDCAD': 0.2,
            'NZDUSD': 0.4
        }

        spread = typical_spreads.get(symbol)

        if spread:
            return {
                'symbol': symbol,
                'typical_spread_pips': spread,
                'is_major_pair': True
            }

        return {
            'symbol': symbol,
            'typical_spread_pips': None,
            'is_major_pair': False
        }
