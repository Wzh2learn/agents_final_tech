"""Unit tests for scripts/preprocess_msg.py pure helpers (classification,
filename sanitizing, URL capture). End-to-end runs require real .msg files
which live outside the repo (sensitive)."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "preprocess_msg",
    os.path.join(os.path.dirname(__file__), "..", "scripts", "preprocess_msg.py"))
pm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pm)


class TestClassify:
    def test_pdf(self):
        assert pm.classify("对账单.pdf") == "pdf"

    def test_images(self):
        for name in ("scan.PNG", "fax.tiff", "photo.jpeg"):
            assert pm.classify(name) == "image"

    def test_other(self):
        assert pm.classify("data.xlsx") == "other"
        assert pm.classify("archive.zip") == "other"


class TestSafeName:
    def test_keeps_cjk(self):
        assert pm.safe_name("转发 对账单_2026.pdf") == "转发 对账单_2026.pdf"

    def test_strips_path_separators(self):
        assert "/" not in pm.safe_name("a/b.pdf")
        bs = chr(92)
        assert bs not in pm.safe_name("a" + bs + "b.pdf")

    def test_empty_fallback(self):
        assert pm.safe_name("") == "unnamed"


class TestUrlCapture:
    def test_captures_http_urls(self):
        body = "请下载 https://example.com/a.pdf 查看\nhttp://x.cn/b?id=1"
        urls = pm.URL_RE.findall(body)
        assert "https://example.com/a.pdf" in urls
        assert any(u.startswith("http://x.cn/b") for u in urls)

    def test_no_urls(self):
        assert pm.URL_RE.findall("正文没有链接") == []
