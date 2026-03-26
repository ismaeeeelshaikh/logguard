"""
Fetch training data from Elasticsearch and PostgreSQL feedback tables.

Used by the retraining pipeline to get:
  1. Historical log features from Elasticsearch
  2. User feedback labels from PostgreSQL
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ml.data.synthetic_generator import LogDataGenerator
from ml.data.data_loader import create_sequences


def fetch_from_elasticsearch(
    es_host: str = "localhost",
    es_port: int = 9200,
    index: str = "logguard-features-*",
    days_back: int = 30,
    max_docs: int = 100000
) -> pd.DataFrame:
    """
    Fetch historical log feature data from Elasticsearch.
    
    In production, this queries ES for processed feature windows.
    Falls back to synthetic data if ES is unavailable.
    """
    try:
        from elasticsearch import Elasticsearch
        
        es = Elasticsearch([{"host": es_host, "port": es_port, "scheme": "http"}])
        
        if not es.ping():
            raise ConnectionError("Cannot connect to Elasticsearch")
        
        query = {
            "query": {
                "range": {
                    "window_start": {
                        "gte": f"now-{days_back}d",
                        "lte": "now"
                    }
                }
            },
            "size": max_docs,
            "sort": [{"window_start": "desc"}]
        }
        
        response = es.search(index=index, body=query)
        hits = response["hits"]["hits"]
        
        if not hits:
            print("⚠️  No data found in Elasticsearch. Using synthetic data.")
            return _generate_synthetic_fallback()
        
        records = [hit["_source"] for hit in hits]
        df = pd.DataFrame(records)
        print(f"✅ Fetched {len(df)} records from Elasticsearch")
        return df
        
    except Exception as e:
        print(f"⚠️  Elasticsearch unavailable ({e}). Using synthetic data.")
        return _generate_synthetic_fallback()


def fetch_feedback_labels(
    db_host: str = "localhost",
    db_port: int = 5432,
    db_name: str = "logguard",
    db_user: str = "logguard",
    db_password: str = "pass",
    days_back: int = 30
) -> pd.DataFrame:
    """
    Fetch user feedback labels from PostgreSQL anomaly_feedback table.
    
    Returns DataFrame with columns: feature_id, is_anomaly (from feedback)
    """
    try:
        import psycopg2
        
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )
        
        query = f"""
            SELECT 
                feature_window_id as feature_id,
                CASE 
                    WHEN feedback_type = 'true_positive' THEN 1
                    WHEN feedback_type = 'false_positive' THEN 0
                    ELSE NULL
                END as is_anomaly
            FROM anomaly_feedback
            WHERE created_at > NOW() - INTERVAL '{days_back} days'
            AND feedback_type IN ('true_positive', 'false_positive')
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"✅ Fetched {len(df)} feedback labels from PostgreSQL")
        return df
        
    except Exception as e:
        print(f"⚠️  PostgreSQL unavailable ({e}). Returning empty feedback.")
        return pd.DataFrame(columns=["feature_id", "is_anomaly"])


def fetch_feedback_dataset(
    days_back: int = 30
) -> Tuple[np.ndarray, np.ndarray]:
    """
    High-level function to fetch complete training dataset
    with feedback labels.
    
    Returns:
        X_all: 2D feature array (n_samples, n_features)
        y_all: Binary labels array
    """
    # Try to fetch from real sources
    features_df = fetch_from_elasticsearch(days_back=days_back)
    feedback_df = fetch_feedback_labels(days_back=days_back)
    
    if len(feedback_df) > 0 and "feature_id" in features_df.columns:
        # Merge features with feedback labels
        merged = features_df.merge(
            feedback_df, on="feature_id", how="left"
        )
        merged["is_anomaly"] = merged["is_anomaly"].fillna(0).astype(int)
        
        feature_cols = [
            c for c in merged.columns
            if c not in ["feature_id", "is_anomaly", "window_start", "window_end",
                         "host", "tenant_id", "sequence_window_id"]
        ]
        
        X = merged[feature_cols].values.astype(np.float32)
        y = merged["is_anomaly"].values
        
        return X, y
    
    # Fallback to synthetic
    print("ℹ️  Using synthetic data for training.")
    return _generate_synthetic_with_labels()


def _generate_synthetic_fallback() -> pd.DataFrame:
    """Generate synthetic feature data as fallback."""
    gen = LogDataGenerator(seed=42)
    df, _, _ = gen.generate_dataset(n_normal=10000, n_anomaly=500)
    return df


def _generate_synthetic_with_labels() -> Tuple[np.ndarray, np.ndarray]:
    """Generate synthetic data with anomaly labels."""
    gen = LogDataGenerator(seed=42)
    df, _, _ = gen.generate_dataset(n_normal=10000, n_anomaly=500)
    
    y = df["is_anomaly"].values
    X = df.drop("is_anomaly", axis=1).values.astype(np.float32)
    
    return X, y


if __name__ == "__main__":
    X, y = fetch_feedback_dataset(days_back=30)
    print(f"Dataset shape: {X.shape}")
    print(f"Anomaly rate: {y.mean()*100:.1f}%")
