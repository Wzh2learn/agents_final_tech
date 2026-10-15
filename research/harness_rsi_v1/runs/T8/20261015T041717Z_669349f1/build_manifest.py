#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat


RUN_ROOT = Path(__file__).resolve().parent
REPO_ROOT = RUN_ROOT.parents[4]
MANIFEST = RUN_ROOT / "artifacts_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    artifacts = []
    for path in sorted(item for item in RUN_ROOT.rglob("*") if item.is_file()):
        if path == MANIFEST or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        artifacts.append(
            {
                "absolute_path": str(path),
                "bytes": path.stat().st_size,
                "mode": "100755" if stat.S_IMODE(path.stat().st_mode) & 0o111 else "100644",
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "relative_path": path.relative_to(RUN_ROOT).as_posix(),
                "sha256": sha256_file(path),
            }
        )
    payload = {
        "schema": "jinrong_t8_artifacts_manifest_v1",
        "run_id": RUN_ROOT.name,
        "task_id": "T8",
        "self_hash_policy": "artifacts_manifest.json is excluded and does not self-hash",
        "artifact_count": len(artifacts),
        "mode_policy": "DELIVERY_FULL_SET_755",
        "artifacts": artifacts,
    }
    MANIFEST.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.chmod(MANIFEST, 0o755)
    print(json.dumps({"artifact_count": len(artifacts), "manifest": str(MANIFEST)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
