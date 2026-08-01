"""Tests for Prometheus metrics endpoint and instrumentation.

Verifies:
1. /api/metrics returns text/plain with expected metric names.
2. After a parse request, m1_parse_total counter increases.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from utils.metrics import registry, m1_parse_total, m2_qa_total


class TestMetricsEndpoint:
    """Metrics exposition endpoint."""

    def test_metrics_endpoint_format(self):
        """GET /api/metrics returns text/plain with expected metric names."""
        from fastapi import FastAPI
        from starlette.testclient import TestClient
        from web.routers.metrics import router

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get("/api/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        body = resp.text
        # Check HELP/TYPE lines exist for our metrics
        assert "# HELP m1_parse_total" in body
        assert "# TYPE m1_parse_total counter" in body
        assert "# HELP m2_qa_total" in body
        assert "# HELP m1_parse_duration_seconds" in body
        assert "# TYPE m1_parse_duration_seconds histogram" in body

    def test_metrics_increment(self):
        """After incrementing, counter value appears in exposition."""
        # Record baseline
        m1_parse_total.inc({"format": "txt", "status": "ok"})
        m1_parse_total.inc({"format": "txt", "status": "ok"})

        output = registry.expose()
        # Should have at least 2 for txt/ok
        assert 'm1_parse_total{format="txt",status="ok"}' in output
        # Parse the value
        for line in output.splitlines():
            if line.startswith('m1_parse_total{format="txt",status="ok"}'):
                val = float(line.split()[-1])
                assert val >= 2
                break
        else:
            pytest.fail("m1_parse_total{format=txt,status=ok} not found")

    def test_histogram_buckets(self):
        """Histogram exposition includes bucket lines."""
        from utils.metrics import m1_parse_duration_seconds
        m1_parse_duration_seconds.observe(0.3, {"format": "pdf"})
        output = registry.expose()
        assert 'm1_parse_duration_seconds_bucket{format="pdf",le="0.5"}' in output
        assert 'm1_parse_duration_seconds_bucket{format="pdf",le="+Inf"}' in output
        assert "m1_parse_duration_seconds_sum" in output
        assert "m1_parse_duration_seconds_count" in output
