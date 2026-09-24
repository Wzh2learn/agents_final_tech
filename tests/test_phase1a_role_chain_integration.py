"""End-to-end composition test for the phase1a role chain.

Composes the role tooling the way assembly day will (protocol doc sections 1, 8
and 10): independent reviews -> label_ledger assembler -> feature-ledger
derivation -> full nine-role package -> contract.validate_package. Proves the
runners compose with the contract on synthetic, self-declared fixtures before
any real data arrives.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import research.phase1a_data_contract as contract
from research.phase1a_feature_ledger_derive import derive
from research.phase1a_label_ledger_assemble import assemble

ONE_SIDED = {
    "H2a_quality_noninferiority": "paired_uid_sign_flip_on_seed_mean_difference",
    "H2b_safety_noninferiority": "paired_uid_sign_flip_on_seed_mean_difference",
    "H2c_risk_constrained_coverage": "paired_uid_sign_flip_on_seed_mean_difference",
    "H3a_uid_any_harm": "exact_mcnemar",
    "H3a_valid_rule_retention": "paired_cluster_sign_flip_noninferiority",
}

SPECS = {
    "train": ("train", "cluster-proposal"),
    "dev": ("train", "cluster-proposal"),
    "gate": ("validation", "cluster-gate"),
    "test": ("test", "cluster-test"),
    "future": ("future-2027q1", "cluster-future"),
}
IDS = {
    "source_tables": "src",
    "schema": "sch",
    "injection_map": "inj",
    "label_ledger": "lab",
    "learnability_feature_ledger": "led",
}
FILES = {
    "src": "source_tables.jsonl",
    "sch": "schema.json",
    "inj": "injection_map.json",
    "lab": "labels.jsonl",
    "led": "feature_ledger.json",
}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows),
        encoding="utf-8",
        newline="\n",
    )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact(path: Path, artifact_id: str, role: str) -> dict:
    return {
        "id": artifact_id,
        "role": role,
        "path": "artifacts/" + path.name,
        "bytes": path.stat().st_size,
        "sha256": _sha(path),
    }


def _build_package(tmp_path: Path, swap_confidence: bool = False) -> Path:
    root = tmp_path / "phase1a-package"
    art = root / "artifacts"
    uids = {
        name: contract.lineage_uid("fixture-finance", "rev-1", f"report-{name}")
        for name in SPECS
    }
    _write_jsonl(art / FILES["src"], [
        {"uid": uids[n], "headers": ["alias", "amount"]} for n in SPECS
    ])
    _write_json(art / FILES["sch"], {"canonical_fields": ["Revenue", "Amount"]})
    _write_json(art / FILES["inj"], {
        uids["train"]: [{"col": 0, "canonical": "Revenue", "family": "alias_variant"}],
        uids["dev"]: [{"col": 1, "canonical": "Amount", "family": "date_variant"}],
    })
    confidence = {
        "field": "none_native",
        "source": "fixture: no native confidence field",
        "missing_policy": "unmeasurable",
        "gain_collateral_substitution": False,
        "allowed_values": ["low", "medium", "high"],
    }
    _write_json(art / "confidence.json", confidence)

    base_judgments = [
        ("sample-train", uids["train"], 0, "map_to", "Revenue"),
        ("sample-dev", uids["dev"], 1, "skip", None),
        ("sample-gate", uids["gate"], 0, "hold", None),
        ("sample-test", uids["test"], 1, "map_to", "Amount"),
        ("sample-future", uids["future"], 0, "skip", None),
    ]
    r1 = {"reviewer_id": "r1", "template_version": "t1", "judgments": [
        {"sample_id": s, "uid": u, "col": c, "action": a, "target": t}
        for (s, u, c, a, t) in base_judgments
    ]}
    r2 = {"reviewer_id": "r2", "template_version": "t1", "judgments": [
        {"sample_id": s, "uid": u, "col": c, "action": (a if s != "sample-dev" else "map_to"),
         "target": (t if s != "sample-dev" else "Amount")}
        for (s, u, c, a, t) in base_judgments
    ]}
    adj = {"adjudicator_id": "adj", "entries": [
        {"sample_id": "sample-dev", "col": 1, "action": "skip", "target": None,
         "rationale_ref": "fixture-note#1"},
    ]}
    rows, _meta = assemble(r1, r2, adj, "generator-fixture")
    _write_jsonl(art / FILES["lab"], rows)

    label_by_sample = {r["sample_id"]: r for r in rows}
    flat_layers = {
        "proposal_train.train": [{"sample_id": "sample-train", "uid": uids["train"]}],
        "proposal_train.dev": [{"sample_id": "sample-dev", "uid": uids["dev"]}],
        "gate_validation": [{"sample_id": "sample-gate", "uid": uids["gate"]}],
    }
    derive_rows = []
    fam_by_uid = {uids["train"]: "alias_variant", uids["dev"]: "date_variant"}
    for sample_id in ("sample-train", "sample-dev"):
        lab = label_by_sample[sample_id]
        derive_rows.append({
            "sample_id": sample_id,
            "uid": lab["uid"],
            "observed_header": "alias amount",
            "canonical_fields": ["Revenue", "Amount"],
            "candidate_target": lab["gold_target"] if lab["gold_action"] == "map_to" else None,
            "confidence": None,
            "family": fam_by_uid[lab["uid"]],
        })
    ledger = derive(
        {"rows": derive_rows},
        {"layers": flat_layers},
        {
            "source_tables": art / FILES["src"],
            "schema": art / FILES["sch"],
            "confidence_manifest": art / "confidence.json",
        },
    )
    _write_json(art / FILES["led"], ledger)

    if swap_confidence:
        confidence["source"] = "fixture: swapped after ledger derivation"
        _write_json(art / "confidence.json", confidence)

    hashes = {aid: _sha(art / FILES[aid]) for aid in IDS.values()}
    _write_json(art / "licence.json", {
        "status": "accepted",
        "accepted_by": "fixture-user",
        "accepted_at": "2026-09-24T00:00:00+00:00",
        "permitted_uses": ["training", "tuning", "evaluation", "rule_acceptance"],
        "covered_artifact_sha256": {
            IDS["source_tables"]: hashes["src"],
            IDS["schema"]: hashes["sch"],
            IDS["injection_map"]: hashes["inj"],
            IDS["label_ledger"]: hashes["lab"],
            IDS["learnability_feature_ledger"]: hashes["led"],
        },
    })
    _write_json(art / "receipt.json", {
        "status": "PASS",
        "checker": "fixture-checker",
        "commit": "0" * 40,
        "executed_at": "2026-09-24T00:00:00+00:00",
        "input_sha256": {
            IDS["source_tables"]: hashes["src"],
            IDS["schema"]: hashes["sch"],
            IDS["injection_map"]: hashes["inj"],
        },
    })

    def _enrich(key, rows):
        return [
            {
                "sample_id": r["sample_id"],
                "uid": r["uid"],
                "dataset_id": "fixture-finance",
                "dataset_revision": "rev-1",
                "source_split": SPECS[key][0],
                "independence_cluster": SPECS[key][1],
                "lineage_root_id": f"report-{key}",
                "transformation_parent_id": None,
            }
            for r in rows
        ]

    layers = {
        "proposal_train": {
            "train": _enrich("train", flat_layers["proposal_train.train"]),
            "dev": _enrich("dev", flat_layers["proposal_train.dev"]),
        },
        "gate_validation": _enrich("gate", flat_layers["gate_validation"]),
        "sealed_test": _enrich(
            "test", [{"sample_id": "sample-test", "uid": uids["test"]}]
        ),
        "future_replay": _enrich(
            "future", [{"sample_id": "sample-future", "uid": uids["future"]}]
        ),
    }
    plan = {
        "status": "approved",
        "approved_by": "fixture-user",
        "approved_at": "2026-09-24T00:00:00+00:00",
        "cluster_unit": "lineage_uid",
        "significance_level": 0.05,
        "target_power": 0.8,
        "risk_limit": 0.1,
        "noninferiority_margins": {
            "delta_quality": 0.02, "delta_harm": 0.02, "delta_retention": 0.02,
        },
        "primary_metrics": ["action_macro_f1", "harmful_map_rate"],
        "threshold_selection": "proposal_dev_only",
        "seed_uid_aggregation": "fixed_seed_pair_then_uid_cluster_bootstrap",
        "holm_families": contract.REQUIRED_HOLM_FAMILIES,
        "one_sided_p_value_methods": ONE_SIDED,
        "holm_adjustment": "step_down_adjusted_p_and_simultaneous_one_sided_ci",
        "minimum_uid_by_action": {"map_to": 2, "skip": 2, "hold": 2},
        "minimum_uid_by_role_family": {"alias_variant": 2, "date_variant": 2},
        "mde_by_confirmatory_contrast": {h: 0.05 for h in contract.REQUIRED_MDE_CONTRASTS},
        "layer_manifest_sha256": contract._digest_object(layers),
    }
    _write_json(art / "plan.json", plan)

    artifacts = [
        _artifact(art / FILES["src"], IDS["source_tables"], "source_tables"),
        _artifact(art / FILES["sch"], IDS["schema"], "schema"),
        _artifact(art / FILES["inj"], IDS["injection_map"], "injection_map"),
        _artifact(art / FILES["lab"], IDS["label_ledger"], "label_ledger"),
        _artifact(art / FILES["led"], IDS["learnability_feature_ledger"],
                  "learnability_feature_ledger"),
        _artifact(art / "licence.json", "lic", "licence_record"),
        _artifact(art / "confidence.json", "conf", "confidence_manifest"),
        _artifact(art / "plan.json", "plan", "analysis_plan"),
        _artifact(art / "receipt.json", "rec", "parser_contract_receipt"),
    ]
    manifest = {
        "contract_version": "phase1a-data-package-v2",
        "package_id": "fixture-package-1",
        "artifacts": artifacts,
        "bindings": {
            "label_ledger": IDS["label_ledger"],
            "learnability_feature_ledger": IDS["learnability_feature_ledger"],
            "licence_record": "lic",
            "confidence_manifest": "conf",
            "analysis_plan": "plan",
            "parser_contract_receipt": "rec",
        },
        "layers": layers,
    }
    _write_json(root / "phase1a_manifest.json", manifest)
    return root


def test_role_chain_composes_to_ready(tmp_path: Path) -> None:
    root = _build_package(tmp_path)
    first = contract.validate_package(root)
    second = contract.validate_package(root)
    assert first["status"] == contract.READY, first
    assert first == second
    assert first["meta"]["socket_attempts"] == 0
    assert all(g["status"] == "PASS" for g in first["gates"].values())


def test_confidence_swap_after_derivation_is_caught(tmp_path: Path) -> None:
    root = _build_package(tmp_path, swap_confidence=True)
    report = contract.validate_package(root)
    assert report["status"] == contract.NO_GO
    codes = [
        e.get("code") for g in report["gates"].values() for e in g["errors"]
    ]
    assert "feature_ledger_source_hash_mismatch" in codes