"""
Machine Learning Module for Trading

Provides neural network-based trading strategies with:
- 12-feature engineering pipeline
- Temporal Convolutional Network (TCN) architecture
- Volatility-scaled position sizing
- Walk-forward backtesting
- Live trading integration
"""

from .feature_engineering import FeatureEngineer
from .data_pipeline import TimeSeriesDataPipeline
from .models import TCNTradingModel, create_default_model
from .volatility_scaler import VolatilityScaler
from .ml_backtest_engine import MLBacktestEngine

__version__ = '1.0.0'

__all__ = [
    'FeatureEngineer',
    'TimeSeriesDataPipeline',
    'TCNTradingModel',
    'create_default_model',
    'VolatilityScaler',
    'MLBacktestEngine'
]
