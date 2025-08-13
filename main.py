import asyncio
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import threading
import os
import MetaTrader5 as mt5

# Import our modules
from config.config import Config
from data.data_collector import MT5DataCollector
from utils.indicators import TechnicalIndicators
from models.simple_models import SimpleMLModels
from trading.signal_generator import SignalGenerator
from dashboard.web_dashboard import TradingDashboard

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class AITradingBot:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_collector = MT5DataCollector(self.config)
        self.technical_indicators = TechnicalIndicators()
        self.ml_models = SimpleMLModels(self.config)
        self.signal_generator = SignalGenerator(self.config)
        
        # State variables
        self.models_trained = {}
        self.last_signals = {}
        self.auto_trading = False
        self.trading_enabled = False
        self.running = False
        
        # Dashboard
        self.dashboard = TradingDashboard(self)
        
        self.logger.info("[OK] AI Trading Bot initialized successfully")

    def enable_auto_trading(self):
        """Enable automatic trading"""
        self.auto_trading = True
        self.trading_enabled = True
        self.logger.info("🚀 AUTO TRADING ENABLED!")
    
    def execute_trade(self, signal, symbol):
        """Execute trade in MT5 based on signal"""
        if not self.auto_trading or not self.trading_enabled:
            return False
        
        if not signal or signal['category'] == 'HOLD':
            return False
        
        # Only trade high confidence signals
        if signal['confidence'] < 0.75:
            self.logger.info(f"Signal confidence {signal['confidence']:.1%} too low for trading")
            return False
        
        try:
            # Check if MT5 is connected (simplified check)
            if not self.data_collector.connected:
                self.logger.error("MT5 not connected for trading")
                return False
            
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                self.logger.error(f"Cannot get price for {symbol}")
                return False
            
            # Determine trade direction
            if signal['signal'] > 0:  # Buy signal
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
                action = "BUY"
            else:  # Sell signal
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
                action = "SELL"
            
            # Position size (start small)
            volume = 0.01
            if abs(signal['signal']) >= 2:  # Strong signal
                volume = 0.02
            
            # Prepare order
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": f"AI_Bot_{signal['category']}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Execute trade
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"✅ TRADE EXECUTED: {action} {volume} {symbol} at ${price:.2f}")
                self.logger.info(f"Order ID: {result.order}")
                return True
            else:
                error_msg = result.comment if result else "Unknown error"
                self.logger.error(f"❌ TRADE FAILED: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Trade execution error: {e}")
            return False

    def update_dashboard_data(self):
        """Update dashboard with real account data"""
        if hasattr(self, 'dashboard') and self.dashboard:
            # Update dashboard's bot reference
            self.dashboard.bot = self
            
            # Log current account status
            if self.data_collector and hasattr(self.data_collector, 'get_account_info'):
                account = self.data_collector.get_account_info()
                if account:
                    self.logger.info(f"💰 Current Balance: ${account['balance']:,.2f} {account.get('currency', '')}")
                    if account['profit'] != 0:
                        self.logger.info(f"📊 Current P&L: ${account['profit']:,.2f}")
    
    def start_dashboard(self):
        """Start the dashboard in a separate thread"""
        def run_dashboard():
            try:
                self.dashboard.run_server(debug=False)
            except Exception as e:
                self.logger.error(f"Dashboard error: {e}")
        
        dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        dashboard_thread.start()
        self.logger.info("[SIGNAL] Dashboard started at http://127.0.0.1:8050")
    
    async def train_models(self):
        """Train ML models for all symbols"""
        self.logger.info("[TRAIN] Training ML models...")
        
        for symbol in self.config.SYMBOLS:
            try:
                # Get historical data
                data = self.data_collector.get_historical_data(symbol, self.config.TIMEFRAME, 500)
                
                if data is None or len(data) < 100:
                    self.logger.warning(f"[WARN] Insufficient data for {symbol}, using demo mode")
                    self.models_trained[symbol] = False
                    continue
                
                # Add technical indicators
                data = self.technical_indicators.add_all_indicators(data)
                
                # Prepare features and train
                X, y, features = self.ml_models.prepare_features(data)
                
                if X is not None and len(X) > 50:
                    success = self.ml_models.train_model(X, y, symbol)
                    self.models_trained[symbol] = success
                    
                    if success:
                        self.logger.info(f"[OK] Model trained for {symbol}")
                    else:
                        self.logger.warning(f"[WARN] Model training failed for {symbol}")
                else:
                    self.logger.warning(f"[WARN] Insufficient features for {symbol}")
                    self.models_trained[symbol] = False
                    
            except Exception as e:
                self.logger.error(f"[ERROR] Error training model for {symbol}: {e}")
                self.models_trained[symbol] = False
    
    async def process_symbol(self, symbol):
        """Process signals for a symbol"""
        try:
            # Get current data
            data = self.data_collector.get_historical_data(symbol, self.config.TIMEFRAME, 100)
            
            if data is None or len(data) < 20:
                # Generate demo signal for dashboard
                demo_signal = self.generate_demo_signal(symbol)
                self.last_signals[symbol] = demo_signal
                return demo_signal
            
            # Add technical indicators
            data = self.technical_indicators.add_all_indicators(data)
            data = data.dropna()
            
            if len(data) < 10:
                demo_signal = self.generate_demo_signal(symbol)
                self.last_signals[symbol] = demo_signal
                return demo_signal
            
            # Get ML prediction
            ml_signal = 0
            ml_confidence = 0.5
            
            if self.models_trained.get(symbol, False):
                X, _, features = self.ml_models.prepare_features(data)
                if X is not None and len(X) > 0:
                    ml_signal, ml_confidence = self.ml_models.predict(X[-1], symbol)
            
            # Generate final signal
            signal = self.signal_generator.generate_signal(symbol, ml_signal, ml_confidence, data)
            
            # Log signal
            self.logger.info(f"[SIGNAL] {symbol}: {signal['category']} (Confidence: {signal['confidence']:.2%})")
            
            # Store signal
            self.last_signals[symbol] = signal

            # Execute trade if auto trading enabled
            if self.auto_trading and signal['category'] in ['BUY', 'STRONG_BUY', 'SELL', 'STRONG_SELL']:
                success = self.execute_trade(signal, symbol)
                if success:
                    self.logger.info(f"🎯 AUTO TRADE: {signal['category']} {symbol}")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error processing {symbol}: {e}")
            demo_signal = self.generate_demo_signal(symbol)
            self.last_signals[symbol] = demo_signal
            return demo_signal
    
    def generate_demo_signal(self, symbol):
        """Generate demo signal for demonstration"""
        signals = ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL']
        signal_values = [2, 1, 0, -1, -2]
        
        # Random but weighted toward neutral
        weights = [0.15, 0.25, 0.3, 0.25, 0.05]
        chosen_idx = np.random.choice(len(signals), p=weights)
        
        return {
            'signal': signal_values[chosen_idx],
            'category': signals[chosen_idx],
            'confidence': np.random.uniform(0.6, 0.9),
            'reasoning': f"Demo signal for {symbol}",
            'timestamp': datetime.now().isoformat()
        }
    
    async def trading_cycle(self):
        """Main trading cycle"""
        while self.running:
            try:
                self.logger.info("[CYCLE] Running trading cycle...")
                
                # Update dashboard with real data
                self.update_dashboard_data()
                
                for symbol in self.config.SYMBOLS:
                    signal = await self.process_symbol(symbol)
                    
                    # In demo mode, just log signals
                    if signal['category'] != 'HOLD':
                        self.logger.info(f"[TRADE] {symbol} Signal: {signal['category']} "
                                       f"(Confidence: {signal['confidence']:.1%})")
                
                # Wait for next cycle
                await asyncio.sleep(30)  # 30 seconds for demo
                
            except Exception as e:
                self.logger.error(f"[ERROR] Error in trading cycle: {e}")
                await asyncio.sleep(60)
    
    async def start(self):
        """Start the bot"""
        self.logger.info("[START] Starting AI Trading Bot...")
        self.running = True
        
        # Start dashboard
        self.start_dashboard()
        
        # Check if auto trading should be enabled
        if os.path.exists('AUTO_TRADING_ENABLED.txt'):
            self.enable_auto_trading()
            self.logger.info("🚀 AUTO TRADING MODE ACTIVATED!")
        else:
            self.logger.info("📊 DEMO MODE - No real trades will execute")
        
        # Train models
        await self.train_models()
        
        # Start trading cycle
        await self.trading_cycle()
    
    def stop(self):
        """Stop the bot"""
        self.logger.info("[STOP] Stopping AI Trading Bot...")
        self.running = False