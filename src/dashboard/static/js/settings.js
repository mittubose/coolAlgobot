/**
 * Settings Page - Backend Integration
 * Manages all configuration settings with tabbed interface
 */

let currentSettings = {
    trading: {},
    risk: {},
    broker: {},
    alerts: {}
};

// Load settings on page load
document.addEventListener('DOMContentLoaded', function() {
    loadAllSettings();
    setupEventListeners();
});

function setupEventListeners() {
    // Form submissions - updated IDs to match new HTML
    const tradingForm = document.getElementById('tradingSettingsForm');
    const riskForm = document.getElementById('riskSettingsForm');
    const brokerForm = document.getElementById('brokerSettingsForm');
    const alertsForm = document.getElementById('alertsSettingsForm');

    if (tradingForm) tradingForm.addEventListener('submit', saveTradingSettings);
    if (riskForm) riskForm.addEventListener('submit', saveRiskSettings);
    if (brokerForm) brokerForm.addEventListener('submit', saveBrokerSettings);
    if (alertsForm) alertsForm.addEventListener('submit', saveAlertsSettings);

    // Test broker connection
    const testBtn = document.getElementById('testBrokerBtn');
    if (testBtn) testBtn.addEventListener('click', testBrokerConnection);
}

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.settings-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Find the clicked tab button and add active class
    const activeTab = Array.from(document.querySelectorAll('.settings-tab')).find(tab => {
        return tab.getAttribute('onclick')?.includes(`'${tabName}'`);
    });
    if (activeTab) activeTab.classList.add('active');

    // Update tab panels - new structure uses IDs like 'trading-tab', 'risk-tab', etc.
    document.querySelectorAll('.settings-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    const targetPanel = document.getElementById(`${tabName}-tab`);
    if (targetPanel) targetPanel.classList.add('active');

    lucide.createIcons();
}

// ============================================================================
// Load Settings
// ============================================================================

async function loadAllSettings() {
    try {
        const response = await fetch('/api/settings');
        if (!response.ok) throw new Error('Failed to load settings');

        const data = await response.json();
        currentSettings = data.settings || {};

        populateTradingSettings(currentSettings.trading || {});
        populateRiskSettings(currentSettings.risk || {});
        populateBrokerSettings(currentSettings.broker || {});
        populateAlertsSettings(currentSettings.alerts || {});

    } catch (error) {
        console.error('Error loading settings:', error);
        showAlert('Failed to load settings: ' + error.message, 'error');
    }
}

function populateTradingSettings(trading) {
    // Updated to match new HTML field IDs
    const tradingMode = document.getElementById('tradingMode');
    const defaultExchange = document.getElementById('defaultExchange');
    const preMarketStart = document.getElementById('preMarketStart');
    const preMarketEnd = document.getElementById('preMarketEnd');
    const marketStart = document.getElementById('marketStart');
    const marketEnd = document.getElementById('marketEnd');
    const autoStart = document.getElementById('autoStart');
    const autoStop = document.getElementById('autoStop');

    if (tradingMode) tradingMode.value = trading.mode || 'paper';
    if (defaultExchange) defaultExchange.value = trading.exchange || 'NSE';
    if (preMarketStart) preMarketStart.value = trading.pre_market_start || '09:00';
    if (preMarketEnd) preMarketEnd.value = trading.pre_market_end || '09:15';
    if (marketStart) marketStart.value = trading.market_start || '09:15';
    if (marketEnd) marketEnd.value = trading.market_end || '15:30';
    if (autoStart) autoStart.checked = trading.auto_start || false;
    if (autoStop) autoStop.checked = trading.auto_stop !== false; // default true
}

function populateRiskSettings(risk) {
    // Updated to match new HTML field IDs
    const totalCapital = document.getElementById('totalCapital');
    const maxCapitalPerTrade = document.getElementById('maxCapitalPerTrade');
    const maxDailyLoss = document.getElementById('maxDailyLoss');
    const positionSizingMethod = document.getElementById('positionSizingMethod');
    const maxPositionSize = document.getElementById('maxPositionSize');
    const maxPositions = document.getElementById('maxPositions');
    const globalStopLoss = document.getElementById('globalStopLoss');
    const globalTarget = document.getElementById('globalTarget');
    const trailingStopLoss = document.getElementById('trailingStopLoss');

    if (totalCapital) totalCapital.value = risk.total_capital || 100000;
    if (maxCapitalPerTrade) maxCapitalPerTrade.value = risk.max_capital_per_trade || 10;
    if (maxDailyLoss) maxDailyLoss.value = risk.max_daily_loss || 5;
    if (positionSizingMethod) positionSizingMethod.value = risk.position_sizing_method || 'fixed';
    if (maxPositionSize) maxPositionSize.value = risk.max_position_size || 50000;
    if (maxPositions) maxPositions.value = risk.max_positions || 5;
    if (globalStopLoss) globalStopLoss.value = risk.global_stop_loss || 2.0;
    if (globalTarget) globalTarget.value = risk.global_target || 4.0;
    if (trailingStopLoss) trailingStopLoss.checked = risk.trailing_stop_loss || false;
}

function populateBrokerSettings(broker) {
    // Updated to match new HTML field IDs
    const primaryBroker = document.getElementById('primaryBroker');
    const apiKey = document.getElementById('apiKey');
    const brokerId = document.getElementById('brokerId');
    const autoLogin = document.getElementById('autoLogin');
    const autoReconnect = document.getElementById('autoReconnect');

    if (primaryBroker) primaryBroker.value = broker.broker_name || 'zerodha';
    if (apiKey) apiKey.value = broker.api_key_masked || '';
    if (brokerId) brokerId.value = broker.user_id || '';
    if (autoLogin) autoLogin.checked = broker.auto_login || false;
    if (autoReconnect) autoReconnect.checked = broker.auto_reconnect !== false; // default true
}

function populateAlertsSettings(alerts) {
    // Updated to match new HTML field IDs
    const telegramEnabled = document.getElementById('telegramEnabled');
    const telegramBotToken = document.getElementById('telegramBotToken');
    const telegramChatId = document.getElementById('telegramChatId');
    const alertTradeExecuted = document.getElementById('alertTradeExecuted');
    const alertStopLoss = document.getElementById('alertStopLoss');
    const alertTarget = document.getElementById('alertTarget');
    const alertError = document.getElementById('alertError');
    const alertDailySummary = document.getElementById('alertDailySummary');

    if (telegramEnabled) telegramEnabled.checked = alerts.telegram_enabled || false;
    if (telegramBotToken) telegramBotToken.value = alerts.telegram_bot_token || '';
    if (telegramChatId) telegramChatId.value = alerts.telegram_chat_id || '';

    if (alertTradeExecuted) alertTradeExecuted.checked = alerts.alert_trade !== false; // default true
    if (alertStopLoss) alertStopLoss.checked = alerts.alert_stop_loss !== false;
    if (alertTarget) alertTarget.checked = alerts.alert_target !== false;
    if (alertError) alertError.checked = alerts.alert_error !== false;
    if (alertDailySummary) alertDailySummary.checked = alerts.alert_daily_summary || false;
}

// ============================================================================
// Save Settings
// ============================================================================

async function saveTradingSettings(event) {
    event.preventDefault();

    // Updated to match new HTML field names
    const tradingSettings = {
        mode: document.getElementById('tradingMode').value,
        exchange: document.getElementById('defaultExchange').value,
        pre_market_start: document.getElementById('preMarketStart').value,
        pre_market_end: document.getElementById('preMarketEnd').value,
        market_start: document.getElementById('marketStart').value,
        market_end: document.getElementById('marketEnd').value,
        auto_start: document.getElementById('autoStart').checked,
        auto_stop: document.getElementById('autoStop').checked
    };

    try {
        const response = await fetch('/api/settings/trading', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tradingSettings)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save trading settings');
        }

        const data = await response.json();
        showAlert(data.message || 'Trading settings saved successfully', 'success');
        currentSettings.trading = tradingSettings;

    } catch (error) {
        console.error('Error saving trading settings:', error);
        showAlert('Failed to save trading settings: ' + error.message, 'error');
    }
}

async function saveRiskSettings(event) {
    event.preventDefault();

    // Updated to match new HTML field names
    const riskSettings = {
        total_capital: parseFloat(document.getElementById('totalCapital').value),
        max_capital_per_trade: parseFloat(document.getElementById('maxCapitalPerTrade').value),
        max_daily_loss: parseFloat(document.getElementById('maxDailyLoss').value),
        position_sizing_method: document.getElementById('positionSizingMethod').value,
        max_position_size: parseFloat(document.getElementById('maxPositionSize').value),
        max_positions: parseInt(document.getElementById('maxPositions').value),
        global_stop_loss: parseFloat(document.getElementById('globalStopLoss').value),
        global_target: parseFloat(document.getElementById('globalTarget').value),
        trailing_stop_loss: document.getElementById('trailingStopLoss').checked
    };

    try {
        const response = await fetch('/api/settings/risk', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(riskSettings)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save risk settings');
        }

        const data = await response.json();
        showAlert(data.message || 'Risk management settings saved successfully', 'success');
        currentSettings.risk = riskSettings;

    } catch (error) {
        console.error('Error saving risk settings:', error);
        showAlert('Failed to save risk settings: ' + error.message, 'error');
    }
}

async function saveBrokerSettings(event) {
    event.preventDefault();

    const apiKey = document.getElementById('apiKey').value;
    const apiSecret = document.getElementById('apiSecret').value;

    if (!apiKey || !apiSecret) {
        showAlert('Please enter both API Key and API Secret', 'error');
        return;
    }

    // Updated to match new HTML field names
    const brokerSettings = {
        broker_name: document.getElementById('primaryBroker').value,
        api_key: apiKey,
        api_secret: apiSecret,
        user_id: document.getElementById('brokerId').value,
        auto_login: document.getElementById('autoLogin').checked,
        auto_reconnect: document.getElementById('autoReconnect').checked
    };

    try {
        const response = await fetch('/api/broker/configure', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(brokerSettings)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save broker settings');
        }

        const data = await response.json();
        showAlert(data.message || 'Broker settings saved successfully', 'success');

        // Clear secret field for security
        document.getElementById('apiSecret').value = '';

        // Update masked key display
        loadAllSettings();

    } catch (error) {
        console.error('Error saving broker settings:', error);
        showAlert('Failed to save broker settings: ' + error.message, 'error');
    }
}

async function saveAlertsSettings(event) {
    event.preventDefault();

    // Updated to match new HTML field names
    const alertsSettings = {
        telegram_enabled: document.getElementById('telegramEnabled').checked,
        telegram_bot_token: document.getElementById('telegramBotToken').value,
        telegram_chat_id: document.getElementById('telegramChatId').value,
        alert_trade: document.getElementById('alertTradeExecuted').checked,
        alert_stop_loss: document.getElementById('alertStopLoss').checked,
        alert_target: document.getElementById('alertTarget').checked,
        alert_error: document.getElementById('alertError').checked,
        alert_daily_summary: document.getElementById('alertDailySummary').checked
    };

    try {
        const response = await fetch('/api/settings/alerts', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(alertsSettings)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to save alerts settings');
        }

        const data = await response.json();
        showAlert(data.message || 'Alerts settings saved successfully', 'success');
        currentSettings.alerts = alertsSettings;

    } catch (error) {
        console.error('Error saving alerts settings:', error);
        showAlert('Failed to save alerts settings: ' + error.message, 'error');
    }
}

// ============================================================================
// Broker Functions
// ============================================================================

async function testBrokerConnection() {
    const btn = event.target;
    const originalText = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader" style="width: 16px; height: 16px; animation: spin 1s linear infinite;"></i> Testing...';
    lucide.createIcons();

    try {
        const response = await fetch('/api/broker/test', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            showAlert('Broker connection successful!', 'success');
        } else {
            showAlert('Broker connection failed: ' + (data.error || 'Unknown error'), 'error');
        }

    } catch (error) {
        console.error('Error testing broker:', error);
        showAlert('Failed to test broker connection: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
        lucide.createIcons();
    }
}

// ============================================================================
// Helper Functions
// ============================================================================

function showAlert(message, type = 'info') {
    const alertArea = document.getElementById('alertArea');
    if (!alertArea) return;

    const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'alert-circle' : 'info';
    const alertHTML = `
        <div class="alert alert--${type}">
            <i data-lucide="${icon}" style="width: 20px; height: 20px;"></i>
            <span>${escapeHtml(message)}</span>
            <button class="alert__close" onclick="this.parentElement.remove()">
                <i data-lucide="x" style="width: 16px; height: 16px;"></i>
            </button>
        </div>
    `;

    alertArea.innerHTML = alertHTML;
    lucide.createIcons();

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = alertArea.querySelector('.alert');
        if (alert) alert.remove();
    }, 5000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add keyframe for loader spin
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
