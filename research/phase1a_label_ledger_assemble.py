"""Assemble the phase1a label_ledger artifact (JSON Lines) from independent reviews.

Fail-closed aggregation of two independent reviewer judgment files plus an
adjudication file into contract-shaped label rows (research/phase1a_data_contract.py
:72-81 LABEL_FIELDS, :745-833 independent_correctness checks, JSON Lines format).

Independence rules enforced here (protocol doc section 1):
- the generator id must not appear as reviewer or adjudicator;
- the two reviewer ids must differ; the adjudicator must not be a reviewer;
- every labelled (sample, col) pair needs both reviews; disagreements need an
  adjudication whose choice becomes gold and must equal the recorded gold;
- one labelled column per sample (contract uniqueness is per sample_id).

The artifact is pure JSON Lines (one object per line, keys exactly LABEL_FIELDS);
diagnostics (carriers, template versions, agreement rate) go to a sidecar meta
file so the artifact itself stays contract-shaped.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

VALID_ACTIONS = {"map_to", "skip", "hold"}


class LabelAssemblyError(ValueError):
    """Fail-closed rejection carrying a machine-readable code."""

    def __init__(self, code: str, **detail: object) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _valid_choice(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    action = value.get("action")
    target = value.get("target")
    if action not in VALID_ACTIONS:
        return False
    if action == "map_to":
        return isinstance(target, str) and bool(target)
    return target is None


def _judgments_by_pair(doc: dict, who: str) -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    for j in doc.get("judgments", []):
        sample_id, col = j.get("sample_id"), j.get("col")
        if not isinstance(sample_id, str) or not sample_id or type(col) is not int:
            raise LabelAssemblyError("invalid_judgment", reviewer=who, entry=j)
        choice = {"action": j.get("action"), "target": j.get("target")}
        if not _valid_choice(choice):
            raise LabelAssemblyError("invalid_judgment", reviewer=who, entry=j)
        key = (sample_id, col)
        if key in out:
            raise LabelAssemblyError("duplicate_judgment", reviewer=who, key=key)
        out[key] = {**j, "_choice": choice}
    return out


def assemble(r1: dict, r2: dict, adj_doc: dict, generator_id: str) -> tuple[list[dict], dict]:
    rid1, rid2 = r1.get("reviewer_id"), r2.get("reviewer_id")
    aid = adj_doc.get("adjudicator_id")
    if not all(isinstance(x, str) and x for x in (rid1, rid2, aid)):
        raise LabelAssemblyError("missing_carrier_ids")
    if rid1 == rid2:
        raise LabelAssemblyError("reviewers_not_distinct", r1=rid1, r2=rid2)
    if generator_id in {rid1, rid2, aid}:
        raise LabelAssemblyError("generator_in_reviewers", generator=generator_id)
    if aid in {rid1, rid2}:
        raise LabelAssemblyError("adjudicator_is_reviewer", adjudicator=aid)
    j1 = _judgments_by_pair(r1, rid1)
    j2 = _judgments_by_pair(r2, rid2)
    adjudications = {
        e.get("sample_id"): e for e in adj_doc.get("entries", [])
    }
    rows: list[dict] = []
    agreed = 0
    for key in sorted(set(j1) | set(j2)):
        sample_id, col = key
        a, b = j1.get(key), j2.get(key)
        if a is None or b is None:
            raise LabelAssemblyError("incomplete_review_pair", sample_id=sample_id, col=col)
        if a["uid"] != b["uid"] or not isinstance(a["uid"], str) or not a["uid"]:
            raise LabelAssemblyError("uid_disagreement", sample_id=sample_id, col=col)
        if any(r["sample_id"] == sample_id and r["col"] != col for r in rows):
            raise LabelAssemblyError("multiple_columns_per_sample", sample_id=sample_id)
        reviewers = [
            {"reviewer_id": rid1, "action": a["action"], "target": a["target"]},
            {"reviewer_id": rid2, "action": b["action"], "target": b["target"]},
        ]
        if a["_choice"] == b["_choice"]:
            agreed += 1
            gold, adjudication = a["_choice"], None
        else:
            entry = adjudications.get(sample_id)
            if not isinstance(entry, dict):
                raise LabelAssemblyError("missing_adjudication", sample_id=sample_id, col=col)
            if entry.get("col", col) != col:
                raise LabelAssemblyError("adjudication_col_mismatch", sample_id=sample_id)
            choice = {"action": entry.get("action"), "target": entry.get("target")}
            if not _valid_choice(choice):
                raise LabelAssemblyError("adjudication_invalid", sample_id=sample_id)
            gold = choice
            adjudication = {
                "adjudicator_id": aid,
                "action": entry.get("action"),
                "target": entry.get("target"),
                "rationale_ref": entry.get("rationale_ref"),
            }
        rows.append({
            "sample_id": sample_id,
            "uid": a["uid"],
            "col": col,
            "gold_action": gold["action"],
            "gold_target": gold["target"],
            "quality_grade": "Q3",
            "reviewers": reviewers,
            "adjudication": adjudication,
        })
    meta = {
        "reviewer_carriers": [rid1, rid2],
        "adjudicator": aid,
        "generator_id": generator_id,
        "template_versions": [r1.get("template_version"), r2.get("template_version")],
        "pairs": len(rows),
        "agreed_pairs": agreed,
        "agreement_rate": (agreed / len(rows)) if rows else None,
        "assembled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return rows, meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--r1", required=True, type=Path)
    ap.add_argument("--r2", required=True, type=Path)
    ap.add_argument("--adjudications", required=True, type=Path)
    ap.add_argument("--generator-id", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--meta-out", type=Path, default=None)
    args = ap.parse_args()
    r1 = json.loads(args.r1.read_text(encoding="utf-8"))
    r2 = json.loads(args.r2.read_text(encoding="utf-8"))
    adj = json.loads(args.adjudications.read_text(encoding="utf-8"))
    rows, meta = assemble(r1, r2, adj, args.generator_id)
    payload = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    )
    args.out.write_text(payload, encoding="utf-8", newline="\n")
    meta_path = args.meta_out or args.out.with_suffix(".meta.json")
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {args.out} rows={len(rows)} meta={meta_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())