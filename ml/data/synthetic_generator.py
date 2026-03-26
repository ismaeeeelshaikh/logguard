import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from typing import Tuple

FEATURE_NAMES = [
    "log_volume",
    "error_rate",
    "warn_rate",
    "unique_template_count",
    "template_entropy",
    "avg_response_time_ms",
    "p95_response_time_ms",
    # template_vector[0..99] will be added separately
]

class LogDataGenerator:
    """
    Generates realistic synthetic log feature data for model training.
    
    Normal behavior: Gaussian distributions around typical server metrics.
    Anomaly types:
      1. Spike anomaly     — sudden surge in error_rate or response_time
      2. Volume anomaly    — dramatic drop in log_volume (server silent)
      3. Pattern anomaly   — unusual template distribution (new attack pattern)
      4. Memory leak       — gradual increase in response_time over sequence
    """
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        random.seed(seed)
    
    def generate_normal_window(self) -> dict:
        """Generate one normal 60-second window feature vector."""
        log_volume = max(10, int(np.random.normal(500, 80)))
        error_rate = max(0, min(1, np.random.beta(1.5, 30)))  # Usually < 5%
        warn_rate  = max(0, min(1, np.random.beta(3, 20)))
        unique_templates = int(np.random.normal(12, 3))
        entropy    = max(0, np.random.normal(2.8, 0.4))
        avg_rt     = max(10, np.random.normal(150, 30))
        p95_rt     = avg_rt * np.random.uniform(1.8, 2.5)
        
        # Template vector: sparse, mostly zeros
        template_vector = np.zeros(100)
        active_templates = random.sample(range(100), k=min(unique_templates, 20))
        for idx in active_templates:
            template_vector[idx] = np.random.dirichlet(np.ones(len(active_templates)))[0]
        
        return {
            "log_volume": log_volume,
            "error_rate": error_rate,
            "warn_rate": warn_rate,
            "unique_template_count": unique_templates,
            "template_entropy": entropy,
            "avg_response_time_ms": avg_rt,
            "p95_response_time_ms": p95_rt,
            "template_vector": template_vector.tolist()
        }
    
    def generate_anomaly_window(self, anomaly_type: str = "random") -> dict:
        """Generate one anomalous window."""
        if anomaly_type == "random":
            anomaly_type = random.choice(["spike", "silent", "pattern", "slowdown"])
        
        base = self.generate_normal_window()
        
        if anomaly_type == "spike":
            base["error_rate"] = np.random.uniform(0.3, 0.9)
            base["log_volume"] = base["log_volume"] * random.uniform(3, 8)
            base["p95_response_time_ms"] = np.random.uniform(8000, 30000)
            
        elif anomaly_type == "silent":
            # Server going quiet — possibly crashed
            base["log_volume"] = random.randint(0, 15)
            base["error_rate"] = 0.0
            
        elif anomaly_type == "pattern":
            # Unusual template distribution — possible injection attack
            base["template_entropy"] = np.random.uniform(4.5, 6.0)
            base["unique_template_count"] = random.randint(40, 80)
            # Activate many unusual template slots
            tv = np.zeros(100)
            for i in range(60):
                tv[random.randint(0, 99)] = random.uniform(0.01, 0.05)
            base["template_vector"] = tv.tolist()
            
        elif anomaly_type == "slowdown":
            # Gradual memory leak / resource exhaustion
            base["avg_response_time_ms"] = np.random.uniform(3000, 10000)
            base["p95_response_time_ms"] = np.random.uniform(8000, 25000)
            base["error_rate"] = np.random.uniform(0.1, 0.3)
        
        return base
    
    def generate_dataset(
        self,
        n_normal: int = 50000,
        n_anomaly: int = 2500,  # 5% contamination
        sequence_length: int = 30  # for LSTM
    ) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        """
        Generates full dataset and splits into sequences.
        Returns: df (all rows), X_val (normal only), X_test (mixed with labels)
        """
        rows = []
        labels = []
        
        for _ in range(n_normal):
            rows.append(self.generate_normal_window())
            labels.append(0)
            
        for _ in range(n_anomaly):
            rows.append(self.generate_anomaly_window())
            labels.append(1)
            
        # Shuffle for a static test set
        combined = list(zip(rows, labels))
        random.shuffle(combined)
        rows, labels = zip(*combined)
        
        df = pd.DataFrame(list(rows))
        df['is_anomaly'] = list(labels)
        
        # Flatten template vector into individual cols
        tv_df = pd.DataFrame(df['template_vector'].to_list(), columns=[f"tv_{i}" for i in range(100)])
        df = pd.concat([df.drop('template_vector', axis=1), tv_df], axis=1)
        
        return df, None, None  # Sequences logic to be done in data_loader

if __name__ == "__main__":
    gen = LogDataGenerator()
    df, _, _ = gen.generate_dataset(n_normal=1000, n_anomaly=50)
    print(df.head())
    print("Anomalies:", df['is_anomaly'].sum())
