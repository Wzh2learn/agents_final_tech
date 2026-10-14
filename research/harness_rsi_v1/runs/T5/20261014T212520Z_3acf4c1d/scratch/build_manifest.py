#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main() -> int:
    run_root = Path(__file__).resolve().parent.parent
    manifest_path = run_root / "artifacts_manifest.json"
    if manifest_path.exists():
        raise SystemExit("refuse to overwrite artifacts_manifest.json")
    artifacts = []
    for path in sorted(run_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(run_root)
        if relative == Path("artifacts_manifest.json") or "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        raw = path.read_bytes()
        artifacts.append(
            {
                "absolute_path": str(path),
                "relative_path": relative.as_posix(),
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "mode": format(path.stat().st_mode, "o"),
            }
        )
    document = {
        "schema": "artifacts_manifest_v2",
        "run_id": "20261014T212520Z_3acf4c1d",
        "root": str(run_root),
        "self_hash_policy": "artifacts_manifest.json does not self-hash",
        "hash_domain": "sha256_file_bytes_plus_mode",
        "required_executables": ["recipe_fixtures/dispatch/watcher.sh"],
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    with manifest_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
