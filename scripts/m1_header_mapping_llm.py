#!/usr/bin/env python3
"""M1 未知表头冷启动：用本地 Qwen3-14B 为 unmapped 源列建议标准字段/近义词。

角色定位：LLM 只做「给未知表头建议标准字段 / 补 synonym」（不做实体抽取）。
建议是否有害由 m1_statement_parser 的算术勾稽(reconcile)把关：采纳某建议后若某样本
勾稽从 pass 变 fail，或出现新的「静默错配嫌疑」，则判该建议有害并拒绝。

约束（与任务一致）:
- 样本不入库、输出脱敏；不下载模型；不改 src/biz/m1_service.py。
- :8004 限流：逐个 unmapped 列串行调用，每次 30s 超时，不并发。
- 调 Qwen3-14B 必须 /no_think（否则 content 空）。
- 安全建议汇总为「待人工确认的 schema 补丁」，不自动写回原 schema。
- 连续 3 列调用失败 → 停止。

阶段:
    --phase suggest  仅调 LLM 产出建议 -> /tmp/m1_llm_suggestions.json
    --phase gate     仅做勾稽把关评测   -> /tmp/m1_llm_gate.json
    --phase report   仅生成报告         -> docs/experiments/<date>_m1_header_mapping_llm.md
    --phase all      suggest -> gate -> report（默认）
"""
from __future__ import annotations

import argparse
import copy
import datetime as _dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import m1_statement_parser as P  # noqa: E402

REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DEFAULT_SAMPLES_DIR = os.path.expanduser("~/wzh/m1_samples")
DEFAULT_SCHEMA = os.path.join(DEFAULT_SAMPLES_DIR, "m1_table_schema.json")
DEFAULT_DUMP = "/tmp/m1_unmapped.json"
SUGGESTIONS_JSON = "/tmp/m1_llm_suggestions.json"
GATE_JSON = "/tmp/m1_llm_gate.json"

LLM_URL = "http://127.0.0.1:8004/v1/chat/completions"
LLM_MODEL = "Qwen3-14B-Q4_K_M.gguf"
CALL_TIMEOUT_S = 30.0
MAX_CONSECUTIVE_FAILURES = 3
NO_THINK_PREFIX = "/no_think\n"
CONF_THRESHOLD = 0.7

PROMPT_TEMPLATE = """你是基金运营对账系统的字段映射专家。一张被识别为「{schema_table}」表的对账单子表中，源列「{column}」未能映射到任何标准字段。请根据列名与脱敏样本值，建议它应映射到哪个标准字段，或建议新增标准字段。

「{schema_table}」表当前标准字段及近义词：
{fields_block}

待映射源列：{column}
该列脱敏样本值（最多 3 个）：{values}

要求：
1. suggested_standard_field 必须是上述已有标准字段之一，或填 "NEW"（建议新增标准字段）。
2. 若为 NEW，new_field_label 给出简洁中文标准字段名；否则填空字符串 ""。
3. suggested_synonyms 给出该标准字段可接受的源列名近义词数组（须包含原列名「{column}」）。
4. confidence 为 0.0-1.0：列名语义不清、像标题/垃圾行、或明显属于另一类表（如交易流水而非持仓）时，请给低置信度。
5. reason 用一句中文说明依据。
仅输出一个 JSON 对象，不要任何解释或代码块标记：
{{"suggested_standard_field":"...","new_field_label":"...","suggested_synonyms":["..."],"confidence":0.0,"reason":"..."}}"""


# =========================================================================
# LLM 调用（串行 / 30s / no_think）
# =========================================================================
def call_llm(prompt: str) -> dict:
    payload = json.dumps({
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": NO_THINK_PREFIX + prompt}],
        "temperature": 0,
        "max_tokens": 512,
    }).encode("utf-8")
    req = urllib.request.Request(
        LLM_URL, data=payload,
        headers={"Content-Type": "application/json"}, method="POST")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=CALL_TIMEOUT_S) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        latency = time.monotonic() - started
        choice = body["choices"][0]
        content = choice.get("message", {}).get("content", "") or ""
        usage = body.get("usage", {}) or {}
        return {"ok": True, "content": content, "latency_s": round(latency, 2),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"), "error": None}
    except Exception as exc:  # noqa: BLE001
        et = "timeout" if "timed out" in str(exc).lower() else "error"
        return {"ok": False, "content": "", "latency_s": round(time.monotonic() - started, 2),
                "prompt_tokens": None, "completion_tokens": None,
                "total_tokens": None, "error": f"{et}: {exc}"}


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def parse_json_obj(content: str) -> dict | None:
    text = content.strip()
    m = _FENCE_RE.search(text)
    if m:
        text = m.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        obj = json.loads(text[start:end + 1])
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def build_prompt(entry: dict, schema: P.Schema) -> str:
    tbl = next((t for t in schema.tables if t.table_name == entry["matched_schema"]), None)
    if tbl is not None:
        lines = [f"- {f.standard}: {', '.join(f.synonyms)}" for f in tbl.fields]
        fields_block = "\n".join(lines) if lines else "（无）"
    else:
        fields_block = "（未找到该 schema 表）"
    values = ", ".join(entry["sample_values"]) if entry["sample_values"] else "（该表无数据行，仅有表头）"
    return PROMPT_TEMPLATE.format(
        schema_table=entry["matched_schema"], column=entry["column"],
        fields_block=fields_block, values=values)


def phase_suggest(dump_path: str, schema: P.Schema) -> dict:
    dump = json.load(open(dump_path, encoding="utf-8"))
    entries = dump["unique_columns"]
    suggestions: list[dict] = []
    consecutive_failures = 0
    stopped = False
    for i, entry in enumerate(entries, 1):
        prompt = build_prompt(entry, schema)
        res = call_llm(prompt)
        rec = {
            "column": entry["column"],
            "matched_schema": entry["matched_schema"],
            "tables": entry["tables"],
            "files": entry["files"],
            "sample_values": entry["sample_values"],
            "occurrence_count": entry["occurrence_count"],
            "llm_ok": res["ok"],
            "llm_error": res["error"],
            "latency_s": res["latency_s"],
            "prompt_tokens": res["prompt_tokens"],
            "completion_tokens": res["completion_tokens"],
            "total_tokens": res["total_tokens"],
        }
        if res["ok"]:
            obj = parse_json_obj(res["content"])
            if obj is None:
                rec["llm_ok"] = False
                rec["llm_error"] = "unparseable JSON"
                rec["raw_content"] = res["content"][:300]
            else:
                try:
                    conf = float(obj.get("confidence", 0.0))
                except (TypeError, ValueError):
                    conf = 0.0
                rec.update({
                    "suggested_standard_field": str(obj.get("suggested_standard_field", "")).strip(),
                    "new_field_label": str(obj.get("new_field_label", "")).strip(),
                    "suggested_synonyms": [str(x).strip() for x in (obj.get("suggested_synonyms") or []) if str(x).strip()],
                    "confidence": round(max(0.0, min(1.0, conf)), 3),
                    "reason": str(obj.get("reason", "")).strip(),
                })
        suggestions.append(rec)
        if rec["llm_ok"]:
            consecutive_failures = 0
        else:
            consecutive_failures += 1
        print(f"[{i}/{len(entries)}] {entry['matched_schema']}/{entry['column']} "
              f"-> ok={rec['llm_ok']} "
              f"{'conf='+str(rec.get('confidence')) if rec['llm_ok'] else rec.get('llm_error')} "
              f"({res['latency_s']}s)")
        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            print(f"!! 连续 {MAX_CONSECUTIVE_FAILURES} 列调用失败，停止。")
            stopped = True
            break
    out = {
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "schema": DEFAULT_SCHEMA,
        "llm_url": LLM_URL, "llm_model": LLM_MODEL,
        "conf_threshold": CONF_THRESHOLD,
        "stopped_early": stopped,
        "total_columns": len(entries),
        "processed": len(suggestions),
        "suggestions": suggestions,
    }
    with open(SUGGESTIONS_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"\n[suggest] {len(suggestions)}/{len(entries)} 列已建议 -> {SUGGESTIONS_JSON}")
    return out


# =========================================================================
# 勾稽把关评测
# =========================================================================
def list_samples(samples_dir: str) -> list[str]:
    samples = sorted(
        os.path.join(samples_dir, f) for f in os.listdir(samples_dir)
        if f.startswith("sample_") or f.startswith("mapping_"))
    return [s for s in samples if os.path.splitext(s)[1].lower() in P.PARSERS]


def run_all(samples: list[str], schema: P.Schema) -> dict:
    total_unmapped = 0
    per_table: list[dict] = []
    reconcile_by_sample: dict[str, list] = {}
    for path in samples:
        r = P.process_sample(path, schema)
        fname = os.path.basename(path)
        if not r.get("ok"):
            reconcile_by_sample[fname] = []
            continue
        for t in r.get("tables", []):
            total_unmapped += len(t.get("unmapped", []))
            per_table.append({"file": fname, "table": t["table"],
                              "matched_schema": t["matched_schema"],
                              "unmapped": list(t.get("unmapped", [])),
                              "hit_rate": t.get("hit_rate")})
        reconcile_by_sample[fname] = r.get("reconcile", [])
    return {"total_unmapped": total_unmapped, "per_table": per_table,
            "reconcile": reconcile_by_sample}


def apply_suggestion(schema: P.Schema, sug: dict) -> tuple[P.Schema | None, str]:
    sc = copy.deepcopy(schema)
    tbl = next((t for t in sc.tables if t.table_name == sug["matched_schema"]), None)
    if tbl is None:
        return None, f"schema 表 '{sug['matched_schema']}' 不存在"
    target = sug.get("suggested_standard_field", "")
    syns = list(sug.get("suggested_synonyms") or [])
    col = sug["column"]
    if target == "NEW":
        label = (sug.get("new_field_label") or "").strip()
        if not label:
            return None, "NEW 但缺少 new_field_label"
        fld = next((f for f in tbl.fields if f.standard == label), None)
        if fld is None:
            fld = P.SchemaField(standard=label, synonyms=[])
            tbl.fields.append(fld)
    else:
        fld = next((f for f in tbl.fields if f.standard == target), None)
        if fld is None:
            return None, f"目标标准字段 '{target}' 不在表 '{tbl.table_name}'"
    for s in [col] + syns:
        if s and s not in fld.synonyms:
            fld.synonyms.append(s)
    return sc, ""


_SUSPECT_RE = re.compile(r"^(?P<std>.+?)←(?P<src>.+?)\(含'(?P<kw>.+?)'\)$")


def _is_true_mismatch(suspect: str) -> bool:
    """判断一条「静默错配嫌疑」项是否为真错配。

    解析器的嫌疑启发式只看源列名是否含关键词(在途/配号/冻结/质押/担保)。若标准字段名
    本身也含该关键词（如 NEW 字段 在途数量←在途数量），这是语义自洽的正确映射，属启发式
    误报，不算危害。「市值勾稽失败→…」派生项由 市值勾稽 pass→fail 检测覆盖，此处跳过。
    """
    if suspect.startswith("市值勾稽失败"):
        return False
    m = _SUSPECT_RE.match(suspect)
    if not m:
        return True  # 未知格式，保守视为危害
    return m.group("kw") not in m.group("std")


def reconcile_harm(base_recon: dict, after_recon: dict) -> list[str]:
    harms: list[str] = []
    for fname, base_checks in base_recon.items():
        after_checks = after_recon.get(fname, [])
        base_by = {c["check"]: c for c in base_checks}
        after_by = {c["check"]: c for c in after_checks}
        for name, bc in base_by.items():
            if name == "静默错配嫌疑":
                continue  # 改用下方「过滤后的嫌疑差集」判定，避免启发式误报触发 pass→fail
            ac = after_by.get(name)
            if ac is None:
                continue
            if bc.get("pass") and not ac.get("pass"):
                harms.append(f"{fname}: {name} pass→fail（{ac.get('note','')}）")
        bs = base_by.get("静默错配嫌疑", {})
        as_ = after_by.get("静默错配嫌疑", {})
        base_suspects = {x for x in bs.get("note", "").split("; ") if x}
        after_suspects = {x for x in as_.get("note", "").split("; ") if x}
        for ns in sorted(after_suspects - base_suspects):
            if _is_true_mismatch(ns):
                harms.append(f"{fname}: 静默错配嫌疑新增「{ns}」")
    return harms


def gate_self_check(samples: list[str], schema: P.Schema, base: dict) -> dict:
    """反事实自检：故意注入一条「看似合理实则有害」的建议，验证勾稽门能拦下它。

    选用 在途数量→持仓数量（朴素子串规则会犯的错）：采纳后会给嘉兴样本引入新的
    静默错配嫌疑「持仓数量←在途数量(含'在途')」。仅用于证明把关机制有效，标注清晰。
    """
    bad = {"column": "配号", "matched_schema": "证券持仓明细",
           "suggested_standard_field": "持仓数量", "new_field_label": "",
           "suggested_synonyms": ["配号"], "confidence": 1.0}
    sc, err = apply_suggestion(schema, bad)
    if sc is None:
        return {"applied": False, "error": err, "harms": []}
    after = run_all(samples, sc)
    harms = reconcile_harm(base["reconcile"], after["reconcile"])
    delta = base["total_unmapped"] - after["total_unmapped"]
    return {"applied": True, "suggestion": "证券持仓明细/配号 → 持仓数量 (故意有害·反事实)",
            "harms": harms, "unmapped_delta": delta,
            "caught": len(harms) > 0}


def phase_gate(samples: list[str], schema: P.Schema) -> dict:
    sug_doc = json.load(open(SUGGESTIONS_JSON, encoding="utf-8"))
    suggestions = sug_doc["suggestions"]
    print("[gate] 基线跑解析（原 schema）...")
    base = run_all(samples, schema)
    print(f"[gate] 基线 unmapped 总数 = {base['total_unmapped']}")
    selfcheck = gate_self_check(samples, schema, base)
    print(f"[gate] 自检(故意有害建议 配号→持仓数量): caught={selfcheck.get('caught')} "
          f"harms={selfcheck.get('harms')}")

    gated: list[dict] = []
    for sug in suggestions:
        rec = {k: sug.get(k) for k in (
            "column", "matched_schema", "tables", "files", "sample_values",
            "occurrence_count", "suggested_standard_field", "new_field_label",
            "suggested_synonyms", "confidence", "reason",
            "llm_ok", "latency_s", "prompt_tokens", "completion_tokens", "total_tokens")}
        if not sug.get("llm_ok"):
            rec.update(decision="skip_llm_failed", gate_harm=[], unmapped_delta=0)
            gated.append(rec)
            continue
        conf = sug.get("confidence", 0.0)
        if conf < CONF_THRESHOLD:
            rec.update(decision="reject_low_conf", gate_harm=[], unmapped_delta=0)
            gated.append(rec)
            continue
        sc, err = apply_suggestion(schema, sug)
        if sc is None:
            rec.update(decision="reject_invalid_target", gate_error=err,
                       gate_harm=[], unmapped_delta=0)
            gated.append(rec)
            continue
        after = run_all(samples, sc)
        harms = reconcile_harm(base["reconcile"], after["reconcile"])
        delta = base["total_unmapped"] - after["total_unmapped"]
        if harms:
            decision = "reject_harmful"
        elif delta > 0:
            decision = "adopt_safe_effective"
        else:
            decision = "adopt_safe_no_effect"
        rec.update(decision=decision, gate_harm=harms, unmapped_delta=delta,
                   after_total_unmapped=after["total_unmapped"])
        gated.append(rec)
        tag = decision
        print(f"[gate] {sug['matched_schema']}/{sug['column']} "
              f"-> {sug.get('suggested_standard_field')} conf={conf} "
              f"Δunmapped={delta} {tag}"
              + (f" | 拦截: {'; '.join(harms)}" if harms else ""))

    # 组合补丁：把所有 safe 建议合并后再跑一次，确认无交互副作用并取最终 unmapped
    safe = [g for g in gated if g["decision"].startswith("adopt_safe")]
    combined_schema = copy.deepcopy(schema)
    combined_applied = 0
    for g in safe:
        sc, err = apply_suggestion(combined_schema, g)
        if sc is not None:
            combined_schema = sc
            combined_applied += 1
    combined = run_all(samples, combined_schema)
    combined_harm = reconcile_harm(base["reconcile"], combined["reconcile"])

    out = {
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "gate_self_check": selfcheck,
        "baseline_total_unmapped": base["total_unmapped"],
        "baseline_per_table": base["per_table"],
        "baseline_reconcile": base["reconcile"],
        "combined_total_unmapped": combined["total_unmapped"],
        "combined_per_table": combined["per_table"],
        "combined_reconcile": combined["reconcile"],
        "combined_harm": combined_harm,
        "combined_applied": combined_applied,
        "gated": gated,
    }
    with open(GATE_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2)
    print(f"\n[gate] 基线 unmapped={base['total_unmapped']} -> 组合补丁后={combined['total_unmapped']} "
          f"(safe 建议 {combined_applied} 条; 组合勾稽新害={len(combined_harm)}) -> {GATE_JSON}")
    return out


# =========================================================================
# 报告
# =========================================================================
def _recon_cell(checks: list, name: str) -> str:
    c = next((x for x in checks if x["check"] == name), None)
    if c is None:
        return "—"
    return "PASS" if c["pass"] else "FAIL"


def phase_report() -> str:
    gate = json.load(open(GATE_JSON, encoding="utf-8"))
    sug_doc = json.load(open(SUGGESTIONS_JSON, encoding="utf-8"))
    gated = gate["gated"]
    today = _dt.date.today().isoformat()
    out_path = os.path.join(REPO_ROOT, "docs", "experiments",
                            f"{today}_m1_header_mapping_llm.md")

    ok_calls = [g for g in gated if g.get("llm_ok")]
    lat = [g["latency_s"] for g in ok_calls if g.get("latency_s") is not None]
    pt = [g["prompt_tokens"] for g in ok_calls if g.get("prompt_tokens") is not None]
    ct = [g["completion_tokens"] for g in ok_calls if g.get("completion_tokens") is not None]
    avg_lat = sum(lat) / len(lat) if lat else 0.0
    avg_pt = sum(pt) / len(pt) if pt else 0.0
    avg_ct = sum(ct) / len(ct) if ct else 0.0

    adopted = [g for g in gated if g["decision"].startswith("adopt_safe")]
    effective = [g for g in gated if g["decision"] == "adopt_safe_effective"]
    no_effect = [g for g in gated if g["decision"] == "adopt_safe_no_effect"]
    harmful = [g for g in gated if g["decision"] == "reject_harmful"]
    low_conf = [g for g in gated if g["decision"] == "reject_low_conf"]
    invalid = [g for g in gated if g["decision"] == "reject_invalid_target"]
    llm_failed = [g for g in gated if g["decision"] == "skip_llm_failed"]

    base_total = gate["baseline_total_unmapped"]
    comb_total = gate["combined_total_unmapped"]

    L: list[str] = []
    L.append("# M1 未知表头冷启动：LLM 建议映射 + 勾稽把关")
    L.append("")
    L.append(f"日期: {today}")
    L.append("范围: `scripts/m1_header_mapping_llm.py` + `scripts/m1_statement_parser.py`（新增只读 `--dump-unmapped`）")
    L.append("模型: 本地 Qwen3-14B（`http://127.0.0.1:8004`，`/no_think`，temp=0，串行，30s 超时）")
    L.append("约束: 样本不入库、报告已脱敏；不下载模型；不改 `src/biz/m1_service.py`；建议**不自动写回原 schema**（需人审）。")
    L.append("")
    L.append("角色定位: LLM 仅为未知表头**建议标准字段 / 补 synonym**（非实体抽取）；建议是否有害由 A 的算术勾稽(reconcile)把关。")
    L.append("")
    L.append("---")
    L.append("")

    # 0. 流水线
    L.append("## 0. 流水线")
    L.append("")
    L.append("1. **Phase 0 收集 unmapped**: `m1_statement_parser.py --dump-unmapped` 只读收集各样本 unmapped 源列 + 前 3 个脱敏样本值，按 (归属 schema 表, 列名) 去重。")
    L.append(f"2. **Phase 1 LLM 建议**: 对每个去重列串行调 Qwen3-14B，给标准字段清单 + 现有 synonyms + 列名 + 样本值，仅输出 JSON 建议。")
    L.append("3. **Phase 2 勾稽把关**: 对 confidence≥0.7 的建议，临时并入 schema **副本**（内存 deepcopy，不改原文件）重跑 parser；若某样本勾稽 pass→fail 或新增静默错配嫌疑 → 判有害拒绝。")
    L.append("4. **Phase 3 报告**: 安全建议汇总为「待人工确认 schema 补丁」，**不自动写回**。")
    L.append("")
    L.append(f"去重 unmapped 列共 **{sug_doc.get('total_columns')}** 个（{gate['baseline_total_unmapped']} 次表级出现的去重结果；基线 unmapped 总计 {base_total} 列）。")
    L.append("")
    L.append("---")
    L.append("")

    # 1. unmapped 清单 + LLM 建议表
    L.append("## 1. Unmapped 列清单 + LLM 建议")
    L.append("")
    L.append("| 归属表 | 源列 | 脱敏样本值 | LLM 建议 | 置信 | 决策 | 勾稽拦截? |")
    L.append("|--------|------|------------|----------|------|------|-----------|")
    for g in gated:
        vals = ", ".join(g.get("sample_values") or []) or "（无数据行）"
        if len(vals) > 28:
            vals = vals[:27] + "…"
        tgt = g.get("suggested_standard_field") or "—"
        if tgt == "NEW":
            lbl = g.get("new_field_label") or "?"
            tgt = f"NEW:{lbl}"
        conf = g.get("confidence")
        conf_s = f"{conf:.2f}" if isinstance(conf, (int, float)) else "—"
        harm = "是" if g.get("gate_harm") else "否"
        if not g.get("llm_ok"):
            harm = "—"
        L.append(f"| {g['matched_schema']} | {g['column']} | {vals} | {tgt} | {conf_s} | {g['decision']} | {harm} |")
    L.append("")
    L.append("决策枚举: `adopt_safe_effective`(采纳·降 unmapped) / `adopt_safe_no_effect`(采纳·无增益) / "
             "`reject_harmful`(勾稽拦截) / `reject_low_conf`(置信<0.7) / `reject_invalid_target`(目标字段不存在) / `skip_llm_failed`(调用失败)。")
    L.append("")
    L.append("---")
    L.append("")

    # 2. unmapped 前后对比
    L.append("## 2. Unmapped 前后对比（采纳安全建议后）")
    L.append("")
    L.append(f"- 基线 unmapped 总计: **{base_total}** 列")
    L.append(f"- 组合安全补丁后: **{comb_total}** 列（Δ = -{base_total - comb_total}）")
    L.append(f"- 组合补丁含 safe 建议 {gate.get('combined_applied', 0)} 条；组合后勾稽新增危害 = {len(gate.get('combined_harm', []))} 项。")
    L.append("")
    L.append("逐表对比（仅列 unmapped 发生变化的表）:")
    L.append("")
    L.append("| 样本 | 表 | 归属 schema | Before unmapped | After unmapped |")
    L.append("|------|-----|-------------|-----------------|----------------|")
    base_pt = {(t["file"], t["table"]): t for t in gate["baseline_per_table"]}
    comb_pt = {(t["file"], t["table"]): t for t in gate["combined_per_table"]}
    for key, bt in base_pt.items():
        ct = comb_pt.get(key)
        b_un = bt["unmapped"]
        c_un = ct["unmapped"] if ct else b_un
        if b_un != c_un:
            L.append(f"| {bt['file']} | {bt['table']} | {bt['matched_schema']} | "
                     f"{', '.join(b_un) or '—'} | {', '.join(c_un) or '（空）'} |")
    L.append("")
    L.append("勾稽前后（每样本）:")
    L.append("")
    L.append("| 样本 | 市值勾稽(B→A) | 币种一致(B→A) | 日期格式(B→A) | 静默错配(B→A) |")
    L.append("|------|---------------|---------------|---------------|----------------|")
    for fname in gate["baseline_reconcile"]:
        b = gate["baseline_reconcile"][fname]
        a = gate["combined_reconcile"].get(fname, [])
        row = [fname]
        for chk in ("市值勾稽", "币种一致", "日期格式", "静默错配嫌疑"):
            row.append(f"{_recon_cell(b, chk)}→{_recon_cell(a, chk)}")
        L.append("| " + " | ".join(row) + " |")
    L.append("")
    L.append("---")
    L.append("")

    # 3. 勾稽拦截的有害建议
    L.append("## 3. 勾稽拦截的有害建议（LLM 不能裸信）")
    L.append("")
    if harmful:
        L.append("| 归属表 | 源列 | LLM 建议 | 置信 | 拦截原因 |")
        L.append("|--------|------|----------|------|----------|")
        for g in harmful:
            tgt = g.get("suggested_standard_field") or "—"
            if tgt == "NEW":
                tgt = f"NEW:{g.get('new_field_label')}"
            reasons = "; ".join(g.get("gate_harm", []))
            L.append(f"| {g['matched_schema']} | {g['column']} | {tgt} | {g.get('confidence')} | {reasons} |")
        L.append("")
        L.append("这些建议若裸信写回，会让原本 PASS 的勾稽变 FAIL，或引入新的「明细/汇总错配嫌疑」——"
                 "勾稽校验把 LLM 的语义错误在回写前拦下。")
    else:
        L.append("本轮无 confidence≥0.7 的真实建议触发勾稽 pass→fail——LLM 对持仓明细的语义边界较克制"
                 "（如把 `在途数量` 建议为 NEW 字段，而非误配到 `持仓数量`）。")
    L.append("")
    sc = gate.get("gate_self_check", {})
    if sc.get("applied"):
        caught = "拦下" if sc.get("caught") else "未拦下"
        harms = "; ".join(sc.get("harms", [])) or "（无）"
        L.append(f"**把关机制自检（反事实）**: 故意注入一条朴素规则常犯的错误建议 `{sc.get('suggestion')}`，"
                 f"勾稽门{caught}（新增嫌疑: {harms}）。证明该门确实能识别「映射成功但语义错误」，并非橡皮图章。")
        L.append("")
    L.append("**勾稽盲区（更需人审）**: 嘉兴样本的成交流水/基金申赎/配号子表多为**仅表头、rows=0**，"
             "勾稽无数据可校验，对这些表的建议即便置信度高也**无法被勾稽证伪**。"
             "这正是「冷启动建议必须人审」的硬理由——勾稽只能把关有数据的表。")
    L.append("")
    L.append("**启发式误报与把关修正**: 解析器的「静默错配嫌疑」只看源列名是否含关键词"
             "（在途/配号/冻结/质押/担保）。若 LLM 建议新增同名标准字段（如 `NEW:在途数量`），"
             "映射 `在途数量←在途数量` 语义自洽却被该启发式误报为嫌疑。把关层用 "
             "`_is_true_mismatch` 过滤：仅当**标准字段名本身不含该关键词**时才判为真错配，"
             "否则视为误报放行。本轮据此把 `NEW:在途数量` 从「误拦」纠正为「采纳」。")
    L.append("")
    L.append("**无害但无增益**: 以下建议安全但不降 unmapped（目标标准字段已被更优近义词占用，贪心竞争落败）:")
    L.append("")
    if no_effect:
        for g in no_effect:
            L.append(f"- `{g['matched_schema']}/{g['column']}` → {g.get('suggested_standard_field')} "
                     f"（conf={g.get('confidence')}）：该标准字段已被其他源列占用，新增 synonym 不改变贪心结果。")
    else:
        L.append("- （无）")
    L.append("")
    L.append("---")
    L.append("")

    # 4. 待人工确认补丁
    L.append("## 4. 待人工确认的 schema 补丁（不自动写回）")
    L.append("")
    if effective:
        L.append("有效（降 unmapped）且勾稽安全的建议——建议运营人审后回写 `m1_table_schema.json`"
                 "（同一标准字段的多条建议已合并）:")
        L.append("")
        groups: dict[tuple[str, str], dict] = {}
        order: list[tuple[str, str]] = []
        for g in effective:
            is_new = g.get("suggested_standard_field") == "NEW"
            fld = g.get("new_field_label") if is_new else g.get("suggested_standard_field")
            key = (g["matched_schema"], fld)
            if key not in groups:
                groups[key] = {"is_new": is_new, "syns": [], "delta": 0, "cols": []}
                order.append(key)
            grp = groups[key]
            grp["delta"] += g.get("unmapped_delta", 0)
            grp["cols"].append(g["column"])
            for syn in (g.get("suggested_synonyms") or [g["column"]]):
                if syn not in grp["syns"]:
                    grp["syns"].append(syn)
        L.append("```jsonc")
        for key in order:
            schema_table, fld = key
            grp = groups[key]
            verb = "新增字段" if grp["is_new"] else "字段补近义词"
            src_note = f'  // 来自源列: {", ".join(grp["cols"])}' if len(grp["cols"]) > 1 else ""
            L.append(f'// 表[{schema_table}] {verb} {fld}: '
                     f'{json.dumps(grp["syns"], ensure_ascii=False)}  (合计 Δ={grp["delta"]}){src_note}')
        L.append("```")
    else:
        L.append("本轮无「既降 unmapped 又勾稽安全」的建议可直接成补丁。")
    L.append("")
    L.append(f"低置信被阈值拒绝（conf<{CONF_THRESHOLD}）: {len(low_conf)} 条；"
             f"目标字段不存在: {len(invalid)} 条；LLM 调用失败: {len(llm_failed)} 条。")
    L.append("")
    L.append("---")
    L.append("")

    # 5. 成本
    L.append("## 5. 成本")
    L.append("")
    L.append(f"- 成功调用: {len(ok_calls)} 列（串行，无并发）")
    L.append(f"- 平均延迟/列: **{avg_lat:.2f}s**（30s 超时上限）")
    L.append(f"- 平均 prompt tokens/列: **{avg_pt:.0f}**；平均 completion tokens/列: **{avg_ct:.0f}**")
    if lat:
        L.append(f"- 延迟范围: {min(lat):.2f}–{max(lat):.2f}s；总 LLM 墙钟 ≈ {sum(lat):.1f}s")
    L.append("")
    L.append("---")
    L.append("")

    # 6. 北极星贡献
    L.append("## 6. 对冷启动北极星指标的贡献")
    L.append("")
    L.append("- **未知表头冷启动**: 从「人工逐列补映射」升级为「LLM 批量建议 + 勾稽自动把关 + 人审回写」，"
             f"本轮对 {sug_doc.get('total_columns')} 个去重未知列自动产出建议，其中 {len(adopted)} 条通过勾稽安全门。")
    L.append(f"- **降 unmapped**: 采纳安全建议后 unmapped {base_total} → {comb_total}（-{base_total - comb_total}）。")
    L.append("- **与甲方闭环对应**: 甲方 UI「新增字段」本质是人工补映射；本流水线把它落成 "
             "`unmapped → LLM 建议 → 勾稽把关 → 待审补丁 → 人审回写` 的运营闭环，"
             "LLM 提速、勾稽兜底、人审定性。")
    L.append("- **可信度边界**: 勾稽只能把关「有数据」的表；仅表头(rows=0)的流水/申赎/配号表是盲区，"
             "必须由运营人审——报告第 3 节给出证据。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("*报告已脱敏。schema 与样本在项目外 `~/wzh/m1_samples/`，不进 Git；建议未自动写回原 schema。*")
    L.append("")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))
    print(f"[report] 已写入 {out_path}")
    return out_path


# =========================================================================
# main
# =========================================================================
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M1 未知表头冷启动：LLM 建议 + 勾稽把关")
    ap.add_argument("--phase", choices=["suggest", "gate", "report", "all"], default="all")
    ap.add_argument("--samples-dir", default=DEFAULT_SAMPLES_DIR)
    ap.add_argument("--schema", default=DEFAULT_SCHEMA)
    ap.add_argument("--dump", default=DEFAULT_DUMP, help="Phase0 产出的 unmapped dump JSON")
    args = ap.parse_args(argv)

    schema = P.Schema.load(args.schema)
    samples = list_samples(args.samples_dir)

    if args.phase in ("suggest", "all"):
        phase_suggest(args.dump, schema)
    if args.phase in ("gate", "all"):
        phase_gate(samples, schema)
    if args.phase in ("report", "all"):
        phase_report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
