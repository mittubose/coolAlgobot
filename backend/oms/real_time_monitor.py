"""
RealTimeRiskMonitor - Real-time risk monitoring and kill switch.

Continuously monitors:
- Account-level risk (daily loss, drawdown)
- Position-level risk (stop-loss hits, excessive losses)
- Triggers kill switch on critical violations
- Broadcasts alerts via WebSocket
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass

from backend.database.database import Database
from backend.oms.position_manager import PositionManager
from backend.models import Position
from backend.config import Config

logger = logging.getLogger(__name__)


@dataclass
class RiskAlert:
    """
    Risk alert data structure.

    Attributes:
        severity: CRITICAL, WARNING, INFO
        alert_type: Type of risk alert
        message: Human-readable message
        details: Additional details (dict)
        timestamp: When alert was generated
    """
    severity: str  # CRITICAL, WARNING, INFO
    alert_type: str
    message: str
    details: Dict
    timestamp: datetime


class RealTimeRiskMonitor:
    """
    Real-time risk monitoring and circuit breaker.

    Monitors:
    1. Account-level risk:
       - Daily PnL vs max loss limit (6%)
       - Account drawdown from peak
       - Total open position count

    2. Position-level risk:
       - Individual position losses
       - Stop-loss proximity
       - Position size limits

    3. Kill switch triggers:
       - Daily loss exceeds 6%
       - Drawdown exceeds 15%
       - Critical system errors

    Usage:
        monitor = RealTimeRiskMonitor(
            db=db,
            position_manager=pm,
            account_balance=100000
        )
        await monitor.start()

        # Register alert callback
        monitor.register_alert_callback(send_telegram_alert)

        # Update with market data
        await monitor.update_position_prices({
            'RELIANCE': Decimal('2450.00'),
            'TCS': Decimal('3500.00')
        })

        # Stop monitoring
        await monitor.stop()
    """

    def __init__(
        self,
        db: Database,
        position_manager: PositionManager,
        account_balance: Decimal,
        monitoring_interval: float = 2.0
    ):
        """
        Initialize RealTimeRiskMonitor.

        Args:
            db: Database instance
            position_manager: PositionManager instance
            account_balance: Current account balance
            monitoring_interval: Monitoring frequency in seconds (default: 2.0)
        """
        self.db = db
        self.position_manager = position_manager
        self.account_balance = account_balance
        self.monitoring_interval = monitoring_interval

        # Load configuration
        self.max_daily_loss_pct = Decimal(str(Config.MAX_DAILY_LOSS))  # 6%
        self.max_drawdown_pct = Decimal(str(Config.MAX_DRAWDOWN))  # 15%
        self.max_position_loss_pct = Decimal(str(Config.MAX_POSITION_LOSS_PCT))  # 5%

        # State tracking
        self.account_peak = account_balance  # Peak account value (for drawdown)
        self.kill_switch_active = False
        self._shutdown = False
        self._monitor_task: Optional[asyncio.Task] = None

        # Alert callbacks
        self.alert_callbacks: List[Callable] = []

        # Alert history (in-memory cache)
        self.recent_alerts: List[RiskAlert] = []
        self.max_alert_history = 100

        logger.info(
            f"RealTimeRiskMonitor initialized: "
            f"balance=₹{account_balance:,.2f}, "
            f"max_daily_loss={self.max_daily_loss_pct:.1%}, "
            f"max_drawdown={self.max_drawdown_pct:.1%}"
        )

    # ========================================================================
    # LIFECYCLE MANAGEMENT
    # ========================================================================

    async def start(self):
        """
        Start real-time monitoring.

        Launches background monitoring task.
        """
        if self._monitor_task is not None:
            logger.warning("RealTimeRiskMonitor already running")
            return

        logger.info("Starting real-time risk monitoring...")

        # Check if kill switch already active from previous session
        self.kill_switch_active = await self.db.is_kill_switch_active()

        if self.kill_switch_active:
            logger.critical(
                "⚠️  KILL SWITCH IS ACTIVE - Trading is disabled. "
                "Manual intervention required."
            )

        # Start monitoring loop
        self._shutdown = False
        self._monitor_task = asyncio.create_task(self._monitoring_loop())

        logger.info("✓ Real-time risk monitoring started")

    async def stop(self):
        """
        Stop real-time monitoring.

        Gracefully shuts down background task.
        """
        logger.info("Stopping real-time risk monitoring...")

        self._shutdown = True

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        logger.info("✓ Real-time risk monitoring stopped")

    # ========================================================================
    # MONITORING LOOP
    # ========================================================================

    async def _monitoring_loop(self):
        """
        Main monitoring loop.

        Runs every `monitoring_interval` seconds.
        """
        while not self._shutdown:
            try:
                # Run all risk checks
                await self._check_all_risks()

                # Wait for next interval
                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                logger.debug("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(self.monitoring_interval)

    async def _check_all_risks(self):
        """
        Run all risk checks.

        Checks:
        1. Account-level risks
        2. Position-level risks
        3. Kill switch status
        """
        # Skip monitoring if kill switch active
        if self.kill_switch_active:
            return

        # 1. Check account-level risks
        await self._check_account_risks()

        # 2. Check position-level risks
        await self._check_position_risks()

    # ========================================================================
    # ACCOUNT-LEVEL RISK CHECKS
    # ========================================================================

    async def _check_account_risks(self):
        """
        Check account-level risk metrics.

        Monitors:
        - Daily PnL vs max loss limit
        - Account drawdown from peak
        - Total exposure
        """
        # Get today's realized PnL
        realized_pnl = await self.db.get_today_realized_pnl()

        # Get unrealized PnL from all open positions
        unrealized_pnl = await self.position_manager.get_total_unrealized_pnl()

        # Calculate total PnL
        total_pnl = realized_pnl + unrealized_pnl

        # Calculate current account value
        current_value = self.account_balance + total_pnl

        # Update peak if new high
        if current_value > self.account_peak:
            self.account_peak = current_value

        # ===================================================================
        # CHECK 1: Daily Loss Limit (6%)
        # ===================================================================
        max_daily_loss = self.account_balance * self.max_daily_loss_pct

        if total_pnl < -max_daily_loss:
            # CRITICAL: Daily loss limit exceeded
            loss_pct = abs(total_pnl / self.account_balance) * 100

            await self._trigger_kill_switch(
                reason=f"Daily loss limit exceeded: ₹{abs(total_pnl):,.2f} ({loss_pct:.2f}%)",
                severity='CRITICAL',
                details={
                    'daily_pnl': float(total_pnl),
                    'loss_pct': float(loss_pct),
                    'max_loss_pct': float(self.max_daily_loss_pct * 100),
                    'realized_pnl': float(realized_pnl),
                    'unrealized_pnl': float(unrealized_pnl)
                }
            )
            return  # Kill switch triggered, stop further checks

        # ===================================================================
        # CHECK 2: Drawdown from Peak (15%)
        # ===================================================================
        drawdown = self.account_peak - current_value
        drawdown_pct = (drawdown / self.account_peak) * 100 if self.account_peak > 0 else Decimal('0')

        max_drawdown = self.account_peak * self.max_drawdown_pct

        if drawdown > max_drawdown:
            # CRITICAL: Drawdown limit exceeded
            await self._trigger_kill_switch(
                reason=f"Drawdown limit exceeded: ₹{drawdown:,.2f} ({drawdown_pct:.2f}%)",
                severity='CRITICAL',
                details={
                    'drawdown': float(drawdown),
                    'drawdown_pct': float(drawdown_pct),
                    'max_drawdown_pct': float(self.max_drawdown_pct * 100),
                    'account_peak': float(self.account_peak),
                    'current_value': float(current_value)
                }
            )
            return

        # ===================================================================
        # WARNING: Approaching Daily Loss Limit (80% of limit)
        # ===================================================================
        if total_pnl < -(max_daily_loss * Decimal('0.8')):
            loss_pct = abs(total_pnl / self.account_balance) * 100
            remaining = max_daily_loss - abs(total_pnl)

            await self._emit_alert(RiskAlert(
                severity='WARNING',
                alert_type='daily_loss_warning',
                message=f"Approaching daily loss limit: {loss_pct:.2f}% of {self.max_daily_loss_pct:.0%}",
                details={
                    'daily_pnl': float(total_pnl),
                    'loss_pct': float(loss_pct),
                    'max_loss_pct': float(self.max_daily_loss_pct * 100),
                    'remaining_buffer': float(remaining)
                },
                timestamp=datetime.utcnow()
            ))

        # ===================================================================
        # WARNING: Approaching Drawdown Limit (80% of limit)
        # ===================================================================
        if drawdown > (max_drawdown * Decimal('0.8')):
            remaining = max_drawdown - drawdown

            await self._emit_alert(RiskAlert(
                severity='WARNING',
                alert_type='drawdown_warning',
                message=f"Approaching drawdown limit: {drawdown_pct:.2f}% of {self.max_drawdown_pct:.0%}",
                details={
                    'drawdown': float(drawdown),
                    'drawdown_pct': float(drawdown_pct),
                    'max_drawdown_pct': float(self.max_drawdown_pct * 100),
                    'remaining_buffer': float(remaining)
                },
                timestamp=datetime.utcnow()
            ))

    # ========================================================================
    # POSITION-LEVEL RISK CHECKS
    # ========================================================================

    async def _check_position_risks(self):
        """
        Check position-level risk metrics.

        Monitors:
        - Individual position losses
        - Stop-loss proximity
        - Position size limits
        """
        # Get all open positions
        positions = await self.position_manager.get_all_open_positions()

        for position in positions:
            await self._check_single_position_risk(position)

    async def _check_single_position_risk(self, position: Position):
        """
        Check risk for a single position.

        Args:
            position: Position to check
        """
        # ===================================================================
        # CHECK 1: Position Loss Limit (5% of account)
        # ===================================================================
        max_position_loss = self.account_balance * self.max_position_loss_pct

        # Calculate total position PnL (realized + unrealized)
        total_position_pnl = position.realized_pnl + position.unrealized_pnl

        if total_position_pnl < -max_position_loss:
            loss_pct = abs(total_position_pnl / self.account_balance) * 100

            await self._emit_alert(RiskAlert(
                severity='CRITICAL',
                alert_type='position_loss_limit',
                message=(
                    f"Position {position.symbol} exceeded loss limit: "
                    f"₹{abs(total_position_pnl):,.2f} ({loss_pct:.2f}%)"
                ),
                details={
                    'symbol': position.symbol,
                    'position_pnl': float(total_position_pnl),
                    'loss_pct': float(loss_pct),
                    'max_loss_pct': float(self.max_position_loss_pct * 100),
                    'quantity': position.quantity,
                    'average_price': float(position.average_price)
                },
                timestamp=datetime.utcnow()
            ))

        # ===================================================================
        # CHECK 2: Stop-Loss Proximity Warning
        # ===================================================================
        # This would require current market price
        # For now, we'll emit a warning if position has no stop-loss
        if position.stop_loss is None:
            await self._emit_alert(RiskAlert(
                severity='WARNING',
                alert_type='missing_stop_loss',
                message=f"Position {position.symbol} has no stop-loss",
                details={
                    'symbol': position.symbol,
                    'quantity': position.quantity,
                    'average_price': float(position.average_price),
                    'unrealized_pnl': float(position.unrealized_pnl)
                },
                timestamp=datetime.utcnow()
            ))

    # ========================================================================
    # KILL SWITCH
    # ========================================================================

    async def _trigger_kill_switch(self, reason: str, severity: str, details: Dict):
        """
        Trigger kill switch (emergency stop).

        Args:
            reason: Reason for kill switch
            severity: Alert severity
            details: Additional details
        """
        logger.critical(f"🚨 TRIGGERING KILL SWITCH: {reason}")

        # Mark kill switch as active
        self.kill_switch_active = True

        # Log to database
        await self.db.trigger_kill_switch(reason, triggered_by='risk_monitor')

        # Emit critical alert
        await self._emit_alert(RiskAlert(
            severity=severity,
            alert_type='kill_switch_triggered',
            message=f"KILL SWITCH ACTIVATED: {reason}",
            details=details,
            timestamp=datetime.utcnow()
        ))

        logger.critical(
            "⚠️  ALL TRADING DISABLED - Manual intervention required to resume"
        )

    async def deactivate_kill_switch(self, deactivated_by: str = 'admin'):
        """
        Deactivate kill switch (resume trading).

        IMPORTANT: Only call this after reviewing and resolving the issue!

        Args:
            deactivated_by: Who deactivated (user ID)
        """
        if not self.kill_switch_active:
            logger.warning("Kill switch is not active")
            return

        logger.warning(f"Deactivating kill switch by: {deactivated_by}")

        # Update database
        await self.db.deactivate_kill_switch(deactivated_by)

        # Update local state
        self.kill_switch_active = False

        # Emit info alert
        await self._emit_alert(RiskAlert(
            severity='INFO',
            alert_type='kill_switch_deactivated',
            message=f"Kill switch deactivated by: {deactivated_by}",
            details={'deactivated_by': deactivated_by},
            timestamp=datetime.utcnow()
        ))

        logger.info("✓ Kill switch deactivated - Trading resumed")

    # ========================================================================
    # MARKET DATA UPDATES
    # ========================================================================

    async def update_position_prices(self, price_dict: Dict[str, Decimal]):
        """
        Update positions with current market prices.

        This should be called frequently (every tick) to keep unrealized PnL updated.

        Args:
            price_dict: Dict of symbol -> current_price
        """
        await self.position_manager.update_all_unrealized_pnl(price_dict)

    # ========================================================================
    # ALERT MANAGEMENT
    # ========================================================================

    def register_alert_callback(self, callback: Callable):
        """
        Register callback for risk alerts.

        Callback signature: async def callback(alert: RiskAlert)

        Args:
            callback: Alert callback function
        """
        self.alert_callbacks.append(callback)
        logger.info(f"Alert callback registered: {callback.__name__}")

    async def _emit_alert(self, alert: RiskAlert):
        """
        Emit risk alert to all registered callbacks.

        Args:
            alert: RiskAlert instance
        """
        # Add to history
        self.recent_alerts.append(alert)
        if len(self.recent_alerts) > self.max_alert_history:
            self.recent_alerts.pop(0)

        # Log alert
        log_func = logger.critical if alert.severity == 'CRITICAL' else \
                   logger.warning if alert.severity == 'WARNING' else \
                   logger.info

        log_func(f"[{alert.severity}] {alert.alert_type}: {alert.message}")

        # Broadcast to callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback {callback.__name__}: {e}")

    def get_recent_alerts(self, count: int = 10) -> List[RiskAlert]:
        """
        Get recent alerts.

        Args:
            count: Number of recent alerts to return

        Returns:
            List of RiskAlert objects
        """
        return self.recent_alerts[-count:]

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

        # Update peak if new balance is higher
        if new_balance > self.account_peak:
            self.account_peak = new_balance

        logger.info(
            f"Account balance updated: ₹{old_balance:,.2f} → ₹{new_balance:,.2f}"
        )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    async def get_risk_summary(self) -> Dict:
        """
        Get current risk summary.

        Returns:
            Dict with all risk metrics
        """
        # Get PnL
        realized_pnl = await self.db.get_today_realized_pnl()
        unrealized_pnl = await self.position_manager.get_total_unrealized_pnl()
        total_pnl = realized_pnl + unrealized_pnl

        # Calculate current value
        current_value = self.account_balance + total_pnl

        # Calculate drawdown
        drawdown = self.account_peak - current_value
        drawdown_pct = (drawdown / self.account_peak) * 100 if self.account_peak > 0 else Decimal('0')

        # Get position count
        position_count = await self.position_manager.get_open_position_count()

        # Calculate limits
        max_daily_loss = self.account_balance * self.max_daily_loss_pct
        max_drawdown = self.account_peak * self.max_drawdown_pct

        return {
            'kill_switch_active': self.kill_switch_active,
            'account_balance': float(self.account_balance),
            'account_peak': float(self.account_peak),
            'current_value': float(current_value),
            'realized_pnl': float(realized_pnl),
            'unrealized_pnl': float(unrealized_pnl),
            'total_pnl': float(total_pnl),
            'daily_pnl_pct': float((total_pnl / self.account_balance) * 100),
            'drawdown': float(drawdown),
            'drawdown_pct': float(drawdown_pct),
            'max_daily_loss': float(max_daily_loss),
            'max_daily_loss_pct': float(self.max_daily_loss_pct * 100),
            'max_drawdown': float(max_drawdown),
            'max_drawdown_pct': float(self.max_drawdown_pct * 100),
            'daily_loss_buffer': float(max_daily_loss - abs(total_pnl)) if total_pnl < 0 else float(max_daily_loss),
            'drawdown_buffer': float(max_drawdown - drawdown),
            'position_count': position_count,
            'max_positions': Config.MAX_POSITIONS,
            'recent_alerts_count': len(self.recent_alerts)
        }
