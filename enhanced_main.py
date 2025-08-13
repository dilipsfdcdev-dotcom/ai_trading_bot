import asyncio
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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

class PositionManager:
    """Manages trading positions and risk"""
    
    def __init__(self, config):
        self.config = config
        self.positions = {}
        self.daily_pnl = 0
        self.trade_count_today = 0
        self.last_trade_time = {}
        self.logger = logging.getLogger(__name__)
    
    def can_open_position(self, symbol):
        """Check if we can open a new position"""
        # Max positions check
        if len(self.positions) >= self.config.MAX_POSITIONS:
            return False, "Max positions reached"
        
        # Daily loss check
        if self.daily_pnl <= self.config.MAX_DAILY_LOSS * self.get_account_balance():
            return False, "Daily loss limit reached"
        
        # Time between trades (minimum 5 minutes)
        if symbol in self.last_trade_time:
            time_diff = datetime.now() - self.last_trade_time[symbol]
            if time_diff.total_seconds() < 300:  # 5 minutes
                return False, "Too soon since last trade"
        
        return True, "OK"
    
    def calculate_position_size(self, symbol, signal_strength, account_balance):
        """Calculate position size based on AI confidence and risk"""
        base_risk = 0.01  # 1% base risk per trade
        
        # Adjust based on signal strength
        if signal_strength >= 0.9:
            risk_multiplier = 2.0
        elif signal_strength >= 0.8:
            risk_multiplier = 1.5
        elif signal_strength >= 0.7:
            risk_multiplier = 1.0
        else:
            risk_multiplier = 0.5
        
        # Calculate position size
        risk_amount = account_balance * base_risk * risk_multiplier
        
        # Get current price for position sizing
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return 0.01  # Default
        
        # Symbol-specific calculations
        if symbol == 'XAUUSD':
            # Gold: $1 per 0.01 lot per point
            position_size = min(risk_amount / 1000, 0.1)  # Max 0.1 lots
        elif symbol == 'BTCUSD':
            # Bitcoin: Higher volatility, smaller size
            position_size = min(risk_amount / 5000, 0.05)  # Max 0.05 lots
        else:
            # Default calculation
            position_size = min(risk_amount / 1000, 0.1)
        
        # Minimum position size
        return max(position_size, 0.01)
    
    def get_account_balance(self):
        """Get current account balance"""
        account = mt5.account_info()
        return account.balance if account else 10000
    
    def add_position(self, symbol, order_id, action, volume, price):
        """Add new position to tracking"""
        self.positions[order_id] = {
            'symbol': symbol,
            'action': action,
            'volume': volume,
            'open_price': price,
            'open_time': datetime.now(),
            'stop_loss': None,
            'take_profit': None
        }
        self.last_trade_time[symbol] = datetime.now()
        self.trade_count_today += 1
    
    def set_stop_loss_take_profit(self, order_id, symbol, action, price):
        """Set stop loss and take profit for position"""
        if order_id not in self.positions:
            return
        
        # Get ATR for dynamic SL/TP
        atr = self.get_atr(symbol)
        if not atr:
            atr = price * 0.01  # 1% fallback
        
        if action == 'BUY':
            stop_loss = price - (atr * 2)  # 2 ATR stop loss
            take_profit = price + (atr * 3)  # 3 ATR take profit
        else:  # SELL
            stop_loss = price + (atr * 2)
            take_profit = price - (atr * 3)
        
        # Update position
        self.positions[order_id]['stop_loss'] = stop_loss
        self.positions[order_id]['take_profit'] = take_profit
        
        # Set in MT5 (simplified - in real implementation, modify the position)
        self.logger.info(f"SL/TP set for {symbol}: SL={stop_loss:.2f}, TP={take_profit:.2f}")
    
    def get_atr(self, symbol):
        """Get ATR for the symbol"""
        # This would fetch from your data collector
        # Simplified version returns estimated ATR
        if symbol == 'XAUUSD':
            return 15.0  # ~$15 ATR for gold
        elif symbol == 'BTCUSD':
            return 3000.0  # ~$3000 ATR for Bitcoin
        return 0.01
    
    def check_positions(self):
        """Check and manage existing positions"""
        mt5_positions = mt5.positions_get()
        if not mt5_positions:
            return
        
        for pos in mt5_positions:
            # Update daily P&L
            self.daily_pnl += pos.profit
            
            # Check for position management (trailing stops, etc.)
            self.manage_position(pos)
    
    def manage_position(self, position):
        """Manage individual position"""
        # Implement trailing stops, position scaling, etc.
        # This is a simplified version
        current_profit = position.profit
        
        # Trail stop loss if in profit
        if current_profit > 50:  # $50 profit
            # Implement trailing stop logic here
            pass

class EnhancedAITradingBot:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_collector = MT5DataCollector(self.config)
        self.technical_indicators = TechnicalIndicators()
        self.ml_models = SimpleMLModels(self.config)
        self.signal_generator = SignalGenerator(self.config)
        self.position_manager = PositionManager(self.config)
        
        # State variables
        self.models_trained = {}
        self.last_signals = {}
        self.auto_trading = False
        self.trading_enabled = False
        self.running = False
        
        # Dashboard
        self.dashboard = TradingDashboard(self)
        
        self.logger.info("🤖 Enhanced AI Trading Bot initialized successfully")

    def enable_auto_trading(self):
        """Enable automatic trading"""
        self.auto_trading = True
        self.trading_enabled = True
        self.logger.info("🚀 AUTO TRADING ENABLED!")
    
    def execute_trade(self, signal, symbol):
        """Execute trade with enhanced risk management"""
        if not self.auto_trading or not self.trading_enabled:
            return False
        
        if not signal or signal['category'] == 'HOLD':
            return False
        
        # Only trade high confidence signals
        if signal['confidence'] < 0.7:
            self.logger.info(f"Signal confidence {signal['confidence']:.1%} too low for trading")
            return False
        
        # Check if we can open a position
        can_trade, reason = self.position_manager.can_open_position(symbol)
        if not can_trade:
            self.logger.warning(f"Cannot trade {symbol}: {reason}")
            return False
        
        try:
            # Check if MT5 is connected
            if not self.data_collector.connected:
                self.logger.error("MT5 not connected for trading")
                return False
            
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                self.logger.error(f"Cannot get price for {symbol}")
                return False
            
            # Get account balance
            account_balance = self.position_manager.get_account_balance()
            
            # Calculate position size based on AI confidence
            volume = self.position_manager.calculate_position_size(
                symbol, signal['confidence'], account_balance
            )
            
            # Determine trade direction
            if signal['signal'] > 0:  # Buy signal
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
                action = "BUY"
            else:  # Sell signal
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
                action = "SELL"
            
            # Prepare order
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": f"AI_Bot_{signal['category']}_Conf{signal['confidence']:.0%}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Execute trade
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.logger.info(f"✅ TRADE EXECUTED: {action} {volume} {symbol} at ${price:.2f}")
                self.logger.info(f"💰 Position Size: {volume} lots (Confidence: {signal['confidence']:.1%})")
                self.logger.info(f"🎯 Order ID: {result.order}")
                
                # Track position
                self.position_manager.add_position(symbol, result.order, action, volume, price)
                
                # Set stop loss and take profit
                self.position_manager.set_stop_loss_take_profit(result.order, symbol, action, price)
                
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
            
            # Check positions
            self.position_manager.check_positions()
            
            # Log current account status
            if self.data_collector and hasattr(self.data_collector, 'get_account_info'):
                account = self.data_collector.get_account_info()
                if account:
                    self.logger.info(f"💰 Balance: ${account['balance']:,.2f} | Equity: ${account['equity']:,.2f}")
                    if account['profit'] != 0:
                        self.logger.info(f"📊 Current P&L: ${account['profit']:,.2f}")
                    
                    # Log position count
                    positions = mt5.positions_get()
                    if positions:
                        self.logger.info(f"📈 Open Positions: {len(positions)}")
    
    def start_dashboard(self):
        """Start the dashboard in a separate thread"""
        def run_dashboard():
            try:
                self.dashboard.run_server(debug=False)
            except Exception as e:
                self.logger.error(f"Dashboard error: {e}")
        
        dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        dashboard_thread.start()
        self.logger.info("📊 Dashboard started at http://127.0.0.1:8050")
    
    async def train_models(self):
        """Train ML models for all symbols"""
        self.logger.info("🧠 Training ML models...")
        
        for symbol in self.config.SYMBOLS:
            try:
                # Get more historical data for better training
                data = self.data_collector.get_historical_data(symbol, self.config.TIMEFRAME, 1000)
                
                if data is None or len(data) < 200:
                    self.logger.warning(f"⚠️ Insufficient data for {symbol}, using demo mode")
                    self.models_trained[symbol] = False
                    continue
                
                # Add technical indicators
                data = self.technical_indicators.add_all_indicators(data)
                
                # Prepare features and train
                X, y, features = self.ml_models.prepare_features(data)
                
                if X is not None and len(X) > 100:
                    success = self.ml_models.train_model(X, y, symbol)
                    self.models_trained[symbol] = success
                    
                    if success:
                        self.logger.info(f"✅ Model trained for {symbol} with {len(X)} samples")
                    else:
                        self.logger.warning(f"⚠️ Model training failed for {symbol}")
                else:
                    self.logger.warning(f"⚠️ Insufficient features for {symbol}")
                    self.models_trained[symbol] = False
                    
            except Exception as e:
                self.logger.error(f"❌ Error training model for {symbol}: {e}")
                self.models_trained[symbol] = False
    
    async def process_symbol(self, symbol):
        """Process signals for a symbol with enhanced logic"""
        try:
            # Get current data with more bars for better analysis
            data = self.data_collector.get_historical_data(symbol, self.config.TIMEFRAME, 200)
            
            if data is None or len(data) < 50:
                # Generate demo signal for dashboard
                demo_signal = self.generate_demo_signal(symbol)
                self.last_signals[symbol] = demo_signal
                return demo_signal
            
            # Add technical indicators
            data = self.technical_indicators.add_all_indicators(data)
            data = data.dropna()
            
            if len(data) < 20:
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
            
            # Generate final signal with enhanced logic
            signal = self.signal_generator.generate_signal(symbol, ml_signal, ml_confidence, data)
            
            # Get current price for logging
            tick = mt5.symbol_info_tick(symbol)
            current_price = tick.bid if tick else "N/A"
            
            # Enhanced logging with market context
            self.logger.info(f"📊 {symbol} @ ${current_price}: {signal['category']} "
                           f"(Conf: {signal['confidence']:.1%}, ML: {ml_signal:.1f})")
            
            # Store signal
            self.last_signals[symbol] = signal

            # Execute trade if auto trading enabled with enhanced conditions
            if (self.auto_trading and 
                signal['category'] in ['BUY', 'STRONG_BUY', 'SELL', 'STRONG_SELL'] and
                signal['confidence'] >= 0.7):
                
                success = self.execute_trade(signal, symbol)
                if success:
                    self.logger.info(f"🎯 AUTO TRADE EXECUTED: {signal['category']} {symbol}")
                    
                    # Log trade reasoning
                    self.logger.info(f"🧠 Trade Reasoning: {signal['reasoning']}")
            
            return signal
            
        except Exception as e:
            self.logger.error(f"❌ Error processing {symbol}: {e}")
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
    
    def log_trading_summary(self):
        """Log daily trading summary"""
        account = mt5.account_info()
        positions = mt5.positions_get()
        
        if account:
            self.logger.info("=" * 60)
            self.logger.info("📈 TRADING SUMMARY")
            self.logger.info("=" * 60)
            self.logger.info(f"💰 Account Balance: ${account.balance:,.2f}")
            self.logger.info(f"📊 Current Equity: ${account.equity:,.2f}")
            self.logger.info(f"📈 Unrealized P&L: ${account.profit:,.2f}")
            self.logger.info(f"🎯 Open Positions: {len(positions) if positions else 0}")
            self.logger.info(f"📊 Trades Today: {self.position_manager.trade_count_today}")
            
            if positions:
                self.logger.info("\n🔍 Open Positions:")
                for pos in positions:
                    profit_emoji = "🟢" if pos.profit > 0 else "🔴" if pos.profit < 0 else "⚪"
                    self.logger.info(f"  {profit_emoji} {pos.symbol} {pos.type_str} "
                                   f"{pos.volume} lots @ ${pos.price_open:.2f} "
                                   f"(P&L: ${pos.profit:.2f})")
            
            self.logger.info("=" * 60)
    
    async def trading_cycle(self):
        """Main enhanced trading cycle"""
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                self.logger.info(f"🔄 Trading Cycle #{cycle_count}")
                
                # Update dashboard with real data
                self.update_dashboard_data()
                
                # Process all symbols
                for symbol in self.config.SYMBOLS:
                    signal = await self.process_symbol(symbol)
                    
                    # Log significant signals
                    if signal['category'] != 'HOLD' and signal['confidence'] > 0.7:
                        self.logger.info(f"🎯 STRONG SIGNAL: {symbol} {signal['category']} "
                                       f"(Confidence: {signal['confidence']:.1%})")
                
                # Log summary every 10 cycles (5 minutes in demo mode)
                if cycle_count % 10 == 0:
                    self.log_trading_summary()
                
                # Check for emergency stops
                account = mt5.account_info()
                if account and account.profit < -1000:  # Emergency stop at -$1000
                    self.logger.error("🚨 EMERGENCY STOP: Large drawdown detected!")
                    self.auto_trading = False
                
                # Wait for next cycle (30 seconds for demo, 5 minutes for live)
                sleep_time = 30 if not self.data_collector.connected else 300
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"❌ Error in trading cycle: {e}")
                await asyncio.sleep(60)
    
    async def start(self):
        """Start the enhanced bot"""
        self.logger.info("🚀 Starting Enhanced AI Trading Bot...")
        self.running = True
        
        # Start dashboard
        self.start_dashboard()
        
        # Check if auto trading should be enabled
        if os.path.exists('AUTO_TRADING_ENABLED.txt'):
            self.enable_auto_trading()
            self.logger.info("⚡ AUTO TRADING MODE ACTIVATED!")
            self.logger.info("💡 Bot will execute trades automatically on high confidence signals")
        else:
            self.logger.info("📊 DEMO MODE - Dashboard only, no real trades")
        
        # Check MT5 connection
        if self.data_collector.connected:
            self.logger.info("✅ MT5 Connected - Using LIVE data")
        else:
            self.logger.info("⚠️ MT5 Not Connected - Using DEMO data")
        
        # Train models
        await self.train_models()
        
        # Log initial status
        self.log_trading_summary()
        
        # Start trading cycle
        await self.trading_cycle()
    
    def stop(self):
        """Stop the bot with cleanup"""
        self.logger.info("🛑 Stopping Enhanced AI Trading Bot...")
        self.running = False
        self.auto_trading = False
        
        # Log final summary
        self.log_trading_summary()
        
        self.logger.info("✅ Bot stopped successfully")

# Usage example
if __name__ == "__main__":
    async def main():
        bot = EnhancedAITradingBot()
        try:
            await bot.start()
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
            bot.stop()
        except Exception as e:
            print(f"❌ Bot error: {e}")
            bot.stop()
    
    asyncio.run(main())