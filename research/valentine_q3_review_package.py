"""Build a deterministic Valentine Q3 review package without gold visibility.

The package contains only source headers, target-table canonical headers, stable
lineage identifiers, and carrier input templates.  The builder never opens
ground_truth.json and never reads table rows.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
APPROVED_PAIRS = (
    "City_Government__Capital_Projects",
    "City_Government__DCM_StreetCenterLine",
    "City_Government__DPR_AthleticFacilities_001",
    "City_Government__DSNY_Districts_With_Disposal_Vendor_Assignments",
    "City_Government__NYC_Municipal_Building_Energy_Benchmarking_Results",
    "Education__COVID-19_Free_Meals_Locations",
    "Housing_&_Development__Housing_Maintenance_Code_Complaints_and_Problems",
    "Housing_&_Development__Public_Design_Commission_Outdoor_Public_Art_Invent",
    "Recreation__Swim_for_Life__2016_to_2020",
    "Transportation__DOT_In-house_Street_Resurfacing_Projects",
)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.phase1a_data_contract import lineage_uid

ALLOWED_HEADER_FILES = {"source_table.csv", "target_table.csv"}
FORBIDDEN_GOLD_NAME = "ground_truth.json"
ALLOWED_PAIR_FILES = ALLOWED_HEADER_FILES | {FORBIDDEN_GOLD_NAME}
DATA_PREFIX = "valentine/experiments/data/"
TEMPLATE_VERSION = "label-review-v1"
GENERATOR_ID = "valentine_q3_package_builder-v1"


class PackageBuildError(ValueError):
    def __init__(self, code: str, **detail: object) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_sha256_manifest(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise PackageBuildError("missing_sha256_manifest", path=str(path))
    rows: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relpath = line.split(None, 1)
        if relpath in rows:
            raise PackageBuildError("duplicate_sha256_manifest_path", path=relpath)
        rows[relpath] = digest
    return rows


def _assert_manifest_hash(rows: dict[str, str], relpath: str, actual: str) -> None:
    expected = rows.get(relpath)
    if expected is None:
        raise PackageBuildError("missing_sha256_manifest_entry", path=relpath)
    if expected != actual:
        raise PackageBuildError("sha256_manifest_mismatch", path=relpath, expected=expected, actual=actual)


def _read_csv_header(path: Path) -> tuple[list[str], str]:
    if path.name not in ALLOWED_HEADER_FILES:
        raise PackageBuildError("forbidden_header_file", path=str(path))
    csv.field_size_limit(sys.maxsize)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
    if not header or any(not isinstance(value, str) for value in header):
        raise PackageBuildError("invalid_csv_header", path=str(path))
    return header, _sha256_file(path)


def _validate_input_tree(staging_root: Path) -> list[Path]:
    data_root = staging_root / "valentine" / "experiments" / "data"
    if not data_root.is_dir() or data_root.is_symlink():
        raise PackageBuildError("missing_valentine_data_root", path=str(data_root))
    entries = list(data_root.iterdir())
    non_dirs = sorted(item.name for item in entries if not item.is_dir() or item.is_symlink())
    if non_dirs:
        raise PackageBuildError("unexpected_data_root_entry", entries=non_dirs)
    actual_pairs = {item.name for item in entries}
    expected_pairs = set(APPROVED_PAIRS)
    if actual_pairs != expected_pairs:
        raise PackageBuildError(
            "pair_directory_allowlist_mismatch",
            missing=sorted(expected_pairs - actual_pairs),
            extra=sorted(actual_pairs - expected_pairs),
        )
    for pair_name in APPROVED_PAIRS:
        pair_dir = data_root / pair_name
        pair_entries = list(pair_dir.iterdir())
        invalid = sorted(item.name for item in pair_entries if not item.is_file() or item.is_symlink())
        if invalid:
            raise PackageBuildError("unexpected_pair_entry_type", pair=pair_name, entries=invalid)
        actual_files = {item.name for item in pair_entries}
        if actual_files != ALLOWED_PAIR_FILES:
            raise PackageBuildError(
                "pair_file_allowlist_mismatch",
                pair=pair_name,
                missing=sorted(ALLOWED_PAIR_FILES - actual_files),
                extra=sorted(actual_files - ALLOWED_PAIR_FILES),
            )
    return [data_root / pair_name for pair_name in APPROVED_PAIRS]


def _validate_manifest_scope(rows: dict[str, str]) -> None:
    expected = {
        f"{DATA_PREFIX}{pair_name}/{file_name}"
        for pair_name in APPROVED_PAIRS
        for file_name in ALLOWED_PAIR_FILES
    }
    actual = {relpath for relpath in rows if relpath.startswith(DATA_PREFIX)}
    if actual != expected:
        raise PackageBuildError(
            "input_manifest_scope_mismatch",
            missing=sorted(expected - actual),
            extra=sorted(actual - expected),
        )


def _validate_output_dir(out_dir: Path, staging_root: Path) -> None:
    if not out_dir.is_absolute():
        raise PackageBuildError("output_path_not_absolute", path=str(out_dir))
    if out_dir.is_symlink():
        raise PackageBuildError("output_path_is_symlink", path=str(out_dir))
    resolved = out_dir.resolve(strict=False)
    temp_root = Path(tempfile.gettempdir()).resolve()
    if resolved == temp_root or not resolved.is_relative_to(temp_root):
        raise PackageBuildError("output_path_outside_temp", path=str(resolved), temp_root=str(temp_root))
    for label, anchor in (("staging", staging_root.resolve()), ("repo", REPO.resolve())):
        if resolved == anchor or resolved.is_relative_to(anchor) or anchor.is_relative_to(resolved):
            raise PackageBuildError("output_path_conflicts_with_input", kind=label, path=str(resolved))
    if out_dir.exists():
        if not out_dir.is_dir() or out_dir.is_symlink():
            raise PackageBuildError("output_path_not_directory", path=str(out_dir))
        entries = list(out_dir.iterdir())
        if entries:
            raise PackageBuildError(
                "output_dir_not_empty",
                entries=sorted(item.name for item in entries),
                has_nested_directory=any(item.is_dir() for item in entries),
            )
        return
    parent = out_dir.parent
    if not parent.is_dir() or parent.is_symlink():
        raise PackageBuildError("output_parent_invalid", path=str(parent))
    out_dir.mkdir()


def _sample_id(dataset_id: str, dataset_revision: str, pair_id: str, col: int) -> str:
    identity = {
        "dataset_id": dataset_id,
        "dataset_revision": dataset_revision,
        "lineage_root_id": pair_id,
        "column_index": col,
    }
    return _sha256_bytes(_stable_json(identity).encode("utf-8"))


def _packet(carrier_id: str, samples: list[dict], reference: dict, reference_sha: str) -> dict:
    return {
        "carrier_id": carrier_id,
        "template_version": TEMPLATE_VERSION,
        "dataset_id": "valentine_nyc",
        "reference_excerpt_path": "package://canonical_reference.json",
        "reference_excerpt_sha256": reference_sha,
        "canonical_reference": reference,
        "samples": samples,
        "forbidden_inputs": ["ground_truth.json", "pipeline_mapping", "injection_map", "other_carrier_judgments"],
    }


def _prompt(carrier_id: str, block_no: int, count: int) -> str:
    return (
        "你是独立复核载体 " + carrier_id + "。仅依据输入包中每个样本的源表原表头、"
        "canonical 参考摘录与判定语义给出唯一判定；禁止参考 ground_truth.json、"
        "管线映射、注入信息、其他载体的判定或任何可见性/检出数字。\n"
        "判定语义：map_to = 该列应映射到 canonical 参考摘录中的某字段（给出 target）；"
        "skip = 无对应 canonical 字段；hold = 信息不足需人工保留。\n"
        "输出 JSON：{\"reviewer_id\": \"" + carrier_id + "\", "
        "\"template_version\": \"" + TEMPLATE_VERSION + "\", \"judgments\": "
        "[{\"sample_id\":..., \"uid\":..., \"col\":..., \"action\":..., \"target\":...}]}。\n"
        "本块样本数 = " + str(count) + "，块号 = " + str(block_no) + "。\n"
    )


def build(staging_root: Path, dataset_revision: str, out_dir: Path, chunk_size: int = 50) -> dict:
    if not isinstance(dataset_revision, str) or not dataset_revision.strip():
        raise PackageBuildError("missing_dataset_revision")
    if type(chunk_size) is not int or chunk_size <= 0:
        raise PackageBuildError("invalid_chunk_size", value=chunk_size)
    manifest_rows = _load_sha256_manifest(staging_root / "sha256_manifest.txt")
    manifest_sha = _sha256_file(staging_root / "sha256_manifest.txt")
    _validate_manifest_scope(manifest_rows)

    dirs = _validate_input_tree(staging_root)
    pairs: dict[str, dict] = {}
    samples: list[dict] = []
    input_files: list[str] = []
    forbidden_present = 0
    for pair_dir in dirs:
        pair_id = pair_dir.name
        source_path = pair_dir / "source_table.csv"
        target_path = pair_dir / "target_table.csv"
        gold_path = pair_dir / FORBIDDEN_GOLD_NAME
        if gold_path.exists():
            forbidden_present += 1
        source_header, source_sha = _read_csv_header(source_path)
        target_header, target_sha = _read_csv_header(target_path)
        source_rel = f"valentine/experiments/data/{pair_id}/source_table.csv"
        target_rel = f"valentine/experiments/data/{pair_id}/target_table.csv"
        _assert_manifest_hash(manifest_rows, source_rel, source_sha)
        _assert_manifest_hash(manifest_rows, target_rel, target_sha)
        if len(set(source_header)) != len(source_header):
            raise PackageBuildError("duplicate_source_header", pair=pair_id)
        if len(set(target_header)) != len(target_header):
            raise PackageBuildError("duplicate_target_header", pair=pair_id)
        uid = lineage_uid("valentine_nyc", dataset_revision, pair_id)
        pairs[pair_id] = {
            "lineage_root_id": pair_id,
            "uid": uid,
            "source_header": source_header,
            "target_header": target_header,
            "source_sha256": source_sha,
            "target_sha256": target_sha,
        }
        input_files.extend([
            source_rel,
            target_rel,
        ])
        for col, header in enumerate(source_header):
            samples.append({
                "sample_id": _sample_id("valentine_nyc", dataset_revision, pair_id, col),
                "uid": uid,
                "col": col,
                "lineage_root_id": pair_id,
                "source_header": header,
                "target_headers": target_header,
                "source_file_sha256": source_sha,
                "target_file_sha256": target_sha,
            })

    if len(pairs) != 10:
        raise PackageBuildError("expected_ten_pairs", actual=len(pairs))
    if len(samples) != 146:
        raise PackageBuildError("expected_146_source_columns", actual=len(samples))
    _validate_output_dir(out_dir, staging_root)

    reference = {
        pair_id: pairs[pair_id]["target_header"]
        for pair_id in sorted(pairs)
    }
    reference_sha = _sha256_bytes(_stable_json(reference).encode("utf-8"))

    chunks = [samples[i:i + chunk_size] for i in range(0, len(samples), chunk_size)]
    manifest_files: list[dict] = []
    for index, block in enumerate(chunks, start=1):
        block_suffix = f"block_{index:03d}"
        for carrier_id in ("R1", "R2"):
            payload = _packet(carrier_id, block, reference, reference_sha)
            path = out_dir / f"{carrier_id.lower()}_{block_suffix}.json"
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8", newline="\n")
            prompt_path = out_dir / f"{carrier_id.lower()}_{block_suffix}.prompt.md"
            prompt_path.write_text(_prompt(carrier_id, index, len(block)), encoding="utf-8", newline="\n")
            manifest_files.extend([
                {"path": path.name, "sha256": _sha256_file(path), "bytes": path.stat().st_size},
                {"path": prompt_path.name, "sha256": _sha256_file(prompt_path), "bytes": prompt_path.stat().st_size},
            ])
        adjudication_path = out_dir / f"adjudication_{block_suffix}.json"
        adjudication_path.write_text(json.dumps({
            "adjudicator_id": "ADJ",
            "template_version": TEMPLATE_VERSION,
            "entries": [
                {"sample_id": sample["sample_id"], "uid": sample["uid"], "col": sample["col"],
                 "action": None, "target": None, "rationale_ref": ""}
                for sample in block
            ],
            "forbidden_inputs": ["ground_truth.json", "pipeline_mapping", "injection_map"],
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        manifest_files.append({"path": adjudication_path.name,
                               "sha256": _sha256_file(adjudication_path),
                               "bytes": adjudication_path.stat().st_size})

    samples_path = out_dir / "samples.jsonl"
    samples_path.write_text("".join(_stable_json(row) + "\n" for row in samples),
                            encoding="utf-8", newline="\n")
    canonical_path = out_dir / "canonical_reference.json"
    canonical_path.write_text(json.dumps(reference, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8", newline="\n")
    manifest_files.extend([
        {"path": samples_path.name, "sha256": _sha256_file(samples_path), "bytes": samples_path.stat().st_size},
        {"path": canonical_path.name, "sha256": _sha256_file(canonical_path), "bytes": canonical_path.stat().st_size},
    ])
    manifest = {
        "generator_id": GENERATOR_ID,
        "template_version": TEMPLATE_VERSION,
        "dataset_id": "valentine_nyc",
        "dataset_revision": dataset_revision,
        "sha256_manifest_sha256": manifest_sha,
        "sha256_manifest_entries": len(manifest_rows),
        "pair_count": len(pairs),
        "sample_count": len(samples),
        "target_header_count": sum(len(value["target_header"]) for value in pairs.values()),
        "chunk_size": chunk_size,
        "chunk_sizes": [len(block) for block in chunks],
        "reference_excerpt_sha256": reference_sha,
        "input_files_read": sorted(input_files),
        "sha256_manifest_path": "sha256_manifest.txt",
        "forbidden_files_present": forbidden_present,
        "forbidden_files_read": [],
        "forbidden_open_count": 0,
        "visibility_contract": {
            "R1": ["source_header", "canonical_reference", "label_semantics"],
            "R2": ["source_header", "canonical_reference", "label_semantics"],
            "ADJ": ["R1/R2 disagreements", "source_header", "canonical_reference"],
            "forbidden": ["ground_truth.json", "pipeline_mapping", "injection_map", "other_carrier_judgments"],
        },
        "files": sorted(manifest_files, key=lambda item: item["path"]),
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8", newline="\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging-root", required=True, type=Path)
    parser.add_argument("--dataset-revision", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--chunk-size", type=int, default=50)
    args = parser.parse_args()
    manifest = build(args.staging_root, args.dataset_revision, args.out, args.chunk_size)
    print(json.dumps({
        "pair_count": manifest["pair_count"],
        "sample_count": manifest["sample_count"],
        "chunk_sizes": manifest["chunk_sizes"],
        "reference_excerpt_sha256": manifest["reference_excerpt_sha256"],
        "sha256_manifest_sha256": manifest["sha256_manifest_sha256"],
        "manifest_sha256": _sha256_file(args.out / "manifest.json"),
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
