"""S3① 数值 claim 确定性核验产品化单测 (2026-08-12)。"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from biz.number_grounding import check_answer, norm


def test_thousands_tolerance():
    r = check_answer("总资产为 2,216,940.90 元", "资产总值=2216940.90")
    assert r["pass"]
    assert r["numbers"] == ["2,216,940.90"]


def test_ungrounded_fails():
    r = check_answer("总资产为 999.99 元", "资产总值=2216940.90")
    assert not r["pass"]
    assert r["ungrounded"] == ["999.99"]


def test_mask_counted_not_failed():
    r = check_answer("总市值 4013****.28 元", "chunk 里没有任何数值")
    assert r["pass"]
    assert r["masked"] == ["4013****.28"]
    assert r["numbers"] == []


def test_date_and_small_int_exempt():
    r = check_answer("截至20231031, 共 3 笔, 序号 2", "毫无匹配")
    assert r["pass"]
    assert r["numbers"] == []


def test_source_line_stripped():
    r = check_answer("总资产 100.5 元。 出处: 样本=sample_x_20231031.pdf, 表=t1", "100.5")
    assert r["pass"]


def test_norm():
    assert norm("2,216, 940.90") == "2216940.90"
