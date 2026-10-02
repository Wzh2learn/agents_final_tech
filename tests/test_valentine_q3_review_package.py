from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from research.valentine_q3_review_package import PackageBuildError, build
from research.valentine_q3_review_package import APPROVED_PAIRS
from research.valentine_q3_review_package import DATA_PREFIX

SOURCE_COUNTS = [15] * 9 + [11]
REVISION = "5d5163f04da304985bd51a476ccf7653de3979c3"
EXPECTED_PAIRS = (
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


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_staging(root: Path) -> Path:
    staging = root / "staging"
    data_root = staging / "valentine" / "experiments" / "data"
    data_root.mkdir(parents=True)
    manifest_rows: list[str] = []
    for pair_index, (pair_name, source_count) in enumerate(zip(EXPECTED_PAIRS, SOURCE_COUNTS)):
        pair = data_root / pair_name
        pair.mkdir()
        source = pair / "source_table.csv"
        target = pair / "target_table.csv"
        gold = pair / "ground_truth.json"
        source.write_text(
            ",".join(f"src_{pair_index}_{col}" for col in range(source_count)) + "\nrow\n",
            encoding="utf-8",
            newline="\n",
        )
        target.write_text(
            "target_a,target_b\nrow,row\n",
            encoding="utf-8",
            newline="\n",
        )
        gold.write_text("{\"matches\": []}\n", encoding="utf-8", newline="\n")
        for path in (source, target, gold):
            relpath = path.relative_to(staging).as_posix()
            manifest_rows.append(f"{_sha256(path)}  {relpath}")
    (staging / "sha256_manifest.txt").write_text("\n".join(manifest_rows) + "\n",
                                                 encoding="utf-8", newline="\n")
    return staging


def test_builds_contract_shaped_package_without_opening_gold(monkeypatch: pytest.MonkeyPatch,
                                                             tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    opened: list[str] = []
    original_open = Path.open

    def tracking_open(self: Path, *args, **kwargs):
        if self.name == "ground_truth.json":
            opened.append(self.name)
            raise AssertionError("ground_truth.json must not be opened")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", tracking_open)
    manifest = build(staging, REVISION, tmp_path / "out1")

    assert opened == []
    assert manifest["pair_count"] == 10
    assert manifest["sample_count"] == 146
    assert manifest["target_header_count"] == 20
    assert manifest["chunk_sizes"] == [50, 50, 46]
    assert manifest["forbidden_files_present"] == 10
    assert manifest["forbidden_files_read"] == []
    assert manifest["forbidden_open_count"] == 0
    assert len(manifest["input_files_read"]) == 20
    assert all(not item.endswith("ground_truth.json") for item in manifest["input_files_read"])

    samples = [json.loads(line) for line in (tmp_path / "out1" / "samples.jsonl").read_text().splitlines()]
    assert len(samples) == 146
    assert {sample["col"] for sample in samples if sample["lineage_root_id"] == EXPECTED_PAIRS[0]} == set(range(15))
    assert all(len(sample["target_headers"]) == 2 for sample in samples)
    assert all(sample["source_header"].startswith("src_") for sample in samples)


def test_double_build_is_byte_identical(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    first = tmp_path / "out1"
    second = tmp_path / "out2"
    build(staging, REVISION, first)
    build(staging, REVISION, second)

    for name in ("manifest.json", "samples.jsonl", "canonical_reference.json",
                 "r1_block_001.json", "r2_block_003.json", "adjudication_block_002.json"):
        assert (first / name).read_bytes() == (second / name).read_bytes(), name


def test_manifest_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    manifest_path = staging / "sha256_manifest.txt"
    text = manifest_path.read_text(encoding="utf-8")
    manifest_path.write_text(text.replace(text.splitlines()[0][:8], "0" * 8, 1),
                             encoding="utf-8", newline="\n")
    with pytest.raises(PackageBuildError) as exc:
        build(staging, REVISION, tmp_path / "out")
    assert exc.value.code == "sha256_manifest_mismatch"


def test_chunk_size_is_validated(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    with pytest.raises(PackageBuildError) as exc:
        build(staging, REVISION, tmp_path / "out", chunk_size=0)
    assert exc.value.code == "invalid_chunk_size"


def test_direct_script_entry_does_not_depend_on_pythonpath() -> None:
    repo = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    proc = subprocess.run([
        sys.executable,
        str(repo / "research" / "valentine_q3_review_package.py"),
        "--help",
    ], cwd=repo, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "--dataset-revision" in proc.stdout


def test_duplicate_headers_fail_closed(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    source = staging / "valentine" / "experiments" / "data" / EXPECTED_PAIRS[0] / "source_table.csv"
    source.write_text("same,same\nrow,row\n", encoding="utf-8", newline="\n")
    rows = (staging / "sha256_manifest.txt").read_text(encoding="utf-8").splitlines()
    relpath = source.relative_to(staging).as_posix()
    rows = [(_sha256(source) + "  " + relpath if line.endswith(relpath) else line) for line in rows]
    (staging / "sha256_manifest.txt").write_text("\n".join(rows) + "\n",
                                                 encoding="utf-8", newline="\n")
    with pytest.raises(PackageBuildError) as exc:
        build(staging, REVISION, tmp_path / "out")
    assert exc.value.code == "duplicate_source_header"


def test_approved_pair_allowlist_is_exact() -> None:
    assert APPROVED_PAIRS == EXPECTED_PAIRS


def test_nonempty_output_dir_fails_and_preserves_existing_file(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    sentinel = out / "sentinel.txt"
    sentinel.write_text("keep", encoding="utf-8")

    with pytest.raises(PackageBuildError) as exc:
        build(staging, REVISION, out)

    assert exc.value.code == "output_dir_not_empty"
    assert sentinel.read_text(encoding="utf-8") == "keep"


def test_nested_output_entry_fails(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    out = tmp_path / "out"
    (out / "nested").mkdir(parents=True)

    with pytest.raises(PackageBuildError) as exc:
        build(staging, REVISION, out)

    assert exc.value.code == "output_dir_not_empty"
    assert exc.value.detail["has_nested_directory"] is True


def test_empty_output_dir_is_accepted(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    out = tmp_path / "out"
    out.mkdir()

    manifest = build(staging, REVISION, out)

    assert manifest["sample_count"] == 146


def test_output_inside_staging_fails_without_creation(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    out = staging / "out"

    with pytest.raises(PackageBuildError) as exc:
        build(staging, REVISION, out)

    assert exc.value.code == "output_path_conflicts_with_input"
    assert not out.exists()


def test_output_temp_root_fails(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    with pytest.raises(PackageBuildError) as exc:
        build(staging, REVISION, Path(tempfile.gettempdir()))

    assert exc.value.code == "output_path_outside_temp"


def test_extra_pair_directory_fails(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    (staging / "valentine" / "experiments" / "data" / "extra_pair").mkdir()

    with pytest.raises(PackageBuildError) as exc:
        build(staging, REVISION, tmp_path / "out")

    assert exc.value.code == "pair_directory_allowlist_mismatch"
    assert exc.value.detail["extra"] == ["extra_pair"]


def test_extra_pair_file_fails(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    extra = staging / "valentine" / "experiments" / "data" / EXPECTED_PAIRS[0] / "extra.json"
    extra.write_text("{}\n", encoding="utf-8")

    with pytest.raises(PackageBuildError) as exc:
        build(staging, REVISION, tmp_path / "out")

    assert exc.value.code == "pair_file_allowlist_mismatch"
    assert exc.value.detail["extra"] == ["extra.json"]


def test_extra_dataset_entry_at_data_root_fails(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    extra = staging / "valentine" / "experiments" / "data" / "other_dataset.csv"
    extra.write_text("header\n", encoding="utf-8")

    with pytest.raises(PackageBuildError) as exc:
        build(staging, REVISION, tmp_path / "out")

    assert exc.value.code == "unexpected_data_root_entry"
    assert exc.value.detail["entries"] == ["other_dataset.csv"]


def test_manifest_extra_data_entry_fails(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    manifest = staging / "sha256_manifest.txt"
    manifest.write_text(manifest.read_text(encoding="utf-8") + f"{'0' * 64}  {DATA_PREFIX}extra/file.csv\n", encoding="utf-8", newline="\n")

    with pytest.raises(PackageBuildError) as exc:
        build(staging, REVISION, tmp_path / "out")

    assert exc.value.code == "input_manifest_scope_mismatch"
    assert exc.value.detail["extra"] == [f"{DATA_PREFIX}extra/file.csv"]
