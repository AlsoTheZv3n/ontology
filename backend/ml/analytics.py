"""
Lightweight analytics using numpy (and optionally scikit-learn for clustering).
No heavy dependencies — these functions should always work.
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def detect_anomalies(values: list[float], sensitivity: float = 2.0) -> list[int]:
    """
    Z-score anomaly detection.

    Returns the indices of values whose absolute Z-score exceeds `sensitivity`.
    Requires at least 3 data points; returns empty list otherwise.
    """
    if len(values) < 3:
        return []

    arr = np.array(values, dtype=float)
    mean = np.nanmean(arr)
    std = np.nanstd(arr)

    if std == 0:
        return []

    z_scores = np.abs((arr - mean) / std)
    return [int(i) for i in np.where(z_scores > sensitivity)[0]]


def cluster_companies(
    feature_matrix: list[list[float]],
    company_keys: list[str],
    n_clusters: int = 5,
) -> dict[int, list[str]]:
    """
    K-Means clustering with StandardScaler + SimpleImputer.

    Returns {cluster_id: [company_key, ...], ...}.
    Falls back to a single cluster containing all companies if sklearn is unavailable.
    """
    if not feature_matrix or not company_keys:
        return {}

    # Cap n_clusters to number of samples
    n_samples = len(feature_matrix)
    n_clusters = min(n_clusters, n_samples)

    try:
        from sklearn.cluster import KMeans
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        logger.warning("scikit-learn not installed — returning all companies in one cluster")
        return {0: list(company_keys)}

    try:
        X = np.array(feature_matrix, dtype=float)

        # Impute missing values, then scale
        imputer = SimpleImputer(strategy="mean")
        X = imputer.fit_transform(X)

        scaler = StandardScaler()
        X = scaler.fit_transform(X)

        kmeans = KMeans(n_clusters=n_clusters, n_init=10, random_state=42)
        labels = kmeans.fit_predict(X)

        clusters: dict[int, list[str]] = {}
        for label, key in zip(labels, company_keys):
            clusters.setdefault(int(label), []).append(key)

        return clusters

    except Exception as exc:
        logger.error("Clustering failed: %s", exc)
        return {0: list(company_keys)}


def forecast_linear(values: list[float], periods: int = 4) -> list[dict]:
    """
    Simple linear extrapolation using least-squares regression.

    Returns [{"period": 1, "forecast": 123.4}, ...] for each future period.
    Requires at least 2 data points; returns empty list otherwise.
    """
    if len(values) < 2 or periods < 1:
        return []

    arr = np.array(values, dtype=float)
    x = np.arange(len(arr))

    # Least-squares linear fit: y = slope * x + intercept
    coeffs = np.polyfit(x, arr, 1)
    slope, intercept = coeffs[0], coeffs[1]

    forecasts = []
    for i in range(1, periods + 1):
        future_x = len(arr) - 1 + i
        predicted = slope * future_x + intercept
        forecasts.append({"period": i, "forecast": round(float(predicted), 4)})

    return forecasts
