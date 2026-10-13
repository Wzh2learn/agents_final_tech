# -*- coding: utf-8 -*-
"""A3+A4: build the TAT-QA origin manifest and the candidate item list for WP-0.
Deterministic, stdlib only, no model calls. Reads the raw records, writes two JSON artefacts
plus a receipt. Origin = one raw record (unique table + unique paragraph context)."""
import json, re, hashlib, sys, pathlib

RAW = pathlib.Path('data/research/tatqa_raw_2026')
OUT = pathlib.Path('data/research/tatqa_wp0_2026'); OUT.mkdir(parents=True, exist_ok=True)
kinds = {"train": json.load(open(RAW/'tatqa_dataset_train.json')),
         "dev": json.load(open(RAW/'tatqa_dataset_dev.json'))}
YEAR = re.compile(r'(19|20)\d{2}')
UNIT = re.compile(r'(%|\$|¥|£|€|EUR|USD|RMB|CNY|million|thousand|billion)', re.I)
SCALE_OF = [('billion', 1e9), ('million', 1e6), ('thousand', 1e3), ('%', 1.0)]

def parse_num(v):
    s = str(v).strip().replace(',', '')
    neg = s.startswith('(') and s.endswith(')')
    s = s.strip('()')
    if not re.fullmatch(r'-?\d+(\.\d+)?', s): return None
    x = float(s)
    return -x if neg else x

def header_scale(h):
    for k, m in SCALE_OF:
        if re.search(k, h, re.I): return k
    if re.search(r'[$¥£€]', h): return 'currency'
    return None

origins, items = [], []
for split, recs in kinds.items():
    for r in recs:
        t = r['table']['table']; uid = r['table']['uid']
        if len(t) < 2: continue
        hdr = [str(c) for c in t[0]]
        per = [(i, h) for i, h in enumerate(hdr) if YEAR.search(h)]
        if len(per) < 2: continue
        unit_cols = [(i, h) for i, h in enumerate(hdr) if UNIT.search(h)]
        if not unit_cols: continue
        rows = []
        for ri, row in enumerate(t[1:], start=1):
            vals = [(i, parse_num(row[i]) if i < len(row) else None) for i, _ in per]
            got = [(i, v) for i, v in vals if v is not None]
            if len(got) >= 2: rows.append((ri, got))
        if not rows: continue
        origins.append({"origin_id": f"tatqa_{uid}", "split": split, "uid": uid,
                        "period_columns": [i for i, _ in per], "period_labels": [h for _, h in per],
                        "unit_markers": [h for _, h in unit_cols if header_scale(h)],
                        "usable_rows": [ri for ri, _ in rows]})
        if len(items) < 60:
            ri, got = rows[0]
            (i_late, v_late), (i_early, v_early) = got[0], got[-1]
            delta = round(v_late - v_early, 6)
            items.append({
                "item_id": f"wp0_{uid[:8]}_r{ri}", "origin_id": f"tatqa_{uid}", "split": split,
                "table": t, "row_index": ri,
                "period_late": {"col": i_late, "label": hdr[i_late]},
                "period_early": {"col": i_early, "label": hdr[i_early]},
                "source_unit": header_scale(hdr[i_late]) or header_scale(hdr[i_early]),
                "requested_quantity": "increase" if delta >= 0 else "decrease",
                "gold_delta_source_unit": delta,
                "gold_recompute_rule": "value(late) - value(early) on row_index, both read from the table cells",
            })

origin_manifest = {"schema": "wp0_tatqa_origin_manifest_v1", "source": "TAT-QA raw (CC BY 4.0)",
                   "origin_definition": "one raw record (unique table + unique paragraph context)",
                   "origin_count": len(origins), "origins": origins}
(OUT/'origin_manifest.json').write_text(json.dumps(origin_manifest, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")

cand = {"schema": "wp0_tatqa_candidate_items_v1", "status": "CANDIDATE_NOT_A_PILOT",
        "note": "Gold is recomputed from table cells by the stated rule; it is NOT an LLM output and NOT a dataset annotation.",
        "item_count": len(items), "items": items}
(OUT/'candidate_items_v1.json').write_text(json.dumps(cand, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")

receipt = {"origins": len(origins), "origins_with_ge2_usable_rows": sum(1 for o in origins if len(o['usable_rows'])>=2),
           "candidate_items": len(items),
           "distinct_origin_ids_in_items": len({i['origin_id'] for i in items}),
           "sha256_origin_manifest": hashlib.sha256((OUT/'origin_manifest.json').read_bytes()).hexdigest(),
           "sha256_candidate_items": hashlib.sha256((OUT/'candidate_items_v1.json').read_bytes()).hexdigest()}
(OUT/'GENERATION_RECEIPT.json').write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
print(json.dumps(receipt, indent=2))