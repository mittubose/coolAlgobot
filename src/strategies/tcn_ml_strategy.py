"""
TCN Neural Network Strategy

ML-based trading strategy using Temporal Convolutional Networks.
Integrates with existing strategy framework and OMS.
"""

import pandas as pd
import numpy as np
import torch
from typing import Dict, Optional
from pathlib import Path

# Import ML components
import sys
sys.path.append(str(Path(__file__).parent.parent))

from ml.feature_engineering import FeatureEngineer
from ml.data_pipeline import TimeSeriesDataPipeline
from ml.models.tcn_model import TCNTradingModel
from ml.volatility_scaler import VolatilityScaler


class TCNMLStrategy:
    """
    Machine Learning Strategy using Temporal Convolutional Networks.

    Generates probabilistic trading signals (0-1) with volatility-scaled
    position sizing.

    Parameters:
        model_path: Path to trained model checkpoint
        confidence_threshold: Minimum confidence to trade (default: 0.6)
        risk_per_trade: Risk per trade as % of capital (default: 0.02)
        enable_volatility_scaling: Use volatility-based position sizing (default: True)
    """

    def __init__(self, parameters: Dict):
        """
        Initialize TCN ML Strategy

        Args:
            parameters: Strategy parameters dict with keys:
                - model_path: Path to model checkpoint
                - confidence_threshold: Min confidence (default: 0.6)
                - risk_per_trade: Risk % (default: 0.02)
                - enable_volatility_scaling: Bool (default: True)
        """
        self.model_path = parameters.get('model_path')
        self.confidence_threshold = parameters.get('confidence_threshold', 0.6)
        self.risk_per_trade = parameters.get('risk_per_trade', 0.02)
        self.enable_volatility_scaling = parameters.get('enable_volatility_scaling', True)

        # Initialize components
        self.feature_engineer = FeatureEngineer()
        self.data_pipeline = TimeSeriesDataPipeline(window_size=64)
        self.volatility_scaler = VolatilityScaler(
            w_min=0.1,
            w_max=1.0,
            deadband_threshold=0.1
        )

        # Load model
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        if self.model_path and Path(self.model_path).exists():
            self._load_model()
        else:
            print(f"Warning: Model not found at {self.model_path}. Strategy will not work until model is loaded.")

        # State
        self.last_signal = None
        self.feature_stats = None

    def _load_model(self):
        """Load trained model from checkpoint"""
        try:
            checkpoint = torch.load(self.model_path, map_location=self.device)

            # Create model (default architecture)
            self.model = TCNTradingModel(
                num_features=12,
                seq_length=64,
                tcn_channels=[64, 128, 128],
                kernel_size=3,
                dropout=0.3
            )

            # Load weights
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model = self.model.to(self.device)
            self.model.eval()

            print(f"✓ TCN model loaded from {self.model_path}")

        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None

    def generate_signal(
        self,
        symbol: str,
        exchange: str,
        quote: Dict,
        historical_data: pd.DataFrame,
        has_position: bool
    ) -> Optional[Dict]:
        """
        Generate trading signal using TCN model.

        Args:
            symbol: Trading symbol
            exchange: Exchange
            quote: Current quote data
            historical_data: Historical OHLC DataFrame (need 200+ rows)
            has_position: Whether we already have a position

        Returns:
            Signal dict or None

        Example:
            >>> signal = strategy.generate_signal(
            ...     'RELIANCE', 'NSE', quote, historical_df, has_position=False
            ... )
            >>> if signal:
            ...     print(f"Action: {signal['action']}, Confidence: {signal['confidence']}")
        """
        try:
            # Validate model loaded
            if self.model is None:
                print("Error: Model not loaded. Cannot generate signal.")
                return None

            # Need sufficient data for feature engineering
            min_required = max(64, 50)  # Window size + feature calculation buffer
            if len(historical_data) < min_required:
                return None

            # Step 1: Engineer features
            features_df = self.feature_engineer.engineer_features(
                historical_data,
                fit_normalization=(self.feature_stats is None)
            )

            if self.feature_stats is None:
                self.feature_stats = self.feature_engineer.feature_stats

            # Step 2: Create rolling window (get last 64 timesteps)
            if len(features_df) < 64:
                return None

            # Get latest window
            feature_window = features_df.iloc[-64:].values  # (64, 12)

            # Convert to tensor
            X = torch.FloatTensor(feature_window).unsqueeze(0).to(self.device)  # (1, 64, 12)

            # Step 3: Model prediction
            self.model.eval()
            with torch.no_grad():
                probability = self.model(X).item()

            # Step 4: Volatility scaling (if enabled)
            current_price = quote.get('last_price', historical_data['close'].iloc[-1])

            if self.enable_volatility_scaling:
                # Calculate returns and volatility
                returns = historical_data['close'].pct_change().dropna().values

                if len(returns) >= 20:
                    # Update reference volatility
                    self.volatility_scaler.update_reference_volatility(returns)

                    # Calculate current volatility
                    current_vol = self.volatility_scaler.calculate_volatility(returns)

                    # Scale position
                    position_size, explanation = self.volatility_scaler.scale_position(
                        probability,
                        current_vol
                    )
                else:
                    position_size = 2 * probability - 1  # Raw signal without scaling
                    explanation = "Insufficient data for volatility scaling"
            else:
                position_size = 2 * probability - 1
                explanation = "Volatility scaling disabled"

            # Step 5: Generate trading signal
            signal = None

            # Bullish signal (probability > threshold)
            if probability > self.confidence_threshold and position_size > 0 and not has_position:
                # Calculate stop-loss and target
                atr = self._calculate_atr(historical_data)
                stop_loss = current_price - (1.5 * atr)
                target = current_price + (3.0 * atr)  # 2:1 risk-reward

                signal = {
                    'action': 'BUY',
                    'symbol': symbol,
                    'exchange': exchange,
                    'price': current_price,
                    'stop_loss': stop_loss,
                    'target': target,
                    'confidence': probability,
                    'position_size': abs(position_size),
                    'reason': f'TCN ML Signal (Confidence: {probability:.2%}, {explanation})',
                    'indicators': {
                        'ml_probability': probability,
                        'position_size': position_size,
                        'volatility_scaling': explanation
                    }
                }

            # Bearish signal (probability < 1 - threshold)
            elif probability < (1 - self.confidence_threshold) and position_size < 0:
                if has_position:
                    # Exit long position
                    signal = {
                        'action': 'CLOSE',
                        'symbol': symbol,
                        'exchange': exchange,
                        'price': current_price,
                        'confidence': 1 - probability,
                        'reason': f'TCN ML Exit Signal (Confidence: {1-probability:.2%})'
                    }
                else:
                    # Short signal (if enabled)
                    atr = self._calculate_atr(historical_data)
                    stop_loss = current_price + (1.5 * atr)
                    target = current_price - (3.0 * atr)

                    signal = {
                        'action': 'SELL',
                        'symbol': symbol,
                        'exchange': exchange,
                        'price': current_price,
                        'stop_loss': stop_loss,
                        'target': target,
                        'confidence': 1 - probability,
                        'position_size': abs(position_size),
                        'reason': f'TCN ML Short Signal (Confidence: {1-probability:.2%}, {explanation})',
                        'indicators': {
                            'ml_probability': probability,
                            'position_size': position_size,
                            'volatility_scaling': explanation
                        }
                    }

            # Exit existing position if confidence drops
            elif has_position and abs(probability - 0.5) < (self.confidence_threshold - 0.5):
                signal = {
                    'action': 'CLOSE',
                    'symbol': symbol,
                    'exchange': exchange,
                    'price': current_price,
                    'reason': f'Low confidence exit (Probability: {probability:.2%})'
                }

            self.last_signal = signal
            return signal

        except Exception as e:
            print(f"Error generating TCN ML signal: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range for stop-loss/target"""
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=period, adjust=False).mean()

        return atr.iloc[-1]

    def get_description(self) -> str:
        """Get strategy description"""
        return (
            f"TCN Neural Network Strategy\n"
            f"Model: {self.model_path or 'Not loaded'}\n"
            f"Confidence Threshold: {self.confidence_threshold}\n"
            f"Risk per Trade: {self.risk_per_trade * 100}%\n"
            f"Volatility Scaling: {'Enabled' if self.enable_volatility_scaling else 'Disabled'}\n"
            f"Device: {self.device}"
        )

    def get_parameters(self) -> Dict:
        """Get current parameters"""
        return {
            'model_path': self.model_path,
            'confidence_threshold': self.confidence_threshold,
            'risk_per_trade': self.risk_per_trade,
            'enable_volatility_scaling': self.enable_volatility_scaling
        }

    def update_model(self, new_model_path: str):
        """Update model checkpoint path and reload"""
        self.model_path = new_model_path
        self._load_model()
