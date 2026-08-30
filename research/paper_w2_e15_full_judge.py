#!/usr/bin/env python3
"""W2 段 E1.5: Full-Judge 基线（12 叶 x 10 状态 = 120 调用, 端点仅 :8004）。

任务卡: docs/experiments/2026-08-30_w2_window_card_8004.md（TASK-20260830-04）
判据: 蓝图 Phase 1 E1.5「所有叶节点走 Judge」; C2 成功标准/降级条款见卡 §2.2。

口径:
  - 状态 = control（活工件只读）+ 9 mutants（scripts/eval_checkpoint_discrimination.py
    的确定性 mutator 作用于 /tmp 副本; 活工件与冻结件零改动）。
  - 叶分 = LLM Judge 读【去标识化证据片段】打分, 取代确定性映射:
      契约叶（9）-> 0-10 整数; judge 叶（3）-> 历史四维 rubric 同构 0-5 整数 *2。
    0-5 粒度 = skills/evaluator-calibration「1-10 量纲聚类在 7」反模式规避,
    且与 eval_checkpoint_aggregate 的 `judge 0-5 *2` 叶量纲一致。
  - 聚合 = Algorithm 1（复用 research/paper_t1_eval_baselines.aggregate, W1 G1 同构门已过）。

红线机械护栏:
  - 端点: socket 层断言只允许 127.0.0.1:8004（并禁用代理外联）; 观测端口集写入自证。
  - 预算: 文件账本累计计数（跨续跑不重置）, 每次真实 HTTP 调用前悲观 +1, >200 立即抛错。
  - 防泄漏: 证据片段不含 mutant 标识/注入字段名; 甲方标识正则清扫 + 零残留硬断言。
  - judge prompt 不见注入 ground truth; 每次调用独立上下文（无跨调用共享历史）。

用法:
  python3 research/paper_w2_e15_full_judge.py --dry-run           # 零调用: 渲染+清扫断言
  python3 research/paper_w2_e15_full_judge.py --states control    # 试点 12 调用
  python3 research/paper_w2_e15_full_judge.py                     # 全量 120 调用
  python3 research/paper_w2_e15_full_judge.py --stability 24      # 追加 temp=0 复采
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import socket
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

EVAL = REPO / "logs" / "graph" / "eval"
TREES_PATH = REPO / "config" / "eval_checkpoint_trees.json"
DISC_PATH = EVAL / "checkpoint_discrimination_report.json"
SCRATCH = Path("/tmp/w2_e15_scratch")
CACHE = EVAL / "w2_e15_judge_cache.jsonl"
LEDGER = EVAL / "w2_e15_call_ledger.json"
OUT = EVAL / "_w2_e15_section.json"

ENDPOINT = "http://127.0.0.1:8004/v1/chat/completions"
MODEL = "Qwen3.6-35B-A3B-Q4_K_M.gguf"
BUDGET_CEILING = 200          # 卡 P3 硬门
ALLOWED_PORT = 8004           # 卡红线: 端点仅 :8004
TAU = 2.0                     # 冻结判据（叶片量纲 0-10）
CONSEC_FAIL_STOP = 2          # 卡 §4: 连续 2 次格式失败 -> E1.5 BLOCKED
MAX_ATTEMPTS_PER_CELL = 2

ARTIFACTS = {
    "m1_regression": "scenario1_regression_report.json",
    "m2_deterministic": "m2_deterministic_report.json",
    "m2_judge": "m2_judge_report.json",
    "m2_number_faithfulness": "number_faithfulness_report.json",
}

# ---------------------------------------------------------------- 端点护栏
PORTS_TOUCHED: set = set()
ENDPOINT_VIOLATIONS: list = []


def install_endpoint_guard() -> None:
    """只允许连 127.0.0.1:8004; 其余（含 :8006/:8008/:5050 与任何外网）立即抛错。"""
    real_socket = socket.socket

    class GuardedSocket(real_socket):
        def connect(self, address, *a, **k):
            host = address[0] if isinstance(address, tuple) else str(address)
            port = address[1] if isinstance(address, tuple) and len(address) >= 2 else -1
            PORTS_TOUCHED.add(int(port))
            if int(port) != ALLOWED_PORT or str(host) != "127.0.0.1":
                ENDPOINT_VIOLATIONS.append("%s:%s" % (host, port))
                raise RuntimeError("ENDPOINT_GUARD: blocked outbound to %s:%s" % (host, port))
            return real_socket.connect(self, address, *a, **k)

    socket.socket = GuardedSocket


# ---------------------------------------------------------------- 预算账本
class BudgetExceeded(RuntimeError):
    pass


def ledger_load() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text(encoding="utf-8"))
    return {"call_counter": 0, "ceiling": BUDGET_CEILING, "notes": []}


def ledger_take(note: str) -> int:
    """真实调用前悲观占用; 超限即抛（不静默超支）。"""
    led = ledger_load()
    if led["call_counter"] + 1 > BUDGET_CEILING:
        raise BudgetExceeded("call_counter=%d ceiling=%d" % (led["call_counter"], BUDGET_CEILING))
    led["call_counter"] += 1
    led["notes"].append({"ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                         "n": led["call_counter"], "note": note})
    LEDGER.write_text(json.dumps(led, ensure_ascii=False), encoding="utf-8")
    return led["call_counter"]


def ledger_record_ports(ports: set) -> list:
    """把本次运行实际观测到的端口并入账本（跨运行累积, 只增不减）。

    动机: PORTS_TOUCHED 是进程内集合, 缓存命中的复算跑不会建立任何连接,
    于是"复算后重写工件"会把原始实跑观测到的 [8004] 覆盖成 []。账本是
    跨运行载体, 端口观测必须落账才谈得上"可复核的红线自证"。
    """
    led = ledger_load()
    seen = set(int(x) for x in led.get("ports_observed", []))
    seen |= {int(x) for x in ports}
    led["ports_observed"] = sorted(seen)
    led["ports_observed_updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    LEDGER.write_text(json.dumps(led, ensure_ascii=False), encoding="utf-8")
    return led["ports_observed"]


# ---------------------------------------------------------------- 去标识化
# 甲方标识零进入: 证据片段一律用位置别名 (row_NN/item_NN) 构造, 名称字段永不读取;
# redact() + redact_assert() 是第二道机械护栏（防未来改动把名称带进来）。
CLIENT_TOKENS = ["华泰紫金", "嘉合", "复熙", "博时", "博时基金", "华泰",
                 "minan", "jiaxing", "boshi", "fuxi", "caitong", "guojin",
                 "nanhua", "TraFax", "WaveFax", "NCAMC", "sample_",
                 "q01_", "q02_", "q03_", "q04_", "q05_", "q06_", "q07_",
                 "q08_", "q09_", "q10_", "q11_", "q12_", "adv_"]
# 注入 ground truth 泄漏源: mutator 写入的字面量（告诉裁判"这里被改过"）
LEAK_TOKENS = ["mutated_field", "mutant", "injection", "M1_m1_", "M2_exact_",
               "M3_source_", "M4_refusal_", "M5_judge_", "M6_judge_",
               "M7_nf_", "M8_judge_", "M9_m1_", "control"]
_ALIAS: dict = {}


def alias_for(token: str, prefix: str) -> str:
    if token not in _ALIAS:
        _ALIAS[token] = "%s_%02d" % (prefix, len(_ALIAS) + 1)
    return _ALIAS[token]


def redact(text: str) -> str:
    out = re.sub(r"sample_[A-Za-z0-9_.\-]+", lambda m: alias_for(m.group(0), "file"), text)
    out = re.sub(r"q\d{2}_[A-Za-z0-9_]+", lambda m: alias_for(m.group(0), "item"), out)
    out = re.sub(r"adv_[A-Za-z0-9_]+", lambda m: alias_for(m.group(0), "item"), out)
    for tok in ("华泰紫金", "嘉合", "复熙", "博时", "华泰"):
        out = out.replace(tok, alias_for(tok, "org"))
    for tok in ("minan", "jiaxing", "boshi", "fuxi", "caitong", "guojin",
                "nanhua", "TraFax", "WaveFax", "NCAMC"):
        out = re.sub("(?i)" + re.escape(tok), alias_for(tok, "org"), out)
    for tok in ("mutated_field",):
        out = out.replace(tok, "field_nn")
    return out


def redact_findings(text: str) -> list:
    """返回片段里残留的禁用词（空列表 = 零残留）。"""
    hits = []
    low = text.lower()
    for tok in CLIENT_TOKENS:
        if tok.lower() in low:
            hits.append(tok)
    for tok in LEAK_TOKENS:
        if tok.lower() in low:
            hits.append(tok)
    return sorted(set(hits))


# ---------------------------------------------------------------- 状态与证据
MUTANTS: list = []
MUT_BY_ID: dict = {}
TREE_LEAVES: dict = {}          # leaf_id -> leaf node dict
TREES: list = []


def load_trees() -> None:
    global TREES, TREE_LEAVES
    TREES = json.loads(TREES_PATH.read_text(encoding="utf-8"))["trees"]

    def walk(n):
        if not n.get("children"):
            TREE_LEAVES[n["id"]] = n
        for c in n.get("children", []):
            walk(c)
    for t in TREES:
        walk(t)


def load_mutants() -> None:
    global MUTANTS, MUT_BY_ID
    sys.path.insert(0, str(REPO / "scripts"))
    import eval_checkpoint_discrimination as ecd  # noqa: F401  纯确定性导入
    MUTANTS = ecd.build_mutants()
    MUT_BY_ID = {m["id"]: m for m in MUTANTS}


def materialize(states: list) -> dict:
    """control + 9 mutants 的工件副本落在 /tmp（活工件与冻结件零改动）。"""
    SCRATCH.mkdir(parents=True, exist_ok=True)
    dirs = {}
    for state in states:
        d = SCRATCH / state
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
        for fname in ARTIFACTS.values():
            src = EVAL / fname
            if src.exists():
                shutil.copyfile(src, d / fname)
        if state != "control":
            MUT_BY_ID[state]["mutate"](str(d))
        dirs[state] = d
    return dirs


def _rows(d: Path) -> list:
    rep = json.loads((d / ARTIFACTS["m1_regression"]).read_text(encoding="utf-8"))
    return rep.get("rows", []), rep


def _base_rows(rows: list) -> list:
    return [r for r in rows if not str(r.get("status", "")).startswith("SKIP")]


def _checks(d: Path, contract: str) -> list:
    rep = json.loads((d / ARTIFACTS["m2_deterministic"]).read_text(encoding="utf-8"))
    out = []
    for i, r in enumerate(rep.get("results", []), 1):
        for ch in r.get("checks", []):
            if ch.get("type") == contract:
                out.append((i, bool(ch.get("pass"))))
    return out


def _judge_items(d: Path, dim: str) -> list:
    p = d / ARTIFACTS["m2_judge"]
    if not p.exists():
        return []
    rep = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for i, r in enumerate(rep.get("results", []), 1):
        cell = (r.get("scores") or {}).get(dim)
        if isinstance(cell, dict) and cell.get("score") is not None:
            out.append((i, int(cell["score"])))
    return out


JUDGE_DIM_OF_LEAF = {"qa.faithfulness.judge": "faithfulness",
                     "qa.citation.judge": "citation_quality",
                     "qa.refusal.judge": "refusal_appropriateness"}
CONTRACT_OF_LEAF = {"qa.retrieval.source_required": "source_required",
                    "qa.numeric.exact": "exact_numeric",
                    "qa.refusal.deterministic": "refusal_expected"}


def evidence_for(d: Path, leaf_id: str) -> tuple:
    """叶级证据片段: 只给 item 级观测, 不给任何预聚合量（overall/avg/rate 一律屏蔽）。

    返回 (kind, snippet, n_items); kind in {contract, judge_dim}。
    """
    if leaf_id == "parse.doc.ok":
        rows, rep = _rows(d)
        lines = ["row_%02d status=%s" % (i, r.get("status")) for i, r in enumerate(rows, 1)]
        return "contract", "\n".join(lines), len(lines)
    if leaf_id == "parse.doc.throughput":
        rows, rep = _rows(d)
        # 只给工件真实记录的 run 级观测; overall 聚合量屏蔽。
        # 注意: 工件不含任何耗时/超时字段（"按时完成"这一需求在证据层不可验证,
        # 该事实本身作为 judged-vs-mapped 差异的成因写入工件）。
        lines = ["run_rows_count=%d" % len(rows),
                 "run_timestamp_recorded=%s" % ("yes" if rep.get("timestamp") else "no"),
                 "run_mode_quick=%s" % ("yes" if rep.get("quick") else "no"),
                 "run_error_or_timeout_field_recorded=no",
                 "run_rows_all_have_status=%s" % ("yes" if rows and all(
                     r.get("status") for r in rows) else "no")]
        return "contract", "\n".join(lines), len(lines)
    if leaf_id == "parse.table.regression":
        rows = _base_rows(_rows(d)[0])
        lines = ["row_%02d table_structure_check=%s"
                 % (i, r.get("status")) for i, r in enumerate(rows, 1)]
        return "contract", "\n".join(lines), len(lines)
    if leaf_id == "parse.field.hit_rate":
        rows = _base_rows(_rows(d)[0])
        lines = ["row_%02d values_checked=%d values_mismatched=%d"
                 % (i, len(r.get("expected") or []), len(r.get("diffs") or []))
                 for i, r in enumerate(rows, 1)]
        return "contract", "\n".join(lines), len(lines)
    if leaf_id == "parse.reconcile.equations":
        rows = _base_rows(_rows(d)[0])
        lines = ["row_%02d identity_check=%s" % (i, r.get("status"))
                 for i, r in enumerate(rows, 1)]
        return "contract", "\n".join(lines), len(lines)
    if leaf_id in CONTRACT_OF_LEAF:
        items = _checks(d, CONTRACT_OF_LEAF[leaf_id])
        lines = ["item_%02d contract_verdict=%s" % (i, "PASS" if p else "FAIL")
                 for i, p in items]
        return "contract", "\n".join(lines), len(lines)
    if leaf_id == "qa.numeric.number_grounding":
        p = d / ARTIFACTS["m2_number_faithfulness"]
        rep = json.loads(p.read_text(encoding="utf-8"))
        lines = []
        for i, r in enumerate(rep.get("results", []), 1):
            lines.append("item_%02d number_claims=%d ungrounded=%d grounding_verdict=%s"
                         % (i, len(r.get("numbers") or []), len(r.get("ungrounded") or []),
                            "PASS" if r.get("pass") else "FAIL"))
        return "contract", "\n".join(lines), len(lines)
    if leaf_id in JUDGE_DIM_OF_LEAF:
        items = _judge_items(d, JUDGE_DIM_OF_LEAF[leaf_id])
        if not items:
            return "judge_dim", "", 0
        lines = ["item_%02d verdict_on_0_5=%d" % (i, v) for i, v in items]
        return "judge_dim", "\n".join(lines), len(lines)
    raise KeyError("unknown leaf " + leaf_id)


# ---------------------------------------------------------------- 判分契约
# 0-5 粒度（evaluator-calibration 反模式规避）: 契约叶 = 失败占比锚点;
# judge 叶 = 历史四维 rubric verbatim 维度定义（scripts/m2_eval_judge.py JUDGE_PROMPT）
# + 显式映射锚点。裁判自行完成"证据 -> 分数"的映射, 这正是与确定性映射对照的对象。
RUBRIC_CONTRACT = """你是严格的评测契约审计员。依据下面的【检查点需求】与【逐条证据】为该检查点打分。

证据是 item 级观测（逐条契约判定 / 逐条数值计数）, 不含任何汇总数字。
你必须自己完成"观测 -> 是否满足需求"的判定与聚合。

打分量纲: 0-10 整数。锚点:
  10 = 需求完全满足, 无任何违反条目
  7  = 绝大多数条目满足, 少数违反
  5  = 约一半条目违反
  3  = 多数条目违反
  0  = 需求基本未满足 / 几乎全部条目违反
计数规则: 标记 SKIP 的条目本次未评估, 既不计入违反也不计入通过（但覆盖变窄需在理由中注明）。
只依据证据, 不得臆测证据之外的信息, 不得因为"问题看起来不大"而抬高分数。"""

RUBRIC_JUDGE_DIM = """你是严格的 RAG 问答质量评审。下面是历史评审对【单个质量维度】逐条给出的 0-5 判定分数。
该维度的历史定义（逐字沿用, 未改写）:
<<DIM_DEF>>

你要把这些 0-5 逐条判定聚合成一个 0-10 分数。映射锚点（必须落在锚点附近）:
  全部 5 -> 10;  全部 4 -> 8;  全部 3 -> 6;  全部 2 -> 4;  全部 1 -> 2;  全部 0 -> 0
混合情形: 先求 0-5 均值 m, 分数 = round(m * 2)。分数越高 = 该维度质量越好。
不得臆测证据之外的信息; 不得因为个别条目而忽略整体占比。"""

# 历史四维 rubric 中各维定义（逐字取自 scripts/m2_eval_judge.py JUDGE_PROMPT 的编号条目）
DIM_DEFS = {
    "faithfulness": ("1. faithfulness 忠实度：答案是否只使用【检索上下文】中的信息。出现上下文中没有的事实/"
                     "数值/名称（包括对脱敏掩码 * 的补全猜测）按程度扣分；完全忠实=5。"),
    "citation_quality": ("3. citation_quality 引用质量：答案是否明确指出出处（样本/表/字段），且与【来源列表】一致。"
                         "具体且一致=5；无出处或与来源矛盾=0-2。豁免：若该题【预期不可回答】且答案明确拒答，"
                         "则按拒答说明的清晰度评分（来源为空不扣分）。"),
    "refusal_appropriateness": ("4. refusal_appropriateness 拒绝恰当性：若该题【预期不可回答】，明确说明未找到/无法"
                                "回答=5，编造答案=0；若该题可回答，正常作答=5，错误拒答=0。"),
}

OUTPUT_CONTRACT = """只输出一个 JSON 对象（不要 markdown 围栏、不要多余文字）:
{"score": <0-10 整数>, "evidence_quote": "<逐字摘录的证据行, 至少 8 字符>", "reason": "<一句话理由>"}"""


def _render(kind_head: str, snippet: str) -> str:
    return "%s\n\n[证据片段]\n%s\n\n%s\n" % (kind_head, snippet, OUTPUT_CONTRACT)


def build_prompt(leaf_id: str, kind: str, snippet: str) -> str:
    """渲染裁判 prompt（零调用，可审计）。

    口径说明（写入工件）: 给裁判的是【检查点需求】（与确定性映射同源的 config 规格）
    + item 级证据, 但**不给**确定性映射公式（硬闸门/兄弟归一化/百分比公式）。
    否则测的是"照抄公式能否复现"而非"Full-Judge 能否替代确定性映射"。
    judged-vs-mapped 差异因此含端点差异 + 量纲口径差异, 两者在工件中分开标注。
    """
    leaf = TREE_LEAVES[leaf_id]
    head = (RUBRIC_CONTRACT if kind == "contract"
            else RUBRIC_JUDGE_DIM.replace("<<DIM_DEF>>", DIM_DEFS[JUDGE_DIM_OF_LEAF[leaf_id]]))
    spec = "[检查点] %s\n[需求] %s" % (redact(str(leaf.get("label", leaf_id))),
                                           redact(str(leaf.get("requirement", ""))))
    n = len([x for x in snippet.splitlines() if x.strip()])
    return "%s\n\n%s\n[证据条目数] %d\n\n[证据片段]\n%s\n\n%s\n" % (
        head, spec, n, snippet if snippet.strip() else "<无证据条目>", OUTPUT_CONTRACT)


def prompt_guard(leaf_id: str, state: str, prompt: str, snippet: str) -> list:
    """机械防泄漏（全清单, 无豁免）:
    1. 证据片段不得残留甲方标识 / 注入 ground truth 字面量;
    2. 完整 prompt 同样不得残留（rubric 与 config 规格文本一并扫）;
    3. prompt 不得含状态标识本身（否则裁判可从 id 反推缺陷）。
    """
    v = ["snippet residue: %s (%s)" % (t, leaf_id) for t in redact_findings(snippet)]
    v += ["prompt residue: %s (%s)" % (t, leaf_id) for t in redact_findings(prompt)]
    if state and state in prompt:
        v.append("LEAK: prompt contains state id '%s'" % state)
    return v


# ---------------------------------------------------------------- 调用与缓存
def _extract_json(content: str) -> dict | None:
    if not content:
        return None
    txt = content.strip()
    txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt, flags=re.M).strip()
    start = txt.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(txt)):
        if txt[i] == "{":
            depth += 1
        elif txt[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    obj = json.loads(txt[start:i + 1])
                except Exception:
                    return None
                return obj if isinstance(obj, dict) else None
    return None


def cache_load() -> dict:
    out = {}
    if CACHE.exists():
        for line in CACHE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            out[rec["key"]] = rec
    return out


def cache_append(rec: dict) -> None:
    with CACHE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _call_8004(prompt: str) -> tuple:
    """一次真实 :8004 调用; 预算在发出前悲观占用。"""
    n = ledger_take("e15 judge call")
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 1024,
        # thinking 显式关闭（与 k2 小臂 / m2_eval_judge 同约定, 卡 P2）
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    content = body["choices"][0]["message"]["content"]
    usage = body.get("usage") or {}
    return content, n, usage


def judge_cell(state: str, leaf_id: str, dirs: dict, cache: dict,
               sample: int | None = None) -> dict:
    kind, raw, n_items = evidence_for(dirs[state], leaf_id)
    snippet = redact(raw)
    prompt = build_prompt(leaf_id, kind, snippet)
    viol = prompt_guard(leaf_id, state, prompt, snippet)
    key = "%s|%s%s" % (state, leaf_id, "" if sample is None else "|s%d" % sample)
    base = {"key": key, "state": state, "leaf": leaf_id, "kind": kind,
            "n_items": n_items, "snippet_sha256": hashlib.sha256(
                snippet.encode("utf-8")).hexdigest()[:16]}
    if viol:
        return dict(base, status = "GUARD_BLOCKED", violations=viol)
    hit = cache.get(key)
    if hit and hit.get("status") == "OK":
        if hit.get("snippet_sha256") == base["snippet_sha256"]:
            return dict(hit, cache_hit=True)
        # 证据构造变了 -> 旧判定作废, 重新调用（防陈旧结果污染复算）
        print("CACHE_STALE (snippet changed): %s" % key, flush=True)
    last_err, content = None, ""
    for attempt in range(1, MAX_ATTEMPTS_PER_CELL + 1):
        try:
            content, n, usage = _call_8004(prompt)
            obj = _extract_json(content)
            if not obj or not isinstance(obj.get("score"), (int, float)):
                last_err = "unparsable/missing score"
                continue
            score = int(round(float(obj["score"])))
            if not 0 <= score <= 10:
                last_err = "score out of range: %s" % obj["score"]
                continue
            quote = str(obj.get("evidence_quote", ""))
            rec = dict(base, status="OK", score=score, attempt=attempt,
                       evidence_quote=quote, reason=str(obj.get("reason", ""))[:300],
                       raw_len=len(content), call_n=n,
                       prompt_chars=len(prompt), completion_tokens=usage.get("completion_tokens"))
            cache_append(rec)
            return rec
        except BudgetExceeded:
            raise
        except Exception as exc:                                   # noqa: BLE001
            last_err = "%s: %s" % (type(exc).__name__, str(exc)[:160])
    return dict(base, status="FORMAT_FAIL", error=last_err,
                raw_head=redact(content)[:300])


# ---------------------------------------------------------------- 分节产出
DISC_V2 = EVAL / "checkpoint_discrimination_report.json"
DISC_PSO_ERA = EVAL / "checkpoint_discrimination_report_20260819.json"
JUDGE_FROZEN_8006 = EVAL / "m2_judge_report_k1.json"
JUDGE_FROZEN_8006_K3 = EVAL / "m2_judge_report_k3.json"
JUDGE_LIVE_8004 = EVAL / "m2_judge_report.json"
PRED_DELTA_DIM = 0.5            # 卡 §2.2 校准预期（非判据）


def _load_t1():
    sys.path.insert(0, str(REPO / "research"))
    import paper_t1_eval_baselines as t1
    return t1


def deterministic_matrix() -> dict:
    """确定性映射口径的 12 叶 x 10 状态矩阵（判分对照基线）。"""
    t1 = _load_t1()
    disc = json.loads(DISC_V2.read_text(encoding="utf-8"))
    base = dict(disc["control"]["live_leaves"])
    out = {"control": base}
    for m in disc["mutants"]:
        out[m["id"]] = t1.mutant_leaf_scores(base, m)
    return out


def judged_matrix(rows: list) -> dict:
    mat = {}
    for r in rows:
        mat.setdefault(r["state"], {})[r["leaf"]] = r.get("score")
    return mat


def separation_view(t1, trees: list, mat: dict, pso_w: dict | None) -> dict:
    """判分/映射两口径共用的分离度算法（control vs 9 mutants, blended + tree root）。"""
    leaves = sorted(mat["control"])
    ok = all(all(mat[s].get(l) is not None for l in leaves) for s in mat)
    disc_pre = json.loads(DISC_V2.read_text(encoding="utf-8"))
    need = ["control"] + [m["id"] for m in disc_pre["mutants"]]
    if not ok or any(st not in mat for st in need):
        return {"complete": False, "reason": "partial state set (%d/%d states present)"
                % (len([st for st in need if st in mat]), len(need))}
    z_roots, z_overall = t1.aggregate(trees, mat["control"], pso_w)
    disc = disc_pre
    rows = []
    for m in disc["mutants"]:
        roots, overall = t1.aggregate(trees, mat[m["id"]], pso_w)
        rows.append({
            "id": m["id"], "tree": m["tree"],
            "sep_blended": round(z_overall - overall, 4),
            "sep_tree_root": round(z_roots[m["tree"]] - roots[m["tree"]], 4),
            "detect_blended": round(z_overall - overall, 4) >= TAU,
            "detect_tree_root": round(z_roots[m["tree"]] - roots[m["tree"]], 4) >= TAU,
            "primary_detect": round(z_roots[m["tree"]] - roots[m["tree"]], 4) >= TAU,
            "target_leaves": sorted({h["leaf"] for h in list(m.get("target_hits", []))
                                     + list(m.get("graded_hits", []))}),
        })
    n = len(rows)
    return {"complete": True, "control_blended": round(z_overall, 4),
            "control_tree_roots": {k: round(v, 4) for k, v in z_roots.items()},
            "per_mutant": rows,
            "mean_sep_blended": round(sum(r["sep_blended"] for r in rows) / n, 6),
            "mean_sep_tree_root": round(sum(r["sep_tree_root"] for r in rows) / n, 6),
            "worst_sep_blended": min(r["sep_blended"] for r in rows),
            "worst_mutant_blended": min(rows, key=lambda r: r["sep_blended"])["id"],
            "worst_sep_tree_root": min(r["sep_tree_root"] for r in rows),
            "worst_mutant_tree_root": min(rows, key=lambda r: r["sep_tree_root"])["id"],
            "detected_blended": sum(1 for r in rows if r["detect_blended"]),
            "detected_tree_root": sum(1 for r in rows if r["detect_tree_root"]),
            "n_mutants": n}


def endpoint_consistency_note(rows: list) -> dict:
    """:8004 判分 vs 冻结 :8006 四维口径 的逐维均值差（卡 §2.2 用户指定必含）。"""
    def avg(p: Path) -> dict:
        rep = json.loads(p.read_text(encoding="utf-8"))
        return {"endpoint": rep.get("judge_endpoint"), "model": rep.get("judge_model"),
                "rubric_version": rep.get("rubric_version"), "judge_runs": rep.get("judge_runs"),
                "dims": {k: v.get("avg") for k, v in (rep.get("summary") or {}).items()}}

    frozen = avg(JUDGE_FROZEN_8006)
    frozen3 = avg(JUDGE_FROZEN_8006_K3)
    live = avg(JUDGE_LIVE_8004)
    # E1.5 重判口径: judge 叶得分 / 2 -> 回到 0-5 维均分（control 状态）
    rej = {}
    for r in rows:
        if r["state"] != "control" or r.get("score") is None:
            continue
        if r["leaf"] in JUDGE_DIM_OF_LEAF:
            rej[JUDGE_DIM_OF_LEAF[r["leaf"]]] = round(r["score"] / 2.0, 3)
    deltas = {}
    for dim, val in sorted(rej.items()):
        f8006 = (frozen["dims"].get(dim))
        f8004 = (live["dims"].get(dim))
        deltas[dim] = {"e15_8004_rejudged_on_0_5": val,
                       "frozen_8006_k1": f8006, "frozen_8006_k3_runs3": f8006 and frozen3["dims"].get(dim),
                       "live_8004": f8004,
                       "abs_delta_vs_frozen_8006": round(abs(val - f8006), 3) if f8006 is not None else None,
                       "abs_delta_vs_live_8004": round(abs(val - f8004), 3) if f8004 is not None else None}
    within = [d["abs_delta_vs_frozen_8006"] for d in deltas.values()
              if d["abs_delta_vs_frozen_8006"] is not None]
    return {"prediction_abs_delta_per_dim_le": PRED_DELTA_DIM,
            "max_observed_abs_delta": max(within) if within else None,
            "prediction_holds": bool(within) and max(within) <= PRED_DELTA_DIM,
            "frozen_8006_k1": frozen, "frozen_8006_k3": frozen3, "live_8004": live,
            "per_dim": deltas,
            "numeric_correctness_note": (
                "四维中的 numeric_correctness 在契约树上无对应 judge 叶"
                "（F-M4 已知缺口）, 故其一致性差异无法由 E1.5 重判口径给出, 如实缺项。"),
            "caveat": ("E1.5 judge 叶读的是历史逐条 0-5 判定再聚合, 非重新评原始答案; "
                       "因此本注记度量的是【:8004 聚合器能否复现历史四维均分】, "
                       "不等于 :8004 与 :8006 对同一原始答案的逐条判定一致率。")}


def ceiling_flags(rows: list) -> dict:
    out = {}
    by = {}
    for r in rows:
        if r.get("score") is None:
            continue
        by.setdefault(r["leaf"], []).append(r["score"])
    for leaf, scores in sorted(by.items()):
        out[leaf] = {"n": len(scores), "mean": round(sum(scores) / len(scores), 3),
                     "distinct": sorted(set(scores)),
                     "saturated_at_10": all(s == 10 for s in scores),
                     "saturated_at_0": all(s == 0 for s in scores)}
    return out


def build_section(rows: list, states: list, extra: dict) -> dict:
    t1 = _load_t1()
    trees = json.loads(TREES_PATH.read_text(encoding="utf-8"))["trees"]
    pso = json.loads((EVAL / "pso_weight_search_v0.json").read_text(encoding="utf-8"))
    jmat = judged_matrix(rows)
    dmat = deterministic_matrix()
    judged_sep = separation_view(t1, trees, jmat, None) if len(jmat) == len(states) else {"complete": False}
    mapped_sep = separation_view(t1, trees, dmat, None)
    per_leaf_delta = {}
    if judged_sep.get("complete"):
        for st in states:
            for lf in sorted(dmat[st]):
                if jmat[st].get(lf) is None:
                    continue
                per_leaf_delta.setdefault(lf, {})[st] = {
                    "judged": jmat[st][lf], "mapped": round(float(dmat[st][lf]), 4),
                    "abs_delta": round(abs(jmat[st][lf] - float(dmat[st][lf])), 4)}
    max_delta = max((v["abs_delta"] for d in per_leaf_delta.values() for v in d.values()),
                    default=None)
    led = ledger_load()
    return {
        "design_note": ("判分证据等价替换: 裁判只见 item 级观测, 不见任何预聚合量"
                        "（overall/avg/pass rate 全屏蔽）, 由裁判自行完成映射与聚合。"
                        "局限: mutation 作用于工件/判定层, 逐条判定本身即被观测证据,"
                        "故 3 个 judge 叶为『裁判评判定』而非『裁判评原始答案』。"),
        "states": states, "leaves": sorted(TREE_LEAVES),
        "call_convention": {"endpoint": ENDPOINT, "model": MODEL, "temperature": 0,
                            "enable_thinking": False},
        "leaf_score_matrix_judged": jmat,
        "leaf_score_matrix_mapped_deterministic": {
            s: {l: round(float(v), 4) for l, v in dmat[s].items()} for s in dmat},
        "separation_judged": judged_sep,
        "separation_mapped_control_only_caliber": mapped_sep,
        "pso_weight_caliber_reference": {"mean_sep": pso["optimized_separation_overall"],
                                         "expert_mean_sep": pso["baseline_separation_overall"]},
        "judged_vs_mapped_per_leaf": per_leaf_delta,
        "judged_vs_mapped_max_abs_delta": max_delta,
        "verdict_distributions_and_ceiling": ceiling_flags(rows),
        "endpoint_consistency_note": endpoint_consistency_note(rows),
        "no_evidence_behavior": extra.get("no_evidence_behavior", {}),
        "failures": [r for r in rows if r.get("status") != "OK"],
        "cells_total": len(states) * len(TREE_LEAVES),
        "cells_ok": sum(1 for r in rows if r.get("status") == "OK"),
        "budget_self_proof": {"call_counter": led["call_counter"], "ceiling": BUDGET_CEILING,
                              "within_ceiling": led["call_counter"] <= BUDGET_CEILING},
        # 作用域显式化: "this_run" = 本进程连接观测（缓存复算跑必然为空）,
        # "window" = 跨运行账本累积。旧字段名 ports_touched 语义含糊, 曾被
        # 汇报当成"实跑观测 [8004]"引用而实际存的是 [] -> 声明与存储不符。
        "endpoint_assert": {
            "allowed": "127.0.0.1:8004",
            "ports_touched_this_run": sorted(PORTS_TOUCHED),
            "live_calls_this_run": sum(1 for r in rows if not r.get("cache_hit")),
            "cache_hit_cells_this_run": sum(1 for r in rows if r.get("cache_hit")),
            "violations_this_run": ENDPOINT_VIOLATIONS,
            "only_allowed_endpoint": set(PORTS_TOUCHED) <= {ALLOWED_PORT},
            "window_ports_observed": ledger_load().get("ports_observed", []),
            "window_live_calls_ledger_notes": len(ledger_load().get("notes", [])),
            "scope_note": ("ports_touched_this_run 只反映本进程; 缓存命中的复算不建连接故为空。"
                           "实跑端点证据 = window_* 字段 + 账本时间戳; "
                           "护栏自身是否真能记录/拦截由 w2_endpoint_guard_probe.json 独立自证。"),
        },
    }


# ---------------------------------------------------------------- 入口


def run_batch(states: list, leaves: list, dirs: dict, cache: dict,
              limit: int | None = None) -> tuple:
    rows, consec_fail, blocked = [], 0, False
    cells = [(st, lf) for st in states for lf in leaves]
    if limit:
        cells = cells[:limit]
    for idx, (st, lf) in enumerate(cells, 1):
        rec = judge_cell(st, lf, dirs, cache)
        if rec.get("status") == "GUARD_BLOCKED":
            print("GUARD_BLOCKED %s/%s -> %s" % (st, lf, rec["violations"]), flush=True)
            blocked = True
        elif rec.get("status") != "OK":
            consec_fail += 1
            print("[%d/%d] FAIL %s/%s: %s" % (idx, len(cells), st, lf,
                                             str(rec.get("error"))[:120]), flush=True)
            if consec_fail >= CONSEC_FAIL_STOP:
                blocked = True
                print("E1.5 BLOCKED: %d consecutive format failures" % consec_fail, flush=True)
                rows.append(rec)
                break
        else:
            consec_fail = 0
            print("[%d/%d] ok %s/%s -> %d (cache=%s n=%s)"
                  % (idx, len(cells), st, lf, rec["score"], rec.get("cache_hit", False),
                     rec.get("call_n")), flush=True)
        rows.append(rec)
    return rows, blocked


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="零调用: 只渲染 + 防泄漏断言")
    ap.add_argument("--states", default="", help="逗号分隔状态子集（默认全部 10 状态）")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--stability", type=int, default=0,
                    help="对前 N 个 control 单元追加第二样本（复采, 计入预算）")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    install_endpoint_guard()
    load_trees()
    load_mutants()
    leaves = sorted(TREE_LEAVES)
    states = [s.strip() for s in args.states.split(",") if s.strip()] or \
             ["control"] + [m["id"] for m in MUTANTS]
    unknown = [s for s in states if s != "control" and s not in MUT_BY_ID]
    if unknown:
        print("unknown states: %s" % unknown, file=sys.stderr)
        return 2
    print("leaves=%d states=%d cells=%d" % (len(leaves), len(states), len(leaves) * len(states)))

    if args.dry_run:
        dirs = materialize(states)
        problems, sizes = [], {}
        max_prompt = max_snip = 0
        for st in states:
            for lf in leaves:
                kind, raw, n_items = evidence_for(dirs[st], lf)
                snip = redact(raw)
                prompt = build_prompt(lf, kind, snip)
                viol = prompt_guard(lf, st, prompt, snip)
                sizes["%s|%s" % (st, lf)] = [kind, n_items, len(snip)]
                max_prompt = max(max_prompt, len(prompt))
                max_snip = max(max_snip, len(snip))
                if viol:
                    problems.append({"state": st, "leaf": lf, "violations": viol})
        kinds = {}
        for v in sizes.values():
            kinds[v[0]] = kinds.get(v[0], 0) + 1
        print("dry-run cells=%d guard_violations=%d max_prompt_chars=%d max_snippet_chars=%d "
              "kinds=%s" % (len(sizes), len(problems), max_prompt, max_snip,
                            json.dumps(kinds, sort_keys=True)))
        if problems:
            print(json.dumps(problems, ensure_ascii=False, indent=1)[:3000])
        print("RESIDUE_GATE: %s" % ("PASS (零残留)" if not problems else "FAIL"))
        print("ports_touched=%s (dry-run 必须为空)" % sorted(PORTS_TOUCHED))
        return 0 if not problems and not PORTS_TOUCHED else 1

    dirs = materialize(states)
    cache = cache_load()
    rows, blocked = run_batch(states, leaves, dirs, cache, args.limit)

    extra = {"no_evidence_behavior": {}}
    if args.stability:
        cells = [(r["state"], r["leaf"]) for r in rows if r.get("status") == "OK"][:args.stability]
        for st, lf in cells:
            rec = dict(judge_cell(st, lf, dirs, cache, sample=2))
            rec["stability_sample"] = 2
            rows.append(rec)
            extra["no_evidence_behavior"].setdefault("stability_pairs", []).append(
                {"state": st, "leaf": lf, "sample2_score": rec.get("score")})

    for st in states:                       # M8 空片段行为记录（非评分, 仅观测）
        for lf in leaves:
            kind, raw, n = evidence_for(dirs[st], lf)
            if n == 0:
                extra["no_evidence_behavior"]["%s|%s" % (st, lf)] = "empty_evidence_snippet"

    ledger_record_ports(PORTS_TOUCHED)
    sec = build_section(rows, states, extra)
    sec["blocked"] = blocked
    Path(args.out).write_text(json.dumps(sec, ensure_ascii=False, indent=1), encoding="utf-8")
    led = ledger_load()
    print("cells_ok=%d/%d call_counter=%d/%d ports=%s violations=%s -> %s"
          % (sec["cells_ok"], sec["cells_total"], led["call_counter"], BUDGET_CEILING,
             sorted(PORTS_TOUCHED), ENDPOINT_VIOLATIONS, args.out))
    return 1 if (blocked or ENDPOINT_VIOLATIONS or not sec["budget_self_proof"]["within_ceiling"]) else 0


if __name__ == "__main__":
    sys.exit(main())
