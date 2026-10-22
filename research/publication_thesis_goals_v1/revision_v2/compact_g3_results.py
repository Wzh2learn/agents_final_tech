"""Create a reviewable compact view from the full GB10 action receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def action_summary(action: dict[str, Any]) -> dict[str, Any]:
    parsed = action.get("parsed")
    if isinstance(parsed, dict):
        if "fixture_count" in parsed:
            parsed = {
                "status": parsed.get("status"),
                "fixture_count": parsed.get("fixture_count"),
                "mismatch_count": len(parsed.get("mismatches", [])),
                "mismatches": parsed.get("mismatches", []),
            }
        elif "prediction" in parsed:
            parsed = {
                key: parsed.get(key)
                for key in (
                    "prediction",
                    "reason",
                    "execution_status",
                    "target_calls",
                    "source_calls",
                    "target_imported",
                    "target_call",
                    "source_imported",
                    "source_call",
                    "target_declared",
                    "source_declared",
                )
                if key in parsed
            }
    return {
        "status": action.get("status"),
        "exit_code": action.get("exit_code"),
        "wall_clock_seconds": action.get("wall_clock_seconds"),
        "accounting_attempts": action.get("accounting_attempts"),
        "accounting_tokens": action.get("accounting_tokens"),
        "command": action.get("command"),
        "parsed": parsed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--gb10-path", required=True)
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    rows = []
    for row in source["rows"]:
        rows.append(
            {
                "id": row["id"],
                "kind": row["kind"],
                "reference": row["reference"],
                "reference_provenance": row.get("reference_provenance"),
                "module_path": row["module_path"],
                "module_sha256": row["module_sha256"],
                "manifest_path": row["manifest_path"],
                "manifest_sha256": row["manifest_sha256"],
                "derived": row["derived"],
                "actions": {
                    name: action_summary(action)
                    for name, action in row["actions"].items()
                },
            }
        )
    compact = {
        "schema": source["schema"] + "_compact",
        "date": source["date"],
        "evidence_identity": source["evidence_identity"],
        "full_raw": {
            "gb10_path": args.gb10_path,
            "sha256": sha256_file(args.input),
            "bytes": args.input.stat().st_size,
        },
        "environment": source["environment"],
        "binding_contract": source["binding_contract"],
        "rows": rows,
        "policies": source["policies"],
        "timing_scope": source["timing_scope"],
        "nonclaims": source["nonclaims"],
    }
    args.output.write_text(
        json.dumps(compact, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
