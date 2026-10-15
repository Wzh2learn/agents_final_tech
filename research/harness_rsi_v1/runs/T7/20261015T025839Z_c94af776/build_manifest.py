#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


RUN_ID = "20261015T025839Z_c94af776"
REPO_ROOT = Path("/home/testuser/wzh/projects/agents_final_tech").resolve()
RUN_ROOT = REPO_ROOT / "research/harness_rsi_v1/runs/T7" / RUN_ID


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    destination = RUN_ROOT / "artifacts_manifest.json"
    files = sorted(
        path
        for path in RUN_ROOT.rglob("*")
        if path.is_file()
        and path != destination
        and ".omc" not in path.parts
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )
    artifacts = []
    for path in files:
        mode = path.stat().st_mode & 0o777
        expected_mode = 0o755 if path.name in {"execute_t7.py", "self_check.py", "build_manifest.py"} else 0o644
        if mode != expected_mode:
            raise SystemExit(f"unexpected mode: {path} {oct(mode)} != {oct(expected_mode)}")
        artifacts.append(
            {
                "absolute_path": str(path),
                "relative_path": path.relative_to(RUN_ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256_file": sha256_file(path),
                "mode": f"100{mode:o}",
            }
        )
    manifest = {
        "schema": "jinrong_t7_artifacts_manifest_v1",
        "task_id": "T7",
        "run_id": RUN_ID,
        "artifact_count": len(artifacts),
        "self_hash_policy": "artifacts_manifest.json is excluded and does not self-hash",
        "mode_policy": {
            "t7_entry_scripts": ["execute_t7.py", "self_check.py", "build_manifest.py"],
            "t7_entry_scripts_mode": "100755",
            "all_other_files_mode": "100644",
            "rollback_parent_snapshot_note": "restored_parent/caller_validator.py preserves its accepted T5 source mode 0644 and is evidence, not an executable T7 entry script.",
            "git_delivery_note": "The closer will normalize all declared executable scripts to git mode 100755; no non-script file is declared executable.",
        },
        "artifacts": artifacts,
    }
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    os.chmod(destination, 0o644)
    print(json.dumps({"artifact_count": len(artifacts), "manifest": str(destination)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
