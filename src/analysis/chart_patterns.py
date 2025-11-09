"""
Chart Pattern Detection
Detects classical chart patterns like double bottom, head & shoulders, triangles, etc.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from scipy.signal import argrelextrema


class ChartPatternDetector:
    """
    Detect classical chart patterns on OHLCV data

    Patterns supported:
    1. Double Bottom / Double Top
    2. Triple Bottom / Triple Top
    3. Head and Shoulders / Inverse Head and Shoulders
    4. Ascending Triangle / Descending Triangle / Symmetrical Triangle
    5. Rising Wedge / Falling Wedge
    6. Bull Flag / Bear Flag
    7. Cup and Handle
    8. Rounding Bottom / Rounding Top
    """

    def __init__(self, df: pd.DataFrame, min_confidence: float = 0.7):
        """
        Initialize chart pattern detector

        Args:
            df: DataFrame with OHLCV data
            min_confidence: Minimum confidence threshold (0.0-1.0)
        """
        self.df = df.copy()
        self.min_confidence = min_confidence

        # Ensure index is datetime
        if 'time' in self.df.columns:
            self.df['time'] = pd.to_datetime(self.df['time'])
            self.df.set_index('time', inplace=True)

        # Find pivots (local maxima and minima)
        self._find_pivot_points()

    def _find_pivot_points(self, order: int = 5):
        """Find pivot highs and lows"""
        # Local maxima (resistance)
        self.df['pivot_high'] = self.df.iloc[argrelextrema(
            self.df['high'].values, np.greater_equal, order=order)[0]]['high']

        # Local minima (support)
        self.df['pivot_low'] = self.df.iloc[argrelextrema(
            self.df['low'].values, np.less_equal, order=order)[0]]['low']

    def detect_all_patterns(self) -> List[Dict]:
        """Detect all chart patterns"""
        patterns = []

        # Reversal patterns
        patterns.extend(self.detect_double_bottom())
        patterns.extend(self.detect_double_top())
        patterns.extend(self.detect_triple_bottom())
        patterns.extend(self.detect_triple_top())
        patterns.extend(self.detect_head_and_shoulders())
        patterns.extend(self.detect_inverse_head_and_shoulders())

        # Continuation patterns
        patterns.extend(self.detect_ascending_triangle())
        patterns.extend(self.detect_descending_triangle())
        patterns.extend(self.detect_symmetrical_triangle())
        patterns.extend(self.detect_rising_wedge())
        patterns.extend(self.detect_falling_wedge())
        patterns.extend(self.detect_bull_flag())
        patterns.extend(self.detect_bear_flag())

        # Other patterns
        patterns.extend(self.detect_cup_and_handle())
        patterns.extend(self.detect_rounding_bottom())
        patterns.extend(self.detect_rounding_top())

        # Filter by confidence
        return [p for p in patterns if p['confidence'] >= self.min_confidence]

    # ===== DOUBLE BOTTOM / TOP =====

    def detect_double_bottom(self) -> List[Dict]:
        """
        Detect double bottom pattern

        Pattern: Two troughs at approximately same level with peak in middle
        Signal: Bullish reversal
        """
        patterns = []
        pivot_lows = self.df['pivot_low'].dropna()

        if len(pivot_lows) < 2:
            return patterns

        for i in range(len(pivot_lows) - 1):
            low1_idx = pivot_lows.index[i]
            low1_price = pivot_lows.iloc[i]

            for j in range(i + 1, len(pivot_lows)):
                low2_idx = pivot_lows.index[j]
                low2_price = pivot_lows.iloc[j]

                # Check if lows are at similar level (within 3%)
                price_diff_pct = abs(low1_price - low2_price) / low1_price * 100

                if price_diff_pct > 3.0:
                    continue

                # Check if there's a peak between the lows
                between_data = self.df.loc[low1_idx:low2_idx]
                peak_price = between_data['high'].max()
                peak_idx = between_data['high'].idxmax()

                # Peak should be at least 5% higher than lows
                if (peak_price - low1_price) / low1_price < 0.05:
                    continue

                # Calculate confidence
                # - Similar lows = higher confidence
                # - Clear peak = higher confidence
                # - Adequate spacing = higher confidence
                similarity_score = 1.0 - (price_diff_pct / 3.0)
                peak_height = (peak_price - low1_price) / low1_price
                peak_score = min(1.0, peak_height / 0.10)  # 10% peak is perfect

                spacing_candles = len(between_data)
                spacing_score = min(1.0, spacing_candles / 20)  # 20 candles is ideal

                confidence = (similarity_score * 0.5 + peak_score * 0.3 + spacing_score * 0.2)

                patterns.append({
                    'name': 'Double Bottom',
                    'type': 'bullish_reversal',
                    'confidence': round(confidence * 100, 1),
                    'start_time': low1_idx,
                    'end_time': low2_idx,
                    'support_level': round((low1_price + low2_price) / 2, 2),
                    'resistance_level': round(peak_price, 2),
                    'target': round(peak_price + (peak_price - low1_price), 2),
                    'stop_loss': round(low2_price * 0.98, 2)
                })

        return patterns

    def detect_double_top(self) -> List[Dict]:
        """
        Detect double top pattern

        Pattern: Two peaks at approximately same level with trough in middle
        Signal: Bearish reversal
        """
        patterns = []
        pivot_highs = self.df['pivot_high'].dropna()

        if len(pivot_highs) < 2:
            return patterns

        for i in range(len(pivot_highs) - 1):
            high1_idx = pivot_highs.index[i]
            high1_price = pivot_highs.iloc[i]

            for j in range(i + 1, len(pivot_highs)):
                high2_idx = pivot_highs.index[j]
                high2_price = pivot_highs.iloc[j]

                # Check if highs are at similar level (within 3%)
                price_diff_pct = abs(high1_price - high2_price) / high1_price * 100

                if price_diff_pct > 3.0:
                    continue

                # Check if there's a trough between the highs
                between_data = self.df.loc[high1_idx:high2_idx]
                trough_price = between_data['low'].min()
                trough_idx = between_data['low'].idxmin()

                # Trough should be at least 5% lower than highs
                if (high1_price - trough_price) / high1_price < 0.05:
                    continue

                # Calculate confidence (same logic as double bottom)
                similarity_score = 1.0 - (price_diff_pct / 3.0)
                trough_depth = (high1_price - trough_price) / high1_price
                depth_score = min(1.0, trough_depth / 0.10)

                spacing_candles = len(between_data)
                spacing_score = min(1.0, spacing_candles / 20)

                confidence = (similarity_score * 0.5 + depth_score * 0.3 + spacing_score * 0.2)

                patterns.append({
                    'name': 'Double Top',
                    'type': 'bearish_reversal',
                    'confidence': round(confidence * 100, 1),
                    'start_time': high1_idx,
                    'end_time': high2_idx,
                    'resistance_level': round((high1_price + high2_price) / 2, 2),
                    'support_level': round(trough_price, 2),
                    'target': round(trough_price - (high1_price - trough_price), 2),
                    'stop_loss': round(high2_price * 1.02, 2)
                })

        return patterns

    # ===== TRIPLE BOTTOM / TOP =====

    def detect_triple_bottom(self) -> List[Dict]:
        """Detect triple bottom pattern - three lows at similar level"""
        patterns = []
        pivot_lows = self.df['pivot_low'].dropna()

        if len(pivot_lows) < 3:
            return patterns

        for i in range(len(pivot_lows) - 2):
            low1 = pivot_lows.iloc[i]
            low2 = pivot_lows.iloc[i + 1]
            low3 = pivot_lows.iloc[i + 2]

            # Check if all three lows are within 3% of each other
            avg_low = (low1 + low2 + low3) / 3
            if all(abs(low - avg_low) / avg_low < 0.03 for low in [low1, low2, low3]):

                idx1 = pivot_lows.index[i]
                idx3 = pivot_lows.index[i + 2]

                confidence = 1.0 - max(abs(low - avg_low) / avg_low for low in [low1, low2, low3])

                patterns.append({
                    'name': 'Triple Bottom',
                    'type': 'bullish_reversal',
                    'confidence': round(confidence * 100, 1),
                    'start_time': idx1,
                    'end_time': idx3,
                    'support_level': round(avg_low, 2),
                    'stop_loss': round(avg_low * 0.98, 2)
                })

        return patterns

    def detect_triple_top(self) -> List[Dict]:
        """Detect triple top pattern - three highs at similar level"""
        patterns = []
        pivot_highs = self.df['pivot_high'].dropna()

        if len(pivot_highs) < 3:
            return patterns

        for i in range(len(pivot_highs) - 2):
            high1 = pivot_highs.iloc[i]
            high2 = pivot_highs.iloc[i + 1]
            high3 = pivot_highs.iloc[i + 2]

            # Check if all three highs are within 3% of each other
            avg_high = (high1 + high2 + high3) / 3
            if all(abs(high - avg_high) / avg_high < 0.03 for high in [high1, high2, high3]):

                idx1 = pivot_highs.index[i]
                idx3 = pivot_highs.index[i + 2]

                confidence = 1.0 - max(abs(high - avg_high) / avg_high for high in [high1, high2, high3])

                patterns.append({
                    'name': 'Triple Top',
                    'type': 'bearish_reversal',
                    'confidence': round(confidence * 100, 1),
                    'start_time': idx1,
                    'end_time': idx3,
                    'resistance_level': round(avg_high, 2),
                    'stop_loss': round(avg_high * 1.02, 2)
                })

        return patterns

    # ===== HEAD AND SHOULDERS =====

    def detect_head_and_shoulders(self) -> List[Dict]:
        """
        Detect head and shoulders pattern

        Pattern: Three peaks - left shoulder, head (highest), right shoulder
        Signal: Bearish reversal
        """
        patterns = []
        pivot_highs = self.df['pivot_high'].dropna()

        if len(pivot_highs) < 3:
            return patterns

        for i in range(len(pivot_highs) - 2):
            left_shoulder = pivot_highs.iloc[i]
            head = pivot_highs.iloc[i + 1]
            right_shoulder = pivot_highs.iloc[i + 2]

            # Head should be highest
            if not (head > left_shoulder and head > right_shoulder):
                continue

            # Shoulders should be at similar level (within 5%)
            shoulder_diff = abs(left_shoulder - right_shoulder) / left_shoulder
            if shoulder_diff > 0.05:
                continue

            # Head should be significantly higher (at least 5%)
            if (head - left_shoulder) / left_shoulder < 0.05:
                continue

            idx_left = pivot_highs.index[i]
            idx_head = pivot_highs.index[i + 1]
            idx_right = pivot_highs.index[i + 2]

            # Find neckline (support connecting troughs between shoulders and head)
            between_left_head = self.df.loc[idx_left:idx_head]
            between_head_right = self.df.loc[idx_head:idx_right]

            neckline_left = between_left_head['low'].min()
            neckline_right = between_head_right['low'].min()
            neckline = (neckline_left + neckline_right) / 2

            # Calculate confidence
            symmetry_score = 1.0 - shoulder_diff
            head_prominence = (head - left_shoulder) / left_shoulder
            prominence_score = min(1.0, head_prominence / 0.10)

            confidence = (symmetry_score * 0.6 + prominence_score * 0.4)

            patterns.append({
                'name': 'Head and Shoulders',
                'type': 'bearish_reversal',
                'confidence': round(confidence * 100, 1),
                'start_time': idx_left,
                'end_time': idx_right,
                'left_shoulder': round(left_shoulder, 2),
                'head': round(head, 2),
                'right_shoulder': round(right_shoulder, 2),
                'neckline': round(neckline, 2),
                'target': round(neckline - (head - neckline), 2),
                'stop_loss': round(right_shoulder * 1.02, 2)
            })

        return patterns

    def detect_inverse_head_and_shoulders(self) -> List[Dict]:
        """
        Detect inverse head and shoulders pattern

        Pattern: Three troughs - left shoulder, head (lowest), right shoulder
        Signal: Bullish reversal
        """
        patterns = []
        pivot_lows = self.df['pivot_low'].dropna()

        if len(pivot_lows) < 3:
            return patterns

        for i in range(len(pivot_lows) - 2):
            left_shoulder = pivot_lows.iloc[i]
            head = pivot_lows.iloc[i + 1]
            right_shoulder = pivot_lows.iloc[i + 2]

            # Head should be lowest
            if not (head < left_shoulder and head < right_shoulder):
                continue

            # Shoulders should be at similar level (within 5%)
            shoulder_diff = abs(left_shoulder - right_shoulder) / left_shoulder
            if shoulder_diff > 0.05:
                continue

            # Head should be significantly lower (at least 5%)
            if (left_shoulder - head) / left_shoulder < 0.05:
                continue

            idx_left = pivot_lows.index[i]
            idx_head = pivot_lows.index[i + 1]
            idx_right = pivot_lows.index[i + 2]

            # Find neckline (resistance)
            between_left_head = self.df.loc[idx_left:idx_head]
            between_head_right = self.df.loc[idx_head:idx_right]

            neckline_left = between_left_head['high'].max()
            neckline_right = between_head_right['high'].max()
            neckline = (neckline_left + neckline_right) / 2

            # Calculate confidence
            symmetry_score = 1.0 - shoulder_diff
            head_prominence = (left_shoulder - head) / left_shoulder
            prominence_score = min(1.0, head_prominence / 0.10)

            confidence = (symmetry_score * 0.6 + prominence_score * 0.4)

            patterns.append({
                'name': 'Inverse Head and Shoulders',
                'type': 'bullish_reversal',
                'confidence': round(confidence * 100, 1),
                'start_time': idx_left,
                'end_time': idx_right,
                'left_shoulder': round(left_shoulder, 2),
                'head': round(head, 2),
                'right_shoulder': round(right_shoulder, 2),
                'neckline': round(neckline, 2),
                'target': round(neckline + (neckline - head), 2),
                'stop_loss': round(right_shoulder * 0.98, 2)
            })

        return patterns

    # ===== TRIANGLES =====

    def detect_ascending_triangle(self) -> List[Dict]:
        """
        Detect ascending triangle pattern

        Pattern: Flat resistance + rising support
        Signal: Bullish continuation
        """
        patterns = []

        # Need at least 20 candles for triangle
        if len(self.df) < 20:
            return patterns

        # Look for flat top (resistance) and rising lows (support)
        window = 20
        for i in range(window, len(self.df)):
            window_data = self.df.iloc[i-window:i]

            highs = window_data['high']
            lows = window_data['low']

            # Check if highs are relatively flat (< 2% variation)
            high_max = highs.max()
            high_min = highs.min()
            if (high_max - high_min) / high_min > 0.02:
                continue

            # Check if lows are rising (linear regression slope > 0)
            x = np.arange(len(lows))
            slope_lows, _ = np.polyfit(x, lows.values, 1)

            if slope_lows <= 0:
                continue

            # Calculate confidence based on flatness of top and steepness of bottom
            flatness_score = 1.0 - ((high_max - high_min) / high_min / 0.02)
            slope_score = min(1.0, slope_lows / high_min * 100)

            confidence = (flatness_score * 0.6 + slope_score * 0.4)

            if confidence >= self.min_confidence:
                patterns.append({
                    'name': 'Ascending Triangle',
                    'type': 'bullish_continuation',
                    'confidence': round(confidence * 100, 1),
                    'start_time': window_data.index[0],
                    'end_time': window_data.index[-1],
                    'resistance_level': round(high_max, 2),
                    'support_slope': round(slope_lows, 4),
                    'target': round(high_max * 1.05, 2),
                    'stop_loss': round(lows.iloc[-1] * 0.98, 2)
                })

        return patterns

    def detect_descending_triangle(self) -> List[Dict]:
        """
        Detect descending triangle pattern

        Pattern: Flat support + falling resistance
        Signal: Bearish continuation
        """
        patterns = []

        if len(self.df) < 20:
            return patterns

        window = 20
        for i in range(window, len(self.df)):
            window_data = self.df.iloc[i-window:i]

            highs = window_data['high']
            lows = window_data['low']

            # Check if lows are relatively flat (< 2% variation)
            low_max = lows.max()
            low_min = lows.min()
            if (low_max - low_min) / low_min > 0.02:
                continue

            # Check if highs are falling (linear regression slope < 0)
            x = np.arange(len(highs))
            slope_highs, _ = np.polyfit(x, highs.values, 1)

            if slope_highs >= 0:
                continue

            # Calculate confidence
            flatness_score = 1.0 - ((low_max - low_min) / low_min / 0.02)
            slope_score = min(1.0, abs(slope_highs) / low_min * 100)

            confidence = (flatness_score * 0.6 + slope_score * 0.4)

            if confidence >= self.min_confidence:
                patterns.append({
                    'name': 'Descending Triangle',
                    'type': 'bearish_continuation',
                    'confidence': round(confidence * 100, 1),
                    'start_time': window_data.index[0],
                    'end_time': window_data.index[-1],
                    'support_level': round(low_min, 2),
                    'resistance_slope': round(slope_highs, 4),
                    'target': round(low_min * 0.95, 2),
                    'stop_loss': round(highs.iloc[-1] * 1.02, 2)
                })

        return patterns

    def detect_symmetrical_triangle(self) -> List[Dict]:
        """
        Detect symmetrical triangle pattern

        Pattern: Converging support and resistance
        Signal: Continuation (direction of breakout)
        """
        patterns = []

        if len(self.df) < 20:
            return patterns

        window = 20
        for i in range(window, len(self.df)):
            window_data = self.df.iloc[i-window:i]

            highs = window_data['high']
            lows = window_data['low']

            # Calculate slopes
            x = np.arange(len(highs))
            slope_highs, _ = np.polyfit(x, highs.values, 1)
            slope_lows, _ = np.polyfit(x, lows.values, 1)

            # Highs should be falling, lows should be rising
            if slope_highs >= 0 or slope_lows <= 0:
                continue

            # Slopes should be converging (similar magnitude)
            slope_ratio = abs(slope_highs) / abs(slope_lows)
            if slope_ratio < 0.5 or slope_ratio > 2.0:
                continue

            # Calculate confidence
            symmetry_score = 1.0 - abs(1.0 - slope_ratio)
            convergence_score = min(1.0, (abs(slope_highs) + abs(slope_lows)) / (highs.mean() * 0.01))

            confidence = (symmetry_score * 0.7 + convergence_score * 0.3)

            if confidence >= self.min_confidence:
                patterns.append({
                    'name': 'Symmetrical Triangle',
                    'type': 'neutral_continuation',
                    'confidence': round(confidence * 100, 1),
                    'start_time': window_data.index[0],
                    'end_time': window_data.index[-1],
                    'upper_slope': round(slope_highs, 4),
                    'lower_slope': round(slope_lows, 4),
                    'apex_estimate': round((highs.iloc[-1] + lows.iloc[-1]) / 2, 2)
                })

        return patterns

    # ===== WEDGES =====

    def detect_rising_wedge(self) -> List[Dict]:
        """
        Detect rising wedge pattern

        Pattern: Both support and resistance rising, converging
        Signal: Bearish reversal
        """
        patterns = []

        if len(self.df) < 20:
            return patterns

        window = 20
        for i in range(window, len(self.df)):
            window_data = self.df.iloc[i-window:i]

            highs = window_data['high']
            lows = window_data['low']

            # Calculate slopes
            x = np.arange(len(highs))
            slope_highs, _ = np.polyfit(x, highs.values, 1)
            slope_lows, _ = np.polyfit(x, lows.values, 1)

            # Both should be rising
            if slope_highs <= 0 or slope_lows <= 0:
                continue

            # Should be converging (resistance rising slower than support)
            if slope_highs >= slope_lows:
                continue

            confidence = min(1.0, (slope_lows - slope_highs) / lows.mean() * 100)

            if confidence >= self.min_confidence:
                patterns.append({
                    'name': 'Rising Wedge',
                    'type': 'bearish_reversal',
                    'confidence': round(confidence * 100, 1),
                    'start_time': window_data.index[0],
                    'end_time': window_data.index[-1],
                    'upper_slope': round(slope_highs, 4),
                    'lower_slope': round(slope_lows, 4),
                    'target': round(lows.iloc[0] * 0.95, 2),
                    'stop_loss': round(highs.iloc[-1] * 1.02, 2)
                })

        return patterns

    def detect_falling_wedge(self) -> List[Dict]:
        """
        Detect falling wedge pattern

        Pattern: Both support and resistance falling, converging
        Signal: Bullish reversal
        """
        patterns = []

        if len(self.df) < 20:
            return patterns

        window = 20
        for i in range(window, len(self.df)):
            window_data = self.df.iloc[i-window:i]

            highs = window_data['high']
            lows = window_data['low']

            # Calculate slopes
            x = np.arange(len(highs))
            slope_highs, _ = np.polyfit(x, highs.values, 1)
            slope_lows, _ = np.polyfit(x, lows.values, 1)

            # Both should be falling
            if slope_highs >= 0 or slope_lows >= 0:
                continue

            # Should be converging (support falling slower than resistance)
            if abs(slope_lows) >= abs(slope_highs):
                continue

            confidence = min(1.0, (abs(slope_highs) - abs(slope_lows)) / lows.mean() * 100)

            if confidence >= self.min_confidence:
                patterns.append({
                    'name': 'Falling Wedge',
                    'type': 'bullish_reversal',
                    'confidence': round(confidence * 100, 1),
                    'start_time': window_data.index[0],
                    'end_time': window_data.index[-1],
                    'upper_slope': round(slope_highs, 4),
                    'lower_slope': round(slope_lows, 4),
                    'target': round(highs.iloc[0] * 1.05, 2),
                    'stop_loss': round(lows.iloc[-1] * 0.98, 2)
                })

        return patterns

    # ===== FLAGS =====

    def detect_bull_flag(self) -> List[Dict]:
        """
        Detect bull flag pattern

        Pattern: Sharp rise (pole) + small consolidation (flag) sloping down
        Signal: Bullish continuation
        """
        patterns = []

        if len(self.df) < 30:
            return patterns

        # Look for sharp move up followed by consolidation
        for i in range(15, len(self.df) - 10):
            # Pole: Previous 15 candles
            pole_data = self.df.iloc[i-15:i]
            pole_gain = (pole_data['close'].iloc[-1] - pole_data['close'].iloc[0]) / pole_data['close'].iloc[0]

            # Need at least 5% gain for pole
            if pole_gain < 0.05:
                continue

            # Flag: Next 10 candles (consolidation)
            flag_data = self.df.iloc[i:i+10]
            flag_range = (flag_data['high'].max() - flag_data['low'].min()) / flag_data['close'].mean()

            # Flag should be consolidating (< 3% range)
            if flag_range > 0.03:
                continue

            # Check if flag is sloping down slightly
            x = np.arange(len(flag_data))
            slope, _ = np.polyfit(x, flag_data['close'].values, 1)

            if slope > 0:
                continue

            confidence = min(1.0, pole_gain / 0.10)  # 10% pole = 100% confidence

            if confidence >= self.min_confidence:
                patterns.append({
                    'name': 'Bull Flag',
                    'type': 'bullish_continuation',
                    'confidence': round(confidence * 100, 1),
                    'start_time': pole_data.index[0],
                    'end_time': flag_data.index[-1],
                    'pole_height': round(pole_gain * 100, 1),
                    'flag_slope': round(slope, 4),
                    'target': round(flag_data['close'].iloc[-1] * (1 + pole_gain), 2),
                    'stop_loss': round(flag_data['low'].min() * 0.98, 2)
                })

        return patterns

    def detect_bear_flag(self) -> List[Dict]:
        """
        Detect bear flag pattern

        Pattern: Sharp drop (pole) + small consolidation (flag) sloping up
        Signal: Bearish continuation
        """
        patterns = []

        if len(self.df) < 30:
            return patterns

        for i in range(15, len(self.df) - 10):
            # Pole: Previous 15 candles (downtrend)
            pole_data = self.df.iloc[i-15:i]
            pole_loss = (pole_data['close'].iloc[0] - pole_data['close'].iloc[-1]) / pole_data['close'].iloc[0]

            # Need at least 5% drop for pole
            if pole_loss < 0.05:
                continue

            # Flag: Next 10 candles (consolidation)
            flag_data = self.df.iloc[i:i+10]
            flag_range = (flag_data['high'].max() - flag_data['low'].min()) / flag_data['close'].mean()

            # Flag should be consolidating (< 3% range)
            if flag_range > 0.03:
                continue

            # Check if flag is sloping up slightly
            x = np.arange(len(flag_data))
            slope, _ = np.polyfit(x, flag_data['close'].values, 1)

            if slope < 0:
                continue

            confidence = min(1.0, pole_loss / 0.10)

            if confidence >= self.min_confidence:
                patterns.append({
                    'name': 'Bear Flag',
                    'type': 'bearish_continuation',
                    'confidence': round(confidence * 100, 1),
                    'start_time': pole_data.index[0],
                    'end_time': flag_data.index[-1],
                    'pole_height': round(pole_loss * 100, 1),
                    'flag_slope': round(slope, 4),
                    'target': round(flag_data['close'].iloc[-1] * (1 - pole_loss), 2),
                    'stop_loss': round(flag_data['high'].max() * 1.02, 2)
                })

        return patterns

    # ===== OTHER PATTERNS =====

    def detect_cup_and_handle(self) -> List[Dict]:
        """
        Detect cup and handle pattern

        Pattern: U-shaped recovery (cup) + small pullback (handle)
        Signal: Bullish continuation
        """
        patterns = []

        if len(self.df) < 40:
            return patterns

        # Look for U-shaped pattern followed by small consolidation
        for i in range(30, len(self.df) - 10):
            cup_data = self.df.iloc[i-30:i]

            # Cup should have low in middle
            cup_low_idx = cup_data['low'].idxmin()
            cup_low_pos = cup_data.index.get_loc(cup_low_idx) / len(cup_data)

            # Low should be roughly in middle (40-60% through)
            if cup_low_pos < 0.4 or cup_low_pos > 0.6:
                continue

            # Handle: Next 10 candles (small pullback)
            handle_data = self.df.iloc[i:i+10]
            handle_depth = (cup_data['close'].iloc[-1] - handle_data['low'].min()) / cup_data['close'].iloc[-1]

            # Handle should be shallow (< 5% pullback)
            if handle_depth > 0.05:
                continue

            # Cup depth
            cup_depth = (cup_data['close'].iloc[0] - cup_data['low'].min()) / cup_data['close'].iloc[0]

            # Cup should be significant (> 10%)
            if cup_depth < 0.10:
                continue

            confidence = min(1.0, cup_depth / 0.20)  # 20% cup = 100% confidence

            if confidence >= self.min_confidence:
                patterns.append({
                    'name': 'Cup and Handle',
                    'type': 'bullish_continuation',
                    'confidence': round(confidence * 100, 1),
                    'start_time': cup_data.index[0],
                    'end_time': handle_data.index[-1],
                    'cup_depth': round(cup_depth * 100, 1),
                    'handle_depth': round(handle_depth * 100, 1),
                    'target': round(handle_data['close'].iloc[-1] * (1 + cup_depth), 2),
                    'stop_loss': round(handle_data['low'].min() * 0.98, 2)
                })

        return patterns

    def detect_rounding_bottom(self) -> List[Dict]:
        """
        Detect rounding bottom (saucer) pattern

        Pattern: Gradual U-shaped recovery
        Signal: Bullish reversal
        """
        patterns = []

        if len(self.df) < 30:
            return patterns

        window = 30
        for i in range(window, len(self.df)):
            window_data = self.df.iloc[i-window:i]

            # Fit parabola to lows
            x = np.arange(len(window_data))
            lows = window_data['low'].values

            # Fit quadratic (y = ax^2 + bx + c)
            try:
                coeffs = np.polyfit(x, lows, 2)
                a, b, c = coeffs

                # For U-shape, a should be positive (opening upward)
                if a <= 0:
                    continue

                # Calculate goodness of fit
                fitted = np.polyval(coeffs, x)
                r_squared = 1 - (np.sum((lows - fitted) ** 2) / np.sum((lows - np.mean(lows)) ** 2))

                confidence = r_squared

                if confidence >= self.min_confidence:
                    patterns.append({
                        'name': 'Rounding Bottom',
                        'type': 'bullish_reversal',
                        'confidence': round(confidence * 100, 1),
                        'start_time': window_data.index[0],
                        'end_time': window_data.index[-1],
                        'curvature': round(a, 6),
                        'r_squared': round(r_squared, 3)
                    })
            except:
                continue

        return patterns

    def detect_rounding_top(self) -> List[Dict]:
        """
        Detect rounding top (inverted saucer) pattern

        Pattern: Gradual inverted U-shaped decline
        Signal: Bearish reversal
        """
        patterns = []

        if len(self.df) < 30:
            return patterns

        window = 30
        for i in range(window, len(self.df)):
            window_data = self.df.iloc[i-window:i]

            # Fit parabola to highs
            x = np.arange(len(window_data))
            highs = window_data['high'].values

            try:
                coeffs = np.polyfit(x, highs, 2)
                a, b, c = coeffs

                # For inverted U-shape, a should be negative (opening downward)
                if a >= 0:
                    continue

                # Calculate goodness of fit
                fitted = np.polyval(coeffs, x)
                r_squared = 1 - (np.sum((highs - fitted) ** 2) / np.sum((highs - np.mean(highs)) ** 2))

                confidence = r_squared

                if confidence >= self.min_confidence:
                    patterns.append({
                        'name': 'Rounding Top',
                        'type': 'bearish_reversal',
                        'confidence': round(confidence * 100, 1),
                        'start_time': window_data.index[0],
                        'end_time': window_data.index[-1],
                        'curvature': round(a, 6),
                        'r_squared': round(r_squared, 3)
                    })
            except:
                continue

        return patterns
