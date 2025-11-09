/**
 * Strategies Page - Backend Integration
 * Connects UI to /api/strategies endpoints
 */

let strategies = [];
let selectedStrategy = null;

// Load strategies on page load
document.addEventListener('DOMContentLoaded', function() {
    loadStrategies();
    setupEventListeners();
    // Refresh every 10 seconds
    setInterval(loadStrategies, 10000);
});

function setupEventListeners() {
    // Search functionality
    const searchInput = document.getElementById('strategySearch');
    if (searchInput) {
        searchInput.addEventListener('input', filterStrategies);
    }

    // Filter buttons
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            filterBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            filterStrategies();
        });
    });
}

async function loadStrategies() {
    try {
        const response = await fetch('/api/strategies');
        if (!response.ok) throw new Error('Failed to load strategies');

        const data = await response.json();
        strategies = data.strategies || [];

        renderStrategies(strategies);
        updateStrategyStats();
    } catch (error) {
        console.error('Error loading strategies:', error);
        if (typeof Toast !== 'undefined') {
            Toast.error('Failed to load strategies: ' + error.message);
        }
    }
}

function renderStrategies(strategiesToRender) {
    const container = document.getElementById('strategiesContainer');
    if (!container) return;

    if (strategiesToRender.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: var(--color-text-secondary);">
                <i data-lucide="inbox" style="width: 48px; height: 48px; margin-bottom: 16px; opacity: 0.5;"></i>
                <h3 style="font-size: var(--text-lg); margin-bottom: 8px;">No Strategies Found</h3>
                <p style="font-size: var(--text-sm); margin-bottom: 20px;">Create your first trading strategy to get started</p>
                <button class="btn btn-primary" onclick="showCreateStrategyModal()">
                    <i data-lucide="plus" style="width: 16px; height: 16px;"></i>
                    Create Strategy
                </button>
            </div>
        `;
        lucide.createIcons();
        return;
    }

    let html = '';
    strategiesToRender.forEach(strategy => {
        const statusClass = strategy.enabled ? 'enabled' : 'disabled';
        const statusText = strategy.enabled ? 'Active' : 'Inactive';
        const winRateClass = strategy.win_rate >= 50 ? 'positive' : 'negative';
        const pnlClass = strategy.total_pnl >= 0 ? 'positive' : 'negative';

        html += `
            <div class="strategy-card" data-strategy-id="${strategy.id}">
                <div class="strategy-card__header">
                    <div>
                        <h3 class="strategy-card__title">${escapeHtml(strategy.name)}</h3>
                        <p class="strategy-card__description">${escapeHtml(strategy.description || 'No description')}</p>
                    </div>
                    <div class="strategy-card__status strategy-card__status--${statusClass}">
                        <span class="status-dot"></span>
                        ${statusText}
                    </div>
                </div>

                <div class="strategy-card__stats">
                    <div class="strategy-stat">
                        <div class="strategy-stat__label">Win Rate</div>
                        <div class="strategy-stat__value strategy-stat__value--${winRateClass}">
                            ${strategy.win_rate.toFixed(1)}%
                        </div>
                    </div>
                    <div class="strategy-stat">
                        <div class="strategy-stat__label">Total P&L</div>
                        <div class="strategy-stat__value strategy-stat__value--${pnlClass}">
                            ₹${strategy.total_pnl.toFixed(2)}
                        </div>
                    </div>
                    <div class="strategy-stat">
                        <div class="strategy-stat__label">Trades</div>
                        <div class="strategy-stat__value">
                            ${strategy.total_trades}
                        </div>
                    </div>
                </div>

                <div class="strategy-card__actions">
                    <button class="btn btn-sm ${strategy.enabled ? 'btn-warning' : 'btn-success'}" onclick="toggleStrategy(${strategy.id}, ${strategy.enabled}, event)">
                        <i data-lucide="${strategy.enabled ? 'pause' : 'play'}" style="width: 14px; height: 14px;"></i>
                        ${strategy.enabled ? 'Deactivate' : 'Activate'}
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="viewStrategy(${strategy.id})">
                        <i data-lucide="eye" style="width: 14px; height: 14px;"></i>
                        View
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="editStrategy(${strategy.id})">
                        <i data-lucide="edit" style="width: 14px; height: 14px;"></i>
                        Edit
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="deployStrategy(${strategy.id}, event)" ${!strategy.enabled ? 'disabled' : ''}>
                        <i data-lucide="rocket" style="width: 14px; height: 14px;"></i>
                        Deploy
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="backtestStrategy(${strategy.id})">
                        <i data-lucide="bar-chart" style="width: 14px; height: 14px;"></i>
                        Backtest
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteStrategy(${strategy.id}, event)">
                        <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                    </button>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
    lucide.createIcons();
}

function updateStrategyStats() {
    const totalStrategies = strategies.length;
    const activeStrategies = strategies.filter(s => s.enabled).length;
    const totalPnl = strategies.reduce((sum, s) => sum + s.total_pnl, 0);
    const avgWinRate = strategies.length > 0
        ? strategies.reduce((sum, s) => sum + s.win_rate, 0) / strategies.length
        : 0;

    // Update stats if elements exist
    updateStat('totalStrategies', totalStrategies);
    updateStat('activeStrategies', activeStrategies);
    updateStat('strategiesTotalPnl', '₹' + totalPnl.toFixed(2), totalPnl >= 0 ? 'positive' : 'negative');
    updateStat('avgWinRate', avgWinRate.toFixed(1) + '%');
}

function updateStat(id, value, className) {
    const el = document.getElementById(id);
    if (el) {
        el.textContent = value;
        if (className) {
            el.className = 'stat__value stat__value--' + className;
        }
    }
}

function filterStrategies() {
    const searchTerm = document.getElementById('strategySearch')?.value.toLowerCase() || '';
    const activeFilter = document.querySelector('.filter-btn.active')?.dataset.filter || 'all';

    let filtered = strategies;

    // Apply search filter
    if (searchTerm) {
        filtered = filtered.filter(s =>
            s.name.toLowerCase().includes(searchTerm) ||
            (s.description && s.description.toLowerCase().includes(searchTerm))
        );
    }

    // Apply status filter
    if (activeFilter === 'active') {
        filtered = filtered.filter(s => s.enabled);
    } else if (activeFilter === 'inactive') {
        filtered = filtered.filter(s => !s.enabled);
    }

    renderStrategies(filtered);
}

async function deployStrategy(id, event) {
    if (!confirm('Deploy this strategy in paper trading mode?')) return;

    const button = event ? event.target.closest('.btn') : null;
    const originalHTML = button ? button.innerHTML : '';

    if (button) {
        // Show loading state
        button.disabled = true;
        button.classList.add('btn-loading');
        button.innerHTML = `
            <div class="spinner"></div>
            <span>Deploying...</span>
        `;
    }

    try {
        const response = await fetch(`/api/strategies/${id}/deploy`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: 'paper' })
        });

        if (!response.ok) throw new Error('Deployment failed');

        const data = await response.json();

        if (button) {
            // Show success state (2 seconds)
            button.classList.remove('btn-loading');
            button.classList.add('btn-success');
            button.innerHTML = `
                <i data-lucide="check-circle" style="width: 14px; height: 14px;"></i>
                <span>Deployed!</span>
            `;
            lucide.createIcons();

            setTimeout(() => {
                button.disabled = false;
                button.classList.remove('btn-success');
                button.innerHTML = originalHTML;
                lucide.createIcons();
            }, 2000);
        }

        Toast.success(data.message || 'Strategy deployed successfully!');
        await loadStrategies();

    } catch (error) {
        console.error('Error deploying strategy:', error);

        if (button) {
            // Show error state (3 seconds)
            button.classList.remove('btn-loading');
            button.classList.add('btn-danger');
            button.innerHTML = `
                <i data-lucide="x-circle" style="width: 14px; height: 14px;"></i>
                <span>Failed</span>
            `;
            lucide.createIcons();

            setTimeout(() => {
                button.disabled = false;
                button.classList.remove('btn-danger');
                button.innerHTML = originalHTML;
                lucide.createIcons();
            }, 3000);
        }

        Toast.error('Failed to deploy strategy: ' + error.message);
    }
}

async function deleteStrategy(id, event) {
    if (!confirm('Are you sure you want to delete this strategy? This action cannot be undone.')) return;

    const button = event ? event.target.closest('.btn') : null;
    const originalHTML = button ? button.innerHTML : '';

    if (button) {
        button.disabled = true;
        button.classList.add('btn-loading');
        button.innerHTML = `
            <div class="spinner"></div>
        `;
    }

    try {
        const response = await fetch(`/api/strategies/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Delete failed');

        const data = await response.json();
        Toast.success(data.message || 'Strategy deleted successfully');
        await loadStrategies();
    } catch (error) {
        console.error('Error deleting strategy:', error);
        Toast.error('Failed to delete strategy: ' + error.message);

        if (button) {
            button.disabled = false;
            button.classList.remove('btn-loading');
            button.innerHTML = originalHTML;
            lucide.createIcons();
        }
    }
}

async function viewStrategy(id) {
    try {
        const response = await fetch(`/api/strategies/${id}`);
        if (!response.ok) throw new Error('Failed to load strategy');

        const strategy = await response.json();
        showStrategyDetailsModal(strategy);
    } catch (error) {
        console.error('Error loading strategy:', error);
        Toast.error('Failed to load strategy details: ' + error.message);
    }
}

function editStrategy(id) {
    const strategy = strategies.find(s => s.id === id);
    if (!strategy) return;

    showEditStrategyModal(strategy);
}

// Toggle strategy activate/deactivate
async function toggleStrategy(id, currentStatus, event) {
    const action = currentStatus ? 'deactivate' : 'activate';
    const confirmMsg = currentStatus
        ? 'Deactivate this strategy? It will stop generating signals.'
        : 'Activate this strategy? It will start generating signals.';

    if (!confirm(confirmMsg)) return;

    const button = event ? event.target.closest('.btn') : null;
    const originalHTML = button ? button.innerHTML : '';

    if (button) {
        button.disabled = true;
        button.classList.add('btn-loading');
        button.innerHTML = `
            <div class="spinner"></div>
            <span>${action === 'activate' ? 'Activating...' : 'Deactivating...'}</span>
        `;
    }

    try {
        const response = await fetch(`/api/strategies/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enabled: !currentStatus })
        });

        if (!response.ok) throw new Error('Failed to toggle strategy');

        const data = await response.json();
        Toast.success(`Strategy ${action}d successfully`);
        await loadStrategies();

        if (button) {
            button.disabled = false;
            button.classList.remove('btn-loading');
        }
    } catch (error) {
        console.error('Error toggling strategy:', error);
        Toast.error('Failed to toggle strategy: ' + error.message);

        if (button) {
            button.disabled = false;
            button.classList.remove('btn-loading');
            button.innerHTML = originalHTML;
            lucide.createIcons();
        }
    }
}

// Backtest strategy with comprehensive modal
async function backtestStrategy(id) {
    const strategy = strategies.find(s => s.id === id);
    if (!strategy) return;

    const modalHTML = `
        <div class="modal-overlay" onclick="closeModal(event)">
            <div class="modal modal--large" onclick="event.stopPropagation()">
                <div class="modal__header">
                    <h2 class="modal__title">Backtest Strategy: ${escapeHtml(strategy.name)}</h2>
                    <button class="modal__close" onclick="event.target.closest('.modal-overlay').remove()">
                        <i data-lucide="x" style="width: 20px; height: 20px;"></i>
                    </button>
                </div>
                <div class="modal__body">
                    <form id="backtestForm" onsubmit="runBacktest(event, ${id})">
                        <div class="form-group">
                            <label class="form-label">Backtest Period *</label>
                            <select class="form-input" name="period" required>
                                <option value="7days">Last 7 Days</option>
                                <option value="30days" selected>Last 30 Days</option>
                                <option value="90days">Last 90 Days</option>
                                <option value="6months">Last 6 Months</option>
                                <option value="1year">Last 1 Year</option>
                                <option value="custom">Custom Range</option>
                            </select>
                        </div>

                        <div class="form-row" id="customDateRange" style="display: none;">
                            <div class="form-group">
                                <label class="form-label">Start Date</label>
                                <input type="date" class="form-input" name="start_date">
                            </div>
                            <div class="form-group">
                                <label class="form-label">End Date</label>
                                <input type="date" class="form-input" name="end_date">
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Initial Capital *</label>
                                <input type="number" class="form-input" name="initial_capital"
                                    min="10000" step="1000" value="100000" required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Commission per Trade</label>
                                <input type="number" class="form-input" name="commission"
                                    min="0" step="0.01" value="20" required>
                            </div>
                        </div>

                        <div class="info-box">
                            <i data-lucide="info" class="info-box__icon" style="width: 20px; height: 20px;"></i>
                            <div class="info-box__content">
                                <div class="info-box__title">Backtest Information</div>
                                <div class="info-box__text">
                                    The backtest will simulate trades using historical data.
                                    Results include P&L, win rate, max drawdown, and trade-by-trade analysis.
                                </div>
                            </div>
                        </div>

                        <div class="modal__actions">
                            <button type="button" class="btn btn-secondary" onclick="event.target.closest('.modal-overlay').remove()">
                                Cancel
                            </button>
                            <button type="submit" class="btn btn-primary">
                                <i data-lucide="play" style="width: 16px; height: 16px;"></i>
                                Run Backtest
                            </button>
                        </div>
                    </form>

                    <div id="backtestResults" style="display: none; margin-top: var(--space-6);">
                        <!-- Results will be displayed here -->
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
    lucide.createIcons();

    // Handle custom date range toggle
    document.querySelector('[name="period"]').addEventListener('change', function() {
        const customRange = document.getElementById('customDateRange');
        customRange.style.display = this.value === 'custom' ? 'flex' : 'none';
    });
}

async function runBacktest(event, strategyId) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    const backtestParams = {
        period: formData.get('period'),
        initial_capital: parseFloat(formData.get('initial_capital')),
        commission: parseFloat(formData.get('commission'))
    };

    if (backtestParams.period === 'custom') {
        backtestParams.start_date = formData.get('start_date');
        backtestParams.end_date = formData.get('end_date');
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalHTML = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i data-lucide="loader" style="width: 16px; height: 16px; animation: spin 1s linear infinite;"></i> Running...';
    lucide.createIcons();

    try {
        const response = await fetch(`/api/strategies/${strategyId}/backtest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(backtestParams)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Backtest failed');
        }

        const data = await response.json();
        displayBacktestResults(data);

    } catch (error) {
        console.error('Error running backtest:', error);
        showError('Backtest failed: ' + error.message);
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalHTML;
        lucide.createIcons();
    }
}

function displayBacktestResults(results) {
    const resultsDiv = document.getElementById('backtestResults');
    if (!resultsDiv) return;

    const html = `
        <div class="backtest-results">
            <h3 style="font-size: var(--text-lg); font-weight: 600; margin-bottom: var(--space-5);">
                Backtest Results
            </h3>

            <div class="stats-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: var(--space-5); margin-bottom: var(--space-6);">
                <div class="stat-box">
                    <div class="stat-box__label">Total Trades</div>
                    <div class="stat-box__value">${results.total_trades || 0}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-box__label">Win Rate</div>
                    <div class="stat-box__value">${(results.win_rate || 0).toFixed(1)}%</div>
                </div>
                <div class="stat-box">
                    <div class="stat-box__label">Total P&L</div>
                    <div class="stat-box__value" style="color: ${results.total_pnl >= 0 ? 'var(--color-success)' : 'var(--color-error)'}">
                        ₹${(results.total_pnl || 0).toFixed(2)}
                    </div>
                </div>
                <div class="stat-box">
                    <div class="stat-box__label">Max Drawdown</div>
                    <div class="stat-box__value" style="color: var(--color-error)">
                        ${(results.max_drawdown || 0).toFixed(2)}%
                    </div>
                </div>
                <div class="stat-box">
                    <div class="stat-box__label">Sharpe Ratio</div>
                    <div class="stat-box__value">${(results.sharpe_ratio || 0).toFixed(2)}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-box__label">Profit Factor</div>
                    <div class="stat-box__value">${(results.profit_factor || 0).toFixed(2)}</div>
                </div>
            </div>

            <div class="alert alert--${results.total_pnl >= 0 ? 'success' : 'error'}">
                <i data-lucide="${results.total_pnl >= 0 ? 'trending-up' : 'trending-down'}" style="width: 20px; height: 20px;"></i>
                <span>
                    ${results.total_pnl >= 0 ? 'Profitable strategy!' : 'Strategy needs optimization.'}
                    ${results.message || ''}
                </span>
            </div>
        </div>
    `;

    resultsDiv.innerHTML = html;
    resultsDiv.style.display = 'block';
    lucide.createIcons();
}

function showCreateStrategyModal() {
    // Create modal HTML
    const modalHTML = `
        <div class="modal-overlay" id="createStrategyModal" onclick="closeModal(event)">
            <div class="modal" onclick="event.stopPropagation()">
                <div class="modal__header">
                    <h2 class="modal__title">Create New Strategy</h2>
                    <button class="modal__close" onclick="closeCreateModal()">
                        <i data-lucide="x" style="width: 20px; height: 20px;"></i>
                    </button>
                </div>
                <div class="modal__body">
                    <form id="createStrategyForm" onsubmit="createStrategy(event)">
                        <div class="form-group">
                            <label class="form-label">Strategy Name *</label>
                            <input type="text" class="form-input" name="name" required
                                placeholder="e.g., EMA Crossover 9/21">
                        </div>

                        <div class="form-group">
                            <label class="form-label">Description</label>
                            <textarea class="form-input" name="description" rows="3"
                                placeholder="Brief description of the strategy..."></textarea>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Strategy Type *</label>
                            <select class="form-input" name="strategy_type" id="strategyType" required onchange="handleStrategyTypeChange()">
                                <option value="">Select type...</option>
                                <option value="ema_crossover">EMA Crossover</option>
                                <option value="rsi_strategy">RSI Strategy</option>
                                <option value="breakout">Breakout</option>
                                <option value="custom">Custom Strategy</option>
                            </select>
                        </div>

                        <!-- Strategy-specific parameters -->
                        <div id="strategyParameters"></div>

                        <!-- Symbols Selection -->
                        <div class="form-group">
                            <label class="form-label">Trading Symbols *</label>
                            <input type="text" class="form-input" name="symbols"
                                placeholder="e.g., RELIANCE, TCS, INFY (comma-separated)" required>
                            <small class="form-hint">Enter NSE/BSE symbols separated by commas</small>
                        </div>

                        <!-- Risk Management -->
                        <div class="form-group">
                            <label class="form-label">Timeframe *</label>
                            <select class="form-input" name="timeframe" required>
                                <option value="1minute">1 Minute</option>
                                <option value="5minute" selected>5 Minutes</option>
                                <option value="15minute">15 Minutes</option>
                                <option value="1hour">1 Hour</option>
                                <option value="1day">1 Day</option>
                            </select>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Stop Loss %</label>
                                <input type="number" class="form-input" name="stop_loss_pct"
                                    step="0.1" min="0" max="10" value="2.0"
                                    placeholder="2.0">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Target %</label>
                                <input type="number" class="form-input" name="target_pct"
                                    step="0.1" min="0" max="20" value="4.0"
                                    placeholder="4.0">
                            </div>
                        </div>

                        <div class="form-group">
                            <label class="form-label">
                                <input type="checkbox" name="enabled" checked>
                                Enable strategy after creation
                            </label>
                        </div>

                        <div class="modal__actions">
                            <button type="button" class="btn btn-secondary" onclick="closeCreateModal()">
                                Cancel
                            </button>
                            <button type="submit" class="btn btn-primary">
                                <i data-lucide="plus" style="width: 16px; height: 16px;"></i>
                                Create Strategy
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
    lucide.createIcons();
}

// Handle strategy type change to show relevant parameters
function handleStrategyTypeChange() {
    const strategyType = document.getElementById('strategyType').value;
    const parametersDiv = document.getElementById('strategyParameters');

    if (!parametersDiv) return;

    let html = '';

    switch(strategyType) {
        case 'ema_crossover':
            html = `
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Fast EMA Period *</label>
                        <input type="number" class="form-input" name="fast_period"
                            min="1" max="200" value="9" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Slow EMA Period *</label>
                        <input type="number" class="form-input" name="slow_period"
                            min="1" max="200" value="21" required>
                    </div>
                </div>
            `;
            break;

        case 'rsi_strategy':
            html = `
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">RSI Period *</label>
                        <input type="number" class="form-input" name="rsi_period"
                            min="1" max="50" value="14" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">RSI Oversold Level</label>
                        <input type="number" class="form-input" name="oversold_level"
                            min="10" max="40" value="30" required>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">RSI Overbought Level</label>
                        <input type="number" class="form-input" name="overbought_level"
                            min="60" max="90" value="70" required>
                    </div>
                </div>
            `;
            break;

        case 'breakout':
            html = `
                <div class="form-row">
                    <div class="form-group">
                        <label class="form-label">Lookback Period *</label>
                        <input type="number" class="form-input" name="lookback_period"
                            min="5" max="100" value="20" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Breakout Threshold %</label>
                        <input type="number" class="form-input" name="breakout_threshold"
                            step="0.1" min="0.1" max="5" value="1.0" required>
                    </div>
                </div>
            `;
            break;

        case 'custom':
            html = `
                <div class="form-group">
                    <label class="form-label">Custom Indicators</label>
                    <textarea class="form-input" name="custom_indicators" rows="3"
                        placeholder="e.g., SMA 20, MACD, Bollinger Bands"></textarea>
                    <small class="form-hint">List the indicators you'll use</small>
                </div>
                <div class="form-group">
                    <label class="form-label">Entry Conditions</label>
                    <textarea class="form-input" name="entry_conditions" rows="3"
                        placeholder="Describe your entry rules..." required></textarea>
                </div>
                <div class="form-group">
                    <label class="form-label">Exit Conditions</label>
                    <textarea class="form-input" name="exit_conditions" rows="3"
                        placeholder="Describe your exit rules..." required></textarea>
                </div>
                <div class="info-box">
                    <i data-lucide="info" class="info-box__icon" style="width: 20px; height: 20px;"></i>
                    <div class="info-box__content">
                        <div class="info-box__title">Custom Strategy Note</div>
                        <div class="info-box__text">
                            Custom strategies require manual implementation in code.
                            This form captures your strategy logic for documentation and future implementation.
                        </div>
                    </div>
                </div>
            `;
            break;
    }

    parametersDiv.innerHTML = html;
    lucide.createIcons();
}

async function createStrategy(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    // Build parameters based on strategy type
    const strategyType = formData.get('strategy_type');
    const parameters = {
        timeframe: formData.get('timeframe'),
        stop_loss_pct: parseFloat(formData.get('stop_loss_pct') || 2.0),
        target_pct: parseFloat(formData.get('target_pct') || 4.0),
        symbols: formData.get('symbols').split(',').map(s => s.trim()).filter(s => s)
    };

    // Add strategy-specific parameters
    switch(strategyType) {
        case 'ema_crossover':
            parameters.fast_period = parseInt(formData.get('fast_period') || 9);
            parameters.slow_period = parseInt(formData.get('slow_period') || 21);
            break;
        case 'rsi_strategy':
            parameters.rsi_period = parseInt(formData.get('rsi_period') || 14);
            parameters.oversold_level = parseInt(formData.get('oversold_level') || 30);
            parameters.overbought_level = parseInt(formData.get('overbought_level') || 70);
            break;
        case 'breakout':
            parameters.lookback_period = parseInt(formData.get('lookback_period') || 20);
            parameters.breakout_threshold = parseFloat(formData.get('breakout_threshold') || 1.0);
            break;
        case 'custom':
            parameters.custom_indicators = formData.get('custom_indicators');
            parameters.entry_conditions = formData.get('entry_conditions');
            parameters.exit_conditions = formData.get('exit_conditions');
            break;
    }

    const strategyData = {
        name: formData.get('name'),
        description: formData.get('description'),
        strategy_type: strategyType,
        enabled: formData.get('enabled') === 'on',
        parameters: parameters
    };

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalHTML = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.classList.add('btn-loading');
    submitBtn.innerHTML = `
        <div class="spinner"></div>
        <span>Creating...</span>
    `;

    try {
        const response = await fetch('/api/strategies', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(strategyData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create strategy');
        }

        const data = await response.json();
        Toast.success(data.message || 'Strategy created successfully!');
        closeCreateModal();
        await loadStrategies();
    } catch (error) {
        console.error('Error creating strategy:', error);
        Toast.error('Failed to create strategy: ' + error.message);
    } finally {
        submitBtn.disabled = false;
        submitBtn.classList.remove('btn-loading');
        submitBtn.innerHTML = originalHTML;
        lucide.createIcons();
    }
}

function closeCreateModal() {
    const modal = document.getElementById('createStrategyModal');
    if (modal) modal.remove();
}

function closeModal(event) {
    if (event.target.classList.contains('modal-overlay')) {
        event.target.remove();
    }
}

function showStrategyDetailsModal(strategy) {
    const modalHTML = `
        <div class="modal-overlay" onclick="closeModal(event)">
            <div class="modal modal--large" onclick="event.stopPropagation()">
                <div class="modal__header">
                    <h2 class="modal__title">${escapeHtml(strategy.name)}</h2>
                    <button class="modal__close" onclick="event.target.closest('.modal-overlay').remove()">
                        <i data-lucide="x" style="width: 20px; height: 20px;"></i>
                    </button>
                </div>
                <div class="modal__body">
                    <div class="strategy-details">
                        <div class="detail-row">
                            <span class="detail-label">Type:</span>
                            <span class="detail-value">${strategy.strategy_type}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Status:</span>
                            <span class="detail-value">${strategy.enabled ? 'Active' : 'Inactive'}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Win Rate:</span>
                            <span class="detail-value">${strategy.win_rate.toFixed(1)}%</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Total P&L:</span>
                            <span class="detail-value">₹${strategy.total_pnl.toFixed(2)}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Total Trades:</span>
                            <span class="detail-value">${strategy.total_trades}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Created:</span>
                            <span class="detail-value">${new Date(strategy.created_at).toLocaleString()}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
    lucide.createIcons();
}

function showEditStrategyModal(strategy) {
    const strategyType = strategy.config?.strategy_type || 'custom';

    // Get strategy-specific parameters
    let strategyParams = '';
    if (strategyType === 'ema_crossover') {
        strategyParams = `
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Fast EMA Period *</label>
                    <input type="number" class="form-input" name="fast_period"
                        min="1" max="200" value="${strategy.config.fast_period || 9}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Slow EMA Period *</label>
                    <input type="number" class="form-input" name="slow_period"
                        min="1" max="200" value="${strategy.config.slow_period || 21}" required>
                </div>
            </div>
        `;
    } else if (strategyType === 'rsi_strategy') {
        strategyParams = `
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">RSI Period *</label>
                    <input type="number" class="form-input" name="rsi_period"
                        min="1" max="50" value="${strategy.config.rsi_period || 14}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Oversold Level</label>
                    <input type="number" class="form-input" name="oversold_level"
                        min="10" max="40" value="${strategy.config.oversold_level || 30}" required>
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">Overbought Level</label>
                <input type="number" class="form-input" name="overbought_level"
                    min="60" max="90" value="${strategy.config.overbought_level || 70}" required>
            </div>
        `;
    } else if (strategyType === 'breakout') {
        strategyParams = `
            <div class="form-row">
                <div class="form-group">
                    <label class="form-label">Lookback Period *</label>
                    <input type="number" class="form-input" name="lookback_period"
                        min="5" max="100" value="${strategy.config.lookback_period || 20}" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Breakout Threshold %</label>
                    <input type="number" class="form-input" name="breakout_threshold"
                        min="0.1" max="10" step="0.1" value="${strategy.config.breakout_threshold || 1.0}" required>
                </div>
            </div>
        `;
    } else if (strategyType === 'custom') {
        strategyParams = `
            <div class="form-group">
                <label class="form-label">Custom Indicators</label>
                <textarea class="form-input" name="custom_indicators" rows="2"
                    placeholder="e.g., SMA 20, MACD, Bollinger Bands">${strategy.config.custom_indicators || ''}</textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Entry Conditions</label>
                <textarea class="form-input" name="entry_conditions" rows="3"
                    placeholder="Describe your entry rules...">${strategy.config.entry_conditions || ''}</textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Exit Conditions</label>
                <textarea class="form-input" name="exit_conditions" rows="3"
                    placeholder="Describe your exit rules...">${strategy.config.exit_conditions || ''}</textarea>
            </div>
        `;
    }

    const symbolsArray = strategy.config?.symbols || [];
    const symbolsStr = Array.isArray(symbolsArray) ? symbolsArray.join(', ') : '';

    const modalHTML = `
        <div class="modal-overlay" onclick="closeModal(event)">
            <div class="modal modal--large" onclick="event.stopPropagation()">
                <div class="modal__header">
                    <h2 class="modal__title">Edit Strategy: ${escapeHtml(strategy.name)}</h2>
                    <button class="modal__close" onclick="event.target.closest('.modal-overlay').remove()">
                        <i data-lucide="x" style="width: 20px; height: 20px;"></i>
                    </button>
                </div>
                <div class="modal__body">
                    <form id="editStrategyForm" onsubmit="updateStrategy(event, ${strategy.id})">
                        <div class="form-group">
                            <label class="form-label">Strategy Name *</label>
                            <input type="text" class="form-input" name="name"
                                value="${escapeHtml(strategy.name)}" readonly style="background: var(--color-bg-tertiary); cursor: not-allowed;">
                            <small class="form-hint">Strategy name cannot be changed</small>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Description *</label>
                            <textarea class="form-input" name="description" rows="2" required>${escapeHtml(strategy.description || '')}</textarea>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Strategy Type</label>
                            <input type="text" class="form-input" value="${strategyType}" readonly style="background: var(--color-bg-tertiary); cursor: not-allowed;">
                            <small class="form-hint">Strategy type cannot be changed</small>
                        </div>

                        ${strategyParams}

                        <div class="form-group">
                            <label class="form-label">Trading Symbols *</label>
                            <input type="text" class="form-input" name="symbols"
                                value="${escapeHtml(symbolsStr)}"
                                placeholder="e.g., RELIANCE, TCS, INFY" required>
                            <small class="form-hint">Enter NSE/BSE symbols separated by commas</small>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Timeframe *</label>
                                <select class="form-input" name="timeframe" required>
                                    <option value="1m" ${strategy.timeframe === '1m' ? 'selected' : ''}>1 Minute</option>
                                    <option value="5m" ${strategy.timeframe === '5m' ? 'selected' : ''}>5 Minutes</option>
                                    <option value="15m" ${strategy.timeframe === '15m' ? 'selected' : ''}>15 Minutes</option>
                                    <option value="1h" ${strategy.timeframe === '1h' ? 'selected' : ''}>1 Hour</option>
                                    <option value="1d" ${strategy.timeframe === '1d' ? 'selected' : ''}>1 Day</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Stop Loss % *</label>
                                <input type="number" class="form-input" name="stop_loss_pct"
                                    min="0.1" max="10" step="0.1" value="${strategy.config?.stop_loss_pct || 2.0}" required>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">Target % *</label>
                                <input type="number" class="form-input" name="target_pct"
                                    min="0.1" max="20" step="0.1" value="${strategy.config?.target_pct || 4.0}" required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Status</label>
                                <select class="form-input" name="enabled">
                                    <option value="true" ${strategy.enabled ? 'selected' : ''}>Enabled</option>
                                    <option value="false" ${!strategy.enabled ? 'selected' : ''}>Disabled</option>
                                </select>
                            </div>
                        </div>

                        <div class="modal__actions">
                            <button type="button" class="btn btn-secondary" onclick="event.target.closest('.modal-overlay').remove()">
                                Cancel
                            </button>
                            <button type="submit" class="btn btn-primary">
                                <i data-lucide="save" style="width: 16px; height: 16px;"></i>
                                Save Changes
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHTML);
    lucide.createIcons();
}

async function updateStrategy(event, strategyId) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    const strategy = strategies.find(s => s.id === strategyId);
    if (!strategy) {
        showError('Strategy not found');
        return;
    }

    const strategyType = strategy.config?.strategy_type || 'custom';

    // Build updated config
    const config = {
        strategy_type: strategyType,
        symbols: formData.get('symbols').split(',').map(s => s.trim()).filter(s => s),
        timeframe: formData.get('timeframe'),
        stop_loss_pct: parseFloat(formData.get('stop_loss_pct')),
        target_pct: parseFloat(formData.get('target_pct'))
    };

    // Add strategy-specific parameters
    if (strategyType === 'ema_crossover') {
        config.fast_period = parseInt(formData.get('fast_period'));
        config.slow_period = parseInt(formData.get('slow_period'));
    } else if (strategyType === 'rsi_strategy') {
        config.rsi_period = parseInt(formData.get('rsi_period'));
        config.oversold_level = parseInt(formData.get('oversold_level'));
        config.overbought_level = parseInt(formData.get('overbought_level'));
    } else if (strategyType === 'breakout') {
        config.lookback_period = parseInt(formData.get('lookback_period'));
        config.breakout_threshold = parseFloat(formData.get('breakout_threshold'));
    } else if (strategyType === 'custom') {
        config.custom_indicators = formData.get('custom_indicators') || '';
        config.entry_conditions = formData.get('entry_conditions') || '';
        config.exit_conditions = formData.get('exit_conditions') || '';
    }

    const updateData = {
        description: formData.get('description'),
        config: config,
        timeframe: formData.get('timeframe'),
        enabled: formData.get('enabled') === 'true'
    };

    const submitBtn = form.querySelector('button[type="submit"]');
    const originalHTML = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i data-lucide="loader" style="width: 16px; height: 16px;"></i> Saving...';
    lucide.createIcons();

    try {
        const response = await fetch(`/api/strategies/${strategyId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to update strategy');
        }

        const data = await response.json();
        Toast.success('Strategy updated successfully!');
        form.closest('.modal-overlay').remove();
        await loadStrategies();

    } catch (error) {
        console.error('Error updating strategy:', error);
        Toast.error('Failed to update strategy: ' + error.message);
    } finally {
        submitBtn.disabled = false;
        submitBtn.classList.remove('btn-loading');
        submitBtn.innerHTML = originalHTML;
        lucide.createIcons();
    }
}

function showBacktestModal(id) {
    Toast.info('Backtest functionality - Coming soon');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
