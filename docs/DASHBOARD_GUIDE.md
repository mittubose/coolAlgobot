# Web Dashboard Guide

## Overview

The Scalping Bot Web Dashboard is a modern, user-friendly interface for monitoring and controlling your trading bot in real-time.

## Starting the Dashboard

### Method 1: Using the Launcher Script
```bash
# Activate virtual environment
source venv/bin/activate

# Run the dashboard
python run_dashboard.py
```

### Method 2: Direct Launch
```bash
# Activate virtual environment
source venv/bin/activate

# Run directly
python -m src.dashboard.app
```

The dashboard will start on **http://localhost:8050**

## Dashboard Features

### 1. Real-Time Monitoring

**Status Overview**
- Bot status (Stopped/Running/Paused/Error)
- Trading mode (Paper/Live)
- Last update timestamp
- Authentication status

**P&L Tracking**
- Daily P&L
- Total P&L
- Unrealized P&L (from open positions)
- Color-coded (green for profit, red for loss)

**Trading Statistics**
- Total trades executed
- Win rate percentage
- Winning trades count
- Losing trades count

### 2. Bot Controls

**Start Button** ▶
- Start the bot in selected mode (Paper/Live)
- Choose between Paper Trading or Live Trading
- Live mode requires confirmation for safety

**Pause Button** ⏸
- Temporarily pause trading
- Keeps positions open
- Stops new trade execution

**Resume Button** ▶
- Resume trading after pause
- Continues with existing positions

**Stop Button** ⏹
- Stop the bot completely
- Requires confirmation
- Closes all positions (configurable)

**Emergency Stop** 🛑
- Immediate halt of all trading
- Cancels all pending orders
- Closes all open positions
- Use in critical situations only

### 3. Position Tracking

View all current open positions with:
- Symbol name
- Quantity
- Average entry price
- Current market price
- Unrealized P&L

**Auto-updates every 2 seconds**

### 4. Trade History

Recent trades display showing:
- Execution time
- Symbol
- Action (BUY/SELL)
- Quantity
- Execution price
- Realized P&L

Shows last 10 trades, most recent first.

### 5. Log Viewer

Real-time log streaming with tabs for:
- **System Logs** - General application events
- **Trade Logs** - All trade executions
- **Error Logs** - Errors and exceptions
- **Signal Logs** - Strategy signals

Features:
- Color-coded log levels
- Timestamps
- Auto-scroll to latest
- Last 50 entries displayed

### 6. Authentication

**Initial Setup**
1. Dashboard shows authentication section
2. Click "Login with Zerodha" button
3. Login to Zerodha in browser
4. Copy request token from redirect URL
5. Paste token in dashboard
6. Click Submit

**Status Indication**
- Green checkmark when authenticated
- Login prompt when not authenticated
- Auto-checks authentication on load

## Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│  📈 Scalping Bot Dashboard    [Status: Running]     │
├─────────────────────────────────────────────────────┤
│  🔐 Authentication (if needed)                      │
├─────────────────────────────────────────────────────┤
│  Mode: [Paper ▼]  [▶ Start] [⏸ Pause] [⏹ Stop]     │
│                   [🛑 EMERGENCY STOP]               │
├─────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │   P&L    │  │  Stats   │  │  System  │          │
│  │  Daily   │  │  Trades  │  │  Info    │          │
│  └──────────┘  └──────────┘  └──────────┘          │
├─────────────────────────────────────────────────────┤
│  📍 Current Positions                               │
│  [Table: Symbol | Qty | Price | P&L]               │
├─────────────────────────────────────────────────────┤
│  📝 Recent Trades                                   │
│  [Table: Time | Symbol | Action | P&L]             │
├─────────────────────────────────────────────────────┤
│  📋 Logs                                            │
│  [System] [Trades] [Errors] [Signals]              │
│  [Log entries with timestamps...]                  │
└─────────────────────────────────────────────────────┘
```

## API Endpoints

The dashboard exposes REST API endpoints:

### Status & Monitoring
- `GET /api/status` - Get bot status and metrics
- `GET /api/positions` - Get current positions
- `GET /api/trades` - Get trade history
- `GET /api/pnl` - Get P&L data
- `GET /api/stats` - Get trading statistics
- `GET /api/logs?type=system&lines=100` - Get log entries

### Bot Control
- `POST /api/start` - Start the bot
- `POST /api/stop` - Stop the bot
- `POST /api/pause` - Pause trading
- `POST /api/resume` - Resume trading
- `POST /api/emergency-stop` - Emergency halt

### Configuration
- `GET /api/config` - Get current configuration
- `POST /api/config/update` - Update configuration

### Authentication
- `GET /api/auth/status` - Check auth status
- `POST /api/authenticate` - Submit authentication

## Auto-Refresh

The dashboard auto-refreshes every **2 seconds** to show:
- Latest bot status
- Updated positions
- New trades
- Fresh log entries
- Current P&L

You can disable auto-refresh by pausing the browser tab.

## Accessing from Other Devices

### Local Network Access

The dashboard listens on `0.0.0.0:8050`, making it accessible from any device on your network:

1. Find your computer's IP address:
   ```bash
   # macOS/Linux
   ifconfig | grep "inet "

   # Windows
   ipconfig
   ```

2. Access from other device:
   ```
   http://YOUR_IP_ADDRESS:8050
   ```

### Security Considerations

**⚠️ Important:**
- Dashboard has no authentication by default
- Only expose on trusted networks
- Use VPN for remote access
- Consider adding password protection

To add password protection, edit `config/config.yaml`:
```yaml
dashboard:
  authentication:
    enabled: true
    username: admin
    password: your_secure_password
```

## Troubleshooting

### Dashboard Won't Start

**Check port availability:**
```bash
lsof -i :8050
```

If port is in use, change it in `config/config.yaml`:
```yaml
dashboard:
  port: 8051  # Use different port
```

**Check Flask installation:**
```bash
pip install flask flask-cors
```

### Dashboard is Slow

**Reduce refresh rate:**

Edit the JavaScript in `dashboard.html`:
```javascript
// Change from 2000ms to 5000ms
updateInterval = setInterval(() => {
    updateDashboard();
    loadLogs();
}, 5000);  // 5 seconds instead of 2
```

**Reduce log lines:**

Modify the log fetch:
```javascript
fetch(`/api/logs?type=${currentLogType}&lines=20`)  // 20 instead of 50
```

### Can't Access from Other Devices

**Check firewall:**
```bash
# macOS - Allow incoming on port 8050
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock python3
```

**Verify dashboard is listening on 0.0.0.0:**
```bash
netstat -an | grep 8050
```

Should show `0.0.0.0.8050` not `127.0.0.1.8050`

## Keyboard Shortcuts

While focused on dashboard:
- `Space` - Start/Stop bot (when available)
- `P` - Pause bot
- `R` - Resume bot
- `Esc` - Cancel confirmation dialogs

*(Feature to be implemented)*

## Mobile Access

The dashboard is mobile-responsive and works on:
- iPhone/iPad (Safari, Chrome)
- Android (Chrome, Firefox)
- Tablets

**Optimized for:**
- Touch interactions
- Responsive layout
- Mobile data efficiency

## Best Practices

1. **Always check authentication status** before starting
2. **Review positions** before emergency stop
3. **Monitor logs** for errors and warnings
4. **Test in paper mode** thoroughly before live
5. **Keep dashboard open** when bot is running
6. **Set up alerts** via Telegram for off-screen monitoring
7. **Check daily P&L** regularly to track performance

## Advanced Usage

### Running Dashboard on Startup

Create a systemd service (Linux) or launchd plist (macOS):

**macOS launchd:**
```xml
<!-- ~/Library/LaunchAgents/com.scalpingbot.dashboard.plist -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.scalpingbot.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/scalping-bot/run_dashboard.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.scalpingbot.dashboard.plist
```

### Reverse Proxy with Nginx

For HTTPS and better security:

```nginx
server {
    listen 443 ssl;
    server_name trading.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8050;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Support

For dashboard issues:
- Check `logs/system.log`
- Review browser console (F12)
- Verify Flask is running
- Test API endpoints with curl
- See main FAQ.md for common issues

---

**Dashboard Version:** 1.0.0
**Last Updated:** 2025-10-17
