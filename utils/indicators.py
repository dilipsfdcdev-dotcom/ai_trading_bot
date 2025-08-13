import pandas as pd
import numpy as np

class TechnicalIndicators:
    def __init__(self):
        pass
    
    def add_all_indicators(self, df):
        """Add all technical indicators to dataframe"""
        if df is None or len(df) < 50:
            return df
        
        try:
            df = df.copy()
            
            # Ensure we have OHLCV data
            required_cols = ['open', 'high', 'low', 'close']
            if not all(col in df.columns for col in required_cols):
                return df
            
            # Price-based indicators
            df = self.add_moving_averages(df)
            df = self.add_rsi(df)
            df = self.add_macd(df)
            df = self.add_bollinger_bands(df)
            df = self.add_stochastic(df)
            df = self.add_atr(df)
            df = self.add_williams_r(df)
            df = self.add_cci(df)
            df = self.add_momentum_indicators(df)
            df = self.add_volume_indicators(df)
            
            # Price action indicators
            df = self.add_price_action_features(df)
            
            # Fill NaN values
            df = df.fillna(method='bfill').fillna(method='ffill')
            
            return df
            
        except Exception as e:
            print(f"Error adding indicators: {e}")
            return df
    
    def add_moving_averages(self, df):
        """Add moving averages"""
        try:
            df['sma_5'] = df['close'].rolling(window=5, min_periods=1).mean()
            df['sma_10'] = df['close'].rolling(window=10, min_periods=1).mean()
            df['sma_20'] = df['close'].rolling(window=20, min_periods=1).mean()
            df['sma_50'] = df['close'].rolling(window=50, min_periods=1).mean()
            df['sma_100'] = df['close'].rolling(window=100, min_periods=1).mean()
            
            df['ema_5'] = df['close'].ewm(span=5, adjust=False).mean()
            df['ema_10'] = df['close'].ewm(span=10, adjust=False).mean()
            df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
            df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
            
            # MA crosses and slopes
            df['sma_20_slope'] = df['sma_20'].diff(5)
            df['ema_cross'] = np.where(df['ema_10'] > df['ema_20'], 1, -1)
            df['price_above_sma20'] = np.where(df['close'] > df['sma_20'], 1, 0)
        except Exception as e:
            print(f"Error in moving averages: {e}")
        
        return df
    
    def add_rsi(self, df, period=14):
        """Add RSI indicators"""
        try:
            df['rsi_14'] = self.calculate_rsi(df['close'], 14)
            df['rsi_7'] = self.calculate_rsi(df['close'], 7)
            df['rsi_21'] = self.calculate_rsi(df['close'], 21)
            
            # RSI conditions
            df['rsi_oversold'] = np.where(df['rsi_14'] < 30, 1, 0)
            df['rsi_overbought'] = np.where(df['rsi_14'] > 70, 1, 0)
            df['rsi_bullish_div'] = self.detect_rsi_divergence(df, 'bullish')
            df['rsi_bearish_div'] = self.detect_rsi_divergence(df, 'bearish')
        except Exception as e:
            print(f"Error in RSI: {e}")
        
        return df
    
    def add_macd(self, df):
        """Add MACD indicators"""
        try:
            ema_12 = df['close'].ewm(span=12, adjust=False).mean()
            ema_26 = df['close'].ewm(span=26, adjust=False).mean()
            
            df['macd'] = ema_12 - ema_26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # MACD conditions
            df['macd_bullish'] = np.where(df['macd'] > df['macd_signal'], 1, 0)
            df['macd_cross_up'] = np.where(
                (df['macd'] > df['macd_signal']) & 
                (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 1, 0
            )
            df['macd_cross_down'] = np.where(
                (df['macd'] < df['macd_signal']) & 
                (df['macd'].shift(1) >= df['macd_signal'].shift(1)), 1, 0
            )
        except Exception as e:
            print(f"Error in MACD: {e}")
        
        return df
    
    def add_bollinger_bands(self, df, period=20, std_dev=2):
        """Add Bollinger Bands"""
        try:
            df['bb_middle'] = df['close'].rolling(window=period, min_periods=1).mean()
            bb_std = df['close'].rolling(window=period, min_periods=1).std()
            
            df['bb_upper'] = df['bb_middle'] + (bb_std * std_dev)
            df['bb_lower'] = df['bb_middle'] - (bb_std * std_dev)
            
            # BB position and squeeze
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            df['bb_squeeze'] = np.where(
                df['bb_width'] < df['bb_width'].rolling(20, min_periods=1).mean() * 0.8, 1, 0
            )
        except Exception as e:
            print(f"Error in Bollinger Bands: {e}")
        
        return df
    
    def add_stochastic(self, df, k_period=14, d_period=3):
        """Add Stochastic Oscillator"""
        try:
            df['stoch_k'] = self.calculate_stochastic_k(df, k_period)
            df['stoch_d'] = df['stoch_k'].rolling(window=d_period, min_periods=1).mean()
            
            # Stochastic conditions
            df['stoch_oversold'] = np.where(df['stoch_k'] < 20, 1, 0)
            df['stoch_overbought'] = np.where(df['stoch_k'] > 80, 1, 0)
            df['stoch_bullish'] = np.where(df['stoch_k'] > df['stoch_d'], 1, 0)
        except Exception as e:
            print(f"Error in Stochastic: {e}")
        
        return df
    
    def add_atr(self, df, period=14):
        """Add Average True Range"""
        try:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            df['atr'] = true_range.rolling(window=period, min_periods=1).mean()
            df['atr_percent'] = (df['atr'] / df['close']) * 100
            
            # Volatility conditions
            atr_mean = df['atr_percent'].rolling(50, min_periods=1).mean()
            df['high_volatility'] = np.where(df['atr_percent'] > atr_mean * 1.5, 1, 0)
            df['low_volatility'] = np.where(df['atr_percent'] < atr_mean * 0.5, 1, 0)
        except Exception as e:
            print(f"Error in ATR: {e}")
        
        return df
    
    def add_williams_r(self, df, period=14):
        """Add Williams %R"""
        try:
            highest_high = df['high'].rolling(window=period, min_periods=1).max()
            lowest_low = df['low'].rolling(window=period, min_periods=1).min()
            
            df['williams_r'] = -100 * (highest_high - df['close']) / (highest_high - lowest_low)
            
            # Williams %R conditions
            df['williams_oversold'] = np.where(df['williams_r'] < -80, 1, 0)
            df['williams_overbought'] = np.where(df['williams_r'] > -20, 1, 0)
        except Exception as e:
            print(f"Error in Williams %R: {e}")
        
        return df
    
    def add_cci(self, df, period=14):
        """Add Commodity Channel Index"""
        try:
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            sma_tp = typical_price.rolling(window=period, min_periods=1).mean()
            
            # Calculate mean absolute deviation
            mad = typical_price.rolling(window=period, min_periods=1).apply(
                lambda x: np.mean(np.abs(x - x.mean())), raw=True
            )
            
            df['cci'] = (typical_price - sma_tp) / (0.015 * mad)
            
            # CCI conditions
            df['cci_bullish'] = np.where(df['cci'] > 100, 1, 0)
            df['cci_bearish'] = np.where(df['cci'] < -100, 1, 0)
        except Exception as e:
            print(f"Error in CCI: {e}")
        
        return df
    
    def add_momentum_indicators(self, df):
        """Add momentum indicators"""
        try:
            # Rate of Change
            df['roc_5'] = ((df['close'] - df['close'].shift(5)) / df['close'].shift(5)) * 100
            df['roc_10'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
            
            # Price momentum
            df['momentum_5'] = df['close'] / df['close'].shift(5)
            df['momentum_10'] = df['close'] / df['close'].shift(10)
            
            # Returns
            df['return_1'] = df['close'].pct_change(1)
            df['return_5'] = df['close'].pct_change(5)
            df['return_10'] = df['close'].pct_change(10)
            
            # Momentum oscillator
            df['momentum_oscillator'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
        except Exception as e:
            print(f"Error in momentum indicators: {e}")
        
        return df
    
    def add_volume_indicators(self, df):
        """Add volume indicators if volume data available"""
        try:
            if 'tick_volume' in df.columns:
                vol_col = 'tick_volume'
            elif 'real_volume' in df.columns:
                vol_col = 'real_volume'
            else:
                # Create synthetic volume based on price action
                df['volume'] = (df['high'] - df['low']) * 1000
                vol_col = 'volume'
            
            # Volume moving averages
            df['vol_sma_10'] = df[vol_col].rolling(window=10, min_periods=1).mean()
            df['vol_sma_20'] = df[vol_col].rolling(window=20, min_periods=1).mean()
            
            # Volume conditions
            df['volume_spike'] = np.where(df[vol_col] > df['vol_sma_20'] * 2, 1, 0)
            df['volume_low'] = np.where(df[vol_col] < df['vol_sma_20'] * 0.5, 1, 0)
            
            # On Balance Volume (simplified)
            price_change = np.where(df['close'] > df['close'].shift(1), df[vol_col], 
                                  np.where(df['close'] < df['close'].shift(1), -df[vol_col], 0))
            df['obv'] = price_change.cumsum()
        except Exception as e:
            print(f"Error in volume indicators: {e}")
        
        return df
    
    def add_price_action_features(self, df):
        """Add price action features"""
        try:
            # Candle patterns
            body_size = np.abs(df['close'] - df['open'])
            candle_range = df['high'] - df['low']
            
            df['doji'] = np.where(body_size < candle_range * 0.1, 1, 0)
            df['hammer'] = self.detect_hammer(df)
            df['shooting_star'] = self.detect_shooting_star(df)
            
            # Price levels
            df['daily_range'] = df['high'] - df['low']
            df['body_size'] = body_size
            df['upper_shadow'] = df['high'] - np.maximum(df['open'], df['close'])
            df['lower_shadow'] = np.minimum(df['open'], df['close']) - df['low']
            
            # Gap detection
            df['gap_up'] = np.where(df['low'] > df['high'].shift(1), 1, 0)
            df['gap_down'] = np.where(df['high'] < df['low'].shift(1), 1, 0)
            
            # Support/Resistance levels (simplified)
            df['local_high'] = (df['high'].rolling(5, center=True, min_periods=1).max() == df['high']).astype(int)
            df['local_low'] = (df['low'].rolling(5, center=True, min_periods=1).min() == df['low']).astype(int)
            
            # Price position in range
            df['price_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        except Exception as e:
            print(f"Error in price action features: {e}")
        
        return df
    
    def calculate_rsi(self, prices, period=14):
        """Calculate RSI manually"""
        try:
            delta = prices.diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=period, min_periods=1).mean()
            avg_loss = loss.rolling(window=period, min_periods=1).mean()
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.fillna(50)  # Fill NaN with neutral RSI
        except Exception as e:
            print(f"Error calculating RSI: {e}")
            return pd.Series([50] * len(prices), index=prices.index)
    
    def calculate_stochastic_k(self, df, period=14):
        """Calculate Stochastic %K"""
        try:
            lowest_low = df['low'].rolling(window=period, min_periods=1).min()
            highest_high = df['high'].rolling(window=period, min_periods=1).max()
            
            k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
            return k_percent.fillna(50)
        except Exception as e:
            print(f"Error calculating Stochastic: {e}")
            return pd.Series([50] * len(df), index=df.index)
    
    def detect_rsi_divergence(self, df, div_type='bullish'):
        """Detect RSI divergence (simplified)"""
        try:
            if len(df) < 20:
                return np.zeros(len(df))
            
            if div_type == 'bullish':
                # Price making lower lows, RSI making higher lows
                price_condition = df['low'] < df['low'].shift(10)
                rsi_condition = df['rsi_14'] > df['rsi_14'].shift(10)
                return np.where(price_condition & rsi_condition, 1, 0)
            else:
                # Price making higher highs, RSI making lower highs
                price_condition = df['high'] > df['high'].shift(10)
                rsi_condition = df['rsi_14'] < df['rsi_14'].shift(10)
                return np.where(price_condition & rsi_condition, 1, 0)
        except Exception as e:
            print(f"Error detecting RSI divergence: {e}")
            return np.zeros(len(df))
    
    def detect_hammer(self, df):
        """Detect hammer candlestick pattern"""
        try:
            body = np.abs(df['close'] - df['open'])
            lower_shadow = np.minimum(df['open'], df['close']) - df['low']
            upper_shadow = df['high'] - np.maximum(df['open'], df['close'])
            
            hammer_condition = (
                (lower_shadow > body * 2) &  # Long lower shadow
                (upper_shadow < body * 0.5) &  # Short upper shadow
                (body > 0)  # Has a body
            )
            
            return np.where(hammer_condition, 1, 0)
        except Exception as e:
            print(f"Error detecting hammer: {e}")
            return np.zeros(len(df))
    
    def detect_shooting_star(self, df):
        """Detect shooting star candlestick pattern"""
        try:
            body = np.abs(df['close'] - df['open'])
            lower_shadow = np.minimum(df['open'], df['close']) - df['low']
            upper_shadow = df['high'] - np.maximum(df['open'], df['close'])
            
            star_condition = (
                (upper_shadow > body * 2) &  # Long upper shadow
                (lower_shadow < body * 0.5) &  # Short lower shadow
                (body > 0)  # Has a body
            )
            
            return np.where(star_condition, 1, 0)
        except Exception as e:
            print(f"Error detecting shooting star: {e}")
            return np.zeros(len(df))
    
    def add_trend_indicators(self, df):
        """Add trend detection indicators"""
        try:
            # Simple trend detection
            df['trend_5'] = np.where(df['close'] > df['close'].shift(5), 1, -1)
            df['trend_10'] = np.where(df['close'] > df['close'].shift(10), 1, -1)
            df['trend_20'] = np.where(df['close'] > df['close'].shift(20), 1, -1)
            
            # Moving average trend
            df['ma_trend'] = np.where(df['sma_10'] > df['sma_20'], 1, -1)
            
            # Price vs MA trend
            df['price_vs_ma'] = np.where(df['close'] > df['sma_20'], 1, -1)
        except Exception as e:
            print(f"Error in trend indicators: {e}")
        
        return df