"""
Feature Engineering for Neural Network Trading Strategy

This module creates 12 engineered features from OHLCV data with proper normalization
for machine learning models.

Features:
    Momentum: RSI(14), MACD, Rate of Change
    Trend: SMA/EMA ratios, ADX
    Volatility: ATR(14), Bollinger Bands width
    Volume: VWAP deviation, Volume SMA ratio
    Mean Reversion: Stochastic, CCI
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')


class FeatureEngineer:
    """
    Feature engineering pipeline for ML trading models.

    Creates 12 normalized features from OHLCV data with proper handling
    of missing values, outliers, and stationarity.

    Parameters:
        rsi_period: RSI calculation period (default: 14)
        macd_fast: MACD fast period (default: 12)
        macd_slow: MACD slow period (default: 26)
        macd_signal: MACD signal period (default: 9)
        bb_period: Bollinger Bands period (default: 20)
        bb_std: Bollinger Bands standard deviation (default: 2)
        adx_period: ADX period (default: 14)
        atr_period: ATR period (default: 14)
        cci_period: CCI period (default: 20)
        stoch_period: Stochastic period (default: 14)
        normalization: Normalization method ('zscore' or 'minmax')
    """

    def __init__(
        self,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        bb_period: int = 20,
        bb_std: float = 2.0,
        adx_period: int = 14,
        atr_period: int = 14,
        cci_period: int = 20,
        stoch_period: int = 14,
        normalization: str = 'zscore'
    ):
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.adx_period = adx_period
        self.atr_period = atr_period
        self.cci_period = cci_period
        self.stoch_period = stoch_period
        self.normalization = normalization

        # Store normalization parameters for consistency
        self.feature_stats: Dict[str, Dict[str, float]] = {}

    def engineer_features(
        self,
        df: pd.DataFrame,
        fit_normalization: bool = True
    ) -> pd.DataFrame:
        """
        Create 12 engineered features from OHLCV data.

        Args:
            df: DataFrame with OHLC data (columns: open, high, low, close, volume)
            fit_normalization: If True, calculate normalization params from this data

        Returns:
            DataFrame with 12 engineered features (normalized)

        Example:
            >>> engineer = FeatureEngineer()
            >>> features = engineer.engineer_features(ohlc_df)
            >>> print(features.columns)
            ['rsi', 'macd', 'roc', 'sma_ratio', 'adx', 'atr', 'bb_width',
             'vwap_deviation', 'volume_ratio', 'stochastic', 'cci', 'price_momentum']
        """
        if len(df) < max(self.macd_slow, self.bb_period, self.adx_period) + 50:
            raise ValueError(
                f"Insufficient data. Need at least {self.macd_slow + 50} rows, "
                f"got {len(df)}"
            )

        features_df = pd.DataFrame(index=df.index)

        # Momentum Features (3)
        features_df['rsi'] = self._calculate_rsi(df['close'], self.rsi_period)
        features_df['macd'] = self._calculate_macd(df['close'])
        features_df['roc'] = self._calculate_roc(df['close'], period=10)

        # Trend Features (2)
        features_df['sma_ratio'] = self._calculate_sma_ratio(df['close'])
        features_df['adx'] = self._calculate_adx(df)

        # Volatility Features (2)
        features_df['atr'] = self._calculate_atr(df)
        features_df['bb_width'] = self._calculate_bb_width(df['close'])

        # Volume Features (2)
        features_df['vwap_deviation'] = self._calculate_vwap_deviation(df)
        features_df['volume_ratio'] = self._calculate_volume_ratio(df['volume'])

        # Mean Reversion Features (2)
        features_df['stochastic'] = self._calculate_stochastic(df)
        features_df['cci'] = self._calculate_cci(df)

        # Price Momentum (1)
        features_df['price_momentum'] = df['close'].pct_change(5)

        # Handle missing values (fill forward then backward)
        features_df = features_df.ffill().bfill()

        # Normalize features
        if fit_normalization:
            features_df = self._fit_normalize(features_df)
        else:
            features_df = self._transform_normalize(features_df)

        return features_df

    def _calculate_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, prices: pd.Series) -> pd.Series:
        """Calculate MACD (difference between fast and slow EMA)"""
        ema_fast = prices.ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.macd_slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        return macd

    def _calculate_roc(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Rate of Change"""
        roc = prices.pct_change(period) * 100
        return roc

    def _calculate_sma_ratio(self, prices: pd.Series) -> pd.Series:
        """Calculate ratio of price to SMA(20)"""
        sma = prices.rolling(window=20).mean()
        ratio = prices / (sma + 1e-10)
        return ratio

    def _calculate_adx(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average Directional Index (trend strength)"""
        high = df['high']
        low = df['low']
        close = df['close']

        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Directional Movement
        dm_plus = high.diff()
        dm_minus = -low.diff()

        dm_plus[dm_plus < 0] = 0
        dm_minus[dm_minus < 0] = 0
        dm_plus[(dm_plus - dm_minus) < 0] = 0
        dm_minus[(dm_minus - dm_plus) < 0] = 0

        # Smoothed indicators
        tr_smooth = tr.rolling(window=self.adx_period).mean()
        dm_plus_smooth = dm_plus.rolling(window=self.adx_period).mean()
        dm_minus_smooth = dm_minus.rolling(window=self.adx_period).mean()

        di_plus = 100 * dm_plus_smooth / (tr_smooth + 1e-10)
        di_minus = 100 * dm_minus_smooth / (tr_smooth + 1e-10)

        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus + 1e-10)
        adx = dx.rolling(window=self.adx_period).mean()

        return adx

    def _calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(span=self.atr_period, adjust=False).mean()

        # Normalize by price
        atr_pct = atr / (close + 1e-10) * 100

        return atr_pct

    def _calculate_bb_width(self, prices: pd.Series) -> pd.Series:
        """Calculate Bollinger Bands width (normalized)"""
        sma = prices.rolling(window=self.bb_period).mean()
        std = prices.rolling(window=self.bb_period).std()

        upper = sma + (self.bb_std * std)
        lower = sma - (self.bb_std * std)

        bb_width = (upper - lower) / (sma + 1e-10) * 100

        return bb_width

    def _calculate_vwap_deviation(self, df: pd.DataFrame) -> pd.Series:
        """Calculate deviation from VWAP"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()

        deviation = (df['close'] - vwap) / (vwap + 1e-10) * 100

        return deviation

    def _calculate_volume_ratio(self, volume: pd.Series) -> pd.Series:
        """Calculate volume ratio (current vs 20-period average)"""
        volume_sma = volume.rolling(window=20).mean()
        volume_ratio = volume / (volume_sma + 1e-10)

        return volume_ratio

    def _calculate_stochastic(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Stochastic Oscillator"""
        low_min = df['low'].rolling(window=self.stoch_period).min()
        high_max = df['high'].rolling(window=self.stoch_period).max()

        stoch = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-10)

        return stoch

    def _calculate_cci(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Commodity Channel Index"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma = typical_price.rolling(window=self.cci_period).mean()

        mean_deviation = typical_price.rolling(window=self.cci_period).apply(
            lambda x: np.abs(x - x.mean()).mean()
        )

        cci = (typical_price - sma) / (0.015 * mean_deviation + 1e-10)

        return cci

    def _fit_normalize(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Fit normalization parameters and normalize features.

        Args:
            features_df: DataFrame with raw features

        Returns:
            Normalized DataFrame
        """
        normalized_df = features_df.copy()

        for col in features_df.columns:
            if self.normalization == 'zscore':
                mean = features_df[col].mean()
                std = features_df[col].std()

                self.feature_stats[col] = {'mean': mean, 'std': std}
                normalized_df[col] = (features_df[col] - mean) / (std + 1e-10)

            elif self.normalization == 'minmax':
                min_val = features_df[col].min()
                max_val = features_df[col].max()

                self.feature_stats[col] = {'min': min_val, 'max': max_val}
                normalized_df[col] = (features_df[col] - min_val) / (max_val - min_val + 1e-10)

        return normalized_df

    def _transform_normalize(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply previously fitted normalization parameters.

        Args:
            features_df: DataFrame with raw features

        Returns:
            Normalized DataFrame
        """
        if not self.feature_stats:
            raise ValueError("Must call fit_normalize first or set fit_normalization=True")

        normalized_df = features_df.copy()

        for col in features_df.columns:
            if col not in self.feature_stats:
                raise ValueError(f"Feature '{col}' not found in fitted statistics")

            stats = self.feature_stats[col]

            if self.normalization == 'zscore':
                normalized_df[col] = (features_df[col] - stats['mean']) / (stats['std'] + 1e-10)

            elif self.normalization == 'minmax':
                normalized_df[col] = (
                    (features_df[col] - stats['min']) / (stats['max'] - stats['min'] + 1e-10)
                )

        return normalized_df

    def get_feature_names(self) -> List[str]:
        """Get list of feature names"""
        return [
            'rsi', 'macd', 'roc', 'sma_ratio', 'adx',
            'atr', 'bb_width', 'vwap_deviation', 'volume_ratio',
            'stochastic', 'cci', 'price_momentum'
        ]

    def save_normalization_params(self, filepath: str):
        """Save normalization parameters to file"""
        import json

        with open(filepath, 'w') as f:
            json.dump({
                'feature_stats': self.feature_stats,
                'normalization': self.normalization
            }, f, indent=2)

    def load_normalization_params(self, filepath: str):
        """Load normalization parameters from file"""
        import json

        with open(filepath, 'r') as f:
            data = json.load(f)
            self.feature_stats = data['feature_stats']
            self.normalization = data['normalization']
