"""
Trade Deduplication and Data Validation Module

This module handles:
1. Duplicate detection across multiple uploads
2. Incremental imports (only new trades)
3. Data sorting and validation
4. Conflict resolution
5. Trade matching and analysis

Author: Scalping Bot Team
Date: October 26, 2025
"""

import hashlib
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import pandas as pd
from decimal import Decimal


class TradeDeduplicator:
    """
    Handles trade deduplication and incremental import logic
    """

    def __init__(self, db_connection):
        """
        Initialize the deduplicator with database connection

        Args:
            db_connection: Database connection object
        """
        self.db = db_connection

    def generate_trade_hash(self, trade: Dict) -> str:
        """
        Generate unique hash for a trade based on key attributes

        This creates a fingerprint of the trade using:
        - Symbol
        - Trade date
        - Trade type (BUY/SELL)
        - Quantity
        - Price
        - Order ID (if available)

        Args:
            trade: Trade dictionary

        Returns:
            SHA256 hash string
        """
        # Create unique identifier from trade attributes
        key_parts = [
            str(trade.get('symbol', '')).upper(),
            str(trade.get('trade_date', '')),
            str(trade.get('trade_type', '')).upper(),
            str(trade.get('quantity', '')),
            str(trade.get('price', '')),
            str(trade.get('order_id', ''))  # Broker's order ID if available
        ]

        # Join and hash
        key_string = '|'.join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get_existing_trades(self, portfolio_id: int) -> pd.DataFrame:
        """
        Fetch all existing trades for a portfolio from database

        Args:
            portfolio_id: Portfolio ID

        Returns:
            DataFrame with existing trades
        """
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    id,
                    symbol,
                    trade_date,
                    trade_type,
                    quantity,
                    price,
                    order_id,
                    trade_hash
                FROM portfolio_trades
                WHERE portfolio_id = %s
                ORDER BY trade_date ASC, symbol ASC
            """

            cursor.execute(query, (portfolio_id,))
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            self.db.release_connection(conn)

            return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            print(f"Error fetching existing trades: {e}")
            return pd.DataFrame()

    def sort_and_validate_trades(self, trades: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Sort trades chronologically and validate data quality

        Sorting order:
        1. Trade date (ascending)
        2. Symbol (alphabetically)
        3. Trade type (BUY before SELL for same day/symbol)

        Args:
            trades: List of trade dictionaries

        Returns:
            Tuple of (valid_trades, invalid_trades)
        """
        valid_trades = []
        invalid_trades = []

        for trade in trades:
            # Validate required fields
            validation_errors = []

            if not trade.get('symbol'):
                validation_errors.append('Missing symbol')

            if not trade.get('trade_date'):
                validation_errors.append('Missing trade date')

            if not trade.get('trade_type'):
                validation_errors.append('Missing trade type')
            elif trade.get('trade_type') not in ['BUY', 'SELL']:
                validation_errors.append('Invalid trade type (must be BUY or SELL)')

            if not trade.get('quantity') or float(trade.get('quantity', 0)) <= 0:
                validation_errors.append('Invalid quantity')

            if not trade.get('price') or float(trade.get('price', 0)) <= 0:
                validation_errors.append('Invalid price')

            if validation_errors:
                invalid_trades.append({
                    **trade,
                    'validation_errors': validation_errors
                })
            else:
                valid_trades.append(trade)

        # Sort valid trades
        valid_trades.sort(key=lambda t: (
            t['trade_date'],
            t['symbol'],
            0 if t['trade_type'] == 'BUY' else 1  # BUY before SELL
        ))

        return valid_trades, invalid_trades

    def detect_duplicates(
        self,
        new_trades: List[Dict],
        existing_trades_df: pd.DataFrame
    ) -> Dict:
        """
        Detect duplicate trades and categorize them

        Categories:
        - Exact duplicates: Same hash
        - Similar trades: Same symbol/date/type but different price/quantity
        - New trades: Not in database

        Args:
            new_trades: List of new trades to import
            existing_trades_df: DataFrame of existing trades

        Returns:
            Dictionary with categorized trades
        """
        # Generate hashes for existing trades if not present
        if not existing_trades_df.empty and 'trade_hash' not in existing_trades_df.columns:
            existing_trades_df['trade_hash'] = existing_trades_df.apply(
                lambda row: self.generate_trade_hash(row.to_dict()), axis=1
            )

        existing_hashes = set(existing_trades_df['trade_hash'].tolist() if not existing_trades_df.empty else [])

        exact_duplicates = []
        similar_trades = []
        new_unique_trades = []

        for trade in new_trades:
            trade_hash = self.generate_trade_hash(trade)
            trade['trade_hash'] = trade_hash

            if trade_hash in existing_hashes:
                # Exact duplicate
                exact_duplicates.append(trade)
            else:
                # Check for similar trades (same symbol/date/type but different price/qty)
                similar = self._find_similar_trades(trade, existing_trades_df)

                if similar:
                    similar_trades.append({
                        'new_trade': trade,
                        'existing_trades': similar
                    })
                else:
                    # Completely new trade
                    new_unique_trades.append(trade)

        return {
            'exact_duplicates': exact_duplicates,
            'similar_trades': similar_trades,
            'new_unique_trades': new_unique_trades,
            'total_new': len(new_trades),
            'total_duplicates': len(exact_duplicates),
            'total_similar': len(similar_trades),
            'total_to_import': len(new_unique_trades)
        }

    def _find_similar_trades(self, trade: Dict, existing_df: pd.DataFrame) -> List[Dict]:
        """
        Find trades with same symbol/date/type but different price/quantity

        Args:
            trade: Trade to check
            existing_df: Existing trades DataFrame

        Returns:
            List of similar trades
        """
        if existing_df.empty:
            return []

        # Filter by symbol, date, and type
        similar = existing_df[
            (existing_df['symbol'] == trade['symbol']) &
            (existing_df['trade_date'] == trade['trade_date']) &
            (existing_df['trade_type'] == trade['trade_type'])
        ]

        # Exclude exact matches (different price or quantity)
        similar = similar[
            (similar['price'] != float(trade['price'])) |
            (similar['quantity'] != float(trade['quantity']))
        ]

        return similar.to_dict('records') if not similar.empty else []

    def analyze_import_impact(
        self,
        portfolio_id: int,
        new_trades: List[Dict]
    ) -> Dict:
        """
        Analyze the impact of importing new trades on the portfolio

        Provides:
        - Holdings changes (new positions, quantity changes)
        - P&L impact
        - Duplicate analysis
        - Recommendations

        Args:
            portfolio_id: Portfolio ID
            new_trades: New trades to analyze

        Returns:
            Analysis report dictionary
        """
        # Get existing trades
        existing_trades_df = self.get_existing_trades(portfolio_id)

        # Sort and validate
        valid_trades, invalid_trades = self.sort_and_validate_trades(new_trades)

        # Detect duplicates
        dedup_results = self.detect_duplicates(valid_trades, existing_trades_df)

        # Analyze holdings impact
        holdings_impact = self._analyze_holdings_impact(
            dedup_results['new_unique_trades'],
            existing_trades_df
        )

        return {
            'validation': {
                'total_trades': len(new_trades),
                'valid_trades': len(valid_trades),
                'invalid_trades': len(invalid_trades),
                'invalid_details': invalid_trades
            },
            'deduplication': dedup_results,
            'holdings_impact': holdings_impact,
            'recommendations': self._generate_recommendations(
                dedup_results,
                holdings_impact
            )
        }

    def _analyze_holdings_impact(
        self,
        new_trades: List[Dict],
        existing_trades_df: pd.DataFrame
    ) -> Dict:
        """
        Analyze how new trades will affect holdings

        Args:
            new_trades: New trades to import
            existing_trades_df: Existing trades

        Returns:
            Holdings impact analysis
        """
        # Calculate current holdings from existing trades
        current_holdings = {}
        if not existing_trades_df.empty:
            for _, trade in existing_trades_df.iterrows():
                symbol = trade['symbol']
                if symbol not in current_holdings:
                    current_holdings[symbol] = 0

                if trade['trade_type'] == 'BUY':
                    current_holdings[symbol] += trade['quantity']
                else:
                    current_holdings[symbol] -= trade['quantity']

        # Calculate new holdings after import
        new_holdings = current_holdings.copy()
        for trade in new_trades:
            symbol = trade['symbol']
            if symbol not in new_holdings:
                new_holdings[symbol] = 0

            if trade['trade_type'] == 'BUY':
                new_holdings[symbol] += trade['quantity']
            else:
                new_holdings[symbol] -= trade['quantity']

        # Identify changes
        new_positions = [s for s in new_holdings if s not in current_holdings and new_holdings[s] != 0]
        closed_positions = [s for s in current_holdings if current_holdings[s] != 0 and new_holdings.get(s, 0) == 0]
        quantity_changes = {
            s: new_holdings[s] - current_holdings.get(s, 0)
            for s in set(list(current_holdings.keys()) + list(new_holdings.keys()))
            if new_holdings.get(s, 0) != current_holdings.get(s, 0)
        }

        return {
            'current_holdings_count': len([h for h in current_holdings.values() if h != 0]),
            'new_holdings_count': len([h for h in new_holdings.values() if h != 0]),
            'new_positions': new_positions,
            'closed_positions': closed_positions,
            'quantity_changes': quantity_changes
        }

    def _generate_recommendations(
        self,
        dedup_results: Dict,
        holdings_impact: Dict
    ) -> List[str]:
        """
        Generate recommendations based on analysis

        Args:
            dedup_results: Deduplication results
            holdings_impact: Holdings impact analysis

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if dedup_results['total_duplicates'] > 0:
            recommendations.append(
                f"⚠️ Found {dedup_results['total_duplicates']} duplicate trades. "
                f"These will be skipped to avoid double-counting."
            )

        if dedup_results['total_similar'] > 0:
            recommendations.append(
                f"⚠️ Found {dedup_results['total_similar']} similar trades with different prices/quantities. "
                f"Please review these manually."
            )

        if holdings_impact['new_positions']:
            recommendations.append(
                f"✅ Will create {len(holdings_impact['new_positions'])} new positions: "
                f"{', '.join(holdings_impact['new_positions'][:5])}"
                f"{'...' if len(holdings_impact['new_positions']) > 5 else ''}"
            )

        if holdings_impact['closed_positions']:
            recommendations.append(
                f"✅ Will close {len(holdings_impact['closed_positions'])} positions: "
                f"{', '.join(holdings_impact['closed_positions'][:5])}"
                f"{'...' if len(holdings_impact['closed_positions']) > 5 else ''}"
            )

        if dedup_results['total_to_import'] == 0:
            recommendations.append(
                "ℹ️ No new trades to import. All trades already exist in the system."
            )
        else:
            recommendations.append(
                f"✅ Ready to import {dedup_results['total_to_import']} new trades."
            )

        return recommendations


def deduplicate_and_prepare_import(
    db_connection,
    portfolio_id: int,
    new_trades: List[Dict]
) -> Dict:
    """
    Convenience function to deduplicate and prepare trades for import

    Args:
        db_connection: Database connection
        portfolio_id: Portfolio ID
        new_trades: New trades to import

    Returns:
        Prepared import data with analysis
    """
    deduplicator = TradeDeduplicator(db_connection)
    analysis = deduplicator.analyze_import_impact(portfolio_id, new_trades)

    return {
        'success': True,
        'analysis': analysis,
        'trades_to_import': analysis['deduplication']['new_unique_trades'],
        'trades_skipped': analysis['deduplication']['exact_duplicates'],
        'trades_similar': analysis['deduplication']['similar_trades'],
        'recommendations': analysis['recommendations']
    }
