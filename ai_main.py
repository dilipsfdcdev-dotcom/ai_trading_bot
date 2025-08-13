import asyncio
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create AI directory if it doesn't exist
os.makedirs('ai', exist_ok=True)
with open('ai/__init__.py', 'w') as f:
    f.write("# AI package\n")

# Import our modules
from config.config import Config
from data.data_collector import MT5DataCollector
from utils.indicators import TechnicalIndicators
from models.simple_models import SimpleMLModels
from ai.signal_generator import AISignalGenerator
from dashboard.tradingview_dashboard import TradingViewAIDashboard

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/ai_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class AIEnhancedTradingBot:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_collector = MT5DataCollector(self.config)
        self.technical_indicators = TechnicalIndicators()
        self.ml_models = SimpleMLModels(self.config)
        
        # NEW: AI Signal Generator
        self.ai_signal_generator = AISignalGenerator(self.config)
        
        # State variables
        self.models_trained = {}
        self.last_signals = {}
        self.last_ai_analysis = {}
        self.auto_trading = False
        self.running = False
        
        # NEW: TradingView AI Dashboard
        self.dashboard = TradingViewAIDashboard(self)
        
        self.logger.info("🤖 AI-Enhanced Trading Bot initialized successfully")
        
        # Log AI capabilities
        if self.config.OPENAI_API_KEY:
            self.logger.info("✅ OpenAI integration available")
        if self.config.ANTHROPIC_API_KEY:
            self.logger.info("✅ Anthropic Claude integration available")
        
        if not (self.config.OPENAI_API_KEY or self.config.ANTHROPIC_API_KEY):
            self.logger.warning("⚠️  No AI API keys configured - using advanced technical analysis")

    def enable_auto_trading(self):
        """Enable automatic trading"""
        self.auto_trading = True
        self.logger.info("🚀 AUTO TRADING ENABLED!")
    
    async def train_models(self):
        """Train ML models for all symbols"""
        self.logger.info("🧠 Training ML models...")
        
        for symbol in self.config.SYMBOLS:
            try:
                # Get historical data
                data = self.data_collector.get_historical_data(symbol, self.config.TIMEFRAME, 1000)
                
                if data is None or len(data) < 200:
                    self.logger.warning(f"⚠️  Insufficient data for {symbol}")
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
                        self.logger.info(f"✅ ML Model trained for {symbol} with {len(X)} samples")
                    else:
                        self.logger.warning(f"⚠️  ML training failed for {symbol}")
                else:
                    self.logger.warning(f"⚠️  Insufficient features for {symbol}")
                    self.models_trained[symbol] = False
                    
            except Exception as e:
                self.logger.error(f"❌ Error training model for {symbol}: {e}")
                self.models_trained[symbol] = False
    
    async def process_symbol_with_ai(self, symbol):
        """Process symbol using AI analysis"""
        try:
            # Get current market data
            data = self.data_collector.get_historical_data(symbol, self.config.TIMEFRAME, 200)
            
            if data is None or len(data) < 50:
                self.logger.warning(f"⚠️  Insufficient data for {symbol}")
                return self._generate_fallback_signal(symbol)
            
            # Add technical indicators
            data = self.technical_indicators.add_all_indicators(data)
            data = data.dropna()
            
            if len(data) < 20:
                return self._generate_fallback_signal(symbol)
            
            # Get ML prediction first
            ml_signal = 0
            ml_confidence = 0.5
            
            if self.models_trained.get(symbol, False):
                X, _, features = self.ml_models.prepare_features(data)
                if X is not None and len(X) > 0:
                    ml_signal, ml_confidence = self.ml_models.predict(X[-1], symbol)
            
            # NEW: Get AI analysis
            ai_analysis = self.ai_signal_generator.analyze_market_data(symbol, data)
            
            # Store AI analysis for dashboard
            self.last_ai_analysis[symbol] = ai_analysis
            
            # Combine ML and AI signals
            final_signal = self._combine_ml_and_ai_signals(ml_signal, ml_confidence, ai_analysis)
            
            # Add to dashboard
            self.dashboard.add_ai_signal(symbol, final_signal)
            
            # Log the AI analysis
            ai_source = ai_analysis.get('ai_source', 'Technical')
            ai_confidence = ai_analysis.get('confidence', 0.5)
            ai_signal_type = ai_analysis.get('signal', 'HOLD')
            
            self.logger.info(f"🤖 {symbol} AI Analysis:")
            self.logger.info(f"   • {ai_source}: {ai_signal_type} ({ai_confidence:.1%} confidence)")
            self.logger.info(f"   • ML Prediction: {ml_signal:.1f} ({ml_confidence:.1%})")
            self.logger.info(f"   • Final Signal: {final_signal.get('signal', 'HOLD')} ({final_signal.get('confidence', 0.5):.1%})")
            
            if ai_analysis.get('reasoning'):
                self.logger.info(f"   • AI Reasoning: {ai_analysis['reasoning'][:100]}...")
            
            # Store for regular dashboard compatibility
            self.last_signals[symbol] = {
                'category': final_signal.get('signal', 'HOLD'),
                'confidence': final_signal.get('confidence', 0.5),
                'reasoning': ai_analysis.get('reasoning', 'AI Analysis'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Execute trade if conditions are met
            if (self.auto_trading and 
                final_signal.get('signal', 'HOLD') in ['BUY', 'STRONG_BUY', 'SELL', 'STRONG_SELL'] and
                final_signal.get('confidence', 0) >= 0.75):
                
                self.logger.info(f"🎯 HIGH CONFIDENCE AI SIGNAL: {final_signal['signal']} {symbol}")
                # Add trade execution logic here if needed
            
            return final_signal
            
        except Exception as e:
            self.logger.error(f"❌ Error in AI analysis for {symbol}: {e}")
            return self._generate_fallback_signal(symbol)
    
    def _combine_ml_and_ai_signals(self, ml_signal, ml_confidence, ai_analysis):
        """Combine ML predictions with AI analysis"""
        
        ai_signal = ai_analysis.get('signal', 'HOLD')
        ai_confidence = ai_analysis.get('confidence', 0.5)
        
        # Convert AI signal to numeric
        signal_map = {
            'STRONG_BUY': 2,
            'BUY': 1,
            'HOLD': 0,
            'SELL': -1,
            'STRONG_SELL': -2
        }
        
        ai_numeric = signal_map.get(ai_signal, 0)
        
        # Weight: 60% AI, 40% ML if both available
        if ai_confidence > 0.6 and ml_confidence > 0.5:
            combined_signal = (ai_numeric * ai_confidence * 0.6) + (ml_signal * ml_confidence * 0.4)
            combined_confidence = (ai_confidence * 0.6) + (ml_confidence * 0.4)
        else:
            # Use stronger signal
            if ai_confidence > ml_confidence:
                combined_signal = ai_numeric
                combined_confidence = ai_confidence
            else:
                combined_signal = ml_signal
                combined_confidence = ml_confidence
        
        # Determine final signal category
        if combined_signal >= 1.5:
            final_signal = 'STRONG_BUY'
        elif combined_signal >= 0.5:
            final_signal = 'BUY'
        elif combined_signal <= -1.5:
            final_signal = 'STRONG_SELL'
        elif combined_signal <= -0.5:
            final_signal = 'SELL'
        else:
            final_signal = 'HOLD'
        
        return {
            'signal': final_signal,
            'confidence': min(combined_confidence, 0.95),  # Cap at 95%
            'reasoning': ai_analysis.get('reasoning', 'Combined AI and ML analysis'),
            'ai_source': ai_analysis.get('ai_source', 'Technical Analysis'),
            'entry_price': ai_analysis.get('entry_price', 0),
            'risk_level': ai_analysis.get('risk_level', 'MEDIUM'),
            'ml_component': ml_signal,
            'ai_component': ai_numeric,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_fallback_signal(self, symbol):
        """Generate fallback signal when analysis fails"""
        return {
            'signal': 'HOLD',
            'confidence': 0.50,
            'reasoning': 'Insufficient data for reliable analysis',
            'ai_source': 'Fallback',
            'timestamp': datetime.now().isoformat()
        }
    
    def start_dashboard(self):
        """Start the AI-enhanced dashboard"""
        def run_dashboard():
            try:
                self.dashboard.run_server(debug=False, port=8051)
            except Exception as e:
                self.logger.error(f"Dashboard error: {e}")
        
        dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
        dashboard_thread.start()
        self.logger.info("🚀 AI TradingView Dashboard started at http://127.0.0.1:8051")
    
    async def trading_cycle(self):
        """Main AI-enhanced trading cycle"""
        cycle_count = 0
        
        while self.running:
            try:
                cycle_count += 1
                self.logger.info(f"🔄 AI Trading Cycle #{cycle_count}")
                
                # Process all symbols with AI
                for symbol in self.config.SYMBOLS:
                    signal = await self.process_symbol_with_ai(symbol)
                    
                    # Log significant AI signals
                    if signal.get('signal', 'HOLD') != 'HOLD' and signal.get('confidence', 0) > 0.7:
                        ai_source = signal.get('ai_source', 'AI')
                        self.logger.info(f"🤖 STRONG AI SIGNAL: {ai_source} recommends {signal['signal']} {symbol}")
                
                # Get market sentiment every 5 cycles
                if cycle_count % 5 == 0:
                    for symbol in self.config.SYMBOLS:
                        try:
                            sentiment = self.ai_signal_generator.get_market_sentiment(symbol)
                            self.logger.info(f"📊 Market Sentiment for {symbol}: {sentiment}")
                        except Exception as e:
                            self.logger.error(f"Error getting sentiment for {symbol}: {e}")
                
                # Wait for next cycle
                await asyncio.sleep(30)  # 30 seconds for demo, adjust as needed
                
            except Exception as e:
                self.logger.error(f"❌ Error in trading cycle: {e}")
                await asyncio.sleep(60)
    
    async def start(self):
        """Start the AI-enhanced bot"""
        self.logger.info("🚀 Starting AI-Enhanced Trading Bot...")
        self.running = True
        
        # Start AI dashboard
        self.start_dashboard()
        
        # Check auto trading
        if os.path.exists('AUTO_TRADING_ENABLED.txt'):
            self.enable_auto_trading()
            self.logger.info("⚡ AUTO TRADING MODE ACTIVATED!")
        else:
            self.logger.info("📊 AI ANALYSIS MODE - Dashboard and signals only")
        
        # Log AI capabilities
        if self.config.OPENAI_API_KEY:
            self.logger.info("🤖 OpenAI GPT-4 analysis ACTIVE")
        if self.config.ANTHROPIC_API_KEY:
            self.logger.info("🤖 Anthropic Claude analysis ACTIVE")
        
        # Check data connection
        if self.data_collector.connected:
            self.logger.info("✅ MT5 Connected - Using LIVE market data")
        else:
            self.logger.info("📊 Demo Mode - Using simulated market data")
        
        # Train ML models
        await self.train_models()
        
        # Start main trading cycle
        self.logger.info("🔄 Starting AI analysis cycle...")
        await self.trading_cycle()
    
    def stop(self):
        """Stop the AI bot"""
        self.logger.info("🛑 Stopping AI-Enhanced Trading Bot...")
        self.running = False
        self.auto_trading = False
        self.logger.info("✅ AI Bot stopped successfully")

# Usage
if __name__ == "__main__":
    async def main():
        print("🤖 AI-Enhanced Trading Bot")
        print("=" * 50)
        print("🚀 TradingView Dashboard: http://127.0.0.1:8051")
        print("🤖 AI Analysis: OpenAI + Anthropic + ML")
        print("📊 Features: Live charts + AI signals")
        print("🔄 Press Ctrl+C to stop")
        print("=" * 50)
        
        bot = AIEnhancedTradingBot()
        
        try:
            await bot.start()
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
            bot.stop()
        except Exception as e:
            print(f"❌ Bot error: {e}")
            bot.stop()
    
    asyncio.run(main())