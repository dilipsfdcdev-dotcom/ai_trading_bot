"""
Pattern Recognition CNN for Chart Pattern Detection

Advanced convolutional neural network for recognizing:
- Candlestick patterns (Doji, Hammer, Engulfing, etc.)
- Chart patterns (Head & Shoulders, Double Top/Bottom, Triangles, etc.)
- Support/Resistance levels
- Trend patterns
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
import os
from datetime import datetime

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class PatternType(Enum):
    # Candlestick Patterns
    DOJI = "doji"
    HAMMER = "hammer"
    INVERTED_HAMMER = "inverted_hammer"
    BULLISH_ENGULFING = "bullish_engulfing"
    BEARISH_ENGULFING = "bearish_engulfing"
    MORNING_STAR = "morning_star"
    EVENING_STAR = "evening_star"
    THREE_WHITE_SOLDIERS = "three_white_soldiers"
    THREE_BLACK_CROWS = "three_black_crows"
    PIERCING_LINE = "piercing_line"
    DARK_CLOUD_COVER = "dark_cloud_cover"
    HARAMI = "harami"

    # Chart Patterns
    HEAD_AND_SHOULDERS = "head_and_shoulders"
    INVERSE_HEAD_AND_SHOULDERS = "inverse_head_and_shoulders"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    TRIPLE_TOP = "triple_top"
    TRIPLE_BOTTOM = "triple_bottom"
    ASCENDING_TRIANGLE = "ascending_triangle"
    DESCENDING_TRIANGLE = "descending_triangle"
    SYMMETRICAL_TRIANGLE = "symmetrical_triangle"
    RISING_WEDGE = "rising_wedge"
    FALLING_WEDGE = "falling_wedge"
    CHANNEL_UP = "channel_up"
    CHANNEL_DOWN = "channel_down"
    FLAG_BULLISH = "flag_bullish"
    FLAG_BEARISH = "flag_bearish"

    # Trend Patterns
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    CONSOLIDATION = "consolidation"
    BREAKOUT_UP = "breakout_up"
    BREAKOUT_DOWN = "breakout_down"
    REVERSAL_BULLISH = "reversal_bullish"
    REVERSAL_BEARISH = "reversal_bearish"


@dataclass
class PatternDetection:
    """Result of pattern detection"""
    pattern_type: str
    confidence: float  # 0-1
    signal: str  # BUY, SELL, NEUTRAL
    strength: float  # 0-1
    start_index: int
    end_index: int
    price_target: Optional[float]
    stop_loss: Optional[float]
    description: str
    timestamp: datetime

    def to_dict(self) -> Dict:
        return {
            "pattern_type": self.pattern_type,
            "confidence": self.confidence,
            "signal": self.signal,
            "strength": self.strength,
            "start_index": self.start_index,
            "end_index": self.end_index,
            "price_target": self.price_target,
            "stop_loss": self.stop_loss,
            "description": self.description,
            "timestamp": self.timestamp.isoformat()
        }


class ConvBlock(nn.Module):
    """Convolutional block with batch norm and residual connection"""

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int = 3,
        stride: int = 1
    ):
        super().__init__()

        self.conv1 = nn.Conv1d(
            in_channels, out_channels, kernel_size,
            stride=stride, padding=kernel_size // 2
        )
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.conv2 = nn.Conv1d(
            out_channels, out_channels, kernel_size,
            padding=kernel_size // 2
        )
        self.bn2 = nn.BatchNorm1d(out_channels)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, 1, stride=stride),
                nn.BatchNorm1d(out_channels)
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += self.shortcut(x)
        out = F.relu(out)
        return out


class MultiScaleCNN(nn.Module):
    """
    Multi-scale CNN for pattern recognition

    Uses multiple kernel sizes to capture patterns at different scales.
    """

    def __init__(
        self,
        input_channels: int = 5,  # OHLCV
        num_classes: int = 30,  # Number of pattern types
        sequence_length: int = 100
    ):
        super().__init__()

        self.sequence_length = sequence_length

        # Multi-scale convolutions
        self.conv_small = nn.Sequential(
            nn.Conv1d(input_channels, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm1d(64)
        )

        self.conv_medium = nn.Sequential(
            nn.Conv1d(input_channels, 32, kernel_size=7, padding=3),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Conv1d(32, 64, kernel_size=7, padding=3),
            nn.ReLU(),
            nn.BatchNorm1d(64)
        )

        self.conv_large = nn.Sequential(
            nn.Conv1d(input_channels, 32, kernel_size=15, padding=7),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Conv1d(32, 64, kernel_size=15, padding=7),
            nn.ReLU(),
            nn.BatchNorm1d(64)
        )

        # Feature fusion
        self.fusion = nn.Sequential(
            nn.Conv1d(64 * 3, 128, kernel_size=1),
            nn.ReLU(),
            nn.BatchNorm1d(128)
        )

        # Deeper processing with residual blocks
        self.res_blocks = nn.Sequential(
            ConvBlock(128, 128),
            nn.MaxPool1d(2),
            ConvBlock(128, 256),
            nn.MaxPool1d(2),
            ConvBlock(256, 256),
            nn.AdaptiveAvgPool1d(1)
        )

        # Classifier
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )

        # Confidence head
        self.confidence_head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )

    def forward(
        self,
        x: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        # Multi-scale features
        small_features = self.conv_small(x)
        medium_features = self.conv_medium(x)
        large_features = self.conv_large(x)

        # Concatenate
        multi_scale = torch.cat(
            [small_features, medium_features, large_features],
            dim=1
        )

        # Fusion
        fused = self.fusion(multi_scale)

        # Residual processing
        features = self.res_blocks(fused)

        # Classification
        logits = self.classifier(features)
        confidence = self.confidence_head(features)

        return logits, confidence


class PatternRecognitionCNN:
    """
    Pattern Recognition System using CNN

    Features:
    - Multi-scale pattern detection
    - Candlestick pattern recognition
    - Chart pattern recognition
    - Real-time pattern scanning
    """

    def __init__(
        self,
        sequence_length: int = 100,
        model_dir: str = "./models"
    ):
        self.sequence_length = sequence_length
        self.model_dir = model_dir
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Pattern labels
        self.pattern_labels = [p.value for p in PatternType]
        self.num_classes = len(self.pattern_labels)

        self.model: Optional[MultiScaleCNN] = None
        self.scaler: Optional[StandardScaler] = None
        self.is_trained = False

        os.makedirs(model_dir, exist_ok=True)
        logger.info(f"PatternRecognitionCNN initialized on device: {self.device}")

    def _detect_candlestick_patterns(
        self,
        df: pd.DataFrame
    ) -> List[PatternDetection]:
        """Detect candlestick patterns using rule-based logic"""
        patterns = []

        o = df['open'].values
        h = df['high'].values
        l = df['low'].values
        c = df['close'].values

        body = c - o
        body_abs = np.abs(body)
        upper_shadow = h - np.maximum(o, c)
        lower_shadow = np.minimum(o, c) - l
        candle_range = h - l

        for i in range(2, len(df)):
            # Doji
            if body_abs[i] < candle_range[i] * 0.1:
                patterns.append(PatternDetection(
                    pattern_type=PatternType.DOJI.value,
                    confidence=0.8,
                    signal="NEUTRAL",
                    strength=0.5,
                    start_index=i,
                    end_index=i,
                    price_target=None,
                    stop_loss=None,
                    description="Doji - Indecision, potential reversal",
                    timestamp=datetime.now()
                ))

            # Hammer (bullish)
            if (lower_shadow[i] > body_abs[i] * 2 and
                upper_shadow[i] < body_abs[i] * 0.5 and
                body[i-1] < 0):  # Previous candle bearish
                patterns.append(PatternDetection(
                    pattern_type=PatternType.HAMMER.value,
                    confidence=0.75,
                    signal="BUY",
                    strength=0.7,
                    start_index=i,
                    end_index=i,
                    price_target=c[i] + candle_range[i] * 2,
                    stop_loss=l[i],
                    description="Hammer - Bullish reversal signal",
                    timestamp=datetime.now()
                ))

            # Inverted Hammer
            if (upper_shadow[i] > body_abs[i] * 2 and
                lower_shadow[i] < body_abs[i] * 0.5 and
                body[i-1] < 0):
                patterns.append(PatternDetection(
                    pattern_type=PatternType.INVERTED_HAMMER.value,
                    confidence=0.7,
                    signal="BUY",
                    strength=0.6,
                    start_index=i,
                    end_index=i,
                    price_target=c[i] + candle_range[i] * 1.5,
                    stop_loss=l[i],
                    description="Inverted Hammer - Potential bullish reversal",
                    timestamp=datetime.now()
                ))

            # Bullish Engulfing
            if (i >= 1 and
                body[i-1] < 0 and body[i] > 0 and
                o[i] < c[i-1] and c[i] > o[i-1]):
                patterns.append(PatternDetection(
                    pattern_type=PatternType.BULLISH_ENGULFING.value,
                    confidence=0.85,
                    signal="BUY",
                    strength=0.8,
                    start_index=i-1,
                    end_index=i,
                    price_target=c[i] + body_abs[i],
                    stop_loss=l[i-1],
                    description="Bullish Engulfing - Strong buy signal",
                    timestamp=datetime.now()
                ))

            # Bearish Engulfing
            if (i >= 1 and
                body[i-1] > 0 and body[i] < 0 and
                o[i] > c[i-1] and c[i] < o[i-1]):
                patterns.append(PatternDetection(
                    pattern_type=PatternType.BEARISH_ENGULFING.value,
                    confidence=0.85,
                    signal="SELL",
                    strength=0.8,
                    start_index=i-1,
                    end_index=i,
                    price_target=c[i] - body_abs[i],
                    stop_loss=h[i-1],
                    description="Bearish Engulfing - Strong sell signal",
                    timestamp=datetime.now()
                ))

            # Morning Star (3 candles)
            if i >= 2:
                if (body[i-2] < 0 and  # First candle bearish
                    body_abs[i-1] < body_abs[i-2] * 0.3 and  # Small middle candle
                    body[i] > 0 and  # Third candle bullish
                    c[i] > (o[i-2] + c[i-2]) / 2):  # Closes above midpoint
                    patterns.append(PatternDetection(
                        pattern_type=PatternType.MORNING_STAR.value,
                        confidence=0.85,
                        signal="BUY",
                        strength=0.85,
                        start_index=i-2,
                        end_index=i,
                        price_target=c[i] + body_abs[i-2],
                        stop_loss=min(l[i-2], l[i-1], l[i]),
                        description="Morning Star - Strong bullish reversal",
                        timestamp=datetime.now()
                    ))

            # Evening Star (3 candles)
            if i >= 2:
                if (body[i-2] > 0 and  # First candle bullish
                    body_abs[i-1] < body_abs[i-2] * 0.3 and  # Small middle candle
                    body[i] < 0 and  # Third candle bearish
                    c[i] < (o[i-2] + c[i-2]) / 2):
                    patterns.append(PatternDetection(
                        pattern_type=PatternType.EVENING_STAR.value,
                        confidence=0.85,
                        signal="SELL",
                        strength=0.85,
                        start_index=i-2,
                        end_index=i,
                        price_target=c[i] - body_abs[i-2],
                        stop_loss=max(h[i-2], h[i-1], h[i]),
                        description="Evening Star - Strong bearish reversal",
                        timestamp=datetime.now()
                    ))

            # Three White Soldiers
            if i >= 2:
                if (body[i-2] > 0 and body[i-1] > 0 and body[i] > 0 and
                    c[i-1] > c[i-2] and c[i] > c[i-1] and
                    o[i-1] > o[i-2] and o[i] > o[i-1]):
                    patterns.append(PatternDetection(
                        pattern_type=PatternType.THREE_WHITE_SOLDIERS.value,
                        confidence=0.9,
                        signal="BUY",
                        strength=0.9,
                        start_index=i-2,
                        end_index=i,
                        price_target=c[i] + (c[i] - c[i-2]),
                        stop_loss=l[i-2],
                        description="Three White Soldiers - Very strong bullish signal",
                        timestamp=datetime.now()
                    ))

            # Three Black Crows
            if i >= 2:
                if (body[i-2] < 0 and body[i-1] < 0 and body[i] < 0 and
                    c[i-1] < c[i-2] and c[i] < c[i-1] and
                    o[i-1] < o[i-2] and o[i] < o[i-1]):
                    patterns.append(PatternDetection(
                        pattern_type=PatternType.THREE_BLACK_CROWS.value,
                        confidence=0.9,
                        signal="SELL",
                        strength=0.9,
                        start_index=i-2,
                        end_index=i,
                        price_target=c[i] - (c[i-2] - c[i]),
                        stop_loss=h[i-2],
                        description="Three Black Crows - Very strong bearish signal",
                        timestamp=datetime.now()
                    ))

        return patterns

    def _detect_chart_patterns(
        self,
        df: pd.DataFrame,
        window: int = 20
    ) -> List[PatternDetection]:
        """Detect chart patterns using pivot points"""
        patterns = []
        c = df['close'].values
        h = df['high'].values
        l = df['low'].values

        # Find pivot points
        pivot_highs = []
        pivot_lows = []

        for i in range(window, len(df) - window):
            if h[i] == max(h[i-window:i+window+1]):
                pivot_highs.append((i, h[i]))
            if l[i] == min(l[i-window:i+window+1]):
                pivot_lows.append((i, l[i]))

        # Double Top detection
        for i in range(1, len(pivot_highs)):
            ph1_idx, ph1_val = pivot_highs[i-1]
            ph2_idx, ph2_val = pivot_highs[i]

            if abs(ph1_val - ph2_val) / ph1_val < 0.02:  # Within 2%
                # Find trough between peaks
                trough_val = min(l[ph1_idx:ph2_idx+1])
                neckline = trough_val

                patterns.append(PatternDetection(
                    pattern_type=PatternType.DOUBLE_TOP.value,
                    confidence=0.8,
                    signal="SELL",
                    strength=0.75,
                    start_index=ph1_idx,
                    end_index=ph2_idx,
                    price_target=neckline - (ph1_val - neckline),
                    stop_loss=max(ph1_val, ph2_val) * 1.01,
                    description="Double Top - Bearish reversal pattern",
                    timestamp=datetime.now()
                ))

        # Double Bottom detection
        for i in range(1, len(pivot_lows)):
            pl1_idx, pl1_val = pivot_lows[i-1]
            pl2_idx, pl2_val = pivot_lows[i]

            if abs(pl1_val - pl2_val) / pl1_val < 0.02:
                peak_val = max(h[pl1_idx:pl2_idx+1])
                neckline = peak_val

                patterns.append(PatternDetection(
                    pattern_type=PatternType.DOUBLE_BOTTOM.value,
                    confidence=0.8,
                    signal="BUY",
                    strength=0.75,
                    start_index=pl1_idx,
                    end_index=pl2_idx,
                    price_target=neckline + (neckline - pl1_val),
                    stop_loss=min(pl1_val, pl2_val) * 0.99,
                    description="Double Bottom - Bullish reversal pattern",
                    timestamp=datetime.now()
                ))

        # Head and Shoulders detection
        if len(pivot_highs) >= 3:
            for i in range(2, len(pivot_highs)):
                left_idx, left_val = pivot_highs[i-2]
                head_idx, head_val = pivot_highs[i-1]
                right_idx, right_val = pivot_highs[i]

                # Head should be higher than shoulders
                if (head_val > left_val and head_val > right_val and
                    abs(left_val - right_val) / left_val < 0.03):

                    # Find neckline
                    trough1 = min(l[left_idx:head_idx+1])
                    trough2 = min(l[head_idx:right_idx+1])
                    neckline = (trough1 + trough2) / 2

                    patterns.append(PatternDetection(
                        pattern_type=PatternType.HEAD_AND_SHOULDERS.value,
                        confidence=0.85,
                        signal="SELL",
                        strength=0.85,
                        start_index=left_idx,
                        end_index=right_idx,
                        price_target=neckline - (head_val - neckline),
                        stop_loss=head_val * 1.01,
                        description="Head and Shoulders - Strong bearish reversal",
                        timestamp=datetime.now()
                    ))

        # Inverse Head and Shoulders
        if len(pivot_lows) >= 3:
            for i in range(2, len(pivot_lows)):
                left_idx, left_val = pivot_lows[i-2]
                head_idx, head_val = pivot_lows[i-1]
                right_idx, right_val = pivot_lows[i]

                if (head_val < left_val and head_val < right_val and
                    abs(left_val - right_val) / left_val < 0.03):

                    peak1 = max(h[left_idx:head_idx+1])
                    peak2 = max(h[head_idx:right_idx+1])
                    neckline = (peak1 + peak2) / 2

                    patterns.append(PatternDetection(
                        pattern_type=PatternType.INVERSE_HEAD_AND_SHOULDERS.value,
                        confidence=0.85,
                        signal="BUY",
                        strength=0.85,
                        start_index=left_idx,
                        end_index=right_idx,
                        price_target=neckline + (neckline - head_val),
                        stop_loss=head_val * 0.99,
                        description="Inverse Head and Shoulders - Strong bullish reversal",
                        timestamp=datetime.now()
                    ))

        # Trend detection
        if len(c) >= 20:
            recent_prices = c[-20:]
            slope = np.polyfit(range(20), recent_prices, 1)[0]
            price_range = max(recent_prices) - min(recent_prices)
            normalized_slope = slope * 20 / price_range if price_range > 0 else 0

            if normalized_slope > 0.3:
                patterns.append(PatternDetection(
                    pattern_type=PatternType.UPTREND.value,
                    confidence=min(0.95, 0.5 + abs(normalized_slope)),
                    signal="BUY",
                    strength=min(0.9, abs(normalized_slope)),
                    start_index=len(c) - 20,
                    end_index=len(c) - 1,
                    price_target=c[-1] * 1.02,
                    stop_loss=min(recent_prices) * 0.99,
                    description="Uptrend detected",
                    timestamp=datetime.now()
                ))
            elif normalized_slope < -0.3:
                patterns.append(PatternDetection(
                    pattern_type=PatternType.DOWNTREND.value,
                    confidence=min(0.95, 0.5 + abs(normalized_slope)),
                    signal="SELL",
                    strength=min(0.9, abs(normalized_slope)),
                    start_index=len(c) - 20,
                    end_index=len(c) - 1,
                    price_target=c[-1] * 0.98,
                    stop_loss=max(recent_prices) * 1.01,
                    description="Downtrend detected",
                    timestamp=datetime.now()
                ))
            else:
                patterns.append(PatternDetection(
                    pattern_type=PatternType.CONSOLIDATION.value,
                    confidence=0.7,
                    signal="NEUTRAL",
                    strength=0.5,
                    start_index=len(c) - 20,
                    end_index=len(c) - 1,
                    price_target=None,
                    stop_loss=None,
                    description="Consolidation - Sideways movement",
                    timestamp=datetime.now()
                ))

        return patterns

    def _prepare_data(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare OHLCV data for CNN"""
        data = df[['open', 'high', 'low', 'close']].copy()

        if 'volume' in df.columns:
            data['volume'] = df['volume']
        else:
            data['volume'] = 0

        # Normalize
        if self.scaler is None:
            self.scaler = StandardScaler()
            normalized = self.scaler.fit_transform(data.values)
        else:
            normalized = self.scaler.transform(data.values)

        return normalized

    async def detect_patterns(
        self,
        df: pd.DataFrame,
        symbol: str = "UNKNOWN"
    ) -> Dict[str, Any]:
        """
        Detect all patterns in the data

        Returns combined candlestick and chart patterns
        """
        # Rule-based candlestick patterns
        candlestick_patterns = self._detect_candlestick_patterns(df)

        # Chart patterns
        chart_patterns = self._detect_chart_patterns(df)

        # Combine all patterns
        all_patterns = candlestick_patterns + chart_patterns

        # Sort by confidence
        all_patterns.sort(key=lambda x: x.confidence, reverse=True)

        # Calculate overall signal
        buy_signals = [p for p in all_patterns if p.signal == "BUY"]
        sell_signals = [p for p in all_patterns if p.signal == "SELL"]

        if buy_signals and not sell_signals:
            overall_signal = "BUY"
            overall_confidence = np.mean([p.confidence for p in buy_signals])
        elif sell_signals and not buy_signals:
            overall_signal = "SELL"
            overall_confidence = np.mean([p.confidence for p in sell_signals])
        elif buy_signals and sell_signals:
            buy_strength = sum(p.confidence * p.strength for p in buy_signals)
            sell_strength = sum(p.confidence * p.strength for p in sell_signals)

            if buy_strength > sell_strength * 1.2:
                overall_signal = "BUY"
                overall_confidence = buy_strength / (buy_strength + sell_strength)
            elif sell_strength > buy_strength * 1.2:
                overall_signal = "SELL"
                overall_confidence = sell_strength / (buy_strength + sell_strength)
            else:
                overall_signal = "NEUTRAL"
                overall_confidence = 0.5
        else:
            overall_signal = "NEUTRAL"
            overall_confidence = 0.5

        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "patterns": [p.to_dict() for p in all_patterns[:10]],  # Top 10
            "pattern_count": len(all_patterns),
            "overall_signal": overall_signal,
            "overall_confidence": overall_confidence,
            "bullish_patterns": len(buy_signals),
            "bearish_patterns": len(sell_signals),
            "neutral_patterns": len(all_patterns) - len(buy_signals) - len(sell_signals)
        }

    async def train_cnn(
        self,
        training_data: List[Tuple[pd.DataFrame, str]],
        epochs: int = 50,
        batch_size: int = 32
    ) -> Dict[str, Any]:
        """Train the CNN model on labeled data"""
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for training")

        logger.info("Preparing training data for CNN...")

        X_list = []
        y_list = []

        for df, label in training_data:
            if len(df) < self.sequence_length:
                continue

            # Get last sequence
            data = self._prepare_data(df.tail(self.sequence_length))
            X_list.append(data)

            # Convert label to index
            if label in self.pattern_labels:
                y_list.append(self.pattern_labels.index(label))
            else:
                continue

        if not X_list:
            raise ValueError("No valid training data")

        X = np.array(X_list)
        y = np.array(y_list)

        # Reshape for CNN: (batch, channels, sequence)
        X = X.transpose(0, 2, 1)

        # Convert to tensors
        X_tensor = torch.FloatTensor(X).to(self.device)
        y_tensor = torch.LongTensor(y).to(self.device)

        # Create data loader
        dataset = TensorDataset(X_tensor, y_tensor)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        # Initialize model
        self.model = MultiScaleCNN(
            input_channels=X.shape[1],
            num_classes=self.num_classes,
            sequence_length=self.sequence_length
        ).to(self.device)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.001)

        losses = []

        for epoch in range(epochs):
            self.model.train()
            epoch_loss = 0

            for batch_X, batch_y in loader:
                optimizer.zero_grad()
                logits, _ = self.model(batch_X)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(loader)
            losses.append(avg_loss)

            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.4f}")

        self.is_trained = True
        self.save_model("pattern_cnn.pt")

        return {
            "epochs_trained": epochs,
            "final_loss": losses[-1],
            "loss_history": losses
        }

    async def predict_pattern_cnn(
        self,
        df: pd.DataFrame
    ) -> Tuple[str, float]:
        """Predict pattern using trained CNN"""
        if not self.is_trained or self.model is None:
            return "unknown", 0.0

        data = self._prepare_data(df.tail(self.sequence_length))
        X = data.transpose(1, 0)  # (channels, sequence)
        X_tensor = torch.FloatTensor(X).unsqueeze(0).to(self.device)

        self.model.eval()
        with torch.no_grad():
            logits, confidence = self.model(X_tensor)
            probs = F.softmax(logits, dim=1)
            pred_class = torch.argmax(probs, dim=1).item()
            pred_prob = probs[0, pred_class].item()

        pattern_name = self.pattern_labels[pred_class]
        return pattern_name, pred_prob * confidence.item()

    def save_model(self, filename: str):
        """Save model to disk"""
        if self.model is None:
            return

        path = os.path.join(self.model_dir, filename)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'scaler': self.scaler,
            'pattern_labels': self.pattern_labels,
            'sequence_length': self.sequence_length
        }, path)
        logger.info(f"Pattern CNN saved to {path}")

    def load_model(self, filename: str):
        """Load model from disk"""
        path = os.path.join(self.model_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found at {path}")

        checkpoint = torch.load(path, map_location=self.device)
        self.scaler = checkpoint['scaler']
        self.pattern_labels = checkpoint['pattern_labels']
        self.sequence_length = checkpoint['sequence_length']

        self.model = MultiScaleCNN(
            input_channels=5,
            num_classes=len(self.pattern_labels),
            sequence_length=self.sequence_length
        ).to(self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.is_trained = True
        logger.info(f"Pattern CNN loaded from {path}")
