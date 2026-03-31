"""Tests for ML modules — analytics always works, others gracefully degrade."""

import pytest
from ml.analytics import detect_anomalies, cluster_companies, forecast_linear


class TestAnomalyDetection:
    def test_detects_outlier(self):
        values = [10.0, 11.0, 10.5, 10.2, 50.0, 10.8]
        anomalies = detect_anomalies(values, sensitivity=2.0)
        assert 4 in anomalies  # 50.0 is the outlier

    def test_no_anomalies_in_uniform_data(self):
        values = [10.0, 10.1, 9.9, 10.0, 10.2]
        assert detect_anomalies(values) == []

    def test_too_few_values(self):
        assert detect_anomalies([1.0]) == []
        assert detect_anomalies([]) == []

    def test_all_same_values(self):
        assert detect_anomalies([5.0, 5.0, 5.0, 5.0]) == []


class TestClustering:
    def test_clusters_companies(self):
        matrix = [
            [100e9, 50e9, 10e9, 1000, 50, 10000],
            [90e9, 45e9, 9e9, 900, 40, 9000],
            [1e6, 500e3, 0, 10, 0, 50],
            [2e6, 600e3, 0, 15, 0, 60],
            [50e9, 20e9, 5e9, 500, 20, 5000],
        ]
        keys = ["big1", "big2", "tiny1", "tiny2", "mid1"]
        clusters = cluster_companies(matrix, keys, n_clusters=2)

        assert len(clusters) == 2
        all_keys = []
        for v in clusters.values():
            all_keys.extend(v)
        assert sorted(all_keys) == sorted(keys)

    def test_empty_matrix(self):
        clusters = cluster_companies([], [], n_clusters=2)
        assert clusters == {}


class TestForecast:
    def test_linear_extrapolation(self):
        values = [100.0, 110.0, 120.0, 130.0]
        forecasts = forecast_linear(values, periods=2)
        assert len(forecasts) == 2
        assert forecasts[0]["forecast"] > 130.0
        assert forecasts[0]["period"] == 1

    def test_two_values(self):
        forecasts = forecast_linear([100.0, 110.0], periods=2)
        assert len(forecasts) == 2
        assert forecasts[0]["forecast"] > 110.0

    def test_single_value_returns_empty(self):
        assert forecast_linear([100.0], periods=3) == []

    def test_empty_values(self):
        assert forecast_linear([], periods=2) == []


class TestFinBERTGraceful:
    def test_finbert_graceful_without_transformers(self):
        """FinBERT should return neutral defaults if transformers not installed."""
        from ml.finbert import analyze_sentiment
        results = analyze_sentiment(["Test text"])
        assert len(results) == 1
        assert "label" in results[0]
        assert "score" in results[0]

    def test_sentiment_score_graceful(self):
        from ml.finbert import sentiment_score
        score = sentiment_score("Revenue beat expectations")
        assert -1.0 <= score <= 1.0


class TestEmbeddingsGraceful:
    def test_embed_object_text(self):
        from ml.embeddings import embed_object
        text = embed_object("company", {"name": "Apple", "description": "Tech company", "sector": "Technology"})
        assert "Apple" in text
        assert "Technology" in text

    def test_embed_texts_graceful(self):
        from ml.embeddings import embed_texts
        result = embed_texts(["Test"])
        # Returns empty if model not available
        assert isinstance(result, list)


class TestNERGraceful:
    def test_extract_entities_graceful(self):
        from ml.ner import extract_entities
        result = extract_entities("Tim Cook is the CEO of Apple in Cupertino")
        assert isinstance(result, dict)
        assert "persons" in result
