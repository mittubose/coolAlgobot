"""
Risk Meter - Portfolio Risk Assessment Engine

Calculates comprehensive risk score (0-10) based on:
- Concentration risk (diversification)
- Volatility (historical price swings)
- Drawdown risk (maximum loss from peak)
- Sector concentration (if sector data available)
"""

from typing import Dict, List, Optional
from decimal import Decimal
from collections import defaultdict
import math


class RiskMeter:
    """
    Portfolio risk assessment engine

    Generates risk scores (0-10 scale):
    - 0-2: Very Low Risk (highly diversified, stable)
    - 3-4: Low Risk
    - 5-6: Moderate Risk
    - 7-8: High Risk
    - 9-10: Very High Risk (concentrated, volatile)
    """

    # Risk weights (must sum to 1.0)
    WEIGHTS = {
        'concentration': 0.40,    # 40% - Portfolio concentration
        'volatility': 0.30,       # 30% - Price volatility
        'drawdown': 0.30          # 30% - Maximum drawdown
    }

    def __init__(self, db_connection):
        """
        Initialize risk meter with database connection

        Args:
            db_connection: Database connection object
        """
        self.db = db_connection

    def calculate_portfolio_risk(self, portfolio_id: int) -> Dict:
        """
        Calculate comprehensive risk score for portfolio

        Args:
            portfolio_id: Portfolio ID

        Returns:
            Dict with overall risk score and component scores
        """
        print(f"\n{'='*60}")
        print(f"Calculating Risk Score for Portfolio ID: {portfolio_id}")
        print(f"{'='*60}")

        # Get holdings data
        holdings = self._fetch_holdings(portfolio_id)

        if not holdings:
            return {
                'portfolio_id': portfolio_id,
                'risk_score': 0,
                'risk_level': 'Unknown',
                'concentration_risk': 0,
                'volatility_risk': 0,
                'drawdown_risk': 0,
                'message': 'No holdings data available'
            }

        # Calculate individual risk components
        concentration_score = self._calculate_concentration_risk(holdings)
        volatility_score = self._calculate_volatility_risk(holdings)
        drawdown_score = self._calculate_drawdown_risk(portfolio_id)

        # Calculate weighted overall score
        overall_score = (
            concentration_score * self.WEIGHTS['concentration'] +
            volatility_score * self.WEIGHTS['volatility'] +
            drawdown_score * self.WEIGHTS['drawdown']
        )

        # Determine risk level
        risk_level = self._get_risk_level(overall_score)

        print(f"\n✓ Risk Calculation Complete")
        print(f"  Concentration Risk: {concentration_score:.1f}/10")
        print(f"  Volatility Risk:    {volatility_score:.1f}/10")
        print(f"  Drawdown Risk:      {drawdown_score:.1f}/10")
        print(f"  Overall Risk Score: {overall_score:.1f}/10 ({risk_level})")

        # Update portfolio with risk score
        self._update_portfolio_risk(portfolio_id, overall_score)

        return {
            'portfolio_id': portfolio_id,
            'risk_score': round(overall_score, 2),
            'risk_level': risk_level,
            'concentration_risk': round(concentration_score, 2),
            'volatility_risk': round(volatility_score, 2),
            'drawdown_risk': round(drawdown_score, 2),
            'components': {
                'concentration': {
                    'score': round(concentration_score, 2),
                    'weight': self.WEIGHTS['concentration'],
                    'holdings_count': len(holdings)
                },
                'volatility': {
                    'score': round(volatility_score, 2),
                    'weight': self.WEIGHTS['volatility']
                },
                'drawdown': {
                    'score': round(drawdown_score, 2),
                    'weight': self.WEIGHTS['drawdown']
                }
            }
        }

    def _fetch_holdings(self, portfolio_id: int) -> List[Dict]:
        """
        Fetch current holdings for portfolio

        Args:
            portfolio_id: Portfolio ID

        Returns:
            List of holdings with symbol, quantity, value
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                symbol,
                quantity,
                avg_buy_price,
                current_price,
                current_value,
                unrealized_pnl,
                unrealized_pnl_pct
            FROM holdings
            WHERE portfolio_id = %s AND quantity > 0
            ORDER BY current_value DESC
        """, (portfolio_id,))

        columns = [desc[0] for desc in cursor.description]
        holdings = [dict(zip(columns, row)) for row in cursor.fetchall()]
        cursor.close()

        return holdings

    def _calculate_concentration_risk(self, holdings: List[Dict]) -> float:
        """
        Calculate concentration risk based on portfolio diversification

        Lower scores = well diversified
        Higher scores = concentrated in few holdings

        Methodology:
        - Top 1 holding > 50%: Score 9-10 (Very High)
        - Top 3 holdings > 70%: Score 7-8 (High)
        - Top 5 holdings > 80%: Score 5-6 (Moderate)
        - 10+ holdings evenly distributed: Score 0-2 (Low)

        Args:
            holdings: List of holdings dicts

        Returns:
            Risk score 0-10
        """
        if not holdings:
            return 0.0

        # Calculate total portfolio value
        total_value = sum(Decimal(str(h['current_value'])) for h in holdings)

        if total_value == 0:
            return 0.0

        # Calculate percentage for each holding
        percentages = [
            (Decimal(str(h['current_value'])) / total_value) * 100
            for h in holdings
        ]
        percentages.sort(reverse=True)

        # Get concentration metrics
        holdings_count = len(holdings)
        top1_pct = float(percentages[0]) if len(percentages) >= 1 else 0
        top3_pct = float(sum(percentages[:3])) if len(percentages) >= 3 else float(sum(percentages))
        top5_pct = float(sum(percentages[:5])) if len(percentages) >= 5 else float(sum(percentages))

        # Calculate Herfindahl-Hirschman Index (HHI) for diversification
        # HHI = sum of squared market shares (0-10000)
        # HHI < 1500: Unconcentrated (competitive market)
        # HHI 1500-2500: Moderate concentration
        # HHI > 2500: High concentration
        hhi = sum(p ** 2 for p in percentages)

        # Score calculation (0-10 scale)
        score = 0.0

        # Factor 1: Top holding concentration (40% weight)
        if top1_pct > 60:
            score += 4.0
        elif top1_pct > 50:
            score += 3.5
        elif top1_pct > 40:
            score += 3.0
        elif top1_pct > 30:
            score += 2.0
        elif top1_pct > 20:
            score += 1.0
        else:
            score += 0.5

        # Factor 2: Top 3 holdings concentration (30% weight)
        if top3_pct > 80:
            score += 3.0
        elif top3_pct > 70:
            score += 2.5
        elif top3_pct > 60:
            score += 2.0
        elif top3_pct > 50:
            score += 1.5
        else:
            score += 0.5

        # Factor 3: Number of holdings (20% weight)
        if holdings_count <= 3:
            score += 2.0
        elif holdings_count <= 5:
            score += 1.5
        elif holdings_count <= 10:
            score += 1.0
        else:
            score += 0.5

        # Factor 4: HHI (10% weight)
        if hhi > 2500:
            score += 1.0
        elif hhi > 1500:
            score += 0.5
        else:
            score += 0.0

        return min(10.0, score)

    def _calculate_volatility_risk(self, holdings: List[Dict]) -> float:
        """
        Calculate volatility risk based on price swings

        Uses unrealized P&L % as proxy for volatility.
        In production, should use historical daily returns (standard deviation).

        Args:
            holdings: List of holdings dicts

        Returns:
            Risk score 0-10
        """
        if not holdings:
            return 0.0

        # Get unrealized P&L percentages
        pnl_percentages = [
            abs(float(h['unrealized_pnl_pct']))
            for h in holdings
            if h['unrealized_pnl_pct'] is not None
        ]

        if not pnl_percentages:
            return 5.0  # Default moderate risk if no data

        # Calculate average absolute deviation (proxy for volatility)
        avg_deviation = sum(pnl_percentages) / len(pnl_percentages)

        # Score based on average deviation
        # 0-5%: Low volatility (score 0-2)
        # 5-15%: Moderate volatility (score 3-5)
        # 15-30%: High volatility (score 6-8)
        # >30%: Very high volatility (score 9-10)

        if avg_deviation < 5:
            score = (avg_deviation / 5) * 2  # Linear 0-2
        elif avg_deviation < 15:
            score = 2 + ((avg_deviation - 5) / 10) * 3  # Linear 2-5
        elif avg_deviation < 30:
            score = 5 + ((avg_deviation - 15) / 15) * 3  # Linear 5-8
        else:
            score = 8 + min(2, (avg_deviation - 30) / 20 * 2)  # Linear 8-10

        return min(10.0, score)

    def _calculate_drawdown_risk(self, portfolio_id: int) -> float:
        """
        Calculate drawdown risk based on maximum loss from peak

        Uses portfolio total return % as proxy.
        In production, should track daily equity curve and calculate max drawdown.

        Args:
            portfolio_id: Portfolio ID

        Returns:
            Risk score 0-10
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get portfolio performance metrics
        cursor.execute("""
            SELECT
                total_return_pct,
                realized_pnl,
                unrealized_pnl,
                initial_capital
            FROM portfolios
            WHERE id = %s
        """, (portfolio_id,))

        result = cursor.fetchone()
        cursor.close()

        if not result:
            return 5.0  # Default moderate risk

        total_return_pct, realized_pnl, unrealized_pnl, initial_capital = result

        # If portfolio is in profit, lower drawdown risk
        if total_return_pct and float(total_return_pct) > 0:
            # Positive returns = lower risk
            if float(total_return_pct) > 20:
                return 0.5
            elif float(total_return_pct) > 10:
                return 1.5
            elif float(total_return_pct) > 5:
                return 2.5
            else:
                return 3.5

        # If portfolio is in loss, higher drawdown risk
        if total_return_pct and float(total_return_pct) < 0:
            loss_pct = abs(float(total_return_pct))

            # Score based on loss magnitude
            # 0-5%: Low risk (score 4-5)
            # 5-10%: Moderate risk (score 5-6)
            # 10-20%: High risk (score 7-8)
            # >20%: Very high risk (score 9-10)

            if loss_pct < 5:
                score = 4 + (loss_pct / 5) * 1
            elif loss_pct < 10:
                score = 5 + ((loss_pct - 5) / 5) * 1
            elif loss_pct < 20:
                score = 6 + ((loss_pct - 10) / 10) * 2
            else:
                score = 8 + min(2, (loss_pct - 20) / 20 * 2)

            return min(10.0, score)

        # No data or neutral position
        return 5.0

    def _get_risk_level(self, score: float) -> str:
        """
        Convert numeric risk score to human-readable level

        Args:
            score: Risk score 0-10

        Returns:
            Risk level string
        """
        if score < 2:
            return "Very Low"
        elif score < 4:
            return "Low"
        elif score < 6:
            return "Moderate"
        elif score < 8:
            return "High"
        else:
            return "Very High"

    def _update_portfolio_risk(self, portfolio_id: int, risk_score: float) -> None:
        """
        Update portfolio with calculated risk score

        Args:
            portfolio_id: Portfolio ID
            risk_score: Calculated risk score (0-10)
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Add risk_score column if not exists (future-proofing)
        try:
            cursor.execute("""
                ALTER TABLE portfolios
                ADD COLUMN IF NOT EXISTS risk_score DECIMAL(4, 2) DEFAULT 0.00
            """)
            conn.commit()
        except Exception:
            pass  # Column might already exist

        # Update risk score
        cursor.execute("""
            UPDATE portfolios
            SET risk_score = %s
            WHERE id = %s
        """, (risk_score, portfolio_id))

        conn.commit()
        cursor.close()

        print(f"✓ Updated portfolio risk score: {risk_score:.2f}")


# ============ EXAMPLE USAGE ============

if __name__ == '__main__':
    """
    Example usage of risk meter
    """
    from backend.database.database import Database

    # Initialize database
    db = Database()
    db.connect()

    # Create risk meter
    risk_meter = RiskMeter(db)

    # Calculate risk for portfolio ID 1
    result = risk_meter.calculate_portfolio_risk(portfolio_id=1)

    print(f"\n{'='*60}")
    print(f"RISK ASSESSMENT COMPLETE")
    print(f"{'='*60}")
    print(f"Portfolio ID:         {result['portfolio_id']}")
    print(f"Overall Risk Score:   {result['risk_score']}/10")
    print(f"Risk Level:           {result['risk_level']}")
    print(f"\nRisk Breakdown:")
    print(f"  Concentration Risk: {result['concentration_risk']}/10 (Weight: {result['components']['concentration']['weight']*100:.0f}%)")
    print(f"  Volatility Risk:    {result['volatility_risk']}/10 (Weight: {result['components']['volatility']['weight']*100:.0f}%)")
    print(f"  Drawdown Risk:      {result['drawdown_risk']}/10 (Weight: {result['components']['drawdown']['weight']*100:.0f}%)")
    print(f"\nHoldings Count:       {result['components']['concentration']['holdings_count']}")
