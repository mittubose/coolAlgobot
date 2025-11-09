# Top Bar & Portfolio Review Page Implementation Plan

**Date:** October 26, 2025
**Status:** 🚧 PLANNING

---

## 📋 Requirements

1. **Create a consistent top bar** across all dashboard pages
2. **Update portfolio.html** to include an "Import CSV" button that links to `/portfolio-import`
3. **Fix broken top bars** in all existing pages
4. **Create a comprehensive portfolio review section** showing all trade accounts and stats

---

## 🎯 Top Bar Design Specification

### **Standard Top Bar Components:**

```html
<div class="topbar">
    <!-- Logo / Brand -->
    <div class="topbar-brand">
        <i data-lucide="trending-up"></i>
        <span>Scalping Bot</span>
    </div>

    <!-- Navigation -->
    <nav class="topbar-nav">
        <a href="/" class="nav-link">Dashboard</a>
        <a href="/portfolio" class="nav-link">Portfolio</a>
        <a href="/strategies" class="nav-link">Strategies</a>
        <a href="/analytics" class="nav-link">Analytics</a>
    </nav>

    <!-- Actions -->
    <div class="topbar-actions">
        <!-- Account Selector -->
        <select id="account-selector" class="topbar-select">
            <option>Zerodha Main</option>
            <option>Groww Main</option>
        </select>

        <!-- Funds Display -->
        <div class="topbar-funds">
            <span class="funds-label">Available</span>
            <span class="funds-value">₹1,25,000</span>
        </div>

        <!-- Status Indicator -->
        <div class="topbar-status">
            <span class="status-dot status-active"></span>
            <span>Active</span>
        </div>

        <!-- User Menu -->
        <button class="topbar-user">
            <i data-lucide="user"></i>
        </button>
    </div>
</div>
```

### **CSS Specifications:**

```css
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 24px;
    background: var(--color-bg-secondary);
    border-bottom: 1px solid var(--color-border);
    margin-bottom: 24px;
    height: 60px;
}

.topbar-brand {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 1.1rem;
}

.topbar-nav {
    display: flex;
    gap: 4px;
}

.nav-link {
    padding: 8px 16px;
    text-decoration: none;
    color: var(--color-text-secondary);
    border-radius: 6px;
    transition: all 0.2s;
}

.nav-link:hover,
.nav-link.active {
    background: rgba(0, 201, 167, 0.1);
    color: var(--color-accent-primary);
}

.topbar-actions {
    display: flex;
    align-items: center;
    gap: 16px;
}

.topbar-select {
    padding: 6px 12px;
    background: var(--color-bg-tertiary);
    border: 1px solid var(--color-border);
    border-radius: 6px;
    color: var(--color-text-primary);
    font-size: 0.875rem;
}

.topbar-funds {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}

.funds-label {
    font-size: 0.7rem;
    color: var(--color-text-secondary);
}

.funds-value {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--color-success);
}

.topbar-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.875rem;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.status-active { background: var(--color-success); }
.status-paused { background: var(--color-warning); }
.status-stopped { background: var(--color-error); }

.topbar-user {
    width: 36px;
    height: 36px;
    background: var(--color-bg-tertiary);
    border: none;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: var(--color-text-primary);
}
```

---

## 📄 Files to Update

### **1. Create Shared Component (New)**

**File:** `src/dashboard/templates/components/topbar.html`

This will be a reusable HTML snippet that can be embedded in all pages.

---

### **2. Update portfolio.html**

**Changes:**
1. Add standard top bar at the top
2. Add "Import CSV" button in header section
3. Enhance portfolio stats display
4. Add portfolio selector dropdown
5. Add recent trades section

**Location:** `/portfolio` route

---

### **3. Update All Dashboard Pages**

**Pages to Fix:**
- `dashboard.html` - Main dashboard
- `strategies.html` - Strategy management
- `analytics.html` - Analytics & reports
- `accounts.html` - Account management
- `settings.html` - Settings page
- `notifications.html` - Notifications
- `help.html` - Help & documentation
- `history.html` - Trade history
- `profile.html` - User profile

**For Each Page:**
1. Replace existing top bar (if any) with standard top bar
2. Ensure navigation links are present
3. Mark current page as active in navigation
4. Maintain consistent spacing and layout

---

## 🎨 Portfolio Page Enhanced Design

### **Updated Header Section:**

```html
<div class="topbar">
    <!-- Standard top bar here -->
</div>

<div class="container">
    <div class="page-header">
        <div>
            <h1>Portfolio Overview</h1>
            <p class="subtitle">Track your holdings, P&L, and trading performance</p>
        </div>
        <div class="header-actions">
            <button class="btn btn-secondary" onclick="window.location.href='/portfolio-import'">
                <i data-lucide="upload"></i>
                Import CSV/Excel
            </button>
            <button class="btn btn-primary" onclick="calculatePNL()">
                <i data-lucide="refresh-cw"></i>
                Calculate P&L
            </button>
        </div>
    </div>

    <!-- Portfolio Selector -->
    <div class="portfolio-selector">
        <label>Select Portfolio:</label>
        <select id="portfolio-select" onchange="loadPortfolioData()">
            <option value="1">Zerodha Main</option>
            <option value="2">Groww Main</option>
        </select>
    </div>

    <!-- Rest of portfolio content -->
</div>
```

### **Portfolio Stats Grid:**

```html
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-label">Total Value</div>
        <div class="stat-value">₹1,25,000</div>
        <div class="stat-change positive">
            <i data-lucide="trending-up"></i>
            <span>+₹25,000 (25.0%)</span>
        </div>
    </div>

    <div class="stat-card">
        <div class="stat-label">Realized P&L</div>
        <div class="stat-value positive">+₹12,500</div>
        <div class="stat-change positive">
            <span>15 closed trades</span>
        </div>
    </div>

    <div class="stat-card">
        <div class="stat-label">Unrealized P&L</div>
        <div class="stat-value positive">+₹3,200</div>
        <div class="stat-change">
            <span>5 open positions</span>
        </div>
    </div>

    <div class="stat-card">
        <div class="stat-label">Win Rate</div>
        <div class="stat-value">68.5%</div>
        <div class="stat-change">
            <span>12 wins / 3 losses</span>
        </div>
    </div>
</div>
```

### **Holdings Table:**

```html
<div class="section">
    <div class="section-header">
        <h2>Current Holdings</h2>
        <span class="badge">5 positions</span>
    </div>

    <table class="data-table">
        <thead>
            <tr>
                <th>Symbol</th>
                <th>Quantity</th>
                <th>Avg. Price</th>
                <th>Current Price</th>
                <th>P&L</th>
                <th>P&L %</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody id="holdings-table">
            <!-- Populated via JavaScript -->
        </tbody>
    </table>
</div>
```

### **Recent Trades:**

```html
<div class="section">
    <div class="section-header">
        <h2>Recent Trades</h2>
        <a href="/history" class="link">View All</a>
    </div>

    <table class="data-table">
        <thead>
            <tr>
                <th>Date/Time</th>
                <th>Symbol</th>
                <th>Type</th>
                <th>Quantity</th>
                <th>Price</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody id="trades-table">
            <!-- Populated via JavaScript -->
        </tbody>
    </table>
</div>
```

---

## 📊 JavaScript Integration

### **Portfolio Data Loading:**

```javascript
async function loadPortfolioData() {
    const portfolioId = document.getElementById('portfolio-select').value;

    try {
        // Fetch portfolio summary
        const response = await fetch(`/api/portfolios/${portfolioId}`);
        const data = await response.json();

        if (data.success) {
            updateStats(data.portfolio);
            updateHoldings(data.holdings);
            updateRecentTrades(data.recent_trades);
        }
    } catch (error) {
        console.error('Error loading portfolio:', error);
    }
}

function updateStats(portfolio) {
    document.querySelector('[data-stat="total-value"]').textContent =
        formatCurrency(portfolio.current_value);
    document.querySelector('[data-stat="realized-pnl"]').textContent =
        formatCurrency(portfolio.realized_pnl);
    document.querySelector('[data-stat="unrealized-pnl"]').textContent =
        formatCurrency(portfolio.unrealized_pnl);
    document.querySelector('[data-stat="win-rate"]').textContent =
        `${portfolio.win_rate}%`;
}

function updateHoldings(holdings) {
    const tbody = document.getElementById('holdings-table');
    tbody.innerHTML = holdings.map(h => `
        <tr>
            <td><strong>${h.symbol}</strong></td>
            <td>${h.quantity}</td>
            <td>₹${h.avg_buy_price.toFixed(2)}</td>
            <td>₹${h.current_price.toFixed(2)}</td>
            <td class="${h.unrealized_pnl >= 0 ? 'positive' : 'negative'}">
                ₹${h.unrealized_pnl.toFixed(2)}
            </td>
            <td class="${h.unrealized_pnl_pct >= 0 ? 'positive' : 'negative'}">
                ${h.unrealized_pnl_pct.toFixed(2)}%
            </td>
            <td>₹${(h.quantity * h.current_price).toFixed(2)}</td>
        </tr>
    `).join('');
}

function updateRecentTrades(trades) {
    const tbody = document.getElementById('trades-table');
    tbody.innerHTML = trades.slice(0, 10).map(t => `
        <tr>
            <td>${formatDateTime(t.trade_date, t.trade_time)}</td>
            <td><strong>${t.symbol}</strong></td>
            <td><span class="badge badge-${t.action.toLowerCase()}">${t.action}</span></td>
            <td>${t.quantity}</td>
            <td>₹${t.price.toFixed(2)}</td>
            <td>₹${(t.quantity * t.price).toFixed(2)}</td>
        </tr>
    `).join('');
}

async function calculatePNL() {
    const portfolioId = document.getElementById('portfolio-select').value;

    try {
        const response = await fetch(`/api/portfolios/${portfolioId}/calculate-pnl`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            alert(`P&L calculated successfully!\nRealized: ₹${data.realized_pnl}\nUnrealized: ₹${data.unrealized_pnl}`);
            loadPortfolioData(); // Reload data
        }
    } catch (error) {
        console.error('Error calculating P&L:', error);
    }
}

// Load data on page load
document.addEventListener('DOMContentLoaded', () => {
    loadPortfolioData();
    lucide.createIcons();
});
```

---

## 🔄 Implementation Steps

### **Phase 1: Create Top Bar Component**
1. Create `topbar.html` component file
2. Define CSS styles for top bar
3. Add JavaScript for account switching

### **Phase 2: Update Portfolio Page**
1. Add top bar
2. Add "Import CSV" button
3. Enhance stats display
4. Add portfolio selector
5. Integrate with API endpoints

### **Phase 3: Fix All Other Pages**
1. Update `dashboard.html`
2. Update `strategies.html`
3. Update `analytics.html`
4. Update `accounts.html`
5. Update `settings.html`
6. Update `notifications.html`
7. Update `help.html`
8. Update `history.html`
9. Update `profile.html`

### **Phase 4: Testing**
1. Test top bar on all pages
2. Test navigation links
3. Test portfolio data loading
4. Test Import CSV button
5. Test responsive design

---

## ✅ Success Criteria

- [ ] Consistent top bar across all pages
- [ ] "Import CSV" button on portfolio page links to `/portfolio-import`
- [ ] Portfolio selector shows all user portfolios
- [ ] Stats update when portfolio changes
- [ ] Holdings and trades display correctly
- [ ] All navigation links work
- [ ] No broken layouts
- [ ] Responsive on mobile devices

---

## 📝 Notes

- **Active Navigation:** Each page should mark its nav link as `active`
- **Portfolio Persistence:** Store last-selected portfolio in `localStorage`
- **Error Handling:** Show user-friendly messages for API errors
- **Loading States:** Show spinners while data loads
- **Empty States:** Show helpful messages when no data exists

---

*This plan covers the complete implementation of the top bar system and enhanced portfolio page.*
