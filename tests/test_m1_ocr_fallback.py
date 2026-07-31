"""Unit tests for OCR fallback logic in scripts/m1_statement_parser.py.

All external dependencies (vision-8004, PaddleOCR, fitz) are mocked.
"""

import json
import os
import sys
from unittest import mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import m1_statement_parser as parser
from m1_statement_parser import (
    _ocr_fallback,
    _try_vision_ocr,
    _vision_ocr_one,
    _parse_markdown_tables,
    _try_paddleocr,
)


# ---------------------------------------------------------------------------
# _vision_ocr_one: mock HTTP call to :8004
# ---------------------------------------------------------------------------

class TestVisionOcrOne:
    def test_mock_response_parsed(self):
        """A successful vision-8004 response returns extracted text."""
        fake_body = json.dumps({
            "choices": [{"message": {"content": "| 证券 | 市值 |\n|---|---|\n| A | 100 |"}}],
            "model": "test-model",
        }).encode()

        fake_resp = mock.MagicMock()
        fake_resp.read.return_value = fake_body
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = mock.MagicMock(return_value=False)

        with mock.patch("urllib.request.urlopen", return_value=fake_resp):
            result = _vision_ocr_one(b"\x89PNG_fake_image_bytes")
        assert "证券" in result
        assert "100" in result

    def test_failure_returns_empty(self):
        """Network error -> graceful empty string."""
        with mock.patch("urllib.request.urlopen", side_effect=ConnectionError("down")):
            result = _vision_ocr_one(b"img")
        assert result == ""


# ---------------------------------------------------------------------------
# _try_vision_ocr: parallel dispatch
# ---------------------------------------------------------------------------

class TestTryVisionOcr:
    def test_empty_images_returns_empty(self):
        assert _try_vision_ocr([]) == ""

    def test_multiple_images_concatenated(self):
        with mock.patch.object(parser, "_vision_ocr_one", side_effect=["text1", "text2"]):
            result = _try_vision_ocr([b"img1", b"img2"])
        assert "text1" in result
        assert "text2" in result


# ---------------------------------------------------------------------------
# _ocr_fallback: orchestration
# ---------------------------------------------------------------------------

class TestOcrFallback:
    def test_ocr_triggered_when_no_text_pdf(self):
        """PDF with images but no text layer triggers OCR path."""
        with mock.patch.object(parser, "_extract_pdf_page_images", return_value=[b"img"]), \
             mock.patch.object(parser, "_try_paddleocr", return_value=""), \
             mock.patch.object(parser, "_try_vision_ocr", return_value="OCR text here"):
            text, engine = _ocr_fallback("/fake/path.pdf", "pdf")
        assert text == "OCR text here"
        assert engine == "vision-8004"

    def test_ocr_not_triggered_for_text_pdf(self):
        """PDF with no extractable images returns empty (text-layer path handles it)."""
        with mock.patch.object(parser, "_extract_pdf_page_images", return_value=[]):
            text, engine = _ocr_fallback("/fake/text.pdf", "pdf")
        assert text == ""
        assert engine == ""

    def test_paddleocr_preferred_over_vision(self):
        """When PaddleOCR succeeds, vision is not called."""
        with mock.patch.object(parser, "_extract_pdf_page_images", return_value=[b"img"]), \
             mock.patch.object(parser, "_try_paddleocr", return_value="paddle result"), \
             mock.patch.object(parser, "_try_vision_ocr") as mock_vision:
            text, engine = _ocr_fallback("/fake/path.pdf", "pdf")
        assert text == "paddle result"
        assert engine == "paddleocr-vl"
        mock_vision.assert_not_called()

    def test_unsupported_kind_returns_empty(self):
        text, engine = _ocr_fallback("/fake/file.xyz", "xyz")
        assert text == ""
        assert engine == ""


# ---------------------------------------------------------------------------
# _parse_markdown_tables (OCR output parsing)
# ---------------------------------------------------------------------------

class TestOcrMarkdownParsing:
    def test_ocr_table_extracted(self):
        md_text = (
            "Some header text\n"
            "| 证券名称 | 市值 | 数量 |\n"
            "| --- | --- | --- |\n"
            "| 平安银行 | 100.00 | 200 |\n"
            "| 招商银行 | 200.00 | 300 |\n"
            "\nFooter note\n"
        )
        tables = _parse_markdown_tables(md_text)
        assert len(tables) == 1
        assert tables[0].headers == ["证券名称", "市值", "数量"]
        assert len(tables[0].rows) == 2
        assert tables[0].rows[0][0] == "平安银行"
