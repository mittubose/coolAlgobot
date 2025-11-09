"""
Dashboard Integration for OMS.

Integrates OrderManager, RealTimeRiskMonitor with existing Flask dashboard.
"""

import asyncio
import logging
from decimal import Decimal
from typing import Optional

from backend.database.database import Database
from backend.api.oms_routes import oms_bp, set_oms_components
from backend.oms import OrderManager, PositionManager, PreTradeValidator, RealTimeRiskMonitor
from backend.config import Config
from tests.mocks.mock_broker import MockBrokerClient

logger = logging.getLogger(__name__)


class OMSDashboardIntegration:
    """
    Integration layer between OMS and Flask dashboard.

    Handles:
    - OMS initialization
    - Background task management (OrderManager, RiskMonitor)
    - Data synchronization with dashboard state
    """

    def __init__(self, app, use_mock_broker: bool = True):
        """
        Initialize OMS integration.

        Args:
            app: Flask app instance
            use_mock_broker: Use MockBrokerClient for testing (default: True)
        """
        self.app = app
        self.use_mock_broker = use_mock_broker

        self.db: Optional[Database] = None
        self.broker = None
        self.order_manager = None
        self.risk_monitor = None
        self._initialized = False

    def register_blueprint(self):
        """
        Register OMS blueprint with Flask app (synchronous).

        Call this BEFORE async initialization to ensure routes are available.
        """
        self.app.register_blueprint(oms_bp)
        logger.info("✓ OMS API routes registered at /api/oms")

    async def initialize(self):
        """
        Initialize OMS components.

        Should be called during Flask app startup.
        """
        if self._initialized:
            logger.warning("OMS already initialized")
            return

        logger.info("Initializing OMS for dashboard...")

        try:
            # 1. Initialize database
            self.db = Database(Config.DATABASE_URL)
            await self.db.connect()
            logger.info("✓ Database connected")

            # 2. Initialize broker
            if self.use_mock_broker:
                self.broker = MockBrokerClient(
                    fill_delay=0.5,
                    fill_probability=0.95
                )
                logger.info("✓ Mock broker initialized")
            else:
                # TODO: Initialize real Zerodha client
                from kiteconnect import KiteConnect
                self.broker = KiteConnect(api_key=Config.ZERODHA_API_KEY)
                logger.info("✓ Real Zerodha broker initialized")

            # 3. Initialize OMS components
            account_balance = Decimal('100000')  # TODO: Fetch from broker

            position_manager = PositionManager(self.db)
            validator = PreTradeValidator(self.db, account_balance)

            self.order_manager = OrderManager(
                db=self.db,
                broker_client=self.broker,
                position_manager=position_manager,
                validator=validator
            )

            self.risk_monitor = RealTimeRiskMonitor(
                db=self.db,
                position_manager=position_manager,
                account_balance=account_balance,
                monitoring_interval=2.0
            )

            # 4. Start background tasks
            await self.order_manager.start()
            await self.risk_monitor.start()
            logger.info("✓ Background tasks started")

            # 5. Set OMS components for route handlers
            set_oms_components({
                'db': self.db,
                'order_manager': self.order_manager,
                'position_manager': position_manager,
                'validator': validator,
                'risk_monitor': self.risk_monitor,
                'broker': self.broker
            })
            logger.info("✓ OMS components initialized")

            self._initialized = True
            logger.info("🎉 OMS initialization complete!")

        except Exception as e:
            logger.error(f"❌ OMS initialization failed: {e}", exc_info=True)
            raise

    async def shutdown(self):
        """
        Shutdown OMS components.

        Should be called during Flask app shutdown.
        """
        if not self._initialized:
            return

        logger.info("Shutting down OMS...")

        try:
            # Stop background tasks
            if self.risk_monitor:
                await self.risk_monitor.stop()
                logger.info("✓ Risk monitor stopped")

            if self.order_manager:
                await self.order_manager.stop()
                logger.info("✓ Order manager stopped")

            # Disconnect database
            if self.db:
                await self.db.disconnect()
                logger.info("✓ Database disconnected")

            self._initialized = False
            logger.info("✓ OMS shutdown complete")

        except Exception as e:
            logger.error(f"Error during OMS shutdown: {e}", exc_info=True)

    def get_dashboard_data(self) -> dict:
        """
        Get data for dashboard UI (synchronous).

        Returns:
            Dictionary with current OMS state
        """
        if not self._initialized:
            return {
                'initialized': False,
                'error': 'OMS not initialized'
            }

        try:
            # Create async task to fetch data
            loop = asyncio.get_event_loop()
            data = loop.run_until_complete(self._fetch_dashboard_data())
            return data

        except Exception as e:
            logger.error(f"Error fetching dashboard data: {e}")
            return {
                'initialized': True,
                'error': str(e)
            }

    async def _fetch_dashboard_data(self) -> dict:
        """
        Fetch dashboard data asynchronously.

        Returns:
            Dictionary with positions, orders, risk summary, stats
        """
        from backend.api.oms_routes import get_oms_component

        pm = get_oms_component('position_manager')
        db = get_oms_component('db')

        # Fetch all data in parallel
        positions = await pm.get_all_open_positions()
        active_orders = await db.get_active_orders()
        risk_summary = await self.risk_monitor.get_risk_summary()
        order_count = await db.get_today_order_count()
        trade_count = await db.get_today_trade_count()

        # Format positions
        positions_data = [
            {
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'avg_price': float(pos.average_price),
                'unrealized_pnl': float(pos.unrealized_pnl),
                'realized_pnl': float(pos.realized_pnl),
                'total_pnl': float(pos.total_pnl)
            }
            for pos in positions
        ]

        # Format orders
        orders_data = [
            {
                'symbol': order.symbol,
                'side': order.side.value,
                'quantity': order.quantity,
                'status': order.status.value
            }
            for order in active_orders
        ]

        return {
            'initialized': True,
            'positions': positions_data,
            'orders': orders_data,
            'risk_summary': risk_summary,
            'stats': {
                'order_count': order_count,
                'trade_count': trade_count,
                'position_count': len(positions_data)
            }
        }


# ============================================================================
# FLASK APP INITIALIZATION HELPER
# ============================================================================

def integrate_oms_with_flask(app, use_mock_broker: bool = True):
    """
    Integrate OMS with Flask app.

    Usage in app.py:
        from backend.api.dashboard_integration import integrate_oms_with_flask

        app = Flask(__name__)
        oms_integration = integrate_oms_with_flask(app)

        # On app startup (before first request)
        @app.before_first_request
        def startup():
            asyncio.run(oms_integration.initialize())

        # On app shutdown
        import atexit
        atexit.register(lambda: asyncio.run(oms_integration.shutdown()))

    Args:
        app: Flask app instance
        use_mock_broker: Use mock broker for testing (default: True)

    Returns:
        OMSDashboardIntegration instance
    """
    integration = OMSDashboardIntegration(app, use_mock_broker=use_mock_broker)

    # Register blueprint synchronously FIRST (before async init)
    integration.register_blueprint()

    # Add to app context
    app.oms_integration = integration

    logger.info("OMS integration layer created")
    return integration
