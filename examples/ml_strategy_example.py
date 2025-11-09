"""
Example: Train and Backtest TCN Neural Network Strategy

This script demonstrates the complete ML trading workflow:
1. Load historical OHLCV data
2. Train TCN model with walk-forward analysis
3. Backtest the model
4. Save results and model checkpoint
5. Use model for live trading (demo)

Usage:
    python examples/ml_strategy_example.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ML components
from src.ml import (
    FeatureEngineer,
    TimeSeriesDataPipeline,
    TCNTradingModel,
    create_default_model,
    VolatilityScaler,
    MLBacktestEngine
)
from src.ml.training.trainer import TCNTrainer, ProbabilityCalibrator


def generate_sample_ohlc_data(num_days: int = 500) -> pd.DataFrame:
    """
    Generate sample OHLCV data for demonstration.
    Replace this with actual data from your broker API.
    """
    print(f"Generating {num_days} days of sample OHLCV data...")

    np.random.seed(42)
    dates = pd.date_range(end=datetime.now(), periods=num_days, freq='D')

    # Simulate price movement (geometric Brownian motion)
    returns = np.random.normal(0.001, 0.02, num_days)
    prices = 2500 * np.exp(np.cumsum(returns))

    # Generate OHLCV
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        high = close * (1 + abs(np.random.normal(0, 0.01)))
        low = close * (1 - abs(np.random.normal(0, 0.01)))
        open_price = close * (1 + np.random.normal(0, 0.005))
        volume = int(np.random.uniform(100000, 500000))

        data.append({
            'date': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)

    print(f"✓ Generated data from {df.index[0]} to {df.index[-1]}")
    return df


def example_1_feature_engineering():
    """Example 1: Feature Engineering Pipeline"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Feature Engineering")
    print("=" * 70)

    # Load data
    ohlc_df = generate_sample_ohlc_data(500)

    # Initialize feature engineer
    engineer = FeatureEngineer(
        rsi_period=14,
        macd_fast=12,
        macd_slow=26,
        normalization='zscore'
    )

    # Engineer features
    features_df = engineer.engineer_features(ohlc_df, fit_normalization=True)

    print("\nEngineered Features:")
    print(f"  Shape: {features_df.shape}")
    print(f"  Features: {engineer.get_feature_names()}")
    print(f"\nFirst 5 rows:")
    print(features_df.head())

    # Save normalization params
    engineer.save_normalization_params('results/feature_normalization_params.json')
    print("\n✓ Normalization parameters saved to results/feature_normalization_params.json")

    return features_df


def example_2_create_training_data():
    """Example 2: Create Training Data with Rolling Windows"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Create Training Data")
    print("=" * 70)

    # Load data
    ohlc_df = generate_sample_ohlc_data(500)

    # Engineer features
    engineer = FeatureEngineer()
    features_df = engineer.engineer_features(ohlc_df)

    # Create labels (future returns)
    pipeline = TimeSeriesDataPipeline(window_size=64, stride=1)
    labels = pipeline.create_labels_from_future_returns(
        ohlc_df['close'],
        forward_period=5,
        threshold=0.01  # 1% threshold
    )

    # Create rolling windows
    X, y, timestamps = pipeline.create_rolling_windows(features_df, labels)

    print(f"\nRolling Windows Created:")
    print(f"  X shape: {X.shape}  # (num_windows, seq_length, num_features)")
    print(f"  y shape: {y.shape}  # (num_windows,)")
    print(f"  Timestamps: {len(timestamps)}")

    # Train/val/test split
    X_train, X_val, X_test, y_train, y_val, y_test, _, _, _ = pipeline.train_val_test_split(
        X, y, timestamps
    )

    print(f"\nData Splits:")
    print(f"  Train: {len(X_train)} samples")
    print(f"  Val: {len(X_val)} samples")
    print(f"  Test: {len(X_test)} samples")

    # Get statistics
    stats = pipeline.get_statistics(X_train, y_train)
    print(f"\nDataset Statistics:")
    for key, value in stats.items():
        if isinstance(value, (int, float)):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")

    return X_train, X_val, X_test, y_train, y_val, y_test


def example_3_train_model():
    """Example 3: Train TCN Model"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Train TCN Model")
    print("=" * 70)

    # Create training data
    X_train, X_val, X_test, y_train, y_val, y_test = example_2_create_training_data()

    # Create model
    model = create_default_model(num_features=12, seq_length=64)

    print(f"\nModel Architecture:")
    info = model.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Create trainer
    trainer = TCNTrainer(
        model,
        device='cpu',  # Change to 'cuda' if GPU available
        learning_rate=0.001,
        weight_decay=1e-5
    )

    # Train model
    print(f"\nTraining model...")
    history = trainer.fit(
        X_train, y_train,
        X_val, y_val,
        num_epochs=50,
        batch_size=32,
        early_stopping_patience=10,
        verbose=True
    )

    # Evaluate on test set
    test_loss, test_acc = trainer.validate(
        torch.utils.data.DataLoader(
            torch.utils.data.TensorDataset(
                torch.FloatTensor(X_test),
                torch.FloatTensor(y_test)
            ),
            batch_size=32
        )
    )

    print(f"\nTest Set Performance:")
    print(f"  Loss: {test_loss:.4f}")
    print(f"  Accuracy: {test_acc:.4f}")

    # Save model
    Path('results').mkdir(exist_ok=True)
    trainer.save_checkpoint(
        'results/tcn_model.pth',
        metadata={'test_accuracy': test_acc}
    )
    print(f"\n✓ Model saved to results/tcn_model.pth")

    return model, trainer


def example_4_volatility_scaling():
    """Example 4: Volatility-Scaled Position Sizing"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Volatility-Scaled Position Sizing")
    print("=" * 70)

    # Create scaler
    scaler = VolatilityScaler(
        w_min=0.1,
        w_max=1.0,
        vol_window=20,
        deadband_threshold=0.1
    )

    # Simulate returns
    np.random.seed(42)
    returns = np.random.normal(0.001, 0.02, 300)

    # Update reference volatility
    scaler.update_reference_volatility(returns)

    # Calculate current volatility
    current_vol = scaler.calculate_volatility(returns)

    print(f"\nVolatility Metrics:")
    print(f"  Reference volatility: {scaler.reference_vol:.3f}")
    print(f"  Current volatility: {current_vol:.3f}")

    # Test different signal probabilities
    print(f"\nPosition Sizing Examples:")
    test_probabilities = [0.3, 0.45, 0.55, 0.65, 0.75, 0.9]

    for prob in test_probabilities:
        position, explanation = scaler.scale_position(prob, current_vol)
        print(f"\n  Probability: {prob:.2f}")
        print(f"  Position Size: {position:.3f}")
        print(f"  {explanation}")


def example_5_walk_forward_backtest():
    """Example 5: Walk-Forward Backtest"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Walk-Forward Backtest")
    print("=" * 70)

    # Generate data (use more data for realistic backtest)
    ohlc_df = generate_sample_ohlc_data(1000)

    # Create backtest engine
    engine = MLBacktestEngine(
        initial_capital=100000,
        train_period=252,  # 1 year
        test_period=63,    # 1 quarter
        commission_per_trade=20,
        slippage_pct=0.001,
        device='cpu'
    )

    # Run backtest
    results = engine.run_walk_forward_backtest(
        ohlc_df,
        model_params={'tcn_channels': [64, 128, 128]},
        training_params={'epochs': 30, 'batch_size': 32, 'lr': 0.001},
        verbose=True
    )

    # Save results
    Path('results').mkdir(exist_ok=True)
    engine.save_results('results/')

    print(f"\n✓ Results saved to results/")

    return results


def example_6_live_trading_simulation():
    """Example 6: Live Trading Simulation"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Live Trading Simulation (Demo)")
    print("=" * 70)

    # Import strategy
    from src.strategies.tcn_ml_strategy import TCNMLStrategy

    # Check if model exists
    model_path = 'results/tcn_model.pth'
    if not Path(model_path).exists():
        print(f"\nWarning: Model not found at {model_path}")
        print("Run example_3_train_model() first to train a model.")
        return

    # Initialize strategy
    strategy = TCNMLStrategy(parameters={
        'model_path': model_path,
        'confidence_threshold': 0.6,
        'risk_per_trade': 0.02,
        'enable_volatility_scaling': True
    })

    print(f"\n{strategy.get_description()}")

    # Generate sample real-time data
    ohlc_df = generate_sample_ohlc_data(200)

    # Simulate quote
    quote = {
        'last_price': ohlc_df['close'].iloc[-1],
        'volume': ohlc_df['volume'].iloc[-1]
    }

    # Generate signal
    print(f"\nGenerating signal for {quote['last_price']:.2f}...")
    signal = strategy.generate_signal(
        symbol='RELIANCE',
        exchange='NSE',
        quote=quote,
        historical_data=ohlc_df,
        has_position=False
    )

    if signal:
        print(f"\n✓ Signal Generated:")
        for key, value in signal.items():
            if key != 'indicators':
                print(f"  {key}: {value}")

        if 'indicators' in signal:
            print(f"  indicators:")
            for k, v in signal['indicators'].items():
                print(f"    {k}: {v}")
    else:
        print(f"\n○ No signal generated (insufficient confidence or data)")


def main():
    """Run all examples"""
    print("\n" + "#" * 70)
    print("#  TCN Neural Network Trading Strategy - Complete Examples")
    print("#" * 70)

    try:
        # Example 1: Feature Engineering
        features = example_1_feature_engineering()

        # Example 2: Create Training Data
        data_splits = example_2_create_training_data()

        # Example 3: Train Model
        model, trainer = example_3_train_model()

        # Example 4: Volatility Scaling
        example_4_volatility_scaling()

        # Example 5: Walk-Forward Backtest
        # Uncomment to run (takes longer)
        # results = example_5_walk_forward_backtest()

        # Example 6: Live Trading Simulation
        example_6_live_trading_simulation()

        print("\n" + "#" * 70)
        print("#  ✓ All examples completed successfully!")
        print("#" * 70)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import torch

    # Create results directory
    Path('results').mkdir(exist_ok=True)

    main()
