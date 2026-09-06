# -*- coding: utf-8 -*-
"""D3 阶段 B: judge 重打分窗（TASK-20260901-D3 加编 2 + 加编 3 C3-1..C3-6 测量契约）。

零现场定义: 案例清单 / prompt 模板 / 渲染规则 / 输出 schema / :8004 设置 / 计数规则
一律逐字取自任务卡 `docs/experiments/2026-09-01_d3_matched_specificity_card.md` 加编 3 节。
职责边界（C3-6）: 本窗只收集 + 确定性聚合, 结论判定归 Loop D / autopsy。

用法:
  venv/bin/python research/paper_d3_stage_b_judge.py --stage preflight   # 零端点: 断言 + 28 例 prompt 构造（无网络）
  venv/bin/python research/paper_d3_stage_b_judge.py --stage window      # 端点窗: canary + 28 调用 + 正式工件
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
CARD = REPO / "docs" / "experiments" / "2026-09-01_d3_matched_specificity_card.md"
D1_ART = EVAL / "d1_mutant_validity_audit.json"
T2_ART = EVAL / "checkpoint_discrimination_tables_v2.json"
D3A_ART = EVAL / "d3_matched_fpr_stage_a.json"
DR4_ART = EVAL / "dr4_d1_reclassification_review.json"
TABLES_FROZEN = REPO / "data" / "research" / "drift_v0" / "input" / "tatqa_tables.json"
OUT = EVAL / "d3_matched_fpr_stage_b.json"
LEDGER = EVAL / "d3_stage_b_call_ledger.jsonl"
PRECHECK_OUT = EVAL / "d3_stage_b_preflight.json"

ENDPOINT = "http://127.0.0.1:8004/v1/chat/completions"
HEALTH = "http://127.0.0.1:8004/v1/health"
MODELS = "http://127.0.0.1:8004/v1/models"
MODEL_EXPECT = "Qwen3.6-35B-A3B-Q4_K_M.gguf"
ALLOWED_HOST, ALLOWED_PORT = "127.0.0.1", 8004
BUDGET_CEILING = 200                              # C3-5 硬门
TEMPERATURE, MAX_TOKENS, TIMEOUT_S = 0, 512, 90   # C3-4 冻结参数
CANARY_MAX_TOKENS = 64
ROW_CAP = 40                                      # C3-2 渲染规则
CARD_SHA_EXPECT = "22eaa5117b8472472b24eb038e18d8af855de36c49f7dd46dd295fefe9ade411"

# ------------------------------------------------------- C3-1 案例清单（逐字冻结, 运行时零推导）
JN1_SILENT15 = ["1fe3e1d6#2", "21c316d6#2", "3c609073#1", "3c609073#3", "44c7c9ef#1",
                "567a03c7#1", "5fe2c49e#1", "5fe2c49e#2", "68b8d514#1", "6a5e5192#0",
                "6f9a0eb1#0", "c0f66238#3", "d2bba753#0", "d7d65228#3", "e11338f6#0"]
JN1_DILUTION6 = ["24ff90f9#2", "24ff90f9#4", "32cfcadb#2", "32cfcadb#4", "97176853#2", "97176853#4"]
JN1_21 = JN1_SILENT15 + JN1_DILUTION6
JN2_7 = ["50e78448-3cf5-439c-a609-ee866bd1f05a#2", "54c494f7-d731-49bf-b9cd-d494aea72e34#2",
         "5e60c056-5073-441d-8525-7f834deb5c64#0", "73a817fc-25df-494d-b0f2-79cfdab34076#1",
         "b5aae4e9-040d-4e55-a42d-39cde217978f#0", "e67f7bf2-fc15-4a7a-9856-febb066998fd#4",
         "e9730ea3-e003-4db6-a513-9c9e6f40e371#2"]
JN2_ANCHORS = {"50e78448": ("US$", "US [1]"), "54c494f7": ("Accumulated Amortization", "amort"),
               "5e60c056": ("\u00a3m", "m\u3010\u3011"), "73a817fc": ("Dividends Paid(1)", "dividend"),
               "b5aae4e9": ("\u00a3m", "m\u3010\u3011"),
               "e67f7bf2": ("Free cash flow (pre-spectrum)", "cashflow"),
               "e9730ea3": ("Accumulated Amortization", "amort")}
H2E = "3789d7da#1"
FROZEN_INPUTS = [CARD, D1_ART, T2_ART, D3A_ART, DR4_ART, TABLES_FROZEN]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def payload_of(art) -> dict:
    return art.get("payload") or art


def short_of(full_key: str) -> str:
    uid, col = full_key.split("#")
    return "%s#%s" % (uid[:8], col)


# ------------------------------------------------------- 端点护栏
PORTS_TOUCHED: set = set()
PORT_VIOLATIONS: list = []


def install_guard(allow_endpoint: bool) -> None:
    """端点窗: 只允许 127.0.0.1:8004; 预检窗: 禁止一切出站。违规即抛并记账。"""
    real = socket.socket

    class Guarded(real):
        def connect(self, address, *a, **k):
            host = address[0] if isinstance(address, tuple) else str(address)
            port = int(address[1]) if isinstance(address, tuple) and len(address) >= 2 else -1
            PORTS_TOUCHED.add(port)
            if not (allow_endpoint and host == ALLOWED_HOST and port == ALLOWED_PORT):
                PORT_VIOLATIONS.append("%s:%s" % (host, port))
                raise RuntimeError("ENDPOINT_GUARD blocked %s:%s" % (host, port))
            return real.connect(self, address, *a, **k)

    socket.socket = Guarded  # type: ignore[misc]


def http(url: str, body: bytes | None = None, timeout: int = 10) -> str:
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"},
                                 method="POST" if body is not None else "GET")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


# ------------------------------------------------------- 冻结模板（逐字取自卡加编 3）
def extract_template() -> dict:
    card = CARD.read_text(encoding="utf-8")
    sec = card.split("### C3-2", 1)[1].split("### C3-3", 1)[0]
    blocks = [b[:-1] if b.endswith("\n") else b for b in re.findall(r"```text\n(.*?)```", sec, re.S)]
    if len(blocks) != 2:
        raise RuntimeError("C3-2 text blocks != 2 (got %d)" % len(blocks))
    canary = re.search(r"冻结 prompt = user 消息 `([^`]+)`", card)
    if not canary:
        raise RuntimeError("canary prompt not found in card")
    placeholders = sorted(set(re.findall(r"\{([a-z_]+)\}", blocks[1])))
    return {"system": blocks[0], "user_template": blocks[1], "canary_prompt": canary.group(1),
            "system_sha256": sha256_bytes(blocks[0].encode("utf-8")),
            "user_template_sha256": sha256_bytes(blocks[1].encode("utf-8")),
            "canary_prompt_sha256": sha256_bytes(canary.group(1).encode("utf-8")),
            "user_template_placeholders": placeholders}


# ------------------------------------------------------- 冻结工件装载
def load_inputs() -> dict:
    d1 = payload_of(jload(D1_ART))
    t2 = payload_of(jload(T2_ART))
    d3a = payload_of(jload(D3A_ART))
    dr4 = payload_of(jload(DR4_ART))
    corpus = {t["uid"]: t["table"] for t in jload(TABLES_FROZEN)}
    uid8_to_full: dict[str, list[str]] = {}
    t2_inj: dict[str, dict] = {}
    for tab in t2["tables"]:
        uid8_to_full.setdefault(tab["uid"][:8], []).append(tab["uid"])
        for i in tab["injections"]:
            t2_inj["%s#%d" % (tab["uid"][:8], i["col"])] = i
    d1_by_key = {"%s#%d" % (r["uid"][:8], r["col"]): r for r in d1["injections"]}
    d1_by_full = {"%s#%d" % (r["uid"], r["col"]): r for r in d1["injections"]}
    per_case = {(c["uid_alias"], c["col"]): c for c in d3a["a3_dilution_rescue"]["per_case"]}
    return {"d1": d1, "t2": t2, "d3a": d3a, "dr4": dr4, "corpus": corpus,
            "uid8_to_full": uid8_to_full, "t2_inj": t2_inj, "d1_by_key": d1_by_key,
            "d1_by_full": d1_by_full, "per_case": per_case}


# ------------------------------------------------------- C3-1 运行时硬断言 ①-⑤（+ uid8 唯一性）
def run_assertions(L: dict) -> list[dict]:
    out: list[dict] = []

    def chk(cid, desc, level, ok, detail):
        out.append({"id": cid, "desc": desc, "evidence_level": level,
                    "pass": bool(ok), "detail": detail})

    inj = L["d1"]["injections"]
    s15 = {"%s#%d" % (r["uid"][:8], r["col"]) for r in inj
           if r["class"] == "HI" and r["invisibility_mechanism"] == "absorption_silent"}
    d06 = {"%s#%d" % (u, c) for (u, c), v in L["per_case"].items() if v["single_drop10"] == 0.0}
    chk("A1", "J-N1 21 == (D1 class=HI ∧ absorption_silent 15) ∪ (D3 a3 single_drop10==0.0 6); 并集 21 且不相交",
        "recompute", s15 == set(JN1_SILENT15) and d06 == set(JN1_DILUTION6)
        and len(s15 | d06) == 21 and not (s15 & d06),
        {"silent15_match": s15 == set(JN1_SILENT15), "dilution6_match": d06 == set(JN1_DILUTION6),
         "n_silent": len(s15), "n_dilution0": len(d06), "union_n": len(s15 | d06),
         "disjoint": not (s15 & d06)})

    e7 = {"%s#%d" % (r["uid"][:8], r["col"]) for r in inj if r["class"] == "E"}
    jn2_short = {short_of(k) for k in JN2_7}
    dr_keys = [c["key"] for c in L["dr4"]["diff"]["current_e_to_oracle_h"]]
    chk("A2", "J-N2 7 == D1 class=E 集 == DR4 diff.current_e_to_oracle_h[].key（全 key 逐字）",
        "recompute", e7 == jn2_short and sorted(dr_keys) == sorted(JN2_7),
        {"e7_match": e7 == jn2_short, "dr4_keys_match": sorted(dr_keys) == sorted(JN2_7),
         "n_dr4_e2h": len(dr_keys)})

    inter = set(JN1_21) & jn2_short
    chk("A3", "J-N1(21) ∩ J-N2(7) = ∅", "recompute", not inter, {"intersection": sorted(inter)})

    mism, anchors = [], []
    for key in JN1_21 + sorted(jn2_short):
        r1, r2 = L["d1_by_key"].get(key), L["t2_inj"].get(key)
        if r1 is None or r2 is None:
            mism.append({"case": key, "problem": "key missing in D1 or tables_v2"})
            continue
        if r1["original"] != r2["original"] or r1["injected"] != r2["injected"]:
            mism.append({"case": key, "d1": [r1["original"], r1["injected"]],
                         "t2": [r2["original"], r2["injected"]]})
    for k in JN2_7:
        s = short_of(k)
        want = JN2_ANCHORS[s.split("#")[0]]
        got = (L["d1_by_full"][k]["original"], L["d1_by_full"][k]["injected"])
        if got != want:
            anchors.append({"case": s, "card_anchor": list(want), "d1_stored": list(got)})
    chk("A4", "28 例 original/injected 自 D1 injections 逐字读取且与 tables_v2 同 key 字段相等; "
              "J-N2 7 例卡内括号锚点相符", "match",
        len(L["d1_by_key"]) > 0 and not mism and not anchors and len(JN1_21) + len(JN2_7) == 28,
        {"n_compared": len(JN1_21) + len(JN2_7), "mismatches_vs_tables_v2": mism,
         "card_anchor_mismatches": anchors})

    h2 = L["t2_inj"].get(H2E)
    dr_h2e = [c for c in L["dr4"]["diff"]["changes"] if c["direction"] == "H->E"]
    chk("A5", "%s（DR4 唯一 H→E 例）不在 28 调用清单 + tables_v2 确定性证据 visible/absorbed/match_tier"
              " = (true,false,0) + DR4 oracle=E" % H2E, "recompute",
        H2E not in (set(JN1_21) | {short_of(k) for k in JN2_7}) and h2 is not None
        and h2["visible"] is True and h2["absorbed"] is False and h2["match_tier"] == 0
        and len(dr_h2e) == 1 and dr_h2e[0]["uid8"] == H2E.split("#")[0]
        and dr_h2e[0]["col"] == int(H2E.split("#")[1]) and dr_h2e[0]["oracle_label"] == "E",
        {"in_call_list": H2E in (set(JN1_21) | {short_of(k) for k in JN2_7}),
         "deterministic_evidence": None if h2 is None else {k: h2[k] for k in ("visible", "absorbed", "match_tier")},
         "dr4_h2e_n": len(dr_h2e), "dr4_h2e_oracle": None if not dr_h2e else dr_h2e[0]["oracle_label"]})

    collisions = {k: v for k, v in L["uid8_to_full"].items() if len(v) > 1}
    unresolved = [k for k in JN1_21 + [short_of(x) for x in JN2_7] if k.split("#")[0] not in L["uid8_to_full"]]
    chk("A6", "uid8 → full uid 解析在 tables_v2 95 表内 1:1 唯一且 28 例全可解析", "recompute",
        not collisions and not unresolved and len(L["uid8_to_full"]) == 95,
        {"collisions": {k: v for k, v in list(collisions.items())[:5]}, "unresolved": unresolved,
         "n_tables_v2": len(L["t2"]["tables"])})
    return out


# ------------------------------------------------------- 渲染（C3-2 冻结: 原始表头 + 全数据行）
def render_table_md(rows: list[list], n_rows_used: int) -> tuple[str, bool, int]:
    def cell(c):
        return "" if c is None else str(c)
    body = [[cell(c) for c in r] for r in rows]
    truncated = (len(body) - 1) > ROW_CAP
    shown = body[:ROW_CAP + 1] if truncated else body
    hdr = shown[0]
    lines = ["| " + " | ".join(hdr) + " |", "|" + "|".join([" --- "] * len(hdr)) + "|"]
    for r in shown[1:]:
        lines.append("| " + " | ".join(r) + " |")
    if truncated:
        lines.append("...(截断, 共 %d 行)" % n_rows_used)
    return "\n".join(lines), truncated, len(shown) - 1


# ------------------------------------------------------- prompt 构造（代码构造, 禁手工编辑）
def build_cases(L: dict, tpl: dict) -> list[dict]:
    cases: list[dict] = []
    for idx, (subgroup, full_key) in enumerate(
            [("J-N1", k) for k in JN1_21] + [("J-N2", k) for k in JN2_7], start=1):
        s = full_key if subgroup == "J-N1" else short_of(full_key)
        uid8, col = s.split("#")
        col = int(col)
        full_uid = L["uid8_to_full"][uid8][0]
        rows = L["corpus"][full_uid]
        n_rows_used = len(rows)                       # 含表头行（渲染口径见报告 §2）
        md, truncated, n_shown = render_table_md(rows, n_rows_used)
        rec = L["d1_by_key"][s]
        user = (tpl["user_template"]
                .replace("{table_md}", md)
                .replace("{n_rows}", str(n_rows_used))
                .replace("{col_1based}", str(col + 1))
                .replace("{original}", rec["original"])
                .replace("{injected}", rec["injected"]))
        body = json.dumps({"model": MODEL_EXPECT,
                           "messages": [{"role": "system", "content": tpl["system"]},
                                        {"role": "user", "content": user}],
                           "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS,
                           "chat_template_kwargs": {"enable_thinking": False}},
                          ensure_ascii=False).encode("utf-8")
        cases.append({"call_id": "B%02d" % idx, "subgroup": subgroup, "injection_key": s,
                      "injection_key_full": full_key, "uid8": uid8, "full_uid": full_uid,
                      "col": col, "col_1based": col + 1, "original": rec["original"],
                      "injected": rec["injected"], "table_rows_total": n_rows_used,
                      "table_data_rows": n_rows_used - 1, "table_rows_shown": n_shown,
                      "table_truncated": truncated, "table_md": md,
                      "table_md_sha256": sha256_bytes(md.encode("utf-8")),
                      "prompt_text": user, "prompt_sha256": sha256_bytes(user.encode("utf-8")),
                      "request_body_sha256": sha256_bytes(body), "request_body": body})
    return cases


# ------------------------------------------------------- 防泄漏机械扫描（白名单外的表内区除外）
LEAK_EN = ["J-N1", "J-N2", "DR4", "oracle", "HARMFUL", "absorbed", "visible", "match_tier",
           "marginal_dH", "single_drop10", "mapping_target", "canonical", "injection",
           "invisibility", "alias_variant", "ocr_similar", "prefix_noise", "date_variant",
           "mixed_lang", "unit_symbol", "class=", "uid8", "full_uid", "detection", "threshold"]
LEAK_CN = ["静默吸收", "阈值稀释", "等价注入", "有害注入", "预期分类", "注入", "同义词", "归一化"]


def leak_scan(cases: list[dict], L: dict) -> dict:
    hits: list[dict] = []
    uids = {u for v in L["uid8_to_full"].values() for u in v} | set(L["uid8_to_full"])
    for c in cases:
        skeleton = c["prompt_text"].replace(c["table_md"], "\u0000")
        low = skeleton.lower()
        for tok in LEAK_EN + LEAK_CN:
            if tok.lower() in low:
                hits.append({"case": c["injection_key"], "token": tok, "region": "skeleton"})
        for uid in uids:
            if uid and uid in skeleton:
                hits.append({"case": c["injection_key"], "token": uid[:16] + "…", "region": "uid_in_skeleton"})
    observations = [{"case": c["injection_key"], "observation": "injected_header_also_in_table_md",
                     "detail": "修改后列名字面量同时出现在表格 markdown 内（数据事实, 非元数据泄漏通道）"}
                    for c in cases if c["injected"] and c["injected"] in c["table_md"]]
    return {"n_prompts_scanned": len(cases), "hits": hits, "holds": not hits,
            "observations_info_only_not_in_pass_denominator": observations,
            "scan_region_rule": ("扫描 = prompt 去掉表格 markdown 后的骨架（模板固定文本 + 列序号 + "
                                 "原始列名 + 修改后列名）; 表格 markdown 属 C3-2 白名单字段不扫"),
            "token_vocabulary": {"en": LEAK_EN, "cn": LEAK_CN}}


# ------------------------------------------------------- 解析契约（C3-3 冻结）
def extract_json(text: str):
    s = (text or "").strip()
    s = re.sub(r"^```[a-zA-Z]*\s*", "", s)
    s = re.sub(r"\s*```$", "", s).strip()
    start = s.find("{")
    if start < 0:
        return None
    depth = in_str = esc = 0
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(s[start:i + 1])
                except Exception:
                    return None
    return None


def parse_response(text: str) -> tuple[dict | None, str]:
    obj = extract_json(text)
    if obj is None or not isinstance(obj, dict):
        return None, "no_balanced_json_object"
    verdict, conf, rationale = obj.get("verdict"), obj.get("confidence"), obj.get("rationale")
    if verdict not in ("equivalent", "meaning_changed"):
        return None, "verdict_missing_or_off_vocabulary"
    if conf not in ("high", "medium", "low"):
        return None, "confidence_off_vocabulary"
    if not isinstance(rationale, str) or len(rationale) > 200:
        return None, "rationale_not_string_or_over_200"
    return {"verdict": verdict, "confidence": conf, "rationale": rationale}, ""


# ------------------------------------------------------- 甲方标识扫描（token 表 verbatim 复用 D1 冻结脚本）
CLIENT_TOKENS: tuple[str, ...] = ()
ID_TOKENS: tuple[str, ...] = ()


def _load_client_tokens() -> None:
    global CLIENT_TOKENS, ID_TOKENS
    src = (REPO / "research" / "paper_d1_mutant_validity_audit.py").read_text(encoding="utf-8")
    import ast as _ast
    for node in _ast.walk(_ast.parse(src)):
        if isinstance(node, _ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, _ast.Name) and tgt.id == "CLIENT_TOKENS":
                    CLIENT_TOKENS = tuple(_ast.literal_eval(node.value))
                if isinstance(tgt, _ast.Name) and tgt.id == "ID_TOKENS":
                    ID_TOKENS = tuple(_ast.literal_eval(node.value))
    if not CLIENT_TOKENS or not ID_TOKENS:
        raise RuntimeError("client token table not found in D1 script")


def client_identifier_scan(obj) -> dict:
    blob = json.dumps(obj, ensure_ascii=False, default=str)
    low = blob.lower()
    return {"client_token_hits": [t for t in CLIENT_TOKENS if t and t.lower() in low],
            "id_token_hits": [t for t in ID_TOKENS if t and t.lower() in low],
            "scanned_chars": len(blob)}


# ------------------------------------------------------- 调用计数（C3-5）+ append-only JSONL
class Ledger:
    def __init__(self, path: Path):
        self.path, self.n, self.records = path, 0, []
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                self.records.append(rec)
                self.n = max(self.n, int(rec.get("counter", 0)))

    def reserve(self, note: str) -> int:
        if self.n + 1 > BUDGET_CEILING:
            raise RuntimeError("BUDGET_HARD_GATE: counter=%d ceiling=%d（>200 立即中止）" % (self.n, BUDGET_CEILING))
        self.n += 1
        self._append({"kind": "reserve", "counter": self.n, "note": note,
                      "ts": datetime.now().astimezone().isoformat()})
        return self.n

    def _append(self, rec: dict) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.records.append(rec)   # 内存镜像须与落盘行同步: 否则本次调用写的行不进账本快照, 计数恒等式失真

    def final_by_case(self) -> dict:
        out: dict[str, dict] = {}
        for r in self.records:
            if r.get("kind") != "call":
                continue
            k = r["injection_key"]
            cur = out.get(k)
            if cur is None or int(cur["attempt"]) <= int(r["attempt"]):
                out[k] = r
        return {k: v for k, v in out.items() if v.get("status") in ("ok", "invalid_final")}

    def attempts_by_case(self) -> dict:
        out: dict[str, list] = {}
        for r in self.records:
            if r.get("kind") == "call":
                out.setdefault(r["injection_key"], []).append(r)
        return out


def call_8004(body: bytes, ledger: Ledger, note: str) -> tuple[str, str, int, dict, int]:
    """一次推理 HTTP 请求（失败/超时同样计数）。返回 (content, error, latency_ms, usage, counter)。"""
    n = ledger.reserve(note)
    t0 = time.monotonic()
    try:
        raw = http(ENDPOINT, body, timeout=TIMEOUT_S)
        err = ""
    except Exception as exc:                              # noqa: BLE001 - 失败也须记账
        raw, err = "", "%s: %s" % (type(exc).__name__, str(exc)[:260])
    latency = int((time.monotonic() - t0) * 1000)
    content, usage = "", {}
    if not err:
        try:
            obj = json.loads(raw)
            content = (obj.get("choices") or [{}])[0].get("message", {}).get("content", "")
            usage = obj.get("usage") or {}
        except Exception as exc:                          # noqa: BLE001
            err = "response_shape: %s: %s" % (type(exc).__name__, str(raw)[:200])
    return content, err, latency, usage, n


# ------------------------------------------------------- 确定性聚合（C3-3, 不设新过判）
def aggregate(cases: list[dict], by_case: dict) -> dict:
    per_case, cross = [], {"J-N1": {"equivalent": 0, "meaning_changed": 0, "invalid_final": 0},
                           "J-N2": {"equivalent": 0, "meaning_changed": 0, "invalid_final": 0}}
    conf_dist = {"high": 0, "medium": 0, "low": 0}
    for c in cases:
        rec = by_case.get(c["injection_key"]) or {}
        parsed = rec.get("parsed") or {}
        ok = rec.get("status") == "ok"
        verdict = parsed.get("verdict") if ok and parsed else "invalid_final"
        if verdict in ("equivalent", "meaning_changed"):
            cross[c["subgroup"]][verdict] += 1
            if parsed.get("confidence") in conf_dist:
                conf_dist[parsed.get("confidence")] += 1
        per_case.append({"call_id": c["call_id"], "subgroup": c["subgroup"],
                         "injection_key": c["injection_key"], "uid8": c["uid8"], "col": c["col"],
                         "col_1based": c["col_1based"], "original": c["original"],
                         "injected": c["injected"], "attempts": rec.get("attempt"),
                         "status": rec.get("status", "not_executed"), "verdict": verdict,
                         "confidence": parsed.get("confidence"), "rationale": parsed.get("rationale"),
                         "judge_harmful": {"meaning_changed": True, "equivalent": False}.get(verdict),
                         "prompt_sha256": c["prompt_sha256"], "table_truncated": c["table_truncated"],
                         "latency_ms": rec.get("latency_ms"), "usage": rec.get("usage") or {},
                         "counter": rec.get("counter"), "parse_error": rec.get("parse_error", ""),
                         "resumed_from_ledger": bool(rec.get("resumed_from_ledger")),
                         "raw_response": rec.get("raw_response", "")})

    def rate(g: str, v: str) -> dict:
        valid = cross[g]["equivalent"] + cross[g]["meaning_changed"]
        return {"numerator": cross[g][v], "valid_denominator": valid,
                "rate": (round(cross[g][v] / valid, 6) if valid else None),
                "invalid_final_excluded": cross[g]["invalid_final"],
                "frozen_denominator": 21 if g == "J-N1" else 7}

    return {"per_case": per_case, "verdict_cross_tab": cross,
            "jn1_confirmation_rate": rate("J-N1", "meaning_changed"),
            "jn2_equivalent_rate_supports_current_E": rate("J-N2", "equivalent"),
            "jn2_meaning_changed_rate_supports_dr4_oracle_H": rate("J-N2", "meaning_changed"),
            "confidence_distribution_valid_only": conf_dist,
            "tokens_valid_calls": {"prompt_tokens": sum(p["usage"].get("prompt_tokens", 0) for p in per_case),
                                   "completion_tokens": sum(p["usage"].get("completion_tokens", 0) for p in per_case)},
            "mapping_rule": {"meaning_changed": "judge_harmful=true", "equivalent": "judge_harmful=false",
                             "invalid_final": "不入分子分母, 逐例原样列出, 不填补不以人工判定替代"}}


def dr4_comparison_8rows(cases: list[dict], by_case: dict, L: dict) -> list[dict]:
    rows = []
    for c in L["dr4"]["diff"]["changes"]:
        s = short_of(c["key"])
        row = {"key": c["key"], "direction": c["direction"], "current_label": c["current_class"],
               "dr4_oracle": c["oracle_label"], "type": c["type"],
               "first_failing_criterion": c.get("evidence_criterion_first_fail")}
        hit = next((x for x in cases if x["injection_key"] == s), None)
        if hit is not None:
            rec = by_case.get(s) or {}
            parsed = rec.get("parsed") or {}
            ok = rec.get("status") == "ok"
            row.update({"evidence_kind": "judge_verdict", "judge_verdict": parsed.get("verdict") if ok else None,
                        "judge_confidence": parsed.get("confidence") if ok else None,
                        "judge_status": rec.get("status", "not_executed"),
                        "deterministic_evidence": None,
                        "agreement": (None if not ok else
                                      ("agree" if (parsed["verdict"] == "meaning_changed") == (c["oracle_label"] == "HARMFUL")
                                       else "disagree"))})
        else:
            t2i = L["t2_inj"][s]
            det = {k: t2i[k] for k in ("visible", "absorbed", "match_tier")}
            row.update({"evidence_kind": "deterministic_evidence", "judge_verdict": None,
                        "judge_confidence": None, "judge_status": "not_called_zero_calls",
                        "deterministic_evidence": det,
                        "agreement": "disagree",
                        "agreement_note": "确定性通道判为检出（visible=true ∧ absorbed=false ∧ match_tier=0）"
                                          "而 DR4 oracle = 等价 ⇒ 方向不一致, 如实入账（卡加编 2 澄清: 本例零 judge 调用）"})
        rows.append(row)
    return rows


def divergence_triggers(agg: dict) -> dict:
    jn1, jn2 = agg["jn1_confirmation_rate"], agg["jn2_equivalent_rate_supports_current_E"]
    jn1_equivalent = jn1["valid_denominator"] - jn1["numerator"]
    t1 = jn2["numerator"] >= 4
    t2 = jn1_equivalent >= 11
    return {"trigger_1_jn2_ge_4of7_equivalent_vs_dr4_oracle": t1,
            "jn2_equivalent_valid": jn2["numerator"],
            "trigger_2_jn1_ge_11of21_equivalent_undermines_harmful_set": t2,
            "jn1_equivalent_valid": jn1_equivalent,
            "any_triggered": bool(t1 or t2),
            "semantics": "C3-3 上报纪律（非判据）: 命中 = 即时上报 Loop D, 不等 autopsy 排期"}


# ------------------------------------------------------- prompt 契约自证（结构级: 模板字面段 ∘ 五占位值）
def contract_selfcheck(cases: list[dict], tpl: dict) -> dict:
    """逐例重建: prompt_text 必须 = 模板字面段与五个白名单值交替拼接, 零残余字符。
    与构造代码不同路径（模板 re.split 后逐段 startswith 游标推进）=> 非循环验证。"""
    parts = re.split(r"\{([a-z_][a-z_0-9]*)\}", tpl["user_template"])   # 占位符含数字（col_1based）
    ph_vocab = sorted(set(parts[1::2]))
    expected = ["col_1based", "injected", "n_rows", "original", "table_md"]
    bad = []
    for c in cases:
        vals = {"table_md": c["table_md"], "n_rows": str(c["table_rows_total"]),
                "col_1based": str(c["col_1based"]), "original": c["original"],
                "injected": c["injected"]}
        pos, ok = 0, True
        for i, seg in enumerate(parts):
            if i % 2 == 0:
                if not c["prompt_text"].startswith(seg, pos):
                    ok = False
                    break
                pos += len(seg)
            else:
                if seg not in vals:
                    ok = False
                    break
                v = vals[seg]
                if not c["prompt_text"].startswith(v, pos):
                    ok = False
                    break
                pos += len(v)
        if not ok or pos != len(c["prompt_text"]):
            bad.append({"case": c["injection_key"], "cursor": pos, "len": len(c["prompt_text"])})
    return {"n_prompts": len(cases), "template_placeholder_vocabulary": ph_vocab,
            "expected_vocabulary": expected, "vocabulary_exact": ph_vocab == expected,
            "unique_prompt_sha256": len({x["prompt_sha256"] for x in cases}),
            "binding_violations": bad,
            "holds": bool(not bad and ph_vocab == expected
                          and len({x["prompt_sha256"] for x in cases}) == len(cases)),
            "note": ("逐例 prompt_text = 卡内 user 模板字面段 ∘ 五白名单值, 游标推进须恰好用尽全文"
                     "=> 零手工编辑 / 零附加字段 / 零缺字段")}


# ------------------------------------------------------- 端点窗
def run_window(L: dict, tpl: dict, sha_before: dict, out_path: Path) -> dict:
    checks = run_assertions(L)
    if not all(c["pass"] for c in checks):
        raise SystemExit("C3-1 运行时硬断言失败 → 停报（零调用）: %s"
                         % json.dumps([c for c in checks if not c["pass"]], ensure_ascii=False)[:1200])
    cases = build_cases(L, tpl)
    leak = leak_scan(cases, L)
    csc = contract_selfcheck(cases, tpl)
    if not (leak["holds"] and csc["holds"]):
        raise SystemExit("防泄漏 / prompt 契约自证失败 → 停报（零调用）")

    served = json.loads(http(MODELS, timeout=10))                    # 不计数
    ids = [m.get("id") for m in served.get("data", [])] or \
          [m.get("name") for m in served.get("models", [])]
    model_ok = MODEL_EXPECT in ids
    health = json.loads(http(HEALTH, timeout=10))                    # 不计数
    model_assert = {"expected": MODEL_EXPECT, "served_ids": ids, "holds": model_ok,
                    "health": health, "counted_as_inference": False,
                    "rule": "零现场换模型: 不一致 → 停报"}
    if not model_ok:
        raise SystemExit("C3-4 模型断言失败 → 停报（零调用）: served=%s" % ids)

    ledger = Ledger(LEDGER)
    calls: list[dict] = []
    canary_body = json.dumps({"model": MODEL_EXPECT,
                              "messages": [{"role": "user", "content": tpl["canary_prompt"]}],
                              "temperature": TEMPERATURE, "max_tokens": CANARY_MAX_TOKENS,
                              "chat_template_kwargs": {"enable_thinking": False}},
                             ensure_ascii=False).encode("utf-8")
    content, err, latency, usage, cn = call_8004(canary_body, ledger, "canary")
    parsed = extract_json(content) if not err else None
    canary_ok = bool(isinstance(parsed, dict) and parsed.get("ok") is True)
    canary = {"counted": True, "counter_at": cn, "prompt_text": tpl["canary_prompt"],
              "prompt_sha256": tpl["canary_prompt_sha256"], "raw_response": content, "error": err,
              "parsed": parsed, "ok": canary_ok, "latency_ms": latency, "usage": usage,
              "model": MODEL_EXPECT, "temperature": TEMPERATURE, "max_tokens": CANARY_MAX_TOKENS,
              "ts": datetime.now().astimezone().isoformat()}
    ledger._append(dict(kind="canary", counter=cn, ok=canary_ok, ts=canary["ts"]))
    if not canary_ok:
        return {"aborted": "CANARY_FAILED", "canary": canary, "calls": calls,
                "counter_total": ledger.n, "assertions": checks, "leak_scan": leak,
                "contract_selfcheck": csc, "model_assert": model_assert,
                "inputs_sha256_before": sha_before}

    prior = ledger.final_by_case()
    for c in cases:
        if c["injection_key"] in prior:
            rec = dict(prior[c["injection_key"]], resumed_from_ledger=True)
            calls.append(rec)
            continue
        for attempt in (1, 2):
            content, err, latency, usage, cn = call_8004(
                c["request_body"], ledger, "%s a%d" % (c["injection_key"], attempt))
            parsed, perr = ((None, err) if err else parse_response(content))
            if parsed is not None:
                status = "ok"
            elif attempt == 1:
                status = "invalid_retry"
            else:
                status = "invalid_final"
            rec = {"call_id": c["call_id"], "subgroup": c["subgroup"],
                   "injection_key": c["injection_key"], "uid8": c["uid8"], "col": c["col"],
                   "attempt": attempt, "prompt_sha256": c["prompt_sha256"],
                   "prompt_text": c["prompt_text"], "table_truncated": c["table_truncated"],
                   "raw_response": content, "parsed": parsed, "parse_error": perr,
                   "request_error": err, "status": status, "model": MODEL_EXPECT,
                   "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS, "latency_ms": latency,
                   "usage": usage, "counter": cn, "ts": datetime.now().astimezone().isoformat(),
                   "request_body_sha256": c["request_body_sha256"], "kind": "call"}
            ledger._append(rec)
            calls.append(rec)
            if status != "invalid_retry":
                break
    by_case: dict[str, dict] = {}
    for r in calls:
        k = r["injection_key"]
        if k not in by_case or int(r["attempt"]) >= int(by_case[k]["attempt"]):
            by_case[k] = r
    return {"aborted": None, "canary": canary, "calls": calls, "counter_total": ledger.n,
            "assertions": checks, "leak_scan": leak, "contract_selfcheck": csc,
            "model_assert": model_assert, "by_case": by_case, "cases": cases,
            "resumed_cases": sorted(k for k in by_case if by_case[k].get("resumed_from_ledger")),
            "ledger_attempts": {k: len(v) for k, v in ledger.attempts_by_case().items()},
            "ledger_rows": list(ledger.records), "stage_a_file_sha": sha256_file(D3A_ART),
            "inputs_sha256_before": sha_before}


# ------------------------------------------------------- 收口工件（C3-3 冻结 schema）
def frozen_records(cases: list, by_case: dict) -> tuple[list, list]:
    """per-call 记录 = C3-3 冻结字段集; 诊断附加项另列 supplement 不污染冻结 schema。"""
    records, supplement = [], []
    for c in cases:
        rec = by_case.get(c["injection_key"])
        if rec is None:
            continue
        records.append({"call_id": c["call_id"], "subgroup": c["subgroup"],
                        "injection_key": c["injection_key"], "uid8": c["uid8"], "col": c["col"],
                        "attempt": rec["attempt"], "prompt_sha256": rec["prompt_sha256"],
                        "prompt_text": rec["prompt_text"], "table_truncated": rec["table_truncated"],
                        "raw_response": rec["raw_response"], "parsed": rec["parsed"],
                        "status": rec["status"], "model": rec["model"],
                        "temperature": rec["temperature"], "max_tokens": rec["max_tokens"],
                        "latency_ms": rec["latency_ms"], "ts": rec["ts"]})
        supplement.append({"injection_key": c["injection_key"],
                           "injection_key_full": c["injection_key_full"], "attempt": rec["attempt"],
                           "counter": rec.get("counter"),
                           "request_body_sha256": c["request_body_sha256"],
                           "table_md_sha256": c["table_md_sha256"], "col_1based": c["col_1based"],
                           "original": c["original"], "injected": c["injected"],
                           "usage": rec.get("usage") or {}, "parse_error": rec.get("parse_error", ""),
                           "request_error": rec.get("request_error", ""),
                           "resumed_from_ledger": bool(rec.get("resumed_from_ledger"))})
    return records, supplement


def build_doc(L: dict, tpl: dict, w: dict, sha_before: dict, sha_after: dict) -> dict:
    cases, by_case = w["cases"], w["by_case"]
    records, supplement = frozen_records(cases, by_case)
    agg = aggregate(cases, by_case)
    dr4 = dr4_comparison_8rows(cases, by_case, L)
    trig = divergence_triggers(agg)
    total = int(w["counter_total"])
    retries = sum(1 for s in supplement if s["attempt"] == 2)
    ports = sorted(PORTS_TOUCHED)
    ledger_rows = w.get("ledger_rows", [])
    canary_probes = sum(1 for r in ledger_rows if r.get("kind") == "canary")
    call_lines = sum(1 for r in ledger_rows if r.get("kind") == "call")
    reserve_lines = sum(1 for r in ledger_rows if r.get("kind") == "reserve")
    counter_identity = (total == canary_probes + call_lines)
    new_calls_this_run = 1 + sum(1 for c in w["cases"]
                                 if not (w.get("by_case", {}).get(c["injection_key"]) or {}).get("resumed_from_ledger"))
    client = client_identifier_scan({"records": records, "supplement": supplement,
                                     "agg": agg, "dr4": dr4, "tpl": tpl})
    gates = {
        "GG1_C3_1_runtime_hard_assertions": all(c["pass"] for c in w["assertions"]),
        "GG2_C3_4_model_service_assertion": w["model_assert"]["holds"],
        "GG3_canary_ok_and_counted": bool(w["canary"]["ok"]) and bool(w["canary"]["counted"]),
        "GG4_budget_hard_gate_le_200": total <= BUDGET_CEILING,
        "GG5_28_cases_all_final": (len(records) == 28 and
                                   all(r["status"] in ("ok", "invalid_final") for r in records)),
        "GG6_only_8004_touched": ports == [ALLOWED_PORT] and not PORT_VIOLATIONS,
        "GG7_8006_zero_touch": (8006 not in ports) and (8008 not in ports),
        "GG8_leak_guard_and_prompt_contract": w["leak_scan"]["holds"] and w["contract_selfcheck"]["holds"],
        "GG9_frozen_inputs_readonly": sha_before == sha_after,
        "GG10_counter_identity_vs_ledger": counter_identity,
        "GG11_card_sha_pinned": sha_before.get(str(CARD.relative_to(REPO)).replace(os.sep, "/")) == CARD_SHA_EXPECT,
        "GG12_client_identifier_zero": not client["client_token_hits"] and not client["id_token_hits"],
        "GG13_jn3_zero_calls": True,
    }
    gates["all_pass"] = all(v is True for v in gates.values())
    payload = {
        "inputs_sha256_before": sha_before, "inputs_sha256_after": sha_after,
        "criterion_provenance": {
            "task_card": str(CARD.relative_to(REPO)),
            "contract": "加编 3（C3-1 案例清单 / C3-2 模板与渲染 / C3-3 schema 与聚合 / C3-4 模型设置 / C3-5 计数）",
            "stage_A_artifact": str(D3A_ART.relative_to(REPO)),
            "dr4_artifact": str(DR4_ART.relative_to(REPO)),
            "zero_new_criterion": True,
            "collection_vs_judgment": "本窗只收集 + 确定性聚合; 结论判定归 Loop D / autopsy（C3-6）"},
        "measurement_contract": {
            "system_prompt_sha256": tpl["system_sha256"], "system_prompt_text": tpl["system"],
            "user_template_sha256": tpl["user_template_sha256"],
            "user_template_text": tpl["user_template"],
            "canary_prompt_sha256": tpl["canary_prompt_sha256"],
            "jn1_21_keys": JN1_21, "jn2_7_keys": JN2_7, "jn3_calls": 0,
            "model": MODEL_EXPECT, "temperature": TEMPERATURE, "max_tokens": MAX_TOKENS,
            "enable_thinking": False, "timeout_s": TIMEOUT_S, "row_cap": ROW_CAP,
            "budget_ceiling": BUDGET_CEILING, "expected_upper_bound_calls": 57},
        "runtime_assertions": w["assertions"],
        "model_service_assertion": w["model_assert"],
        "canary": w["canary"],
        "leak_guard": w["leak_scan"],
        "prompt_contract_selfcheck": w["contract_selfcheck"],
        "calls": records,
        "call_supplement": {"fields": "非冻结诊断补充（计数器 / 请求体 sha / usage / 错误文本）",
                            "rows": supplement},
        "call_counter_total": total,
        "call_counter_breakdown": {
            "counter_total_vs_ceiling": {"total": total, "ceiling": BUDGET_CEILING,
                                         "within": total <= BUDGET_CEILING,
                                         "expected_upper_bound_single_run": 57},
            "canary_probes_all_invocations": canary_probes,
            "formal_call_records_in_window": len(records),
            "formal_distinct_cases": len({r["injection_key"] for r in records}),
            "invalid_retries": retries,
            "resumed_cases_reusing_append_only_ledger": len(w.get("resumed_cases", [])),
            "new_inference_calls_this_invocation": new_calls_this_run,
            "identity_counter_eq_canary_plus_call_records": counter_identity,
            "identity_note": ("计数器每次推理请求前 +1 且同步行落 JSONL（append-only）; "
                             "恒等式 = counter_total == canary 探针数 + call 记录数 ⇒ 零计数外请求。"
                             "续跑（装配缺陷修复后重开窗）只重发 canary 探针, 28 例判定复用账本"
                             "（payload 字节相同 ⇒ 判定不可变）, 账本行完整保留两次探针的审计痕迹"),
            "ledger_path": str(LEDGER.relative_to(REPO)),
            "ledger_lines_total": len(ledger_rows),
            "ledger_reserve_lines": reserve_lines,
            "ledger_reserve_eq_counter": reserve_lines == total},
        "verdict_cross_tab": agg["verdict_cross_tab"],
        "jn1_confirmation_rate": agg["jn1_confirmation_rate"],
        "jn2_equivalent_rate_supports_current_E": agg["jn2_equivalent_rate_supports_current_E"],
        "jn2_meaning_changed_rate_supports_dr4_oracle_H": agg["jn2_meaning_changed_rate_supports_dr4_oracle_H"],
        "per_case": agg["per_case"],
        "confidence_distribution_valid_only": agg["confidence_distribution_valid_only"],
        "tokens_valid_calls": agg["tokens_valid_calls"],
        "aggregation_rule": agg["mapping_rule"],
        "dr4_comparison_8rows": dr4,
        "dr4_agreement_tally": {"agree": sum(1 for r in dr4 if r["agreement"] == "agree"),
                                "disagree": sum(1 for r in dr4 if r["agreement"] == "disagree"),
                                "unresolved_invalid_final": sum(1 for r in dr4 if r["agreement"] is None)},
        "divergence_triggers_report_discipline": trig,
        "gate_details": gates,
        "redline_self_check": {
            "stage": "B_endpoint_window（仅 :8004）", "ports_observed": ports,
            "endpoint_violations": PORT_VIOLATIONS,
            "endpoint_8004_only": gates["GG6_only_8004_touched"],
            "endpoint_8006_zero_touch": gates["GG7_8006_zero_touch"],
            "jn3_zero_calls": True, "tat_dqa_frozen_line_untouched": True,
            "frozen_nodes_untouched": "tests/test_m1_service.py / ~/wzh/m1_samples / frozen_hashes 零读写",
            "read_only_frozen_inputs": {"sha_equal": sha_before == sha_after, "n_inputs": len(sha_before)},
            "client_identifier_scan": client,
            "git_discipline": "逐路径 add; 禁 -A / 禁 amend", "outbound_sent": False,
            "j7_endpoint_robustness_window_not_opened": True},
        "window_abort": w.get("aborted")}
    dig = sha256_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    doc = {"meta": {"name": "d3-matched-fpr-stage-b", "version": "v1", "card_id": "TASK-20260901-D3",
                    "task_card": str(CARD.relative_to(REPO)),
                    "contract": "加编 3 C3-1..C3-6 = 测量契约（零现场定义空间）",
                    "report": "docs/experiments/2026-09-06_d3_matched_fpr_stage_b.md",
                    "script": "research/paper_d3_stage_b_judge.py",
                    "phase": "B_endpoint_window_8004",
                    "generated": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                    "inference_endpoint": ENDPOINT, "model": MODEL_EXPECT,
                    "call_counter_total": total,
                    "reproduce": ["venv/bin/python research/paper_d3_stage_b_judge.py --stage window"],
                    "cross_caliber_note": ("本窗 judge = :8004（A3B, temp=0）与历史四维 judge 基线"
                                           "（4.94-5.0, 含 :8006 xhigh 档）不同口径; 仅用于 J-N1/J-N2"
                                           " 效度判定, 不与历史 judge 分数作跨比较（C3-4）")},
           "gates": gates, "payload": payload, "payload_sha256": dig,
           "digest_self_consistency": None}
    doc["digest_self_consistency"] = (sha256_bytes(json.dumps(
        doc["payload"], ensure_ascii=False, sort_keys=True).encode("utf-8")) == dig)
    return doc


# ------------------------------------------------------- 入口
def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                        # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("preflight", "window"), default="preflight")
    ap.add_argument("--dump-prompts", default="", help="预检用: 把 28 例 prompt 落盘到给定路径（建议 /tmp）")
    args = ap.parse_args()
    window = args.stage == "window"
    install_guard(window)
    _load_client_tokens()
    key = lambda p: str(Path(p).relative_to(REPO)).replace(os.sep, "/")  # noqa: E731
    sha_before = {key(p): sha256_file(p) for p in FROZEN_INPUTS}
    t0 = time.time()
    L = load_inputs()
    tpl = extract_template()
    checks = run_assertions(L)
    print("stage = %s | card_sha = %s | system_sha = %s | user_tmpl_sha = %s"
          % (args.stage, sha256_file(CARD)[:12], tpl["system_sha256"][:12], tpl["user_template_sha256"][:12]))
    print("C3-1 assertions:", json.dumps({c["id"]: c["pass"] for c in checks}, ensure_ascii=False))
    for c in checks:
        if not c["pass"]:
            print("FAIL", c["id"], json.dumps(c["detail"], ensure_ascii=False)[:900])
    sha_after_early = {key(p): sha256_file(p) for p in FROZEN_INPUTS}
    if not all(c["pass"] for c in checks):
        print("=> 停报（C3-1 任一失败 → 零调用, 零现场替换）")
        return 2
    cases = build_cases(L, tpl)
    leak = leak_scan(cases, L)
    csc = contract_selfcheck(cases, tpl)
    sizes = [len(c["prompt_text"].encode("utf-8")) for c in cases]
    print("leak_guard holds = %s | hits = %s" % (leak["holds"], leak["hits"][:6]))
    print("leak observations(info) = %s" % json.dumps(
        leak["observations_info_only_not_in_pass_denominator"], ensure_ascii=False)[:300])
    print("prompt contract = %s" % json.dumps(
        {k: csc[k] for k in ("template_placeholder_vocabulary", "vocabulary_exact",
                             "unique_prompt_sha256", "n_prompts", "holds")}, ensure_ascii=False))
    print("prompt bytes min/max/mean = %d/%d/%.1f | truncated = %s"
          % (min(sizes), max(sizes), sum(sizes) / len(sizes),
             [c["injection_key"] for c in cases if c["table_truncated"]]))
    if not (leak["holds"] and csc["holds"]):
        print("=> 停报（防泄漏 / prompt 契约自证失败 → 零调用）")
        return 2
    if not window:
        print("ports_touched = %s | violations = %s（预检窗应恒空）" % (sorted(PORTS_TOUCHED), PORT_VIOLATIONS))
        print("cases:")
        for c in cases:
            print("  %s %s %-12s rows=%2d sha=%s" % (c["call_id"], c["subgroup"], c["injection_key"],
                                                     c["table_rows_total"], c["prompt_sha256"][:12]))
        if args.dump_prompts:
            Path(args.dump_prompts).write_text(json.dumps(
                [{"key": c["injection_key"], "prompt_sha256": c["prompt_sha256"],
                  "request_body_sha256": c["request_body_sha256"], "prompt_text": c["prompt_text"]}
                 for c in cases], ensure_ascii=False, indent=1), encoding="utf-8")
            print("prompts dumped ->", args.dump_prompts)
        print("preflight ok | elapsed %.1fs | frozen sha equal = %s"
              % (time.time() - t0, sha_before == sha_after_early))
        return 0
    w = run_window(L, tpl, sha_before, OUT)
    sha_after = {key(p): sha256_file(p) for p in FROZEN_INPUTS}
    if w.get("aborted"):
        Path("/tmp/d3b_abort.json").write_text(json.dumps(
            {"aborted": w["aborted"], "canary": w["canary"], "counter_total": w["counter_total"],
             "ts": datetime.now().astimezone().isoformat()}, ensure_ascii=False, indent=1), encoding="utf-8")
        print("=> 窗中止: %s（canary 异常即停 + 记账 /tmp/d3b_abort.json, 正式工件零产出）" % w["aborted"])
        print("counter_total =", w["counter_total"], "| ports =", sorted(PORTS_TOUCHED))
        return 3
    doc = build_doc(L, tpl, w, sha_before, sha_after)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(doc["gates"], ensure_ascii=False, indent=1))
    print("call_counter_total = %d (canary 1 + formal 28 + retries %d) | ceiling %d | ports %s"
          % (doc["meta"]["call_counter_total"], doc["payload"]["call_counter_breakdown"]["invalid_retries"],
             BUDGET_CEILING, sorted(PORTS_TOUCHED)))
    print("J-N1 =", json.dumps(doc["payload"]["jn1_confirmation_rate"], ensure_ascii=False))
    print("J-N2 equiv =", json.dumps(doc["payload"]["jn2_equivalent_rate_supports_current_E"], ensure_ascii=False))
    print("J-N2 changed =", json.dumps(doc["payload"]["jn2_meaning_changed_rate_supports_dr4_oracle_H"], ensure_ascii=False))
    print("triggers =", json.dumps(doc["payload"]["divergence_triggers_report_discipline"], ensure_ascii=False))
    print("dr4 tally =", json.dumps(doc["payload"]["dr4_agreement_tally"], ensure_ascii=False))
    print("artifact = %s | payload_sha256 = %s | digest_self_consistency = %s | elapsed %.1fs"
          % (key(OUT), doc["payload_sha256"][:16], doc["digest_self_consistency"], time.time() - t0))
    return 0 if doc["gates"]["all_pass"] else 4


if __name__ == "__main__":
    sys.exit(main())
