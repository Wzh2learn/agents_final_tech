# -*- coding: utf-8 -*-
'''TQ-3 finalize: build MANIFEST.json for tq3_execution_prep_v1 (self-excluded; no __pycache__/.pyc).'''
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

TQ3 = Path(
    "D:/AIRcommend/JinRongAgents/agents_final_tech/research/"
    "paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/"
    "tq3_execution_prep_v1"
)
PKG = TQ3.parent


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


files = []
for p in sorted(TQ3.rglob("*")):
    if not p.is_file():
        continue
    if p.name == "MANIFEST.json":
        continue
    if "__pycache__" in p.parts or p.suffix == ".pyc":
        continue
    files.append(
        {
            "path": p.relative_to(TQ3).as_posix(),
            "sha256": sha(p),
            "bytes": p.stat().st_size,
        }
    )

manifest = {
    "schema": "tq3_execution_prep_manifest_v1",
    "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "actor": "Loop D (AI)",
    "status": "MATERIALS_PREPARED_AWAITING_RUN_AUTHORIZATION",
    "scientific_gold_validity": "NOT_ESTABLISHED",
    "system_outcome": "NOT_RUN",
    "layer2_authorized": False,
    "model_calls_this_round": 0,
    "counts": {
        "specs_rev1": 9,
        "dev_inputs": 12,
        "reference_files": 6,
        "scoring_files": 6,
        "entry_checks_passed": 7,
    },
    "inputs": {
        "stage2_cases": {
            "path": "packets/stage2_cases.json",
            "sha256": sha(PKG / "packets/stage2_cases.json"),
        },
        "case_provenance": {
            "path": "coordinator/case_provenance.json",
            "sha256": sha(PKG / "coordinator/case_provenance.json"),
        },
        "measurement_contract_v2_manifest": {
            "path": "measurement_contract_v2/MANIFEST.json",
            "sha256": sha(PKG / "measurement_contract_v2/MANIFEST.json"),
        },
    },
    "files": files,
    "manifest_self_excluded": True,
}
out = TQ3 / "MANIFEST.json"
out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8")
print(json.dumps({"files": len(files), "schema": manifest["schema"]}, ensure_ascii=True))
