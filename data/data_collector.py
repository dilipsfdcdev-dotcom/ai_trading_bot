import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import MetaTrader5 as mt5

class MT5DataCollector:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.demo_mode = True
        self.connected = False
        self.initialize_mt5()
    
    def initialize_mt5(self):
        """Initialize MT5 connection"""
        try:
            if not mt5.initialize():
                self.logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            # Check if we have real credentials
            if (hasattr(self.config, 'MT5_LOGIN') and self.config.MT5_LOGIN and 
                hasattr(self.config, 'MT5_PASSWORD') and self.config.MT5_PASSWORD):
                
                if mt5.login(self.config.MT5_LOGIN, self.config.MT5_PASSWORD, self.config.MT5_SERVER):
                    self.connected = True
                    self.demo_mode = False
                    account = mt5.account_info()
                    self.logger.info(f"✅ REAL MT5 CONNECTED - Balance: ${account.balance:.2f} {account.currency}")
                    return True
                else:
                    self.logger.error(f"MT5 login failed: {mt5.last_error()}")
                    self.demo_mode = True
                    return False
            else:
                self.logger.info("No MT5 credentials - using demo mode")
                self.demo_mode = True
                return True
                
        except Exception as e:
            self.logger.error(f"MT5 error: {e}")
            self.demo_mode = True
            return False
    
    def get_historical_data(self, symbol, timeframe, bars=1000):
        """Get historical data - REAL if connected, demo if not"""
        
        if self.connected and not self.demo_mode:
            return self._get_real_data(symbol, timeframe, bars)
        else:
            return self._get_demo_data(symbol, bars)
    
    def _get_real_data(self, symbol, timeframe, bars):
        """Get REAL data from MT5"""
        try:
            # MT5 timeframe mapping
            mt5_timeframes = {
                1: mt5.TIMEFRAME_M1,
                5: mt5.TIMEFRAME_M5,
                15: mt5.TIMEFRAME_M15,
                30: mt5.TIMEFRAME_M30,
                60: mt5.TIMEFRAME_H1
            }
            
            mt5_tf = mt5_timeframes.get(timeframe, mt5.TIMEFRAME_M5)
            
            # Get real rates from MT5
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, bars)
            
            if rates is None or len(rates) == 0:
                self.logger.error(f"Failed to get real data for {symbol}")
                return self._get_demo_data(symbol, bars)
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Log current live price
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                self.logger.info(f"📊 LIVE {symbol}: ${tick.bid:.2f}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting real data: {e}")
            return self._get_demo_data(symbol, bars)
    
    def _get_demo_data(self, symbol, bars):
        """Get demo data (fallback)"""
        try:
            dates = pd.date_range(end=datetime.now(), periods=bars, freq='5T')
            
            # Use realistic current prices as base
            base_prices = {
                'XAUUSD': 3350,   # Current gold price area
                'BTCUSD': 119500, # Current bitcoin price area
                'EURUSD': 1.17
            }
            base_price = base_prices.get(symbol, 2000)
            
            # Generate realistic movement
            returns = np.random.normal(0, 0.005, bars)  # Lower volatility
            prices = [base_price]
            
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))
            
            data = []
            for i, price in enumerate(prices):
                high = price * (1 + abs(np.random.normal(0, 0.002)))
                low = price * (1 - abs(np.random.normal(0, 0.002)))
                open_price = prices[i-1] if i > 0 else price
                close = price
                volume = np.random.randint(100, 1000)
                
                data.append({
                    'time': dates[i],
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'tick_volume': volume
                })
            
            df = pd.DataFrame(data)
            df.set_index('time', inplace=True)
            
            if self.demo_mode:
                self.logger.info(f"📊 DEMO {symbol}: ${base_price:.2f} (simulated)")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error generating demo data: {e}")
            return None
    
    def get_account_info(self):
        """Get account info"""
        if self.connected and not self.demo_mode:
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
        
        # Return demo account info
        return {
            'balance': 1000000.0,
            'equity': 1000000.0,
            'profit': 0.0,
            'currency': 'INR'
        }
