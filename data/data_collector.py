import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time

# Try to import MetaTrader5, but don't fail if not available
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    print("⚠️  MetaTrader5 not available - running in demo mode")
    MT5_AVAILABLE = False

class MT5DataCollector:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.demo_mode = True
        self.connected = False
        
        if MT5_AVAILABLE:
            self.initialize_mt5()
        else:
            self.logger.info("📊 Running in demo mode - MT5 not available")
    
    def initialize_mt5(self):
        """Initialize MT5 connection"""
        if not MT5_AVAILABLE:
            return False
            
        try:
            if not mt5.initialize():
                self.demo_mode = True
                return False
            
            # Check credentials
            if (hasattr(self.config, 'MT5_LOGIN') and self.config.MT5_LOGIN and 
                hasattr(self.config, 'MT5_PASSWORD') and self.config.MT5_PASSWORD):
                
                if mt5.login(self.config.MT5_LOGIN, self.config.MT5_PASSWORD, self.config.MT5_SERVER):
                    self.connected = True
                    self.demo_mode = False
                    self.logger.info("✅ MT5 Connected")
                    return True
            
            self.demo_mode = True
            return True
            
        except Exception as e:
            self.logger.error(f"MT5 error: {e}")
            self.demo_mode = True
            return False
    
    def get_historical_data(self, symbol, timeframe, bars=1000):
        """Get historical data"""
        
        if self.connected and not self.demo_mode and MT5_AVAILABLE:
            return self._get_real_data(symbol, timeframe, bars)
        else:
            return self._get_demo_data(symbol, bars)
    
    def _get_real_data(self, symbol, timeframe, bars):
        """Get real data from MT5"""
        try:
            mt5_timeframes = {
                1: mt5.TIMEFRAME_M1,
                5: mt5.TIMEFRAME_M5,
                15: mt5.TIMEFRAME_M15,
                30: mt5.TIMEFRAME_M30,
                60: mt5.TIMEFRAME_H1
            }
            
            mt5_tf = mt5_timeframes.get(timeframe, mt5.TIMEFRAME_M5)
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, bars)
            
            if rates is None or len(rates) == 0:
                return self._get_demo_data(symbol, bars)
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting real data: {e}")
            return self._get_demo_data(symbol, bars)
    
    def _get_demo_data(self, symbol, bars):
        """Generate demo data"""
        try:
            dates = pd.date_range(end=datetime.now(), periods=bars, freq='5T')
            
            # Realistic base prices
            base_prices = {
                'XAUUSD': 2650.0,
                'BTCUSD': 96000.0,
                'EURUSD': 1.0450
            }
            
            base_price = base_prices.get(symbol, 1.0000)
            
            # Generate price movement
            np.random.seed(int(time.time()) % 1000)
            returns = np.random.normal(0.0001, 0.005, bars)
            prices = [base_price]
            
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))
            
            data = []
            for i, price in enumerate(prices):
                high = price * (1 + abs(np.random.normal(0, 0.002)))
                low = price * (1 - abs(np.random.normal(0, 0.002)))
                open_price = prices[i-1] if i > 0 else price
                close = price
                
                high = max(high, open_price, close)
                low = min(low, open_price, close)
                
                data.append({
                    'time': dates[i],
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'tick_volume': np.random.randint(100, 1000),
                    'real_volume': 0
                })
            
            df = pd.DataFrame(data)
            df.set_index('time', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error generating demo data: {e}")
            return None
    
    def get_account_info(self):
        """Get account info"""
        if self.connected and not self.demo_mode and MT5_AVAILABLE:
            try:
                account = mt5.account_info()
                if account:
                    return {
                        'balance': account.balance,
                        'equity': account.equity,
                        'profit': account.profit,
                        'currency': account.currency
                    }
            except:
                pass
        
        # Demo account
        return {
            'balance': 100000.0,
            'equity': 100000.0 + np.random.uniform(-1000, 1000),
            'profit': np.random.uniform(-500, 500),
            'currency': 'USD'
        }
