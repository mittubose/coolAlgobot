"""
WebSocket Handler for Real-Time OMS Updates.

Provides real-time push updates to dashboard for:
- Position changes
- Order status updates
- Risk alerts
- Account balance changes
"""

import json
import logging
from typing import Set, Dict, Any
from flask import request
from flask_sock import Sock

from backend.oms import RiskAlert

logger = logging.getLogger(__name__)


class OMSWebSocketHandler:
    """
    WebSocket handler for OMS events.

    Manages WebSocket connections and broadcasts OMS events to connected clients.
    """

    def __init__(self, app):
        """
        Initialize WebSocket handler.

        Args:
            app: Flask app instance
        """
        self.app = app
        self.sock = Sock(app)
        self.clients: Set = set()

        # Register WebSocket route
        self.sock.route('/ws/oms')(self.handle_websocket)

        logger.info("WebSocket handler initialized")

    def handle_websocket(self, ws):
        """
        Handle WebSocket connection.

        Args:
            ws: WebSocket connection
        """
        # Add client to set
        self.clients.add(ws)
        client_id = id(ws)
        logger.info(f"WebSocket client connected: {client_id}")

        try:
            # Send initial connection message
            self.send_to_client(ws, {
                'type': 'connection',
                'status': 'connected',
                'message': 'Connected to OMS WebSocket'
            })

            # Keep connection alive
            while True:
                message = ws.receive()

                if message:
                    # Handle client messages (ping, subscribe, etc.)
                    self.handle_client_message(ws, message)

        except Exception as e:
            logger.error(f"WebSocket error for client {client_id}: {e}")

        finally:
            # Remove client from set
            self.clients.discard(ws)
            logger.info(f"WebSocket client disconnected: {client_id}")

    def handle_client_message(self, ws, message: str):
        """
        Handle message from client.

        Args:
            ws: WebSocket connection
            message: Message from client
        """
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'ping':
                # Respond to ping
                self.send_to_client(ws, {'type': 'pong'})

            elif msg_type == 'subscribe':
                # Subscribe to specific events
                events = data.get('events', [])
                # TODO: Implement event-specific subscriptions
                logger.debug(f"Client subscribed to events: {events}")

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from client: {message}")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")

    def send_to_client(self, ws, data: Dict[str, Any]):
        """
        Send data to specific client.

        Args:
            ws: WebSocket connection
            data: Data to send
        """
        try:
            ws.send(json.dumps(data))
        except Exception as e:
            logger.error(f"Error sending to client: {e}")

    def broadcast(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcast event to all connected clients.

        Args:
            event_type: Event type (e.g., 'order:filled', 'risk:alert')
            data: Event data
        """
        if not self.clients:
            return

        message = json.dumps({
            'type': event_type,
            'data': data
        })

        # Send to all connected clients
        disconnected_clients = set()

        for ws in self.clients:
            try:
                ws.send(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(ws)

        # Remove disconnected clients
        self.clients -= disconnected_clients

    # ========================================================================
    # OMS EVENT HANDLERS
    # ========================================================================

    async def on_order_placed(self, order):
        """
        Handle order placed event.

        Args:
            order: Order object
        """
        self.broadcast('order:placed', {
            'order_id': order.id,
            'broker_order_id': order.broker_order_id,
            'symbol': order.symbol,
            'side': order.side.value,
            'quantity': order.quantity,
            'status': order.status.value
        })

    async def on_order_filled(self, order):
        """
        Handle order filled event.

        Args:
            order: Order object
        """
        self.broadcast('order:filled', {
            'order_id': order.id,
            'broker_order_id': order.broker_order_id,
            'symbol': order.symbol,
            'side': order.side.value,
            'quantity': order.filled_quantity,
            'price': float(order.average_price) if order.average_price else None,
            'status': order.status.value
        })

    async def on_order_cancelled(self, order):
        """
        Handle order cancelled event.

        Args:
            order: Order object
        """
        self.broadcast('order:cancelled', {
            'order_id': order.id,
            'broker_order_id': order.broker_order_id,
            'symbol': order.symbol
        })

    async def on_position_updated(self, position):
        """
        Handle position updated event.

        Args:
            position: Position object
        """
        self.broadcast('position:updated', {
            'symbol': position.symbol,
            'quantity': position.quantity,
            'avg_price': float(position.average_price),
            'unrealized_pnl': float(position.unrealized_pnl),
            'realized_pnl': float(position.realized_pnl),
            'total_pnl': float(position.total_pnl)
        })

    async def on_position_closed(self, position):
        """
        Handle position closed event.

        Args:
            position: Position object
        """
        self.broadcast('position:closed', {
            'symbol': position.symbol,
            'realized_pnl': float(position.realized_pnl)
        })

    async def on_risk_alert(self, alert: RiskAlert):
        """
        Handle risk alert event.

        Args:
            alert: RiskAlert object
        """
        self.broadcast('risk:alert', {
            'severity': alert.severity,
            'alert_type': alert.alert_type,
            'message': alert.message,
            'details': alert.details,
            'timestamp': alert.timestamp.isoformat()
        })

    async def on_kill_switch_triggered(self, reason: str):
        """
        Handle kill switch triggered event.

        Args:
            reason: Reason for kill switch
        """
        self.broadcast('risk:kill_switch_triggered', {
            'reason': reason,
            'timestamp': 'now'
        })

    async def on_kill_switch_deactivated(self):
        """Handle kill switch deactivated event."""
        self.broadcast('risk:kill_switch_deactivated', {
            'timestamp': 'now'
        })

    async def on_account_balance_updated(self, balance: float):
        """
        Handle account balance updated event.

        Args:
            balance: New account balance
        """
        self.broadcast('account:balance_updated', {
            'balance': balance
        })


# ============================================================================
# INTEGRATION WITH RISK MONITOR
# ============================================================================

def setup_websocket_alerts(app, risk_monitor):
    """
    Setup WebSocket alert broadcasting from RiskMonitor.

    Args:
        app: Flask app instance
        risk_monitor: RealTimeRiskMonitor instance
    """
    # Create WebSocket handler
    ws_handler = OMSWebSocketHandler(app)

    # Register alert callback
    risk_monitor.register_alert_callback(ws_handler.on_risk_alert)

    logger.info("WebSocket alerts configured")

    return ws_handler
