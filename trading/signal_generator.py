import numpy as np
import pandas as pd
from datetime import datetime
import logging

class SignalGenerator:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def generate_signal(self, symbol, ml_signal, ml_confidence, market_data):
        """Generate final trading signal"""
        
        if market_data is None or len(market_data) == 0:
            return self._create_signal(0, "HOLD", 0.0, "No market data")
        
        latest = market_data.iloc[-1]
        
        # Technical confirmation
        tech_score = self._get_technical_score(latest)
        
        # Market condition filter
        market_filter = self._get_market_filter(latest)
        
        # Combine signals
        final_signal = self._combine_signals(ml_signal, ml_confidence, tech_score, market_filter)
        
        return final_signal
    
    def _get_technical_score(self, data):
        """Get technical analysis score"""
        score = 0
        
        # RSI
        rsi = data.get('rsi_14', 50)
        if rsi < 30:
            score += 1
        elif rsi > 70:
            score -= 1
        
        # MACD
        macd = data.get('macd', 0)
        macd_signal = data.get('macd_signal', 0)
        if macd > macd_signal:
            score += 0.5
        else:
            score -= 0.5
        
        # Trend
        sma_20 = data.get('sma_20', 0)
        sma_50 = data.get('sma_50', 0)
        current_price = data.get('close', 0)
        
        if current_price > sma_20 > sma_50:
            score += 1
        elif current_price < sma_20 < sma_50:
            score -= 1
        
        return np.clip(score / 2.5, -1, 1)  # Normalize to [-1, 1]
    
    def _get_market_filter(self, data):
        """Get market condition filter"""
        atr_percent = data.get('atr_percent', 1)
        
        # Volatility filter
        if atr_percent > 3:  # High volatility
            return 0.5
        elif atr_percent < 0.3:  # Low volatility
            return 0.7
        else:
            return 1.0
    
    def _combine_signals(self, ml_signal, ml_confidence, tech_score, market_filter):
        """Combine all signals"""
        
        # Weight the signals
        combined_signal = (ml_signal * ml_confidence * 0.6) + (tech_score * 0.4)
        final_confidence = (ml_confidence + 0.7) / 2 * market_filter
        
        # Determine signal category
        if abs(combined_signal) < 0.3 or final_confidence < 0.5:
            category = "HOLD"
            signal_value = 0
        elif combined_signal >= 1.5:
            category = "STRONG_BUY"
            signal_value = 2
        elif combined_signal >= 0.5:
            category = "BUY"
            signal_value = 1
        elif combined_signal <= -1.5:
            category = "STRONG_SELL"
            signal_value = -2
        elif combined_signal <= -0.5:
            category = "SELL"
            signal_value = -1
        else:
            category = "HOLD"
            signal_value = 0
        
        return self._create_signal(
            signal_value, category, final_confidence,
            f"ML:{ml_signal:.1f}({ml_confidence:.2f}) Tech:{tech_score:.2f}"
        )
    
    def _create_signal(self, signal, category, confidence, reasoning):
        """Create signal dictionary"""
        return {
            'signal': signal,
            'category': category,
            'confidence': confidence,
            'reasoning': reasoning,
            'timestamp': datetime.now().isoformat()
        }
