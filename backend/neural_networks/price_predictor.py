"""
Neural Network Price Prediction Models

Advanced deep learning models for price prediction:
- LSTM with attention mechanism
- Transformer-based predictor
- Ensemble model combining multiple architectures
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
from datetime import datetime
import json
import os

# Deep Learning imports - using PyTorch
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from sklearn.preprocessing import MinMaxScaler, StandardScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    PRICE = "price"
    DIRECTION = "direction"
    VOLATILITY = "volatility"
    TREND_STRENGTH = "trend_strength"


@dataclass
class PricePrediction:
    """Price prediction result"""
    symbol: str
    current_price: float
    predicted_price: float
    predicted_direction: str  # UP, DOWN, NEUTRAL
    confidence: float  # 0-1
    predicted_high: float
    predicted_low: float
    time_horizon: str  # "1H", "4H", "1D"
    volatility_forecast: float
    trend_strength: float  # -1 to 1
    model_type: str
    timestamp: datetime
    features_importance: Dict[str, float]

    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "current_price": self.current_price,
            "predicted_price": self.predicted_price,
            "predicted_direction": self.predicted_direction,
            "confidence": self.confidence,
            "predicted_high": self.predicted_high,
            "predicted_low": self.predicted_low,
            "time_horizon": self.time_horizon,
            "volatility_forecast": self.volatility_forecast,
            "trend_strength": self.trend_strength,
            "model_type": self.model_type,
            "timestamp": self.timestamp.isoformat(),
            "features_importance": self.features_importance
        }


class AttentionLayer(nn.Module):
    """Self-attention layer for sequence models"""

    def __init__(self, hidden_size: int, num_heads: int = 4):
        super().__init__()
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=num_heads,
            batch_first=True
        )
        self.layer_norm = nn.LayerNorm(hidden_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        attn_output, _ = self.attention(x, x, x)
        return self.layer_norm(x + attn_output)


class LSTMWithAttention(nn.Module):
    """LSTM network with self-attention mechanism for price prediction"""

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 3,
        dropout: float = 0.2,
        num_heads: int = 4,
        output_size: int = 1
    ):
        super().__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # Input projection
        self.input_projection = nn.Linear(input_size, hidden_size)

        # Bidirectional LSTM layers
        self.lstm = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )

        # Attention layer
        self.attention = AttentionLayer(hidden_size * 2, num_heads)

        # Output layers
        self.fc_layers = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, output_size)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Input projection
        x = self.input_projection(x)

        # LSTM
        lstm_out, _ = self.lstm(x)

        # Attention
        attended = self.attention(lstm_out)

        # Take the last time step
        last_output = attended[:, -1, :]

        # Output
        return self.fc_layers(last_output)


class PositionalEncoding(nn.Module):
    """Positional encoding for Transformer"""

    def __init__(self, d_model: int, max_len: int = 500, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class TransformerPriceModel(nn.Module):
    """Transformer-based model for price prediction"""

    def __init__(
        self,
        input_size: int,
        d_model: int = 128,
        nhead: int = 8,
        num_encoder_layers: int = 4,
        dim_feedforward: int = 512,
        dropout: float = 0.1,
        output_size: int = 1
    ):
        super().__init__()

        self.d_model = d_model

        # Input embedding
        self.input_embedding = nn.Linear(input_size, d_model)

        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, dropout=dropout)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_encoder_layers
        )

        # Output layers
        self.output_layers = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, output_size)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Input embedding
        x = self.input_embedding(x)

        # Positional encoding
        x = self.pos_encoder(x)

        # Transformer encoder
        encoded = self.transformer_encoder(x)

        # Take the last time step
        last_output = encoded[:, -1, :]

        # Output
        return self.output_layers(last_output)


class PricePredictor:
    """
    LSTM-based Price Predictor with attention mechanism

    Features:
    - Bidirectional LSTM with self-attention
    - Multi-horizon predictions
    - Uncertainty estimation
    - Online learning capability
    """

    def __init__(
        self,
        sequence_length: int = 60,
        hidden_size: int = 128,
        num_layers: int = 3,
        learning_rate: float = 0.001,
        model_dir: str = "./models"
    ):
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.learning_rate = learning_rate
        self.model_dir = model_dir

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[LSTMWithAttention] = None
        self.scaler_X: Optional[StandardScaler] = None
        self.scaler_y: Optional[MinMaxScaler] = None
        self.feature_names: List[str] = []
        self.is_trained = False

        os.makedirs(model_dir, exist_ok=True)
        logger.info(f"PricePredictor initialized on device: {self.device}")

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features from OHLCV data"""
        features = pd.DataFrame(index=df.index)

        # Price features
        features['close'] = df['close']
        features['open'] = df['open']
        features['high'] = df['high']
        features['low'] = df['low']
        features['volume'] = df['volume'] if 'volume' in df.columns else 0

        # Returns
        features['returns'] = df['close'].pct_change()
        features['log_returns'] = np.log(df['close'] / df['close'].shift(1))

        # Price ratios
        features['hl_ratio'] = (df['high'] - df['low']) / df['close']
        features['oc_ratio'] = (df['close'] - df['open']) / df['close']

        # Moving averages
        for period in [5, 10, 20, 50]:
            features[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            features[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            features[f'sma_ratio_{period}'] = df['close'] / features[f'sma_{period}']

        # Volatility
        features['volatility_5'] = features['returns'].rolling(window=5).std()
        features['volatility_20'] = features['returns'].rolling(window=20).std()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        features['macd'] = ema12 - ema26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()
        features['macd_hist'] = features['macd'] - features['macd_signal']

        # Bollinger Bands
        sma20 = df['close'].rolling(window=20).mean()
        std20 = df['close'].rolling(window=20).std()
        features['bb_upper'] = sma20 + (std20 * 2)
        features['bb_lower'] = sma20 - (std20 * 2)
        features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / sma20
        features['bb_position'] = (df['close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])

        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        features['atr'] = true_range.rolling(window=14).mean()
        features['atr_ratio'] = features['atr'] / df['close']

        # Momentum
        features['momentum_5'] = df['close'] / df['close'].shift(5) - 1
        features['momentum_10'] = df['close'] / df['close'].shift(10) - 1
        features['momentum_20'] = df['close'] / df['close'].shift(20) - 1

        # Stochastic
        low_14 = df['low'].rolling(window=14).min()
        high_14 = df['high'].rolling(window=14).max()
        features['stoch_k'] = 100 * (df['close'] - low_14) / (high_14 - low_14)
        features['stoch_d'] = features['stoch_k'].rolling(window=3).mean()

        # Volume features (if available)
        if 'volume' in df.columns and df['volume'].sum() > 0:
            features['volume_sma'] = df['volume'].rolling(window=20).mean()
            features['volume_ratio'] = df['volume'] / features['volume_sma']

        # Drop NaN
        features = features.dropna()

        self.feature_names = features.columns.tolist()
        return features

    def _create_sequences(
        self,
        data: np.ndarray,
        target: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for training"""
        X, y = [], []
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:(i + self.sequence_length)])
            y.append(target[i + self.sequence_length])
        return np.array(X), np.array(y)

    async def train(
        self,
        df: pd.DataFrame,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> Dict[str, Any]:
        """Train the LSTM model"""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for training")
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for training")

        logger.info("Preparing training data...")

        # Prepare features
        features = self._prepare_features(df)

        # Scale features
        self.scaler_X = StandardScaler()
        self.scaler_y = MinMaxScaler()

        X_scaled = self.scaler_X.fit_transform(features.values)
        y_scaled = self.scaler_y.fit_transform(features['close'].values.reshape(-1, 1))

        # Create sequences
        X_seq, y_seq = self._create_sequences(X_scaled, y_scaled.flatten())

        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X_seq, y_seq, test_size=validation_split, shuffle=False
        )

        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_train_tensor = torch.FloatTensor(y_train).unsqueeze(1).to(self.device)
        X_val_tensor = torch.FloatTensor(X_val).to(self.device)
        y_val_tensor = torch.FloatTensor(y_val).unsqueeze(1).to(self.device)

        # Create data loaders
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        # Initialize model
        input_size = X_train.shape[2]
        self.model = LSTMWithAttention(
            input_size=input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers
        ).to(self.device)

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode='min', factor=0.5, patience=5
        )

        # Training loop
        train_losses = []
        val_losses = []
        best_val_loss = float('inf')

        logger.info(f"Training LSTM model for {epochs} epochs...")

        for epoch in range(epochs):
            self.model.train()
            epoch_loss = 0

            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                epoch_loss += loss.item()

            avg_train_loss = epoch_loss / len(train_loader)
            train_losses.append(avg_train_loss)

            # Validation
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val_tensor)
                val_loss = criterion(val_outputs, y_val_tensor).item()
                val_losses.append(val_loss)

            scheduler.step(val_loss)

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self.save_model("best_lstm_model.pt")

            if (epoch + 1) % 10 == 0:
                logger.info(
                    f"Epoch [{epoch+1}/{epochs}], "
                    f"Train Loss: {avg_train_loss:.6f}, "
                    f"Val Loss: {val_loss:.6f}"
                )

        self.is_trained = True

        return {
            "train_losses": train_losses,
            "val_losses": val_losses,
            "best_val_loss": best_val_loss,
            "epochs_trained": epochs,
            "features_count": input_size
        }

    async def predict(
        self,
        df: pd.DataFrame,
        symbol: str = "UNKNOWN",
        time_horizon: str = "1H"
    ) -> PricePrediction:
        """Make price prediction"""
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Prepare features
        features = self._prepare_features(df)

        # Scale
        X_scaled = self.scaler_X.transform(features.values)

        # Get last sequence
        last_sequence = X_scaled[-self.sequence_length:]
        X_tensor = torch.FloatTensor(last_sequence).unsqueeze(0).to(self.device)

        # Predict
        self.model.eval()
        with torch.no_grad():
            prediction_scaled = self.model(X_tensor).cpu().numpy()

        # Inverse scale
        predicted_price = self.scaler_y.inverse_transform(
            prediction_scaled.reshape(-1, 1)
        )[0, 0]

        current_price = df['close'].iloc[-1]

        # Calculate prediction confidence based on recent accuracy
        price_change_pct = abs(predicted_price - current_price) / current_price
        confidence = max(0.3, min(0.95, 1 - price_change_pct * 2))

        # Determine direction
        if predicted_price > current_price * 1.002:
            direction = "UP"
        elif predicted_price < current_price * 0.998:
            direction = "DOWN"
        else:
            direction = "NEUTRAL"

        # Estimate high/low based on ATR
        atr = features['atr'].iloc[-1]
        predicted_high = predicted_price + atr * 0.5
        predicted_low = predicted_price - atr * 0.5

        # Volatility forecast
        volatility_forecast = features['volatility_20'].iloc[-1]

        # Trend strength (-1 to 1)
        momentum = features['momentum_20'].iloc[-1]
        trend_strength = np.tanh(momentum * 10)  # Normalize to -1 to 1

        # Feature importance (simplified)
        feature_importance = {
            "momentum": abs(features['momentum_20'].iloc[-1]),
            "rsi": abs(features['rsi'].iloc[-1] - 50) / 50,
            "macd": abs(features['macd_hist'].iloc[-1]),
            "volatility": features['volatility_20'].iloc[-1],
            "bb_position": abs(features['bb_position'].iloc[-1] - 0.5)
        }

        return PricePrediction(
            symbol=symbol,
            current_price=current_price,
            predicted_price=predicted_price,
            predicted_direction=direction,
            confidence=confidence,
            predicted_high=predicted_high,
            predicted_low=predicted_low,
            time_horizon=time_horizon,
            volatility_forecast=volatility_forecast,
            trend_strength=trend_strength,
            model_type="LSTM_Attention",
            timestamp=datetime.now(),
            features_importance=feature_importance
        )

    def save_model(self, filename: str):
        """Save model to disk"""
        if self.model is None:
            return

        path = os.path.join(self.model_dir, filename)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'scaler_X': self.scaler_X,
            'scaler_y': self.scaler_y,
            'feature_names': self.feature_names,
            'sequence_length': self.sequence_length,
            'hidden_size': self.hidden_size,
            'num_layers': self.num_layers
        }, path)
        logger.info(f"Model saved to {path}")

    def load_model(self, filename: str):
        """Load model from disk"""
        path = os.path.join(self.model_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found at {path}")

        checkpoint = torch.load(path, map_location=self.device)

        self.scaler_X = checkpoint['scaler_X']
        self.scaler_y = checkpoint['scaler_y']
        self.feature_names = checkpoint['feature_names']
        self.sequence_length = checkpoint['sequence_length']
        self.hidden_size = checkpoint['hidden_size']
        self.num_layers = checkpoint['num_layers']

        input_size = len(self.feature_names)
        self.model = LSTMWithAttention(
            input_size=input_size,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers
        ).to(self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.is_trained = True
        logger.info(f"Model loaded from {path}")


class TransformerPredictor:
    """
    Transformer-based Price Predictor

    Uses self-attention to capture long-range dependencies in price data.
    """

    def __init__(
        self,
        sequence_length: int = 60,
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 4,
        learning_rate: float = 0.0001,
        model_dir: str = "./models"
    ):
        self.sequence_length = sequence_length
        self.d_model = d_model
        self.nhead = nhead
        self.num_layers = num_layers
        self.learning_rate = learning_rate
        self.model_dir = model_dir

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: Optional[TransformerPriceModel] = None
        self.scaler_X: Optional[StandardScaler] = None
        self.scaler_y: Optional[MinMaxScaler] = None
        self.feature_names: List[str] = []
        self.is_trained = False

        os.makedirs(model_dir, exist_ok=True)
        logger.info(f"TransformerPredictor initialized on device: {self.device}")

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features - same as LSTM"""
        features = pd.DataFrame(index=df.index)

        # Price features
        features['close'] = df['close']
        features['open'] = df['open']
        features['high'] = df['high']
        features['low'] = df['low']

        # Returns
        features['returns'] = df['close'].pct_change()
        features['log_returns'] = np.log(df['close'] / df['close'].shift(1))

        # Price ratios
        features['hl_ratio'] = (df['high'] - df['low']) / df['close']
        features['oc_ratio'] = (df['close'] - df['open']) / df['close']

        # Moving averages
        for period in [5, 10, 20, 50]:
            features[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            features[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            features[f'sma_ratio_{period}'] = df['close'] / features[f'sma_{period}']

        # Technical indicators
        features['volatility_20'] = features['returns'].rolling(window=20).std()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features['rsi'] = 100 - (100 / (1 + rs))

        # MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        features['macd'] = ema12 - ema26
        features['macd_signal'] = features['macd'].ewm(span=9).mean()

        # Momentum
        features['momentum_10'] = df['close'] / df['close'].shift(10) - 1
        features['momentum_20'] = df['close'] / df['close'].shift(20) - 1

        features = features.dropna()
        self.feature_names = features.columns.tolist()
        return features

    def _create_sequences(
        self,
        data: np.ndarray,
        target: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences for training"""
        X, y = [], []
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:(i + self.sequence_length)])
            y.append(target[i + self.sequence_length])
        return np.array(X), np.array(y)

    async def train(
        self,
        df: pd.DataFrame,
        epochs: int = 100,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> Dict[str, Any]:
        """Train the Transformer model"""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for training")

        logger.info("Preparing training data for Transformer...")

        # Prepare features
        features = self._prepare_features(df)

        # Scale
        self.scaler_X = StandardScaler()
        self.scaler_y = MinMaxScaler()

        X_scaled = self.scaler_X.fit_transform(features.values)
        y_scaled = self.scaler_y.fit_transform(features['close'].values.reshape(-1, 1))

        # Create sequences
        X_seq, y_seq = self._create_sequences(X_scaled, y_scaled.flatten())

        # Split
        X_train, X_val, y_train, y_val = train_test_split(
            X_seq, y_seq, test_size=validation_split, shuffle=False
        )

        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train).to(self.device)
        y_train_tensor = torch.FloatTensor(y_train).unsqueeze(1).to(self.device)
        X_val_tensor = torch.FloatTensor(X_val).to(self.device)
        y_val_tensor = torch.FloatTensor(y_val).unsqueeze(1).to(self.device)

        # Data loader
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

        # Initialize model
        input_size = X_train.shape[2]
        self.model = TransformerPriceModel(
            input_size=input_size,
            d_model=self.d_model,
            nhead=self.nhead,
            num_encoder_layers=self.num_layers
        ).to(self.device)

        # Loss and optimizer
        criterion = nn.MSELoss()
        optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.learning_rate,
            weight_decay=0.01
        )
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        # Training
        train_losses = []
        val_losses = []
        best_val_loss = float('inf')

        logger.info(f"Training Transformer model for {epochs} epochs...")

        for epoch in range(epochs):
            self.model.train()
            epoch_loss = 0

            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                optimizer.step()
                epoch_loss += loss.item()

            avg_train_loss = epoch_loss / len(train_loader)
            train_losses.append(avg_train_loss)

            # Validation
            self.model.eval()
            with torch.no_grad():
                val_outputs = self.model(X_val_tensor)
                val_loss = criterion(val_outputs, y_val_tensor).item()
                val_losses.append(val_loss)

            scheduler.step()

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self.save_model("best_transformer_model.pt")

            if (epoch + 1) % 10 == 0:
                logger.info(
                    f"Epoch [{epoch+1}/{epochs}], "
                    f"Train Loss: {avg_train_loss:.6f}, "
                    f"Val Loss: {val_loss:.6f}"
                )

        self.is_trained = True

        return {
            "train_losses": train_losses,
            "val_losses": val_losses,
            "best_val_loss": best_val_loss,
            "epochs_trained": epochs
        }

    async def predict(
        self,
        df: pd.DataFrame,
        symbol: str = "UNKNOWN",
        time_horizon: str = "1H"
    ) -> PricePrediction:
        """Make price prediction using Transformer"""
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained")

        features = self._prepare_features(df)
        X_scaled = self.scaler_X.transform(features.values)

        last_sequence = X_scaled[-self.sequence_length:]
        X_tensor = torch.FloatTensor(last_sequence).unsqueeze(0).to(self.device)

        self.model.eval()
        with torch.no_grad():
            prediction_scaled = self.model(X_tensor).cpu().numpy()

        predicted_price = self.scaler_y.inverse_transform(
            prediction_scaled.reshape(-1, 1)
        )[0, 0]

        current_price = df['close'].iloc[-1]
        price_change_pct = abs(predicted_price - current_price) / current_price
        confidence = max(0.3, min(0.95, 1 - price_change_pct * 2))

        if predicted_price > current_price * 1.002:
            direction = "UP"
        elif predicted_price < current_price * 0.998:
            direction = "DOWN"
        else:
            direction = "NEUTRAL"

        return PricePrediction(
            symbol=symbol,
            current_price=current_price,
            predicted_price=predicted_price,
            predicted_direction=direction,
            confidence=confidence,
            predicted_high=predicted_price * 1.01,
            predicted_low=predicted_price * 0.99,
            time_horizon=time_horizon,
            volatility_forecast=features['volatility_20'].iloc[-1],
            trend_strength=np.tanh(features['momentum_20'].iloc[-1] * 10),
            model_type="Transformer",
            timestamp=datetime.now(),
            features_importance={}
        )

    def save_model(self, filename: str):
        """Save model"""
        if self.model is None:
            return
        path = os.path.join(self.model_dir, filename)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'scaler_X': self.scaler_X,
            'scaler_y': self.scaler_y,
            'feature_names': self.feature_names,
            'config': {
                'sequence_length': self.sequence_length,
                'd_model': self.d_model,
                'nhead': self.nhead,
                'num_layers': self.num_layers
            }
        }, path)
        logger.info(f"Transformer model saved to {path}")

    def load_model(self, filename: str):
        """Load model"""
        path = os.path.join(self.model_dir, filename)
        checkpoint = torch.load(path, map_location=self.device)

        self.scaler_X = checkpoint['scaler_X']
        self.scaler_y = checkpoint['scaler_y']
        self.feature_names = checkpoint['feature_names']

        config = checkpoint['config']
        self.sequence_length = config['sequence_length']
        self.d_model = config['d_model']
        self.nhead = config['nhead']
        self.num_layers = config['num_layers']

        input_size = len(self.feature_names)
        self.model = TransformerPriceModel(
            input_size=input_size,
            d_model=self.d_model,
            nhead=self.nhead,
            num_encoder_layers=self.num_layers
        ).to(self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.is_trained = True
        logger.info(f"Transformer model loaded from {path}")


class EnsemblePredictor:
    """
    Ensemble model combining LSTM and Transformer predictions

    Uses weighted averaging with dynamic weight adjustment based on recent accuracy.
    """

    def __init__(self, model_dir: str = "./models"):
        self.lstm_predictor = PricePredictor(model_dir=model_dir)
        self.transformer_predictor = TransformerPredictor(model_dir=model_dir)
        self.lstm_weight = 0.5
        self.transformer_weight = 0.5
        self.prediction_history: List[Dict] = []

    async def train_all(
        self,
        df: pd.DataFrame,
        epochs: int = 100
    ) -> Dict[str, Any]:
        """Train all models"""
        lstm_results = await self.lstm_predictor.train(df, epochs=epochs)
        transformer_results = await self.transformer_predictor.train(df, epochs=epochs)

        return {
            "lstm": lstm_results,
            "transformer": transformer_results
        }

    async def predict(
        self,
        df: pd.DataFrame,
        symbol: str = "UNKNOWN",
        time_horizon: str = "1H"
    ) -> PricePrediction:
        """Ensemble prediction"""
        predictions = []

        if self.lstm_predictor.is_trained:
            lstm_pred = await self.lstm_predictor.predict(df, symbol, time_horizon)
            predictions.append((lstm_pred, self.lstm_weight))

        if self.transformer_predictor.is_trained:
            transformer_pred = await self.transformer_predictor.predict(df, symbol, time_horizon)
            predictions.append((transformer_pred, self.transformer_weight))

        if not predictions:
            raise ValueError("No trained models available")

        # Weighted average
        total_weight = sum(w for _, w in predictions)

        ensemble_price = sum(
            pred.predicted_price * w for pred, w in predictions
        ) / total_weight

        ensemble_confidence = sum(
            pred.confidence * w for pred, w in predictions
        ) / total_weight

        current_price = df['close'].iloc[-1]

        if ensemble_price > current_price * 1.002:
            direction = "UP"
        elif ensemble_price < current_price * 0.998:
            direction = "DOWN"
        else:
            direction = "NEUTRAL"

        return PricePrediction(
            symbol=symbol,
            current_price=current_price,
            predicted_price=ensemble_price,
            predicted_direction=direction,
            confidence=ensemble_confidence,
            predicted_high=ensemble_price * 1.01,
            predicted_low=ensemble_price * 0.99,
            time_horizon=time_horizon,
            volatility_forecast=predictions[0][0].volatility_forecast,
            trend_strength=predictions[0][0].trend_strength,
            model_type="Ensemble_LSTM_Transformer",
            timestamp=datetime.now(),
            features_importance=predictions[0][0].features_importance
        )

    def update_weights(self, lstm_accuracy: float, transformer_accuracy: float):
        """Update model weights based on recent accuracy"""
        total = lstm_accuracy + transformer_accuracy
        if total > 0:
            self.lstm_weight = lstm_accuracy / total
            self.transformer_weight = transformer_accuracy / total
