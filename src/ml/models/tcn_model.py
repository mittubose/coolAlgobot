"""
Temporal Convolutional Network (TCN) Model for Trading Signal Generation

Implements a TCN architecture with calibrated sigmoid output for
probabilistic trade signal generation (0 = no trade, 1 = strong buy/sell).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Optional, Tuple
import numpy as np


class TCNBlock(nn.Module):
    """
    Single TCN block with dilated causal convolution.

    Args:
        in_channels: Number of input channels
        out_channels: Number of output channels
        kernel_size: Convolution kernel size
        dilation: Dilation factor for temporal receptive field
        dropout: Dropout probability
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        dilation: int,
        dropout: float = 0.3
    ):
        super().__init__()

        # Padding for causal convolution (no future information)
        padding = (kernel_size - 1) * dilation

        self.conv = nn.Conv1d(
            in_channels,
            out_channels,
            kernel_size,
            padding=padding,
            dilation=dilation
        )

        # Chomp to remove future padding (causal)
        self.chomp = Chomp1d(padding)

        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)

        # Residual connection
        self.downsample = nn.Conv1d(in_channels, out_channels, 1) \
            if in_channels != out_channels else None

        self.init_weights()

    def init_weights(self):
        """Initialize weights"""
        self.conv.weight.data.normal_(0, 0.01)
        if self.downsample is not None:
            self.downsample.weight.data.normal_(0, 0.01)

    def forward(self, x):
        """
        Forward pass

        Args:
            x: (batch_size, in_channels, seq_length)

        Returns:
            (batch_size, out_channels, seq_length)
        """
        out = self.conv(x)
        out = self.chomp(out)
        out = self.relu(out)
        out = self.dropout(out)

        # Residual connection
        res = x if self.downsample is None else self.downsample(x)
        return self.relu(out + res)


class Chomp1d(nn.Module):
    """Remove padding from causal convolution"""

    def __init__(self, chomp_size):
        super().__init__()
        self.chomp_size = chomp_size

    def forward(self, x):
        return x[:, :, :-self.chomp_size].contiguous() if self.chomp_size > 0 else x


class TemporalConvNet(nn.Module):
    """
    Multi-layer Temporal Convolutional Network.

    Args:
        num_inputs: Number of input features
        num_channels: List of channel sizes for each layer
        kernel_size: Convolution kernel size
        dropout: Dropout probability
    """

    def __init__(
        self,
        num_inputs: int,
        num_channels: list,
        kernel_size: int = 3,
        dropout: float = 0.3
    ):
        super().__init__()
        layers = []
        num_levels = len(num_channels)

        for i in range(num_levels):
            dilation = 2 ** i  # Exponentially increasing receptive field
            in_channels = num_inputs if i == 0 else num_channels[i - 1]
            out_channels = num_channels[i]

            layers.append(
                TCNBlock(
                    in_channels,
                    out_channels,
                    kernel_size,
                    dilation,
                    dropout
                )
            )

        self.network = nn.Sequential(*layers)

    def forward(self, x):
        """
        Forward pass

        Args:
            x: (batch_size, num_inputs, seq_length)

        Returns:
            (batch_size, num_channels[-1], seq_length)
        """
        return self.network(x)


class TCNTradingModel(nn.Module):
    """
    Complete TCN-based trading signal model with calibrated sigmoid output.

    Architecture:
        Input (batch, num_features, seq_length)
        -> TCN layers (with dilated convolutions)
        -> Global Average Pooling
        -> Fully connected layers
        -> Calibrated sigmoid head
        -> Output probability (batch, 1)

    Args:
        num_features: Number of input features (default: 12)
        seq_length: Input sequence length (default: 64)
        tcn_channels: Channel sizes for TCN layers (default: [64, 128, 128])
        kernel_size: TCN kernel size (default: 3)
        dropout: Dropout probability (default: 0.3)
        fc_hidden_dim: Hidden dimension for FC layer (default: 64)
    """

    def __init__(
        self,
        num_features: int = 12,
        seq_length: int = 64,
        tcn_channels: list = None,
        kernel_size: int = 3,
        dropout: float = 0.3,
        fc_hidden_dim: int = 64
    ):
        super().__init__()

        if tcn_channels is None:
            tcn_channels = [64, 128, 128]

        self.num_features = num_features
        self.seq_length = seq_length

        # TCN backbone
        self.tcn = TemporalConvNet(
            num_inputs=num_features,
            num_channels=tcn_channels,
            kernel_size=kernel_size,
            dropout=dropout
        )

        # Global average pooling (reduces seq_length to 1)
        self.gap = nn.AdaptiveAvgPool1d(1)

        # Fully connected layers
        self.fc1 = nn.Linear(tcn_channels[-1], fc_hidden_dim)
        self.relu = nn.ReLU()
        self.dropout_fc = nn.Dropout(dropout)

        # Calibrated sigmoid head for probability output
        self.fc2 = nn.Linear(fc_hidden_dim, 32)
        self.fc3 = nn.Linear(32, 1)

    def forward(self, x):
        """
        Forward pass

        Args:
            x: (batch_size, seq_length, num_features) - NOTE: seq and features are swapped
               OR (batch_size, num_features, seq_length) if already transposed

        Returns:
            (batch_size, 1) - probability of positive signal [0, 1]
        """
        # Handle both input formats
        if x.shape[1] == self.seq_length and x.shape[2] == self.num_features:
            # Input is (batch, seq, features) -> transpose to (batch, features, seq)
            x = x.transpose(1, 2)

        # TCN processing
        tcn_out = self.tcn(x)  # (batch, tcn_channels[-1], seq_length)

        # Global average pooling
        gap_out = self.gap(tcn_out)  # (batch, tcn_channels[-1], 1)
        gap_out = gap_out.squeeze(-1)  # (batch, tcn_channels[-1])

        # Fully connected layers
        fc_out = self.fc1(gap_out)  # (batch, fc_hidden_dim)
        fc_out = self.relu(fc_out)
        fc_out = self.dropout_fc(fc_out)

        # Sigmoid head
        fc_out = self.fc2(fc_out)  # (batch, 32)
        fc_out = self.relu(fc_out)
        probability = torch.sigmoid(self.fc3(fc_out))  # (batch, 1)

        return probability

    def predict_signal(self, x: torch.Tensor, threshold: float = 0.5) -> Tuple[int, float]:
        """
        Generate trading signal from input.

        Args:
            x: Input features (seq_length, num_features) for single sample
            threshold: Decision threshold (default: 0.5)

        Returns:
            (signal, confidence):
                signal: 1 (buy/bullish), 0 (neutral), -1 (sell/bearish)
                confidence: probability value [0, 1]
        """
        self.eval()
        with torch.no_grad():
            if x.dim() == 2:
                x = x.unsqueeze(0)  # Add batch dimension

            probability = self.forward(x).item()

            if probability > threshold:
                signal = 1  # Bullish
            elif probability < (1 - threshold):
                signal = -1  # Bearish
            else:
                signal = 0  # Neutral

            return signal, probability

    def get_receptive_field(self) -> int:
        """
        Calculate the effective receptive field of the TCN.

        Returns:
            Number of timesteps the model can see
        """
        kernel_size = 3
        num_layers = len(self.tcn.network)

        receptive_field = 1
        for i in range(num_layers):
            dilation = 2 ** i
            receptive_field += (kernel_size - 1) * dilation

        return receptive_field

    def count_parameters(self) -> int:
        """Count total trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def get_model_info(self) -> Dict:
        """Get model architecture information"""
        return {
            'num_features': self.num_features,
            'seq_length': self.seq_length,
            'tcn_channels': [module.conv.out_channels for module in self.tcn.network],
            'receptive_field': self.get_receptive_field(),
            'total_parameters': self.count_parameters()
        }


def create_default_model(num_features: int = 12, seq_length: int = 64) -> TCNTradingModel:
    """
    Create default TCN trading model with recommended hyperparameters.

    Args:
        num_features: Number of input features
        seq_length: Input sequence length

    Returns:
        Initialized TCN model
    """
    model = TCNTradingModel(
        num_features=num_features,
        seq_length=seq_length,
        tcn_channels=[64, 128, 128],
        kernel_size=3,
        dropout=0.3,
        fc_hidden_dim=64
    )

    return model


# Example usage
if __name__ == "__main__":
    # Create model
    model = create_default_model(num_features=12, seq_length=64)

    print("Model Info:")
    info = model.get_model_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    # Test forward pass
    batch_size = 32
    x = torch.randn(batch_size, 64, 12)  # (batch, seq, features)

    output = model(x)
    print(f"\nInput shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Output range: [{output.min().item():.4f}, {output.max().item():.4f}]")

    # Test single prediction
    single_input = torch.randn(64, 12)  # (seq, features)
    signal, confidence = model.predict_signal(single_input, threshold=0.6)
    print(f"\nSingle prediction:")
    print(f"  Signal: {signal} ({'Bullish' if signal == 1 else 'Bearish' if signal == -1 else 'Neutral'})")
    print(f"  Confidence: {confidence:.4f}")
