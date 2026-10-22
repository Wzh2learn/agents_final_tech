"""Independent real-fixture behavior comparison against the parent module."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def load_module(path: Path) -> tuple[Any, str]:
    name = f"candidate_behavior_{abs(hash(path.read_bytes()))}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("module_load_failed")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module, name


def observe(module: Any, raw: bytes) -> dict[str, Any]:
    encoding = module.detect_encoding(iter(raw.splitlines(keepends=True)))
    if not isinstance(encoding, str):
        return {"encoding": None, "decoded_text": None, "error": "non_string_encoding"}
    try:
        return {
            "encoding": encoding,
            "decoded_text": raw.decode(encoding),
            "error": None,
        }
    except Exception as exc:
        return {
            "encoding": encoding,
            "decoded_text": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def select_fixtures(root: Path, limit: int) -> list[Path]:
    paths = sorted(
        path
        for path in root.rglob("*.txt")
        if path.is_file() and path.stat().st_size > 0
    )
    if len(paths) <= limit:
        return paths
    stride = max(1, len(paths) // limit)
    selected = paths[::stride][:limit]
    if paths[-1] not in selected:
        selected[-1] = paths[-1]
    return selected


def evaluate(
    module_path: Path,
    reference_path: Path,
    fixture_root: Path,
    fixture_limit: int,
) -> dict[str, Any]:
    candidate, candidate_name = load_module(module_path)
    reference, reference_name = load_module(reference_path)
    rows: list[dict[str, Any]] = []
    try:
        for path in select_fixtures(fixture_root, fixture_limit):
            raw = path.read_bytes()
            expected = observe(reference, raw)
            actual = observe(candidate, raw)
            rows.append(
                {
                    "fixture": str(path.relative_to(fixture_root)),
                    "bytes": len(raw),
                    "reference": expected,
                    "candidate": actual,
                    "pass": (
                        expected["error"] is None
                        and actual["error"] is None
                        and actual["decoded_text"] == expected["decoded_text"]
                    ),
                }
            )
    finally:
        sys.modules.pop(candidate_name, None)
        sys.modules.pop(reference_name, None)

    diagnostics = []
    for case_id, raw in (
        ("ascii_short", b"abc\n"),
        ("latin1_short", b"caf\xe9\n"),
        ("utf8_short", b"caf\xc3\xa9\n"),
    ):
        diagnostics.append(
            {
                "case_id": case_id,
                "reference": observe(reference, raw),
                "candidate": observe(candidate, raw),
            }
        )
    mismatches = [row["fixture"] for row in rows if not row["pass"]]
    return {
        "schema": "partridge_independent_behavior_contract_v2",
        "status": "PASS" if rows and not mismatches else "FAIL",
        "module_path": str(module_path),
        "reference_module_path": str(reference_path),
        "fixture_root": str(fixture_root),
        "fixture_count": len(rows),
        "mismatches": mismatches,
        "rows": rows,
        "short_input_environment_diagnostics": diagnostics,
        "nonclaims": [
            "The pass/fail contract compares candidate and parent decoded text on actual repository fixtures.",
            "Short-input detector differences are environment diagnostics and do not redefine the historical migration task.",
            "This channel is independent of the paired target-result intervention.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--reference-module", type=Path, required=True)
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--fixture-limit", type=int, default=24)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(
        args.module.resolve(),
        args.reference_module.resolve(),
        args.fixture_root.resolve(),
        args.fixture_limit,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
