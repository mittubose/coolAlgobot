"""
Portfolio Management API Routes
Handles portfolio CRUD, CSV import, P&L calculation, and risk scoring
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Optional
import os
import uuid
from datetime import datetime

# CSV Parser
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from portfolio.csv_parser import CSVImportParser


# Create Blueprint
portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolios')

# Global database connection (will be injected)
db_connection = None


def init_portfolio_routes(database):
    """Initialize routes with database connection"""
    global db_connection
    db_connection = database


# ==================== PORTFOLIO CRUD ====================

@portfolio_bp.route('', methods=['GET'])
def get_portfolios():
    """
    Get all portfolios

    Query params:
    - status: Filter by status (active, closed, archived)
    - broker: Filter by broker

    Response:
        {
            "success": true,
            "portfolios": [
                {
                    "id": 1,
                    "name": "Zerodha Main",
                    "broker": "zerodha",
                    "current_value": 125000.00,
                    "total_pnl": 25000.00,
                    "total_return_pct": 25.00,
                    "holdings_count": 5,
                    "trades_count": 23
                }
            ]
        }
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()

        # Build query with filters
        query = "SELECT * FROM portfolio_summary WHERE 1=1"
        params = []

        # Filter by status
        status = request.args.get('status')
        if status:
            query += " AND status = %s"
            params.append(status)

        # Filter by broker
        broker = request.args.get('broker')
        if broker:
            query += " AND broker = %s"
            params.append(broker)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        portfolios = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.close()

        return jsonify({
            'success': True,
            'portfolios': portfolios,
            'count': len(portfolios)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/<int:portfolio_id>', methods=['GET'])
def get_portfolio(portfolio_id: int):
    """
    Get detailed portfolio info

    Response:
        {
            "success": true,
            "portfolio": {...},
            "holdings": [...],
            "recent_trades": [...],
            "performance": {...}
        }
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()

        # Get portfolio details
        cursor.execute("""
            SELECT * FROM portfolios WHERE id = %s
        """, (portfolio_id,))

        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404

        columns = [desc[0] for desc in cursor.description]
        portfolio = dict(zip(columns, cursor.fetchone()))

        # Get holdings
        cursor.execute("""
            SELECT * FROM holdings
            WHERE portfolio_id = %s AND quantity > 0
            ORDER BY weight DESC
        """, (portfolio_id,))
        columns = [desc[0] for desc in cursor.description]
        holdings = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Get recent trades (last 10)
        cursor.execute("""
            SELECT * FROM portfolio_trades
            WHERE portfolio_id = %s
            ORDER BY trade_date DESC, id DESC
            LIMIT 10
        """, (portfolio_id,))
        columns = [desc[0] for desc in cursor.description]
        recent_trades = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Get latest snapshot for performance
        cursor.execute("""
            SELECT * FROM portfolio_snapshots
            WHERE portfolio_id = %s
            ORDER BY snapshot_date DESC
            LIMIT 1
        """, (portfolio_id,))

        performance = None
        if cursor.rowcount > 0:
            columns = [desc[0] for desc in cursor.description]
            performance = dict(zip(columns, cursor.fetchone()))

        cursor.close()

        return jsonify({
            'success': True,
            'portfolio': portfolio,
            'holdings': holdings,
            'holdings_count': len(holdings),
            'recent_trades': recent_trades,
            'performance': performance
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('', methods=['POST'])
def create_portfolio():
    """
    Create new portfolio

    Request body:
        {
            "name": "Zerodha Main",
            "description": "Primary trading account",
            "type": "stocks",
            "broker": "zerodha",
            "account_number": "ABC123",
            "initial_capital": 100000.00
        }

    Response:
        {
            "success": true,
            "portfolio": {...}
        }
    """
    try:
        data = request.json
        required_fields = ['name', 'initial_capital']

        # Validate required fields
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400

        conn = db_connection.get_connection()
        cursor = conn.cursor()

        # Insert portfolio
        cursor.execute("""
            INSERT INTO portfolios (
                name, description, type, broker, account_number, initial_capital, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data['name'],
            data.get('description'),
            data.get('type', 'stocks'),
            data.get('broker'),
            data.get('account_number'),
            data['initial_capital'],
            'active'
        ))

        portfolio_id = cursor.fetchone()[0]
        conn.commit()

        # Fetch created portfolio
        cursor.execute("SELECT * FROM portfolios WHERE id = %s", (portfolio_id,))
        columns = [desc[0] for desc in cursor.description]
        portfolio = dict(zip(columns, cursor.fetchone()))

        cursor.close()

        return jsonify({
            'success': True,
            'portfolio': portfolio,
            'message': 'Portfolio created successfully'
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/<int:portfolio_id>', methods=['PUT'])
def update_portfolio(portfolio_id: int):
    """
    Update portfolio details

    Request body:
        {
            "name": "Updated Name",
            "description": "Updated description",
            "status": "active"
        }
    """
    try:
        data = request.json
        conn = db_connection.get_connection()
        cursor = conn.cursor()

        # Build update query dynamically
        update_fields = []
        params = []

        allowed_fields = ['name', 'description', 'type', 'broker', 'account_number', 'status']
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])

        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400

        params.append(portfolio_id)
        query = f"UPDATE portfolios SET {', '.join(update_fields)} WHERE id = %s"

        cursor.execute(query, params)
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404

        # Fetch updated portfolio
        cursor.execute("SELECT * FROM portfolios WHERE id = %s", (portfolio_id,))
        columns = [desc[0] for desc in cursor.description]
        portfolio = dict(zip(columns, cursor.fetchone()))

        cursor.close()

        return jsonify({
            'success': True,
            'portfolio': portfolio,
            'message': 'Portfolio updated successfully'
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/<int:portfolio_id>', methods=['DELETE'])
def delete_portfolio(portfolio_id: int):
    """
    Delete portfolio (cascades to trades, holdings, etc.)
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM portfolios WHERE id = %s", (portfolio_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404

        cursor.close()

        return jsonify({
            'success': True,
            'message': 'Portfolio deleted successfully'
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== CSV IMPORT ====================

@portfolio_bp.route('/<int:portfolio_id>/import', methods=['POST'])
def import_csv(portfolio_id: int):
    """
    Import trades from CSV/Excel file with deduplication

    Form data:
    - file: CSV or Excel file (.csv, .xlsx, .xls)
    - broker: Broker name (zerodha, groww, upstox, icici, generic)

    Response:
        {
            "success": true,
            "import_stats": {
                "total_rows": 150,
                "imported": 120,
                "duplicates_skipped": 28,
                "invalid": 2,
                "import_batch_id": "uuid",
                "start_date": "2024-01-01",
                "end_date": "2024-10-26"
            },
            "deduplication": {
                "exact_duplicates": 28,
                "similar_trades": 0,
                "new_trades": 120
            },
            "recommendations": [...],
            "message": "Imported 120 new trades, skipped 28 duplicates"
        }
    """
    try:
        # Check if portfolio exists
        conn = db_connection.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM portfolios WHERE id = %s", (portfolio_id,))
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404

        # Get file
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        file = request.files['file']
        broker = request.form.get('broker', 'zerodha')

        # Validate file format
        allowed_extensions = ['csv', 'xlsx', 'xls']
        file_ext = file.filename.lower().split('.')[-1]
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False,
                'error': f'Unsupported file format: .{file_ext}. Allowed: {", ".join(allowed_extensions)}'
            }), 400

        # Save file temporarily
        upload_folder = '/tmp/portfolio_imports'
        os.makedirs(upload_folder, exist_ok=True)
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # Parse CSV/Excel
        parser = CSVImportParser(broker=broker)
        parsed_trades, parse_stats = parser.parse_csv(filepath, portfolio_id)

        # Convert parsed trades to deduplication format
        new_trades = []
        for trade in parsed_trades:
            new_trades.append({
                'symbol': trade['symbol'],
                'trade_date': trade['trade_date'],
                'trade_type': trade['action'],  # BUY/SELL
                'quantity': trade['quantity'],
                'price': trade['price'],
                'order_id': trade.get('order_id')
            })

        # Deduplicate trades
        from portfolio.trade_deduplication import deduplicate_and_prepare_import

        dedup_result = deduplicate_and_prepare_import(
            db_connection,
            portfolio_id,
            new_trades
        )

        # Get trades to import (with hash)
        trades_to_import = dedup_result['trades_to_import']

        # Map back to original parsed trade format and add hash
        trades_to_insert = []
        for new_trade in trades_to_import:
            # Find matching parsed trade
            matching_trade = None
            for parsed_trade in parsed_trades:
                if (parsed_trade['symbol'] == new_trade['symbol'] and
                    parsed_trade['trade_date'] == new_trade['trade_date'] and
                    parsed_trade['action'] == new_trade['trade_type'] and
                    parsed_trade['quantity'] == new_trade['quantity'] and
                    parsed_trade['price'] == new_trade['price']):
                    matching_trade = parsed_trade
                    break

            if matching_trade:
                # Add trade hash
                matching_trade['trade_hash'] = new_trade['trade_hash']
                trades_to_insert.append(matching_trade)

        # Insert non-duplicate trades into database
        for trade in trades_to_insert:
            cursor.execute("""
                INSERT INTO portfolio_trades (
                    portfolio_id, symbol, exchange, trade_date, trade_time,
                    action, quantity, price, brokerage, stt, exchange_charges,
                    gst, sebi_charges, stamp_duty, total_charges, gross_value,
                    net_value, import_source, import_batch_id, order_id, trade_id,
                    trade_hash
                ) VALUES (
                    %(portfolio_id)s, %(symbol)s, %(exchange)s, %(trade_date)s, %(trade_time)s,
                    %(action)s, %(quantity)s, %(price)s, %(brokerage)s, %(stt)s, %(exchange_charges)s,
                    %(gst)s, %(sebi_charges)s, %(stamp_duty)s, %(total_charges)s, %(gross_value)s,
                    %(net_value)s, %(import_source)s, %(import_batch_id)s, %(order_id)s, %(trade_id)s,
                    %(trade_hash)s
                )
            """, trade)

        # Calculate final stats
        duplicates_skipped = len(dedup_result['trades_skipped'])
        trades_imported = len(trades_to_insert)
        invalid_trades = parse_stats['failed_rows']

        # Insert import history with deduplication stats
        cursor.execute("""
            INSERT INTO import_history (
                portfolio_id, import_batch_id, filename, broker, import_type,
                total_rows, success_rows, failed_rows, skipped_rows,
                status, start_date, end_date, failed_records, completed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            portfolio_id,
            parse_stats['import_batch_id'],
            file.filename,
            broker,
            'csv' if file_ext == 'csv' else 'excel',
            parse_stats['total_rows'],
            trades_imported,
            invalid_trades,
            duplicates_skipped,
            'completed' if invalid_trades == 0 else 'partial',
            parse_stats['start_date'],
            parse_stats['end_date'],
            None
        ))

        # Update portfolio last_import_at
        cursor.execute("""
            UPDATE portfolios SET last_import_at = NOW() WHERE id = %s
        """, (portfolio_id,))

        conn.commit()
        cursor.close()

        # Clean up temp file
        os.remove(filepath)

        # Build response
        dedup_analysis = dedup_result['analysis']
        message = f"Imported {trades_imported} new trades"
        if duplicates_skipped > 0:
            message += f", skipped {duplicates_skipped} duplicates"
        if invalid_trades > 0:
            message += f", {invalid_trades} invalid rows"

        return jsonify({
            'success': True,
            'import_stats': {
                'total_rows': parse_stats['total_rows'],
                'imported': trades_imported,
                'duplicates_skipped': duplicates_skipped,
                'invalid': invalid_trades,
                'import_batch_id': parse_stats['import_batch_id'],
                'start_date': str(parse_stats['start_date']) if parse_stats['start_date'] else None,
                'end_date': str(parse_stats['end_date']) if parse_stats['end_date'] else None
            },
            'deduplication': {
                'exact_duplicates': dedup_analysis['deduplication']['total_duplicates'],
                'similar_trades': dedup_analysis['deduplication']['total_similar'],
                'new_trades': dedup_analysis['deduplication']['total_to_import']
            },
            'holdings_impact': dedup_analysis['holdings_impact'],
            'recommendations': dedup_result['recommendations'],
            'message': message
        }), 200

    except Exception as e:
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== HOLDINGS ====================

@portfolio_bp.route('/<int:portfolio_id>/holdings', methods=['GET'])
def get_holdings(portfolio_id: int):
    """
    Get current holdings for portfolio

    Response:
        {
            "success": true,
            "holdings": [
                {
                    "symbol": "RELIANCE",
                    "quantity": 10,
                    "avg_buy_price": 2450.00,
                    "current_price": 2500.00,
                    "unrealized_pnl": 500.00,
                    "unrealized_pnl_pct": 2.04
                }
            ]
        }
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM holdings
            WHERE portfolio_id = %s AND quantity > 0
            ORDER BY weight DESC
        """, (portfolio_id,))

        columns = [desc[0] for desc in cursor.description]
        holdings = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.close()

        return jsonify({
            'success': True,
            'holdings': holdings,
            'count': len(holdings)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== TRADES ====================

@portfolio_bp.route('/<int:portfolio_id>/trades', methods=['GET'])
def get_trades(portfolio_id: int):
    """
    Get trades for portfolio with pagination

    Query params:
    - limit: Number of trades (default: 50)
    - offset: Pagination offset (default: 0)
    - symbol: Filter by symbol
    - action: Filter by action (BUY/SELL)
    - start_date: Filter by start date
    - end_date: Filter by end date
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()

        # Build query with filters
        query = "SELECT * FROM portfolio_trades WHERE portfolio_id = %s"
        params = [portfolio_id]

        # Filters
        symbol = request.args.get('symbol')
        if symbol:
            query += " AND symbol = %s"
            params.append(symbol.upper())

        action = request.args.get('action')
        if action:
            query += " AND action = %s"
            params.append(action.upper())

        start_date = request.args.get('start_date')
        if start_date:
            query += " AND trade_date >= %s"
            params.append(start_date)

        end_date = request.args.get('end_date')
        if end_date:
            query += " AND trade_date <= %s"
            params.append(end_date)

        # Pagination
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        query += " ORDER BY trade_date DESC, id DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        trades = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Get total count
        count_query = "SELECT COUNT(*) FROM portfolio_trades WHERE portfolio_id = %s"
        cursor.execute(count_query, [portfolio_id])
        total_count = cursor.fetchone()[0]

        cursor.close()

        return jsonify({
            'success': True,
            'trades': trades,
            'count': len(trades),
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== IMPORT HISTORY ====================

@portfolio_bp.route('/<int:portfolio_id>/imports', methods=['GET'])
def get_import_history(portfolio_id: int):
    """
    Get import history for portfolio
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM import_history
            WHERE portfolio_id = %s
            ORDER BY imported_at DESC
        """, (portfolio_id,))

        columns = [desc[0] for desc in cursor.description]
        imports = [dict(zip(columns, row)) for row in cursor.fetchall()]

        cursor.close()

        return jsonify({
            'success': True,
            'imports': imports,
            'count': len(imports)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== P&L CALCULATION ====================

@portfolio_bp.route('/<int:portfolio_id>/calculate-pnl', methods=['POST'])
def calculate_pnl(portfolio_id: int):
    """
    Calculate P&L and update holdings (FIFO matching)

    This endpoint:
    1. Fetches all trades for portfolio
    2. Calculates realized P&L (SELL trades matched with BUY trades using FIFO)
    3. Calculates unrealized P&L (current holdings)
    4. Updates portfolio totals

    Response:
        {
            "success": true,
            "realized_pnl": 12500.00,
            "unrealized_pnl": 3200.00,
            "total_pnl": 15700.00,
            "holdings_count": 5
        }
    """
    try:
        # Import P&L calculator
        from portfolio.pnl_calculator import FIFOCalculator

        # Initialize calculator
        calculator = FIFOCalculator(db_connection)

        # Calculate P&L
        result = calculator.calculate_portfolio_pnl(portfolio_id)

        return jsonify({
            'success': True,
            'portfolio_id': result['portfolio_id'],
            'realized_pnl': result['realized_pnl'],
            'unrealized_pnl': result['unrealized_pnl'],
            'total_pnl': result['total_pnl'],
            'holdings_count': result['holdings_count'],
            'message': f"P&L calculated successfully for {result['holdings_count']} holdings"
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@portfolio_bp.route('/<int:portfolio_id>/risk', methods=['GET'])
def get_portfolio_risk(portfolio_id: int):
    """
    Calculate risk score for portfolio

    This endpoint:
    1. Analyzes portfolio concentration (diversification)
    2. Calculates volatility risk (price swings)
    3. Calculates drawdown risk (losses from peak)
    4. Returns overall risk score (0-10 scale)

    Response:
        {
            "success": true,
            "portfolio_id": 1,
            "risk_score": 6.5,
            "risk_level": "Moderate",
            "concentration_risk": 7.2,
            "volatility_risk": 5.8,
            "drawdown_risk": 6.5,
            "components": {
                "concentration": {
                    "score": 7.2,
                    "weight": 0.4,
                    "holdings_count": 5
                },
                "volatility": {
                    "score": 5.8,
                    "weight": 0.3
                },
                "drawdown": {
                    "score": 6.5,
                    "weight": 0.3
                }
            }
        }
    """
    try:
        # Import risk meter
        from portfolio.risk_meter import RiskMeter

        # Initialize risk meter
        risk_meter = RiskMeter(db_connection)

        # Calculate risk
        result = risk_meter.calculate_portfolio_risk(portfolio_id)

        return jsonify({
            'success': True,
            **result
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


print(" Portfolio API routes module loaded")
