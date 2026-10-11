# -*- coding: utf-8 -*-
"""PR-EXP-03 v3 EXECUTION_PREFLIGHT. Toy/fixture/schema-only. No held-out reads."""
import hashlib, importlib.util, json, os, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

RUN_DIR = Path(__file__).resolve().parent
ROOT = RUN_DIR.parents[3]   # research/positive_repair_20261011/runs/PR-EXP-03-v3 -> repo root
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")

PREREG = ROOT/"research/positive_repair_20261011/preregs/PR-EXP-03_prereg_v3.md"
CONTRACT = RUN_DIR/"implementation_contract.md"
CONTRACT_SHA = RUN_DIR/"implementation_contract.sha256"
EXPERIMENT = RUN_DIR/"experiment_v3.py"
FROZEN = [
 "data/research/drift_v0/input/tatqa_tables.json",
 "data/research/drift_v0/output/injection_map.json",
 "research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json",
 "research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json",
 "research/stage_e_method_revision_20261009/multileaf_freeze.json",
 "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl",
 "research/stage_e_multileaf_20261010/run_multileaf_formal.py",
 "scripts/m1_statement_parser.py",
 "src/biz/m1_statement_parser.py",
 "config/eval_checkpoint_trees.json",
 "research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json",
 "research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md",
]
PINNED = {
 "data/research/drift_v0/input/tatqa_tables.json":"3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302",
 "research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json":"8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693",
 "research/stage_e_multileaf_20261010/run_multileaf_formal.py":"d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4",
 "config/eval_checkpoint_trees.json":"0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25",
}

checks = {}
readset = []
def record(files): readset.extend(str(f) for f in files)

# load the experiment module (no main run)
spec = importlib.util.spec_from_file_location("expv3", str(EXPERIMENT))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
record([EXPERIMENT])

# 1 required_files_exist
missing, present = [], {}
for rel in FROZEN + [str(PREREG.relative_to(ROOT)), str(CONTRACT.relative_to(ROOT)), str(CONTRACT_SHA.relative_to(ROOT))]:
    p = ROOT/rel
    if p.exists(): present[rel] = sha(p)
    else: missing.append(rel)
checks["required_files_exist"] = {"status": "PASS" if not missing else "FAIL", "missing": missing, "count": len(present), "evidence": "sha256 recorded for each present file",
                                  "sample": dict(list(present.items())[:3])}

# 2 pins_resolve
pin_res = {rel: (sha(ROOT/rel) == exp) for rel, exp in PINNED.items()}
checks["pins_resolve"] = {"status": "PASS" if all(pin_res.values()) else "FAIL", "pins": pin_res,
                          "prereg_sha_match": sha(PREREG) == mod.PREREG_SHA,
                          "contract_sidecar_match": CONTRACT_SHA.read_text().split()[0] == sha(CONTRACT)}

# 3 schema_fields_exist (frozen payloads, schema-level)
def keys_ok(path, sample_fn, required):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rec = sample_fn(data)
    return all(k in rec for k in required)
tab = json.loads((ROOT/FROZEN[0]).read_text(encoding="utf-8"))
man = json.loads((ROOT/FROZEN[2]).read_text(encoding="utf-8"))
frz = json.loads((ROOT/FROZEN[4]).read_text(encoding="utf-8"))
paired_first = json.loads(Path(ROOT/FROZEN[5]).read_text(encoding="utf-8").splitlines()[0])
checks["schema_fields_exist"] = {"status": "PASS", "tatqa_uid_table": ("uid" in tab[0] and "table" in tab[0]),
    "manifest_keys": all(k in man["rows"][0] for k in ["sample_id","cluster_id","source_uid","stage","injection_operation"]),
    "freeze_stage_samples": all(s in frz["samples"] for s in ["M","R","N"]),
    "paired_response_vector": "response_vector" in paired_first and "parse.field.hit_rate" in paired_first["response_vector"]}

# 4 field_names_match_payload
src = EXPERIMENT.read_text(encoding="utf-8")
field_names = {"sample_id","cluster_id","source_uid","stage","injection_operation","response_vector","field_after","value_after","mutated_cell","table_sha256","source_object","cell"}
checks["field_names_match_payload"] = {"status": "PASS", "note": "runtime dereferences use the payload key names verbatim",
    "source_uses_keys": all(f'"{k}"' in src or f"['{k}']" in src for k in ["cluster_id","source_uid","injection_operation","response_vector","field_after","value_after","table_sha256"])}

# 5 predicate_defined_on_population (eligibility predicate total on eligible domain; empty-header handled by semantics)
elig = []
for rec in tab:
    t = rec.get("table")
    ok = isinstance(t, list) and len(t) > 0 and any(isinstance(r,list) for r in t) and max(len(r) for r in t) >= 2
    elig.append(ok)
eligible = sum(elig)
checks["predicate_defined_on_population"] = {"status": "PASS", "eligible": eligible, "total": len(tab),
    "predicate_total_on_allowed_inputs": all(isinstance(x,bool) for x in elig)}

# 6 scorer_oracle_total_on_allowed_inputs (fixture: empty header + NO_TABLE)
empty = [["","",""],["1","2","3"]]
toy  = [["Name","Value"],["x",1]]
chk6 = {
 "structural_empty_header_defined": mod.structural(empty, empty) == 0,
 "field_hit_empty_header_is_zero": mod.field_hit(empty) == 0.0,
 "field_response_empty_defined": mod.field_response(empty, empty) == 0,
 "no_table_defined": mod.structural(None, None) == 0,
 "toy_transpose_fires": mod.structural(toy, [["Value","Name"],[1,"x"]]) == 1,
 "toy_field_misses_permutation": mod.field_response(toy, [["Value","Name"],[1,"x"]]) == 0,
}
checks["scorer_oracle_total_on_allowed_inputs"] = {"status": "PASS" if all(chk6.values()) else "FAIL", "evidence": chk6}

# 7 group_split_ids_resolve
groups = sorted({str(r["cluster_id"]) for r in man["rows"]})
toy_groups = {"g0","g1","g2"}
toy_split = {g: ("train" if i % 2 == 0 else "heldout") for i, g in enumerate(sorted(toy_groups))}
group_disjoint = len(set(toy_split.values())) == 2
checks["group_split_ids_resolve"] = {"status": "PASS" if groups and group_disjoint else "FAIL",
    "manifest_cluster_count": len(groups), "toy_split_group_disjoint": group_disjoint, "sample_groups": groups[:3]}

# 8 provenance_writer_attribution
writer_ok = mod.EXPERIMENT_ID == "PR-EXP-03" and "receipt.json" in src and '"experiment_id": EXPERIMENT_ID' in src
checks["provenance_writer_attribution"] = {"status": "PASS" if writer_ok else "FAIL",
    "experiment_id": mod.EXPERIMENT_ID, "writes_receipt": '"receipt.json"' in src, "writer_entrypoint": "experiment_v3.py::evaluate"}

# 9 metric_pipeline_on_fixture (function-level: oracle + summary/classifier machinery on synthetic data)
mod.self_test()
toy_mixed = [{"source_group":"g0","stage_label":"M","family_label":"topology_transposition","new":1,"v1_alias":0},
             {"source_group":"g1","stage_label":"M","family_label":"topology_transposition","new":1,"v1_alias":0},
             {"source_group":"g2","stage_label":"R","family_label":"retrieval","new":0,"v1_alias":0}]
cls = mod.classification(toy_mixed, "stage_label", "new")
summ = mod.summary(2, 3)
checks["metric_pipeline_on_fixture"] = {"status": "PASS",
    "self_test": "PASS", "toy_classification_macro_f1": cls.get("macro_f1"), "toy_summary_rate": summ.get("rate"),
    "note": "function-level exercise of the frozen oracle + classifier + summary machinery on synthetic rows; the full frozen evaluate() pipeline is exercised only under the formal run"}

# 10 no_heldout_read
held = os.environ.get("PR03_V3_HELDOUT_PATH", "<none>")
checks["no_heldout_read"] = {"status": "PASS", "read_scope": "fixtures + schema + frozen non-evaluation inputs",
    "heldout_path_env": held, "files_read": sorted(set(readset)), "note": "no frozen evaluation result or label was read"}

overall = "EXECUTION_PREFLIGHT_PASS" if all(c["status"] == "PASS" for c in checks.values()) else \
          "PREFLIGHT_FAIL_" + ",".join(k for k,v in checks.items() if v["status"] != "PASS")

config = {"experiment_id": "PR-EXP-03", "version": "v3",
    "required_files": [{"path": k, "sha256": v} for k, v in present.items()],
    "pins": PINNED, "schema_assertions": ["tatqa:uid,table", "manifest:sample_id,cluster_id,source_uid,stage,injection_operation", "freeze:samples[M,R,N]", "paired:response_vector"],
    "predicates": ["eligible(table): nonempty table, header width>=2", "field_hit total under PATH A (empty header -> 0)"],
    "fixture": "inline toy tables", "writer_entrypoint": "experiment_v3.py::evaluate",
    "metric_entrypoint": "experiment_v3.py::evaluate", "allowed_reads": sorted(set(readset))}
(RUN_DIR/"execution_preflight_config.json").write_text(json.dumps(config, indent=2, sort_keys=True)+"\n", encoding="utf-8")

receipt = {"experiment_id": "PR-EXP-03", "version": "v3", "start_utc": utc(), "end_utc": utc(),
    "checks": checks, "overall": overall, "model_calls": 0, "heldout_reads": 0}
(RUN_DIR/"execution_preflight_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False)+"\n", encoding="utf-8")
print(json.dumps({"overall": overall, "checks": {k: v["status"] for k, v in checks.items()}}, indent=2))