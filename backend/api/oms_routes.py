"""
OMS Flask API Routes.

RESTful API endpoints for Order Management System integration with dashboard.
"""

from flask import Blueprint, jsonify, request, current_app
from functools import wraps
from decimal import Decimal
import logging
import asyncio
from typing import Dict, Any

from backend.oms import (
    OrderManager,
    PositionManager,
    PreTradeValidator,
    RealTimeRiskMonitor,
    OrderRejected
)
from backend.models import OrderRequest, OrderSide, OrderType, Product, Validity
from backend.database.database import Database
from backend.config import Config

logger = logging.getLogger(__name__)

# Create Blueprint
oms_bp = Blueprint('oms', __name__, url_prefix='/api/oms')

# Global OMS components (initialized lazily on first request)
_oms_components: Dict[str, Any] = {}
_oms_init_lock = asyncio.Lock()
_oms_initialized = False


async def init_oms_components(db: Database, broker, account_balance: Decimal):
    """
    Initialize OMS components (async).

    Args:
        db: Database instance
        broker: Broker client instance
        account_balance: Current account balance
    """
    global _oms_components, _oms_initialized

    if _oms_initialized:
        return

    async with _oms_init_lock:
        # Double-check after acquiring lock
        if _oms_initialized:
            return

        logger.info("Initializing OMS components...")

        position_manager = PositionManager(db)
        validator = PreTradeValidator(db, account_balance)

        order_manager = OrderManager(
            db=db,
            broker_client=broker,
            position_manager=position_manager,
            validator=validator
        )

        risk_monitor = RealTimeRiskMonitor(
            db=db,
            position_manager=position_manager,
            account_balance=account_balance,
            monitoring_interval=2.0
        )

        # Start background tasks
        await order_manager.start()
        await risk_monitor.start()

        _oms_components = {
            'db': db,
            'order_manager': order_manager,
            'position_manager': position_manager,
            'validator': validator,
            'risk_monitor': risk_monitor,
            'broker': broker
        }

        _oms_initialized = True
        logger.info("✓ OMS components initialized")


def get_oms_component(name: str):
    """Get OMS component by name."""
    if name not in _oms_components:
        raise RuntimeError(f"OMS component '{name}' not initialized. Call init_oms_components() first.")
    return _oms_components[name]


def set_oms_components(components: Dict[str, Any]):
    """
    Set OMS components directly (for external initialization).

    Args:
        components: Dictionary of initialized OMS components
    """
    global _oms_components, _oms_initialized
    _oms_components = components
    _oms_initialized = True
    logger.info("OMS components set externally")


# Flask 3.0+ natively supports async routes, no decorator needed

# ============================================================================
# POSITION ENDPOINTS
# ============================================================================

@oms_bp.route('/positions', methods=['GET'])
async def get_positions():
    """
    Get all open positions.

    Returns:
        {
            "positions": [
                {
                    "id": 1,
                    "symbol": "RELIANCE",
                    "exchange": "NSE",
                    "quantity": 10,
                    "average_price": 2450.50,
                    "current_price": 2460.00,
                    "unrealized_pnl": 95.00,
                    "realized_pnl": 0.00,
                    "total_pnl": 95.00,
                    "stop_loss": 2430.00,
                    "take_profit": 2491.00,
                    "entry_time": "2025-10-25T10:30:00"
                }
            ],
            "count": 1
        }
    """
    try:
        pm = get_oms_component('position_manager')
        positions = await pm.get_all_open_positions()

        positions_data = [
            {
                'id': pos.id,
                'symbol': pos.symbol,
                'exchange': pos.exchange,
                'quantity': pos.quantity,
                'average_price': float(pos.average_price),
                'unrealized_pnl': float(pos.unrealized_pnl),
                'realized_pnl': float(pos.realized_pnl),
                'total_pnl': float(pos.total_pnl),
                'stop_loss': float(pos.stop_loss) if pos.stop_loss else None,
                'take_profit': float(pos.take_profit) if pos.take_profit else None,
                'is_long': pos.is_long,
                'is_short': pos.is_short,
                'entry_time': pos.created_at.isoformat() if pos.created_at else None
            }
            for pos in positions
        ]

        return jsonify({
            'positions': positions_data,
            'count': len(positions_data)
        })

    except Exception as e:
        logger.error(f"Error fetching positions: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@oms_bp.route('/positions/<int:position_id>', methods=['GET'])
async def get_position(position_id: int):
    """Get single position by ID."""
    try:
        db = get_oms_component('db')
        # TODO: Add get_position_by_id method to database
        return jsonify({'error': 'Not implemented'}), 501

    except Exception as e:
        logger.error(f"Error fetching position {position_id}: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ORDER ENDPOINTS
# ============================================================================

@oms_bp.route('/orders', methods=['POST'])
async def place_order():
    """
    Place new order.

    Request Body:
        {
            "symbol": "RELIANCE",
            "exchange": "NSE",
            "side": "BUY",
            "quantity": 10,
            "order_type": "LIMIT",
            "price": 2450.00,
            "stop_loss": 2430.00,
            "take_profit": 2491.00,
            "product": "MIS",
            "validity": "DAY",
            "strategy_id": 1
        }

    Returns:
        {
            "order_id": 123,
            "broker_order_id": "MOCK001001",
            "status": "SUBMITTED",
            "message": "Order placed successfully"
        }
    """
    try:
        data = request.get_json()

        # Create order request
        order_request = OrderRequest(
            symbol=data['symbol'],
            exchange=data.get('exchange', 'NSE'),
            side=OrderSide(data['side'].upper()),
            quantity=int(data['quantity']),
            order_type=OrderType(data.get('order_type', 'LIMIT').upper()),
            price=Decimal(str(data.get('price'))) if data.get('price') else None,
            product=Product(data.get('product', 'MIS').upper()),
            validity=Validity(data.get('validity', 'DAY').upper()),
            strategy_id=int(data.get('strategy_id', 1)),
            stop_loss=Decimal(str(data.get('stop_loss'))) if data.get('stop_loss') else None,
            take_profit=Decimal(str(data.get('take_profit'))) if data.get('take_profit') else None,
            metadata=data.get('metadata', {})
        )

        # Place order via OrderManager
        om = get_oms_component('order_manager')
        result = await om.place_order(order_request)

        return jsonify({
            'order_id': result.order_id,
            'broker_order_id': result.broker_order_id,
            'status': result.status.value,
            'message': 'Order placed successfully'
        }), 201

    except OrderRejected as e:
        logger.warning(f"Order rejected: {e}")
        return jsonify({
            'error': 'Order rejected',
            'reason': str(e),
            'failed_check': e.failed_check if hasattr(e, 'failed_check') else None
        }), 400

    except ValueError as e:
        logger.warning(f"Invalid order data: {e}")
        return jsonify({'error': 'Invalid order data', 'details': str(e)}), 400

    except Exception as e:
        logger.error(f"Error placing order: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@oms_bp.route('/orders/active', methods=['GET'])
async def get_active_orders():
    """
    Get all active orders (PENDING, SUBMITTED, OPEN).

    Returns:
        {
            "orders": [
                {
                    "id": 123,
                    "broker_order_id": "MOCK001001",
                    "symbol": "RELIANCE",
                    "side": "BUY",
                    "quantity": 10,
                    "price": 2450.00,
                    "status": "OPEN",
                    "order_type": "LIMIT",
                    "created_at": "2025-10-25T10:30:00"
                }
            ],
            "count": 1
        }
    """
    try:
        db = get_oms_component('db')
        orders = await db.get_active_orders()

        orders_data = [
            {
                'id': order.id,
                'broker_order_id': order.broker_order_id,
                'symbol': order.symbol,
                'exchange': order.exchange,
                'side': order.side.value,
                'quantity': order.quantity,
                'price': float(order.price) if order.price else None,
                'status': order.status.value,
                'order_type': order.order_type.value,
                'filled_quantity': order.filled_quantity,
                'created_at': order.created_at.isoformat() if order.created_at else None
            }
            for order in orders
        ]

        return jsonify({
            'orders': orders_data,
            'count': len(orders_data)
        })

    except Exception as e:
        logger.error(f"Error fetching active orders: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@oms_bp.route('/orders/<int:order_id>', methods=['DELETE'])
async def cancel_order(order_id: int):
    """
    Cancel order.

    Returns:
        {
            "order_id": 123,
            "message": "Order cancelled successfully"
        }
    """
    try:
        om = get_oms_component('order_manager')
        await om.cancel_order(order_id)

        return jsonify({
            'order_id': order_id,
            'message': 'Order cancelled successfully'
        })

    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@oms_bp.route('/orders/<int:order_id>', methods=['PUT'])
async def modify_order(order_id: int):
    """
    Modify order.

    Request Body:
        {
            "quantity": 15,
            "price": 2455.00
        }

    Returns:
        {
            "order_id": 123,
            "message": "Order modified successfully"
        }
    """
    try:
        data = request.get_json()
        om = get_oms_component('order_manager')

        await om.modify_order(
            order_id=order_id,
            quantity=int(data.get('quantity')) if data.get('quantity') else None,
            price=Decimal(str(data['price'])) if data.get('price') else None
        )

        return jsonify({
            'order_id': order_id,
            'message': 'Order modified successfully'
        })

    except Exception as e:
        logger.error(f"Error modifying order {order_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# VALIDATION ENDPOINT
# ============================================================================

@oms_bp.route('/validate-order', methods=['POST'])
async def validate_order():
    """
    Validate order without placing it.

    Request Body: Same as /orders

    Returns:
        {
            "is_valid": true,
            "reason": "",
            "failed_check": "",
            "warnings": []
        }
    """
    try:
        data = request.get_json()

        # Create order request
        order_request = OrderRequest(
            symbol=data['symbol'],
            exchange=data.get('exchange', 'NSE'),
            side=OrderSide(data['side'].upper()),
            quantity=int(data['quantity']),
            order_type=OrderType(data.get('order_type', 'LIMIT').upper()),
            price=Decimal(str(data.get('price'))) if data.get('price') else None,
            product=Product(data.get('product', 'MIS').upper()),
            validity=Validity(data.get('validity', 'DAY').upper()),
            strategy_id=int(data.get('strategy_id', 1)),
            stop_loss=Decimal(str(data.get('stop_loss'))) if data.get('stop_loss') else None,
            take_profit=Decimal(str(data.get('take_profit'))) if data.get('take_profit') else None
        )

        # Validate
        validator = get_oms_component('validator')
        result = await validator.validate_order(order_request)

        return jsonify({
            'is_valid': result.is_valid,
            'reason': result.reason,
            'failed_check': result.failed_check,
            'warnings': result.warnings
        })

    except Exception as e:
        logger.error(f"Error validating order: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# RISK MANAGEMENT ENDPOINTS
# ============================================================================

@oms_bp.route('/risk/summary', methods=['GET'])
async def get_risk_summary():
    """
    Get risk summary from RealTimeRiskMonitor.

    Returns:
        {
            "kill_switch_active": false,
            "account_balance": 100000.00,
            "current_value": 101234.50,
            "daily_pnl": 1234.50,
            "daily_pnl_pct": 1.23,
            "drawdown": 0.00,
            "drawdown_pct": 0.00,
            "position_count": 2,
            "max_positions": 5,
            "recent_alerts_count": 0
        }
    """
    try:
        monitor = get_oms_component('risk_monitor')
        summary = await monitor.get_risk_summary()

        return jsonify(summary)

    except Exception as e:
        logger.error(f"Error fetching risk summary: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@oms_bp.route('/risk/alerts', methods=['GET'])
def get_recent_alerts():
    """
    Get recent risk alerts.

    Query params:
        count: Number of alerts to return (default: 10)

    Returns:
        {
            "alerts": [
                {
                    "severity": "WARNING",
                    "alert_type": "daily_loss_warning",
                    "message": "Approaching daily loss limit",
                    "details": {},
                    "timestamp": "2025-10-25T10:30:00"
                }
            ]
        }
    """
    try:
        count = int(request.args.get('count', 10))
        monitor = get_oms_component('risk_monitor')
        alerts = monitor.get_recent_alerts(count=count)

        alerts_data = [
            {
                'severity': alert.severity,
                'alert_type': alert.alert_type,
                'message': alert.message,
                'details': alert.details,
                'timestamp': alert.timestamp.isoformat()
            }
            for alert in alerts
        ]

        return jsonify({'alerts': alerts_data})

    except Exception as e:
        logger.error(f"Error fetching alerts: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@oms_bp.route('/risk/deactivate-kill-switch', methods=['POST'])
async def deactivate_kill_switch():
    """
    Deactivate kill switch (admin only).

    Request Body:
        {
            "deactivated_by": "admin_user_123"
        }

    Returns:
        {
            "message": "Kill switch deactivated"
        }
    """
    try:
        data = request.get_json()
        deactivated_by = data.get('deactivated_by', 'admin')

        monitor = get_oms_component('risk_monitor')
        await monitor.deactivate_kill_switch(deactivated_by=deactivated_by)

        return jsonify({'message': 'Kill switch deactivated'})

    except Exception as e:
        logger.error(f"Error deactivating kill switch: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@oms_bp.route('/stats/today', methods=['GET'])
async def get_today_stats():
    """
    Get today's statistics.

    Returns:
        {
            "order_count": 10,
            "trade_count": 8,
            "realized_pnl": 1234.50,
            "position_count": 2
        }
    """
    try:
        db = get_oms_component('db')

        order_count = await db.get_today_order_count()
        trade_count = await db.get_today_trade_count()
        realized_pnl = await db.get_today_realized_pnl()
        pm = get_oms_component('position_manager')
        position_count = await pm.get_open_position_count()

        return jsonify({
            'order_count': order_count,
            'trade_count': trade_count,
            'realized_pnl': float(realized_pnl),
            'position_count': position_count
        })

    except Exception as e:
        logger.error(f"Error fetching today stats: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@oms_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        {
            "status": "healthy",
            "components": {
                "database": true,
                "order_manager": true,
                "risk_monitor": true
            }
        }
    """
    health_status = {
        'status': 'healthy',
        'components': {}
    }

    try:
        # Check if components are initialized
        health_status['components']['database'] = 'db' in _oms_components
        health_status['components']['order_manager'] = 'order_manager' in _oms_components
        health_status['components']['risk_monitor'] = 'risk_monitor' in _oms_components

        # If any component is missing, mark as unhealthy
        if not all(health_status['components'].values()):
            health_status['status'] = 'unhealthy'
            return jsonify(health_status), 503

        return jsonify(health_status)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        health_status['status'] = 'unhealthy'
        health_status['error'] = str(e)
        return jsonify(health_status), 503
