"""
Risk Manager
Implements risk management rules and position sizing
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from src.utils.logger import setup_logger


class RiskManager:
    """
    Manages trading risk
    - Position sizing based on risk parameters
    - Daily loss limits
    - Maximum position limits
    - Maximum drawdown protection
    - Circuit breaker functionality
    """

    def __init__(self, config: Dict):
        """
        Initialize Risk Manager

        Args:
            config: Risk configuration dict containing:
                - capital: Total trading capital
                - max_risk_per_trade: Max % of capital to risk per trade
                - max_position_size: Max % of capital per position
                - max_daily_loss: Max daily loss in rupees
                - max_daily_loss_pct: Max daily loss as % of capital
                - max_positions: Maximum number of concurrent positions
                - max_drawdown_pct: Maximum drawdown % before stopping
        """
        self.config = config
        self.logger = setup_logger('risk_manager')

        # Capital tracking
        self.starting_capital = config.get('capital', 100000)
        self.current_capital = self.starting_capital
        self.peak_capital = self.starting_capital

        # Risk parameters
        self.max_risk_per_trade = config.get('max_risk_per_trade', 1.0)  # %
        self.max_position_size = config.get('max_position_size', 10.0)  # %
        self.max_daily_loss = config.get('max_daily_loss', 5000)  # Absolute
        self.max_daily_loss_pct = config.get('max_daily_loss_pct', 3.0)  # %
        self.max_positions = config.get('max_positions', 5)
        self.max_drawdown_pct = config.get('max_drawdown_pct', 10.0)  # %

        # Daily tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.current_date = datetime.now().date()

        # Circuit breaker
        self.trading_halted = False
        self.halt_reason = None

        self.logger.info(
            f"RiskManager initialized with capital: {self.starting_capital}, "
            f"max risk per trade: {self.max_risk_per_trade}%"
        )

    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        side: str = 'BUY'
    ) -> Tuple[int, float]:
        """
        Calculate position size based on risk parameters

        Args:
            entry_price: Entry price
            stop_loss: Stop-loss price
            side: BUY or SELL

        Returns:
            Tuple of (quantity, risk_amount)
        """
        try:
            # Calculate risk per share
            if side.upper() == 'BUY':
                risk_per_share = abs(entry_price - stop_loss)
            else:
                risk_per_share = abs(stop_loss - entry_price)

            if risk_per_share <= 0:
                self.logger.error("Invalid stop-loss: risk per share <= 0")
                return 0, 0.0

            # Calculate max risk amount for this trade
            max_risk_amount = self.current_capital * (self.max_risk_per_trade / 100)

            # Calculate quantity based on risk
            quantity = int(max_risk_amount / risk_per_share)

            # Check against max position size
            max_position_value = self.current_capital * (self.max_position_size / 100)
            max_quantity_by_size = int(max_position_value / entry_price)

            # Use the smaller quantity
            final_quantity = min(quantity, max_quantity_by_size)

            # Calculate actual risk
            actual_risk = final_quantity * risk_per_share

            self.logger.info(
                f"Position sizing: entry={entry_price}, SL={stop_loss}, "
                f"qty={final_quantity}, risk={actual_risk:.2f}"
            )

            return final_quantity, actual_risk

        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0, 0.0

    def validate_trade(
        self,
        quantity: int,
        price: float,
        current_positions: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate if a trade should be allowed

        Args:
            quantity: Proposed quantity
            price: Trade price
            current_positions: Number of current open positions

        Returns:
            Tuple of (allowed: bool, reason: str or None)
        """
        try:
            # Check if trading is halted
            if self.trading_halted:
                return False, f"Trading halted: {self.halt_reason}"

            # Reset daily tracking if new day
            self._check_new_day()

            # Check max positions
            if current_positions >= self.max_positions:
                return False, f"Maximum positions limit reached ({self.max_positions})"

            # Check position size
            position_value = quantity * price
            max_allowed = self.current_capital * (self.max_position_size / 100)

            if position_value > max_allowed:
                return False, f"Position size exceeds limit (max: {max_allowed:.2f})"

            # Check daily loss limit
            if self.daily_pnl < 0:
                abs_loss = abs(self.daily_pnl)

                # Check absolute limit
                if abs_loss >= self.max_daily_loss:
                    self._halt_trading("Daily loss limit reached (absolute)")
                    return False, "Daily loss limit reached"

                # Check percentage limit
                loss_pct = (abs_loss / self.starting_capital) * 100
                if loss_pct >= self.max_daily_loss_pct:
                    self._halt_trading("Daily loss limit reached (percentage)")
                    return False, "Daily loss percentage limit reached"

            # Check drawdown
            drawdown_pct = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
            if drawdown_pct >= self.max_drawdown_pct:
                self._halt_trading(f"Maximum drawdown reached ({drawdown_pct:.2f}%)")
                return False, f"Maximum drawdown limit reached"

            # All checks passed
            return True, None

        except Exception as e:
            self.logger.error(f"Error validating trade: {e}")
            return False, f"Validation error: {str(e)}"

    def update_capital(self, pnl: float):
        """
        Update capital after trade

        Args:
            pnl: Profit/Loss from trade
        """
        self._check_new_day()

        self.current_capital += pnl
        self.daily_pnl += pnl
        self.daily_trades += 1

        # Update peak capital
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        self.logger.info(
            f"Capital updated: {self.current_capital:.2f} "
            f"(P&L: {pnl:+.2f}, Daily: {self.daily_pnl:+.2f})"
        )

    def _check_new_day(self):
        """Check if it's a new trading day and reset daily tracking"""
        today = datetime.now().date()

        if today != self.current_date:
            self.logger.info(
                f"New trading day - Previous day P&L: {self.daily_pnl:.2f}, "
                f"Trades: {self.daily_trades}"
            )

            self.current_date = today
            self.daily_pnl = 0.0
            self.daily_trades = 0

            # Reset circuit breaker
            if self.trading_halted:
                self.resume_trading()

    def _halt_trading(self, reason: str):
        """Halt all trading"""
        self.trading_halted = True
        self.halt_reason = reason
        self.logger.critical(f"TRADING HALTED: {reason}")

    def resume_trading(self):
        """Resume trading after halt"""
        if self.trading_halted:
            self.logger.info(f"Trading resumed (was halted: {self.halt_reason})")
            self.trading_halted = False
            self.halt_reason = None

    def get_available_capital(self) -> float:
        """
        Get available capital for new positions

        Returns:
            Available capital amount
        """
        # Could be enhanced to consider reserved capital, margin, etc.
        return self.current_capital

    def get_max_position_value(self) -> float:
        """
        Get maximum allowed position value

        Returns:
            Max position value
        """
        return self.current_capital * (self.max_position_size / 100)

    def get_remaining_daily_loss_buffer(self) -> float:
        """
        Get remaining daily loss buffer

        Returns:
            Remaining loss buffer before hitting limit
        """
        if self.daily_pnl >= 0:
            return self.max_daily_loss

        abs_loss = abs(self.daily_pnl)
        return max(0, self.max_daily_loss - abs_loss)

    def get_drawdown_info(self) -> Dict:
        """
        Get current drawdown information

        Returns:
            Dict with drawdown stats
        """
        if self.peak_capital == 0:
            drawdown_pct = 0
        else:
            drawdown_pct = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100

        drawdown_amount = self.peak_capital - self.current_capital

        return {
            'peak_capital': self.peak_capital,
            'current_capital': self.current_capital,
            'drawdown_amount': drawdown_amount,
            'drawdown_pct': round(drawdown_pct, 2),
            'max_allowed_drawdown_pct': self.max_drawdown_pct,
            'buffer_pct': round(self.max_drawdown_pct - drawdown_pct, 2)
        }

    def calculate_stop_loss(
        self,
        entry_price: float,
        side: str,
        risk_pct: float = None
    ) -> float:
        """
        Calculate stop-loss price based on risk percentage

        Args:
            entry_price: Entry price
            side: BUY or SELL
            risk_pct: Risk % (default uses max_risk_per_trade)

        Returns:
            Stop-loss price
        """
        if risk_pct is None:
            risk_pct = self.max_risk_per_trade

        risk_amount = entry_price * (risk_pct / 100)

        if side.upper() == 'BUY':
            return entry_price - risk_amount
        else:
            return entry_price + risk_amount

    def calculate_target(
        self,
        entry_price: float,
        stop_loss: float,
        side: str,
        risk_reward_ratio: float = 2.0
    ) -> float:
        """
        Calculate target price based on risk-reward ratio

        Args:
            entry_price: Entry price
            stop_loss: Stop-loss price
            side: BUY or SELL
            risk_reward_ratio: Risk-reward ratio (default 2:1)

        Returns:
            Target price
        """
        risk = abs(entry_price - stop_loss)
        reward = risk * risk_reward_ratio

        if side.upper() == 'BUY':
            return entry_price + reward
        else:
            return entry_price - reward

    def get_summary(self) -> Dict:
        """
        Get summary of risk manager status

        Returns:
            Dict with status information
        """
        drawdown_info = self.get_drawdown_info()

        return {
            'starting_capital': self.starting_capital,
            'current_capital': round(self.current_capital, 2),
            'peak_capital': round(self.peak_capital, 2),
            'daily_pnl': round(self.daily_pnl, 2),
            'daily_trades': self.daily_trades,
            'trading_halted': self.trading_halted,
            'halt_reason': self.halt_reason,
            'risk_parameters': {
                'max_risk_per_trade_pct': self.max_risk_per_trade,
                'max_position_size_pct': self.max_position_size,
                'max_daily_loss': self.max_daily_loss,
                'max_daily_loss_pct': self.max_daily_loss_pct,
                'max_positions': self.max_positions,
                'max_drawdown_pct': self.max_drawdown_pct
            },
            'drawdown': drawdown_info,
            'remaining_daily_loss_buffer': round(self.get_remaining_daily_loss_buffer(), 2),
            'max_position_value': round(self.get_max_position_value(), 2)
        }

    def reset(self, new_capital: float = None):
        """
        Reset risk manager state

        Args:
            new_capital: Optional new starting capital
        """
        if new_capital:
            self.starting_capital = new_capital

        self.current_capital = self.starting_capital
        self.peak_capital = self.starting_capital
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.trading_halted = False
        self.halt_reason = None

        self.logger.info(f"RiskManager reset with capital: {self.starting_capital}")
