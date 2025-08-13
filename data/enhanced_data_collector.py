import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import MetaTrader5 as mt5
import time

class EnhancedMT5DataCollector:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.demo_mode = True
        self.connected = False
        self.last_data_cache = {}
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        
        self.initialize_mt5()
    
    def initialize_mt5(self):
        """Initialize MT5 connection with enhanced error handling"""
        try:
            # Check if MT5 path is provided
            if hasattr(self.config, 'MT5_PATH') and self.config.MT5_PATH:
                if not mt5.initialize(path=self.config.MT5_PATH):
                    self.logger.warning(f"Failed to initialize MT5 with path: {self.config.MT5_PATH}")
                    if not mt5.initialize():
                        self.logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                        return False
            else:
                if not mt5.initialize():
                    self.logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                    return False
            
            self.logger.info("✅ MT5 Terminal initialized successfully")
            
            # Try to login if credentials are provided
            if (hasattr(self.config, 'MT5_LOGIN') and self.config.MT5_LOGIN and 
                hasattr(self.config, 'MT5_PASSWORD') and self.config.MT5_PASSWORD and
                hasattr(self.config, 'MT5_SERVER') and self.config.MT5_SERVER):
                
                return self.attempt_login()
            else:
                self.logger.info("ℹ️  No MT5 credentials provided - checking existing connection")
                # Check if already logged in
                account = mt5.account_info()
                if account:
                    self.connected = True
                    self.demo_mode = False
                    self.logger.info(f"✅ Already connected to MT5 - Account: {account.login}")
                    self.logger.info(f"💰 Balance: ${account.balance:.2f} {account.currency}")
                    return True
                else:
                    self.logger.info("📊 No active MT5 connection - using demo mode")
                    self.demo_mode = True
                    return True
                
        except Exception as e:
            self.logger.error(f"MT5 initialization error: {e}")
            self.demo_mode = True
            return False
    
    def attempt_login(self):
        """Attempt to login to MT5"""
        self.connection_attempts += 1
        
        try:
            if mt5.login(self.config.MT5_LOGIN, self.config.MT5_PASSWORD, self.config.MT5_SERVER):
                self.connected = True
                self.demo_mode = False
                account = mt5.account_info()
                
                self.logger.info("🎉 MT5 LOGIN SUCCESSFUL!")
                self.logger.info(f"👤 Account: {account.login}")
                self.logger.info(f"🏦 Server: {account.server}")
                self.logger.info(f"💰 Balance: ${account.balance:.2f} {account.currency}")
                self.logger.info(f"📊 Equity: ${account.equity:.2f}")
                self.logger.info(f"🎯 Account Type: {'Demo' if account.trade_mode == 1 else 'Real'}")
                
                return True
            else:
                error = mt5.last_error()
                self.logger.error(f"❌ MT5 login failed: {error}")
                
                if self.connection_attempts < self.max_connection_attempts:
                    self.logger.info(f"🔄 Retrying connection... (Attempt {self.connection_attempts + 1}/{self.max_connection_attempts})")
                    time.sleep(2)
                    return self.attempt_login()
                else:
                    self.logger.warning("⚠️  Max connection attempts reached - switching to demo mode")
                    self.demo_mode = True
                    return False
                    
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            self.demo_mode = True
            return False
    
    def get_historical_data(self, symbol, timeframe, bars=1000):
        """Get historical data with enhanced caching and error handling"""
        
        if self.connected and not self.demo_mode:
            return self._get_real_data(symbol, timeframe, bars)
        else:
            return self._get_demo_data(symbol, bars)
    
    def _get_real_data(self, symbol, timeframe, bars):
        """Get REAL data from MT5 with enhanced features"""
        try:
            # MT5 timeframe mapping
            mt5_timeframes = {
                1: mt5.TIMEFRAME_M1,
                5: mt5.TIMEFRAME_M5,
                15: mt5.TIMEFRAME_M15,
                30: mt5.TIMEFRAME_M30,
                60: mt5.TIMEFRAME_H1,
                240: mt5.TIMEFRAME_H4,
                1440: mt5.TIMEFRAME_D1
            }
            
            mt5_tf = mt5_timeframes.get(timeframe, mt5.TIMEFRAME_M5)
            
            # Check symbol availability
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                self.logger.error(f"Symbol {symbol} not available")
                return self._get_demo_data(symbol, bars)
            
            # Ensure symbol is visible in MarketWatch
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    self.logger.error(f"Failed to select symbol {symbol}")
                    return self._get_demo_data(symbol, bars)
            
            # Get real rates from MT5
            rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, bars)
            
            if rates is None or len(rates) == 0:
                self.logger.error(f"Failed to get real data for {symbol}")
                return self._get_demo_data(symbol, bars)
            
            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            # Add spread information
            df['spread'] = symbol_info.spread
            
            # Get current live tick
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                self.logger.info(f"📊 LIVE {symbol}: Bid=${tick.bid:.2f} Ask=${tick.ask:.2f} "
                               f"Spread={tick.ask-tick.bid:.5f}")
                
                # Update cache
                self.last_data_cache[symbol] = {
                    'data': df,
                    'timestamp': datetime.now(),
                    'current_price': tick.bid
                }
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting real data for {symbol}: {e}")
            return self._get_demo_data(symbol, bars)
    
    def _get_demo_data(self, symbol, bars):
        """Generate realistic demo data"""
        try:
            # Check cache first
            if symbol in self.last_data_cache:
                cache_age = datetime.now() - self.last_data_cache[symbol]['timestamp']
                if cache_age.total_seconds() < 300:  # Use cache if less than 5 minutes old
                    cached_data = self.last_data_cache[symbol]['data']
                    if len(cached_data) >= bars:
                        self.logger.info(f"📊 Using cached demo data for {symbol}")
                        return cached_data.tail(bars)
            
            dates = pd.date_range(end=datetime.now(), periods=bars, freq='5T')
            
            # Use realistic current prices as base
            base_prices = {
                'XAUUSD': 2650.0,   # Current gold price area
                'BTCUSD': 96000.0,  # Current bitcoin price area  
                'EURUSD': 1.0450,   # Current EUR/USD
                'GBPUSD': 1.2750,   # Current GBP/USD
                'USDJPY': 151.20,   # Current USD/JPY
                'AUDUSD': 0.6420,   # Current AUD/USD
                'USDCAD': 1.4250,   # Current USD/CAD
                'USDCHF': 0.8820    # Current USD/CHF
            }
            
            base_price = base_prices.get(symbol, 1.0000)
            
            # Symbol-specific volatility
            volatilities = {
                'XAUUSD': 0.008,    # 0.8% volatility for gold
                'BTCUSD': 0.025,    # 2.5% volatility for bitcoin
                'EURUSD': 0.003,    # 0.3% volatility for major pairs
                'GBPUSD': 0.004,    # 0.4% volatility
                'USDJPY': 0.003,    # 0.3% volatility
                'AUDUSD': 0.005,    # 0.5% volatility
                'USDCAD': 0.004,    # 0.4% volatility
                'USDCHF': 0.003     # 0.3% volatility
            }
            
            volatility = volatilities.get(symbol, 0.005)
            
            # Generate realistic movement with trend
            np.random.seed(int(time.time()) % 1000)  # Different seed each time
            returns = np.random.normal(0.0001, volatility, bars)  # Slight upward bias
            
            # Add some trending behavior
            trend_strength = np.random.choice([-1, 0, 1], p=[0.3, 0.4, 0.3])
            if trend_strength != 0:
                trend = np.linspace(0, trend_strength * 0.01, bars)
                returns += trend
            
            prices = [base_price]
            
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))
            
            data = []
            for i, price in enumerate(prices):
                # Realistic OHLC generation
                volatility_factor = abs(np.random.normal(0, volatility * 0.5))
                high = price * (1 + volatility_factor)
                low = price * (1 - volatility_factor)
                open_price = prices[i-1] if i > 0 else price
                close = price
                
                # Ensure OHLC consistency
                high = max(high, open_price, close)
                low = min(low, open_price, close)
                
                # Generate realistic volume
                volume = np.random.randint(50, 500)
                
                # Add realistic spread
                spread = {
                    'XAUUSD': 0.5,
                    'BTCUSD': 10.0,
                    'EURUSD': 0.00015,
                    'GBPUSD': 0.00020,
                    'USDJPY': 0.015,
                    'AUDUSD': 0.00025,
                    'USDCAD': 0.00025,
                    'USDCHF': 0.00020
                }.get(symbol, 0.0001)
                
                data.append({
                    'time': dates[i],
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'tick_volume': volume,
                    'spread': spread,
                    'real_volume': 0
                })
            
            df = pd.DataFrame(data)
            df.set_index('time', inplace=True)
            
            # Cache the data
            self.last_data_cache[symbol] = {
                'data': df,
                'timestamp': datetime.now(),
                'current_price': base_price
            }
            
            if self.demo_mode:
                self.logger.info(f"📊 DEMO {symbol}: ${base_price:.2f} (simulated with trend)")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error generating demo data for {symbol}: {e}")
            return None
    
    def get_account_info(self):
        """Get account info with enhanced details"""
        if self.connected and not self.demo_mode:
            try:
                account = mt5.account_info()
                if account:
                    return {
                        'balance': account.balance,
                        'equity': account.equity,
                        'profit': account.profit,
                        'margin': account.margin,
                        'margin_free': account.margin_free,
                        'margin_level': account.margin_level if account.margin > 0 else 0,
                        'currency': account.currency,
                        'login': account.login,
                        'server': account.server,
                        'leverage': account.leverage,
                        'trade_mode': account.trade_mode  # 0=Demo, 1=Real
                    }
            except Exception as e:
                self.logger.error(f"Error getting account info: {e}")
        
        # Return demo account info
        demo_balance = 100000.0
        demo_profit = np.random.uniform(-500, 500)  # Random P&L for demo
        
        return {
            'balance': demo_balance,
            'equity': demo_balance + demo_profit,
            'profit': demo_profit,
            'margin': 0.0,
            'margin_free': demo_balance,
            'margin_level': 0.0,
            'currency': 'USD',
            'login': 999999999,
            'server': 'Demo-Server',
            'leverage': 1000,
            'trade_mode': 0  # Demo
        }
    
    def get_positions(self):
        """Get current positions"""
        if self.connected and not self.demo_mode:
            try:
                positions = mt5.positions_get()
                return positions if positions else []
            except Exception as e:
                self.logger.error(f"Error getting positions: {e}")
        
        return []  # No positions in demo mode
    
    def get_symbol_info(self, symbol):
        """Get detailed symbol information"""
        if self.connected and not self.demo_mode:
            try:
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info:
                    return {
                        'symbol': symbol_info.name,
                        'description': symbol_info.description,
                        'point': symbol_info.point,
                        'digits': symbol_info.digits,
                        'spread': symbol_info.spread,
                        'trade_mode': symbol_info.trade_mode,
                        'volume_min': symbol_info.volume_min,
                        'volume_max': symbol_info.volume_max,
                        'volume_step': symbol_info.volume_step,
                        'margin_initial': symbol_info.margin_initial,
                        'margin_maintenance': symbol_info.margin_maintenance,
                        'contract_size': symbol_info.trade_contract_size,
                        'currency_base': symbol_info.currency_base,
                        'currency_profit': symbol_info.currency_profit,
                        'currency_margin': symbol_info.currency_margin
                    }
            except Exception as e:
                self.logger.error(f"Error getting symbol info for {symbol}: {e}")
        
        # Return demo symbol info
        demo_info = {
            'XAUUSD': {
                'symbol': 'XAUUSD',
                'description': 'Gold vs US Dollar',
                'point': 0.01,
                'digits': 2,
                'spread': 5,
                'trade_mode': 4,
                'volume_min': 0.01,
                'volume_max': 100.0,
                'volume_step': 0.01,
                'margin_initial': 1000.0,
                'margin_maintenance': 1000.0,
                'contract_size': 100.0,
                'currency_base': 'XAU',
                'currency_profit': 'USD',
                'currency_margin': 'USD'
            },
            'BTCUSD': {
                'symbol': 'BTCUSD',
                'description': 'Bitcoin vs US Dollar',
                'point': 0.01,
                'digits': 2,
                'spread': 100,
                'trade_mode': 4,
                'volume_min': 0.01,
                'volume_max': 10.0,
                'volume_step': 0.01,
                'margin_initial': 5000.0,
                'margin_maintenance': 5000.0,
                'contract_size': 1.0,
                'currency_base': 'BTC',
                'currency_profit': 'USD',
                'currency_margin': 'USD'
            }
        }
        
        return demo_info.get(symbol, demo_info['XAUUSD'])
    
    def get_current_tick(self, symbol):
        """Get current tick data"""
        if self.connected and not self.demo_mode:
            try:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    return {
                        'symbol': symbol,
                        'bid': tick.bid,
                        'ask': tick.ask,
                        'last': tick.last,
                        'volume': tick.volume,
                        'time': datetime.fromtimestamp(tick.time),
                        'spread': tick.ask - tick.bid
                    }
            except Exception as e:
                self.logger.error(f"Error getting tick for {symbol}: {e}")
        
        # Return demo tick data
        if symbol in self.last_data_cache:
            base_price = self.last_data_cache[symbol]['current_price']
        else:
            base_prices = {
                'XAUUSD': 2650.0,
                'BTCUSD': 96000.0,
                'EURUSD': 1.0450
            }
            base_price = base_prices.get(symbol, 1.0000)
        
        spread = 0.5 if symbol == 'XAUUSD' else 10.0 if symbol == 'BTCUSD' else 0.00015
        
        return {
            'symbol': symbol,
            'bid': base_price,
            'ask': base_price + spread,
            'last': base_price,
            'volume': np.random.randint(100, 1000),
            'time': datetime.now(),
            'spread': spread
        }
    
    def check_market_hours(self, symbol=None):
        """Check if market is open for trading"""
        if self.connected and not self.demo_mode:
            try:
                if symbol:
                    symbol_info = mt5.symbol_info(symbol)
                    if symbol_info:
                        return symbol_info.trade_mode in [3, 4]  # Full or Close Only
                
                # General market check
                current_time = datetime.now()
                # Simple check - assume forex market (24/5)
                weekday = current_time.weekday()
                return weekday < 5  # Monday=0 to Friday=4
                
            except Exception as e:
                self.logger.error(f"Error checking market hours: {e}")
        
        # Demo mode - always open
        return True
    
    def get_market_info(self):
        """Get general market information"""
        try:
            info = {
                'symbols_total': 0,
                'symbols_available': [],
                'server_time': datetime.now(),
                'trade_allowed': True,
                'expert_allowed': True
            }
            
            if self.connected and not self.demo_mode:
                # Get available symbols
                symbols = mt5.symbols_get()
                if symbols:
                    info['symbols_total'] = len(symbols)
                    info['symbols_available'] = [s.name for s in symbols[:20]]  # First 20
                
                # Check trading permissions
                account = mt5.account_info()
                if account:
                    info['trade_allowed'] = account.trade_allowed
                    info['expert_allowed'] = account.trade_expert
            else:
                # Demo info
                info['symbols_available'] = ['XAUUSD', 'BTCUSD', 'EURUSD', 'GBPUSD', 'USDJPY']
                info['symbols_total'] = len(info['symbols_available'])
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting market info: {e}")
            return {
                'symbols_total': 0,
                'symbols_available': [],
                'server_time': datetime.now(),
                'trade_allowed': False,
                'expert_allowed': False
            }
    
    def reconnect(self):
        """Attempt to reconnect to MT5"""
        self.logger.info("🔄 Attempting to reconnect to MT5...")
        self.connected = False
        self.connection_attempts = 0
        
        # Shutdown current connection
        try:
            mt5.shutdown()
        except:
            pass
        
        # Reinitialize
        return self.initialize_mt5()
    
    def get_connection_status(self):
        """Get detailed connection status"""
        status = {
            'connected': self.connected,
            'demo_mode': self.demo_mode,
            'connection_attempts': self.connection_attempts,
            'last_error': None,
            'terminal_info': None,
            'account_info': None
        }
        
        try:
            if self.connected:
                # Get terminal info
                terminal = mt5.terminal_info()
                if terminal:
                    status['terminal_info'] = {
                        'version': terminal.version,
                        'build': terminal.build,
                        'connected': terminal.connected,
                        'trade_allowed': terminal.trade_allowed,
                        'expert_allowed': terminal.tradeapi_disabled == False
                    }
                
                # Get account info
                account = mt5.account_info()
                if account:
                    status['account_info'] = {
                        'login': account.login,
                        'server': account.server,
                        'currency': account.currency,
                        'leverage': account.leverage,
                        'trade_mode': 'Demo' if account.trade_mode == 0 else 'Real'
                    }
            else:
                status['last_error'] = mt5.last_error()
                
        except Exception as e:
            status['last_error'] = str(e)
        
        return status
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            if hasattr(self, 'connected') and self.connected:
                mt5.shutdown()
                self.logger.info("🔌 MT5 connection closed")
        except:
            pass