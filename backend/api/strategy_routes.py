"""
Strategy Library Flask API Routes.

RESTful API endpoints for strategy management, backtesting, ratings, and usage tracking.
"""

from flask import Blueprint, jsonify, request
from decimal import Decimal
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from backend.database.database import Database

logger = logging.getLogger(__name__)

# Create Blueprint
strategy_bp = Blueprint('strategy', __name__, url_prefix='/api/strategies')

# Global database instance
_db: Optional[Database] = None


def init_strategy_routes(db: Database):
    """
    Initialize strategy routes with database instance.

    Call this from Flask app startup.

    Args:
        db: Database instance
    """
    global _db
    _db = db
    logger.info("Strategy routes initialized")


# ============================================================================
# STRATEGY CRUD ENDPOINTS
# ============================================================================

@strategy_bp.route('', methods=['GET'])
def get_strategies():
    """
    Get all strategies with optional filtering.

    Query params:
        - category: Filter by category (e.g., trend_following)
        - complexity: Filter by complexity (beginner/intermediate/advanced)
        - is_public: Filter by public/private (true/false)
        - tags: Comma-separated tags to filter by
        - limit: Max results (default 50)
        - offset: Pagination offset (default 0)

    Returns:
        JSON array of strategy objects with metadata
    """
    try:
        # Parse query parameters
        category = request.args.get('category')
        complexity = request.args.get('complexity')
        is_public = request.args.get('is_public')
        tags = request.args.get('tags', '').split(',') if request.args.get('tags') else None
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        # Build SQL query
        conditions = []
        params = []

        if category:
            conditions.append("category = %s")
            params.append(category)

        if complexity:
            conditions.append("complexity = %s")
            params.append(complexity)

        if is_public is not None:
            conditions.append("is_public = %s")
            params.append(is_public.lower() == 'true')

        if tags:
            conditions.append("tags && %s")  # PostgreSQL array overlap operator
            params.append(tags)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT
                s.id, s.name, s.type, s.category, s.tags, s.complexity,
                s.timeframe, s.asset_class, s.is_public, s.version,
                s.total_pnl, s.total_trades, s.created_at, s.updated_at,
                COUNT(DISTINCT sr.id) as rating_count,
                AVG(sr.rating) as avg_rating,
                COUNT(DISTINCT su.user_id) as user_count
            FROM strategies s
            LEFT JOIN strategy_ratings sr ON s.id = sr.strategy_id
            LEFT JOIN strategy_usage su ON s.id = su.strategy_id
            {where_clause}
            GROUP BY s.id
            ORDER BY s.created_at DESC
            LIMIT %s OFFSET %s
        """

        params.extend([limit, offset])

        results = _db.fetch_all(query, tuple(params))

        strategies = []
        for row in results:
            strategies.append({
                'id': row[0],
                'name': row[1],
                'type': row[2],
                'category': row[3],
                'tags': row[4] if row[4] else [],
                'complexity': row[5],
                'timeframe': row[6],
                'asset_class': row[7],
                'is_public': row[8],
                'version': row[9],
                'total_pnl': float(row[10]) if row[10] else 0.0,
                'total_trades': row[11] or 0,
                'created_at': row[12].isoformat() if row[12] else None,
                'updated_at': row[13].isoformat() if row[13] else None,
                'rating_count': row[14] or 0,
                'avg_rating': float(row[15]) if row[15] else None,
                'user_count': row[16] or 0
            })

        return jsonify({
            'success': True,
            'data': strategies,
            'count': len(strategies),
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        logger.error(f"Error fetching strategies: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@strategy_bp.route('/<int:strategy_id>', methods=['GET'])
def get_strategy(strategy_id: int):
    """
    Get detailed information about a specific strategy.

    Includes backtest results, ratings, and usage statistics.

    Args:
        strategy_id: Strategy ID

    Returns:
        JSON object with complete strategy details
    """
    try:
        # Get strategy details
        strategy_query = """
            SELECT
                s.id, s.name, s.type, s.category, s.tags, s.complexity,
                s.timeframe, s.asset_class, s.is_public, s.version,
                s.config, s.status, s.mode,
                s.total_pnl, s.total_trades, s.created_at, s.updated_at
            FROM strategies s
            WHERE s.id = %s
        """

        strategy = _db.fetch_one(strategy_query, (strategy_id,))

        if not strategy:
            return jsonify({'success': False, 'error': 'Strategy not found'}), 404

        # Get latest backtest results
        backtest_query = """
            SELECT
                id, start_date, end_date, initial_capital, total_return,
                sharpe_ratio, max_drawdown, win_rate, profit_factor,
                total_trades, created_at
            FROM backtest_results
            WHERE strategy_id = %s
            ORDER BY created_at DESC
            LIMIT 5
        """

        backtests = _db.fetch_all(backtest_query, (strategy_id,))

        # Get ratings summary
        ratings_query = """
            SELECT
                COUNT(*) as count,
                AVG(rating) as avg_rating,
                COUNT(CASE WHEN rating = 5 THEN 1 END) as five_star,
                COUNT(CASE WHEN rating = 4 THEN 1 END) as four_star,
                COUNT(CASE WHEN rating = 3 THEN 1 END) as three_star,
                COUNT(CASE WHEN rating = 2 THEN 1 END) as two_star,
                COUNT(CASE WHEN rating = 1 THEN 1 END) as one_star
            FROM strategy_ratings
            WHERE strategy_id = %s
        """

        ratings = _db.fetch_one(ratings_query, (strategy_id,))

        # Get usage statistics
        usage_query = """
            SELECT
                COUNT(DISTINCT user_id) as total_users,
                SUM(total_runs) as total_runs,
                SUM(user_total_pnl) as total_pnl_all_users
            FROM strategy_usage
            WHERE strategy_id = %s
        """

        usage = _db.fetch_one(usage_query, (strategy_id,))

        # Build response
        response = {
            'id': strategy[0],
            'name': strategy[1],
            'type': strategy[2],
            'category': strategy[3],
            'tags': strategy[4] if strategy[4] else [],
            'complexity': strategy[5],
            'timeframe': strategy[6],
            'asset_class': strategy[7],
            'is_public': strategy[8],
            'version': strategy[9],
            'config': strategy[10],
            'status': strategy[11],
            'mode': strategy[12],
            'total_pnl': float(strategy[13]) if strategy[13] else 0.0,
            'total_trades': strategy[14] or 0,
            'created_at': strategy[15].isoformat() if strategy[15] else None,
            'updated_at': strategy[16].isoformat() if strategy[16] else None,
            'backtests': [
                {
                    'id': bt[0],
                    'start_date': bt[1].isoformat() if bt[1] else None,
                    'end_date': bt[2].isoformat() if bt[2] else None,
                    'initial_capital': float(bt[3]) if bt[3] else 0.0,
                    'total_return': float(bt[4]) if bt[4] else 0.0,
                    'sharpe_ratio': float(bt[5]) if bt[5] else None,
                    'max_drawdown': float(bt[6]) if bt[6] else 0.0,
                    'win_rate': float(bt[7]) if bt[7] else 0.0,
                    'profit_factor': float(bt[8]) if bt[8] else None,
                    'total_trades': bt[9] or 0,
                    'created_at': bt[10].isoformat() if bt[10] else None
                }
                for bt in backtests
            ],
            'ratings': {
                'count': ratings[0] or 0,
                'avg_rating': float(ratings[1]) if ratings[1] else None,
                'distribution': {
                    '5': ratings[2] or 0,
                    '4': ratings[3] or 0,
                    '3': ratings[4] or 0,
                    '2': ratings[5] or 0,
                    '1': ratings[6] or 0
                }
            },
            'usage': {
                'total_users': usage[0] or 0,
                'total_runs': usage[1] or 0,
                'total_pnl_all_users': float(usage[2]) if usage[2] else 0.0
            }
        }

        return jsonify({'success': True, 'data': response}), 200

    except Exception as e:
        logger.error(f"Error fetching strategy {strategy_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@strategy_bp.route('', methods=['POST'])
def create_strategy():
    """
    Create a new strategy.

    Request body:
        {
            "name": "My Strategy",
            "type": "scalping",
            "category": "trend_following",
            "tags": ["momentum", "rsi"],
            "complexity": "intermediate",
            "timeframe": "5m",
            "asset_class": "stocks",
            "is_public": false,
            "config": {...}
        }

    Returns:
        JSON with created strategy ID
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['name', 'type', 'category', 'config']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400

        # Insert strategy
        query = """
            INSERT INTO strategies (
                name, type, category, tags, complexity, timeframe,
                asset_class, is_public, version, config, status, mode
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """

        params = (
            data['name'],
            data['type'],
            data['category'],
            data.get('tags', []),
            data.get('complexity', 'intermediate'),
            data.get('timeframe', '5m'),
            data.get('asset_class', 'stocks'),
            data.get('is_public', False),
            data.get('version', '1.0.0'),
            data.get('config', {}),
            'inactive',
            'paper'
        )

        strategy_id = _db.execute(query, params)

        logger.info(f"Created strategy {strategy_id}: {data['name']}")

        return jsonify({
            'success': True,
            'data': {'id': strategy_id},
            'message': 'Strategy created successfully'
        }), 201

    except Exception as e:
        logger.error(f"Error creating strategy: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# BACKTEST ENDPOINTS
# ============================================================================

@strategy_bp.route('/<int:strategy_id>/backtests', methods=['POST'])
def create_backtest(strategy_id: int):
    """
    Create a new backtest for a strategy.

    Request body:
        {
            "start_date": "2024-01-01",
            "end_date": "2024-06-30",
            "initial_capital": 100000,
            "total_return": 0.15,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.08,
            "win_rate": 0.65,
            "profit_factor": 2.1,
            "total_trades": 150,
            "equity_curve": [...]
        }

    Returns:
        JSON with backtest ID
    """
    try:
        data = request.get_json()

        # Validate strategy exists
        strategy_check = _db.fetch_one("SELECT id FROM strategies WHERE id = %s", (strategy_id,))
        if not strategy_check:
            return jsonify({'success': False, 'error': 'Strategy not found'}), 404

        # Insert backtest
        query = """
            INSERT INTO backtest_results (
                strategy_id, start_date, end_date, initial_capital,
                total_return, sharpe_ratio, max_drawdown, win_rate,
                profit_factor, total_trades, equity_curve
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """

        params = (
            strategy_id,
            data.get('start_date'),
            data.get('end_date'),
            data.get('initial_capital', 100000),
            data.get('total_return'),
            data.get('sharpe_ratio'),
            data.get('max_drawdown'),
            data.get('win_rate'),
            data.get('profit_factor'),
            data.get('total_trades', 0),
            data.get('equity_curve')
        )

        backtest_id = _db.execute(query, params)

        logger.info(f"Created backtest {backtest_id} for strategy {strategy_id}")

        return jsonify({
            'success': True,
            'data': {'id': backtest_id},
            'message': 'Backtest created successfully'
        }), 201

    except Exception as e:
        logger.error(f"Error creating backtest: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@strategy_bp.route('/backtests', methods=['GET'])
def get_all_backtests():
    """
    Get all backtest results with optional filtering.

    Query params:
        - strategy_id: Filter by strategy
        - limit: Max results (default 50)
        - offset: Pagination offset (default 0)

    Returns:
        JSON array of backtest results
    """
    try:
        strategy_id = request.args.get('strategy_id')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        where_clause = "WHERE strategy_id = %s" if strategy_id else ""
        params = [int(strategy_id)] if strategy_id else []

        query = f"""
            SELECT
                br.id, br.strategy_id, s.name as strategy_name,
                br.start_date, br.end_date, br.initial_capital,
                br.total_return, br.sharpe_ratio, br.max_drawdown,
                br.win_rate, br.profit_factor, br.total_trades,
                br.created_at
            FROM backtest_results br
            JOIN strategies s ON br.strategy_id = s.id
            {where_clause}
            ORDER BY br.created_at DESC
            LIMIT %s OFFSET %s
        """

        params.extend([limit, offset])

        results = _db.fetch_all(query, tuple(params))

        backtests = [
            {
                'id': row[0],
                'strategy_id': row[1],
                'strategy_name': row[2],
                'start_date': row[3].isoformat() if row[3] else None,
                'end_date': row[4].isoformat() if row[4] else None,
                'initial_capital': float(row[5]) if row[5] else 0.0,
                'total_return': float(row[6]) if row[6] else 0.0,
                'sharpe_ratio': float(row[7]) if row[7] else None,
                'max_drawdown': float(row[8]) if row[8] else 0.0,
                'win_rate': float(row[9]) if row[9] else 0.0,
                'profit_factor': float(row[10]) if row[10] else None,
                'total_trades': row[11] or 0,
                'created_at': row[12].isoformat() if row[12] else None
            }
            for row in results
        ]

        return jsonify({
            'success': True,
            'data': backtests,
            'count': len(backtests),
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        logger.error(f"Error fetching backtests: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# RATING ENDPOINTS
# ============================================================================

@strategy_bp.route('/<int:strategy_id>/ratings', methods=['POST'])
def create_rating(strategy_id: int):
    """
    Create or update a rating for a strategy.

    Request body:
        {
            "user_id": 1,
            "rating": 5,
            "review": "Excellent strategy!"
        }

    Returns:
        JSON confirmation
    """
    try:
        data = request.get_json()

        # Validate strategy exists
        strategy_check = _db.fetch_one("SELECT id FROM strategies WHERE id = %s", (strategy_id,))
        if not strategy_check:
            return jsonify({'success': False, 'error': 'Strategy not found'}), 404

        # Validate rating
        rating = data.get('rating')
        if not rating or rating < 1 or rating > 5:
            return jsonify({'success': False, 'error': 'Rating must be between 1 and 5'}), 400

        # Upsert rating (insert or update if exists)
        query = """
            INSERT INTO strategy_ratings (strategy_id, user_id, rating, review)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (strategy_id, user_id)
            DO UPDATE SET rating = EXCLUDED.rating, review = EXCLUDED.review, created_at = NOW()
            RETURNING id
        """

        params = (
            strategy_id,
            data.get('user_id', 1),  # Default user_id if not provided
            rating,
            data.get('review')
        )

        rating_id = _db.execute(query, params)

        logger.info(f"Created/updated rating {rating_id} for strategy {strategy_id}")

        return jsonify({
            'success': True,
            'data': {'id': rating_id},
            'message': 'Rating submitted successfully'
        }), 201

    except Exception as e:
        logger.error(f"Error creating rating: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@strategy_bp.route('/<int:strategy_id>/ratings', methods=['GET'])
def get_ratings(strategy_id: int):
    """
    Get all ratings for a strategy.

    Returns:
        JSON array of ratings with reviews
    """
    try:
        query = """
            SELECT id, user_id, rating, review, created_at
            FROM strategy_ratings
            WHERE strategy_id = %s
            ORDER BY created_at DESC
        """

        results = _db.fetch_all(query, (strategy_id,))

        ratings = [
            {
                'id': row[0],
                'user_id': row[1],
                'rating': row[2],
                'review': row[3],
                'created_at': row[4].isoformat() if row[4] else None
            }
            for row in results
        ]

        return jsonify({
            'success': True,
            'data': ratings,
            'count': len(ratings)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching ratings: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# USAGE TRACKING ENDPOINTS
# ============================================================================

@strategy_bp.route('/<int:strategy_id>/usage', methods=['POST'])
def track_usage(strategy_id: int):
    """
    Track strategy usage by a user.

    Request body:
        {
            "user_id": 1,
            "pnl": 1250.50
        }

    Updates total runs and P&L for the user.

    Returns:
        JSON confirmation
    """
    try:
        data = request.get_json()

        # Validate strategy exists
        strategy_check = _db.fetch_one("SELECT id FROM strategies WHERE id = %s", (strategy_id,))
        if not strategy_check:
            return jsonify({'success': False, 'error': 'Strategy not found'}), 404

        # Upsert usage (insert or update if exists)
        query = """
            INSERT INTO strategy_usage (strategy_id, user_id, total_runs, user_total_pnl, last_used_at)
            VALUES (%s, %s, 1, %s, NOW())
            ON CONFLICT (strategy_id, user_id)
            DO UPDATE SET
                total_runs = strategy_usage.total_runs + 1,
                user_total_pnl = strategy_usage.user_total_pnl + EXCLUDED.user_total_pnl,
                last_used_at = NOW()
            RETURNING id
        """

        params = (
            strategy_id,
            data.get('user_id', 1),
            data.get('pnl', 0.0)
        )

        usage_id = _db.execute(query, params)

        logger.info(f"Tracked usage {usage_id} for strategy {strategy_id}")

        return jsonify({
            'success': True,
            'data': {'id': usage_id},
            'message': 'Usage tracked successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error tracking usage: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@strategy_bp.route('/<int:strategy_id>/usage', methods=['GET'])
def get_usage(strategy_id: int):
    """
    Get usage statistics for a strategy.

    Query params:
        - user_id: Get specific user's usage stats

    Returns:
        JSON with usage statistics
    """
    try:
        user_id = request.args.get('user_id')

        if user_id:
            # Get specific user's usage
            query = """
                SELECT total_runs, user_total_pnl, first_used_at, last_used_at
                FROM strategy_usage
                WHERE strategy_id = %s AND user_id = %s
            """
            result = _db.fetch_one(query, (strategy_id, int(user_id)))

            if not result:
                return jsonify({
                    'success': True,
                    'data': {
                        'total_runs': 0,
                        'user_total_pnl': 0.0,
                        'first_used_at': None,
                        'last_used_at': None
                    }
                }), 200

            return jsonify({
                'success': True,
                'data': {
                    'total_runs': result[0] or 0,
                    'user_total_pnl': float(result[1]) if result[1] else 0.0,
                    'first_used_at': result[2].isoformat() if result[2] else None,
                    'last_used_at': result[3].isoformat() if result[3] else None
                }
            }), 200
        else:
            # Get aggregate usage statistics
            query = """
                SELECT
                    COUNT(DISTINCT user_id) as total_users,
                    SUM(total_runs) as total_runs,
                    SUM(user_total_pnl) as total_pnl,
                    MIN(first_used_at) as first_used,
                    MAX(last_used_at) as last_used
                FROM strategy_usage
                WHERE strategy_id = %s
            """
            result = _db.fetch_one(query, (strategy_id,))

            return jsonify({
                'success': True,
                'data': {
                    'total_users': result[0] or 0,
                    'total_runs': result[1] or 0,
                    'total_pnl': float(result[2]) if result[2] else 0.0,
                    'first_used': result[3].isoformat() if result[3] else None,
                    'last_used': result[4].isoformat() if result[4] else None
                }
            }), 200

    except Exception as e:
        logger.error(f"Error fetching usage: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
