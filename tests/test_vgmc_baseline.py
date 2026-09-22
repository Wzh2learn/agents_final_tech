"""小 A 基线层单测（段 D, 设计稿 2026-08-27_small_a_baseline_protocol_design.md）。"""
import importlib.util
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))


def _load():
    spec = importlib.util.spec_from_file_location(
        "vgmc_exp1", os.path.join(REPO, "research", "vgmc_exp1.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_fewshot_pool_from_fix_only():
    m = _load()
    fix = [f"fix-{index}" for index in range(11)]
    meas = ["meas-0", "meas-1"]
    corpus = {
        uid: {
            "inj_header": [f"{uid}-header-0", f"{uid}-header-1"],
            "entries": [{"col": col, "original": f"field-{col}"} for col in range(2)],
        }
        for uid in meas + fix
    }
    pool = m.fewshot_pool(corpus, fix)
    expected = [
        {"header": f"{uid}-header-{col}", "canonical": f"field-{col}"}
        for uid in fix[:10]
        for col in range(2)
    ]
    assert pool == expected
    excluded_headers = {
        header for uid in meas + fix[10:] for header in corpus[uid]["inj_header"]
    }
    assert excluded_headers.isdisjoint(item["header"] for item in pool)
    assert m.fewshot_pool(corpus, []) == []
    assert m.fewshot_pool(corpus, fix[:1]) == expected[:2]


def test_memory_text_deterministic_and_capped():
    m = _load()
    pool = [{"header": "收八", "canonical": "收入"}, {"header": "Balance", "canonical": "余额"},
            {"header": "攤銷", "canonical": "Accumulated Amortization"}]
    a = m.memory_text("fewshot", [], ["收八"], pool)
    b = m.memory_text("fewshot", [], ["收八"], pool)
    assert a == b and a.startswith("- "), "确定性 + 非空"
    mem = [f"事实{i}" for i in range(20)]
    assert m.memory_text("mem0", mem, ["收八"], []).count("\n") <= 7, "mem0 top-8 上限"
    assert m.memory_text("awm", mem, [], []).count("\n") == 14, "awm ≤15 条"
    assert m.memory_text("none", mem, ["x"], pool) == ""


def test_memory_write_llm_parse(monkeypatch):
    m = _load()
    class FakeResp:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            return json.dumps({"choices": [{"message": {"content": '["规则一", "规则二"]'}}]}).encode()
    monkeypatch.setattr(m.urllib.request, "urlopen", lambda req, timeout=None: FakeResp())
    out = m.memory_write_llm("awm", [("收八", "收入")])
    assert out == ["规则一", "规则二"]
    assert len(m.memory_write_llm("mem0", [("a", "b")] * 20)) <= 8


def test_llm_suggest_mem_text_injection(monkeypatch):
    m = _load()
    cap = {}
    class FakeResp:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def read(self):
            return json.dumps({"choices": [{"message": {"content": "[]"}}]}).encode()
    def fake_urlopen(req, timeout=None):
        cap["body"] = json.loads(req.data.decode())
        return FakeResp()
    monkeypatch.setattr(m.urllib.request, "urlopen", fake_urlopen)
    rec = {"uid": "t", "rows": [["h"], ["1"]], "inj_header": ["h"],
           "canonicals": ["F"], "entries": []}
    m.llm_suggest(rec, [0], {})
    assert "已有经验" not in cap["body"]["messages"][0]["content"], "无记忆时不注入"
    m.llm_suggest(rec, [0], {}, mem_text="- 示例经验")
    assert "已有经验（可参考）" in cap["body"]["messages"][0]["content"]
