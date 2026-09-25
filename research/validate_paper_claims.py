#!/usr/bin/env python3
"""Static acceptance gate for the teacher-review paper draft.

This checker performs no network, model, database, or service calls. It verifies
that every declared claim has manuscript language and repository evidence, and
that internal workflow markers do not leak into the teacher-facing manuscript.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO / "paper" / "claim_manifest_v1.json"


def validate(manifest_path: Path = DEFAULT_MANIFEST) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paper_path = REPO / manifest["paper"]
    errors: list[str] = []
    checks: list[dict[str, object]] = []

    if not paper_path.is_file():
        return {"status": "FAIL", "errors": [f"missing paper: {manifest['paper']}"], "checks": []}

    manuscript = paper_path.read_text(encoding="utf-8")

    for section in manifest["required_sections"]:
        present = f"## {section}" in manuscript or f"## 1. {section}" in manuscript
        if not present:
            # Numbered manuscript sections have variable numeric prefixes.
            present = any(
                line.startswith("## ") and line.split(". ", 1)[-1] == section
                for line in manuscript.splitlines()
            )
        checks.append({"check": f"section:{section}", "pass": present})
        if not present:
            errors.append(f"missing section: {section}")

    for marker in manifest["forbidden_manuscript_markers"]:
        absent = marker not in manuscript
        checks.append({"check": f"forbidden:{marker}", "pass": absent})
        if not absent:
            errors.append(f"internal marker leaked into manuscript: {marker}")

    for claim in manifest["claims"]:
        claim_id = claim["id"]
        for token in claim["manuscript_tokens"]:
            present = token in manuscript
            checks.append({"check": f"{claim_id}:token:{token}", "pass": present})
            if not present:
                errors.append(f"{claim_id} missing manuscript token: {token}")
        for relative in claim["evidence"]:
            exists = (REPO / relative).is_file()
            checks.append({"check": f"{claim_id}:evidence:{relative}", "pass": exists})
            if not exists:
                errors.append(f"{claim_id} missing evidence: {relative}")
        # Audit records are separated from measurement evidence so that a review cannot be
        # mistaken for a data artifact; a dangling pointer here must still fail closed.
        for relative in claim.get("audit_records", []):
            exists = (REPO / relative).is_file()
            checks.append({"check": f"{claim_id}:audit_record:{relative}", "pass": exists})
            if not exists:
                errors.append(f"{claim_id} missing audit record: {relative}")

    for relative in manifest["figures"]:
        exists = (REPO / relative).is_file()
        checks.append({"check": f"figure:{relative}", "pass": exists})
        if not exists:
            errors.append(f"missing figure: {relative}")

    for relative in manifest.get("delivery_files", []):
        exists = (REPO / relative).is_file()
        checks.append({"check": f"delivery:{relative}", "pass": exists})
        if not exists:
            errors.append(f"missing delivery file: {relative}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "paper": manifest["paper"],
        "claims": len(manifest["claims"]),
        "checks_total": len(checks),
        "checks_passed": sum(bool(item["pass"]) for item in checks),
        "errors": errors,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.manifest)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.json:
        print(rendered)
    else:
        print(
            f"paper-claims: {result['status']} "
            f"({result.get('checks_passed', 0)}/{result.get('checks_total', 0)} checks)"
        )
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
