"""
Volatility-Scaled Position Sizing with Deadbands

Implements dynamic position sizing based on market volatility and
model confidence scores. Includes deadband (neutral zone) to reduce
overtrading in uncertain conditions.
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple


class VolatilityScaler:
    """
    Volatility-based position sizing with deadbands.

    Scales position size inversely to market volatility:
        - High volatility → Smaller positions
        - Low volatility → Larger positions

    Applies deadband (neutral zone) to filter weak signals:
        - Signal < deadband_threshold → No trade
        - Signal > deadband_threshold → Scaled trade

    Parameters:
        w_min: Minimum position size as fraction of capital (default: 0.1)
        w_max: Maximum position size as fraction of capital (default: 1.0)
        vol_window: Rolling window for volatility calculation (default: 20)
        deadband_threshold: Minimum signal strength to trade (default: 0.1)
        vol_lookback: Periods for reference volatility (default: 252)
    """

    def __init__(
        self,
        w_min: float = 0.1,
        w_max: float = 1.0,
        vol_window: int = 20,
        deadband_threshold: float = 0.1,
        vol_lookback: int = 252
    ):
        if not (0 < w_min <= w_max <= 1.0):
            raise ValueError("Must have 0 < w_min <= w_max <= 1.0")

        if not (0 <= deadband_threshold < 0.5):
            raise ValueError("Deadband threshold must be in [0, 0.5)")

        self.w_min = w_min
        self.w_max = w_max
        self.vol_window = vol_window
        self.deadband_threshold = deadband_threshold
        self.vol_lookback = vol_lookback

        # State
        self.reference_vol = None
        self.vol_history = []

    def calculate_volatility(
        self,
        returns: np.ndarray,
        method: str = 'ewma'
    ) -> float:
        """
        Calculate rolling volatility.

        Args:
            returns: Array of returns
            method: 'simple' (standard deviation) or 'ewma' (exponential weighted)

        Returns:
            Volatility estimate (annualized)
        """
        if len(returns) < self.vol_window:
            raise ValueError(
                f"Need at least {self.vol_window} returns, got {len(returns)}"
            )

        recent_returns = returns[-self.vol_window:]

        if method == 'simple':
            vol = np.std(recent_returns)
        elif method == 'ewma':
            # Exponentially weighted moving average
            weights = np.exp(np.linspace(-1, 0, self.vol_window))
            weights /= weights.sum()
            weighted_variance = np.average(recent_returns**2, weights=weights)
            vol = np.sqrt(weighted_variance)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Annualize (assuming daily returns)
        vol_annualized = vol * np.sqrt(252)

        return vol_annualized

    def update_reference_volatility(self, returns: np.ndarray):
        """
        Update long-term reference volatility.

        Args:
            returns: Historical returns
        """
        if len(returns) >= self.vol_lookback:
            self.reference_vol = np.std(returns[-self.vol_lookback:]) * np.sqrt(252)
        else:
            # Use all available data if insufficient history
            self.reference_vol = np.std(returns) * np.sqrt(252)

        self.vol_history.append(self.reference_vol)

    def scale_position(
        self,
        signal_probability: float,
        current_vol: float,
        reference_vol: Optional[float] = None
    ) -> Tuple[float, str]:
        """
        Calculate volatility-scaled position size with deadband.

        Args:
            signal_probability: Model output probability [0, 1]
                - 0 = strong bearish
                - 0.5 = neutral
                - 1 = strong bullish
            current_vol: Current market volatility
            reference_vol: Reference volatility (uses stored if None)

        Returns:
            (position_size, explanation):
                - position_size: Scaled position size [-w_max, w_max]
                  (positive = long, negative = short, 0 = no position)
                - explanation: String describing the scaling logic

        Example:
            >>> scaler = VolatilityScaler(w_min=0.1, w_max=1.0, deadband_threshold=0.1)
            >>> position, reason = scaler.scale_position(
            ...     signal_probability=0.75,  # 75% bullish
            ...     current_vol=0.20,
            ...     reference_vol=0.15
            ... )
            >>> print(f"Position: {position:.2f}, Reason: {reason}")
        """
        # Use stored reference volatility if not provided
        if reference_vol is None:
            if self.reference_vol is None:
                raise ValueError("Must call update_reference_volatility() first")
            reference_vol = self.reference_vol

        # Convert probability to signal strength [-1, 1]
        # 0 → -1 (bearish), 0.5 → 0 (neutral), 1 → +1 (bullish)
        raw_signal = 2 * signal_probability - 1

        # Apply deadband (filter weak signals)
        if abs(raw_signal) < self.deadband_threshold:
            return 0.0, (
                f"Signal {raw_signal:.3f} within deadband "
                f"[{-self.deadband_threshold:.3f}, {self.deadband_threshold:.3f}] → No trade"
            )

        # Volatility scaling factor (inverse relationship)
        vol_scale = reference_vol / (current_vol + 1e-10)

        # Apply scaling
        scaled_signal = vol_scale * raw_signal

        # Clip to position size limits
        position_size = np.clip(scaled_signal, -self.w_max, self.w_max)

        # Ensure minimum position size (if trading)
        if position_size > 0:
            position_size = max(position_size, self.w_min)
        elif position_size < 0:
            position_size = min(position_size, -self.w_min)

        # Generate explanation
        direction = "LONG" if position_size > 0 else "SHORT"
        explanation = (
            f"{direction} position: {abs(position_size):.2f}x | "
            f"Raw signal: {raw_signal:.3f} → "
            f"Vol-scaled: {scaled_signal:.3f} → "
            f"Clipped: {position_size:.3f} | "
            f"Current vol: {current_vol:.3f}, "
            f"Reference vol: {reference_vol:.3f}"
        )

        return position_size, explanation

    def calculate_position_units(
        self,
        position_size: float,
        account_equity: float,
        current_price: float,
        risk_per_trade: float = 0.02
    ) -> int:
        """
        Convert position size to number of units (shares/contracts).

        Args:
            position_size: Scaled position size [-1, 1]
            account_equity: Total account value
            current_price: Current asset price
            risk_per_trade: Maximum risk per trade (default: 2%)

        Returns:
            Number of units to trade (positive = buy, negative = sell)

        Example:
            >>> units = scaler.calculate_position_units(
            ...     position_size=0.5,    # 50% of max position
            ...     account_equity=100000,
            ...     current_price=2500,
            ...     risk_per_trade=0.02
            ... )
        """
        if position_size == 0:
            return 0

        # Calculate position value
        max_risk = account_equity * risk_per_trade
        position_value = max_risk / abs(position_size)

        # Convert to units
        num_units = int(position_value / current_price)

        # Apply direction
        if position_size < 0:
            num_units = -num_units

        return num_units

    def get_adaptive_deadband(
        self,
        recent_returns: np.ndarray,
        base_threshold: Optional[float] = None
    ) -> float:
        """
        Calculate adaptive deadband based on recent market conditions.

        Increases deadband in high-volatility regimes (be more selective).
        Decreases deadband in low-volatility regimes (trade more).

        Args:
            recent_returns: Recent return series
            base_threshold: Base deadband (uses self.deadband_threshold if None)

        Returns:
            Adaptive deadband threshold
        """
        if base_threshold is None:
            base_threshold = self.deadband_threshold

        # Calculate recent volatility
        recent_vol = np.std(recent_returns[-self.vol_window:])

        # Calculate long-term volatility
        if len(recent_returns) >= self.vol_lookback:
            long_term_vol = np.std(recent_returns[-self.vol_lookback:])
        else:
            long_term_vol = np.std(recent_returns)

        # Scale deadband by volatility ratio
        vol_ratio = recent_vol / (long_term_vol + 1e-10)

        # Adaptive threshold (increase in high vol, decrease in low vol)
        adaptive_threshold = base_threshold * vol_ratio

        # Clip to reasonable range
        adaptive_threshold = np.clip(adaptive_threshold, 0.05, 0.3)

        return adaptive_threshold

    def get_statistics(self) -> dict:
        """Get scaler statistics"""
        stats = {
            'w_min': self.w_min,
            'w_max': self.w_max,
            'vol_window': self.vol_window,
            'deadband_threshold': self.deadband_threshold,
            'current_reference_vol': self.reference_vol
        }

        if self.vol_history:
            stats['avg_reference_vol'] = np.mean(self.vol_history)
            stats['min_reference_vol'] = np.min(self.vol_history)
            stats['max_reference_vol'] = np.max(self.vol_history)

        return stats


# Example usage
if __name__ == "__main__":
    # Create scaler
    scaler = VolatilityScaler(
        w_min=0.1,
        w_max=1.0,
        vol_window=20,
        deadband_threshold=0.1
    )

    # Simulate returns
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 500)  # 500 days of returns

    # Update reference volatility
    scaler.update_reference_volatility(returns)

    # Calculate current volatility
    current_vol = scaler.calculate_volatility(returns)

    print("Volatility Scaler Example")
    print("=" * 50)
    print(f"Reference volatility: {scaler.reference_vol:.3f}")
    print(f"Current volatility: {current_vol:.3f}")
    print()

    # Test different signal probabilities
    test_probabilities = [0.3, 0.45, 0.55, 0.75, 0.9]

    for prob in test_probabilities:
        position, explanation = scaler.scale_position(
            signal_probability=prob,
            current_vol=current_vol
        )

        print(f"Probability: {prob:.2f}")
        print(f"  Position: {position:.3f}")
        print(f"  {explanation}")
        print()

    # Calculate units for actual trade
    position, _ = scaler.scale_position(0.75, current_vol)
    units = scaler.calculate_position_units(
        position_size=position,
        account_equity=100000,
        current_price=2500,
        risk_per_trade=0.02
    )
    print(f"Trade execution: {units} units @ ₹2500")

    # Show statistics
    print("\nScaler Statistics:")
    stats = scaler.get_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
