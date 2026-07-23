#!/usr/bin/env python3
"""Download-plan and integrity checks for the official TAT-DQA Drive package.

Raw files and all validation output belong under ``/home/testuser/wzh/datasets``.
This module intentionally makes one request per file: a quota, network, or access
failure is reported to the caller instead of being hidden by automatic retries.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import requests


OFFICIAL_FOLDER_URL = "https://drive.google.com/drive/folders/1SGpZyRWqycMd_dZim1ygvWhl5KdJYDR2"
OFFICIAL_PROJECT_URL = "https://nextplusplus.github.io/TAT-DQA/"
LICENSE = "CC BY 4.0"
DEFAULT_DATA_ROOT = Path("/home/testuser/wzh/datasets/tat-dqa")


@dataclass(frozen=True)
class PackageFile:
    name: str
    drive_id: str
    expected_bytes: int


# Sizes are the byte counts published by the official Drive folder on 2026-07-22.
PACKAGE_FILES = (
    PackageFile("tatdqa_dataset_dev.json", "1dmXKledPa6ptXuFibUCtoJMEP6oCD60N", 1_210_555),
    PackageFile("tatdqa_dataset_test_gold.json", "1ZQjjIC0BB14l6t9b1Ryq0t-CNAP6iC2J", 1_229_595),
    PackageFile("tatdqa_dataset_test.json", "1Dqvlu83R4t5odayhtt65qwFkxHWmieOr", 351_652),
    PackageFile("tatdqa_dataset_train.json", "1FQUbZRlJKB-1sbvZ_HiZtE5isNwSvjki", 9_722_633),
    PackageFile("tatdqa_docs_dev.zip", "1M1CtHAS4SzFFnNVsFVGgpaGq84mEzPcR", 155_773_433),
    PackageFile("tatdqa_docs_test.zip", "1iqe5r-qgQZLhGtM4G6LkNp9S6OCwOF2L", 173_931_848),
    PackageFile("tatdqa_docs_train.zip", "1VX4U0wx4ojITs72d5FAKvNJMkL5J6Xdw", 1_172_553_879),
)


def expected_package_bytes(files: Iterable[PackageFile] = PACKAGE_FILES) -> int:
    return sum(item.expected_bytes for item in files)


def package_plan(data_root: Path) -> dict[str, object]:
    free_bytes = shutil.disk_usage(data_root.parent if data_root.parent.exists() else data_root).free
    expected = expected_package_bytes()
    return {
        "dataset": "TAT-DQA",
        "license": LICENSE,
        "official_folder_url": OFFICIAL_FOLDER_URL,
        "official_project_url": OFFICIAL_PROJECT_URL,
        "data_root": str(data_root),
        "expected_archive_bytes": expected,
        "expected_archive_gib": round(expected / 1024**3, 3),
        "available_bytes": free_bytes,
        "available_gib": round(free_bytes / 1024**3, 3),
        "files": [asdict(item) for item in PACKAGE_FILES],
    }


def _download_url(drive_id: str) -> str:
    return f"https://drive.usercontent.google.com/download?id={drive_id}&export=download&confirm=t"


def download_package(data_root: Path) -> dict[str, object]:
    """Download the official package once per invocation, resuming valid partials."""
    plan = package_plan(data_root)
    if plan["available_bytes"] < plan["expected_archive_bytes"]:
        raise RuntimeError(
            "insufficient disk space: "
            f"need {plan['expected_archive_bytes']} bytes, have {plan['available_bytes']} bytes"
        )

    raw_dir = data_root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    with requests.Session() as session:
        for item in PACKAGE_FILES:
            destination = raw_dir / item.name
            if destination.exists() and destination.stat().st_size == item.expected_bytes:
                results.append({"name": item.name, "status": "already_present", "bytes": item.expected_bytes})
                continue
            partial = destination.with_suffix(destination.suffix + ".part")
            partial_bytes = partial.stat().st_size if partial.exists() else 0
            if partial_bytes > item.expected_bytes:
                partial_bytes = 0
            headers = {"Range": f"bytes={partial_bytes}-"} if partial_bytes else None
            response = session.get(
                _download_url(item.drive_id),
                stream=True,
                timeout=(15, 120),
                headers=headers,
            )
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type.lower():
                raise RuntimeError(f"download blocked for {item.name}: received HTML instead of file content")
            digest = hashlib.sha256()
            resumed = bool(partial_bytes and response.status_code == 206)
            if resumed:
                content_range = response.headers.get("Content-Range", "")
                if not content_range.startswith(f"bytes {partial_bytes}-"):
                    raise RuntimeError(
                        f"invalid resume response for {item.name}: {content_range!r}"
                    )
                with partial.open("rb") as existing:
                    for chunk in iter(lambda: existing.read(1024 * 1024), b""):
                        digest.update(chunk)
                received = partial_bytes
                mode = "ab"
            else:
                received = 0
                mode = "wb"
            with partial.open(mode) as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
                        digest.update(chunk)
                        received += len(chunk)
            if received != item.expected_bytes:
                raise RuntimeError(
                    f"download size mismatch for {item.name}: expected {item.expected_bytes}, received {received}"
                )
            partial.replace(destination)
            results.append({
                "name": item.name,
                "status": "resumed" if resumed else "downloaded",
                "bytes": received,
                "sha256": digest.hexdigest(),
            })
    return {"plan": plan, "downloads": results}


def validate_package(data_root: Path) -> dict[str, object]:
    """Validate sizes, JSON parsing, and ZIP CRCs without extracting public data."""
    raw_dir = data_root / "raw"
    checks: list[dict[str, object]] = []
    for item in PACKAGE_FILES:
        path = raw_dir / item.name
        if not path.is_file():
            raise FileNotFoundError(f"missing expected official file: {path}")
        actual = path.stat().st_size
        if actual != item.expected_bytes:
            raise ValueError(f"size mismatch for {item.name}: expected {item.expected_bytes}, got {actual}")
        check: dict[str, object] = {"name": item.name, "bytes": actual, "sha256": _sha256(path)}
        if path.suffix == ".json":
            with path.open(encoding="utf-8") as handle:
                parsed = json.load(handle)
            check["json_top_level"] = type(parsed).__name__
            check["json_records"] = len(parsed) if hasattr(parsed, "__len__") else None
        elif path.suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                bad_member = archive.testzip()
                if bad_member is not None:
                    raise ValueError(f"CRC failure in {item.name}: {bad_member}")
                check["zip_members"] = len(archive.infolist())
        checks.append(check)
    return {
        "dataset": "TAT-DQA",
        "license": LICENSE,
        "expected_archive_bytes": expected_package_bytes(),
        "files": checks,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "download", "validate"))
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--status-out", type=Path, help="Optional external JSON status path.")
    args = parser.parse_args()
    try:
        if args.command == "plan":
            result = package_plan(args.data_root)
        elif args.command == "download":
            result = download_package(args.data_root)
        else:
            result = validate_package(args.data_root)
    except (OSError, requests.RequestException, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        result = {"status": "blocked", "command": args.command, "error_type": type(exc).__name__, "error": str(exc)}
        if args.status_out:
            args.status_out.parent.mkdir(parents=True, exist_ok=True)
            args.status_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    if args.status_out:
        args.status_out.parent.mkdir(parents=True, exist_ok=True)
        args.status_out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
