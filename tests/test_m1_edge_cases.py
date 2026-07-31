"""Edge case and robustness tests for M1 parse-file endpoint.

Tests boundary conditions: empty files, oversized files, non-statement docs,
encoding anomalies, and concurrent requests.
"""

import io
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from fastapi.testclient import TestClient

try:
    from main import app
    client = TestClient(app)
    HAS_APP = True
except Exception:
    HAS_APP = False

pytestmark = pytest.mark.skipif(not HAS_APP, reason="FastAPI app not importable")


class TestEmptyFile:
    """Empty or near-empty files should return graceful errors."""

    def test_empty_txt(self):
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("success", "error")
        if data["status"] == "success":
            assert data["result"]["table_count"] == 0

    def test_whitespace_only_txt(self):
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("spaces.txt", b"   \n\n  \t  \n", "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("success", "error")

    def test_empty_pdf(self):
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("success", "error")


class TestOversizedFile:
    """Large files should be handled gracefully."""

    def test_large_txt_no_crash(self):
        chunk = b"A" * 1024 * 1024
        large_content = chunk * 10
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("large.txt", large_content, "text/plain")},
        )
        assert resp.status_code in (200, 413)
        if resp.status_code == 200:
            data = resp.json()
            assert data["status"] in ("success", "error")

    def test_very_long_single_line(self):
        content = b"X" * 100000 + b"\n"
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("longline.txt", content, "text/plain")},
        )
        assert resp.status_code == 200


class TestNonStatementDoc:
    """Non-financial documents should return 0 tables gracefully."""

    def test_random_chinese_text(self):
        content = "今天天气很好，我们去公园散步吧。" * 50
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("random.txt", content.encode("utf-8"), "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        if data["status"] == "success":
            assert data["result"]["table_count"] == 0

    def test_code_file(self):
        content = b"def hello():\n    print('world')\n    return 42\n" * 100
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("code.txt", content, "text/plain")},
        )
        assert resp.status_code == 200

    def test_html_content(self):
        content = b"<html><body><h1>Hello</h1><p>Not a statement</p></body></html>"
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("page.txt", content, "text/plain")},
        )
        assert resp.status_code == 200


class TestEncodingAnomalies:
    """Various encodings should be handled."""

    def test_gbk_encoded_txt(self):
        text = "客户姓名：测试客户\n资产账号：1234567890\n资金余额：10000.00"
        gbk_bytes = text.encode("gbk")
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("gbk.txt", gbk_bytes, "text/plain")},
        )
        assert resp.status_code == 200

    def test_utf16_encoded_txt(self):
        text = "客户姓名：测试客户\n资产账号：1234567890\n"
        utf16_bytes = text.encode("utf-16")
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("utf16.txt", utf16_bytes, "text/plain")},
        )
        assert resp.status_code == 200

    def test_latin1_encoded_txt(self):
        content = b"Customer: Test\nBalance: 1000.00\n\xc0\xc1\xc2"
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("latin1.txt", content, "text/plain")},
        )
        assert resp.status_code == 200

    def test_random_bytes(self):
        import random
        random.seed(42)
        content = bytes(random.randint(0, 255) for _ in range(1000))
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("random.bin", content, "text/plain")},
        )
        assert resp.status_code == 200


class TestUnsupportedFormats:
    """Unsupported file types should return clear errors."""

    def test_exe_file(self):
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("malware.exe", b"MZ\x90\x00", "application/octet-stream")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
        assert "不支持" in data.get("error", "")

    def test_image_file(self):
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("photo.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"

    def test_no_extension(self):
        resp = client.post(
            "/api/m1/parse-file",
            files={"file": ("noext", b"some content", "application/octet-stream")},
        )
        assert resp.status_code == 200


class TestConcurrentRequests:
    """Concurrent requests should be handled correctly."""

    def test_three_concurrent_parses(self):
        content = b"test content for concurrent parse\n" * 100

        def make_request(i):
            resp = client.post(
                "/api/m1/parse-file",
                files={"file": (f"concurrent_{i}.txt", content, "text/plain")},
            )
            return resp.status_code

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i) for i in range(3)]
            results = [f.result() for f in as_completed(futures)]

        assert all(code == 200 for code in results), f"Got: {results}"

    def test_rapid_sequential_requests(self):
        content = b"rapid test\n" * 50
        for i in range(10):
            resp = client.post(
                "/api/m1/parse-file",
                files={"file": (f"rapid_{i}.txt", content, "text/plain")},
            )
            assert resp.status_code == 200