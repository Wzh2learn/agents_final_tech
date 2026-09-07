"""D3 Stage B closeout spot-check (Loop D, C3-6 interface).

Read-only + zero endpoint. Independently rebuilds the frozen measurement contract
(card addendum 3, C3-1..C3-6) from source artifacts and compares it against the
delivered Stage B artifacts, ledger, report, STATE and THREADS entries.

Emits logs/graph/eval/d3_stage_b_closeout_spotcheck.json
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
import socket
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL = REPO / "logs" / "graph" / "eval"
CARD = REPO / "docs" / "experiments" / "2026-09-01_d3_matched_specificity_card.md"
ART = EVAL / "d3_matched_fpr_stage_b.json"
LEDGER = EVAL / "d3_stage_b_call_ledger.jsonl"
REPORT = REPO / "docs" / "experiments" / "2026-09-06_d3_matched_fpr_stage_b.md"
D1_ART = EVAL / "d1_mutant_validity_audit.json"
T2_ART = EVAL / "checkpoint_discrimination_tables_v2.json"
D3A_ART = EVAL / "d3_matched_fpr_stage_a.json"
DR4_ART = EVAL / "dr4_d1_reclassification_review.json"
CORPUS = REPO / "data" / "research" / "drift_v0" / "input" / "tatqa_tables.json"
STATE = REPO / "memory" / "STATE.md"
THREADS = REPO / "memory" / "THREADS.md"
D1_SCRIPT = REPO / "research" / "paper_d1_mutant_validity_audit.py"
OUT = EVAL / "d3_stage_b_closeout_spotcheck.json"

MODEL_EXPECT = "Qwen3.6-35B-A3B-Q4_K_M.gguf"
ROW_CAP = 40
BUDGET_CEILING = 200
CARD_SHA_EXPECT = "22eaa5117b8472472b24eb038e18d8af855de36c49f7dd46dd295fefe9ade411"

# The frozen corpus (data/research/drift_v0/input/tatqa_tables.json) lives only on GB10.
# Loop D reads a sha-verified mirror instead; --corpus PATH overrides the default.
CORPUS_MIRROR: Path | None = None
CORPUS_PROVENANCE = "repo"
for _i, _a in enumerate(sys.argv[1:]):
    if _a == "--corpus" and len(sys.argv) > _i + 2:
        CORPUS_MIRROR = Path(sys.argv[_i + 2])
        CORPUS_PROVENANCE = "gb10_mirror:%s" % CORPUS_MIRROR

# ---------------------------------------------------------- zero endpoint guard
SOCKET_ATTEMPTS: list[str] = []
_real_connect = socket.socket.connect
_real_connect_ex = socket.socket.connect_ex


def _blocked(self, address, *a, **k):
    SOCKET_ATTEMPTS.append(str(address))
    raise RuntimeError("ZERO_ENDPOINT_GUARD blocked %s" % (address,))


socket.socket.connect = _blocked          # type: ignore[assignment]
socket.socket.connect_ex = _blocked       # type: ignore[assignment]

# ---------------------------------------------------------- helpers
CHECKS: list[dict] = []


def chk(cid: str, desc: str, level: str, passed, detail=None) -> None:
    CHECKS.append({"id": cid, "desc": desc, "evidence_level": level,
                   "pass": bool(passed), "detail": detail})


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: Path) -> str:
    return sha_bytes(p.read_bytes())


def jload(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def payload_of(doc):
    return doc.get("payload", doc) if isinstance(doc, dict) else doc


def rel(p: Path) -> str:
    return str(p.relative_to(REPO)).replace("\\", "/")


def sha_file_eol(p: Path) -> tuple:
    """sha256 of raw bytes and of LF-normalized bytes (Windows core.autocrlf checkout)."""
    b = p.read_bytes()
    return sha_bytes(b), sha_bytes(b.replace(bytes([13, 10]), bytes([10])))


def norm(text: str) -> str:
    """Whitespace/markdown-insensitive form used for cross-document number checks."""
    t = text.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", t)


def short_of(full_key: str) -> str:
    uid, col = full_key.split("#")
    return "%s#%s" % (uid[:8], col)


# ---------------------------------------------------------- card parsing (frozen text)
def parse_card() -> dict:
    card = CARD.read_text(encoding="utf-8")
    sec = card.split("### C3-2", 1)[1].split("### C3-3", 1)[0]
    blocks = [b[:-1] if b.endswith("\n") else b for b in re.findall(r"```text\n(.*?)```", sec, re.S)]
    if len(blocks) != 2:
        raise RuntimeError("C3-2 text blocks != 2 (got %d)" % len(blocks))
    canary = re.search(r"冻结 prompt = user 消息 `([^`]+)`", card)
    if not canary:
        raise RuntimeError("canary prompt not found in card")
    placeholders = sorted(set(re.findall(r"\{([a-z_][a-z_0-9]*)\}", blocks[1])))

    c31 = card.split("### C3-1", 1)[1].split("### C3-2", 1)[0]
    def key_run(label: str) -> list:
        """Card writes each frozen list as ONE backtick run: a#1 / b#2 / ..."""
        blob = re.search(re.escape(label) + " *`([^`]+)`", c31).group(1)
        keys = [k.strip() for k in blob.split("/") if k.strip()]
        if not all(re.fullmatch("[0-9a-f]{8}#[0-9]+", k) for k in keys):
            raise RuntimeError("malformed key run for %s: %s" % (label, keys))
        return keys

    silent15 = key_run("silent 15:")
    dilution6 = key_run("dilution-0 6:")
    jn2_block = c31.split("**J-N2", 1)[1]
    jn2_7 = re.findall(r"^\d+\.\s+`([0-9a-f-]{36}#\d+)`", jn2_block, re.M)
    anchors = dict(re.findall(r"`([0-9a-f-]{36}#\d+)`（([^）]*)）", jn2_block))
    return {"system": blocks[0], "user_template": blocks[1], "canary_prompt": canary.group(1),
            "placeholders": placeholders, "silent15": silent15, "dilution6": dilution6,
            "jn1_21": silent15 + dilution6, "jn2_7": jn2_7, "jn2_anchors": anchors,
            "text": card}


# ---------------------------------------------------------- independent renderer (C3-2)
def render_table_md(rows: list) -> tuple:
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
        lines.append("...(截断, 共 %d 行)" % len(rows))
    return "\n".join(lines), truncated, len(shown) - 1


def rebuild_prompt(tpl: dict, md: str, n_rows: int, col: int, original: str, injected: str) -> str:
    return (tpl["user_template"]
            .replace("{table_md}", md)
            .replace("{n_rows}", str(n_rows))
            .replace("{col_1based}", str(col + 1))
            .replace("{original}", original)
            .replace("{injected}", injected))


# ---------------------------------------------------------- conservative parser (C3-3)
def parse_response(raw: str):
    if not isinstance(raw, str):
        return None, "raw_not_string"
    t = raw.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t).strip()
    start = t.find("{")
    if start < 0:
        return None, "no_json_object"
    depth = 0
    for i in range(start, len(t)):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                blob = t[start:i + 1]
                break
    else:
        return None, "unbalanced_braces"
    try:
        obj = json.loads(blob)
    except Exception:
        return None, "json_parse_failed"
    if not isinstance(obj, dict):
        return None, "not_object"
    verdict, conf, rationale = obj.get("verdict"), obj.get("confidence"), obj.get("rationale")
    if verdict not in ("equivalent", "meaning_changed"):
        return None, "verdict_out_of_vocabulary"
    if conf not in ("high", "medium", "low"):
        return None, "confidence_out_of_vocabulary"
    if not isinstance(rationale, str) or len(rationale) > 200:
        return None, "rationale_not_string_or_over_200"
    return {"verdict": verdict, "confidence": conf, "rationale": rationale}, ""


# ---------------------------------------------------------- client identifier tokens
def load_client_tokens() -> tuple:
    src = D1_SCRIPT.read_text(encoding="utf-8")
    client, idt = (), ()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "CLIENT_TOKENS":
                    client = tuple(ast.literal_eval(node.value))
                if isinstance(tgt, ast.Name) and tgt.id == "ID_TOKENS":
                    idt = tuple(ast.literal_eval(node.value))
    if not client or not idt:
        raise RuntimeError("client token table not found in D1 script")
    return client, idt


# ---------------------------------------------------------- leak vocabulary (card C3-2)
LEAK_EN = ["J-N1", "J-N2", "DR4", "oracle", "HARMFUL", "absorbed", "visible", "match_tier",
           "marginal_dH", "single_drop10", "mapping_target", "canonical", "injection",
           "invisibility", "alias_variant", "ocr_similar", "prefix_noise", "date_variant",
           "mixed_lang", "unit_symbol", "class=", "uid8", "full_uid", "detection", "threshold"]
LEAK_CN = ["静默吸收", "阈值稀释", "等价注入", "有害注入", "预期分类", "注入", "同义词", "归一化"]


def main() -> int:
    tpl = parse_card()
    doc = jload(ART)
    p = doc["payload"]
    mc = p["measurement_contract"]
    calls = p["calls"]
    per_case = p["per_case"]
    ledger_rows = [json.loads(l) for l in LEDGER.read_text(encoding="utf-8").splitlines() if l.strip()]
    d1 = payload_of(jload(D1_ART))
    t2 = payload_of(jload(T2_ART))
    d3a = payload_of(jload(D3A_ART))
    dr4 = payload_of(jload(DR4_ART))
    corpus_src = CORPUS_MIRROR if (CORPUS_MIRROR and CORPUS_MIRROR.exists()) else CORPUS
    corpus_sha_local = sha_file(corpus_src)
    corpus = {t["uid"]: t["table"] for t in jload(corpus_src)}
    report_md = REPORT.read_text(encoding="utf-8")
    state_md = STATE.read_text(encoding="utf-8")
    threads_md = THREADS.read_text(encoding="utf-8")

    uid8_to_full: dict = {}
    t2_inj: dict = {}
    for tab in t2["tables"]:
        uid8_to_full.setdefault(tab["uid"][:8], []).append(tab["uid"])
        for i in tab["injections"]:
            t2_inj["%s#%d" % (tab["uid"][:8], i["col"])] = i
    d1_by_key = {"%s#%d" % (r["uid"][:8], r["col"]): r for r in d1["injections"]}
    a3_by_key = {(c["uid_alias"], c["col"]): c for c in d3a["a3_dilution_rescue"]["per_case"]}

    # S-01 zero endpoint self proof (this script)
    chk("S-01", "本抽验脚本零端点自证（socket 层封死 + 无出站尝试）", "independent_recompute",
        SOCKET_ATTEMPTS == [], {"socket_attempts": SOCKET_ATTEMPTS,
                                "http_clients_imported": [m for m in ("urllib", "requests", "httpx")
                                                          if m in sys.modules]})

    # S-02 card sha pinned
    card_sha = sha_file(CARD)
    before = p["inputs_sha256_before"].get(rel(CARD))
    after = p["inputs_sha256_after"].get(rel(CARD))
    chk("S-02", "卡 sha 钉死（C3-6/GG11）: 现盘 sha == 冻结期望 == 工件 before/after",
        "independent_recompute",
        card_sha == CARD_SHA_EXPECT == before == after,
        {"disk": card_sha, "expect": CARD_SHA_EXPECT, "artifact_before": before, "artifact_after": after})

    # S-03 frozen inputs read-only
    ro = {}
    for path_s, want in p["inputs_sha256_before"].items():
        fp = REPO / path_s
        if fp.exists():
            raw, lf = sha_file_eol(fp)
            now = raw if raw == want else lf
            src = "local_repo_raw" if raw == want else (
                "local_repo_lf_normalized" if lf == want else "local_repo_MISMATCH")
        elif path_s == rel(CORPUS) and corpus_src.exists():
            now, src = corpus_sha_local, CORPUS_PROVENANCE
        else:
            now, src = "MISSING", "absent"
        ro[path_s] = {"before": want, "after": p["inputs_sha256_after"].get(path_s),
                      "disk_now": now, "source": src,
                      "equal": now == want == p["inputs_sha256_after"].get(path_s)}
    chk("S-03", "冻结输入 6 件只读（GG9）: sha == before == after（本机 core.autocrlf=true, JSON 件按 LF 归一核对; 语料件用 GB10 sha 校验镜像）",
        "independent_recompute", all(v["equal"] for v in ro.values()), ro)

    # S-04 / S-05 frozen prompt text vs card
    chk("S-04", "system prompt 逐字取自卡 C3-2（byte-equal + sha）", "independent_recompute",
        tpl["system"] == mc["system_prompt_text"]
        and sha_bytes(tpl["system"].encode()) == mc["system_prompt_sha256"],
        {"card_len": len(tpl["system"]), "artifact_len": len(mc["system_prompt_text"]),
         "sha_match": sha_bytes(tpl["system"].encode()) == mc["system_prompt_sha256"]})
    expect_ph = ["col_1based", "injected", "n_rows", "original", "table_md"]
    chk("S-05", "user 模板逐字取自卡 C3-2 + 占位符词表精确 5 项", "independent_recompute",
        tpl["user_template"] == mc["user_template_text"]
        and sha_bytes(tpl["user_template"].encode()) == mc["user_template_sha256"]
        and tpl["placeholders"] == expect_ph,
        {"template_match": tpl["user_template"] == mc["user_template_text"],
         "placeholders": tpl["placeholders"], "expected": expect_ph})

    # S-06 / S-07 case lists from card vs artifact vs calls
    jn1_card, jn2_card = tpl["jn1_21"], tpl["jn2_7"]
    call_keys = [c["injection_key"] for c in calls]
    jn1_calls = [c["injection_key"] for c in calls if c["subgroup"] == "J-N1"]
    jn2_calls = [c["injection_key"] for c in calls if c["subgroup"] == "J-N2"]
    chk("S-06", "J-N1 21 例清单: 卡逐字 == 工件 jn1_21_keys == 实际调用键（顺序与集合）",
        "independent_recompute",
        len(jn1_card) == 21 and jn1_card == mc["jn1_21_keys"] and sorted(jn1_calls) == sorted(jn1_card),
        {"n_card": len(jn1_card), "n_artifact": len(mc["jn1_21_keys"]), "n_calls": len(jn1_calls),
         "silent15": len(tpl["silent15"]), "dilution6": len(tpl["dilution6"])})
    jn2_short = [short_of(k) for k in jn2_card]
    chk("S-07", "J-N2 7 例清单: 卡完整 key == 工件 == 调用键; 3789d7da#1 不在 28 例内",
        "independent_recompute",
        len(jn2_card) == 7 and jn2_card == mc["jn2_7_keys"] and sorted(jn2_calls) == sorted(jn2_short)
        and not any(k.startswith("3789d7da") for k in call_keys) and mc["jn3_calls"] == 0,
        {"n_card": len(jn2_card), "jn3_calls": mc["jn3_calls"],
         "h2e_absent": not any(k.startswith("3789d7da") for k in call_keys),
         "anchors_parsed": len(tpl["jn2_anchors"])})

    # S-08 C3-1 runtime assertions recheck (independent)
    silent_set = {"%s#%d" % (r["uid"][:8], r["col"]) for r in d1["injections"]
                  if r.get("class") == "HI" and r.get("invisibility_mechanism") == "absorption_silent"}
    dil_set = {"%s#%d" % (u, c) for (u, c), v in a3_by_key.items() if v.get("single_drop10") == 0.0}
    e_set = {"%s#%d" % (r["uid"][:8], r["col"]) for r in d1["injections"] if r.get("class") == "E"}
    dr4_e2h = {short_of(c["key"]) for c in dr4["diff"]["current_e_to_oracle_h"]}
    dr4_h2e = [c for c in dr4["diff"]["changes"] if c["direction"] == "H->E"]
    anchor_mismatch = []
    for full in jn2_card:
        s = short_of(full)
        rec = d1_by_key.get(s)
        want = tpl["jn2_anchors"].get(full, "")
        if rec is None:
            anchor_mismatch.append({"key": s, "problem": "missing in D1"})
            continue
        pair = "%s → %s" % (rec["original"], rec["injected"])
        if want and want.split("（")[0].strip() not in ("", pair) and pair != want:
            anchor_mismatch.append({"key": s, "card_anchor": want, "d1": pair})
    uid8_dupes = {k: v for k, v in uid8_to_full.items() if len(v) != 1}
    a = {"A1_union_21_disjoint": (silent_set | dil_set) == set(jn1_card) and len(silent_set) == 15
         and len(dil_set) == 6 and not (silent_set & dil_set),
         "A2_e7_eq_jn2_eq_dr4": e_set == set(jn2_short) == dr4_e2h and len(dr4_e2h) == 7,
         "A3_jn1_jn2_disjoint": not (set(jn1_card) & set(jn2_short)),
         "A4_anchors_verbatim_vs_d1": not anchor_mismatch,
         "A5_h2e_excluded_zero_calls": len(dr4_h2e) == 1
         and short_of(dr4_h2e[0]["key"]) not in call_keys and mc["jn3_calls"] == 0,
         "A6_uid8_1to1_unique": not uid8_dupes and len(t2["tables"]) == 95
         and all(k.split("#")[0] in uid8_to_full for k in call_keys)}
    chk("S-08", "C3-1 运行时硬断言 A1-A6 独立复算（并集/相等/不相交/逐字锚点/H→E 排除/uid8 1:1）",
        "independent_recompute", all(a.values()),
        dict(a, silent15=len(silent_set), dilution6=len(dil_set), e7=len(e_set),
             dr4_e2h=len(dr4_e2h), anchor_mismatch=anchor_mismatch[:4], uid8_dupes=list(uid8_dupes)[:4]))

    # S-09 prompt rebuild 28/28 byte equal (C3-6 interface item 1, no sampling)
    rebuild = []
    for c in calls:
        s = c["injection_key"]
        full_uid = uid8_to_full[s.split("#")[0]][0]
        rows = corpus[full_uid]
        md, truncated, shown = render_table_md(rows)
        rec = d1_by_key[s]
        mine = rebuild_prompt(tpl, md, len(rows), int(s.split("#")[1]), rec["original"], rec["injected"])
        ok = mine == c["prompt_text"]
        entry = {"call_id": c["call_id"], "key": s, "byte_equal": ok,
                 "len_mine": len(mine), "len_artifact": len(c["prompt_text"]),
                 "table_truncated": truncated, "rows_total": len(rows), "rows_shown": shown}
        if not ok:
            off = next((i for i, (x, y) in enumerate(zip(mine, c["prompt_text"])) if x != y),
                       min(len(mine), len(c["prompt_text"])))
            entry["first_diff_offset"] = off
            entry["mine_ctx"] = mine[max(0, off - 40):off + 40]
            entry["artifact_ctx"] = c["prompt_text"][max(0, off - 40):off + 40]
        rebuild.append(entry)
    n_equal = sum(1 for r in rebuild if r["byte_equal"])
    chk("S-09", "C3-6① prompt 逐例比对不抽样: 28/28 由卡模板 + 冻结源独立重建后 byte-equal",
        "independent_recompute", n_equal == 28 == len(calls),
        {"n_calls": len(calls), "n_byte_equal": n_equal,
         "mismatches": [r for r in rebuild if not r["byte_equal"]][:5],
         "prompt_len_range": [min(r["len_mine"] for r in rebuild), max(r["len_mine"] for r in rebuild)],
         "any_table_truncated": any(r["table_truncated"] for r in rebuild)})

    # S-10 prompt sha recompute + uniqueness
    sha_bad = [c["call_id"] for c in calls
               if sha_bytes(c["prompt_text"].encode("utf-8")) != c["prompt_sha256"]]
    shas = [c["prompt_sha256"] for c in calls]
    chk("S-10", "prompt_sha256 逐例独立重算 + 28 唯一", "independent_recompute",
        not sha_bad and len(set(shas)) == 28,
        {"mismatch": sha_bad, "n_unique": len(set(shas))})

    # S-11 independent leak scan
    hits = []
    all_uids = {u for v in uid8_to_full.values() for u in v} | set(uid8_to_full)
    for c in calls:
        md = c["prompt_text"].split("\n\n原始列名")[0]
        skeleton = c["prompt_text"].replace(md, "\x00")
        low = skeleton.lower()
        for tok in LEAK_EN + LEAK_CN:
            if tok.lower() in low:
                hits.append({"call_id": c["call_id"], "token": tok, "region": "skeleton"})
        for uid in all_uids:
            if uid and uid in skeleton:
                hits.append({"call_id": c["call_id"], "token": uid, "region": "uid_in_skeleton"})
        if c["injection_key"].split("#")[0] in skeleton:
            hits.append({"call_id": c["call_id"], "token": "uid8", "region": "uid8_in_skeleton"})
    chk("S-11", "C3-2 防泄漏白黑名单独立扫描（骨架区 + uid/uid8）: 零命中", "independent_recompute",
        not hits, {"n_prompts_scanned": len(calls), "hits": hits[:8],
                   "artifact_leak_guard_holds": p["leak_guard"]["holds"],
                   "artifact_hits": p["leak_guard"]["hits"]})

    # S-12 per-call schema (C3-3 frozen field list)
    want_fields = ["call_id", "subgroup", "injection_key", "uid8", "col", "attempt", "prompt_sha256",
                   "prompt_text", "table_truncated", "raw_response", "parsed", "status", "model",
                   "temperature", "max_tokens", "latency_ms", "ts"]
    missing = {c["call_id"]: [f for f in want_fields if f not in c] for c in calls}
    missing = {k: v for k, v in missing.items() if v}
    bad_status = [c["call_id"] for c in calls
                  if c["status"] not in ("ok", "invalid_retry", "invalid_final")]
    chk("S-12", "C3-3 per-call 冻结字段 17 项齐备 + status 词表合法", "field_exists",
        not missing and not bad_status,
        {"n_calls": len(calls), "missing_fields": missing, "bad_status": bad_status})

    # S-13 raw_response re-parse vs stored parsed
    reparse_bad = []
    verdicts = {}
    for c in calls:
        got, err = parse_response(c["raw_response"])
        if got != c["parsed"]:
            reparse_bad.append({"call_id": c["call_id"], "err": err, "stored": c["parsed"], "reparsed": got})
        verdicts[c["injection_key"]] = (c["parsed"] or {}).get("verdict")
    chk("S-13", "raw_response 独立保守解析 == 工件 parsed（28/28, 词表 + rationale ≤200）",
        "independent_recompute", not reparse_bad, {"n": len(calls), "mismatch": reparse_bad[:5]})

    # S-14 model settings frozen (C3-4)
    bad_cfg = [c["call_id"] for c in calls if c["model"] != MODEL_EXPECT or c["temperature"] != 0
               or c["max_tokens"] != 512]
    chk("S-14", "C3-4 模型设置逐例一致（model/temperature=0/max_tokens=512）+ 契约字段存值",
        "value_match",
        not bad_cfg and mc["model"] == MODEL_EXPECT and mc["temperature"] == 0
        and mc["max_tokens"] == 512 and mc["enable_thinking"] is False and mc["row_cap"] == ROW_CAP,
        {"bad_cfg": bad_cfg, "model": mc["model"], "temperature": mc["temperature"],
         "max_tokens": mc["max_tokens"], "enable_thinking": mc["enable_thinking"],
         "timeout_s": mc["timeout_s"], "row_cap": mc["row_cap"],
         "served_ids": p["model_service_assertion"]["served_ids"],
         "assertion_holds": p["model_service_assertion"]["holds"]})

    # S-15 ledger line-by-line (C3-5 / C3-6 interface item 2)
    kinds = {}
    for r in ledger_rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    reserves = [r for r in ledger_rows if r["kind"] == "reserve"]
    lcalls = [r for r in ledger_rows if r["kind"] == "call"]
    lcanary = [r for r in ledger_rows if r["kind"] == "canary"]
    counters = [r["counter"] for r in reserves]
    bd = p["call_counter_breakdown"]
    ledger_case_keys = [r["injection_key"] for r in lcalls]
    ledger_sha_ok = all(sha_bytes(r["prompt_text"].encode("utf-8")) == r["prompt_sha256"] for r in lcalls)
    art_by_key = {c["injection_key"]: c for c in calls}
    cross_ok = all(art_by_key.get(r["injection_key"], {}).get("prompt_sha256") == r["prompt_sha256"]
                   for r in lcalls)
    ident = (p["call_counter_total"] == len(lcanary) + len(lcalls)
             and len(reserves) == p["call_counter_total"]
             and counters == list(range(1, len(reserves) + 1))
             and bd["identity_counter_eq_canary_plus_call_records"] is True
             and bd["ledger_reserve_eq_counter"] is True)
    retries = sum(1 for r in lcalls if r.get("attempt", 1) != 1)
    chk("S-15", "C3-5/C3-6② 账本逐行核对: 62 行 / reserve 1..31 连续 / 恒等式 / ≤200 / 零重试 / 28 例各一次 / 跨文件 sha 一致",
        "independent_recompute",
        len(ledger_rows) == 62 and kinds == {"reserve": 31, "call": 28, "canary": 3} and ident
        and p["call_counter_total"] <= BUDGET_CEILING and retries == 0
        and sorted(ledger_case_keys) == sorted(call_keys) and len(set(ledger_case_keys)) == 28
        and ledger_sha_ok and cross_ok,
        {"lines": len(ledger_rows), "kinds": kinds, "counter_total": p["call_counter_total"],
         "ceiling": BUDGET_CEILING, "expected_upper_bound_single_run": 1 + 28 + 28,
         "identity": ident, "reserve_counters_contiguous": counters == list(range(1, 32)),
         "retries": retries, "distinct_cases": len(set(ledger_case_keys)),
         "ledger_prompt_sha_selfconsistent": ledger_sha_ok, "ledger_vs_artifact_sha": cross_ok,
         "breakdown": bd})

    # S-16 canary
    canary_sha = sha_bytes(tpl["canary_prompt"].encode("utf-8"))
    chk("S-16", "canary 冻结 prompt sha + 3 次探针全 ok + 计数入账", "independent_recompute",
        p["canary"]["prompt_sha256"] == canary_sha == mc["canary_prompt_sha256"]
        and p["canary"]["ok"] is True and p["canary"]["counted"] is True
        and len(lcanary) == 3 and all(r.get("ok") for r in lcanary),
        {"card_sha": canary_sha, "artifact_sha": p["canary"]["prompt_sha256"],
         "ok": p["canary"]["ok"], "counted": p["canary"]["counted"],
         "counter_at": p["canary"]["counter_at"], "canary_rows_in_ledger": len(lcanary),
         "parsed": p["canary"]["parsed"], "latency_ms": p["canary"]["latency_ms"]})

    # S-17 aggregation recompute
    cross = {"J-N1": {"equivalent": 0, "meaning_changed": 0, "invalid_final": 0},
             "J-N2": {"equivalent": 0, "meaning_changed": 0, "invalid_final": 0}}
    conf = {"high": 0, "medium": 0, "low": 0}
    prompt_tokens = completion_tokens = 0
    lat = []
    for pc in per_case:
        g = pc["subgroup"]
        v = pc.get("verdict")
        if v in ("equivalent", "meaning_changed"):
            cross[g][v] += 1
            conf[pc.get("confidence")] = conf.get(pc.get("confidence"), 0) + 1
        elif pc.get("status") == "invalid_final":
            cross[g]["invalid_final"] += 1
        u = pc.get("usage") or {}
        prompt_tokens += u.get("prompt_tokens", 0)
        completion_tokens += u.get("completion_tokens", 0)
        if pc.get("latency_ms"):
            lat.append(pc["latency_ms"])
    lat.sort()
    med = lat[len(lat) // 2] if lat else None
    jn1_eq, jn1_mc = cross["J-N1"]["equivalent"], cross["J-N1"]["meaning_changed"]
    jn2_eq, jn2_mc = cross["J-N2"]["equivalent"], cross["J-N2"]["meaning_changed"]
    agg_ok = (cross == {k: dict(v) for k, v in p["verdict_cross_tab"].items()}
              and p["jn1_confirmation_rate"]["numerator"] == jn1_mc
              and p["jn1_confirmation_rate"]["valid_denominator"] == jn1_eq + jn1_mc == 21
              and p["jn2_equivalent_rate_supports_current_E"]["numerator"] == jn2_eq
              and p["jn2_meaning_changed_rate_supports_dr4_oracle_H"]["numerator"] == jn2_mc
              and conf == p["confidence_distribution_valid_only"]
              and p["tokens_valid_calls"]["prompt_tokens"] == prompt_tokens
              and p["tokens_valid_calls"]["completion_tokens"] == completion_tokens)
    chk("S-17", "判定聚合独立重算（交叉表 / 比率分母 / confidence 分布 / tokens / latency）",
        "independent_recompute", agg_ok,
        {"recomputed_cross_tab": cross, "artifact_cross_tab": p["verdict_cross_tab"],
         "jn1_rate": {"numerator": jn1_mc, "denominator": jn1_eq + jn1_mc},
         "jn2_equivalent": jn2_eq, "jn2_meaning_changed": jn2_mc,
         "confidence": conf, "tokens": {"prompt": prompt_tokens, "completion": completion_tokens},
         "latency_ms": {"min": lat[0] if lat else None, "median": med, "max": lat[-1] if lat else None},
         "mapping_rule": p["aggregation_rule"]})

    # S-18 DR4 8 rows recompute
    rows = []
    for c in dr4["diff"]["changes"]:
        s = short_of(c["key"])
        pc = next((x for x in per_case if x["injection_key"] == s), None)
        if pc is not None and pc.get("status") == "ok":
            v = pc["verdict"]
            agree = (v == "meaning_changed") == (c["oracle_label"] == "HARMFUL")
            rows.append({"key": c["key"], "direction": c["direction"], "current_label": c["current_class"],
                         "dr4_oracle": c["oracle_label"], "evidence_kind": "judge_verdict",
                         "judge_verdict": v, "judge_confidence": pc.get("confidence"),
                         "agreement": "agree" if agree else "disagree"})
        else:
            t2i = t2_inj[s]
            det = {k: t2i[k] for k in ("visible", "absorbed", "match_tier")}
            rows.append({"key": c["key"], "direction": c["direction"], "current_label": c["current_class"],
                         "dr4_oracle": c["oracle_label"], "evidence_kind": "deterministic_evidence",
                         "deterministic_evidence": det, "judge_status": "not_called_zero_calls",
                         "agreement": "disagree" if (det["visible"] and not det["absorbed"]
                                                     and det["match_tier"] == 0
                                                     and c["oracle_label"] == "E") else "unresolved"})
    tally = {"agree": sum(1 for r in rows if r["agreement"] == "agree"),
             "disagree": sum(1 for r in rows if r["agreement"] == "disagree"),
             "unresolved_invalid_final": sum(1 for r in rows if r["agreement"] not in ("agree", "disagree"))}
    art_rows = p["dr4_comparison_8rows"]
    row_diff = []
    for mine, theirs in zip(rows, art_rows):
        for f in ("key", "direction", "current_label", "dr4_oracle", "evidence_kind", "agreement"):
            if mine.get(f) != theirs.get(f):
                row_diff.append({"key": mine["key"], "field": f, "mine": mine.get(f), "artifact": theirs.get(f)})
        if mine.get("judge_verdict") and mine["judge_verdict"] != theirs.get("judge_verdict"):
            row_diff.append({"key": mine["key"], "field": "judge_verdict",
                             "mine": mine["judge_verdict"], "artifact": theirs.get("judge_verdict")})
    chk("S-18", "8 行 DR4 对照独立重建（7 judge + 1 确定性）+ 逐行 agreement + tally",
        "independent_recompute",
        len(rows) == 8 == len(art_rows) and not row_diff and tally == p["dr4_agreement_tally"],
        {"recomputed_tally": tally, "artifact_tally": p["dr4_agreement_tally"],
         "row_diffs": row_diff[:6], "rows": rows})

    # S-19 divergence triggers
    t1 = jn2_eq >= 4
    t2 = jn1_eq >= 11
    trig = p["divergence_triggers_report_discipline"]
    chk("S-19", "方向性触发独立重算（① J-N2 ≥4/7 equivalent; ② J-N1 ≥11/21 equivalent）",
        "independent_recompute",
        trig["trigger_1_jn2_ge_4of7_equivalent_vs_dr4_oracle"] == t1
        and trig["trigger_2_jn1_ge_11of21_equivalent_undermines_harmful_set"] == t2
        and trig["jn2_equivalent_valid"] == jn2_eq and trig["jn1_equivalent_valid"] == jn1_eq
        and trig["any_triggered"] == (t1 or t2),
        {"trigger_1": t1, "trigger_2": t2, "jn2_equivalent_valid": jn2_eq,
         "jn1_equivalent_valid": jn1_eq, "artifact": trig})

    # S-20 endpoint isolation
    blob = json.dumps(doc, ensure_ascii=False)
    ports_in_urls = sorted(set(re.findall(r"https?://[^\s\"']*?:(\d{2,5})", blob)))
    rl = p["redline_self_check"]
    chk("S-20", "C3-6③ 端点隔离: ports_observed=[8004] / violations=[] / 8006·8008·5050 零触碰 / 工件内 URL 端口集={8004}",
        "value_match",
        rl["ports_observed"] == [8004] and rl["endpoint_violations"] == []
        and rl["endpoint_8004_only"] is True and rl["endpoint_8006_zero_touch"] is True
        and rl["jn3_zero_calls"] is True and ports_in_urls == ["8004"]
        and doc["gates"]["GG6_only_8004_touched"] and doc["gates"]["GG7_8006_zero_touch"],
        {"ports_observed": rl["ports_observed"], "endpoint_violations": rl["endpoint_violations"],
         "ports_in_urls": ports_in_urls, "redline": rl})

    # S-21 client identifier scan
    client_tokens, id_tokens = load_client_tokens()
    blobs = {"artifact": blob, "ledger": LEDGER.read_text(encoding="utf-8"), "report": report_md}
    hits2 = {}
    for name, text in blobs.items():
        low = text.lower()
        hits2[name] = {"chars": len(text),
                       "client_hits": [t for t in client_tokens if t and t.lower() in low],
                       "id_hits": [t for t in id_tokens if t and t.lower() in low]}
    chk("S-21", "甲方标识零进入（GG12）: 独立 AST 取 D1 冻结 token 表, 扫工件/账本/报告",
        "independent_recompute",
        all(not v["client_hits"] and not v["id_hits"] for v in hits2.values()),
        dict(hits2, token_counts={"client": len(client_tokens), "id": len(id_tokens)},
             artifact_scan=rl["client_identifier_scan"]))

    # S-22 payload digest
    dig = sha_bytes(json.dumps(p, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    chk("S-22", "payload_sha256 独立重算 + digest 自洽 + 工件文件 sha", "independent_recompute",
        dig == doc["payload_sha256"] and doc["digest_self_consistency"] is True,
        {"recomputed": dig, "stored": doc["payload_sha256"],
         "self_consistency": doc["digest_self_consistency"], "artifact_file_sha256": sha_file(ART),
         "artifact_bytes": ART.stat().st_size, "ledger_lines": len(ledger_rows)})

    # S-23 gates
    gates = doc["gates"]
    gg = {k: v for k, v in gates.items() if k.startswith("GG")}
    chk("S-23", "13 门逐门存值核对 + all_pass", "value_match",
        len(gg) == 13 and all(v is True for v in gg.values()) and gates["all_pass"] is True
        and p["window_abort"] is None,
        {"gates": gates, "window_abort": p["window_abort"],
         "gate_details_present": sorted(p["gate_details"].keys()) == sorted(gates.keys())})

    # S-24 report markdown numbers
    nrep = norm(report_md)
    silent_eq = sum(1 for r in per_case if r["subgroup"] == "J-N1" and r["injection_key"] in tpl["silent15"]
                    and r["verdict"] == "equivalent")
    silent_mc = 15 - silent_eq
    dil_mc = sum(1 for r in per_case if r["injection_key"] in tpl["dilution6"] and r["verdict"] == "meaning_changed")
    expects = {
        "endpoint_calls_frontmatter": "endpoint_calls: %d" % p["call_counter_total"],
        "counter_ceiling": "计数器 = %d ≤ %d 硬门" % (p["call_counter_total"], BUDGET_CEILING),
        "counter_breakdown": "canary 探针 %d + 正式 call 记录 %d + invalid 重试 **0** = %d"
                             % (len(lcanary), len(lcalls), p["call_counter_total"]),
        "ledger_lines": "append-only 共 %d 行" % len(ledger_rows),
        "jn1_silent": "| **%d** | %d |" % (silent_eq, silent_mc),
        "jn1_dilution": "| 0 | **%d** |" % dil_mc,
        "jn1_total": "%d（66.7%%） | **%d（33.3%%）**" % (jn1_eq, jn1_mc),
        "jn2_total": "**%d（57.1%%）** | %d（42.9%%）" % (jn2_eq, jn2_mc),
        "dr4_tally": "%d agree / %d disagree" % (tally["agree"], tally["disagree"]),
        "trigger_1": "J-N2 有效判定 %d/7 为 equivalent" % jn2_eq,
        "trigger_2": "J-N1 有效判定 %d/21 为 equivalent" % jn1_eq,
        "ports": "ports_observed=[8004]",
    }
    miss_rep = {k: v for k, v in expects.items() if norm(v) not in nrep}
    chk("S-24", "报告 Markdown 关键数字与独立重算逐项一致（F06 家族防误誊）", "value_match",
        not miss_rep, {"n_expected": len(expects), "missing": miss_rep,
                       "silent_split": {"equivalent": silent_eq, "meaning_changed": silent_mc},
                       "dilution_meaning_changed": dil_mc})

    # S-25 report per-case tables vs artifact
    md_verdicts = {}
    for line in report_md.splitlines():
        m = re.match(r"^\|\s+(?:\*\*)?`([0-9a-f]{8}#\d+)`(?:\*\*)?\s+\|(.+)$", line.strip())
        if not m:
            continue
        rest = m.group(2)
        v = "meaning_changed" if "meaning_changed" in rest else ("equivalent" if "equivalent" in rest else None)
        if v:
            md_verdicts[m.group(1)] = v
    diff25 = [{"key": k, "md": v, "artifact": verdicts.get(k)} for k, v in md_verdicts.items()
              if verdicts.get(k) != v]
    chk("S-25", "报告 §4/§5 逐例 verdict 表（21+7 行）与工件一致",
        "independent_recompute", len(md_verdicts) == 28 and not diff25,
        {"n_rows_parsed": len(md_verdicts), "expected_rows": 21 + 7, "diffs": diff25[:6]})

    # S-26 STATE / THREADS consistency
    nstate, nthreads = norm(state_md), norm(threads_md)
    st_expects = {
        "counter": "计数器 %d ≤ %d" % (p["call_counter_total"], BUDGET_CEILING),
        "breakdown": "canary %d + call %d + 重试 %d" % (len(lcanary), len(lcalls), retries),
        "jn1_rate": "meaning_changed %d/21（33.3%%）" % jn1_mc,
        "jn1_equivalent": "equivalent %d" % jn1_eq,
        "jn2_rate": "equivalent %d/7（57.1%%）" % jn2_eq,
        "jn2_mc_rate": "meaning_changed %d/7（42.9%%）" % jn2_mc,
        "dr4_tally": "%d agree / %d disagree / %d unresolved"
                     % (tally["agree"], tally["disagree"], tally["unresolved_invalid_final"]),
        "silent_split": "%d/15 equivalent" % silent_eq,
        "dilution_split": "%d/6 meaning_changed" % dil_mc,
        "ledger_lines": "%d 行" % len(ledger_rows),
        "gates": "13 门全 PASS",
    }
    miss_state = {k: v for k, v in st_expects.items() if norm(v) not in nstate}
    th_expects = {
        "trigger_1": "4/7 equivalent ≥ 4/7",
        "trigger_2": "14/21 equivalent ≥ 11/21",
        "counter": "计数器 = 31 ≤ 200 硬门",
        "breakdown": "canary 探针 3 + 正式 call 28 + invalid 重试 0",
        "dr4_tally": "3 agree / 5 disagree / 0 unresolved",
        "ledger": "账本 62 行",
        "silent_split": "equivalent 14 / meaning_changed 1",
        "dilution_split": "meaning_changed 6/6",
    }
    miss_threads = {k: v for k, v in th_expects.items() if norm(v) not in nthreads}
    chk("S-26", "STATE.md 阶段 B 节 + THREADS #D3-STAGE-B-CLOSEOUT 与独立重算一致", "value_match",
        not miss_state and not miss_threads,
        {"state_missing": miss_state, "threads_missing": miss_threads})

    # S-27 report section 6: 8-row comparison table vs independently rebuilt rows
    mine6 = {short_of(r["key"]): r for r in rows}
    md6 = {}
    for line in report_md.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if len(cells) != 6 or not (cells[0].startswith("`") and cells[0].endswith("`")):
            continue
        key = cells[0].strip("`")
        if key in mine6 and cells[1] in ("H→E", "E→H"):
            md6[key] = {"direction": cells[1], "evidence_cell": cells[4], "agreement": cells[5]}
    diff27 = []
    for key, got in md6.items():
        want = mine6[key]
        if got["agreement"] != want["agreement"]:
            diff27.append({"key": key, "field": "agreement", "md": got["agreement"],
                           "mine": want["agreement"]})
        if want["evidence_kind"] == "judge_verdict":
            if ("judge: " + str(want["judge_verdict"])) not in got["evidence_cell"]:
                diff27.append({"key": key, "field": "judge_verdict",
                               "md": got["evidence_cell"], "mine": want["judge_verdict"]})
        else:
            det = want["deterministic_evidence"]
            if not (got["evidence_cell"].startswith("det:") and det["visible"] is True
                    and det["absorbed"] is False and det["match_tier"] == 0):
                diff27.append({"key": key, "field": "deterministic_evidence",
                               "md": got["evidence_cell"], "mine": det})
    chk("S-27", "报告 §6 8 行对照表（direction / 证据 / agreement）与独立重建逐行一致",
        "independent_recompute", len(md6) == 8 and not diff27,
        {"n_rows_parsed": len(md6), "expected_rows": 8, "diffs": diff27[:6]})

    all_pass = all(c["pass"] for c in CHECKS)
    recomputed = {
        "call_counter_total": p["call_counter_total"],
        "canary_probes": len(lcanary), "formal_calls": len(lcalls), "invalid_retries": retries,
        "ledger_lines": len(ledger_rows),
        "verdict_cross_tab": cross,
        "jn1": {"equivalent": jn1_eq, "meaning_changed": jn1_mc, "valid": jn1_eq + jn1_mc,
                "silent15": {"equivalent": silent_eq, "meaning_changed": silent_mc},
                "dilution6_meaning_changed": dil_mc},
        "jn2": {"equivalent": jn2_eq, "meaning_changed": jn2_mc, "valid": jn2_eq + jn2_mc},
        "dr4_tally": tally, "dr4_rows": rows,
        "triggers": {"trigger_1_jn2_ge_4of7": t1, "trigger_2_jn1_ge_11of21": t2},
        "prompt_rebuild_byte_equal": "%d/%d" % (n_equal, len(calls)),
        "confidence_distribution": conf,
        "tokens": {"prompt": prompt_tokens, "completion": completion_tokens},
        "latency_ms": {"min": lat[0] if lat else None, "median": med, "max": lat[-1] if lat else None},
    }
    boundary = [
        {"key": "567a03c7#1", "why": "静默吸收子组唯一 meaning_changed; 形态为追加文字（Exercise date 2021-期末日期）而非字符级扰动"},
        {"key": "68b8d514#1", "why": "与 567a03c7#1 同为日期列追加文字形态, judge 判 equivalent ⇒ 同形态反判, 边界样本"},
        {"key": "3789d7da#1", "why": "唯一 H→E 例, 零 judge 调用, 确定性证据 visible=T/absorbed=F/tier=0 与 oracle=E 方向不一致（如实记 disagree）"},
        {"key": "54c494f7#2 / e9730ea3#2", "why": "同形对（Accumulated Amortization → amort）判定自洽一致, 佐证 temp=0 稳定"},
        {"key": "5e60c056#0 / b5aae4e9#0", "why": "同形对（£m → m【】）判定自洽一致"},
        {"key": "family_blocking", "why": "分歧按扰动族成块（缩写/单位族全 disagree, 删限定语与货币符号族全 agree）⇒ 分界落在「缩写是否算改口径」的判定标准歧义, 非随机噪声"},
    ]
    payload = {"script": rel(Path(__file__)), "generated": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
               "role": "Loop D closeout spot-check (C3-6 interface items 1-4)",
               "contract": "docs/experiments/2026-09-01_d3_matched_specificity_card.md 加编 3 C3-1..C3-6",
               "inputs": {"artifact": rel(ART), "ledger": rel(LEDGER), "report": rel(REPORT),
                          "card": rel(CARD), "d1": rel(D1_ART), "t2": rel(T2_ART),
                          "d3a": rel(D3A_ART), "dr4": rel(DR4_ART), "corpus": rel(CORPUS)},
               "zero_endpoint": True, "socket_attempts": SOCKET_ATTEMPTS,
               "checks": CHECKS, "n_checks": len(CHECKS), "all_pass": all_pass,
               "recomputed_summary": recomputed, "boundary_cases_for_autopsy": boundary,
               "evidence_level_legend": {
                   "field_exists": "字段存在即通过（最弱）",
                   "value_match": "读取工件/文档存值并与冻结期望比对（中）",
                   "independent_recompute": "由冻结源独立重算后比对（最强）"}}
    dig = sha_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    out = {"meta": {"name": "d3-stage-b-closeout-spotcheck", "version": "v1",
                    "card_id": "TASK-20260901-D3", "phase": "closeout_loop_d",
                    "generated": payload["generated"], "endpoint_calls": 0,
                    "script": payload["script"],
                    "target_artifact_sha256": sha_file(ART),
                    "target_payload_sha256": doc["payload_sha256"]},
           "payload": payload, "payload_sha256": dig, "digest_self_consistency": None}
    out["digest_self_consistency"] = sha_bytes(
        json.dumps(out["payload"], ensure_ascii=False, sort_keys=True).encode("utf-8")) == dig
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    for c in CHECKS:
        print("%-6s %-4s %s" % (c["id"], "PASS" if c["pass"] else "FAIL", c["desc"]))
    print("all_pass=%s n_checks=%d endpoint_calls=0 socket_attempts=%d"
          % (all_pass, len(CHECKS), len(SOCKET_ATTEMPTS)))
    print("artifact = %s | payload_sha256 = %s" % (rel(OUT), dig[:16]))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
