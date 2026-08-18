"""K3 schema 漂移注入器 v0 测试 — 确定性复现 + 分类学覆盖。

- 同 seed 同输入 -> 输出字节级一致（跨进程也一致, 用独立 subprocess 复跑验证）
- 6 类注入各至少 1 例断言（在注入映射清单里各类型计数 >= 1）
- 注入必变化 + 映射清单与输出表一致 + 未命中列保持原样
- 不触碰既有测试与冻结文件
"""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts", "research"))

from drift_inject import DriftInjector, _sha256_hex, _dump_json

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXPECTED_TYPES = {
    "alias_variant", "mixed_lang", "unit_suffix",
    "date_variant", "ocr_similar", "prefix_noise",
}

# 复刻 TAT-QA 归一化形态的小型确定性样本（不带外网依赖）
TINY_TABLES = [
    {"uid": "t-001", "table": [
        ["Trade Date", "Revenue", "Market Value", "Total Assets"],
        ["2020-01-01", "100.0", "200.0", "300.0"],
        ["2020-01-02", "110.0", "210.0", "310.0"],
    ]},
    {"uid": "t-002", "table": [
        ["Closing Price", "Trading Volume", "Dividends", "Net Income"],
        ["10.5", "10000", "0.5", "5.0"],
        ["10.8", "12000", "0.6", "6.0"],
    ]},
    {"uid": "t-003", "table": [
        ["Cash Flow", "Operating Profit", "Net Income", "Revenue"],
        ["1.0", "2.0", "3.0", "4.0"],
    ]},
    {"uid": "t-004", "table": [
        ["A", "Revenue(date)", "equity", "liabilit"],
        ["1", "2", "3", "4"],
    ]},
    {"uid": "t-005", "table": [
        ["Grant Date", "Closing Price", "Interest", "Market Value",
         "Operating Profit", "Cash Flow", "Revenue", "Dividends",
         "Total Assets", "Net Income", "Trading Volume", "RD Expenses"],
        ["2019-01-01"] + ["x"] * 11,
    ]},
    {"uid": "t-006", "table": [
        ["T", "U", "Revenue", "Cash flow", "interest", "liabilities"],
        ["1", "2", "3", "4", "5", "6"],
    ]},
    {"uid": "t-007", "table": [
        ["Assets", "Income", "Interest", "Revenue", "Liabilities", "Capital",
         "Profit", "Dividend", "Volume", "Closing", "Operating", "Equity"],
        ["1"] * 12,
    ]},
    {"uid": "t-008", "table": [
        ["Revenue", "Cash flow", "Trade Date", "Dividends", "Account", "Interest"],
        ["1", "2", "3", "4", "5", "6"],
    ]},
]


def _run_cli(args):
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = str(0)
    return subprocess.run(
        [sys.executable, os.path.join(REPO, "scripts", "research", "drift_inject.py")] + args,
        capture_output=True, text=True, env=env, cwd=REPO,
    )


@pytest.fixture()
def tiny_input(tmp_path):
    p = tmp_path / "tables.json"
    _dump_json(TINY_TABLES, p)
    return p


def test_deterministic_same_process(tiny_input, tmp_path):
    o1 = tmp_path / "o1"
    o2 = tmp_path / "o2"
    _run_cli(["--input", str(tiny_input), "--out", str(o1), "--ratio", "0.3", "--seed", "42"])
    _run_cli(["--input", str(tiny_input), "--out", str(o2), "--ratio", "0.3", "--seed", "42"])
    for name in ("injected_tables.json", "injection_map.json", "report.json"):
        a = (o1 / name).read_bytes()
        b = (o2 / name).read_bytes()
        assert a == b, f"{name} 字节级不一致"


def test_deterministic_cross_process(tiny_input, tmp_path):
    """不同 seed 输出必须不同（说明注入确实生效且与 PRNG 相关）。"""
    o1 = tmp_path / "o1"
    o2 = tmp_path / "o2"
    _run_cli(["--input", str(tiny_input), "--out", str(o1), "--ratio", "0.3", "--seed", "42"])
    _run_cli(["--input", str(tiny_input), "--out", str(o2), "--ratio", "0.3", "--seed", "1"])
    assert (o1 / "injected_tables.json").read_bytes() != (o2 / "injected_tables.json").read_bytes()


def test_all_six_types_present(tiny_input, tmp_path):
    # ratio=0.3 (单位后缀类, 小表数据); ratio=1.0 全表强制 (其余 5 类)
    for ratio, expected in ((0.3, {"unit_suffix"}), (1.0, EXPECTED_TYPES - {"unit_suffix"})):
        out_dir = tmp_path / f"o{ratio}"
        _run_cli(["--input", str(tiny_input), "--out", str(out_dir), "--ratio", str(ratio), "--seed", "42"])
        mp = json.loads((out_dir / "injection_map.json").read_text(encoding="utf-8"))["mapping"]
        types = {e["type"] for e in mp}
        assert expected <= types, f"ratio={ratio} missing types: {expected - types}"


def test_injection_always_changes_header(tiny_input, tmp_path):
    out_dir = tmp_path / "o"
    _run_cli(["--input", str(tiny_input), "--out", str(out_dir), "--ratio", "1.0", "--seed", "42"])
    mp = json.loads((out_dir / "injection_map.json").read_text(encoding="utf-8"))["mapping"]
    for e in mp:
        assert e["original"] != e["injected"]


def test_map_consistent_with_output(tiny_input, tmp_path):
    out_dir = tmp_path / "o"
    _run_cli(["--input", str(tiny_input), "--out", str(out_dir), "--ratio", "0.3", "--seed", "42"])
    it = json.loads((out_dir / "injected_tables.json").read_text(encoding="utf-8"))
    mp = json.loads((out_dir / "injection_map.json").read_text(encoding="utf-8"))["mapping"]
    by_uid = {t["uid"]: t["table"] for t in it}
    assert len(by_uid) == len(it)
    for e in mp:
        assert by_uid[e["uid"]][e["row"]][e["col"]] == e["injected"]


def test_untouched_columns_stay_identical(tiny_input, tmp_path):
    out_dir = tmp_path / "o"
    _run_cli(["--input", str(tiny_input), "--out", str(out_dir), "--ratio", "0.3", "--seed", "42"])
    it = json.loads((out_dir / "injected_tables.json").read_text(encoding="utf-8"))
    mp = json.loads((out_dir / "injection_map.json").read_text(encoding="utf-8"))["mapping"]
    inj_cols = {(e["uid"], e["col"]) for e in mp}
    by_uid = {t["uid"]: t["table"] for t in it}
    for t in TINY_TABLES:
        for ci, h in enumerate(t["table"][0]):
            if (t["uid"], ci) not in inj_cols:
                assert by_uid[t["uid"]][0][ci] == h


def test_real_data_full_run_and_stats(tmp_path):
    """TAT-QA 全量（城市样本）——注入统计与报告数字一致。"""
    input_p = os.path.join(REPO, "data", "research", "drift_v0", "input", "tatqa_tables.json")
    out_dir = os.path.join(REPO, "data", "research", "drift_v0", "output")
    if not os.path.exists(input_p):
        pytest.skip("TAT-QA full input not present (data/ 为 gitignored 大件目录)")
    p = tmp_path / "report.json"
    r = _run_cli(["--input", input_p, "--out", str(tmp_path),
                  "--ratio", "0.3", "--seed", "42"])
    assert r.returncode == 0, r.stderr
    rep = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    it = json.loads((tmp_path / "injected_tables.json").read_text(encoding="utf-8"))
    assert len(it) == rep["n_tables_total"]
    assert rep["n_injections_total"] == sum(rep["by_type"].values())
    # 报告数字与注入映射清单一致
    mp = json.loads((tmp_path / "injection_map.json").read_text(encoding="utf-8"))["mapping"]
    assert len(mp) == rep["n_injections_total"]
    from collections import Counter
    assert dict(Counter(e["type"] for e in mp)) == rep["by_type"]


def test_injector_api_deterministic_hash():
    out = DriftInjector(seed=42, ratio=0.3, tables=TINY_TABLES).run()
    h1 = _sha256_hex(out["tables"])
    out2 = DriftInjector(seed=42, ratio=0.3, tables=TINY_TABLES).run()
    assert h1 == _sha256_hex(out2["tables"])
    assert len(out["mapping"]) > 0
