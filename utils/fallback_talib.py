
# Fallback for TA-Lib if not installed
import numpy as np
import pandas as pd

def RSI(prices, timeperiod=14):
    """Simple RSI calculation"""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=timeperiod).mean()
    avg_loss = loss.rolling(window=timeperiod).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

def MACD(prices, fastperiod=12, slowperiod=26, signalperiod=9):
    """Simple MACD calculation"""
    ema_fast = prices.ewm(span=fastperiod).mean()
    ema_slow = prices.ewm(span=slowperiod).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signalperiod).mean()
    histogram = macd - signal
    return macd, signal, histogram

def BBANDS(prices, timeperiod=20, nbdevup=2, nbdevdn=2):
    """Simple Bollinger Bands calculation"""
    middle = prices.rolling(window=timeperiod).mean()
    std = prices.rolling(window=timeperiod).std()
    upper = middle + (std * nbdevup)
    lower = middle - (std * nbdevdn)
    return upper, middle, lower
