/**
 * OMS Client - Frontend JavaScript for OMS API Integration
 *
 * Provides:
 * - RESTful API calls to OMS endpoints
 * - WebSocket connection for real-time updates
 * - UI update handlers
 */

class OMSClient {
    constructor(apiBaseUrl = '/api/oms', wsUrl = 'ws://localhost:8050/ws/oms') {
        this.apiBaseUrl = apiBaseUrl;
        this.wsUrl = wsUrl;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;

        // Event handlers
        this.eventHandlers = {
            'order:placed': [],
            'order:filled': [],
            'order:cancelled': [],
            'position:updated': [],
            'position:closed': [],
            'risk:alert': [],
            'risk:kill_switch_triggered': [],
            'risk:kill_switch_deactivated': [],
            'account:balance_updated': []
        };
    }

    // ========================================================================
    // REST API METHODS
    // ========================================================================

    /**
     * Get all open positions
     */
    async getPositions() {
        return await this._fetch('/positions');
    }

    /**
     * Get all active orders
     */
    async getActiveOrders() {
        return await this._fetch('/orders/active');
    }

    /**
     * Place new order
     */
    async placeOrder(orderData) {
        return await this._fetch('/orders', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }

    /**
     * Cancel order
     */
    async cancelOrder(orderId) {
        return await this._fetch(`/orders/${orderId}`, {
            method: 'DELETE'
        });
    }

    /**
     * Modify order
     */
    async modifyOrder(orderId, changes) {
        return await this._fetch(`/orders/${orderId}`, {
            method: 'PUT',
            body: JSON.stringify(changes)
        });
    }

    /**
     * Validate order before placing
     */
    async validateOrder(orderData) {
        return await this._fetch('/validate-order', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }

    /**
     * Get risk summary
     */
    async getRiskSummary() {
        return await this._fetch('/risk/summary');
    }

    /**
     * Get recent risk alerts
     */
    async getRecentAlerts(count = 10) {
        return await this._fetch(`/risk/alerts?count=${count}`);
    }

    /**
     * Deactivate kill switch
     */
    async deactivateKillSwitch(deactivatedBy = 'admin') {
        return await this._fetch('/risk/deactivate-kill-switch', {
            method: 'POST',
            body: JSON.stringify({ deactivated_by: deactivatedBy })
        });
    }

    /**
     * Get today's statistics
     */
    async getTodayStats() {
        return await this._fetch('/stats/today');
    }

    /**
     * Health check
     */
    async healthCheck() {
        return await this._fetch('/health');
    }

    // ========================================================================
    // WEBSOCKET METHODS
    // ========================================================================

    /**
     * Connect to WebSocket
     */
    connectWebSocket() {
        try {
            this.ws = new WebSocket(this.wsUrl);

            this.ws.onopen = () => {
                console.log('✓ WebSocket connected');
                this.reconnectAttempts = 0;

                // Send ping every 30 seconds to keep connection alive
                this.pingInterval = setInterval(() => {
                    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                        this.ws.send(JSON.stringify({ type: 'ping' }));
                    }
                }, 30000);
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleWebSocketMessage(message);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                clearInterval(this.pingInterval);
                this.attemptReconnect();
            };

        } catch (error) {
            console.error('Error connecting WebSocket:', error);
            this.attemptReconnect();
        }
    }

    /**
     * Attempt to reconnect WebSocket
     */
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max WebSocket reconnect attempts reached');
            this.showNotification('error', 'Real-time updates disconnected. Please refresh the page.');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * this.reconnectAttempts;

        console.log(`Reconnecting WebSocket in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
            this.connectWebSocket();
        }, delay);
    }

    /**
     * Handle WebSocket message
     */
    handleWebSocketMessage(message) {
        const { type, data } = message;

        // Trigger registered event handlers
        if (this.eventHandlers[type]) {
            this.eventHandlers[type].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`Error in event handler for ${type}:`, error);
                }
            });
        }
    }

    /**
     * Register event handler
     */
    on(eventType, handler) {
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType].push(handler);
        } else {
            console.warn(`Unknown event type: ${eventType}`);
        }
    }

    /**
     * Disconnect WebSocket
     */
    disconnect() {
        if (this.ws) {
            clearInterval(this.pingInterval);
            this.ws.close();
            this.ws = null;
        }
    }

    // ========================================================================
    // HELPER METHODS
    // ========================================================================

    /**
     * Fetch wrapper with error handling
     */
    async _fetch(endpoint, options = {}) {
        const url = `${this.apiBaseUrl}${endpoint}`;

        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        };

        const mergedOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, mergedOptions);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    /**
     * Show notification (uses toast library if available)
     */
    showNotification(type, message) {
        // If toast library is available (e.g., Toastify)
        if (typeof Toastify !== 'undefined') {
            Toastify({
                text: message,
                duration: type === 'error' ? 5000 : 3000,
                gravity: 'top',
                position: 'right',
                backgroundColor: type === 'success' ? '#10b981' :
                                type === 'error' ? '#ef4444' : '#f59e0b'
            }).showToast();
        } else {
            // Fallback to console
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
}

// ============================================================================
// UI UPDATE HANDLERS
// ============================================================================

/**
 * Update positions table
 */
function updatePositionsTable(positions) {
    const tbody = document.querySelector('#positions-table tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    positions.forEach(position => {
        const row = document.createElement('tr');
        const pnlClass = position.total_pnl > 0 ? 'text-green-500' : 'text-red-500';

        row.innerHTML = `
            <td class="px-4 py-2">${position.symbol}</td>
            <td class="px-4 py-2">${position.quantity}</td>
            <td class="px-4 py-2">₹${position.average_price.toFixed(2)}</td>
            <td class="px-4 py-2 ${pnlClass}">
                ₹${position.unrealized_pnl.toFixed(2)}
            </td>
            <td class="px-4 py-2 ${pnlClass}">
                ₹${position.total_pnl.toFixed(2)}
            </td>
            <td class="px-4 py-2">
                <button
                    class="btn btn-sm btn-danger"
                    onclick="closePosition('${position.symbol}')"
                >
                    Close
                </button>
            </td>
        `;

        tbody.appendChild(row);
    });

    // Update position count
    document.getElementById('position-count').textContent = positions.length;
}

/**
 * Update orders table
 */
function updateOrdersTable(orders) {
    const tbody = document.querySelector('#orders-table tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    orders.forEach(order => {
        const row = document.createElement('tr');
        const sideClass = order.side === 'BUY' ? 'text-green-500' : 'text-red-500';

        row.innerHTML = `
            <td class="px-4 py-2">${order.symbol}</td>
            <td class="px-4 py-2 ${sideClass}">${order.side}</td>
            <td class="px-4 py-2">${order.quantity}</td>
            <td class="px-4 py-2">
                <span class="badge badge-${getStatusBadgeColor(order.status)}">
                    ${order.status}
                </span>
            </td>
            <td class="px-4 py-2">
                <button
                    class="btn btn-sm btn-outline"
                    onclick="cancelOrder(${order.id})"
                >
                    Cancel
                </button>
            </td>
        `;

        tbody.appendChild(row);
    });
}

/**
 * Update risk summary cards
 */
function updateRiskSummary(summary) {
    // Account balance
    if (document.getElementById('account-balance')) {
        document.getElementById('account-balance').textContent =
            `₹${summary.current_value.toLocaleString()}`;
    }

    // Daily P&L
    if (document.getElementById('daily-pnl')) {
        const pnlElement = document.getElementById('daily-pnl');
        pnlElement.textContent = `₹${summary.daily_pnl.toLocaleString()}`;
        pnlElement.className = summary.daily_pnl > 0 ? 'text-green-500' : 'text-red-500';
    }

    // Daily P&L percentage
    if (document.getElementById('daily-pnl-pct')) {
        document.getElementById('daily-pnl-pct').textContent =
            `${summary.daily_pnl_pct.toFixed(2)}%`;
    }

    // Drawdown
    if (document.getElementById('drawdown')) {
        document.getElementById('drawdown').textContent =
            `${summary.drawdown_pct.toFixed(2)}%`;
    }

    // Position count
    if (document.getElementById('position-count-display')) {
        document.getElementById('position-count-display').textContent =
            `${summary.position_count}/${summary.max_positions}`;
    }

    // Kill switch status
    if (document.getElementById('kill-switch-status')) {
        const statusElement = document.getElementById('kill-switch-status');
        if (summary.kill_switch_active) {
            statusElement.innerHTML = '<span class="badge badge-danger">ACTIVE</span>';
            showKillSwitchBanner();
        } else {
            statusElement.innerHTML = '<span class="badge badge-success">INACTIVE</span>';
            hideKillSwitchBanner();
        }
    }
}

/**
 * Show risk alert
 */
function showRiskAlert(alert) {
    const alertsContainer = document.getElementById('risk-alerts-container');
    if (!alertsContainer) return;

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${getSeverityClass(alert.severity)} mb-2`;

    alertDiv.innerHTML = `
        <div class="flex items-start gap-3">
            <span class="text-2xl">${getSeverityIcon(alert.severity)}</span>
            <div class="flex-1">
                <h4 class="font-semibold">${alert.alert_type.replace(/_/g, ' ').toUpperCase()}</h4>
                <p class="text-sm">${alert.message}</p>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="btn-icon">
                ×
            </button>
        </div>
    `;

    alertsContainer.prepend(alertDiv);

    // Auto-dismiss info alerts after 5 seconds
    if (alert.severity === 'INFO') {
        setTimeout(() => alertDiv.remove(), 5000);
    }
}

/**
 * Show kill switch modal
 */
function showKillSwitchModal(reason) {
    // TODO: Implement modal
    alert(`🛑 KILL SWITCH ACTIVATED\n\n${reason}\n\nAll trading has been halted.`);
}

/**
 * Show kill switch banner
 */
function showKillSwitchBanner() {
    let banner = document.getElementById('kill-switch-banner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'kill-switch-banner';
        banner.className = 'bg-red-900/50 p-4 rounded-lg mb-6';
        banner.innerHTML = `
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                    <span class="text-2xl">🛑</span>
                    <div>
                        <h3 class="font-semibold">Kill Switch Active</h3>
                        <p class="text-sm text-gray-400">All trading is currently disabled</p>
                    </div>
                </div>
                <button
                    class="btn btn-danger"
                    onclick="deactivateKillSwitch()"
                >
                    Deactivate
                </button>
            </div>
        `;

        const container = document.querySelector('.dashboard-container');
        if (container) {
            container.prepend(banner);
        }
    }
}

/**
 * Hide kill switch banner
 */
function hideKillSwitchBanner() {
    const banner = document.getElementById('kill-switch-banner');
    if (banner) {
        banner.remove();
    }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function getStatusBadgeColor(status) {
    const colors = {
        'PENDING': 'warning',
        'SUBMITTED': 'info',
        'OPEN': 'primary',
        'FILLED': 'success',
        'CANCELLED': 'secondary',
        'REJECTED': 'danger'
    };
    return colors[status] || 'secondary';
}

function getSeverityClass(severity) {
    const classes = {
        'CRITICAL': 'danger',
        'WARNING': 'warning',
        'INFO': 'info'
    };
    return classes[severity] || 'info';
}

function getSeverityIcon(severity) {
    const icons = {
        'CRITICAL': '🚨',
        'WARNING': '⚠️',
        'INFO': 'ℹ️'
    };
    return icons[severity] || 'ℹ️';
}

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

// Create global OMS client instance
window.omsClient = new OMSClient();

// Connect WebSocket on page load
document.addEventListener('DOMContentLoaded', () => {
    omsClient.connectWebSocket();

    // Register event handlers
    omsClient.on('position:updated', (data) => {
        console.log('Position updated:', data);
        // Refresh positions table
        omsClient.getPositions().then(result => {
            if (result.positions) {
                updatePositionsTable(result.positions);
            }
        });
    });

    omsClient.on('order:filled', (data) => {
        console.log('Order filled:', data);
        omsClient.showNotification('success', `Order filled: ${data.symbol} ${data.side} ${data.quantity}`);
    });

    omsClient.on('risk:alert', (data) => {
        console.log('Risk alert:', data);
        showRiskAlert(data);
    });

    omsClient.on('risk:kill_switch_triggered', (data) => {
        console.log('Kill switch triggered:', data);
        showKillSwitchModal(data.reason);
    });

    // Load initial data
    refreshDashboard();
});

// Disconnect WebSocket on page unload
window.addEventListener('beforeunload', () => {
    omsClient.disconnect();
});

// ============================================================================
// DASHBOARD ACTIONS
// ============================================================================

/**
 * Refresh entire dashboard
 */
async function refreshDashboard() {
    try {
        const [positions, orders, riskSummary, stats] = await Promise.all([
            omsClient.getPositions(),
            omsClient.getActiveOrders(),
            omsClient.getRiskSummary(),
            omsClient.getTodayStats()
        ]);

        if (positions.positions) {
            updatePositionsTable(positions.positions);
        }

        if (orders.orders) {
            updateOrdersTable(orders.orders);
        }

        if (riskSummary) {
            updateRiskSummary(riskSummary);
        }

        // Update stats
        if (stats) {
            if (document.getElementById('order-count')) {
                document.getElementById('order-count').textContent = stats.order_count;
            }
            if (document.getElementById('trade-count')) {
                document.getElementById('trade-count').textContent = stats.trade_count;
            }
        }

    } catch (error) {
        console.error('Error refreshing dashboard:', error);
        omsClient.showNotification('error', 'Failed to refresh dashboard');
    }
}

/**
 * Close position
 */
async function closePosition(symbol) {
    if (!confirm(`Close position for ${symbol}?`)) {
        return;
    }

    try {
        // TODO: Implement close position API call
        omsClient.showNotification('info', `Closing position: ${symbol}...`);

    } catch (error) {
        console.error('Error closing position:', error);
        omsClient.showNotification('error', `Failed to close position: ${error.message}`);
    }
}

/**
 * Cancel order
 */
async function cancelOrder(orderId) {
    if (!confirm('Cancel this order?')) {
        return;
    }

    try {
        await omsClient.cancelOrder(orderId);
        omsClient.showNotification('success', 'Order cancelled');
        refreshDashboard();

    } catch (error) {
        console.error('Error cancelling order:', error);
        omsClient.showNotification('error', `Failed to cancel order: ${error.message}`);
    }
}

/**
 * Deactivate kill switch
 */
async function deactivateKillSwitch() {
    const confirmText = prompt('Type "RESUME TRADING" to deactivate kill switch:');

    if (confirmText !== 'RESUME TRADING') {
        omsClient.showNotification('warning', 'Kill switch deactivation cancelled');
        return;
    }

    try {
        await omsClient.deactivateKillSwitch('admin');
        omsClient.showNotification('success', 'Kill switch deactivated. Trading resumed.');
        refreshDashboard();

    } catch (error) {
        console.error('Error deactivating kill switch:', error);
        omsClient.showNotification('error', `Failed to deactivate kill switch: ${error.message}`);
    }
}

// Auto-refresh dashboard every 5 seconds
setInterval(refreshDashboard, 5000);
