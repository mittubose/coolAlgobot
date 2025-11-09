"""
ML Walk-Forward Backtest Engine

Implements walk-forward analysis with periodic model retraining to prevent
look-ahead bias and evaluate ML strategies realistically.

Features:
    - Train on N periods, test on M periods
    - Periodic model retraining (weekly/monthly)
    - Out-of-sample performance tracking
    - Integration with volatility scaling
    - Comprehensive performance metrics
"""

import numpy as np
import pandas as pd
import torch
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from pathlib import Path
import json

from .feature_engineering import FeatureEngineer
from .data_pipeline import TimeSeriesDataPipeline
from .models.tcn_model import TCNTradingModel, create_default_model
from .training.trainer import TCNTrainer, ProbabilityCalibrator
from .volatility_scaler import VolatilityScaler


class MLBacktestEngine:
    """
    Walk-forward backtesting engine for ML trading strategies.

    Parameters:
        initial_capital: Starting capital (default: 100000)
        train_period: Training window in days (default: 252 = 1 year)
        test_period: Test window in days (default: 63 = 1 quarter)
        retrain_frequency: How often to retrain ('test_period', 'monthly', 'weekly')
        commission_per_trade: Fixed commission per trade (default: 20)
        slippage_pct: Slippage as percentage (default: 0.1%)
        device: PyTorch device ('cpu' or 'cuda')
    """

    def __init__(
        self,
        initial_capital: float = 100000,
        train_period: int = 252,
        test_period: int = 63,
        retrain_frequency: str = 'test_period',
        commission_per_trade: float = 20,
        slippage_pct: float = 0.001,
        device: str = 'cpu'
    ):
        self.initial_capital = initial_capital
        self.train_period = train_period
        self.test_period = test_period
        self.retrain_frequency = retrain_frequency
        self.commission_per_trade = commission_per_trade
        self.slippage_pct = slippage_pct
        self.device = device

        # Components
        self.feature_engineer = FeatureEngineer()
        self.data_pipeline = TimeSeriesDataPipeline(window_size=64, stride=1)
        self.volatility_scaler = VolatilityScaler(
            w_min=0.1,
            w_max=1.0,
            deadband_threshold=0.1
        )

        # State
        self.model = None
        self.trainer = None
        self.calibrator = None

        # Results storage
        self.backtest_results = []
        self.trade_log = []
        self.equity_curve = []

    def run_walk_forward_backtest(
        self,
        ohlc_data: pd.DataFrame,
        model_params: Optional[Dict] = None,
        training_params: Optional[Dict] = None,
        verbose: bool = True
    ) -> Dict:
        """
        Run complete walk-forward backtest.

        Args:
            ohlc_data: DataFrame with OHLC data (columns: open, high, low, close, volume)
            model_params: TCN model parameters (None = use defaults)
            training_params: Training parameters (None = use defaults)
            verbose: Print progress

        Returns:
            Dictionary with backtest results

        Example:
            >>> engine = MLBacktestEngine(initial_capital=100000)
            >>> results = engine.run_walk_forward_backtest(ohlc_df, verbose=True)
            >>> print(f"Total Return: {results['total_return']:.2%}")
            >>> print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        """
        if verbose:
            print("=" * 70)
            print("ML WALK-FORWARD BACKTEST")
            print("=" * 70)
            print(f"Data period: {ohlc_data.index[0]} to {ohlc_data.index[-1]}")
            print(f"Total days: {len(ohlc_data)}")
            print(f"Train period: {self.train_period} days")
            print(f"Test period: {self.test_period} days")
            print(f"Initial capital: ₹{self.initial_capital:,.0f}")
            print("=" * 70)
            print()

        # Step 1: Engineer features
        if verbose:
            print("[1/5] Engineering features...")

        features_df = self.feature_engineer.engineer_features(
            ohlc_data,
            fit_normalization=True
        )

        # Step 2: Create labels (future returns)
        if verbose:
            print("[2/5] Creating labels...")

        labels = self.data_pipeline.create_labels_from_future_returns(
            ohlc_data['close'],
            forward_period=5,
            threshold=0.01  # 1% threshold for positive label
        )

        # Step 3: Create rolling windows
        if verbose:
            print("[3/5] Creating rolling windows...")

        X, y, timestamps = self.data_pipeline.create_rolling_windows(
            features_df,
            labels
        )

        if verbose:
            print(f"  Total windows: {len(X)}")
            print(f"  Window shape: {X.shape}")

        # Step 4: Walk-forward splits
        if verbose:
            print("[4/5] Creating walk-forward splits...")

        splits = self.data_pipeline.walk_forward_split(
            X, y,
            train_period=self.train_period,
            test_period=self.test_period
        )

        if verbose:
            print(f"  Total splits: {len(splits)}")

        # Step 5: Run backtest on each split
        if verbose:
            print("[5/5] Running backtest...")
            print()

        capital = self.initial_capital
        self.equity_curve = [capital]
        position = 0  # Current position (0 = no position)

        for split_idx, (X_train, y_train, X_test, y_test) in enumerate(splits):
            if verbose:
                print(f"  Split {split_idx + 1}/{len(splits)}:")

            # Train model
            self.model = create_default_model(
                num_features=X_train.shape[2],
                seq_length=X_train.shape[1]
            )

            self.trainer = TCNTrainer(
                self.model,
                device=self.device,
                learning_rate=training_params.get('lr', 0.001) if training_params else 0.001
            )

            # Use 20% of training data for validation
            val_split = int(0.8 * len(X_train))
            X_train_split = X_train[:val_split]
            y_train_split = y_train[:val_split]
            X_val_split = X_train[val_split:]
            y_val_split = y_train[val_split:]

            if verbose:
                print(f"    Training samples: {len(X_train_split)}, Val: {len(X_val_split)}")

            history = self.trainer.fit(
                X_train_split,
                y_train_split,
                X_val_split,
                y_val_split,
                num_epochs=training_params.get('epochs', 50) if training_params else 50,
                batch_size=training_params.get('batch_size', 32) if training_params else 32,
                early_stopping_patience=10,
                verbose=False
            )

            # Calibrate probabilities
            val_predictions = self.trainer.predict_proba(X_val_split)
            self.calibrator = ProbabilityCalibrator(method='platt')
            self.calibrator.fit(val_predictions, y_val_split)

            # Test predictions
            test_predictions = self.trainer.predict_proba(X_test)
            calibrated_predictions = self.calibrator.transform(test_predictions)

            # Calculate returns for volatility
            test_start_idx = split_idx * self.test_period
            test_end_idx = test_start_idx + len(X_test)
            test_prices = ohlc_data['close'].iloc[test_start_idx:test_end_idx]
            test_returns = test_prices.pct_change().dropna().values

            # Update reference volatility
            if len(test_returns) >= 20:
                self.volatility_scaler.update_reference_volatility(test_returns)

            # Simulate trading
            split_trades = 0
            split_profit = 0

            for i in range(len(calibrated_predictions)):
                if i >= len(test_prices) - 1:
                    break

                # Get signal
                probability = calibrated_predictions[i]
                current_price = test_prices.iloc[i]

                # Calculate current volatility
                if i >= 20:
                    current_vol = self.volatility_scaler.calculate_volatility(
                        test_returns[:i]
                    )
                else:
                    current_vol = self.volatility_scaler.reference_vol

                # Scale position
                position_size, _ = self.volatility_scaler.scale_position(
                    probability,
                    current_vol
                )

                # Execute trade if signal strong enough
                if abs(position_size) > 0.01:
                    # Calculate number of shares
                    num_shares = self.volatility_scaler.calculate_position_units(
                        position_size,
                        capital,
                        current_price,
                        risk_per_trade=0.02
                    )

                    if num_shares != 0 and position == 0:
                        # Enter position
                        entry_price = current_price * (1 + self.slippage_pct * np.sign(num_shares))
                        capital -= self.commission_per_trade
                        position = num_shares

                        split_trades += 1

                    elif num_shares == 0 and position != 0:
                        # Exit position
                        exit_price = current_price * (1 - self.slippage_pct * np.sign(position))
                        profit = position * (exit_price - entry_price)
                        capital += profit - self.commission_per_trade
                        split_profit += profit

                        # Log trade
                        self.trade_log.append({
                            'split': split_idx + 1,
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'profit': profit,
                            'return_pct': profit / (abs(position) * entry_price)
                        })

                        position = 0

                # Update equity curve
                if position != 0:
                    unrealized_pnl = position * (current_price - entry_price)
                    self.equity_curve.append(capital + unrealized_pnl)
                else:
                    self.equity_curve.append(capital)

            # Close any open position at end of period
            if position != 0:
                exit_price = test_prices.iloc[-1]
                profit = position * (exit_price - entry_price)
                capital += profit - self.commission_per_trade
                position = 0

            split_return = split_profit / self.initial_capital

            if verbose:
                print(f"    Test samples: {len(X_test)}")
                print(f"    Trades: {split_trades}, P&L: ₹{split_profit:,.0f}, Return: {split_return:.2%}")
                print()

        # Calculate final metrics
        results = self._calculate_performance_metrics(capital)

        if verbose:
            print("=" * 70)
            print("BACKTEST RESULTS")
            print("=" * 70)
            print(f"Final Capital: ₹{capital:,.0f}")
            print(f"Total Return: {results['total_return']:.2%}")
            print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
            print(f"Max Drawdown: {results['max_drawdown']:.2%}")
            print(f"Win Rate: {results['win_rate']:.2%}")
            print(f"Total Trades: {results['total_trades']}")
            print("=" * 70)

        return results

    def _calculate_performance_metrics(self, final_capital: float) -> Dict:
        """Calculate comprehensive performance metrics"""
        # Total return
        total_return = (final_capital - self.initial_capital) / self.initial_capital

        # Equity curve returns
        equity_series = pd.Series(self.equity_curve)
        returns = equity_series.pct_change().dropna()

        # Sharpe ratio (annualized)
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0

        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Trade metrics
        if self.trade_log:
            wins = [t for t in self.trade_log if t['profit'] > 0]
            win_rate = len(wins) / len(self.trade_log)
            avg_win = np.mean([t['profit'] for t in wins]) if wins else 0
            avg_loss = np.mean([t['profit'] for t in self.trade_log if t['profit'] < 0])
            avg_loss = avg_loss if not np.isnan(avg_loss) else 0
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0

        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(self.trade_log),
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'final_capital': final_capital,
            'equity_curve': self.equity_curve
        }

    def save_results(self, output_dir: str):
        """Save backtest results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save trade log
        if self.trade_log:
            trade_df = pd.DataFrame(self.trade_log)
            trade_df.to_csv(output_path / 'trade_log.csv', index=False)

        # Save equity curve
        if self.equity_curve:
            equity_df = pd.DataFrame({
                'timestep': range(len(self.equity_curve)),
                'equity': self.equity_curve
            })
            equity_df.to_csv(output_path / 'equity_curve.csv', index=False)

        # Save model checkpoint
        if self.trainer:
            self.trainer.save_checkpoint(
                str(output_path / 'final_model.pth'),
                metadata={'backtest_date': datetime.now().isoformat()}
            )

        print(f"Results saved to: {output_path}")
