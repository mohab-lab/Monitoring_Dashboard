# ml/anomaly.py
import pandas as pd

def detect_anomalies(df, col):
    """Simple anomaly detector: finds NaN or out-of-range values."""
    if col not in df.columns:
        return []
    s = df[col]
    anomalies = []
    if pd.api.types.is_numeric_dtype(s):
        anomalies = s[(s < 0) | (s > 120)].index.tolist()
    else:
        anomalies = s[s.isna()].index.tolist()
    return anomalies
