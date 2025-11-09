"""
P&L Calculator with FIFO Trade Matching
Calculates realized and unrealized P&L for portfolios
"""

from typing import Dict, List, Tuple
from decimal import Decimal
from collections import defaultdict


class FIFOCalculator:
    """
    FIFO (First-In-First-Out) P&L Calculator

    Matches SELL trades with BUY trades in chronological order
    to calculate realized P&L and update holdings.
    """

    def __init__(self, db_connection):
        """
        Initialize calculator with database connection

        Args:
            db_connection: Database connection object
        """
        self.db = db_connection

    def calculate_portfolio_pnl(self, portfolio_id: int) -> Dict:
        """
        Calculate complete P&L for a portfolio

        Process:
        1. Fetch all trades for portfolio
        2. Match SELL trades with BUY trades (FIFO)
        3. Calculate realized P&L for matched trades
        4. Calculate unrealized P&L for remaining holdings
        5. Update portfolio totals
        6. Update holdings table

        Args:
            portfolio_id: Portfolio ID

        Returns:
            Dict with P&L summary
        """
        print(f"\n{'='*60}")
        print(f"Calculating P&L for Portfolio ID: {portfolio_id}")
        print(f"{'='*60}")

        # Fetch all trades
        trades = self._fetch_trades(portfolio_id)
        print(f"✓ Fetched {len(trades)} trades")

        # Group trades by symbol
        trades_by_symbol = self._group_trades_by_symbol(trades)
        print(f"✓ Grouped trades into {len(trades_by_symbol)} symbols")

        # Calculate P&L per symbol
        holdings_data = {}
        realized_pnl_total = Decimal('0')
        unrealized_pnl_total = Decimal('0')

        for symbol, symbol_trades in trades_by_symbol.items():
            result = self._calculate_symbol_pnl(symbol, symbol_trades)

            if result['quantity'] > 0:
                holdings_data[symbol] = result
                unrealized_pnl_total += result['unrealized_pnl']

            realized_pnl_total += result['realized_pnl']

        print(f"\n✓ Calculated P&L for {len(holdings_data)} holdings")
        print(f"  Realized P&L:   ₹{realized_pnl_total:,.2f}")
        print(f"  Unrealized P&L: ₹{unrealized_pnl_total:,.2f}")

        # Update database
        self._update_holdings(portfolio_id, holdings_data)
        self._update_portfolio_totals(portfolio_id, realized_pnl_total, unrealized_pnl_total)

        return {
            'portfolio_id': portfolio_id,
            'realized_pnl': float(realized_pnl_total),
            'unrealized_pnl': float(unrealized_pnl_total),
            'total_pnl': float(realized_pnl_total + unrealized_pnl_total),
            'holdings_count': len(holdings_data),
            'symbols': list(holdings_data.keys())
        }

    def _fetch_trades(self, portfolio_id: int) -> List[Dict]:
        """
        Fetch all trades for portfolio, sorted by date

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of trade dictionaries
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id, symbol, trade_date, action, quantity, price,
                total_charges, gross_value, net_value
            FROM portfolio_trades
            WHERE portfolio_id = %s
            ORDER BY trade_date ASC, id ASC
        """, (portfolio_id,))

        columns = [desc[0] for desc in cursor.description]
        trades = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()

        return trades

    def _group_trades_by_symbol(self, trades: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group trades by symbol

        Args:
            trades: List of all trades

        Returns:
            Dict mapping symbol to list of trades
        """
        grouped = defaultdict(list)
        for trade in trades:
            grouped[trade['symbol']].append(trade)
        return dict(grouped)

    def _calculate_symbol_pnl(self, symbol: str, trades: List[Dict]) -> Dict:
        """
        Calculate P&L for a single symbol using FIFO

        Args:
            symbol: Stock symbol
            trades: List of trades for this symbol

        Returns:
            Dict with P&L breakdown and holdings info
        """
        # FIFO queue: [{'quantity': 10, 'price': 100, 'date': '2024-01-01'}, ...]
        buy_queue = []

        realized_pnl = Decimal('0')
        total_quantity = 0
        total_invested = Decimal('0')

        for trade in trades:
            quantity = trade['quantity']
            price = Decimal(str(trade['price']))
            action = trade['action']

            if action == 'BUY':
                # Add to FIFO queue
                buy_queue.append({
                    'quantity': quantity,
                    'price': price,
                    'date': trade['trade_date']
                })
                total_quantity += quantity
                total_invested += quantity * price

            elif action == 'SELL':
                # Match with BUY trades (FIFO)
                remaining_to_sell = quantity
                sell_proceeds = quantity * price

                while remaining_to_sell > 0 and buy_queue:
                    oldest_buy = buy_queue[0]

                    if oldest_buy['quantity'] <= remaining_to_sell:
                        # Fully match this BUY trade
                        matched_qty = oldest_buy['quantity']
                        buy_cost = matched_qty * oldest_buy['price']
                        sell_value = matched_qty * price

                        realized_pnl += sell_value - buy_cost
                        total_quantity -= matched_qty
                        total_invested -= buy_cost

                        remaining_to_sell -= matched_qty
                        buy_queue.pop(0)  # Remove fully matched BUY
                    else:
                        # Partially match this BUY trade
                        matched_qty = remaining_to_sell
                        buy_cost = matched_qty * oldest_buy['price']
                        sell_value = matched_qty * price

                        realized_pnl += sell_value - buy_cost
                        total_quantity -= matched_qty
                        total_invested -= buy_cost

                        oldest_buy['quantity'] -= matched_qty
                        remaining_to_sell = 0

        # Calculate average buy price for remaining holdings
        avg_buy_price = Decimal('0')
        if total_quantity > 0 and buy_queue:
            avg_buy_price = total_invested / total_quantity

        # Calculate unrealized P&L (requires current price - using avg_buy_price for now)
        # TODO: Fetch real-time price from market API
        current_price = avg_buy_price  # Placeholder
        current_value = total_quantity * current_price if total_quantity > 0 else Decimal('0')
        unrealized_pnl = current_value - total_invested if total_quantity > 0 else Decimal('0')

        return {
            'symbol': symbol,
            'quantity': total_quantity,
            'avg_buy_price': float(avg_buy_price),
            'total_invested': float(total_invested),
            'current_price': float(current_price),
            'current_value': float(current_value),
            'realized_pnl': float(realized_pnl),
            'unrealized_pnl': float(unrealized_pnl),
            'unrealized_pnl_pct': float((unrealized_pnl / total_invested * 100) if total_invested > 0 else 0),
            'first_buy_date': buy_queue[0]['date'] if buy_queue else None,
            'last_buy_date': buy_queue[-1]['date'] if buy_queue else None
        }

    def _update_holdings(self, portfolio_id: int, holdings_data: Dict[str, Dict]) -> None:
        """
        Update holdings table with calculated P&L

        Args:
            portfolio_id: Portfolio ID
            holdings_data: Dict mapping symbol to holdings info
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Clear existing holdings for this portfolio
        cursor.execute("DELETE FROM holdings WHERE portfolio_id = %s", (portfolio_id,))

        # Insert updated holdings
        for symbol, data in holdings_data.items():
            cursor.execute("""
                INSERT INTO holdings (
                    portfolio_id, symbol, quantity, avg_buy_price, total_invested,
                    current_price, current_value, unrealized_pnl, unrealized_pnl_pct,
                    first_buy_date, last_buy_date, last_updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
            """, (
                portfolio_id,
                data['symbol'],
                data['quantity'],
                data['avg_buy_price'],
                data['total_invested'],
                data['current_price'],
                data['current_value'],
                data['unrealized_pnl'],
                data['unrealized_pnl_pct'],
                data['first_buy_date'],
                data['last_buy_date']
            ))

        conn.commit()
        cursor.close()
        print(f"✓ Updated holdings table ({len(holdings_data)} records)")

    def _update_portfolio_totals(self, portfolio_id: int, realized_pnl: Decimal, unrealized_pnl: Decimal) -> None:
        """
        Update portfolio totals

        Args:
            portfolio_id: Portfolio ID
            realized_pnl: Total realized P&L
            unrealized_pnl: Total unrealized P&L
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        total_pnl = realized_pnl + unrealized_pnl

        # Get initial capital to calculate return %
        cursor.execute("SELECT initial_capital FROM portfolios WHERE id = %s", (portfolio_id,))
        initial_capital = cursor.fetchone()[0]
        total_return_pct = (total_pnl / Decimal(str(initial_capital)) * 100) if initial_capital > 0 else Decimal('0')

        # Update portfolio
        cursor.execute("""
            UPDATE portfolios SET
                realized_pnl = %s,
                unrealized_pnl = %s,
                total_pnl = %s,
                total_return_pct = %s,
                last_calculated_at = NOW()
            WHERE id = %s
        """, (
            float(realized_pnl),
            float(unrealized_pnl),
            float(total_pnl),
            float(total_return_pct),
            portfolio_id
        ))

        conn.commit()
        cursor.close()
        print(f"✓ Updated portfolio totals (Return: {total_return_pct:.2f}%)")


# ============ EXAMPLE USAGE ============

if __name__ == '__main__':
    """
    Example usage of FIFO P&L calculator
    """
    from backend.database.database import Database

    # Initialize database
    db = Database()
    db.connect()

    # Create calculator
    calculator = FIFOCalculator(db)

    # Calculate P&L for portfolio ID 1
    result = calculator.calculate_portfolio_pnl(portfolio_id=1)

    print(f"\n{'='*60}")
    print(f"P&L CALCULATION COMPLETE")
    print(f"{'='*60}")
    print(f"Portfolio ID:    {result['portfolio_id']}")
    print(f"Realized P&L:    ₹{result['realized_pnl']:,.2f}")
    print(f"Unrealized P&L:  ₹{result['unrealized_pnl']:,.2f}")
    print(f"Total P&L:       ₹{result['total_pnl']:,.2f}")
    print(f"Holdings:        {result['holdings_count']} symbols")
    print(f"Symbols:         {', '.join(result['symbols'])}")
