import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import logging

class SimpleMLModels:
    def __init__(self, config):
        self.config = config
        self.models = {}
        self.scalers = {}
        self.logger = logging.getLogger(__name__)
        
    def prepare_features(self, df):
        """Prepare features for ML models"""
        df = df.dropna()
        
        if len(df) < 50:
            return None, None, None
        
        # Select numeric features
        feature_columns = []
        for col in df.columns:
            if col not in ['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']:
                if df[col].dtype in ['float64', 'int64']:
                    feature_columns.append(col)
        
        if len(feature_columns) < 5:
            return None, None, None
        
        X = df[feature_columns].values
        
        # Create target (simplified)
        future_periods = 3
        df['future_return'] = df['close'].shift(-future_periods) / df['close'] - 1
        
        # Create classification target
        y = np.where(df['future_return'] > 0.001, 2,      # Strong Buy
                    np.where(df['future_return'] > 0, 1,   # Buy  
                            np.where(df['future_return'] < -0.001, -2,  # Strong Sell
                                    np.where(df['future_return'] < 0, -1, 0))))  # Sell, Hold
        
        # Remove NaN values
        valid_mask = ~np.isnan(y)
        X = X[valid_mask]
        y = y[valid_mask]
        
        return X, y, feature_columns
    
    def train_model(self, X, y, symbol):
        """Train simple random forest model"""
        if X is None or len(X) < 20:
            return False
        
        try:
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train model
            model = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42)
            model.fit(X_scaled, y)
            
            self.models[symbol] = model
            self.scalers[symbol] = scaler
            
            return True
        except Exception as e:
            self.logger.error(f"Error training model for {symbol}: {e}")
            return False
    
    def predict(self, X, symbol):
        """Make prediction"""
        if symbol not in self.models or X is None:
            return 0, 0.5
        
        try:
            X_scaled = self.scalers[symbol].transform(X.reshape(1, -1))
            prediction = self.models[symbol].predict(X_scaled)[0]
            probabilities = self.models[symbol].predict_proba(X_scaled)[0]
            confidence = np.max(probabilities)
            
            return prediction, confidence
        except Exception as e:
            self.logger.error(f"Prediction error for {symbol}: {e}")
            return 0, 0.5
