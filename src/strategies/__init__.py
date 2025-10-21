"""
Trading Strategy Templates
Built-in strategy implementations
"""

from .ema_crossover import EMACrossoverStrategy
from .rsi_strategy import RSIStrategy
from .breakout_strategy import BreakoutStrategy

__all__ = [
    'EMACrossoverStrategy',
    'RSIStrategy',
    'BreakoutStrategy'
]
