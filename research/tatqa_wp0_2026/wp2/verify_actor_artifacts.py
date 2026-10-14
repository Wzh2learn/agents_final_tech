#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[3]
METADATA_PATH = ROOT / "docs/datasets/2026-10-05_qwen_model_metadata_v1.json"
VALIDATION_RECEIPT_PATH = ROOT / (
    "docs/datasets/2026-10-05_qwen3_8b_artifact_validation_receipt_v1.json"
)
SYNC_RECEIPT_PATH = ROOT / (
    "docs/datasets/2026-10-05_qwen3_8b_sync_receipt_v1.json"
)
OUTPUT_PATH = ROOT / (
    "research/tatqa_wp0_2026/wp2/ACTOR_ARTIFACT_VERIFICATION_RECEIPT.json"
)
MODEL_ID = "Qwen/Qwen3-8B"
REVISION = "b968826d9c46dd6066d109eabc6255188de91218"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_blob_sha1(path: Path) -> str:
    digest = hashlib.sha1()
    digest.update(f"blob {path.stat().st_size}\0".encode("ascii"))
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def model_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    matches = [row for row in metadata["models"] if row.get("id") == MODEL_ID]
    require(len(matches) == 1, f"expected exactly one metadata row for {MODEL_ID}")
    model = dict(matches[0])
    require(
        model.get("revision") == REVISION,
        "Qwen3-8B metadata revision mismatch",
    )
    require(
        model.get("license") == "apache-2.0",
        "Qwen3-8B licence mismatch",
    )
    return model


def runtime_environment() -> dict[str, Any]:
    cpu_model = None
    cpuinfo = Path("/proc/cpuinfo").read_text(encoding="utf-8", errors="replace")
    for line in cpuinfo.splitlines():
        if line.lower().startswith("model name"):
            cpu_model = line.split(":", 1)[1].strip()
            break
    gpu_command = ["nvidia-smi", "--query-gpu=name,driver_version,utilization.gpu"]
    gpu_command += ["--format=csv,noheader"]
    require(
        shutil.which("nvidia-smi") is not None,
        "nvidia-smi is unavailable on the execution host",
    )
    gpu_result = subprocess.run(
        gpu_command,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    import torch

    return {
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "implementation": platform.python_implementation(),
        },
        "torch": {
            "version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_version": torch.version.cuda,
        },
        "os": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "kernel": platform.release(),
        },
        "cpu": {
            "logical_count": os.cpu_count(),
            "model_name": cpu_model,
        },
        "gpu": {
            "query": " ".join(gpu_command),
            "raw_csv": gpu_result.stdout.strip().splitlines(),
            "fb_memory_note": (
                "GB10 unified memory reports FB memory as N/A; "
                "runtime memory gates use host available memory"
            ),
        },
    }


def main() -> int:
    metadata = load_json(METADATA_PATH)
    validation = load_json(VALIDATION_RECEIPT_PATH)
    sync_receipt = load_json(SYNC_RECEIPT_PATH)
    model = model_metadata(metadata)
    model_root = Path(model["planned_cache_path"])
    require(model_root.is_dir(), "Qwen3-8B model directory is absent")

    validation_hashes = {
        row["name"]: row for row in validation["files"]
    }
    require(
        validation.get("revision") == REVISION,
        "artifact validation revision mismatch",
    )
    require(
        validation.get("model_id") == MODEL_ID,
        "artifact validation model id mismatch",
    )
    require(
        sync_receipt.get("revision") == REVISION,
        "sync receipt revision mismatch",
    )
    require(
        sync_receipt.get("model_id") == MODEL_ID,
        "sync receipt model id mismatch",
    )
    require(
        sha256_file(VALIDATION_RECEIPT_PATH)
        == model["download_receipt"]["artifact_validation_receipt_sha256"],
        "artifact validation receipt hash mismatch",
    )
    require(
        sha256_file(SYNC_RECEIPT_PATH)
        == model["download_receipt"]["sync_receipt_sha256"],
        "sync receipt hash mismatch",
    )

    expected_names = sorted(row["name"] for row in model["files"])
    actual_names = sorted(
        path.name
        for path in model_root.iterdir()
        if path.is_file()
    )
    require(
        actual_names == expected_names,
        f"top-level model file set mismatch: expected {expected_names}, "
        f"found {actual_names}",
    )

    files: list[dict[str, Any]] = []
    for expected in sorted(model["files"], key=lambda row: row["name"]):
        name = expected["name"]
        path = model_root / name
        require(path.is_file(), f"missing model artifact: {name}")
        actual_bytes = path.stat().st_size
        require(
            actual_bytes == expected["bytes"],
            f"size mismatch for {name}",
        )
        actual_sha256 = sha256_file(path)
        validation_expected = validation_hashes[name]["content_sha256"]
        require(
            actual_sha256 == validation_expected,
            f"content SHA-256 mismatch for {name}",
        )
        identity: dict[str, Any] = {
            "content_sha256": actual_sha256,
            "bytes": actual_bytes,
        }
        if expected["lfs_sha256"] is None:
            actual_blob = git_blob_sha1(path)
            require(
                actual_blob == expected["git_blob_sha1"],
                f"git blob SHA-1 mismatch for {name}",
            )
            identity["git_blob_sha1"] = actual_blob
        else:
            require(
                actual_sha256 == expected["lfs_sha256"],
                f"LFS SHA-256 mismatch for {name}",
            )
            identity["lfs_sha256"] = actual_sha256
        files.append({"name": name, "status": "PASS", **identity})

    receipt = {
        "schema": "tatqa_wp2_actor_artifact_verification_receipt_v1",
        "task": "tatqa-wp2-s4s7-20261014",
        "status": "PASS",
        "generated_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "actor": {
            "model_id": MODEL_ID,
            "revision": REVISION,
            "license": model["license"],
            "model_root": str(model_root),
            "revision_identity_source": (
                "pinned metadata and mirror receipts; the local model root "
                "does not contain a VCS ref"
            ),
        },
        "inputs": {
            "metadata": {
                "path": str(METADATA_PATH.relative_to(ROOT)),
                "sha256": sha256_file(METADATA_PATH),
            },
            "artifact_validation_receipt": {
                "path": str(VALIDATION_RECEIPT_PATH.relative_to(ROOT)),
                "sha256": sha256_file(VALIDATION_RECEIPT_PATH),
            },
            "sync_receipt": {
                "path": str(SYNC_RECEIPT_PATH.relative_to(ROOT)),
                "sha256": sha256_file(SYNC_RECEIPT_PATH),
            },
        },
        "checks": {
            "top_level_file_count": len(files),
            "metadata_file_count": model["file_count"],
            "all_file_sizes_match": True,
            "all_content_sha256_match": True,
            "all_identity_hashes_match": True,
            "all_shards_present": len(
                [row for row in files if row["name"].endswith(".safetensors")]
            )
            == 5,
            "tokenizer_artifacts_verified": all(
                name in {row["name"] for row in files}
                for name in ("tokenizer.json", "tokenizer_config.json", "vocab.json")
            ),
        },
        "environment": runtime_environment(),
        "safety": {
            "network_calls": 0,
            "model_load_started": False,
            "judge_calls": 0,
            "database_calls": 0,
            "production_service_calls": 0,
        },
    }
    require(receipt["checks"]["top_level_file_count"] == 15, "file count is not 15")
    OUTPUT_PATH.write_bytes(canonical_bytes(receipt))
    print(
        "ACTOR_ARTIFACT_VERIFICATION_PASS "
        f"files={len(files)} revision={REVISION} "
        f"output_sha256={sha256_file(OUTPUT_PATH)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
