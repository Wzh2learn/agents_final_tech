"""CLI 兼容性测试 — biz.m1_statement_parser (P1.3, 2026-08-08 沉淀)。

覆盖：
- 前缀过滤跳过文件时的 stderr 显式警告（列明文件名）
- --files 显式文件列表绕过 sample_/mapping_ 前缀过滤
- OCR 预算政策：M1_OCR_BUDGET_SECONDS 耗尽时逐引擎 skipped-budget 留痕
- schema 自学习建议的去重合并 (_append_schema_suggestions / _sanitize_suggestions)
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import m1_statement_parser as m


@pytest.fixture
def samples_dir(tmp_path):
    (tmp_path / "sample_ok.txt").write_text(
        "客户全称：测试产品\n资产总值：100.00\n", encoding="utf-8")
    (tmp_path / "random.txt").write_text(
        "客户全称：另一个产品\n", encoding="utf-8")
    return tmp_path


def test_prefix_filter_warns_on_skipped_files(samples_dir, capsys):
    out_json = samples_dir / "out.json"
    rc = m.main(["--samples-dir", str(samples_dir), "--no-llm",
                 "--json", str(out_json)])
    err = capsys.readouterr().err
    assert rc == 0
    assert "[warn]" in err and "random.txt" in err
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert [r["file"] for r in data] == ["sample_ok.txt"]


def test_files_flag_bypasses_prefix_filter(samples_dir):
    out_json = samples_dir / "out2.json"
    rc = m.main(["--samples-dir", str(samples_dir), "--no-llm",
                 "--files", "random.txt", "--json", str(out_json)])
    assert rc == 0
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["file"] == "random.txt"


def test_files_flag_missing_file_warns_and_skips(samples_dir, capsys):
    out_json = samples_dir / "out3.json"
    rc = m.main(["--samples-dir", str(samples_dir), "--no-llm",
                 "--files", "nope.txt", "--json", str(out_json)])
    err = capsys.readouterr().err
    assert rc == 0
    assert "nope.txt" in err
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data == []


def test_ocr_budget_zero_skips_vlm_and_vision(monkeypatch):
    monkeypatch.setattr(m, "_OCR_BUDGET_SECONDS", 0.0)
    monkeypatch.setattr(m, "_extract_pdf_page_images", lambda path: [b"fakeimg"])
    monkeypatch.setattr(m, "_try_paddleocr", lambda images, name: "")
    called = {}
    monkeypatch.setattr(m, "_try_vlm_table",
                        lambda images: called.setdefault("vlm", 1) or "x")
    monkeypatch.setattr(m, "_try_vision_ocr",
                        lambda images: called.setdefault("vision", 1) or "x")
    text, engine = m._ocr_fallback("/fake/x.pdf", "pdf")
    assert (text, engine) == ("", "")
    assert "vlm" not in called and "vision" not in called
    statuses = {e["engine"]: e["status"] for e in m._ocr_engine_log}
    assert statuses["paddleocr-vl"] == "empty"
    assert statuses["vlm-8007"] == "skipped-budget"
    assert statuses["vision-8004"] == "skipped-budget"


def test_ocr_budget_enough_prefers_vlm(monkeypatch):
    monkeypatch.setattr(m, "_OCR_BUDGET_SECONDS", 240.0)
    monkeypatch.setattr(m, "_extract_pdf_page_images", lambda path: [b"fakeimg"])
    monkeypatch.setattr(m, "_try_paddleocr", lambda images, name: "")
    monkeypatch.setattr(m, "_try_vlm_table",
                        lambda images: "| a | b |\n| - | - |\n| 1 | 2 |")
    text, engine = m._ocr_fallback("/fake/x.pdf", "pdf")
    assert engine == "vlm-8007"
    assert m._ocr_engine_log[-1]["status"] == "ok"


def test_ocr_engine_error_falls_back(monkeypatch):
    monkeypatch.setattr(m, "_OCR_BUDGET_SECONDS", 240.0)
    monkeypatch.setattr(m, "_extract_pdf_page_images", lambda path: [b"fakeimg"])
    monkeypatch.setattr(m, "_try_paddleocr", lambda images, name: "")

    def boom(images):
        raise RuntimeError("vlm down")
    monkeypatch.setattr(m, "_try_vlm_table", boom)
    monkeypatch.setattr(m, "_try_vision_ocr", lambda images: "| a |\n| - |\n| 1 |")
    text, engine = m._ocr_fallback("/fake/x.pdf", "pdf")
    assert engine == "vision-8004"
    statuses = {e["engine"]: e["status"] for e in m._ocr_engine_log}
    assert statuses["vlm-8007"] == "error"


def test_append_schema_suggestions_dedup(tmp_path, monkeypatch):
    target = tmp_path / "schema_suggestions.json"
    monkeypatch.setattr(m, "SCHEMA_SUGGESTIONS_PATH", str(target))
    item = {"sample": "s.txt", "table": "交易对账单", "raw_column": "交易费用",
            "standard_field": "交易费用", "confidence": "medium", "reason": "r"}
    assert m._append_schema_suggestions([dict(item)]) == 1
    assert m._append_schema_suggestions([dict(item, confidence="high")]) == 0
    data = json.loads(target.read_text(encoding="utf-8"))
    sugg = data["suggestions"]
    assert len(sugg) == 1
    assert sugg[0]["count"] == 2
    assert sugg[0]["confidence"] == "high"  # 置信度只升不降


def test_sanitize_suggestions_filters_bad_entries():
    allowed = {"交易费用", "分红方式"}
    raw = [
        {"column": "交易费用", "standard_field": "交易费用",
         "confidence": "high", "reason": "同名"},
        {"column": "不在unmapped集合", "standard_field": "x", "confidence": "high"},
        {"column": "分红方式", "standard_field": "", "confidence": "high"},
        {"column": "交易费用", "standard_field": "y", "confidence": "INVALID"},
        "junk",
    ]
    out = m._sanitize_suggestions(raw, allowed)
    assert len(out) == 1
    assert out[0]["raw_column"] == "交易费用"
