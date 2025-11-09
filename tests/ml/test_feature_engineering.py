"""
Unit tests for Feature Engineering module
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.ml.feature_engineering import FeatureEngineer


@pytest.fixture
def sample_ohlc_data():
    """Generate sample OHLCV data for testing"""
    np.random.seed(42)
    num_days = 200

    dates = pd.date_range(end='2024-01-01', periods=num_days, freq='D')
    returns = np.random.normal(0.001, 0.02, num_days)
    prices = 2500 * np.exp(np.cumsum(returns))

    data = []
    for date, close in zip(dates, prices):
        high = close * (1 + abs(np.random.normal(0, 0.01)))
        low = close * (1 - abs(np.random.normal(0, 0.01)))
        open_price = close * (1 + np.random.normal(0, 0.005))
        volume = int(np.random.uniform(100000, 500000))

        data.append({
            'date': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)
    return df


class TestFeatureEngineer:
    """Test suite for FeatureEngineer"""

    def test_initialization(self):
        """Test feature engineer initialization"""
        engineer = FeatureEngineer(
            rsi_period=14,
            macd_fast=12,
            macd_slow=26,
            normalization='zscore'
        )

        assert engineer.rsi_period == 14
        assert engineer.macd_fast == 12
        assert engineer.normalization == 'zscore'

    def test_feature_engineering(self, sample_ohlc_data):
        """Test feature engineering pipeline"""
        engineer = FeatureEngineer()
        features = engineer.engineer_features(sample_ohlc_data)

        # Check shape
        assert features.shape[0] == sample_ohlc_data.shape[0]
        assert features.shape[1] == 12  # 12 features

        # Check feature names
        expected_features = [
            'rsi', 'macd', 'roc', 'sma_ratio', 'adx',
            'atr', 'bb_width', 'vwap_deviation', 'volume_ratio',
            'stochastic', 'cci', 'price_momentum'
        ]
        assert list(features.columns) == expected_features

        # Check no NaN values (after ffill/bfill)
        assert features.isna().sum().sum() == 0

    def test_normalization_zscore(self, sample_ohlc_data):
        """Test Z-score normalization"""
        engineer = FeatureEngineer(normalization='zscore')
        features = engineer.engineer_features(sample_ohlc_data)

        # Check normalization stats stored
        assert len(engineer.feature_stats) == 12

        # Check each feature has mean ~0, std ~1
        for col in features.columns:
            assert abs(features[col].mean()) < 0.1
            assert abs(features[col].std() - 1.0) < 0.1

    def test_normalization_minmax(self, sample_ohlc_data):
        """Test min-max normalization"""
        engineer = FeatureEngineer(normalization='minmax')
        features = engineer.engineer_features(sample_ohlc_data)

        # Check each feature in [0, 1] range
        for col in features.columns:
            assert features[col].min() >= -0.01  # Allow small tolerance
            assert features[col].max() <= 1.01

    def test_insufficient_data(self):
        """Test error with insufficient data"""
        engineer = FeatureEngineer()

        # Create tiny dataset
        tiny_df = pd.DataFrame({
            'open': [100, 101],
            'high': [102, 103],
            'low': [99, 100],
            'close': [101, 102],
            'volume': [1000, 1100]
        })

        with pytest.raises(ValueError, match="Insufficient data"):
            engineer.engineer_features(tiny_df)

    def test_save_load_normalization_params(self, sample_ohlc_data, tmp_path):
        """Test saving and loading normalization parameters"""
        engineer1 = FeatureEngineer(normalization='zscore')
        features1 = engineer1.engineer_features(sample_ohlc_data)

        # Save params
        param_file = tmp_path / "params.json"
        engineer1.save_normalization_params(str(param_file))

        # Load params in new engineer
        engineer2 = FeatureEngineer(normalization='zscore')
        engineer2.load_normalization_params(str(param_file))

        # Check params match
        assert engineer2.feature_stats == engineer1.feature_stats

    def test_get_feature_names(self):
        """Test getting feature names"""
        engineer = FeatureEngineer()
        names = engineer.get_feature_names()

        assert len(names) == 12
        assert 'rsi' in names
        assert 'macd' in names
        assert 'price_momentum' in names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
