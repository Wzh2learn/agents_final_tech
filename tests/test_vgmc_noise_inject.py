"""vgmc_exp1 噪声层单测（L1 temp / L2 prompt / L3 force; 台账 #12）。"""
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


REC = {"uid": "t1", "canonicals": ["收入", "支出", "余额"],
       "entries": [{"col": 0, "original": "收入", "injected": "收八"}],
       "inj_header": ["收八", "支出", "余额"],
       "rows": [["收八", "支出", "余额"], [1, 2, 3], [4, 5, 6]]}


def test_force_inject_deterministic_wrong_target():
    m = _load()
    a = m.force_inject([], REC, [0], 1.0, 7)
    b = m.force_inject([], REC, [0], 1.0, 7)
    assert a == b, "注入必须种子派生确定"
    assert len(a) == 1
    s = a[0]
    assert s["synthetic"] is True and s["confidence"] == "low"
    assert s["action"] == "map_to" and s["column"] == 1
    assert s["target"] in ("支出", "余额"), "目标必须是随机其他 canonical"


def test_force_inject_rate_zero_noop_and_rate_one_total():
    m = _load()
    base = [{"column": 1, "action": "skip"}]
    assert m.force_inject(base, REC, [0], 0.0, 7) == base
    out = m.force_inject(base, REC, [0, 1], 1.0, 7)
    assert len(out) == 3, "rate=1.0 每列必注一条 (1 原始 + 2 注入)"


def test_force_last_wins_override_semantics():
    m = _load()
    sgs = [{"column": 1, "action": "map_to", "target": "收入"}]
    out = m.force_inject(sgs, REC, [0], 1.0, 7)
    col2sg = {}
    for s in out:  # run_arm 同构: 后写覆盖
        col2sg[int(s["column"]) - 1] = s
    assert col2sg[0].get("synthetic") is True


def test_llm_suggest_payload_branches(monkeypatch):
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
    rules = {"收入": ["营收"]}
    m.llm_suggest(REC, [0], rules)
    b = cap["body"]
    assert b["temperature"] == 0.0
    assert "营收" in b["messages"][0]["content"], "none 档保留别名提示"
    assert "1" in b["messages"][0]["content"], "none 档保留数据行"
    m.llm_suggest(REC, [0], rules, noise="temp", noise_temp=0.8)
    assert cap["body"]["temperature"] == 0.8, "L1 档温度走 payload 级"
    m.llm_suggest(REC, [0], rules, noise="prompt")
    p = cap["body"]["messages"][0]["content"]
    assert cap["body"]["temperature"] == 0.0
    assert "营收" not in p, "L2 档去别名提示"
    assert "| 1 |" not in p, "L2 档去数据行"


def test_endpoint_assertion_rejects_8006():
    m = _load()
    m.assert_endpoint_safe()
    orig = m.QA_ENDPOINT
    try:
        m.QA_ENDPOINT = "http://127.0.0.1:8006/v1/chat/completions"
        try:
            m.assert_endpoint_safe()
            raise AssertionError("必须拒绝 :8006")
        except RuntimeError:
            pass
    finally:
        m.QA_ENDPOINT = orig
