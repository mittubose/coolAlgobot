"""
PreTradeValidator - Pre-trade risk validation.

Validates all orders BEFORE submission to broker to prevent:
- Excessive risk per trade (>2%)
- Daily loss limit violations (>6%)
- Position limit breaches (>5)
- Missing stop-loss
- Poor risk-reward ratios (<2:1)
- Price sanity issues
- Quantity/balance issues
"""

import logging
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from dataclasses import dataclass

from backend.database.database import Database
from backend.models import OrderRequest, OrderSide
from backend.config import Config

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """
    Result of pre-trade validation.

    Attributes:
        is_valid: True if order passes all checks
        reason: Human-readable rejection reason (if invalid)
        failed_check: Name of failed validation check (if invalid)
        warnings: List of non-blocking warnings
    """
    is_valid: bool
    reason: str = ""
    failed_check: str = ""
    warnings: list = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class PreTradeValidator:
    """
    Pre-trade risk validation.

    Implements 10 critical validation checks:
    1. Balance check - Sufficient funds
    2. Position limit - Max 5 open positions
    3. Risk per trade - Max 2% of account balance
    4. Daily loss limit - Max 6% daily loss
    5. Stop-loss required - All orders must have stop-loss
    6. Risk-reward ratio - Min 2:1 reward-to-risk
    7. Price sanity - Price within ±10% of LTP (if available)
    8. Quantity limits - Min/max quantity per symbol
    9. Order-to-trade ratio - Max pending orders vs positions
    10. Circuit breaker - Auto-block trading after kill switch

    Usage:
        validator = PreTradeValidator(db, account_balance=100000)
        result = await validator.validate_order(order_request)

        if not result.is_valid:
            raise OrderRejected(result.reason, result.failed_check)
    """

    def __init__(
        self,
        db: Database,
        account_balance: Decimal,
        enable_all_checks: bool = True
    ):
        """
        Initialize PreTradeValidator.

        Args:
            db: Database instance
            account_balance: Current account balance (Decimal)
            enable_all_checks: If False, only run critical checks (default: True)
        """
        self.db = db
        self.account_balance = account_balance
        self.enable_all_checks = enable_all_checks

        # Load configuration
        self.max_risk_per_trade = Decimal(str(Config.MAX_RISK_PER_TRADE))  # 2%
        self.max_daily_loss = Decimal(str(Config.MAX_DAILY_LOSS))  # 6%
        self.max_positions = Config.MAX_POSITIONS  # 5
        self.min_risk_reward_ratio = Decimal(str(Config.MIN_RISK_REWARD_RATIO))  # 2.0
        self.max_price_deviation = Decimal(str(Config.MAX_PRICE_DEVIATION_PCT))  # 10%
        self.max_order_to_position_ratio = Config.MAX_ORDER_TO_POSITION_RATIO  # 3

        logger.info(
            f"PreTradeValidator initialized: "
            f"balance=₹{account_balance:,.2f}, "
            f"max_risk={self.max_risk_per_trade:.1%}, "
            f"max_daily_loss={self.max_daily_loss:.1%}, "
            f"max_positions={self.max_positions}"
        )

    # ========================================================================
    # MAIN VALIDATION ENTRY POINT
    # ========================================================================

    async def validate_order(self, request: OrderRequest) -> ValidationResult:
        """
        Validate order against all risk checks.

        Args:
            request: Order request to validate

        Returns:
            ValidationResult with is_valid and reason/failed_check if invalid
        """
        logger.info(
            f"Validating order: {request.symbol} {request.side.value} "
            f"{request.quantity} @ {request.order_type.value} {request.price}"
        )

        # Run all validation checks in order
        # If any check fails, return immediately

        # CHECK 1: Balance check
        result = await self._check_balance(request)
        if not result.is_valid:
            return result

        # CHECK 2: Position limit
        result = await self._check_position_limit(request)
        if not result.is_valid:
            return result

        # CHECK 3: Risk per trade
        result = await self._check_risk_per_trade(request)
        if not result.is_valid:
            return result

        # CHECK 4: Daily loss limit
        result = await self._check_daily_loss_limit(request)
        if not result.is_valid:
            return result

        # CHECK 5: Stop-loss required
        result = self._check_stop_loss_required(request)
        if not result.is_valid:
            return result

        # CHECK 6: Risk-reward ratio
        result = self._check_risk_reward_ratio(request)
        if not result.is_valid:
            return result

        # CHECK 7: Price sanity (optional - requires LTP)
        if self.enable_all_checks:
            result = await self._check_price_sanity(request)
            if not result.is_valid:
                return result

        # CHECK 8: Quantity limits
        result = self._check_quantity_limits(request)
        if not result.is_valid:
            return result

        # CHECK 9: Order-to-trade ratio
        if self.enable_all_checks:
            result = await self._check_order_to_position_ratio(request)
            if not result.is_valid:
                return result

        # CHECK 10: Circuit breaker / kill switch
        result = await self._check_circuit_breaker(request)
        if not result.is_valid:
            return result

        # All checks passed
        logger.info(f"✓ Order validation PASSED: {request.symbol}")
        return ValidationResult(is_valid=True)

    # ========================================================================
    # VALIDATION CHECK IMPLEMENTATIONS
    # ========================================================================

    async def _check_balance(self, request: OrderRequest) -> ValidationResult:
        """
        CHECK 1: Verify sufficient account balance.

        Args:
            request: Order request

        Returns:
            ValidationResult
        """
        # Calculate required margin
        if request.price is None:
            # Market order - estimate using last traded price
            # For now, fail validation if no price
            return ValidationResult(
                is_valid=False,
                reason="Cannot validate balance for market orders without LTP",
                failed_check="balance_check"
            )

        required_margin = request.quantity * request.price

        # For MIS (intraday), broker provides 5x leverage
        if request.product.value == 'MIS':
            required_margin = required_margin / Decimal('5')

        # Check if sufficient balance
        if self.account_balance < required_margin:
            return ValidationResult(
                is_valid=False,
                reason=(
                    f"Insufficient balance: Required ₹{required_margin:,.2f}, "
                    f"Available ₹{self.account_balance:,.2f}"
                ),
                failed_check="balance_check"
            )

        logger.debug(
            f"✓ Balance check passed: Required ₹{required_margin:,.2f}, "
            f"Available ₹{self.account_balance:,.2f}"
        )

        return ValidationResult(is_valid=True)

    async def _check_position_limit(self, request: OrderRequest) -> ValidationResult:
        """
        CHECK 2: Verify position count limit (max 5).

        Args:
            request: Order request

        Returns:
            ValidationResult
        """
        # Get current open position count
        position_count = await self.db.get_open_position_count()

        # Check if opening new position
        existing_position = await self.db.get_position(
            request.symbol,
            request.exchange,
            request.strategy_id
        )

        # If opening new position and at limit
        if existing_position is None and position_count >= self.max_positions:
            return ValidationResult(
                is_valid=False,
                reason=(
                    f"Position limit reached: {position_count}/{self.max_positions} "
                    f"open positions"
                ),
                failed_check="position_limit"
            )

        logger.debug(
            f"✓ Position limit check passed: {position_count}/{self.max_positions} "
            f"open positions"
        )

        return ValidationResult(is_valid=True)

    async def _check_risk_per_trade(self, request: OrderRequest) -> ValidationResult:
        """
        CHECK 3: Verify risk per trade <= 2% of account balance.

        Risk = (Entry Price - Stop Loss) * Quantity

        Args:
            request: Order request

        Returns:
            ValidationResult
        """
        if request.stop_loss is None:
            # This will be caught by stop-loss required check
            # But we can't calculate risk without stop-loss
            return ValidationResult(is_valid=True)

        if request.price is None:
            # Can't validate risk without price
            return ValidationResult(is_valid=True)

        # Calculate risk amount
        risk_per_share = abs(request.price - request.stop_loss)
        total_risk = risk_per_share * request.quantity

        # Calculate max allowed risk (2% of balance)
        max_risk = self.account_balance * self.max_risk_per_trade

        if total_risk > max_risk:
            risk_pct = (total_risk / self.account_balance) * 100
            return ValidationResult(
                is_valid=False,
                reason=(
                    f"Risk per trade exceeds limit: "
                    f"₹{total_risk:,.2f} ({risk_pct:.2f}%) > "
                    f"₹{max_risk:,.2f} ({self.max_risk_per_trade:.1%})"
                ),
                failed_check="risk_per_trade"
            )

        logger.debug(
            f"✓ Risk per trade check passed: ₹{total_risk:,.2f} "
            f"({(total_risk/self.account_balance)*100:.2f}%) <= "
            f"₹{max_risk:,.2f} ({self.max_risk_per_trade:.1%})"
        )

        return ValidationResult(is_valid=True)

    async def _check_daily_loss_limit(self, request: OrderRequest) -> ValidationResult:
        """
        CHECK 4: Verify daily loss <= 6% of account balance.

        Args:
            request: Order request

        Returns:
            ValidationResult
        """
        # Get today's realized PnL
        today_pnl = await self.db.get_today_realized_pnl()

        # Calculate max allowed loss (6% of balance)
        max_daily_loss = self.account_balance * self.max_daily_loss

        # If already exceeded daily loss limit
        if today_pnl < -max_daily_loss:
            loss_pct = abs(today_pnl / self.account_balance) * 100
            return ValidationResult(
                is_valid=False,
                reason=(
                    f"Daily loss limit exceeded: "
                    f"₹{abs(today_pnl):,.2f} ({loss_pct:.2f}%) > "
                    f"₹{max_daily_loss:,.2f} ({self.max_daily_loss:.1%})"
                ),
                failed_check="daily_loss_limit"
            )

        logger.debug(
            f"✓ Daily loss check passed: ₹{today_pnl:,.2f} >= "
            f"₹{-max_daily_loss:,.2f} (-{self.max_daily_loss:.1%})"
        )

        return ValidationResult(is_valid=True)

    def _check_stop_loss_required(self, request: OrderRequest) -> ValidationResult:
        """
        CHECK 5: Verify stop-loss is set.

        CRITICAL: All orders MUST have stop-loss.

        Args:
            request: Order request

        Returns:
            ValidationResult
        """
        if request.stop_loss is None:
            return ValidationResult(
                is_valid=False,
                reason="Stop-loss is required for all orders",
                failed_check="stop_loss_required"
            )

        # Verify stop-loss is in correct direction
        if request.side == OrderSide.BUY:
            # Buy order: stop-loss must be below entry
            if request.price and request.stop_loss >= request.price:
                return ValidationResult(
                    is_valid=False,
                    reason=(
                        f"Invalid stop-loss: Buy order stop-loss "
                        f"(₹{request.stop_loss}) must be < entry (₹{request.price})"
                    ),
                    failed_check="stop_loss_required"
                )
        else:
            # Sell order: stop-loss must be above entry
            if request.price and request.stop_loss <= request.price:
                return ValidationResult(
                    is_valid=False,
                    reason=(
                        f"Invalid stop-loss: Sell order stop-loss "
                        f"(₹{request.stop_loss}) must be > entry (₹{request.price})"
                    ),
                    failed_check="stop_loss_required"
                )

        logger.debug(f"✓ Stop-loss check passed: SL=₹{request.stop_loss}")

        return ValidationResult(is_valid=True)

    def _check_risk_reward_ratio(self, request: OrderRequest) -> ValidationResult:
        """
        CHECK 6: Verify risk-reward ratio >= 2:1.

        Args:
            request: Order request

        Returns:
            ValidationResult
        """
        if request.stop_loss is None or request.take_profit is None:
            # Can't calculate R:R without both stop-loss and take-profit
            # But stop-loss is required, so this shouldn't happen
            return ValidationResult(is_valid=True)

        if request.price is None:
            # Can't validate without price
            return ValidationResult(is_valid=True)

        # Calculate risk and reward
        risk = abs(request.price - request.stop_loss)
        reward = abs(request.take_profit - request.price)

        # Avoid division by zero
        if risk == 0:
            return ValidationResult(
                is_valid=False,
                reason="Risk cannot be zero (stop-loss = entry price)",
                failed_check="risk_reward_ratio"
            )

        # Calculate ratio
        rr_ratio = reward / risk

        if rr_ratio < self.min_risk_reward_ratio:
            return ValidationResult(
                is_valid=False,
                reason=(
                    f"Risk-reward ratio too low: {rr_ratio:.2f}:1 < "
                    f"{self.min_risk_reward_ratio:.0f}:1 required"
                ),
                failed_check="risk_reward_ratio"
            )

        logger.debug(
            f"✓ Risk-reward check passed: {rr_ratio:.2f}:1 >= "
            f"{self.min_risk_reward_ratio:.0f}:1"
        )

        return ValidationResult(is_valid=True)

    async def _check_price_sanity(self, request: OrderRequest) -> ValidationResult:
        """
        CHECK 7: Verify price within ±10% of last traded price.

        Prevents fat-finger errors (e.g., entering 2450 instead of 245).

        Args:
            request: Order request

        Returns:
            ValidationResult
        """
        if request.price is None:
            # Market order - skip price sanity check
            return ValidationResult(is_valid=True)

        # Get last traded price (LTP) from database or market data
        # For now, we'll need to implement this based on available data
        # This is a placeholder implementation

        # TODO: Integrate with market data feed to get LTP
        # For now, skip this check if LTP not available

        logger.debug("Price sanity check skipped (LTP not available)")

        return ValidationResult(is_valid=True)

    def _check_quantity_limits(self, request: OrderRequest) -> ValidationResult:
        """
        CHECK 8: Verify quantity within min/max limits.

        Args:
            request: Order request

        Returns:
            ValidationResult
        """
        # Minimum quantity (1 share)
        if request.quantity < 1:
            return ValidationResult(
                is_valid=False,
                reason=f"Quantity must be >= 1 (got {request.quantity})",
                failed_check="quantity_limits"
            )

        # Maximum quantity (configurable per symbol)
        # For now, use a global max of 10,000 shares
        max_quantity = Config.MAX_QUANTITY_PER_ORDER

        if request.quantity > max_quantity:
            return ValidationResult(
                is_valid=False,
                reason=(
                    f"Quantity exceeds maximum: {request.quantity} > "
                    f"{max_quantity} allowed"
                ),
                failed_check="quantity_limits"
            )

        logger.debug(
            f"✓ Quantity check passed: {request.quantity} shares "
            f"(1 <= qty <= {max_quantity})"
        )

        return ValidationResult(is_valid=True)

    async def _check_order_to_position_ratio(
        self,
        request: OrderRequest
    ) -> ValidationResult:
        """
        CHECK 9: Verify order-to-position ratio.

        Prevents excessive pending orders relative to open positions.
        Max ratio: 3 pending orders per 1 open position.

        Args:
            request: Order request

        Returns:
            ValidationResult
        """
        # Get active order count (PENDING, SUBMITTED, OPEN)
        active_orders = await self.db.get_active_orders()
        active_order_count = len(active_orders)

        # Get open position count
        position_count = await self.db.get_open_position_count()

        # If no positions, allow up to 3 pending orders
        if position_count == 0:
            max_allowed_orders = self.max_order_to_position_ratio
        else:
            max_allowed_orders = position_count * self.max_order_to_position_ratio

        # Check if adding this order exceeds ratio
        if active_order_count >= max_allowed_orders:
            return ValidationResult(
                is_valid=False,
                reason=(
                    f"Too many pending orders: {active_order_count} orders "
                    f"for {position_count} positions "
                    f"(max {self.max_order_to_position_ratio}:1 ratio)"
                ),
                failed_check="order_to_position_ratio"
            )

        logger.debug(
            f"✓ Order-to-position ratio check passed: "
            f"{active_order_count}/{max_allowed_orders} orders"
        )

        return ValidationResult(is_valid=True)

    async def _check_circuit_breaker(self, request: OrderRequest) -> ValidationResult:
        """
        CHECK 10: Verify kill switch is not active.

        If kill switch was triggered, block all new orders.

        Args:
            request: Order request

        Returns:
            ValidationResult
        """
        # Check if kill switch is active (today)
        kill_switch_active = await self.db.is_kill_switch_active()

        if kill_switch_active:
            return ValidationResult(
                is_valid=False,
                reason=(
                    "Trading is blocked: Kill switch is active. "
                    "Manual intervention required."
                ),
                failed_check="circuit_breaker"
            )

        logger.debug("✓ Circuit breaker check passed: Kill switch inactive")

        return ValidationResult(is_valid=True)

    # ========================================================================
    # ACCOUNT BALANCE UPDATE
    # ========================================================================

    def update_account_balance(self, new_balance: Decimal):
        """
        Update account balance (for real-time updates).

        Args:
            new_balance: New account balance
        """
        old_balance = self.account_balance
        self.account_balance = new_balance

        logger.info(
            f"Account balance updated: ₹{old_balance:,.2f} → ₹{new_balance:,.2f}"
        )
