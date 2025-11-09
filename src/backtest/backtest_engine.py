"""
Core Backtesting Engine
Simulates trading strategy execution on historical data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
import logging

from src.utils.logger import setup_logger


@dataclass
class Trade:
    """Represents a single trade"""
    entry_time: datetime
    exit_time: Optional[datetime] = None
    symbol: str = ''
    side: str = 'BUY'  # BUY or SELL
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    quantity: int = 0
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    commission: float = 0.0
    exit_reason: str = ''  # target_hit, stop_loss, signal, eod
    status: str = 'open'  # open, closed


@dataclass
class BacktestResult:
    """Comprehensive backtest results"""
    # Basic metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    # P&L metrics
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    # Risk metrics
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0

    # Capital metrics
    initial_capital: float = 0.0
    final_capital: float = 0.0
    peak_capital: float = 0.0

    # Commission
    total_commission: float = 0.0

    # Trade history
    trades: List[Trade] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)

    # Execution details
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    duration_days: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.win_rate, 2),
            'total_pnl': round(self.total_pnl, 2),
            'total_pnl_percent': round(self.total_pnl_percent, 2),
            'gross_profit': round(self.gross_profit, 2),
            'gross_loss': round(self.gross_loss, 2),
            'avg_win': round(self.avg_win, 2),
            'avg_loss': round(self.avg_loss, 2),
            'largest_win': round(self.largest_win, 2),
            'largest_loss': round(self.largest_loss, 2),
            'max_drawdown': round(self.max_drawdown, 2),
            'max_drawdown_percent': round(self.max_drawdown_percent, 2),
            'profit_factor': round(self.profit_factor, 2),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'initial_capital': round(self.initial_capital, 2),
            'final_capital': round(self.final_capital, 2),
            'peak_capital': round(self.peak_capital, 2),
            'total_commission': round(self.total_commission, 2),
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'duration_days': self.duration_days
        }


class BacktestEngine:
    """
    Core backtesting engine

    Features:
    - Historical data simulation
    - Position management
    - Commission calculation
    - Stop-loss and target execution
    - Performance metrics calculation
    """

    def __init__(
        self,
        initial_capital: float = 100000,
        commission_per_trade: float = 20,
        commission_percent: float = 0.0,
        slippage: float = 0.0,
        risk_per_trade: float = 0.02,  # 2% risk per trade
        max_positions: int = 5
    ):
        """
        Initialize backtesting engine

        Args:
            initial_capital: Starting capital
            commission_per_trade: Fixed commission per trade
            commission_percent: Commission as percentage of trade value
            slippage: Slippage in percentage
            risk_per_trade: Maximum risk per trade as fraction
            max_positions: Maximum concurrent positions
        """
        self.initial_capital = initial_capital
        self.commission_per_trade = commission_per_trade
        self.commission_percent = commission_percent
        self.slippage = slippage
        self.risk_per_trade = risk_per_trade
        self.max_positions = max_positions

        # State
        self.current_capital = initial_capital
        self.peak_capital = initial_capital
        self.open_trades: List[Trade] = []
        self.closed_trades: List[Trade] = []
        self.equity_history: List[Dict] = []

        self.logger = setup_logger('backtest_engine')

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy_func: Callable,
        strategy_params: Dict = None
    ) -> BacktestResult:
        """
        Run backtest on historical data

        Args:
            data: OHLCV DataFrame with columns [time, open, high, low, close, volume]
            strategy_func: Strategy function that returns signals
            strategy_params: Parameters for strategy function

        Returns:
            BacktestResult object with comprehensive metrics
        """
        if strategy_params is None:
            strategy_params = {}

        self.logger.info(f"Starting backtest with {len(data)} candles")
        self.logger.info(f"Initial capital: ₹{self.initial_capital:,.2f}")

        # Reset state
        self._reset_state()

        # Ensure data is sorted by time
        data = data.sort_values('time').reset_index(drop=True)

        start_date = pd.to_datetime(data['time'].iloc[0])
        end_date = pd.to_datetime(data['time'].iloc[-1])

        # Process each candle
        for idx in range(len(data)):
            current_candle = data.iloc[idx]
            current_time = pd.to_datetime(current_candle['time'])

            # Update open positions (check stop-loss, targets, trailing stops)
            self._update_open_positions(current_candle)

            # Generate signal from strategy
            # Strategy receives historical data up to current point
            historical_data = data.iloc[:idx+1].copy()
            signal = strategy_func(historical_data, strategy_params)

            # Execute signal
            if signal:
                self._execute_signal(signal, current_candle, current_time)

            # Record equity
            self._record_equity(current_time, current_candle['close'])

        # Close any remaining open positions at end
        self._close_all_positions(data.iloc[-1], reason='backtest_end')

        # Calculate final metrics
        result = self._calculate_results(start_date, end_date)

        self.logger.info(f"Backtest completed: {result.total_trades} trades, "
                        f"Win rate: {result.win_rate:.1f}%, "
                        f"Total P&L: ₹{result.total_pnl:,.2f}")

        return result

    def _execute_signal(self, signal: Dict, candle: pd.Series, current_time: datetime):
        """Execute a trading signal"""
        action = signal.get('action')  # BUY, SELL, CLOSE

        if action == 'CLOSE':
            # Close specific position or all positions
            symbol = signal.get('symbol')
            if symbol:
                self._close_position_by_symbol(symbol, candle, reason='signal')
            else:
                self._close_all_positions(candle, reason='signal')
            return

        # Check if we can open new position
        if len(self.open_trades) >= self.max_positions:
            return

        # Calculate position size based on risk
        entry_price = candle['close'] * (1 + self.slippage / 100)
        stop_loss = signal.get('stop_loss')
        target = signal.get('target')

        if not stop_loss:
            # If no stop-loss provided, use default 2% risk
            stop_loss = entry_price * 0.98 if action == 'BUY' else entry_price * 1.02

        # Calculate quantity based on risk
        risk_amount = self.current_capital * self.risk_per_trade
        risk_per_share = abs(entry_price - stop_loss)

        if risk_per_share == 0:
            return

        quantity = int(risk_amount / risk_per_share)

        if quantity == 0:
            return

        # Calculate commission
        trade_value = entry_price * quantity
        commission = self.commission_per_trade + (trade_value * self.commission_percent / 100)

        # Check if we have enough capital
        required_capital = trade_value + commission
        if required_capital > self.current_capital:
            return

        # Create trade
        trade = Trade(
            entry_time=current_time,
            symbol=signal.get('symbol', 'UNKNOWN'),
            side=action,
            entry_price=entry_price,
            quantity=quantity,
            stop_loss=stop_loss,
            target=target,
            commission=commission
        )

        # Deduct capital
        self.current_capital -= commission

        # Add to open trades
        self.open_trades.append(trade)

        self.logger.debug(f"{action} {quantity} @ ₹{entry_price:.2f}, SL: ₹{stop_loss:.2f}")

    def _update_open_positions(self, candle: pd.Series):
        """Update open positions - check stop-loss and targets"""
        for trade in self.open_trades[:]:  # Copy list to avoid modification issues
            high = candle['high']
            low = candle['low']
            close = candle['close']

            if trade.side == 'BUY':
                # Check stop-loss
                if trade.stop_loss and low <= trade.stop_loss:
                    self._close_trade(trade, trade.stop_loss, candle['time'], 'stop_loss')
                # Check target
                elif trade.target and high >= trade.target:
                    self._close_trade(trade, trade.target, candle['time'], 'target_hit')

            elif trade.side == 'SELL':
                # Check stop-loss
                if trade.stop_loss and high >= trade.stop_loss:
                    self._close_trade(trade, trade.stop_loss, candle['time'], 'stop_loss')
                # Check target
                elif trade.target and low <= trade.target:
                    self._close_trade(trade, trade.target, candle['time'], 'target_hit')

    def _close_trade(self, trade: Trade, exit_price: float, exit_time: datetime, reason: str):
        """Close a trade and calculate P&L"""
        # Apply slippage
        exit_price = exit_price * (1 - self.slippage / 100)

        # Calculate P&L
        if trade.side == 'BUY':
            pnl = (exit_price - trade.entry_price) * trade.quantity
        else:  # SELL
            pnl = (trade.entry_price - exit_price) * trade.quantity

        # Calculate commission for exit
        exit_commission = self.commission_per_trade + (exit_price * trade.quantity * self.commission_percent / 100)
        total_commission = trade.commission + exit_commission

        # Net P&L
        net_pnl = pnl - exit_commission
        pnl_percent = (net_pnl / (trade.entry_price * trade.quantity)) * 100

        # Update trade
        trade.exit_time = exit_time
        trade.exit_price = exit_price
        trade.pnl = net_pnl
        trade.pnl_percent = pnl_percent
        trade.commission = total_commission
        trade.exit_reason = reason
        trade.status = 'closed'

        # Update capital
        self.current_capital += (trade.entry_price * trade.quantity) + net_pnl

        # Update peak
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        # Move to closed trades
        self.open_trades.remove(trade)
        self.closed_trades.append(trade)

    def _close_position_by_symbol(self, symbol: str, candle: pd.Series, reason: str):
        """Close position for specific symbol"""
        for trade in self.open_trades[:]:
            if trade.symbol == symbol:
                self._close_trade(trade, candle['close'], candle['time'], reason)

    def _close_all_positions(self, candle: pd.Series, reason: str):
        """Close all open positions"""
        for trade in self.open_trades[:]:
            self._close_trade(trade, candle['close'], candle['time'], reason)

    def _record_equity(self, timestamp: datetime, price: float):
        """Record equity curve point"""
        # Calculate unrealized P&L from open positions
        unrealized_pnl = sum(
            (price - t.entry_price) * t.quantity if t.side == 'BUY'
            else (t.entry_price - price) * t.quantity
            for t in self.open_trades
        )

        total_equity = self.current_capital + unrealized_pnl

        self.equity_history.append({
            'time': timestamp,
            'capital': self.current_capital,
            'unrealized_pnl': unrealized_pnl,
            'total_equity': total_equity,
            'open_positions': len(self.open_trades)
        })

    def _calculate_results(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """Calculate comprehensive backtest results"""
        result = BacktestResult()

        result.initial_capital = self.initial_capital
        result.final_capital = self.current_capital
        result.peak_capital = self.peak_capital
        result.start_date = start_date
        result.end_date = end_date
        result.duration_days = (end_date - start_date).days

        # Trade statistics
        result.total_trades = len(self.closed_trades)
        result.trades = self.closed_trades
        result.equity_curve = self.equity_history

        if result.total_trades == 0:
            return result

        # Win/Loss analysis
        winning_trades = [t for t in self.closed_trades if t.pnl > 0]
        losing_trades = [t for t in self.closed_trades if t.pnl < 0]

        result.winning_trades = len(winning_trades)
        result.losing_trades = len(losing_trades)
        result.win_rate = (result.winning_trades / result.total_trades) * 100

        # P&L metrics
        result.total_pnl = sum(t.pnl for t in self.closed_trades)
        result.total_pnl_percent = ((result.final_capital - result.initial_capital) / result.initial_capital) * 100
        result.gross_profit = sum(t.pnl for t in winning_trades)
        result.gross_loss = abs(sum(t.pnl for t in losing_trades))
        result.total_commission = sum(t.commission for t in self.closed_trades)

        if winning_trades:
            result.avg_win = result.gross_profit / len(winning_trades)
            result.largest_win = max(t.pnl for t in winning_trades)

        if losing_trades:
            result.avg_loss = result.gross_loss / len(losing_trades)
            result.largest_loss = min(t.pnl for t in losing_trades)

        # Profit factor
        if result.gross_loss > 0:
            result.profit_factor = result.gross_profit / result.gross_loss

        # Drawdown calculation
        if self.equity_history:
            equity_values = [e['total_equity'] for e in self.equity_history]
            peak = self.initial_capital
            max_dd = 0

            for equity in equity_values:
                if equity > peak:
                    peak = equity
                drawdown = peak - equity
                if drawdown > max_dd:
                    max_dd = drawdown

            result.max_drawdown = max_dd
            if peak > 0:
                result.max_drawdown_percent = (max_dd / peak) * 100

        # Sharpe ratio (simplified - assumes daily returns)
        if self.equity_history and len(self.equity_history) > 1:
            returns = []
            for i in range(1, len(self.equity_history)):
                prev_equity = self.equity_history[i-1]['total_equity']
                curr_equity = self.equity_history[i]['total_equity']
                if prev_equity > 0:
                    returns.append((curr_equity - prev_equity) / prev_equity)

            if returns:
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                if std_return > 0:
                    result.sharpe_ratio = (mean_return / std_return) * np.sqrt(252)  # Annualized

        return result

    def _reset_state(self):
        """Reset engine state for new backtest"""
        self.current_capital = self.initial_capital
        self.peak_capital = self.initial_capital
        self.open_trades = []
        self.closed_trades = []
        self.equity_history = []
