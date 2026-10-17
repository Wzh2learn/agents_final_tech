#!/usr/bin/env python3
"""Hash-guarded entrypoint for the frozen TQ-5 execution and analysis snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import runpy
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
MANIFEST_PATH = HERE / "SNAPSHOT_MANIFEST.json"
CONFIG_NAME = "chain_config_tq5_frozen.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(root: Path = HERE) -> dict:
    return json.loads((root / "SNAPSHOT_MANIFEST.json").read_text(encoding="utf-8"))


def verify_snapshot(root: Path = HERE) -> dict:
    manifest = load_manifest(root)
    failures = []
    for item in manifest["files"]:
        path = root / item["path"]
        if not path.is_file():
            failures.append({"path": item["path"], "error": "missing"})
            continue
        actual = sha256_file(path)
        if actual != item["sha256"]:
            failures.append({"path": item["path"], "expected": item["sha256"], "actual": actual})
    if failures:
        raise RuntimeError("snapshot verification failed: " + json.dumps(failures, ensure_ascii=True))
    return manifest


def option_value(args: list[str], name: str) -> str | None:
    if name not in args:
        return None
    index = args.index(name)
    if index + 1 >= len(args):
        raise ValueError(f"{name} requires a value")
    return args[index + 1]


def validate_invocation(stage: str, child_args: list[str], manifest: dict) -> None:
    config = option_value(child_args, "--config")
    expected_config = (HERE / CONFIG_NAME).resolve()
    if config is None or Path(config).resolve() != expected_config:
        raise ValueError("formal execution must use the frozen snapshot config")
    root = option_value(child_args, "--root")
    if root is None:
        raise ValueError("--root must be explicit")
    if stage in {"run", "analyze"} and root != manifest["execution_root"]:
        raise ValueError("run/analyze require the exact Linux execution_root override")
    if stage == "run" and "--run" not in child_args:
        raise ValueError("run stage requires --run")
    if stage == "run" and "--resume" in child_args:
        raise ValueError("first formal TQ-5 run cannot use --resume")
    if stage == "preflight" and not ("--plan" in child_args or "--check-pins" in child_args):
        raise ValueError("preflight stage requires --plan or --check-pins")
    if stage == "preflight" and ("--run" in child_args or "--resume" in child_args):
        raise ValueError("preflight cannot execute generation")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("preflight", "run", "analyze"), required=True)
    args, child_args = parser.parse_known_args()
    sys.dont_write_bytecode = True
    manifest = verify_snapshot()
    validate_invocation(args.stage, child_args, manifest)
    target = HERE / ("chain_analyze.py" if args.stage == "analyze" else "chain_runner.py")
    sys.argv = [str(target), *child_args]
    runpy.run_path(str(target), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
