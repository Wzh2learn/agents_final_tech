#!/usr/bin/env python3
"""K2 v1 判别力联跑 · 表注入臂 (v2)。

对 K3 漂移注入器 v0 的 95 张注入表（TAT-QA 公开底座, 全合成, 甲方零进入）
过 K2 v1 判别协议的表头层:

  1. 重建 original 表头（注入列换回原值, 与 sample 原件交叉核对）
  2. 每表以 original 表头构造自含 canonical schema（唯一标准字段集）
  3. 双表头过离线 matcher（scripts/m1_statement_parser.py 的 map_headers,
     纯规则零端点）:
       - 注入列可见性: 注入表头是否仍被吸收进原字段（吸收=matcher 对漂移盲区）
       - 非注入列局部性: 未被注入的字段映射必须零移动
       - 双跑零漂移: 注入臂跑两次结果必须一致（确定性）
  4. leaf drop = (H_orig - H_inj) * 10, 判据 >= 2.0（对齐 08-19 叶片量纲）
  5. 第三层小臂（可选, --no-qa 关闭）: <=12 表 :8004 表忠实度 QA, temp=0,
     运行时断言零 :8006

产出: logs/graph/eval/checkpoint_discrimination_tables_v2.json
      （批 20 续跑检查点: logs/graph/eval/_k2_tables_v2_checkpoint.json）

用法:
  python3 research/k2_table_discrimination_v2.py [--limit N] [--no-qa]
      [--qa-limit 12] [--batch-size 20] [--fresh]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import m1_statement_parser as mp  # noqa: E402  (test-suite import convention)

DRIFT_OUT = REPO / "data" / "research" / "drift_v0" / "output"
SAMPLE = REPO / "data" / "research" / "drift_v0" / "sample_injected_tables.json"
EVAL = REPO / "logs" / "graph" / "eval"
CKPT = EVAL / "_k2_tables_v2_checkpoint.json"
OUT = EVAL / "checkpoint_discrimination_tables_v2.json"

DROP_THRESHOLD = 2.0  # 08-19 v1 判据（叶片量纲 0-10）

# 第三层小臂端点: 只许 :8004（F-J2 结构隔离）, 禁 :8006
QA_ENDPOINT = os.environ.get("K2_QA_ENDPOINT", "http://127.0.0.1:8004/v1/chat/completions")

# 专利四型 crosswalk（卡片口径）
PATENT_CROSSWALK = {
    "别名型": ["alias_variant", "mixed_lang"],
    "列名型": ["ocr_similar", "prefix_noise"],
    "类型型": ["unit_suffix", "date_variant"],
    "结构型": [],  # v0 注入器无结构类缺陷 -> 缺口如实注记
}


def assert_qa_endpoint_safe() -> None:
    if "8006" in QA_ENDPOINT or ":8006" in QA_ENDPOINT:
        raise RuntimeError("QA endpoint must never point at :8006")
    if "127.0.0.1:8004" not in QA_ENDPOINT:
        raise RuntimeError(f"QA endpoint unexpected (want :8004): {QA_ENDPOINT}")


def load_inputs():
    tables = json.loads((DRIFT_OUT / "injected_tables.json").read_text(encoding="utf-8"))
    imap = json.loads((DRIFT_OUT / "injection_map.json").read_text(encoding="utf-8"))
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    by_uid = {t["uid"]: t["table"] for t in tables}
    entries_by_uid: dict[str, list[dict]] = {}
    for e in imap["mapping"]:
        entries_by_uid.setdefault(e["uid"], []).append(e)
    sample_by_uid = {s["uid"]: s for s in sample}
    return by_uid, entries_by_uid, sample_by_uid


def unique_canonical(orig_header: list[str]) -> list[str]:
    """去重后的非空 canonical 字段（按归一化文本去重, 保留首现序）。"""
    seen: set[str] = set()
    out: list[str] = []
    for h in orig_header:
        if not mp.normalize_header(h):
            continue
        key = mp.normalize_header(h)
        if key in seen:
            continue
        seen.add(key)
        out.append(str(h))
    return out


def run_table(uid: str, inj_rows: list, entries: list[dict], sample_rec: dict | None):
    """单表双臂: 返回 per_table 记录。"""
    inj_header = [str(c) if c is not None else "" for c in inj_rows[0]]
    orig_header = list(inj_header)
    for e in entries:
        orig_header[e["col"]] = e["original"]

    # 与 sample 原件交叉核对（重建正确性）
    crosscheck = "no_sample"
    if sample_rec is not None:
        sample_orig_row0 = [str(c) if c is not None else "" for c in sample_rec["original"][0]]
        crosscheck = "match" if sample_orig_row0 == orig_header else "MISMATCH"

    canonicals = unique_canonical(orig_header)
    n_canon = len(canonicals)
    fields = [mp.SchemaField(std, [std]) for std in canonicals]
    st = mp.SchemaTable(table_name=f"k2_{uid[:8]}", layout="grid",
                        header_region_keywords=[], fields=fields)

    mapping_orig, unmapped_orig = mp.map_headers(orig_header, st)
    mapping_inj, unmapped_inj = mp.map_headers(inj_header, st)
    mapping_inj_2, _ = mp.map_headers(inj_header, st)  # 双跑零漂移
    zero_drift = mapping_inj == mapping_inj_2

    h_orig = (len(mapping_orig) / n_canon) if n_canon else 1.0
    h_inj = (len(mapping_inj) / n_canon) if n_canon else 1.0
    drop10 = round((h_orig - h_inj) * 10.0, 4)
    discriminated = drop10 >= DROP_THRESHOLD

    targeted_canonicals: set[str] = set()
    injections = []
    for e in entries:
        o, x, col = e["original"], e["injected"], e["col"]
        # 该注入对应的 canonical 字段（按归一化文本定位）
        c = next((c for c in canonicals
                  if mp.normalize_header(c) == mp.normalize_header(o)), None)
        if c is not None:
            targeted_canonicals.add(c)
        best = mp._best_field_for_header(mp.normalize_header(x), fields)
        tier = best[0] if best else 0
        tier_std = best[2] if best else None
        mapped_to_in_inj = mapping_inj.get(c) if c else None
        absorbed = (c is not None and mapped_to_in_inj == x)
        injections.append({
            "col": col, "type": e["type"], "original": o, "injected": x,
            "canonical": c, "absorbed": absorbed,
            "match_tier": tier, "match_tier_target": tier_std,
            "visible": (not absorbed),
        })

    # 局部性: 未被注入的 canonical 字段, 双臂映射文本必须一致
    locality_moves = []
    for c in canonicals:
        if c in targeted_canonicals:
            continue
        if mapping_orig.get(c) != mapping_inj.get(c):
            locality_moves.append({"field": c, "orig": mapping_orig.get(c),
                                   "inj": mapping_inj.get(c)})
    locality_clean = not locality_moves

    return {
        "uid": uid,
        "n_cols": len(inj_header),
        "n_canonical": n_canon,
        "n_injections": len(entries),
        "types": sorted(set(e["type"] for e in entries)),
        "crosscheck": crosscheck,
        "h_orig": round(h_orig, 4), "h_inj": round(h_inj, 4),
        "drop10": drop10, "discriminated": discriminated,
        "zero_drift": zero_drift, "locality_clean": locality_clean,
        "locality_moves": locality_moves,
        "unmapped_orig": unmapped_orig, "unmapped_inj": unmapped_inj,
        "injections": injections,
    }


def select_qa_arm(entries_by_uid: dict, limit: int) -> list[dict]:
    """每类型取前 2 条注入（按 uid/col 确定性排序, 不同表优先）。"""
    flat = []
    for uid, es in entries_by_uid.items():
        for e in es:
            flat.append({"uid": uid, **e})
    sel: list[dict] = []
    seen_tables: set[str] = set()
    for typ in sorted(PATENT_CROSSWALK["别名型"] + PATENT_CROSSWALK["列名型"]
                      + PATENT_CROSSWALK["类型型"]):
        cand = sorted([f for f in flat if f["type"] == typ],
                      key=lambda f: (f["uid"], f["col"]))
        picked = 0
        for f in cand:  # 先取不同表
            if picked >= 2:
                break
            if f["uid"] in seen_tables:
                continue
            sel.append(f); seen_tables.add(f["uid"]); picked += 1
        for f in cand:  # 不足则允许同表
            if picked >= 2:
                break
            if f in sel:
                continue
            sel.append(f); picked += 1
    return sel[:limit]


def qa_call(table_rows: list, col: int) -> dict:
    """单条 :8004 表忠实度 QA（temp=0）。"""
    assert_qa_endpoint_safe()
    rows = table_rows[:4]  # 表头 + 至多 3 数据行
    md = "\n".join("| " + " | ".join(str(c) if c is not None else "" for c in r) + " |"
                   for r in rows)
    prompt = (
        "下面是表格（首行为表头）:\n" + md + "\n\n"
        f"问: 该表表头第 {col + 1} 列的列名是什么？只输出列名本身, 不要任何其他文字、"
        "不要纠正或改写表头。"
    )
    body = json.dumps({
        "model": "local",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0, "max_tokens": 128,
        # judge 同源约定（F-J2）: A3B 默认 thinking, 必须显式关闭, 否则 content 为空
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode("utf-8")
    req = urllib.request.Request(
        QA_ENDPOINT, data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    return {"answer": text.strip(), "latency_s": round(time.time() - t0, 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="只跑前 N 表（冒烟用）")
    ap.add_argument("--no-qa", action="store_true", help="跳过 :8004 第三层小臂")
    ap.add_argument("--qa-limit", type=int, default=12)
    ap.add_argument("--batch-size", type=int, default=20)
    ap.add_argument("--fresh", action="store_true", help="忽略续跑检查点")
    args = ap.parse_args()

    t0 = time.time()
    by_uid, entries_by_uid, sample_by_uid = load_inputs()
    uids = sorted(entries_by_uid.keys())
    if args.limit:
        uids = uids[:args.limit]

    done: dict[str, dict] = {}
    if CKPT.exists() and not args.fresh:
        try:
            done = json.loads(CKPT.read_text(encoding="utf-8")).get("tables", {})
            print(f"[resume] checkpoint: {len(done)} tables done", file=sys.stderr)
        except Exception:
            done = {}

    batch: list[str] = []
    for uid in uids:
        if uid in done:
            continue
        rec = run_table(uid, by_uid[uid], entries_by_uid[uid],
                        sample_by_uid.get(uid))
        done[uid] = rec
        batch.append(uid)
        if len(batch) >= args.batch_size:
            CKPT.write_text(json.dumps({"tables": done}, ensure_ascii=False),
                            encoding="utf-8")
            print(f"[ckpt] {len(done)}/{len(uids)} tables", file=sys.stderr)
            batch = []
    if batch:
        CKPT.write_text(json.dumps({"tables": done}, ensure_ascii=False),
                        encoding="utf-8")

    # 汇总
    tables_list = [done[u] for u in uids if u in done]
    n = len(tables_list)
    n_disc = sum(1 for t in tables_list if t["discriminated"])
    n_loc = sum(1 for t in tables_list if t["locality_clean"])
    n_zd = sum(1 for t in tables_list if t["zero_drift"])
    n_cross_mismatch = sum(1 for t in tables_list if t["crosscheck"] == "MISMATCH")

    by_type: dict[str, dict] = {}
    for t in tables_list:
        for inj in t["injections"]:
            e = by_type.setdefault(inj["type"], {
                "n_injections": 0, "n_visible": 0, "n_absorbed": 0,
                "tables": set(), "tables_discriminated": set(),
                "tiers": {}})
            e["n_injections"] += 1
            e["tables"].add(t["uid"])
            if t["discriminated"]:
                e["tables_discriminated"].add(t["uid"])
            if inj["visible"]:
                e["n_visible"] += 1
            else:
                e["n_absorbed"] += 1
            e["tiers"][inj["match_tier"]] = e["tiers"].get(inj["match_tier"], 0) + 1
    by_type_out = {}
    for typ, e in sorted(by_type.items()):
        by_type_out[typ] = {
            "n_injections": e["n_injections"],
            "n_tables": len(e["tables"]),
            "n_visible": e["n_visible"],
            "n_absorbed": e["n_absorbed"],
            "visibility_rate": round(e["n_visible"] / e["n_injections"], 4)
            if e["n_injections"] else None,
            "match_tiers": {str(k): v for k, v in sorted(e["tiers"].items())},
        }

    crosswalk = {}
    for patent_type, members in PATENT_CROSSWALK.items():
        if not members:
            crosswalk[patent_type] = {"types": [], "note": "v0 注入器无结构类缺陷注入, 缺口如实注记（后续版本补结构扰动: 列增删/行错位/合并单元格）"}
            continue
        n_inj = sum(by_type_out.get(m, {}).get("n_injections", 0) for m in members)
        n_vis = sum(by_type_out.get(m, {}).get("n_visible", 0) for m in members)
        crosswalk[patent_type] = {
            "types": members, "n_injections": n_inj, "n_visible": n_vis,
            "visibility_rate": round(n_vis / n_inj, 4) if n_inj else None,
        }

    payload = {
        "meta": {
            "name": "checkpoint-discrimination-tables",
            "version": "v2",
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "caliber": "K2 v1 表注入臂: 95 表 / 118 注入（K3 drift v0, TAT-QA 公开底座, 全合成）; "
                       "matcher=scripts/m1_statement_parser.py map_headers（纯规则零端点）; "
                       "drop=(H_orig-H_inj)*10 判据>=2 对齐 08-19 叶片量纲; 与 08-19 报告互补不混同"
                       "（08-19=检查点树 mutant 臂, 本臂=表头漂移臂）",
            "drop_threshold": DROP_THRESHOLD,
            "runtime_s": round(time.time() - t0, 2),
        },
        "properties": {
            "discrimination": {"tables_discriminated": n_disc, "n_tables": n,
                               "rate": round(n_disc / n, 4) if n else None},
            "locality": {"tables_clean": n_loc, "n_tables": n,
                         "violations": [t["uid"] for t in tables_list
                                        if not t["locality_clean"]]},
            "zero_drift": {"tables_stable": n_zd, "n_tables": n},
            "crosscheck_mismatch": n_cross_mismatch,
        },
        "by_type": by_type_out,
        "patent_crosswalk": crosswalk,
        "tables": tables_list,
    }

    # 第三层小臂
    if not args.no_qa:
        sel = select_qa_arm(entries_by_uid, args.qa_limit)
        qa_rows = []
        for f in sel:
            inj_rows = by_uid[f["uid"]]
            try:
                r = qa_call(inj_rows, f["col"])
                ans = r["answer"]
                faithful = ans == str(f["injected"])
                corrected = ans == str(f["original"])
                qa_rows.append({
                    "uid": f["uid"], "col": f["col"], "type": f["type"],
                    "injected": f["injected"], "original": f["original"],
                    "answer": ans, "faithful_to_injected": faithful,
                    "auto_corrected_to_original": corrected,
                    "latency_s": r["latency_s"],
                })
            except Exception as ex:  # 小臂失败不阻塞主臂
                qa_rows.append({"uid": f["uid"], "col": f["col"], "type": f["type"],
                                "error": str(ex)[:200]})
        payload["qa_arm"] = {
            "endpoint": QA_ENDPOINT, "n": len(qa_rows),
            "note": "忠实度: 模型照读注入表头=漂移存活到 LLM 层; 自动改写回原列名=LLM 层静默归一（盲区）",
            "rows": qa_rows,
        }

    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(json.dumps({
        "tables": n, "discriminated": n_disc, "locality_clean": n_loc,
        "zero_drift": n_zd, "crosscheck_mismatch": n_cross_mismatch,
        "out": str(OUT),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
