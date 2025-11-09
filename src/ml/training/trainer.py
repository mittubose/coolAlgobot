"""
Training Pipeline for TCN Trading Model

Handles model training, validation, calibration, and checkpointing.
Includes early stopping based on validation Sharpe ratio.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from typing import Dict, Optional, Tuple, Callable
from pathlib import Path
import json
from datetime import datetime


class TCNTrainer:
    """
    Trainer for TCN trading models.

    Features:
        - Binary cross-entropy loss with class weights
        - Gradient clipping for stability
        - Early stopping on validation metric
        - Learning rate scheduling
        - Model checkpointing
        - Training history tracking

    Args:
        model: TCN model to train
        device: Device to train on ('cpu' or 'cuda')
        learning_rate: Initial learning rate (default: 0.001)
        weight_decay: L2 regularization (default: 1e-5)
        class_weights: Weights for handling class imbalance (default: None)
    """

    def __init__(
        self,
        model: nn.Module,
        device: str = 'cpu',
        learning_rate: float = 0.001,
        weight_decay: float = 1e-5,
        class_weights: Optional[torch.Tensor] = None
    ):
        self.model = model.to(device)
        self.device = device

        # Optimizer
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )

        # Loss function
        if class_weights is not None:
            class_weights = class_weights.to(device)

        self.criterion = nn.BCELoss(weight=class_weights)

        # Learning rate scheduler (reduce on plateau)
        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='max',  # Maximize validation metric
            factor=0.5,
            patience=5,
            verbose=True
        )

        # Training history
        self.history = {
            'train_loss': [],
            'val_loss': [],
            'train_acc': [],
            'val_acc': [],
            'learning_rates': []
        }

        # Best model tracking
        self.best_val_metric = -np.inf
        self.best_model_state = None
        self.patience_counter = 0

    def train_epoch(
        self,
        train_loader: DataLoader,
        clip_grad_norm: float = 1.0
    ) -> Tuple[float, float]:
        """
        Train for one epoch.

        Args:
            train_loader: Training data loader
            clip_grad_norm: Maximum gradient norm for clipping

        Returns:
            (average_loss, accuracy)
        """
        self.model.train()
        total_loss = 0.0
        correct = 0
        total = 0

        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device).unsqueeze(1)  # (batch, 1)

            # Forward pass
            self.optimizer.zero_grad()
            predictions = self.model(X_batch)

            # Calculate loss
            loss = self.criterion(predictions, y_batch)

            # Backward pass
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(
                self.model.parameters(),
                max_norm=clip_grad_norm
            )

            self.optimizer.step()

            # Track metrics
            total_loss += loss.item() * len(X_batch)

            # Calculate accuracy
            predicted_labels = (predictions > 0.5).float()
            correct += (predicted_labels == y_batch).sum().item()
            total += len(y_batch)

        avg_loss = total_loss / total
        accuracy = correct / total

        return avg_loss, accuracy

    @torch.no_grad()
    def validate(self, val_loader: DataLoader) -> Tuple[float, float]:
        """
        Validate model.

        Args:
            val_loader: Validation data loader

        Returns:
            (average_loss, accuracy)
        """
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0

        for X_batch, y_batch in val_loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device).unsqueeze(1)

            # Forward pass
            predictions = self.model(X_batch)

            # Calculate loss
            loss = self.criterion(predictions, y_batch)

            # Track metrics
            total_loss += loss.item() * len(X_batch)

            # Calculate accuracy
            predicted_labels = (predictions > 0.5).float()
            correct += (predicted_labels == y_batch).sum().item()
            total += len(y_batch)

        avg_loss = total_loss / total
        accuracy = correct / total

        return avg_loss, accuracy

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        num_epochs: int = 100,
        batch_size: int = 32,
        early_stopping_patience: int = 10,
        verbose: bool = True
    ) -> Dict:
        """
        Train model with early stopping.

        Args:
            X_train: Training features (num_samples, seq_length, num_features)
            y_train: Training labels (num_samples,)
            X_val: Validation features
            y_val: Validation labels
            num_epochs: Maximum number of epochs
            batch_size: Batch size
            early_stopping_patience: Epochs to wait before early stopping
            verbose: Print progress

        Returns:
            Training history dictionary
        """
        # Create data loaders
        train_dataset = TensorDataset(
            torch.FloatTensor(X_train),
            torch.FloatTensor(y_train)
        )
        val_dataset = TensorDataset(
            torch.FloatTensor(X_val),
            torch.FloatTensor(y_val)
        )

        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False
        )

        # Training loop
        for epoch in range(num_epochs):
            # Train
            train_loss, train_acc = self.train_epoch(train_loader)

            # Validate
            val_loss, val_acc = self.validate(val_loader)

            # Update history
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['train_acc'].append(train_acc)
            self.history['val_acc'].append(val_acc)
            self.history['learning_rates'].append(
                self.optimizer.param_groups[0]['lr']
            )

            # Learning rate scheduling
            self.scheduler.step(val_acc)

            # Print progress
            if verbose and (epoch + 1) % 5 == 0:
                print(
                    f"Epoch {epoch + 1}/{num_epochs}: "
                    f"Train Loss: {train_loss:.4f}, "
                    f"Train Acc: {train_acc:.4f}, "
                    f"Val Loss: {val_loss:.4f}, "
                    f"Val Acc: {val_acc:.4f}"
                )

            # Early stopping check
            if val_acc > self.best_val_metric:
                self.best_val_metric = val_acc
                self.best_model_state = self.model.state_dict().copy()
                self.patience_counter = 0

                if verbose:
                    print(f"  → New best validation accuracy: {val_acc:.4f}")
            else:
                self.patience_counter += 1

                if self.patience_counter >= early_stopping_patience:
                    if verbose:
                        print(
                            f"\nEarly stopping triggered after {epoch + 1} epochs. "
                            f"Best val accuracy: {self.best_val_metric:.4f}"
                        )
                    break

        # Load best model
        if self.best_model_state is not None:
            self.model.load_state_dict(self.best_model_state)

        return self.history

    def save_checkpoint(self, filepath: str, metadata: Optional[Dict] = None):
        """
        Save model checkpoint.

        Args:
            filepath: Path to save checkpoint
            metadata: Optional metadata dictionary
        """
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'history': self.history,
            'best_val_metric': self.best_val_metric,
            'timestamp': datetime.now().isoformat()
        }

        if metadata is not None:
            checkpoint['metadata'] = metadata

        torch.save(checkpoint, filepath)

    def load_checkpoint(self, filepath: str) -> Dict:
        """
        Load model checkpoint.

        Args:
            filepath: Path to checkpoint file

        Returns:
            Metadata dictionary
        """
        checkpoint = torch.load(filepath, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        self.history = checkpoint['history']
        self.best_val_metric = checkpoint['best_val_metric']

        return checkpoint.get('metadata', {})

    @torch.no_grad()
    def predict_proba(self, X: np.ndarray, batch_size: int = 32) -> np.ndarray:
        """
        Generate probability predictions.

        Args:
            X: Input features (num_samples, seq_length, num_features)
            batch_size: Batch size for prediction

        Returns:
            Probabilities (num_samples,)
        """
        self.model.eval()

        dataset = TensorDataset(torch.FloatTensor(X))
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        predictions = []
        for (X_batch,) in loader:
            X_batch = X_batch.to(self.device)
            pred = self.model(X_batch)
            predictions.append(pred.cpu().numpy())

        return np.concatenate(predictions).flatten()

    def get_learning_curve_data(self) -> Dict:
        """Get data for plotting learning curves"""
        return {
            'epochs': list(range(1, len(self.history['train_loss']) + 1)),
            'train_loss': self.history['train_loss'],
            'val_loss': self.history['val_loss'],
            'train_acc': self.history['train_acc'],
            'val_acc': self.history['val_acc'],
            'learning_rates': self.history['learning_rates']
        }


class ProbabilityCalibrator:
    """
    Calibrate model probabilities using Platt scaling or isotonic regression.

    Args:
        method: 'platt' (logistic regression) or 'isotonic'
    """

    def __init__(self, method: str = 'platt'):
        self.method = method
        self.calibrator = None

    def fit(self, probabilities: np.ndarray, y_true: np.ndarray):
        """
        Fit calibrator on validation set.

        Args:
            probabilities: Model predictions (num_samples,)
            y_true: True labels (num_samples,)
        """
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.linear_model import LogisticRegression

        # Reshape for sklearn
        probabilities = probabilities.reshape(-1, 1)

        if self.method == 'platt':
            # Platt scaling (logistic regression)
            self.calibrator = LogisticRegression()
            self.calibrator.fit(probabilities, y_true)

        elif self.method == 'isotonic':
            # Isotonic regression
            from sklearn.isotonic import IsotonicRegression
            self.calibrator = IsotonicRegression(out_of_bounds='clip')
            self.calibrator.fit(probabilities.flatten(), y_true)

    def transform(self, probabilities: np.ndarray) -> np.ndarray:
        """
        Apply calibration to probabilities.

        Args:
            probabilities: Uncalibrated probabilities (num_samples,)

        Returns:
            Calibrated probabilities (num_samples,)
        """
        if self.calibrator is None:
            raise ValueError("Must call fit() before transform()")

        if self.method == 'platt':
            probabilities = probabilities.reshape(-1, 1)
            calibrated = self.calibrator.predict_proba(probabilities)[:, 1]
        else:
            calibrated = self.calibrator.predict(probabilities.flatten())

        return calibrated
