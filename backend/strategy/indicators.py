"""Technical indicators calculator"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Calculates various technical indicators for trading signals
    Includes: RSI, MACD, Bollinger Bands, Moving Averages, ATR, Stochastic, CCI
    """

    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index

        Args:
            data: Price data (usually close prices)
            period: RSI period

        Returns:
            RSI series
        """
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def calculate_macd(
        data: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence)

        Args:
            data: Price data
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_bollinger_bands(
        data: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands

        Args:
            data: Price data
            period: Moving average period
            std_dev: Standard deviation multiplier

        Returns:
            Tuple of (Upper band, Middle band, Lower band)
        """
        middle_band = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()

        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)

        return upper_band, middle_band, lower_band

    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period

        Returns:
            ATR series
        """
        high_low = high - low
        high_close = abs(high - close.shift())
        low_close = abs(low - close.shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)

        atr = true_range.rolling(window=period).mean()

        return atr

    @staticmethod
    def calculate_stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
        smooth_k: int = 3,
        smooth_d: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Calculate Stochastic Oscillator

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Lookback period
            smooth_k: %K smoothing
            smooth_d: %D smoothing

        Returns:
            Tuple of (%K, %D)
        """
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()

        k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        k = k.rolling(window=smooth_k).mean()
        d = k.rolling(window=smooth_d).mean()

        return k, d

    @staticmethod
    def calculate_cci(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 20
    ) -> pd.Series:
        """
        Calculate Commodity Channel Index

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: CCI period

        Returns:
            CCI series
        """
        typical_price = (high + low + close) / 3
        sma = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )

        cci = (typical_price - sma) / (0.015 * mean_deviation)

        return cci

    @staticmethod
    def calculate_adx(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average Directional Index (trend strength)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ADX period

        Returns:
            ADX series
        """
        # Calculate True Range
        high_low = high - low
        high_close = abs(high - close.shift())
        low_close = abs(low - close.shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)

        # Calculate directional movement
        up_move = high - high.shift()
        down_move = low.shift() - low

        pos_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
        neg_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)

        # Smooth the values
        atr = true_range.rolling(window=period).mean()
        pos_di = 100 * (pos_dm.rolling(window=period).mean() / atr)
        neg_di = 100 * (neg_dm.rolling(window=period).mean() / atr)

        # Calculate DX and ADX
        dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
        adx = dx.rolling(window=period).mean()

        return adx

    @staticmethod
    def calculate_ichimoku(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series
    ) -> Dict[str, pd.Series]:
        """
        Calculate Ichimoku Cloud components

        Args:
            high: High prices
            low: Low prices
            close: Close prices

        Returns:
            Dictionary with Ichimoku components
        """
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        period9_high = high.rolling(window=9).max()
        period9_low = low.rolling(window=9).min()
        tenkan_sen = (period9_high + period9_low) / 2

        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        period26_high = high.rolling(window=26).max()
        period26_low = low.rolling(window=26).min()
        kijun_sen = (period26_high + period26_low) / 2

        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)

        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
        period52_high = high.rolling(window=52).max()
        period52_low = low.rolling(window=52).min()
        senkou_span_b = ((period52_high + period52_low) / 2).shift(26)

        # Chikou Span (Lagging Span): Close shifted back 26 periods
        chikou_span = close.shift(-26)

        return {
            'tenkan_sen': tenkan_sen,
            'kijun_sen': kijun_sen,
            'senkou_span_a': senkou_span_a,
            'senkou_span_b': senkou_span_b,
            'chikou_span': chikou_span
        }

    @staticmethod
    def calculate_moving_averages(data: pd.Series, periods: list = [20, 50, 200]) -> Dict[str, pd.Series]:
        """
        Calculate multiple moving averages

        Args:
            data: Price data
            periods: List of MA periods

        Returns:
            Dictionary of moving averages
        """
        mas = {}
        for period in periods:
            mas[f'sma_{period}'] = data.rolling(window=period).mean()
            mas[f'ema_{period}'] = data.ewm(span=period, adjust=False).mean()

        return mas

    @staticmethod
    def calculate_fibonacci_levels(high: float, low: float) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels

        Args:
            high: Highest price in range
            low: Lowest price in range

        Returns:
            Dictionary of Fibonacci levels
        """
        diff = high - low

        levels = {
            '0.0': high,
            '23.6': high - (0.236 * diff),
            '38.2': high - (0.382 * diff),
            '50.0': high - (0.5 * diff),
            '61.8': high - (0.618 * diff),
            '78.6': high - (0.786 * diff),
            '100.0': low,
            '161.8': high + (0.618 * diff),
            '261.8': high + (1.618 * diff)
        }

        return levels

    @staticmethod
    def calculate_pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
        """
        Calculate pivot points and support/resistance levels

        Args:
            high: Previous period high
            low: Previous period low
            close: Previous period close

        Returns:
            Dictionary of pivot levels
        """
        pivot = (high + low + close) / 3

        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)

        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)

        return {
            'pivot': pivot,
            'r1': r1,
            'r2': r2,
            'r3': r3,
            's1': s1,
            's2': s2,
            's3': s3
        }

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> Dict:
        """
        Calculate all technical indicators at once

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)

        Returns:
            Dictionary of all indicators and their signals
        """
        indicators = {}

        try:
            # Ensure we have enough data
            if len(df) < 200:
                logger.warning(f"Insufficient data for indicators: {len(df)} bars")
                return indicators

            close = df['close']
            high = df['high']
            low = df['low']
            open_price = df['open']

            # RSI
            rsi = TechnicalIndicators.calculate_rsi(close)
            indicators['rsi'] = rsi.iloc[-1] if len(rsi) > 0 else 50
            indicators['rsi_signal'] = TechnicalIndicators._rsi_signal(indicators['rsi'])

            # MACD
            macd, signal, histogram = TechnicalIndicators.calculate_macd(close)
            indicators['macd'] = histogram.iloc[-1] if len(histogram) > 0 else 0
            indicators['macd_signal'] = 1 if indicators['macd'] > 0 else -1

            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = TechnicalIndicators.calculate_bollinger_bands(close)
            current_price = close.iloc[-1]
            bb_position = (current_price - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
            indicators['bb_position'] = bb_position
            indicators['bb_signal'] = TechnicalIndicators._bb_signal(bb_position)

            # ATR
            atr = TechnicalIndicators.calculate_atr(high, low, close)
            indicators['atr'] = atr.iloc[-1] if len(atr) > 0 else 0

            # Stochastic
            stoch_k, stoch_d = TechnicalIndicators.calculate_stochastic(high, low, close)
            indicators['stochastic_k'] = stoch_k.iloc[-1] if len(stoch_k) > 0 else 50
            indicators['stochastic_signal'] = TechnicalIndicators._stochastic_signal(
                indicators['stochastic_k']
            )

            # CCI
            cci = TechnicalIndicators.calculate_cci(high, low, close)
            indicators['cci'] = cci.iloc[-1] if len(cci) > 0 else 0
            indicators['cci_signal'] = TechnicalIndicators._cci_signal(indicators['cci'])

            # ADX
            adx = TechnicalIndicators.calculate_adx(high, low, close)
            indicators['adx'] = adx.iloc[-1] if len(adx) > 0 else 0

            # Moving Averages
            mas = TechnicalIndicators.calculate_moving_averages(close)
            for key, value in mas.items():
                if len(value) > 0:
                    indicators[key] = value.iloc[-1]

            # MA trend
            if 'sma_20' in indicators and 'sma_50' in indicators:
                if current_price > indicators['sma_20'] > indicators['sma_50']:
                    indicators['ma_trend'] = 'uptrend'
                    indicators['ma_signal'] = 1
                elif current_price < indicators['sma_20'] < indicators['sma_50']:
                    indicators['ma_trend'] = 'downtrend'
                    indicators['ma_signal'] = -1
                else:
                    indicators['ma_trend'] = 'sideways'
                    indicators['ma_signal'] = 0

            # Pivot Points (using previous day's data)
            if len(df) > 1:
                prev_high = df['high'].iloc[-2]
                prev_low = df['low'].iloc[-2]
                prev_close = df['close'].iloc[-2]
                pivot_levels = TechnicalIndicators.calculate_pivot_points(
                    prev_high, prev_low, prev_close
                )
                indicators['pivot_points'] = pivot_levels

            # Overall signal (combine all)
            signals = [
                indicators.get('rsi_signal', 0),
                indicators.get('macd_signal', 0),
                indicators.get('bb_signal', 0),
                indicators.get('stochastic_signal', 0),
                indicators.get('cci_signal', 0),
                indicators.get('ma_signal', 0)
            ]
            indicators['overall_signal'] = sum(signals) / len(signals)

        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")

        return indicators

    @staticmethod
    def _rsi_signal(rsi: float) -> float:
        """Convert RSI to signal (-1 to 1)"""
        if rsi < 30:
            return 1.0  # Oversold - Buy
        elif rsi > 70:
            return -1.0  # Overbought - Sell
        else:
            return (50 - rsi) / 20  # Gradual signal

    @staticmethod
    def _bb_signal(position: float) -> float:
        """Convert Bollinger Band position to signal"""
        if position < 0.2:
            return 1.0  # Near lower band - Buy
        elif position > 0.8:
            return -1.0  # Near upper band - Sell
        else:
            return (0.5 - position) * 2  # Gradual signal

    @staticmethod
    def _stochastic_signal(value: float) -> float:
        """Convert Stochastic to signal"""
        if value < 20:
            return 1.0  # Oversold
        elif value > 80:
            return -1.0  # Overbought
        else:
            return (50 - value) / 30

    @staticmethod
    def _cci_signal(cci: float) -> float:
        """Convert CCI to signal"""
        if cci < -100:
            return 1.0  # Oversold
        elif cci > 100:
            return -1.0  # Overbought
        else:
            return -cci / 100
