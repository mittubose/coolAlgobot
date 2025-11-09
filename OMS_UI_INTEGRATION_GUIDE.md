# OMS UI Integration Guide

**Date:** October 25, 2025
**Purpose:** Bridge OMS backend implementation with UI/UX design
**Companion to:** ALGO_TRADING_UI_UX.md, OMS_IMPLEMENTATION_COMPLETE.md

---

## 🔗 Connecting OMS Backend to Frontend

### Real-Time Data Flow

```typescript
// WebSocket connection to OMS
interface OMSWebSocketEvents {
  // Order lifecycle events
  'order:placed': (order: Order) => void
  'order:filled': (order: Order) => void
  'order:cancelled': (order: Order) => void
  'order:rejected': (order: Order, reason: string) => void

  // Position updates
  'position:opened': (position: Position) => void
  'position:updated': (position: Position) => void
  'position:closed': (position: Position, pnl: number) => void

  // Risk alerts (from RealTimeRiskMonitor)
  'risk:alert': (alert: RiskAlert) => void
  'risk:kill_switch_triggered': (reason: string) => void
  'risk:kill_switch_deactivated': () => void

  // Account updates
  'account:balance_updated': (balance: number) => void
  'account:pnl_updated': (realized: number, unrealized: number) => void
}
```

### Dashboard Component Integration

```tsx
// Main Trading Dashboard
const TradingDashboard = () => {
  const [positions, setPositions] = useState<Position[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null)
  const [alerts, setAlerts] = useState<RiskAlert[]>([])

  // WebSocket connection
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/oms')

    // Position updates
    ws.on('position:updated', (position) => {
      setPositions(prev =>
        prev.map(p => p.id === position.id ? position : p)
      )

      // Show toast notification for P&L change
      if (position.unrealized_pnl !== 0) {
        const color = position.unrealized_pnl > 0 ? 'success' : 'danger'
        toast[color](
          `${position.symbol}: ₹${position.unrealized_pnl.toFixed(2)}`
        )
      }
    })

    // Risk alerts (from RealTimeRiskMonitor)
    ws.on('risk:alert', (alert: RiskAlert) => {
      setAlerts(prev => [alert, ...prev].slice(0, 10))

      // Show notification based on severity
      if (alert.severity === 'CRITICAL') {
        showModal({
          title: alert.alert_type,
          message: alert.message,
          icon: '🚨',
          buttons: ['Acknowledge']
        })
      } else if (alert.severity === 'WARNING') {
        toast.warning(alert.message)
      } else {
        toast.info(alert.message)
      }
    })

    // Kill switch alert
    ws.on('risk:kill_switch_triggered', (reason) => {
      showFullScreenAlert({
        title: '🛑 TRADING HALTED',
        message: reason,
        actions: [
          {
            label: 'View Risk Summary',
            onClick: () => navigateTo('/risk-summary')
          },
          {
            label: 'Contact Support',
            onClick: () => navigateTo('/support')
          }
        ]
      })
    })

    return () => ws.close()
  }, [])

  // Fetch initial data
  useEffect(() => {
    const loadData = async () => {
      const [posData, orderData, riskData] = await Promise.all([
        fetch('/api/oms/positions').then(r => r.json()),
        fetch('/api/oms/orders/active').then(r => r.json()),
        fetch('/api/oms/risk/summary').then(r => r.json())
      ])

      setPositions(posData)
      setOrders(orderData)
      setRiskSummary(riskData)
    }

    loadData()
  }, [])

  return (
    <div className="dashboard-layout">
      {/* Tier 1: Critical Information */}
      <div className="stats-row grid grid-cols-3 gap-4 mb-6">
        <StatCard
          label="Portfolio Value"
          value={`₹${riskSummary?.current_value.toLocaleString()}`}
          change={riskSummary?.daily_pnl_pct}
          trend={riskSummary?.daily_pnl_pct > 0 ? 'up' : 'down'}
        />

        <StatCard
          label="Today's P&L"
          value={`₹${riskSummary?.total_pnl.toLocaleString()}`}
          subtitle={`${riskSummary?.daily_pnl_pct.toFixed(2)}%`}
          color={riskSummary?.total_pnl > 0 ? 'success' : 'danger'}
        />

        <RiskLevelCard
          level={getRiskLevel(riskSummary)}
          dailyLoss={riskSummary?.daily_pnl_pct}
          maxDailyLoss={-6.0}
          positionCount={riskSummary?.position_count}
          maxPositions={5}
        />
      </div>

      {/* Tier 2: Active Positions & Orders */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <PositionsTable
          positions={positions}
          onClose={(positionId) => handleClosePosition(positionId)}
          onModify={(positionId) => handleModifyPosition(positionId)}
        />

        <OrdersTable
          orders={orders}
          onCancel={(orderId) => handleCancelOrder(orderId)}
          onModify={(orderId) => handleModifyOrder(orderId)}
        />
      </div>

      {/* Alerts Panel */}
      <AlertsPanel
        alerts={alerts}
        killSwitchActive={riskSummary?.kill_switch_active}
        onDeactivateKillSwitch={() => handleDeactivateKillSwitch()}
      />
    </div>
  )
}
```

---

## 🎯 Order Placement Flow with PreTradeValidator

```tsx
// Order Form with Real-Time Validation
const OrderForm = ({ symbol }: { symbol: string }) => {
  const [orderData, setOrderData] = useState<OrderRequest>({
    symbol,
    exchange: 'NSE',
    side: 'BUY',
    quantity: 0,
    order_type: 'LIMIT',
    price: null,
    stop_loss: null,
    take_profit: null,
    product: 'MIS',
    validity: 'DAY',
    strategy_id: 1
  })

  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)
  const [isValidating, setIsValidating] = useState(false)

  // Real-time validation (client-side basic checks)
  useEffect(() => {
    const validateOrder = async () => {
      if (!orderData.quantity || !orderData.price) return

      setIsValidating(true)

      try {
        // Call OMS PreTradeValidator endpoint
        const result = await fetch('/api/oms/validate-order', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(orderData)
        }).then(r => r.json())

        setValidationResult(result)

      } catch (error) {
        console.error('Validation error:', error)
      } finally {
        setIsValidating(false)
      }
    }

    // Debounce validation (500ms)
    const timer = setTimeout(validateOrder, 500)
    return () => clearTimeout(timer)
  }, [orderData])

  const handleSubmit = async () => {
    // Final validation
    if (!validationResult?.is_valid) {
      toast.error(`Order validation failed: ${validationResult?.reason}`)
      return
    }

    try {
      // Place order via OrderManager
      const result = await fetch('/api/oms/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(orderData)
      }).then(r => r.json())

      toast.success(`Order placed: ${result.broker_order_id}`)

      // Show order confirmation with details
      showConfirmation({
        title: 'Order Placed',
        details: {
          'Symbol': orderData.symbol,
          'Side': orderData.side,
          'Quantity': orderData.quantity,
          'Price': `₹${orderData.price}`,
          'Stop-Loss': `₹${orderData.stop_loss}`,
          'Take-Profit': `₹${orderData.take_profit}`,
          'Risk-Reward': calculateRR(orderData),
          'Order ID': result.broker_order_id
        }
      })

    } catch (error) {
      // Handle OMS errors (from OrderManager)
      if (error.status === 400 && error.code === 'ORDER_REJECTED') {
        showErrorModal({
          title: 'Order Rejected',
          message: error.message,
          failedCheck: error.failed_check,
          suggestions: getOrderSuggestions(error.failed_check)
        })
      }
    }
  }

  return (
    <form className="order-form glass-card p-6">
      <h3 className="text-xl font-bold mb-4">Place Order: {symbol}</h3>

      {/* Order Type Selector */}
      <div className="mb-4">
        <label>Order Side</label>
        <div className="btn-group">
          <button
            type="button"
            className={`btn ${orderData.side === 'BUY' ? 'btn-success' : 'btn-outline'}`}
            onClick={() => setOrderData({ ...orderData, side: 'BUY' })}
          >
            BUY
          </button>
          <button
            type="button"
            className={`btn ${orderData.side === 'SELL' ? 'btn-danger' : 'btn-outline'}`}
            onClick={() => setOrderData({ ...orderData, side: 'SELL' })}
          >
            SELL
          </button>
        </div>
      </div>

      {/* Quantity */}
      <div className="mb-4">
        <label>Quantity</label>
        <input
          type="number"
          value={orderData.quantity}
          onChange={(e) => setOrderData({ ...orderData, quantity: parseInt(e.target.value) })}
          className="input"
          min="1"
          max="10000"
        />
      </div>

      {/* Price */}
      <div className="mb-4">
        <label>Price (₹)</label>
        <input
          type="number"
          value={orderData.price || ''}
          onChange={(e) => setOrderData({ ...orderData, price: parseFloat(e.target.value) })}
          className="input"
          step="0.05"
        />
      </div>

      {/* Stop-Loss (Required) */}
      <div className="mb-4">
        <label className="flex items-center">
          Stop-Loss (₹)
          <span className="badge badge-danger ml-2">Required</span>
        </label>
        <input
          type="number"
          value={orderData.stop_loss || ''}
          onChange={(e) => setOrderData({ ...orderData, stop_loss: parseFloat(e.target.value) })}
          className="input"
          step="0.05"
          required
        />
      </div>

      {/* Take-Profit */}
      <div className="mb-4">
        <label>Take-Profit (₹)</label>
        <input
          type="number"
          value={orderData.take_profit || ''}
          onChange={(e) => setOrderData({ ...orderData, take_profit: parseFloat(e.target.value) })}
          className="input"
          step="0.05"
        />
      </div>

      {/* Real-Time Validation Feedback */}
      {isValidating && (
        <div className="validation-status mb-4">
          <Spinner size="sm" />
          <span className="ml-2">Validating order...</span>
        </div>
      )}

      {validationResult && !isValidating && (
        <div className={`validation-result mb-4 p-3 rounded ${
          validationResult.is_valid ? 'bg-green-900/20' : 'bg-red-900/20'
        }`}>
          {validationResult.is_valid ? (
            <div className="flex items-center text-green-400">
              <CheckCircle className="w-5 h-5 mr-2" />
              <span>Order validation passed</span>
            </div>
          ) : (
            <div className="text-red-400">
              <div className="flex items-center mb-2">
                <XCircle className="w-5 h-5 mr-2" />
                <span className="font-semibold">Validation Failed</span>
              </div>
              <p className="text-sm mb-1">
                <strong>Check:</strong> {validationResult.failed_check}
              </p>
              <p className="text-sm">
                <strong>Reason:</strong> {validationResult.reason}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Order Summary */}
      <div className="order-summary glass-card p-4 mb-4">
        <h4 className="font-semibold mb-2">Order Summary</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <p className="text-gray-400">Risk per share</p>
            <p className="font-semibold">
              ₹{orderData.price && orderData.stop_loss
                ? Math.abs(orderData.price - orderData.stop_loss).toFixed(2)
                : '—'}
            </p>
          </div>
          <div>
            <p className="text-gray-400">Total risk</p>
            <p className="font-semibold text-red-400">
              ₹{orderData.price && orderData.stop_loss && orderData.quantity
                ? (Math.abs(orderData.price - orderData.stop_loss) * orderData.quantity).toFixed(2)
                : '—'}
            </p>
          </div>
          <div>
            <p className="text-gray-400">Risk-Reward</p>
            <p className="font-semibold">
              {calculateRR(orderData)}:1
            </p>
          </div>
          <div>
            <p className="text-gray-400">Risk %</p>
            <p className="font-semibold">
              {calculateRiskPercent(orderData)}%
            </p>
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={!validationResult?.is_valid || isValidating}
        className="btn btn-primary w-full"
      >
        {isValidating ? 'Validating...' : 'Place Order'}
      </button>
    </form>
  )
}

// Helper functions
function calculateRR(order: OrderRequest): string {
  if (!order.price || !order.stop_loss || !order.take_profit) return '—'

  const risk = Math.abs(order.price - order.stop_loss)
  const reward = Math.abs(order.take_profit - order.price)

  return (reward / risk).toFixed(2)
}

function calculateRiskPercent(order: OrderRequest): string {
  // Assuming account balance of ₹100,000 (fetch from API)
  const accountBalance = 100000

  if (!order.price || !order.stop_loss || !order.quantity) return '—'

  const risk = Math.abs(order.price - order.stop_loss) * order.quantity
  const riskPct = (risk / accountBalance) * 100

  return riskPct.toFixed(2)
}

function getOrderSuggestions(failedCheck: string): string[] {
  const suggestions = {
    'risk_per_trade': [
      'Reduce order quantity',
      'Widen stop-loss (increases risk, not recommended)',
      'Choose a different symbol with lower volatility'
    ],
    'stop_loss_required': [
      'Set a stop-loss at least 2% below entry price',
      'Use ATR-based stop-loss calculator',
      'Review recent support levels for stop placement'
    ],
    'risk_reward_ratio': [
      'Increase take-profit target (min 2:1 required)',
      'Tighten stop-loss (reduces risk)',
      'Wait for better entry price'
    ],
    'balance_check': [
      'Reduce order quantity',
      'Close existing positions to free up margin',
      'Add funds to trading account'
    ],
    'position_limit': [
      'Close one existing position first',
      'Wait for existing position to hit target',
      'Combine similar positions'
    ]
  }

  return suggestions[failedCheck] || ['Review order parameters and try again']
}
```

---

## 🔔 Alert UI Components

### Risk Alert Toast
```tsx
const RiskAlertToast = ({ alert }: { alert: RiskAlert }) => {
  const icons = {
    'CRITICAL': '🚨',
    'WARNING': '⚠️',
    'INFO': 'ℹ️'
  }

  const colors = {
    'CRITICAL': 'bg-red-900/90',
    'WARNING': 'bg-yellow-900/90',
    'INFO': 'bg-blue-900/90'
  }

  return (
    <div className={`${colors[alert.severity]} p-4 rounded-lg shadow-lg max-w-md`}>
      <div className="flex items-start gap-3">
        <span className="text-2xl">{icons[alert.severity]}</span>

        <div className="flex-1">
          <h4 className="font-semibold text-white mb-1">
            {alert.severity}: {alert.alert_type.replace(/_/g, ' ').toUpperCase()}
          </h4>
          <p className="text-sm text-gray-200">
            {alert.message}
          </p>

          {alert.details && Object.keys(alert.details).length > 0 && (
            <div className="mt-2 text-xs text-gray-300">
              {Object.entries(alert.details).map(([key, value]) => (
                <div key={key}>
                  <strong>{key}:</strong> {value}
                </div>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={() => dismissAlert(alert)}
          className="text-gray-400 hover:text-white"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
```

### Kill Switch Modal
```tsx
const KillSwitchModal = ({ reason, onDeactivate }: KillSwitchModalProps) => {
  const [confirmText, setConfirmText] = useState('')
  const [loading, setLoading] = useState(false)

  const handleDeactivate = async () => {
    if (confirmText !== 'RESUME TRADING') {
      toast.error('Please type "RESUME TRADING" to confirm')
      return
    }

    setLoading(true)

    try {
      await fetch('/api/oms/risk/deactivate-kill-switch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ deactivated_by: 'user_123' })
      })

      toast.success('Kill switch deactivated. Trading resumed.')
      onDeactivate()

    } catch (error) {
      toast.error('Failed to deactivate kill switch')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal size="lg" className="kill-switch-modal">
      <div className="text-center p-6">
        <div className="text-6xl mb-4">🛑</div>
        <h2 className="text-2xl font-bold text-red-500 mb-2">
          TRADING HALTED
        </h2>
        <p className="text-gray-400 mb-6">
          {reason}
        </p>

        <div className="bg-gray-900 p-4 rounded-lg mb-6">
          <h3 className="font-semibold mb-2">Before resuming, ensure:</h3>
          <ul className="text-sm text-left space-y-2">
            <li>✓ You've reviewed all open positions</li>
            <li>✓ Risk limits have been adjusted if needed</li>
            <li>✓ You understand why the kill switch was triggered</li>
            <li>✓ Market conditions are favorable</li>
          </ul>
        </div>

        <div className="mb-6">
          <label className="block text-sm mb-2">
            Type <strong>"RESUME TRADING"</strong> to deactivate kill switch
          </label>
          <input
            type="text"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            className="input w-full text-center"
            placeholder="RESUME TRADING"
          />
        </div>

        <div className="flex gap-4">
          <button
            onClick={() => window.location.href = '/risk-summary'}
            className="btn btn-outline flex-1"
          >
            View Risk Summary
          </button>
          <button
            onClick={handleDeactivate}
            disabled={confirmText !== 'RESUME TRADING' || loading}
            className="btn btn-danger flex-1"
          >
            {loading ? 'Deactivating...' : 'Deactivate Kill Switch'}
          </button>
        </div>
      </div>
    </Modal>
  )
}
```

---

## 📊 Risk Dashboard Component

```tsx
const RiskDashboard = () => {
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null)

  useEffect(() => {
    const loadRiskSummary = async () => {
      const data = await fetch('/api/oms/risk/summary').then(r => r.json())
      setRiskSummary(data)
    }

    loadRiskSummary()

    // Refresh every 2 seconds (matches RealTimeRiskMonitor interval)
    const interval = setInterval(loadRiskSummary, 2000)
    return () => clearInterval(interval)
  }, [])

  if (!riskSummary) return <LoadingSpinner />

  return (
    <div className="risk-dashboard">
      <h2 className="text-2xl font-bold mb-6">Risk Management</h2>

      {/* Kill Switch Status */}
      {riskSummary.kill_switch_active && (
        <div className="kill-switch-banner bg-red-900/50 p-4 rounded-lg mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertOctagon className="w-6 h-6 text-red-500" />
              <div>
                <h3 className="font-semibold">Kill Switch Active</h3>
                <p className="text-sm text-gray-400">
                  All trading is currently disabled
                </p>
              </div>
            </div>
            <button className="btn btn-danger">
              Deactivate
            </button>
          </div>
        </div>
      )}

      {/* Risk Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {/* Daily P&L */}
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400 mb-1">Daily P&L</p>
          <p className={`text-2xl font-bold ${
            riskSummary.total_pnl > 0 ? 'text-green-500' : 'text-red-500'
          }`}>
            ₹{riskSummary.total_pnl.toLocaleString()}
          </p>
          <p className="text-sm text-gray-400">
            {riskSummary.daily_pnl_pct.toFixed(2)}%
          </p>

          {/* Progress bar showing proximity to limit */}
          <div className="mt-2">
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  Math.abs(riskSummary.daily_pnl_pct) > 4 ? 'bg-red-500' : 'bg-yellow-500'
                }`}
                style={{
                  width: `${Math.min((Math.abs(riskSummary.daily_pnl_pct) / 6) * 100, 100)}%`
                }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Limit: -6% (Buffer: ₹{riskSummary.daily_loss_buffer.toLocaleString()})
            </p>
          </div>
        </div>

        {/* Drawdown */}
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400 mb-1">Drawdown</p>
          <p className="text-2xl font-bold text-yellow-500">
            {riskSummary.drawdown_pct.toFixed(2)}%
          </p>
          <p className="text-sm text-gray-400">
            ₹{riskSummary.drawdown.toLocaleString()}
          </p>

          <div className="mt-2">
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className={`h-full ${
                  riskSummary.drawdown_pct > 10 ? 'bg-red-500' : 'bg-yellow-500'
                }`}
                style={{
                  width: `${Math.min((riskSummary.drawdown_pct / 15) * 100, 100)}%`
                }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Limit: 15% (Buffer: ₹{riskSummary.drawdown_buffer.toLocaleString()})
            </p>
          </div>
        </div>

        {/* Position Count */}
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400 mb-1">Open Positions</p>
          <p className="text-2xl font-bold">
            {riskSummary.position_count}/{riskSummary.max_positions}
          </p>

          <div className="mt-2">
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500"
                style={{
                  width: `${(riskSummary.position_count / riskSummary.max_positions) * 100}%`
                }}
              />
            </div>
          </div>
        </div>

        {/* Account Value */}
        <div className="glass-card p-4">
          <p className="text-sm text-gray-400 mb-1">Account Value</p>
          <p className="text-2xl font-bold">
            ₹{riskSummary.current_value.toLocaleString()}
          </p>
          <p className="text-sm text-gray-400">
            Peak: ₹{riskSummary.account_peak.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-semibold mb-4">Recent Alerts</h3>
        {riskSummary.recent_alerts_count === 0 ? (
          <p className="text-gray-500">No recent alerts</p>
        ) : (
          <div className="space-y-2">
            {/* Fetch and display recent alerts */}
            <p className="text-sm text-gray-400">
              {riskSummary.recent_alerts_count} alerts in last hour
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
```

---

## ✅ Integration Checklist

### Backend API Endpoints Needed

- [ ] `GET /api/oms/positions` - Get all open positions
- [ ] `GET /api/oms/orders/active` - Get active orders
- [ ] `POST /api/oms/orders` - Place new order
- [ ] `DELETE /api/oms/orders/:id` - Cancel order
- [ ] `PUT /api/oms/orders/:id` - Modify order
- [ ] `POST /api/oms/validate-order` - Validate order (PreTradeValidator)
- [ ] `GET /api/oms/risk/summary` - Get risk summary (RealTimeRiskMonitor)
- [ ] `POST /api/oms/risk/deactivate-kill-switch` - Deactivate kill switch
- [ ] `WebSocket /oms` - Real-time updates

### Frontend Components to Build

- [ ] `<TradingDashboard />` - Main dashboard
- [ ] `<OrderForm />` - Order placement with validation
- [ ] `<PositionsTable />` - Active positions
- [ ] `<OrdersTable />` - Active orders
- [ ] `<RiskDashboard />` - Risk metrics
- [ ] `<RiskAlertToast />` - Alert notifications
- [ ] `<KillSwitchModal />` - Kill switch UI
- [ ] `<StatCard />` - Metric cards
- [ ] `<RiskLevelCard />` - Risk level indicator

### State Management

- [ ] Setup Zustand store for OMS state
- [ ] WebSocket connection management
- [ ] Real-time data synchronization
- [ ] Optimistic UI updates

---

*Last updated: October 25, 2025*
*Bridges: OMS backend ↔ Trading UI*
