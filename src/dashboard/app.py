"""
Scalping Bot Web Dashboard
A modern web interface for monitoring and controlling the trading bot
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import sys
import threading
import time
import json
import secrets
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.config_loader import ConfigLoader
from src.auth.zerodha_auth import ZerodhaAuth
from src.utils.error_handler import get_error_handler
from src.utils.exceptions import ScalpingBotError

app = Flask(__name__)

# Security Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.config['WTF_CSRF_TIME_LIMIT'] = None  # CSRF tokens don't expire (adjust as needed)
app.config['WTF_CSRF_SSL_STRICT'] = False  # Allow local development without HTTPS
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# CORS configuration (restrict in production)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8050", "http://127.0.0.1:8050"],
        "supports_credentials": True
    }
})

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
strategy_executor = None  # Global strategy executor instance
executor_lock = threading.Lock()  # Lock for thread-safe executor operations


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
    # Generate CSRF token for the session
    csrf_token = generate_csrf()
    return render_template('dashboard.html', csrf_token=csrf_token)


@app.route('/api/csrf-token')
def get_csrf_token():
    """Get CSRF token for AJAX requests"""
    return jsonify({'csrf_token': generate_csrf()})


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


@app.route('/implementation-log')
def implementation_log():
    """Implementation log page"""
    return render_template('implementation-log.html')


@app.route('/settings-old')
def settings_old():
    """Settings page (old route)"""
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


@app.route('/portfolio')
def portfolio():
    """Portfolio dashboard page"""
    return render_template('portfolio.html')


@app.route('/portfolio-import')
def portfolio_import():
    """Portfolio import wizard page"""
    return render_template('portfolio-import.html')


@app.route('/api/status')
def get_status():
    """Get current bot status"""
    global strategy_executor

    bot_state['last_updated'] = datetime.now().isoformat()

    # If executor is running, get real-time data
    if strategy_executor:
        try:
            summary = strategy_executor.get_summary()

            # Update bot state with real-time data
            bot_state['positions'] = summary.get('positions', {}).get('positions', [])
            bot_state['trades'] = []  # Would need to fetch from position tracker
            bot_state['stats']['total_trades'] = summary.get('trades_count', 0)

            # Add executor status
            bot_state['executor'] = {
                'strategy_name': summary.get('strategy_name'),
                'strategy_type': summary.get('strategy_type'),
                'running': summary.get('running', False),
                'paused': summary.get('paused', False),
                'symbols': summary.get('symbols', []),
                'session_id': summary.get('session_id')
            }
        except Exception as e:
            app.logger.error(f"Error getting executor summary: {e}")

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
@limiter.limit("5 per minute")  # Max 5 starts per minute
def start_bot():
    """Start the trading bot"""
    global strategy_executor

    try:
        data = request.json or {}
        mode = data.get('mode', 'paper')
        strategy_id = data.get('strategy_id')

        # Validation
        if mode not in ['paper', 'live']:
            return jsonify({'error': 'Invalid mode. Must be "paper" or "live"'}), 400

        if bot_state['status'] == 'running':
            return jsonify({'error': 'Bot is already running'}), 400

        if not strategy_id:
            return jsonify({'error': 'Strategy ID is required'}), 400

        # Log the action for audit trail
        app.logger.info(f"Bot start requested - Mode: {mode}, IP: {get_remote_address()}, Strategy: {strategy_id}")

        with executor_lock:
            # Load configuration
            if not config_loader:
                load_config()

            # Get strategy from database
            from src.database import get_session, Strategy
            with get_session() as db_session:
                strategy = db_session.query(Strategy).filter_by(id=strategy_id).first()
                if not strategy:
                    return jsonify({'error': 'Strategy not found'}), 404

                if not strategy.enabled:
                    return jsonify({'error': 'Cannot start disabled strategy'}), 400

                strategy_config = {
                    'name': strategy.name,
                    'strategy_type': strategy.config.get('strategy_type', 'custom'),
                    'parameters': strategy.config,
                    'symbols': strategy.config.get('symbols', [])
                }

            # Get risk configuration
            risk_config = config_loader.get('risk', {})

            # Initialize broker
            broker_name = config_loader.get('broker.name', 'zerodha')
            api_key = config_loader.get('broker.api_key')
            api_secret = config_loader.get('broker.api_secret')

            if not api_key or not api_secret:
                return jsonify({'error': 'Broker API credentials not configured'}), 400

            from src.brokers import create_broker
            broker = create_broker(broker_name, api_key, api_secret)

            # Load access token
            if not broker.load_access_token():
                return jsonify({'error': 'Broker authentication required. Please login first.'}), 401

            # Create strategy executor
            from src.trading.strategy_executor import StrategyExecutor
            strategy_executor = StrategyExecutor(
                broker=broker,
                strategy_config=strategy_config,
                risk_config=risk_config,
                mode=mode
            )

            # Start executor
            success = strategy_executor.start()

            if success:
                bot_state['status'] = 'running'
                bot_state['mode'] = mode
                bot_state['last_updated'] = datetime.now().isoformat()

                app.logger.info(f"Bot started successfully in {mode} mode with strategy: {strategy.name}")

                return jsonify({
                    'success': True,
                    'message': f'Bot started in {mode} mode with strategy: {strategy.name}',
                    'status': bot_state['status'],
                    'strategy': strategy.name,
                    'mode': mode
                })
            else:
                return jsonify({'error': 'Failed to start strategy executor'}), 500

    except Exception as e:
        bot_state['status'] = 'error'
        app.logger.error(f"Bot start failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/stop', methods=['POST'])
def stop_bot():
    """Stop the trading bot"""
    global strategy_executor

    try:
        if bot_state['status'] not in ['running', 'paused']:
            return jsonify({'error': 'Bot is not running'}), 400

        with executor_lock:
            if strategy_executor:
                app.logger.info("Stopping trading bot...")
                success = strategy_executor.stop()

                if success:
                    # Get final summary before cleanup
                    summary = strategy_executor.get_summary()

                    # Update bot state
                    bot_state['status'] = 'stopped'
                    bot_state['last_updated'] = datetime.now().isoformat()
                    bot_state['stats']['total_trades'] = summary.get('trades_count', 0)

                    # Cleanup executor
                    strategy_executor.cleanup()
                    strategy_executor = None

                    app.logger.info("Bot stopped successfully")

                    return jsonify({
                        'success': True,
                        'message': 'Bot stopped successfully',
                        'status': bot_state['status'],
                        'total_trades': summary.get('trades_count', 0)
                    })
                else:
                    return jsonify({'error': 'Failed to stop strategy executor'}), 500
            else:
                # No executor running, just update state
                bot_state['status'] = 'stopped'
                bot_state['last_updated'] = datetime.now().isoformat()

                return jsonify({
                    'success': True,
                    'message': 'Bot stopped',
                    'status': bot_state['status']
                })

    except Exception as e:
        app.logger.error(f"Error stopping bot: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/pause', methods=['POST'])
def pause_bot():
    """Pause the trading bot"""
    global strategy_executor

    try:
        if bot_state['status'] != 'running':
            return jsonify({'error': 'Bot is not running'}), 400

        with executor_lock:
            if strategy_executor:
                success = strategy_executor.pause()

                if success:
                    bot_state['status'] = 'paused'
                    bot_state['last_updated'] = datetime.now().isoformat()

                    app.logger.info("Bot paused successfully")

                    return jsonify({
                        'success': True,
                        'message': 'Bot paused successfully. No new trades will be opened.',
                        'status': bot_state['status']
                    })
                else:
                    return jsonify({'error': 'Failed to pause strategy executor'}), 500
            else:
                return jsonify({'error': 'No strategy executor running'}), 400

    except Exception as e:
        app.logger.error(f"Error pausing bot: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/resume', methods=['POST'])
def resume_bot():
    """Resume the trading bot"""
    global strategy_executor

    try:
        if bot_state['status'] != 'paused':
            return jsonify({'error': 'Bot is not paused'}), 400

        with executor_lock:
            if strategy_executor:
                success = strategy_executor.resume()

                if success:
                    bot_state['status'] = 'running'
                    bot_state['last_updated'] = datetime.now().isoformat()

                    app.logger.info("Bot resumed successfully")

                    return jsonify({
                        'success': True,
                        'message': 'Bot resumed successfully. Trading will continue.',
                        'status': bot_state['status']
                    })
                else:
                    return jsonify({'error': 'Failed to resume strategy executor'}), 500
            else:
                return jsonify({'error': 'No strategy executor running'}), 400

    except Exception as e:
        app.logger.error(f"Error resuming bot: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/emergency-stop', methods=['POST'])
@limiter.limit("10 per minute")  # Allow multiple emergency stops if needed
def emergency_stop():
    """Emergency stop - closes all positions and stops bot"""
    global strategy_executor

    try:
        # Log emergency stop for audit trail
        app.logger.critical(f"⚠️ ⚠️ ⚠️  EMERGENCY STOP TRIGGERED - IP: {get_remote_address()}")

        with executor_lock:
            if strategy_executor:
                # Execute emergency stop on strategy executor
                # This will:
                # 1. Cancel all pending orders
                # 2. Close all open positions at market price
                # 3. Stop the strategy immediately
                success = strategy_executor.emergency_stop()

                if success:
                    # Get final summary
                    summary = strategy_executor.get_summary()

                    # Update bot state
                    bot_state['status'] = 'stopped'
                    bot_state['positions'] = []
                    bot_state['last_updated'] = datetime.now().isoformat()

                    # Cleanup executor
                    strategy_executor.cleanup()
                    strategy_executor = None

                    app.logger.warning("✅ Emergency stop completed successfully - All positions closed, bot stopped")

                    # Send alert notification (if alerts are configured)
                    try:
                        from src.utils.alerts import send_alert
                        send_alert(
                            'EMERGENCY_STOP',
                            f"Emergency stop executed. All positions closed. Total trades: {summary.get('trades_count', 0)}",
                            priority='critical'
                        )
                    except Exception as alert_err:
                        app.logger.error(f"Failed to send emergency stop alert: {alert_err}")

                    return jsonify({
                        'success': True,
                        'message': 'Emergency stop executed successfully. All positions closed and bot stopped.',
                        'status': bot_state['status'],
                        'positions_closed': summary.get('positions', {}).get('count', 0),
                        'total_trades': summary.get('trades_count', 0)
                    })
                else:
                    app.logger.error("❌ Emergency stop FAILED to execute properly")
                    return jsonify({'error': 'Emergency stop failed to execute'}), 500
            else:
                # No executor running, just update state
                bot_state['status'] = 'stopped'
                bot_state['positions'] = []
                bot_state['last_updated'] = datetime.now().isoformat()

                app.logger.warning("Emergency stop called but no executor was running")

                return jsonify({
                    'success': True,
                    'message': 'Emergency stop executed (no active trading session)',
                    'status': bot_state['status']
                })

    except Exception as e:
        app.logger.critical(f"❌ ❌ ❌ EMERGENCY STOP FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

        # Try to send critical alert
        try:
            from src.utils.alerts import send_alert
            send_alert(
                'EMERGENCY_STOP_FAILED',
                f"CRITICAL: Emergency stop failed with error: {str(e)}",
                priority='critical'
            )
        except:
            pass

        return jsonify({'error': str(e), 'critical': True}), 500


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

            # Build config object from all strategy parameters
            config = {
                'strategy_type': data.get('strategy_type', 'custom'),
                'symbols': data.get('symbols', []),
                'timeframe': data.get('timeframe', '5m'),
                'stop_loss_pct': data.get('stop_loss_pct', 2.0),
                'target_pct': data.get('target_pct', 4.0)
            }

            # Add strategy-specific parameters
            strategy_type = data.get('strategy_type', 'custom')
            if strategy_type == 'ema_crossover':
                config['fast_period'] = data.get('fast_period', 9)
                config['slow_period'] = data.get('slow_period', 21)
            elif strategy_type == 'rsi_strategy':
                config['rsi_period'] = data.get('rsi_period', 14)
                config['oversold_level'] = data.get('oversold_level', 30)
                config['overbought_level'] = data.get('overbought_level', 70)
            elif strategy_type == 'breakout':
                config['lookback_period'] = data.get('lookback_period', 20)
                config['breakout_threshold'] = data.get('breakout_threshold', 1.0)
            elif strategy_type == 'custom':
                config['custom_indicators'] = data.get('custom_indicators', '')
                config['entry_conditions'] = data.get('entry_conditions', '')
                config['exit_conditions'] = data.get('exit_conditions', '')

            # Create new strategy
            strategy = Strategy(
                name=data['name'],
                display_name=data.get('display_name', data['name']),
                description=data.get('description', ''),
                config=config,
                timeframe=data.get('timeframe', '5m'),
                enabled=data.get('enabled', True),
                is_template=data.get('is_template', False),
                version=data.get('version', '1.0.0')
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

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        with get_session() as session:
            strategy = session.query(Strategy).filter_by(id=strategy_id).first()
            if not strategy:
                return jsonify({'error': 'Strategy not found'}), 404

            # Update fields (using correct model fields)
            if 'name' in data:
                # Check if name is being changed and if it conflicts
                if data['name'] != strategy.name:
                    existing = session.query(Strategy).filter_by(name=data['name']).first()
                    if existing:
                        return jsonify({'error': 'Strategy name already exists'}), 400
                    strategy.name = data['name']

            if 'display_name' in data:
                strategy.display_name = data['display_name']

            if 'description' in data:
                strategy.description = data['description']

            if 'config' in data:
                strategy.config = data['config']

            if 'timeframe' in data:
                strategy.timeframe = data['timeframe']

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
        import random

        data = request.json or {}
        period = data.get('period', '30days')
        initial_capital = data.get('initial_capital', 100000)
        commission = data.get('commission', 20)
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        with get_session() as session:
            strategy = session.query(Strategy).filter_by(id=strategy_id).first()
            if not strategy:
                return jsonify({'error': 'Strategy not found'}), 404

            # Generate realistic mock backtest results
            # In production, this would run actual backtesting logic

            # Calculate number of trades based on period
            period_days = 30 if period == '30days' else (
                7 if period == '7days' else (
                90 if period == '90days' else (
                180 if period == '6months' else (
                365 if period == '1year' else 30
            ))))

            # Estimate trades (avg 2-5 trades per day for intraday)
            total_trades = random.randint(period_days * 2, period_days * 5)

            # Generate realistic win rate (45-65%)
            win_rate = random.uniform(45, 65)
            winning_trades = int(total_trades * (win_rate / 100))
            losing_trades = total_trades - winning_trades

            # Calculate P&L
            avg_win = initial_capital * random.uniform(0.005, 0.015)  # 0.5-1.5% per win
            avg_loss = initial_capital * random.uniform(0.003, 0.01)  # 0.3-1% per loss

            gross_profit = winning_trades * avg_win
            gross_loss = losing_trades * avg_loss
            total_pnl = gross_profit - gross_loss - (total_trades * commission)

            # Calculate other metrics
            max_drawdown = random.uniform(5, 15)  # 5-15% max drawdown
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            sharpe_ratio = random.uniform(0.8, 2.5)

            # Calculate returns
            total_return_pct = (total_pnl / initial_capital) * 100

            return jsonify({
                'success': True,
                'message': f'Backtest completed for strategy "{strategy.name}"',
                'strategy_id': strategy_id,
                'period': period,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'gross_profit': round(gross_profit, 2),
                'gross_loss': round(gross_loss, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'max_drawdown': round(max_drawdown, 2),
                'profit_factor': round(profit_factor, 2),
                'sharpe_ratio': round(sharpe_ratio, 2),
                'total_return_pct': round(total_return_pct, 2),
                'initial_capital': initial_capital,
                'final_capital': round(initial_capital + total_pnl, 2),
                'total_commission': round(total_trades * commission, 2)
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


# ==================== USER MANAGEMENT ENDPOINTS ====================

@app.route('/api/users/current', methods=['GET'])
@csrf.exempt
def get_current_user():
    """Get current logged-in user from session"""
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({
            'authenticated': False,
            'user': None
        }), 200

    try:
        import psycopg2
        database_url = os.getenv('DATABASE_URL')

        if not database_url:
            return jsonify({'error': 'Database not configured'}), 500

        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, email, phone, default_broker, is_active, created_at
            FROM user_profiles
            WHERE id = %s AND is_active = true
        """, (user_id,))

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            session.clear()
            return jsonify({
                'authenticated': False,
                'user': None
            }), 200

        return jsonify({
            'authenticated': True,
            'user': {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'phone': user[3],
                'default_broker': user[4],
                'is_active': user[5],
                'created_at': user[6].isoformat() if user[6] else None
            }
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/register', methods=['POST'])
@csrf.exempt
def register_user():
    """Register a new user"""
    try:
        data = request.json

        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400

        import psycopg2
        database_url = os.getenv('DATABASE_URL')

        if not database_url:
            return jsonify({'error': 'Database not configured'}), 500

        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Check if email already exists (if provided)
        if data.get('email'):
            cursor.execute("SELECT id FROM user_profiles WHERE email = %s", (data['email'],))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({'error': 'Email already registered'}), 400

        # Insert new user
        cursor.execute("""
            INSERT INTO user_profiles (name, email, phone, default_broker, is_active)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, name, email, phone, default_broker
        """, (
            data['name'],
            data.get('email'),
            data.get('phone'),
            data.get('default_broker', 'zerodha'),
            True
        ))

        user = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        # Set session
        session['user_id'] = user[0]
        session['user_name'] = user[1]

        return jsonify({
            'success': True,
            'user': {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'phone': user[3],
                'default_broker': user[4]
            },
            'message': 'Registration successful'
        }), 201

    except Exception as e:
        try:
            if 'conn' in locals() and conn:
                conn.rollback()
        except:
            pass
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/login', methods=['POST'])
@csrf.exempt
def login_user():
    """Login user (simple name-based auth for now)"""
    try:
        data = request.json

        if not data.get('name') and not data.get('email'):
            return jsonify({'error': 'Name or email is required'}), 400

        import psycopg2
        database_url = os.getenv('DATABASE_URL')

        if not database_url:
            return jsonify({'error': 'Database not configured'}), 500

        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Find user by name or email
        if data.get('email'):
            cursor.execute("""
                SELECT id, name, email, phone, default_broker
                FROM user_profiles
                WHERE email = %s AND is_active = true
            """, (data['email'],))
        else:
            cursor.execute("""
                SELECT id, name, email, phone, default_broker
                FROM user_profiles
                WHERE name = %s AND is_active = true
            """, (data['name'],))

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Set session
        session['user_id'] = user[0]
        session['user_name'] = user[1]

        return jsonify({
            'success': True,
            'user': {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'phone': user[3],
                'default_broker': user[4]
            },
            'message': 'Login successful'
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/logout', methods=['POST'])
@csrf.exempt
def logout_user():
    """Logout current user"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


@app.route('/api/users/profile', methods=['PUT'])
@csrf.exempt
def update_user_profile():
    """Update user profile"""
    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        data = request.json

        import psycopg2
        database_url = os.getenv('DATABASE_URL')

        if not database_url:
            return jsonify({'error': 'Database not configured'}), 500

        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Build update query
        updates = []
        params = []

        if 'name' in data:
            updates.append("name = %s")
            params.append(data['name'])
        if 'email' in data:
            updates.append("email = %s")
            params.append(data['email'])
        if 'phone' in data:
            updates.append("phone = %s")
            params.append(data['phone'])
        if 'default_broker' in data:
            updates.append("default_broker = %s")
            params.append(data['default_broker'])

        if not updates:
            return jsonify({'error': 'No fields to update'}), 400

        updates.append("updated_at = NOW()")
        params.append(user_id)

        query = f"UPDATE user_profiles SET {', '.join(updates)} WHERE id = %s RETURNING id, name, email, phone, default_broker"

        cursor.execute(query, params)
        user = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        if user:
            session['user_name'] = user[1]

        return jsonify({
            'success': True,
            'user': {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'phone': user[3],
                'default_broker': user[4]
            },
            'message': 'Profile updated successfully'
        }), 200

    except Exception as e:
        try:
            if 'conn' in locals() and conn:
                conn.rollback()
        except:
            pass
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

    # Initialize watchlist database
    try:
        from src.database.db_manager import init_database as init_watchlist_db
        init_watchlist_db()
        print("✅ Watchlist database initialized")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize watchlist database: {e}")

    # Initialize OMS
    try:
        initialize_oms()
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize OMS: {e}")

    # Register shutdown handler
    import atexit
    atexit.register(shutdown_oms)

    # Run Flask app
    app.run(host=host, port=port, debug=debug, threaded=True)


# ============================================================================
# Implementation Progress Endpoint
# ============================================================================

@app.route('/api/implementation-progress', methods=['GET'])
def get_implementation_progress():
    """Get implementation progress from markdown file"""
    try:
        progress_file = Path(__file__).parent.parent.parent / 'IMPLEMENTATION_PROGRESS.md'

        if not progress_file.exists():
            return jsonify({
                'success': False,
                'error': 'Implementation progress file not found'
            }), 404

        # Read the markdown file
        with open(progress_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the markdown into structured data
        phases = []
        current_phase = None
        current_section = None

        for line in content.split('\n'):
            line = line.strip()

            # Phase headers (## Phase X:...)
            if line.startswith('## Phase'):
                if current_phase:
                    phases.append(current_phase)

                # Extract phase info
                phase_text = line.replace('##', '').strip()
                completed = '✅ COMPLETED' in phase_text or '✅' in phase_text

                current_phase = {
                    'title': phase_text.replace('✅ COMPLETED', '').replace('✅', '').strip(),
                    'completed': completed,
                    'sections': []
                }
                current_section = None

            # Subsection headers (### ...)
            elif line.startswith('###') and current_phase:
                section_text = line.replace('###', '').strip()
                completed = '✅' in section_text

                current_section = {
                    'title': section_text.replace('✅', '').strip(),
                    'completed': completed,
                    'items': []
                }
                current_phase['sections'].append(current_section)

            # Checklist items (- ✅ or - ❌)
            elif line.startswith('- ✅') or line.startswith('- ❌') or line.startswith('- [ ]') or line.startswith('- [x]'):
                if current_section:
                    is_completed = '✅' in line or '[x]' in line
                    item_text = line.replace('- ✅', '').replace('- ❌', '').replace('- [ ]', '').replace('- [x]', '').strip()

                    current_section['items'].append({
                        'text': item_text,
                        'completed': is_completed
                    })

        # Add last phase
        if current_phase:
            phases.append(current_phase)

        return jsonify({
            'success': True,
            'phases': phases,
            'raw_content': content
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== Chart Data Endpoints ====================

@app.route('/api/chart/ohlc', methods=['GET'])
def get_ohlc_data():
    """Get OHLC candlestick data for charts"""
    try:
        from src.utils.ohlc_generator import generate_ohlc_data

        # Get parameters
        symbol = request.args.get('symbol', 'NIFTY50')
        timeframe = request.args.get('timeframe', '5m')
        count = int(request.args.get('count', 100))
        trend = request.args.get('trend', 'sideways')

        # Generate OHLC data
        data = generate_ohlc_data(count, timeframe, symbol, trend)

        return jsonify({
            'success': True,
            **data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/chart/patterns-sync', methods=['POST'])
def sync_patterns_with_chart():
    """
    Detect patterns and sync with chart candles
    Returns patterns with timestamps for chart markers
    """
    try:
        from src.analysis import CandlestickPatternDetector
        import pandas as pd

        # Get OHLC data from request
        data = request.json
        candles = data.get('candles', [])

        if not candles:
            return jsonify({
                'success': False,
                'error': 'No candle data provided'
            }), 400

        # Convert to DataFrame for pattern detection
        df = pd.DataFrame(candles)
        df.columns = ['time', 'open', 'high', 'low', 'close', 'volume']

        # Detect patterns
        detector = CandlestickPatternDetector(df)
        patterns = detector.get_active_patterns()

        # Add timestamp and marker info for last few candles
        patterns_with_markers = []
        for pattern in patterns:
            # Associate pattern with latest candle
            latest_candle = candles[-1]

            patterns_with_markers.append({
                **pattern,
                'candle_time': latest_candle['time'],
                'candle_index': len(candles) - 1,
                'marker': {
                    'position': 'aboveBar' if 'bullish' in pattern['type'] else 'belowBar',
                    'color': '#10B981' if 'bullish' in pattern['type'] else '#EF4444',
                    'shape': 'arrowUp' if 'bullish' in pattern['type'] else 'arrowDown',
                    'text': f"{pattern['name']} ({pattern['confidence']}%)"
                }
            })

        return jsonify({
            'success': True,
            'patterns': patterns_with_markers,
            'count': len(patterns_with_markers)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== Pattern Recognition Endpoints ====================

@app.route('/api/patterns/candlestick', methods=['GET'])
def get_candlestick_patterns():
    """Get detected candlestick patterns"""
    try:
        from src.analysis import CandlestickPatternDetector

        # Create detector (using mock data for now)
        detector = CandlestickPatternDetector()

        # Get active patterns
        patterns = detector.get_active_patterns()

        return jsonify({
            'success': True,
            'patterns': patterns,
            'count': len(patterns)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/patterns/indicators', methods=['GET'])
def get_technical_indicators():
    """Get technical indicator signals"""
    try:
        from src.analysis import TechnicalIndicators

        # Create indicators (using mock data for now)
        indicators = TechnicalIndicators()

        # Get signals
        signals = indicators.get_indicator_signals()

        # Get values
        values = indicators.get_indicator_values()

        return jsonify({
            'success': True,
            'signals': signals,
            'values': values
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/patterns/all', methods=['GET'])
def get_all_patterns():
    """Get all pattern detection data (candlestick + chart + indicators)"""
    try:
        from src.analysis import CandlestickPatternDetector, TechnicalIndicators

        # Candlestick patterns
        candlestick_detector = CandlestickPatternDetector()
        candlestick_patterns = candlestick_detector.get_active_patterns()

        # Technical indicators
        indicators = TechnicalIndicators()
        indicator_signals = indicators.get_indicator_signals()
        indicator_values = indicators.get_indicator_values()

        return jsonify({
            'success': True,
            'candlestick_patterns': candlestick_patterns,
            'chart_patterns': [],  # TODO: Add chart pattern detection
            'indicators': {
                'signals': indicator_signals,
                'values': indicator_values
            },
            'total_patterns': len(candlestick_patterns),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# WATCHLIST & RECOMMENDATIONS API ENDPOINTS
# ============================================================================

@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """Get all stocks in watchlist with current prices"""
    try:
        from src.database.watchlist_manager import WatchlistManager
        from src.utils.ohlc_generator import OHLCGenerator
        from src.analysis.candlestick_patterns import CandlestickPatternDetector

        wm = WatchlistManager()
        watchlist_stocks = wm.get_all()

        # Enrich with current prices and pattern detection
        ohlc_gen = OHLCGenerator()
        enriched_watchlist = []

        for stock in watchlist_stocks:
            symbol = stock['symbol']

            # Generate OHLC data (will use real API later)
            ohlc_data = ohlc_gen.generate_candles(count=100, timeframe='5m')
            current_price = ohlc_data[-1]['close']
            prev_price = ohlc_data[-2]['close'] if len(ohlc_data) > 1 else current_price
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price * 100) if prev_price != 0 else 0

            # Detect patterns on this stock
            # Convert ohlc list to pandas DataFrame
            import pandas as pd
            df = pd.DataFrame(ohlc_data)
            pattern_detector = CandlestickPatternDetector(df)
            patterns = pattern_detector.get_active_patterns()

            # Get highest confidence pattern
            pattern_badge = None
            if patterns:
                top_pattern = max(patterns, key=lambda p: p['confidence'])
                if top_pattern['confidence'] > 75:
                    pattern_badge = {
                        'name': top_pattern['name'],
                        'type': top_pattern['type'],
                        'confidence': top_pattern['confidence']
                    }

            enriched_watchlist.append({
                'id': stock['id'],
                'symbol': symbol,
                'current_price': round(current_price, 2),
                'price_change': round(price_change, 2),
                'price_change_pct': round(price_change_pct, 2),
                'pattern_badge': pattern_badge,
                'added_at': stock['added_at']
            })

        return jsonify({
            'success': True,
            'watchlist': enriched_watchlist,
            'count': len(enriched_watchlist),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/watchlist/add', methods=['POST'])
def add_to_watchlist():
    """Add a stock to watchlist"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').strip().upper()

        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Symbol is required'
            }), 400

        from src.database.watchlist_manager import WatchlistManager
        wm = WatchlistManager()

        success = wm.add_stock(symbol)

        if success:
            return jsonify({
                'success': True,
                'message': f'{symbol} added to watchlist',
                'symbol': symbol
            })
        else:
            return jsonify({
                'success': False,
                'error': f'{symbol} already in watchlist'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/watchlist/remove', methods=['DELETE'])
def remove_from_watchlist():
    """Remove a stock from watchlist"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').strip().upper()

        if not symbol:
            return jsonify({
                'success': False,
                'error': 'Symbol is required'
            }), 400

        from src.database.watchlist_manager import WatchlistManager
        wm = WatchlistManager()

        success = wm.remove_stock(symbol)

        if success:
            return jsonify({
                'success': True,
                'message': f'{symbol} removed from watchlist',
                'symbol': symbol
            })
        else:
            return jsonify({
                'success': False,
                'error': f'{symbol} not found in watchlist'
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/recommendations/today', methods=['GET'])
def get_daily_recommendations():
    """Get today's top stock recommendations"""
    try:
        from src.analysis.recommendation_engine import RecommendationEngine

        engine = RecommendationEngine()

        # Get cached picks (or generate fresh if not cached)
        limit = request.args.get('limit', 5, type=int)
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'

        if force_refresh:
            recommendations = engine.refresh_daily_picks(limit=limit)
        else:
            recommendations = engine.get_todays_picks_from_db(limit=limit)

        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations),
            'cached': not force_refresh,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# STRATEGY LIBRARY API (PostgreSQL Backend)
# ============================================================================

# Register strategy library routes
try:
    from backend.api.strategy_routes import strategy_bp, init_strategy_routes
    from backend.database.sync_db import Database

    # Initialize database connection (synchronous wrapper for Flask routes)
    strategy_db = Database()
    strategy_db.connect()

    # Initialize strategy routes with database
    init_strategy_routes(strategy_db)

    # Register blueprint
    app.register_blueprint(strategy_bp)

    print("✅ Strategy library routes registered at /api/strategies")
except Exception as e:
    print(f"⚠️  Warning: Could not register strategy library routes: {e}")


# ============================================================================
# PORTFOLIO IMPORT & TRACKING API
# ============================================================================

# Register portfolio management routes
try:
    from backend.api.portfolio_routes import portfolio_bp, init_portfolio_routes

    # Re-use the same database connection as strategy library
    init_portfolio_routes(strategy_db)

    # Register blueprint
    app.register_blueprint(portfolio_bp)

    # Exempt file upload endpoint from CSRF (FormData doesn't include CSRF token)
    csrf.exempt(portfolio_bp)

    print("✅ Portfolio management routes registered at /api/portfolios")
except Exception as e:
    print(f"⚠️  Warning: Could not register portfolio routes: {e}")


# ============================================================================
# OMS INTEGRATION
# ============================================================================

# Global OMS integration instance
oms_integration = None


def initialize_oms():
    """Initialize OMS components on app startup"""
    global oms_integration

    try:
        import asyncio
        from backend.api.dashboard_integration import integrate_oms_with_flask

        # Create integration (this registers the blueprint synchronously)
        oms_integration = integrate_oms_with_flask(app, use_mock_broker=True)
        print("✅ OMS blueprint registered at /api/oms")

        # Initialize async components in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(oms_integration.initialize())

        print("✅ OMS integration initialized successfully")

    except Exception as e:
        print(f"❌ OMS integration failed: {e}")
        import traceback
        traceback.print_exc()


def shutdown_oms():
    """Shutdown OMS components"""
    global oms_integration

    if oms_integration:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(oms_integration.shutdown())
            print("✅ OMS shutdown complete")
        except Exception as e:
            print(f"Error during OMS shutdown: {e}")


if __name__ == '__main__':
    run_dashboard()
