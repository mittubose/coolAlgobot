"""
Data Pipeline for Neural Network Training

Creates 64-timestep rolling windows from feature data for TCN model training.
Handles train/validation/test splits with proper time-series awareness.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, List
from datetime import datetime, timedelta


class TimeSeriesDataPipeline:
    """
    Time-series data pipeline for ML model training.

    Creates rolling windows with proper train/val/test splits that respect
    temporal ordering (no look-ahead bias).

    Parameters:
        window_size: Number of timesteps in each sequence (default: 64)
        stride: Step size for rolling window (default: 1)
        train_ratio: Proportion of data for training (default: 0.7)
        val_ratio: Proportion of data for validation (default: 0.15)
        test_ratio: Proportion of data for testing (default: 0.15)
    """

    def __init__(
        self,
        window_size: int = 64,
        stride: int = 1,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ):
        if not np.isclose(train_ratio + val_ratio + test_ratio, 1.0):
            raise ValueError("Train + val + test ratios must sum to 1.0")

        self.window_size = window_size
        self.stride = stride
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio

    def create_rolling_windows(
        self,
        features: pd.DataFrame,
        targets: Optional[pd.Series] = None
    ) -> Tuple[np.ndarray, Optional[np.ndarray], pd.DatetimeIndex]:
        """
        Create rolling windows from feature data.

        Args:
            features: DataFrame with engineered features (shape: [T, num_features])
            targets: Optional Series with target labels (shape: [T])

        Returns:
            Tuple of (X_windows, y_targets, timestamps):
                - X_windows: (num_windows, window_size, num_features)
                - y_targets: (num_windows,) if targets provided, else None
                - timestamps: DatetimeIndex of window end times

        Example:
            >>> pipeline = TimeSeriesDataPipeline(window_size=64, stride=1)
            >>> X, y, times = pipeline.create_rolling_windows(features, targets)
            >>> print(X.shape)  # (num_windows, 64, 12)
        """
        if len(features) < self.window_size:
            raise ValueError(
                f"Need at least {self.window_size} rows, got {len(features)}"
            )

        num_features = features.shape[1]
        num_samples = len(features)
        num_windows = (num_samples - self.window_size) // self.stride + 1

        # Pre-allocate arrays
        X_windows = np.zeros((num_windows, self.window_size, num_features))
        timestamps = []

        if targets is not None:
            y_targets = np.zeros(num_windows)
        else:
            y_targets = None

        # Create rolling windows
        for i in range(num_windows):
            start_idx = i * self.stride
            end_idx = start_idx + self.window_size

            X_windows[i] = features.iloc[start_idx:end_idx].values

            # Target corresponds to the next timestep after window
            if targets is not None and end_idx < len(targets):
                y_targets[i] = targets.iloc[end_idx]

            # Store timestamp of window end
            timestamps.append(features.index[end_idx - 1])

        timestamps = pd.DatetimeIndex(timestamps)

        return X_windows, y_targets, timestamps

    def train_val_test_split(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        timestamps: Optional[pd.DatetimeIndex] = None
    ) -> Tuple:
        """
        Split data into train/validation/test sets (chronologically).

        Args:
            X: Feature windows (num_windows, window_size, num_features)
            y: Target labels (num_windows,)
            timestamps: Timestamps for each window

        Returns:
            Tuple of (X_train, X_val, X_test, y_train, y_val, y_test,
                      times_train, times_val, times_test)

        Example:
            >>> X_train, X_val, X_test, y_train, y_val, y_test, _, _, _ = \\
            ...     pipeline.train_val_test_split(X, y, timestamps)
        """
        num_samples = len(X)

        # Calculate split indices (chronologically ordered)
        train_end = int(num_samples * self.train_ratio)
        val_end = int(num_samples * (self.train_ratio + self.val_ratio))

        # Split features
        X_train = X[:train_end]
        X_val = X[train_end:val_end]
        X_test = X[val_end:]

        # Split targets
        if y is not None:
            y_train = y[:train_end]
            y_val = y[train_end:val_end]
            y_test = y[val_end:]
        else:
            y_train = y_val = y_test = None

        # Split timestamps
        if timestamps is not None:
            times_train = timestamps[:train_end]
            times_val = timestamps[train_end:val_end]
            times_test = timestamps[val_end:]
        else:
            times_train = times_val = times_test = None

        return (X_train, X_val, X_test, y_train, y_val, y_test,
                times_train, times_val, times_test)

    def create_labels_from_future_returns(
        self,
        prices: pd.Series,
        forward_period: int = 5,
        threshold: float = 0.01
    ) -> pd.Series:
        """
        Create binary labels based on future price movement.

        Args:
            prices: Price series
            forward_period: Number of periods to look ahead
            threshold: Minimum return threshold for positive label

        Returns:
            Binary labels (1 = price will rise > threshold, 0 = otherwise)

        Example:
            >>> labels = pipeline.create_labels_from_future_returns(
            ...     df['close'], forward_period=5, threshold=0.01
            ... )
            >>> # 1 if price rises >1% in next 5 periods, else 0
        """
        future_returns = prices.shift(-forward_period) / prices - 1

        labels = (future_returns > threshold).astype(int)

        # Fill NaN values at the end (no future data available)
        labels = labels.fillna(0)

        return labels

    def walk_forward_split(
        self,
        X: np.ndarray,
        y: np.ndarray,
        train_period: int = 252,  # 1 year of trading days
        test_period: int = 63     # 1 quarter of trading days
    ) -> List[Tuple]:
        """
        Create walk-forward analysis splits for backtesting.

        Args:
            X: Feature windows (num_windows, window_size, num_features)
            y: Target labels (num_windows,)
            train_period: Number of samples in training window
            test_period: Number of samples in test window

        Returns:
            List of (X_train, y_train, X_test, y_test) tuples

        Example:
            >>> splits = pipeline.walk_forward_split(X, y, train_period=252, test_period=63)
            >>> for X_train, y_train, X_test, y_test in splits:
            ...     # Train model on X_train, test on X_test
            ...     pass
        """
        num_samples = len(X)
        splits = []

        current_idx = 0
        while current_idx + train_period + test_period <= num_samples:
            train_start = current_idx
            train_end = current_idx + train_period
            test_end = train_end + test_period

            X_train = X[train_start:train_end]
            y_train = y[train_start:train_end]

            X_test = X[train_end:test_end]
            y_test = y[train_end:test_end]

            splits.append((X_train, y_train, X_test, y_test))

            # Move forward by test_period
            current_idx += test_period

        return splits

    def balance_classes(
        self,
        X: np.ndarray,
        y: np.ndarray,
        method: str = 'undersample'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Balance class distribution to handle imbalanced data.

        Args:
            X: Feature windows
            y: Target labels
            method: 'undersample' or 'oversample'

        Returns:
            Balanced (X, y)

        Example:
            >>> X_balanced, y_balanced = pipeline.balance_classes(X, y, method='undersample')
        """
        unique, counts = np.unique(y, return_counts=True)

        if len(unique) != 2:
            raise ValueError("Only binary classification supported")

        majority_class = unique[np.argmax(counts)]
        minority_class = unique[np.argmin(counts)]

        majority_count = np.max(counts)
        minority_count = np.min(counts)

        majority_indices = np.where(y == majority_class)[0]
        minority_indices = np.where(y == minority_class)[0]

        if method == 'undersample':
            # Randomly sample majority class to match minority
            np.random.seed(42)
            sampled_majority_indices = np.random.choice(
                majority_indices,
                size=minority_count,
                replace=False
            )

            balanced_indices = np.concatenate([
                sampled_majority_indices,
                minority_indices
            ])

        elif method == 'oversample':
            # Randomly oversample minority class to match majority
            np.random.seed(42)
            sampled_minority_indices = np.random.choice(
                minority_indices,
                size=majority_count,
                replace=True
            )

            balanced_indices = np.concatenate([
                majority_indices,
                sampled_minority_indices
            ])

        else:
            raise ValueError(f"Unknown method: {method}")

        # Shuffle indices
        np.random.seed(42)
        np.random.shuffle(balanced_indices)

        return X[balanced_indices], y[balanced_indices]

    def get_statistics(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> dict:
        """
        Get dataset statistics.

        Args:
            X: Feature windows
            y: Optional target labels

        Returns:
            Dictionary with dataset statistics
        """
        stats = {
            'num_samples': len(X),
            'window_size': X.shape[1],
            'num_features': X.shape[2],
            'X_mean': X.mean(),
            'X_std': X.std(),
            'X_min': X.min(),
            'X_max': X.max()
        }

        if y is not None:
            unique, counts = np.unique(y, return_counts=True)
            class_distribution = dict(zip(unique.tolist(), counts.tolist()))

            stats['num_classes'] = len(unique)
            stats['class_distribution'] = class_distribution
            stats['class_balance'] = counts.min() / counts.max()

        return stats
