import os
import numpy as np
import pandas as pd
from typing import Tuple
from .synthetic_generator import LogDataGenerator

def load_data(
    n_normal_train: int = 50000,
    n_normal_val: int = 10000,
    n_test: int = 5000,
    anomaly_ratio: float = 0.05,
    sequence_length: int = 30
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generates and formats data for Model Training.
    
    Returns:
    - X_train (normal data only) for training Autoencoders / IF
    - X_val (normal data only) for threshold tuning
    - X_test (mixed normal + anomalies)
    - y_test (labels for test set)
    """
    gen = LogDataGenerator()
    
    print(f"Generating {(n_normal_train + n_normal_val)} normal records...")
    df_normal, _, _ = gen.generate_dataset(n_normal=n_normal_train + n_normal_val, n_anomaly=0)
    
    # Train/Val split
    train_df = df_normal.iloc[:n_normal_train]
    val_df = df_normal.iloc[n_normal_train:]
    
    print(f"Generating {n_test} test records with {anomaly_ratio * 100}% anomalies...")
    n_anomaly = int(n_test * anomaly_ratio)
    test_df, _, _ = gen.generate_dataset(n_normal=(n_test - n_anomaly), n_anomaly=n_anomaly)
    
    X_train = train_df.drop('is_anomaly', axis=1).values
    X_val = val_df.drop('is_anomaly', axis=1).values
    
    X_test = test_df.drop('is_anomaly', axis=1).values
    y_test = test_df['is_anomaly'].values
    
    return X_train, X_val, X_test, y_test

def create_sequences(data: np.ndarray, seq_length: int) -> np.ndarray:
    """
    Convert 2D array (samples, features) to 3D array (samples, seq_length, features)
    for RNN/LSTM models.
    """
    sequences = []
    for i in range(len(data) - seq_length + 1):
        sequences.append(data[i:(i + seq_length)])
    return np.array(sequences)

if __name__ == "__main__":
    X_train, X_val, X_test, y_test = load_data(
        n_normal_train=1000,
        n_normal_val=200,
        n_test=500
    )
    print(f"X_train shape: {X_train.shape}")
    print(f"X_test shape: {X_test.shape}")
    print(f"Anomalies in test: {np.sum(y_test)}")
