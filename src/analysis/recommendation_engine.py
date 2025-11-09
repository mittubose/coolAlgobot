"""
Recommendation Engine
Generates daily stock recommendations based on pattern detection
"""

import sqlite3
from typing import List, Dict
import logging
from datetime import datetime, date

from .candlestick_patterns import CandlestickPatternDetector
from ..utils.ohlc_generator import OHLCGenerator
from ..database.db_manager import get_db_connection

logger = logging.getLogger(__name__)

# NIFTY 50 stocks (top 50 stocks for MVP)
NIFTY_50 = [
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR',
    'ICICIBANK', 'KOTAKBANK', 'SBIN', 'BHARTIARTL', 'ITC',
    'AXISBANK', 'LT', 'ASIANPAINT', 'MARUTI', 'TITAN',
    'SUNPHARMA', 'ULTRACEMCO', 'BAJFINANCE', 'NESTLEIND', 'WIPRO',
    'POWERGRID', 'NTPC', 'HCLTECH', 'ONGC', 'TECHM',
    'TATAMOTORS', 'TATASTEEL', 'ADANIPORTS', 'M&M', 'BAJAJFINSV',
    'DIVISLAB', 'DRREDDY', 'BRITANNIA', 'HINDALCO', 'CIPLA',
    'EICHERMOT', 'GRASIM', 'COALINDIA', 'JSWSTEEL', 'SHREECEM',
    'UPL', 'INDUSINDBK', 'HEROMOTOCO', 'BAJAJ-AUTO', 'SBILIFE',
    'APOLLOHOSP', 'TATACONSUM', 'BPCL', 'HDFCLIFE', 'ADANIENT'
]


class RecommendationEngine:
    """Generate stock recommendations based on pattern detection"""

    def __init__(self):
        self.ohlc_generator = OHLCGenerator()

    def generate_daily_recommendations(self, stock_list: List[str] = None) -> List[Dict]:
        """
        Generate daily stock recommendations

        Args:
            stock_list: List of stocks to scan (default: NIFTY 50)

        Returns:
            List[Dict]: Top recommendations sorted by confidence
        """
        if stock_list is None:
            stock_list = NIFTY_50

        logger.info(f"Scanning {len(stock_list)} stocks for patterns...")
        recommendations = []

        for symbol in stock_list:
            try:
                # Get OHLC data (using generator for MVP, will use real API later)
                ohlc_data = self.ohlc_generator.generate_candles(
                    count=100,
                    timeframe='5m'
                )

                # Detect patterns
                # Convert ohlc list to pandas DataFrame
                import pandas as pd
                df = pd.DataFrame(ohlc_data)
                pattern_detector = CandlestickPatternDetector(df)
                patterns = pattern_detector.get_active_patterns()

                # Filter high-confidence bullish patterns only
                for pattern in patterns:
                    if pattern['confidence'] > 75 and pattern['type'] == 'bullish':
                        recommendations.append({
                            'symbol': symbol,
                            'pattern_name': pattern['name'],
                            'confidence': pattern['confidence'],
                            'entry_price': round(ohlc_data[-1]['close'], 2),
                            'pattern_type': pattern['type'],
                            'description': pattern.get('description', '')
                        })

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue

        # Sort by confidence (highest first)
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)

        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations

    def get_top_picks(self, limit: int = 5) -> List[Dict]:
        """
        Get top N recommendations

        Args:
            limit: Number of top picks to return (default: 5)

        Returns:
            List[Dict]: Top N recommendations
        """
        all_recommendations = self.generate_daily_recommendations()
        return all_recommendations[:limit]

    def save_daily_picks_to_db(self, picks: List[Dict]) -> int:
        """
        Save daily picks to database

        Args:
            picks: List of recommendation dictionaries

        Returns:
            int: Number of picks saved
        """
        if not picks:
            logger.warning("No picks to save")
            return 0

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            today = date.today()
            saved_count = 0

            for pick in picks:
                cursor.execute('''
                    INSERT INTO daily_picks (symbol, pattern_name, confidence, entry_price, date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    pick['symbol'],
                    pick['pattern_name'],
                    pick['confidence'],
                    pick['entry_price'],
                    today
                ))
                saved_count += 1

            conn.commit()
            logger.info(f"Saved {saved_count} daily picks to database")
            return saved_count

        except sqlite3.Error as e:
            logger.error(f"Error saving daily picks: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()

    def get_todays_picks_from_db(self, limit: int = 5) -> List[Dict]:
        """
        Get today's picks from database (cached)

        Args:
            limit: Number of picks to return

        Returns:
            List[Dict]: Today's picks
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT symbol, pattern_name, confidence, entry_price, generated_at
                FROM daily_picks
                WHERE date = DATE('now')
                ORDER BY confidence DESC
                LIMIT ?
            ''', (limit,))

            rows = cursor.fetchall()

            if not rows:
                # No cached picks for today, generate fresh ones
                logger.info("No cached picks found, generating fresh recommendations...")
                fresh_picks = self.get_top_picks(limit)
                self.save_daily_picks_to_db(fresh_picks)
                return fresh_picks

            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error getting today's picks: {e}")
            return []
        finally:
            conn.close()

    def refresh_daily_picks(self, limit: int = 5) -> List[Dict]:
        """
        Force refresh daily picks (clear cache and regenerate)

        Args:
            limit: Number of picks to generate

        Returns:
            List[Dict]: Fresh picks
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Clear today's picks
            cursor.execute("DELETE FROM daily_picks WHERE date = DATE('now')")
            conn.commit()

            # Generate fresh picks
            fresh_picks = self.get_top_picks(limit)
            self.save_daily_picks_to_db(fresh_picks)

            logger.info(f"Refreshed {len(fresh_picks)} daily picks")
            return fresh_picks

        except sqlite3.Error as e:
            logger.error(f"Error refreshing daily picks: {e}")
            conn.rollback()
            return []
        finally:
            conn.close()


def generate_and_cache_picks():
    """
    Utility function to generate and cache daily picks
    Can be run as a cron job daily
    """
    engine = RecommendationEngine()
    picks = engine.get_top_picks(limit=5)
    engine.save_daily_picks_to_db(picks)

    print(f"\nGenerated {len(picks)} daily picks:")
    for i, pick in enumerate(picks, 1):
        print(f"{i}. {pick['symbol']}: {pick['pattern_name']} ({pick['confidence']}%) @ ₹{pick['entry_price']}")


if __name__ == '__main__':
    # Test recommendation engine
    logging.basicConfig(level=logging.INFO)

    # Initialize database first
    from ..database.db_manager import init_database
    init_database()

    print("\n=== Testing Recommendation Engine ===")

    engine = RecommendationEngine()

    # Generate recommendations
    print("\nGenerating top 5 picks...")
    top_picks = engine.get_top_picks(limit=5)

    print(f"\nTop {len(top_picks)} Stock Picks:")
    for i, pick in enumerate(top_picks, 1):
        print(f"\n{i}. {pick['symbol']}")
        print(f"   Pattern: {pick['pattern_name']}")
        print(f"   Confidence: {pick['confidence']}%")
        print(f"   Entry Price: ₹{pick['entry_price']}")

    # Save to database
    print("\nSaving picks to database...")
    saved = engine.save_daily_picks_to_db(top_picks)
    print(f"Saved {saved} picks")

    # Retrieve from database
    print("\nRetrieving today's picks from database...")
    cached_picks = engine.get_todays_picks_from_db(limit=5)
    print(f"Retrieved {len(cached_picks)} cached picks")

    # Refresh picks
    print("\nRefreshing daily picks...")
    refreshed_picks = engine.refresh_daily_picks(limit=5)
    print(f"Generated {len(refreshed_picks)} fresh picks")
