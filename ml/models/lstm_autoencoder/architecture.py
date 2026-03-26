"""
LSTM Autoencoder architecture for sequence anomaly detection.

Architecture:
  Input (seq_len, n_features)
    → LSTM(128) → LSTM(64) → Dense(32) [ENCODER]
    → RepeatVector(seq_len)
    → LSTM(64) → LSTM(128) [DECODER]
    → TimeDistributed(Dense(n_features))
    → Output (seq_len, n_features)

Anomaly score = Mean Squared Reconstruction Error.
If reconstruction is poor → sequence is anomalous.
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import numpy as np


def build_lstm_autoencoder(
    sequence_length: int = 30,
    n_features: int = 107,          # 7 base features + 100 template vector
    encoding_dim: int = 32,         # Bottleneck size
    lstm_units: list = None,        # Encoder layers
    dropout_rate: float = 0.2
) -> keras.Model:
    """
    Build an LSTM Autoencoder for sequence anomaly detection.
    
    Args:
        sequence_length: Number of time steps in each input sequence
        n_features: Number of features per time step
        encoding_dim: Size of the bottleneck layer
        lstm_units: List of LSTM layer sizes [encoder_1, encoder_2]
        dropout_rate: Dropout rate between layers
    
    Returns:
        Compiled Keras model
    """
    if lstm_units is None:
        lstm_units = [128, 64]
    
    # ── ENCODER ──────────────────────────────────────────────
    encoder_input = keras.Input(
        shape=(sequence_length, n_features),
        name="encoder_input"
    )
    
    x = layers.LSTM(
        lstm_units[0],
        return_sequences=True,
        name="encoder_lstm_1"
    )(encoder_input)
    x = layers.Dropout(dropout_rate)(x)
    
    x = layers.LSTM(
        lstm_units[1],
        return_sequences=False,  # Compress to fixed vector
        name="encoder_lstm_2"
    )(x)
    x = layers.Dropout(dropout_rate)(x)
    
    # Bottleneck: compressed representation
    encoded = layers.Dense(
        encoding_dim,
        activation="relu",
        name="bottleneck"
    )(x)
    
    # ── DECODER ──────────────────────────────────────────────
    # Repeat the bottleneck vector for each time step
    x = layers.RepeatVector(sequence_length, name="repeat_vector")(encoded)
    
    x = layers.LSTM(
        lstm_units[1],
        return_sequences=True,
        name="decoder_lstm_1"
    )(x)
    x = layers.Dropout(dropout_rate)(x)
    
    x = layers.LSTM(
        lstm_units[0],
        return_sequences=True,
        name="decoder_lstm_2"
    )(x)
    
    # Reconstruct each time step's feature vector
    decoded = layers.TimeDistributed(
        layers.Dense(n_features, activation="linear"),
        name="output"
    )(x)
    
    model = keras.Model(
        inputs=encoder_input,
        outputs=decoded,
        name="LSTM_Autoencoder"
    )
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="mse",
        metrics=["mae"]
    )
    
    return model


def get_reconstruction_errors(
    model: keras.Model,
    X_sequences: np.ndarray,
    batch_size: int = 256
) -> np.ndarray:
    """
    Compute per-sample reconstruction error (MSE).
    High error = anomalous sequence.
    
    Args:
        model: Trained LSTM autoencoder
        X_sequences: Input sequences, shape (n_samples, seq_len, n_features)
        batch_size: Prediction batch size
    
    Returns:
        Array of shape (n_samples,) with MSE per sequence
    """
    X_reconstructed = model.predict(X_sequences, batch_size=batch_size, verbose=0)
    
    # MSE per sample (mean over sequence and feature dimensions)
    mse = np.mean(np.power(X_sequences - X_reconstructed, 2), axis=(1, 2))
    return mse
