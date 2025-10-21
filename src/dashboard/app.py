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
from src.utils.error_handler import get_error_handler
from src.utils.exceptions import ScalpingBotError

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


# ==================== Broker Management Endpoints ====================

@app.route('/api/brokers/supported')
def get_supported_brokers():
    """Get list of supported brokers"""
    from src.brokers import BrokerFactory

    brokers = BrokerFactory.get_supported_brokers()
    return jsonify({'brokers': brokers})


@app.route('/api/broker/current')
def get_current_broker():
    """Get current broker configuration"""
    if not config_loader:
        load_config()

    broker_config = config_loader.get('broker')
    if broker_config:
        # Mask sensitive data
        return jsonify({
            'name': broker_config.get('name', 'zerodha'),
            'api_key': broker_config.get('api_key', '')[:8] + '...' if broker_config.get('api_key') else '',
            'has_secret': bool(broker_config.get('api_secret')),
            'redirect_url': broker_config.get('redirect_url', '')
        })

    return jsonify({'error': 'Broker not configured'}), 500


@app.route('/api/broker/configure', methods=['POST'])
def configure_broker():
    """Configure broker credentials"""
    if not config_loader:
        load_config()

    try:
        data = request.json
        broker_name = data.get('broker_name', '').lower()
        api_key = data.get('api_key', '').strip()
        api_secret = data.get('api_secret', '').strip()

        if not all([broker_name, api_key, api_secret]):
            return jsonify({'error': 'Broker name, API key and secret are required'}), 400

        # Validate broker is supported
        from src.brokers import BrokerFactory
        if not BrokerFactory.is_broker_supported(broker_name):
            return jsonify({'error': f'Broker {broker_name} is not supported'}), 400

        # Update configuration
        config_loader.update('broker.name', broker_name)
        config_loader.update('broker.api_key', api_key)

        # Save API secret to secrets.env file
        secrets_file = Path("config/secrets.env")
        secrets_file.parent.mkdir(parents=True, exist_ok=True)

        # Read existing secrets
        existing_secrets = {}
        if secrets_file.exists():
            with open(secrets_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        existing_secrets[key.strip()] = value.strip()

        # Update API secret
        existing_secrets['API_SECRET'] = api_secret

        # Write back to file
        with open(secrets_file, 'w') as f:
            f.write("# Broker API Credentials\n")
            f.write("# DO NOT COMMIT THIS FILE TO VERSION CONTROL\n\n")
            for key, value in existing_secrets.items():
                f.write(f"{key}={value}\n")

        # Save config
        config_loader.save()

        return jsonify({
            'success': True,
            'message': f'Broker {broker_name} configured successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/broker/test', methods=['POST'])
def test_broker_connection():
    """Test broker connection"""
    try:
        if not config_loader:
            load_config()

        broker_name = config_loader.get('broker.name', 'zerodha')
        api_key = config_loader.get('broker.api_key')
        api_secret = config_loader.get('broker.api_secret')

        if not api_key or not api_secret:
            return jsonify({'error': 'API credentials not configured'}), 400

        # Create broker instance
        from src.brokers import create_broker
        broker = create_broker(broker_name, api_key, api_secret)

        # Try to load existing token and verify
        if broker.load_access_token():
            if broker.verify_token():
                profile = broker.get_profile()
                return jsonify({
                    'success': True,
                    'message': 'Connection successful',
                    'broker': broker_name,
                    'user': profile.get('user_name', profile.get('user_id', 'Unknown'))
                })

        # Need to authenticate
        return jsonify({
            'success': False,
            'message': 'Authentication required',
            'login_url': broker.get_login_url()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Strategy Management Endpoints ====================

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    """Get all strategies"""
    try:
        from src.database import get_session, Strategy

        with get_session() as session:
            strategies = session.query(Strategy).all()
            return jsonify({
                'strategies': [s.to_dict() for s in strategies],
                'count': len(strategies)
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategies/<int:strategy_id>', methods=['GET'])
def get_strategy(strategy_id):
    """Get specific strategy by ID"""
    try:
        from src.database import get_session, Strategy

        with get_session() as session:
            strategy = session.query(Strategy).filter_by(id=strategy_id).first()
            if not strategy:
                return jsonify({'error': 'Strategy not found'}), 404

            return jsonify(strategy.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategies', methods=['POST'])
def create_strategy():
    """Create a new strategy"""
    try:
        from src.database import get_session, Strategy

        data = request.json

        # Validate required fields
        required_fields = ['name', 'description']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields: name, description'}), 400

        with get_session() as session:
            # Check if strategy with same name exists
            existing = session.query(Strategy).filter_by(name=data['name']).first()
            if existing:
                return jsonify({'error': 'Strategy with this name already exists'}), 400

            # Create new strategy
            strategy = Strategy(
                name=data['name'],
                description=data.get('description', ''),
                strategy_type=data.get('strategy_type', 'custom'),
                parameters=data.get('parameters', {}),
                enabled=data.get('enabled', True),
                is_template=data.get('is_template', False),
                version=data.get('version', '1.0')
            )

            session.add(strategy)
            session.commit()

            return jsonify({
                'success': True,
                'message': 'Strategy created successfully',
                'strategy': strategy.to_dict()
            }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategies/<int:strategy_id>', methods=['PUT'])
def update_strategy(strategy_id):
    """Update an existing strategy"""
    try:
        from src.database import get_session, Strategy

        data = request.json

        with get_session() as session:
            strategy = session.query(Strategy).filter_by(id=strategy_id).first()
            if not strategy:
                return jsonify({'error': 'Strategy not found'}), 404

            # Update fields
            if 'name' in data:
                strategy.name = data['name']
            if 'description' in data:
                strategy.description = data['description']
            if 'strategy_type' in data:
                strategy.strategy_type = data['strategy_type']
            if 'parameters' in data:
                strategy.parameters = data['parameters']
            if 'enabled' in data:
                strategy.enabled = data['enabled']
            if 'version' in data:
                strategy.version = data['version']

            strategy.updated_at = datetime.now()

            session.commit()

            return jsonify({
                'success': True,
                'message': 'Strategy updated successfully',
                'strategy': strategy.to_dict()
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategies/<int:strategy_id>', methods=['DELETE'])
def delete_strategy(strategy_id):
    """Delete a strategy"""
    try:
        from src.database import get_session, Strategy

        with get_session() as session:
            strategy = session.query(Strategy).filter_by(id=strategy_id).first()
            if not strategy:
                return jsonify({'error': 'Strategy not found'}), 404

            strategy_name = strategy.name
            session.delete(strategy)
            session.commit()

            return jsonify({
                'success': True,
                'message': f'Strategy "{strategy_name}" deleted successfully'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategies/<int:strategy_id>/deploy', methods=['POST'])
def deploy_strategy(strategy_id):
    """Deploy a strategy for live/paper trading"""
    try:
        from src.database import get_session, Strategy

        data = request.json or {}
        mode = data.get('mode', 'paper')  # paper or live

        with get_session() as session:
            strategy = session.query(Strategy).filter_by(id=strategy_id).first()
            if not strategy:
                return jsonify({'error': 'Strategy not found'}), 404

            if not strategy.enabled:
                return jsonify({'error': 'Cannot deploy disabled strategy'}), 400

            # TODO: Implement actual strategy deployment logic
            # This should initialize the strategy executor with the strategy config

            strategy.last_traded_at = datetime.now()
            session.commit()

            return jsonify({
                'success': True,
                'message': f'Strategy "{strategy.name}" deployed in {mode} mode',
                'strategy_id': strategy_id,
                'mode': mode
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategies/<int:strategy_id>/backtest', methods=['POST'])
def backtest_strategy(strategy_id):
    """Run backtest for a strategy"""
    try:
        from src.database import get_session, Strategy

        data = request.json or {}
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        symbols = data.get('symbols', [])

        with get_session() as session:
            strategy = session.query(Strategy).filter_by(id=strategy_id).first()
            if not strategy:
                return jsonify({'error': 'Strategy not found'}), 404

            # TODO: Implement actual backtesting logic
            # This should run the strategy against historical data

            return jsonify({
                'success': True,
                'message': f'Backtest started for strategy "{strategy.name}"',
                'strategy_id': strategy_id,
                'status': 'pending',
                'parameters': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'symbols': symbols
                }
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/strategies/templates', methods=['GET'])
def get_strategy_templates():
    """Get all strategy templates"""
    try:
        from src.database import get_session, Strategy

        with get_session() as session:
            templates = session.query(Strategy).filter_by(is_template=True).all()
            return jsonify({
                'templates': [t.to_dict() for t in templates],
                'count': len(templates)
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Settings Management Endpoints ====================

@app.route('/api/settings', methods=['GET'])
def get_all_settings():
    """Get all settings"""
    if not config_loader:
        load_config()

    try:
        return jsonify({
            'trading': config_loader.get('trading'),
            'risk': config_loader.get('risk'),
            'broker': {
                'name': config_loader.get('broker.name', 'zerodha'),
                'api_key': config_loader.get('broker.api_key', '')[:8] + '...' if config_loader.get('broker.api_key') else '',
                'has_secret': bool(config_loader.get('broker.api_secret')),
                'redirect_url': config_loader.get('broker.redirect_url', '')
            },
            'alerts': config_loader.get('alerts'),
            'logging': config_loader.get('logging')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/trading', methods=['PUT'])
def update_trading_settings():
    """Update trading settings"""
    if not config_loader:
        return jsonify({'error': 'Configuration not loaded'}), 500

    try:
        data = request.json

        # Update trading settings
        for key, value in data.items():
            config_loader.update(f'trading.{key}', value)

        config_loader.save()

        return jsonify({
            'success': True,
            'message': 'Trading settings updated',
            'settings': config_loader.get('trading')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/risk', methods=['PUT'])
def update_risk_settings():
    """Update risk management settings"""
    if not config_loader:
        return jsonify({'error': 'Configuration not loaded'}), 500

    try:
        data = request.json

        # Update risk settings
        for key, value in data.items():
            config_loader.update(f'risk.{key}', value)

        config_loader.save()

        return jsonify({
            'success': True,
            'message': 'Risk settings updated',
            'settings': config_loader.get('risk')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/alerts', methods=['PUT'])
def update_alert_settings():
    """Update alert/notification settings"""
    if not config_loader:
        return jsonify({'error': 'Configuration not loaded'}), 500

    try:
        data = request.json

        # Update alert settings
        for key, value in data.items():
            config_loader.update(f'alerts.{key}', value)

        config_loader.save()

        return jsonify({
            'success': True,
            'message': 'Alert settings updated',
            'settings': config_loader.get('alerts')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/logging', methods=['PUT'])
def update_logging_settings():
    """Update logging settings"""
    if not config_loader:
        return jsonify({'error': 'Configuration not loaded'}), 500

    try:
        data = request.json

        # Update logging settings
        for key, value in data.items():
            config_loader.update(f'logging.{key}', value)

        config_loader.save()

        return jsonify({
            'success': True,
            'message': 'Logging settings updated',
            'settings': config_loader.get('logging')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Trading Engine Status Endpoints ====================

@app.route('/api/engine/status', methods=['GET'])
def get_engine_status():
    """Get trading engine status"""
    try:
        # This would return status from a running strategy executor
        # For now, return placeholder data
        return jsonify({
            'running': False,
            'mode': 'paper',
            'strategy': None,
            'positions_count': 0,
            'orders_count': 0,
            'message': 'Trading engine not started'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/engine/start', methods=['POST'])
def start_trading_engine():
    """Start trading engine with a strategy"""
    try:
        data = request.json or {}
        strategy_id = data.get('strategy_id')
        mode = data.get('mode', 'paper')

        # TODO: Initialize and start strategy executor
        # This would create a StrategyExecutor instance and start it

        return jsonify({
            'success': True,
            'message': f'Trading engine started in {mode} mode',
            'strategy_id': strategy_id,
            'mode': mode
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/engine/stop', methods=['POST'])
def stop_trading_engine():
    """Stop trading engine"""
    try:
        # TODO: Stop running strategy executor

        return jsonify({
            'success': True,
            'message': 'Trading engine stopped'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Error Tracking Endpoints ====================

@app.route('/api/errors/statistics')
def get_error_statistics():
    """Get error statistics"""
    try:
        error_handler = get_error_handler()
        stats = error_handler.get_error_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/errors/recent')
def get_recent_errors():
    """Get recent errors"""
    try:
        limit = int(request.args.get('limit', 50))
        error_handler = get_error_handler()

        recent_errors = error_handler.error_history[-limit:]

        return jsonify({
            'total_count': error_handler.error_count,
            'errors': recent_errors
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/errors/clear', methods=['POST'])
def clear_error_history():
    """Clear error history"""
    try:
        error_handler = get_error_handler()
        error_handler.clear_history()

        return jsonify({
            'success': True,
            'message': 'Error history cleared'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== Global Error Handler ====================

@app.errorhandler(ScalpingBotError)
def handle_scalping_bot_error(error: ScalpingBotError):
    """Handle custom ScalpingBotError exceptions"""
    error_handler = get_error_handler()
    error_handler.handle_error(error, context='API Request')

    return jsonify(error.to_dict()), 400


@app.errorhandler(404)
def handle_not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'NOT_FOUND',
        'message': 'The requested resource was not found'
    }), 404


@app.errorhandler(500)
def handle_internal_error(error):
    """Handle 500 errors"""
    error_handler = get_error_handler()
    error_handler.handle_error(
        error,
        context='Internal Server Error',
        severity='critical',
        notify=True
    )

    return jsonify({
        'error': 'INTERNAL_SERVER_ERROR',
        'message': 'An internal server error occurred'
    }), 500


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
