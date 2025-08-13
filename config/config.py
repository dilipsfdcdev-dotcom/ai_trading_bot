import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MT5 Configuration
    MT5_LOGIN = int(os.getenv('MT5_LOGIN', 0))
    MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
    MT5_SERVER = os.getenv('MT5_SERVER', '')
    MT5_PATH = os.getenv('MT5_PATH', '')
    # API Keys
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    
    # Trading Parameters
    SYMBOLS = ['XAUUSD', 'BTCUSD']
    TIMEFRAME = 5
    LOOKBACK_PERIODS = 1000
    
    # Risk Management
    MAX_POSITION_SIZE = 0.02
    MAX_DAILY_LOSS = -0.05
    MAX_POSITIONS = 4
    
    # Model Parameters
    MODEL_RETRAIN_DAYS = 7
    MIN_PREDICTION_CONFIDENCE = 0.7
    SIGNAL_THRESHOLD = 0.8
