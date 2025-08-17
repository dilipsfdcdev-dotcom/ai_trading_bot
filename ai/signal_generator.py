import openai
import json
import logging
from datetime import datetime
import pandas as pd
import numpy as np

class AISignalGenerator:
    """AI-powered signal generator using OpenAI/Anthropic - FIXED VERSION"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize AI clients - FIXED OPENAI INITIALIZATION
        self.openai_client = None
        self.anthropic_client = None
        
        if config.OPENAI_API_KEY and config.OPENAI_API_KEY.startswith('sk-'):
            try:
                # FIXED: Use proper OpenAI client initialization
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
                self.logger.info("✅ OpenAI API initialized successfully")
            except Exception as e:
                self.logger.error(f"OpenAI initialization failed: {e}")
        
        if config.ANTHROPIC_API_KEY and config.ANTHROPIC_API_KEY.startswith('sk-ant-'):
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
                self.logger.info("✅ Anthropic API initialized successfully")
            except Exception as e:
                self.logger.error(f"Anthropic initialization failed: {e}")
    
    def analyze_market_data(self, symbol, data):
        """Analyze market data using AI"""
        
        if data is None or len(data) < 20:
            return self._generate_fallback_signal(symbol)
        
        # Prepare market context
        market_context = self._prepare_market_context(symbol, data)
        
        # Try OpenAI first, then Anthropic, then fallback
        if self.openai_client:
            return self._analyze_with_openai(symbol, market_context)
        elif self.anthropic_client:
            return self._analyze_with_anthropic(symbol, market_context)
        else:
            return self._generate_advanced_technical_signal(symbol, data)
    
    def _prepare_market_context(self, symbol, data):
        """Prepare market data context for AI analysis"""
        
        latest = data.iloc[-1]
        prev_5 = data.iloc[-6:-1] if len(data) >= 6 else data.iloc[:-1]
        
        # Calculate key metrics
        price_change = ((latest['close'] - data.iloc[-2]['close']) / data.iloc[-2]['close']) * 100
        
        # Get volume data safely
        volume_col = 'tick_volume' if 'tick_volume' in data.columns else 'real_volume'
        if volume_col in data.columns:
            volume_change = ((latest[volume_col] - prev_5[volume_col].mean()) / prev_5[volume_col].mean()) * 100
        else:
            volume_change = 0
        
        # Technical indicators
        rsi = latest.get('rsi_14', 50)
        macd = latest.get('macd', 0)
        bb_position = latest.get('bb_position', 0.5)
        
        # Market context
        context = {
            'symbol': symbol,
            'current_price': latest['close'],
            'price_change_percent': price_change,
            'volume_change_percent': volume_change,
            'rsi': rsi,
            'macd': macd,
            'bollinger_position': bb_position,
            'high_24h': data.tail(24)['high'].max() if len(data) >= 24 else latest['high'],
            'low_24h': data.tail(24)['low'].min() if len(data) >= 24 else latest['low'],
            'volatility': data.tail(20)['close'].std() if len(data) >= 20 else 0,
            'trend_5min': 'UP' if data.tail(5)['close'].iloc[-1] > data.tail(5)['close'].iloc[0] else 'DOWN'
        }
        
        return context
    
    def _analyze_with_openai(self, symbol, context):
        """Analyze using OpenAI GPT - FIXED VERSION"""
        
        prompt = f"""
You are an expert financial analyst. Analyze this market data for {symbol} and provide a trading signal.

Current Market Data:
- Symbol: {context['symbol']}
- Current Price: ${context['current_price']:.2f}
- Price Change: {context['price_change_percent']:.2f}%
- Volume Change: {context['volume_change_percent']:.2f}%
- RSI: {context['rsi']:.1f}
- MACD: {context['macd']:.4f}
- Bollinger Position: {context['bollinger_position']:.2f}
- 24h High: ${context['high_24h']:.2f}
- 24h Low: ${context['low_24h']:.2f}
- 5min Trend: {context['trend_5min']}

Provide your analysis in this exact JSON format:
{{
    "signal": "BUY/SELL/HOLD",
    "confidence": 0.75,
    "reasoning": "Your detailed analysis here",
    "entry_price": {context['current_price']},
    "stop_loss": 0,
    "take_profit": 0,
    "risk_level": "LOW/MEDIUM/HIGH"
}}

Consider:
1. Technical indicators alignment
2. Market momentum and volume
3. Risk/reward ratio
4. Market volatility
5. Price action patterns
"""

        try:
            # FIXED: Use proper OpenAI client method
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a professional trading analyst. Provide precise, actionable trading signals based on technical analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse JSON response
            try:
                signal_data = json.loads(ai_response)
                signal_data['ai_source'] = 'OpenAI GPT-4'
                signal_data['timestamp'] = datetime.now().isoformat()
                
                # Add stop loss and take profit if not provided
                if signal_data['stop_loss'] == 0 and signal_data['signal'] in ['BUY', 'SELL']:
                    signal_data = self._add_stop_loss_take_profit(signal_data, context)
                
                self.logger.info(f"🤖 OpenAI Signal for {symbol}: {signal_data['signal']} ({signal_data['confidence']:.1%})")
                return signal_data
                
            except json.JSONDecodeError:
                self.logger.error("Failed to parse OpenAI JSON response")
                return self._parse_text_response(ai_response, symbol, 'OpenAI')
                
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return self._generate_advanced_technical_signal(symbol, context)
    
    def _add_stop_loss_take_profit(self, signal_data, context):
        """Add stop loss and take profit levels"""
        try:
            entry_price = signal_data['entry_price']
            volatility = context['volatility']
            
            # Use ATR-based levels if volatility available, otherwise use percentage
            if volatility > 0:
                stop_distance = volatility * 2  # 2x volatility for stop loss
                profit_distance = volatility * 3  # 3x volatility for take profit
            else:
                # Fallback to percentage-based levels
                if context['symbol'] == 'XAUUSD':
                    stop_distance = entry_price * 0.015  # 1.5%
                    profit_distance = entry_price * 0.025  # 2.5%
                elif context['symbol'] == 'BTCUSD':
                    stop_distance = entry_price * 0.03  # 3%
                    profit_distance = entry_price * 0.05  # 5%
                else:
                    stop_distance = entry_price * 0.01  # 1%
                    profit_distance = entry_price * 0.02  # 2%
            
            if signal_data['signal'] == 'BUY':
                signal_data['stop_loss'] = entry_price - stop_distance
                signal_data['take_profit'] = entry_price + profit_distance
            elif signal_data['signal'] == 'SELL':
                signal_data['stop_loss'] = entry_price + stop_distance
                signal_data['take_profit'] = entry_price - profit_distance
            
        except Exception as e:
            self.logger.error(f"Error adding SL/TP: {e}")
        
        return signal_data
    
    def _analyze_with_anthropic(self, symbol, context):
        """Analyze using Anthropic Claude"""
        
        prompt = f"""
Analyze this market data for {symbol} and provide a trading signal.

Market Data:
- Symbol: {context['symbol']}
- Current Price: ${context['current_price']:.2f}
- Price Change: {context['price_change_percent']:.2f}%
- RSI: {context['rsi']:.1f}
- MACD: {context['macd']:.4f}
- Trend: {context['trend_5min']}

Provide analysis in JSON format:
{{
    "signal": "BUY/SELL/HOLD",
    "confidence": 0.75,
    "reasoning": "Your analysis",
    "risk_level": "LOW/MEDIUM/HIGH"
}}
"""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            ai_response = response.content[0].text
            
            try:
                signal_data = json.loads(ai_response)
                signal_data['ai_source'] = 'Anthropic Claude'
                signal_data['timestamp'] = datetime.now().isoformat()
                signal_data['entry_price'] = context['current_price']
                
                # Add stop loss and take profit
                if signal_data['signal'] in ['BUY', 'SELL']:
                    signal_data = self._add_stop_loss_take_profit(signal_data, context)
                
                self.logger.info(f"🤖 Claude Signal for {symbol}: {signal_data['signal']} ({signal_data['confidence']:.1%})")
                return signal_data
                
            except json.JSONDecodeError:
                return self._parse_text_response(ai_response, symbol, 'Claude')
                
        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            return self._generate_advanced_technical_signal(symbol, context)
    
    def _parse_text_response(self, response_text, symbol, source):
        """Parse non-JSON AI responses"""
        
        response_lower = response_text.lower()
        
        # Determine signal
        if 'strong buy' in response_lower or 'buy strong' in response_lower:
            signal = 'STRONG_BUY'
            confidence = 0.85
        elif 'buy' in response_lower:
            signal = 'BUY'
            confidence = 0.75
        elif 'strong sell' in response_lower or 'sell strong' in response_lower:
            signal = 'STRONG_SELL'
            confidence = 0.85
        elif 'sell' in response_lower:
            signal = 'SELL'
            confidence = 0.75
        else:
            signal = 'HOLD'
            confidence = 0.60
        
        return {
            'signal': signal,
            'confidence': confidence,
            'reasoning': response_text[:200] + "..." if len(response_text) > 200 else response_text,
            'ai_source': source,
            'timestamp': datetime.now().isoformat(),
            'risk_level': 'MEDIUM',
            'entry_price': 0,
            'stop_loss': 0,
            'take_profit': 0
        }
    
    def _generate_advanced_technical_signal(self, symbol, context):
        """Generate signal using advanced technical analysis when AI fails"""
        
        if isinstance(context, dict):
            # Context is already prepared
            data_dict = context
        else:
            # Context is DataFrame, prepare it
            data_dict = self._prepare_market_context(symbol, context)
        
        # Multi-factor scoring system
        score = 0
        confidence_factors = []
        
        # RSI Analysis
        rsi = data_dict.get('rsi', 50)
        if rsi < 30:
            score += 2
            confidence_factors.append("RSI oversold")
        elif rsi < 40:
            score += 1
            confidence_factors.append("RSI approaching oversold")
        elif rsi > 70:
            score -= 2
            confidence_factors.append("RSI overbought")
        elif rsi > 60:
            score -= 1
            confidence_factors.append("RSI approaching overbought")
        
        # MACD Analysis
        macd = data_dict.get('macd', 0)
        if macd > 0:
            score += 1
            confidence_factors.append("MACD bullish")
        else:
            score -= 1
            confidence_factors.append("MACD bearish")
        
        # Price Change Analysis
        price_change = data_dict.get('price_change_percent', 0)
        if price_change > 1:
            score += 1
            confidence_factors.append("Strong upward momentum")
        elif price_change < -1:
            score -= 1
            confidence_factors.append("Strong downward momentum")
        
        # Volume Analysis
        volume_change = data_dict.get('volume_change_percent', 0)
        if abs(volume_change) > 50:
            confidence_factors.append("High volume confirmation")
        
        # Determine signal
        if score >= 3:
            signal = 'STRONG_BUY'
            confidence = 0.85
        elif score >= 1:
            signal = 'BUY'
            confidence = 0.75
        elif score <= -3:
            signal = 'STRONG_SELL'
            confidence = 0.85
        elif score <= -1:
            signal = 'SELL'
            confidence = 0.75
        else:
            signal = 'HOLD'
            confidence = 0.60
        
        reasoning = f"Technical Analysis: {', '.join(confidence_factors[:3])}"
        
        result = {
            'signal': signal,
            'confidence': confidence,
            'reasoning': reasoning,
            'ai_source': 'Advanced Technical Analysis',
            'timestamp': datetime.now().isoformat(),
            'entry_price': data_dict.get('current_price', 0),
            'risk_level': 'MEDIUM',
            'score': score,
            'stop_loss': 0,
            'take_profit': 0
        }
        
        # Add stop loss and take profit for trading signals
        if signal in ['BUY', 'SELL', 'STRONG_BUY', 'STRONG_SELL']:
            result = self._add_stop_loss_take_profit(result, data_dict)
        
        return result
    
    def _generate_fallback_signal(self, symbol):
        """Generate fallback signal when no data available"""
        
        return {
            'signal': 'HOLD',
            'confidence': 0.50,
            'reasoning': 'Insufficient data for analysis',
            'ai_source': 'Fallback',
            'timestamp': datetime.now().isoformat(),
            'risk_level': 'LOW',
            'entry_price': 0,
            'stop_loss': 0,
            'take_profit': 0
        }
    
    def get_market_sentiment(self, symbol):
        """Get overall market sentiment using AI"""
        
        if not (self.openai_client or self.anthropic_client):
            return "NEUTRAL"
        
        prompt = f"""
        What is the current market sentiment for {symbol}? 
        Consider recent market conditions, news, and technical outlook.
        Respond with just: BULLISH, BEARISH, or NEUTRAL
        """
        
        try:
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10,
                    temperature=0.1
                )
                sentiment = response.choices[0].message.content.strip().upper()
            else:
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=10,
                    messages=[{"role": "user", "content": prompt}]
                )
                sentiment = response.content[0].text.strip().upper()
            
            return sentiment if sentiment in ['BULLISH', 'BEARISH', 'NEUTRAL'] else 'NEUTRAL'
            
        except Exception as e:
            self.logger.error(f"Error getting market sentiment: {e}")
            return "NEUTRAL"