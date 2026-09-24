"""Derive the phase1a learnability feature ledger from accepted roles.

Zero fabrication: every row field comes from the supplied derivation inputs,
which must themselves be produced from accepted roles (layer manifest, source
tables, schema, label ledger). This runner validates and assembles; it never
invents sample ids, uids, headers, families or candidate targets.

The nine mirrored constraints follow research/phase1a_data_contract.py
:665-742 (addendum A of the DATA_NO_GO report); fail codes reuse the contract
names so a rejection here reads identically at package-validation time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FEATURE_LEDGER_VERSION = "phase1a-feature-ledger-v1"
FEATURE_FIELDS = {
    "sample_id",
    "uid",
    "observed_header",
    "canonical_fields",
    "candidate_target",
    "confidence",
    "family",
}
PROPOSAL_PARTITIONS = ("proposal_train.train", "proposal_train.dev")
ALLOWED_CONFIDENCE = {"low", "medium", "high"}


class LedgerDerivationError(ValueError):
    """Fail-closed derivation rejection carrying a contract-style code."""

    def __init__(self, code: str, **detail: object) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _proposal_map(layer_manifest: dict) -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for partition, rows in (layer_manifest.get("layers") or {}).items():
        for row in rows or []:
            sample_id, uid = row.get("sample_id"), row.get("uid")
            if not isinstance(sample_id, str) or not sample_id:
                raise LedgerDerivationError("invalid_layer_manifest_row", partition=partition)
            if sample_id in out:
                raise LedgerDerivationError("duplicate_layer_sample", sample_id=sample_id)
            out[sample_id] = (uid if isinstance(uid, str) else "", partition)
    return out


def derive(
    inputs: dict,
    layer_manifest: dict,
    role_paths: dict[str, Path],
) -> dict:
    samples = _proposal_map(layer_manifest)
    proposal_ids = {sid for sid, (_, partition) in samples.items() if partition in PROPOSAL_PARTITIONS}
    rows_in = inputs.get("rows")
    if not isinstance(rows_in, list) or not rows_in:
        raise LedgerDerivationError("invalid_feature_ledger_rows")
    rows: dict[str, dict] = {}
    for index, row in enumerate(rows_in):
        if not isinstance(row, dict):
            raise LedgerDerivationError("invalid_feature_ledger_row", index=index)
        sample_id = row.get("sample_id")
        uid = row.get("uid")
        canonical = row.get("canonical_fields")
        candidate = row.get("candidate_target")
        confidence = row.get("confidence")
        if not isinstance(sample_id, str) or not sample_id:
            raise LedgerDerivationError("invalid_feature_ledger_row", index=index, why="sample_id")
        if sample_id not in proposal_ids:
            raise LedgerDerivationError("feature_ledger_identity_mismatch", index=index, sample_id=sample_id)
        if samples[sample_id][0] != uid or not isinstance(uid, str) or not uid:
            raise LedgerDerivationError("feature_ledger_identity_mismatch", index=index, sample_id=sample_id)
        if sample_id in rows:
            raise LedgerDerivationError("invalid_feature_ledger_row", index=index, why="duplicate_sample_id")
        if not isinstance(row.get("observed_header"), str) or not row["observed_header"]:
            raise LedgerDerivationError("invalid_feature_ledger_row", index=index, why="observed_header")
        if not isinstance(row.get("family"), str) or not row["family"]:
            raise LedgerDerivationError("invalid_feature_ledger_row", index=index, why="family")
        if (
            not isinstance(canonical, list)
            or not canonical
            or any(not isinstance(f, str) or not f for f in canonical)
            or len(set(canonical)) != len(canonical)
        ):
            raise LedgerDerivationError("invalid_feature_ledger_row", index=index, why="canonical_fields")
        if candidate is not None and candidate not in canonical:
            raise LedgerDerivationError("invalid_feature_ledger_row", index=index, why="candidate_target")
        if confidence is not None and confidence not in ALLOWED_CONFIDENCE:
            raise LedgerDerivationError("invalid_feature_ledger_row", index=index, why="confidence")
        rows[sample_id] = {
            "sample_id": sample_id,
            "uid": uid,
            "observed_header": row["observed_header"],
            "canonical_fields": list(canonical),
            "candidate_target": candidate,
            "confidence": confidence,
            "family": row["family"],
        }
    if set(rows) != proposal_ids:
        raise LedgerDerivationError(
            "feature_ledger_proposal_coverage_mismatch",
            missing=sorted(proposal_ids - set(rows)),
            extra=sorted(set(rows) - proposal_ids),
        )
    ordered = [rows[sid] for sid in sorted(rows)]
    for role in ("source_tables", "schema", "confidence_manifest"):
        if role not in role_paths:
            raise LedgerDerivationError("missing_role_artifact", role=role)
    return {
        "contract_version": FEATURE_LEDGER_VERSION,
        "source_tables_sha256": sha256_file(role_paths["source_tables"]),
        "schema_sha256": sha256_file(role_paths["schema"]),
        "confidence_manifest_sha256": sha256_file(role_paths["confidence_manifest"]),
        "rows": ordered,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs", required=True, type=Path)
    ap.add_argument("--layer-manifest", required=True, type=Path)
    ap.add_argument("--source-tables", required=True, type=Path)
    ap.add_argument("--schema", required=True, type=Path)
    ap.add_argument("--confidence-manifest", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    inputs = json.loads(args.inputs.read_text(encoding="utf-8"))
    manifest = json.loads(args.layer_manifest.read_text(encoding="utf-8"))
    ledger = derive(
        inputs,
        manifest,
        {
            "source_tables": args.source_tables,
            "schema": args.schema,
            "confidence_manifest": args.confidence_manifest,
        },
    )
    payload = json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.out.write_text(payload, encoding="utf-8", newline="\n")
    print(f"wrote {args.out} rows={len(ledger['rows'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())