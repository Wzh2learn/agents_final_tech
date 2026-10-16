# -*- coding: utf-8 -*-
"""TQ-3 rev1 spec builder.

Fills question_uid/table_uid (from coordinator/case_provenance.json, asserted
against the raw TAT-QA records) and restores per-case table pins for the 9
measurement specs. Writes only into tq3_execution_prep_v1/specs_rev1/.

Read-only inputs:
- packets/stage2_cases.json
- coordinator/case_provenance.json
- raw/tatqa_dataset_train.json, raw/tatqa_dataset_dev.json
- measurement_contract_v2/cases/Qxx.json (v2 specs; NOT overwritten)

No network. No model calls.
"""
import hashlib
import json
from pathlib import Path

PKG = Path(
    "D:/AIRcommend/JinRongAgents/agents_final_tech/research/"
    "paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1"
)
TQ3 = PKG / "tq3_execution_prep_v1"
OUT = TQ3 / "specs_rev1"

SPEC_IDS = ["Q02", "Q03", "Q04", "Q05", "Q06", "Q08", "Q09", "Q10", "Q12"]
DEV_PANEL = {"Q02", "Q03", "Q04", "Q05", "Q10", "Q12"}

CORPUS_PIN_SOURCE = (
    "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302"
)
CORPUS_PIN_INJECTED = (
    "827092cf6af2212ae334a9ad5f7b9ea12122d90ff9117353baf79bb1936e4fa9"
)
CANON_NOTE = (
    "canonical serialization: json.dumps(obj, ensure_ascii=False, "
    "sort_keys=True, separators=(',', ':')).encode('utf-8')"
)


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def canon_sha256(obj):
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main():
    cases = {
        c["case_id"]: c
        for c in json.loads(
            (PKG / "packets/stage2_cases.json").read_text(encoding="utf-8")
        )
    }
    prov = {
        p["case_id"]: p
        for p in json.loads(
            (PKG / "coordinator/case_provenance.json").read_text(encoding="utf-8")
        )
    }

    raw_cache = {}

    def raw_records(name):
        if name not in raw_cache:
            raw_cache[name] = json.loads(
                (PKG / "raw" / name).read_text(encoding="utf-8")
            )
        return raw_cache[name]

    receipt = {
        "schema": "tq3_specs_rev1_build_receipt_v1",
        "date": "2026-10-16",
        "actor": "Loop D (AI)",
        "canonical_serialization": CANON_NOTE,
        "inputs": {
            "stage2_cases": {
                "path": "packets/stage2_cases.json",
                "sha256": sha256_file(PKG / "packets/stage2_cases.json"),
            },
            "case_provenance": {
                "path": "coordinator/case_provenance.json",
                "sha256": sha256_file(PKG / "coordinator/case_provenance.json"),
            },
        },
        "v2_pin_observations": {},
        "outputs": [],
        "uid_verification": [],
    }

    v2_source_pins = set()
    v2_perturbed_pins = set()

    for cid in SPEC_IDS:
        v2 = json.loads(
            (PKG / "measurement_contract_v2/cases" / f"{cid}.json").read_text(
                encoding="utf-8"
            )
        )
        p = prov[cid]
        c = cases[cid]

        # Assert provenance uids against raw records.
        rec = raw_records(p["raw_file"])[p["raw_record_index"]]
        q_uid_raw = rec["questions"][p["question_index"]].get("uid")
        t_uid_raw = rec.get("table", {}).get("uid")
        assert q_uid_raw == p["question_uid"], f"{cid}: question uid mismatch"
        assert t_uid_raw == p["uid"], f"{cid}: table uid mismatch"
        receipt["uid_verification"].append(
            {
                "task_id": cid,
                "question_uid": p["question_uid"],
                "table_uid": p["uid"],
                "verified_against": f"raw/{p['raw_file']}"
                f"#/records/{p['raw_record_index']}",
            }
        )

        v2_source_pins.add(v2["source"]["source_table_sha256"])
        v2_perturbed_pins.add(v2["source"]["perturbed_table_sha256"])

        src = dict(v2["source"])
        src.update(
            {
                "question_uid": p["question_uid"],
                "table_uid": p["uid"],
                "source_table_sha256": canon_sha256(c["source_table"]),
                "perturbed_table_sha256": canon_sha256(c["perturbed_table"]),
                "corpus_pins": {
                    "note": (
                        "rev1: v2 stored drift-v0 corpus-file hashes under "
                        "source_table_sha256/perturbed_table_sha256 (identical "
                        "across all 9 specs); rev1 relocates them here with "
                        "accurate labels and restores per-case table pins."
                    ),
                    "source_tables_corpus_file": {
                        "file": "data/research/drift_v0/input/tatqa_tables.json",
                        "sha256": CORPUS_PIN_SOURCE,
                    },
                    "injected_tables_corpus_file": {
                        "file": "data/research/drift_v0/output/injected_tables.json",
                        "sha256": CORPUS_PIN_INJECTED,
                    },
                },
                "raw": {
                    "raw_file": p["raw_file"],
                    "raw_file_sha256": sha256_file(PKG / "raw" / p["raw_file"]),
                    "raw_record_index": p["raw_record_index"],
                    "question_index": p["question_index"],
                },
            }
        )

        spec = dict(v2)
        spec["source"] = src
        spec["revision"] = {
            "rev": "rev1",
            "date": "2026-10-16",
            "actor": "Loop D (AI)",
            "supersedes_for_execution": f"measurement_contract_v2/cases/{cid}.json",
            "changes": [
                "filled question_uid/table_uid from coordinator/case_provenance.json; "
                "both asserted against raw TAT-QA records",
                "restored per-case source_table_sha256/perturbed_table_sha256 "
                "(v2 values were corpus-file pins, identical across all specs; "
                "moved to corpus_pins)",
                "added raw-file pin block",
            ],
        }
        spec["panel_plan"] = (
            {
                "role": "dev_panel_dry_run_input",
                "variants": ["original", "perturbed"],
                "in_primary_metrics": True,
            }
            if cid in DEV_PANEL
            else {
                "role": "exploratory_ambiguity_side_case",
                "in_primary_metrics": False,
            }
        )

        out = OUT / f"{cid}.json"
        out.write_text(
            json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        receipt["outputs"].append(
            {
                "path": f"specs_rev1/{cid}.json",
                "sha256": sha256_file(out),
                "bytes": out.stat().st_size,
            }
        )

    receipt["v2_pin_observations"] = {
        "distinct_source_pin_values": sorted(v2_source_pins),
        "distinct_perturbed_pin_values": sorted(v2_perturbed_pins),
        "matches_corpus_files": (
            v2_source_pins == {CORPUS_PIN_SOURCE}
            and v2_perturbed_pins == {CORPUS_PIN_INJECTED}
        ),
        "defect": (
            "v2 per-case hash fields carried corpus-level file hashes for all "
            "9 specs; corrected in rev1"
        ),
    }

    (OUT / "BUILD_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "specs_written": len(receipt["outputs"]),
                "uid_verified": len(receipt["uid_verification"]),
                "v2_pin_defect_confirmed": receipt["v2_pin_observations"][
                    "matches_corpus_files"
                ],
            },
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
