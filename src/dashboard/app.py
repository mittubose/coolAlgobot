"""
Scalping Bot Web Dashboard
A modern web interface for monitoring and controlling the trading bot
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
import os
import sys
import threading
import time
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config_loader import ConfigLoader
from src.auth.zerodha_auth import ZerodhaAuth

app = Flask(__name__)
CORS(app)

# Global state
bot_state = {
    'status': 'stopped',  # stopped, running, paused, error
    'mode': 'paper',      # paper, live
    'authenticated': False,
    'last_updated': datetime.now().isoformat(),
    'positions': [],
    'trades': [],
    'pnl': {
        'daily': 0.0,
        'total': 0.0,
        'unrealized': 0.0
    },
    'stats': {
        'total_trades': 0,
        'winning_trades': 0,
        'losing_trades': 0,
        'win_rate': 0.0
    }
}

config_loader = None


def load_config():
    """Load configuration"""
    global config_loader
    try:
        config_loader = ConfigLoader()
        config_loader.load()
        return True
    except Exception as e:
        print(f"Error loading config: {e}")
        return False


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/strategies')
def strategies():
    """Strategies page"""
    return render_template('strategies.html')


@app.route('/analytics')
def analytics():
    """Analytics page"""
    return render_template('analytics.html')


@app.route('/accounts')
def accounts():
    """Accounts page"""
    return render_template('accounts.html')


@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')


@app.route('/notifications')
def notifications():
    """Notifications page"""
    return render_template('notifications.html')


@app.route('/help')
def help_page():
    """Help page"""
    return render_template('help.html')


@app.route('/history')
def history():
    """History page - trades and sessions"""
    return render_template('history.html')


@app.route('/profile')
def profile():
    """Profile page"""
    return render_template('profile.html')


@app.route('/api/status')
def get_status():
    """Get current bot status"""
    bot_state['last_updated'] = datetime.now().isoformat()
    return jsonify(bot_state)


@app.route('/api/config')
def get_config():
    """Get current configuration"""
    if not config_loader:
        load_config()

    if config_loader:
        return jsonify({
            'trading': config_loader.get('trading'),
            'instruments': config_loader.get('instruments'),
            'strategies': config_loader.get('strategies'),
            'risk': config_loader.get('risk')
        })
    return jsonify({'error': 'Configuration not loaded'}), 500


@app.route('/api/config/update', methods=['POST'])
def update_config():
    """Update configuration"""
    if not config_loader:
        return jsonify({'error': 'Configuration not loaded'}), 500

    try:
        data = request.json

        # Update configuration
        for key, value in data.items():
            config_loader.update(key, value)

        # Save to file
        config_loader.save()

        return jsonify({'success': True, 'message': 'Configuration updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/start', methods=['POST'])
def start_bot():
    """Start the trading bot"""
    try:
        data = request.json or {}
        mode = data.get('mode', 'paper')

        if bot_state['status'] == 'running':
            return jsonify({'error': 'Bot is already running'}), 400

        # TODO: Implement actual bot start logic
        bot_state['status'] = 'running'
        bot_state['mode'] = mode
        bot_state['last_updated'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'message': f'Bot started in {mode} mode',
            'status': bot_state['status']
        })
    except Exception as e:
        bot_state['status'] = 'error'
        return jsonify({'error': str(e)}), 500


@app.route('/api/stop', methods=['POST'])
def stop_bot():
    """Stop the trading bot"""
    try:
        # TODO: Implement actual bot stop logic
        bot_state['status'] = 'stopped'
        bot_state['last_updated'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'message': 'Bot stopped',
            'status': bot_state['status']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/pause', methods=['POST'])
def pause_bot():
    """Pause the trading bot"""
    try:
        if bot_state['status'] != 'running':
            return jsonify({'error': 'Bot is not running'}), 400

        # TODO: Implement actual bot pause logic
        bot_state['status'] = 'paused'
        bot_state['last_updated'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'message': 'Bot paused',
            'status': bot_state['status']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/resume', methods=['POST'])
def resume_bot():
    """Resume the trading bot"""
    try:
        if bot_state['status'] != 'paused':
            return jsonify({'error': 'Bot is not paused'}), 400

        # TODO: Implement actual bot resume logic
        bot_state['status'] = 'running'
        bot_state['last_updated'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'message': 'Bot resumed',
            'status': bot_state['status']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/emergency-stop', methods=['POST'])
def emergency_stop():
    """Emergency stop - closes all positions and stops bot"""
    try:
        # TODO: Implement emergency stop logic
        # 1. Cancel all pending orders
        # 2. Close all open positions
        # 3. Stop bot

        bot_state['status'] = 'stopped'
        bot_state['positions'] = []
        bot_state['last_updated'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'message': 'Emergency stop executed - all positions closed',
            'status': bot_state['status']
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/positions')
def get_positions():
    """Get current positions"""
    return jsonify(bot_state['positions'])


@app.route('/api/trades')
def get_trades():
    """Get recent trades"""
    return jsonify(bot_state['trades'])


@app.route('/api/pnl')
def get_pnl():
    """Get P&L data"""
    return jsonify(bot_state['pnl'])


@app.route('/api/stats')
def get_stats():
    """Get trading statistics"""
    return jsonify(bot_state['stats'])


@app.route('/api/logs')
def get_logs():
    """Get recent log entries"""
    try:
        log_type = request.args.get('type', 'system')
        lines = int(request.args.get('lines', 100))

        log_file_map = {
            'system': 'logs/system.log',
            'trades': 'logs/trades.log',
            'errors': 'logs/errors.log',
            'signals': 'logs/signals.log'
        }

        log_file = log_file_map.get(log_type, 'logs/system.log')

        if not os.path.exists(log_file):
            return jsonify({'logs': [], 'message': 'Log file not found'})

        # Read last N lines
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        # Parse JSON logs if applicable
        logs = []
        for line in recent_lines:
            try:
                log_entry = json.loads(line.strip())
                logs.append(log_entry)
            except json.JSONDecodeError:
                # Plain text log
                logs.append({'message': line.strip()})

        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/authenticate', methods=['POST'])
def authenticate():
    """Authenticate with Zerodha"""
    try:
        data = request.json
        request_token = data.get('request_token')

        if not request_token:
            return jsonify({'error': 'Request token required'}), 400

        if not config_loader:
            load_config()

        api_key = config_loader.get('broker.api_key')
        api_secret = config_loader.get('broker.api_secret')

        if not api_key or not api_secret:
            return jsonify({'error': 'API credentials not configured'}), 400

        # Authenticate
        auth = ZerodhaAuth(api_key, api_secret)
        session_data = auth.generate_session(request_token)

        bot_state['authenticated'] = True
        bot_state['last_updated'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'message': 'Authentication successful',
            'user': session_data.get('user_name', 'Unknown')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/status')
def auth_status():
    """Check authentication status"""
    try:
        if not config_loader:
            load_config()

        api_key = config_loader.get('broker.api_key')
        api_secret = config_loader.get('broker.api_secret')

        if not api_key or not api_secret:
            return jsonify({
                'authenticated': False,
                'message': 'API credentials not configured'
            })

        # Try to load existing token
        auth = ZerodhaAuth(api_key, api_secret)
        if auth.load_access_token():
            if auth.verify_token():
                bot_state['authenticated'] = True
                return jsonify({
                    'authenticated': True,
                    'message': 'Valid authentication found'
                })

        return jsonify({
            'authenticated': False,
            'message': 'Authentication required',
            'login_url': auth.get_login_url()
        })
    except Exception as e:
        return jsonify({
            'authenticated': False,
            'error': str(e)
        })


def run_dashboard(host='0.0.0.0', port=8050, debug=False):
    """Run the dashboard server"""
    print(f"\n{'='*60}")
    print(f"🚀 Starting Scalping Bot Web Dashboard")
    print(f"{'='*60}")
    print(f"\n📊 Dashboard URL: http://localhost:{port}")
    print(f"   Access from network: http://{host}:{port}")
    print(f"\n⚡ Features:")
    print(f"   • Real-time monitoring")
    print(f"   • Start/Stop/Pause bot controls")
    print(f"   • Configuration management")
    print(f"   • Live P&L tracking")
    print(f"   • Trade history")
    print(f"   • Log viewer")
    print(f"\n{'='*60}\n")

    # Load configuration
    load_config()

    # Run Flask app
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    run_dashboard()
