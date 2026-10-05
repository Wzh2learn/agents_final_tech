from __future__ import annotations

import argparse
import configparser
import csv
import io
import json
import zipfile
from pathlib import Path
from typing import Any
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.audit_remote_zip_structure import RangeReader, RemoteZipError


def _json_schema(value: Any) -> dict[str, object]:
    if isinstance(value, dict):
        return {
            "type": "object",
            "keys": {key: _json_schema(item) for key, item in value.items()},
        }
    if isinstance(value, list):
        item_schemas = [_json_schema(item) for item in value[:8]]
        unique_schemas = {json.dumps(item, sort_keys=True) for item in item_schemas}
        return {
            "type": "array",
            "length": len(value),
            "item_schemas": [json.loads(item) for item in sorted(unique_schemas)],
        }
    return {"type": type(value).__name__}


def _inspect_json(raw: bytes) -> dict[str, object]:
    value = json.loads(raw.decode("utf-8"))
    return {"format": "json", "structure_only": True, "schema": _json_schema(value)}


def _inspect_csv(raw: bytes) -> dict[str, object]:
    text = raw.decode("utf-8-sig", errors="strict")
    reader = csv.reader(io.StringIO(text, newline=""))
    rows = list(reader)
    if not rows:
        raise RemoteZipError("empty_csv_entry")
    header = rows[0]
    return {
        "format": "csv",
        "columns": header,
        "column_count": len(header),
        "row_count_excluding_header": max(0, len(rows) - 1),
        "sample_values_disclosed": False,
    }


def _inspect_ini(raw: bytes) -> dict[str, object]:
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(raw.decode("utf-8"))
    return {
        "format": "ini",
        "sections": {
            section: sorted(parser[section].keys())
            for section in parser.sections()
        },
        "values_disclosed": False,
    }


def _inspect_entry(archive: zipfile.ZipFile, filename: str) -> dict[str, object]:
    info = archive.getinfo(filename)
    if info.file_size > 8 * 1024 * 1024:
        raise RemoteZipError("entry_schema_size_exceeded", filename=filename, file_size=info.file_size)
    raw = archive.read(filename)
    suffix = Path(filename).suffix.lower()
    if suffix == ".json":
        return _inspect_json(raw)
    if suffix == ".csv":
        return _inspect_csv(raw)
    if suffix == ".ini":
        return _inspect_ini(raw)
    raise RemoteZipError("unsupported_schema_entry", filename=filename)


def inspect_pairs(
    url: str,
    archive_size: int,
    pair_prefixes: list[str],
    *,
    block_size: int,
    max_fetch_bytes: int,
    range_retries: int,
) -> dict[str, object]:
    reader = RangeReader(
        url,
        archive_size,
        block_size=block_size,
        max_fetch_bytes=max_fetch_bytes,
        range_retries=range_retries,
    )
    pair_reports: dict[str, object] = {}
    with zipfile.ZipFile(reader) as archive:
        names = set(archive.namelist())
        for prefix in pair_prefixes:
            leaf = Path(prefix).name
            candidates = [
                f"{prefix}_source.csv",
                f"{prefix}_source.json",
                f"{prefix}_target.csv",
                f"{prefix}_target.json",
                f"{prefix}_mapping.json",
                f"{str(Path(prefix).parent)}/config_{leaf}.ini",
            ]
            present = [name for name in candidates if name in names]
            pair_reports[prefix] = {
                "files": {
                    Path(name).name: {
                        "entry_size": archive.getinfo(name).file_size,
                        "structure": _inspect_entry(archive, name),
                    }
                    for name in present
                },
                "missing_optional_files": [Path(name).name for name in candidates if name not in names],
            }
    return {
        "record_type": "remote_zip_schema_inspection",
        "record_version": "remote-zip-schema-inspection-v1",
        "status": "PASS_STRUCTURE_ONLY",
        "source": {"url": url, "archive_size": archive_size},
        "transport": {
            "mode": "HTTP_RANGE_ONLY",
            "block_size": block_size,
            "max_fetch_bytes": max_fetch_bytes,
            "fetched_bytes": reader.fetched_bytes,
            "range_requests": reader.request_count,
            "range_retries": reader.retry_count,
            "retry_error_types": reader.retry_errors,
            "full_archive_downloaded": False,
        },
        "ground_truth_use": "STRUCTURE_ONLY_NO_VALUES_DISCLOSED_NO_ACTION_TARGET_GENERATION",
        "adapter_run": False,
        "pairs": pair_reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect selected remote ZIP entry schemas without disclosing row or mapping values")
    parser.add_argument("--url", required=True)
    parser.add_argument("--size", required=True, type=int)
    parser.add_argument("--pair-prefix", action="append", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--block-size", type=int, default=256 * 1024)
    parser.add_argument("--max-fetch-mib", type=int, default=8)
    parser.add_argument("--range-retries", type=int, default=3)
    args = parser.parse_args()

    report = inspect_pairs(
        args.url,
        args.size,
        args.pair_prefix,
        block_size=args.block_size,
        max_fetch_bytes=args.max_fetch_mib * 1024 * 1024,
        range_retries=args.range_retries,
    )
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "pairs": len(report["pairs"]),
        "transport": report["transport"],
        "ground_truth_use": report["ground_truth_use"],
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
