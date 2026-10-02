from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.valentine_q3_review_package import PackageBuildError, build

SOURCE_COUNTS = [15] * 9 + [11]
REVISION = "5d5163f04da304985bd51a476ccf7653de3979c3"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_staging(root: Path) -> Path:
    staging = root / "staging"
    data_root = staging / "valentine" / "experiments" / "data"
    data_root.mkdir(parents=True)
    manifest_rows: list[str] = []
    for pair_index, source_count in enumerate(SOURCE_COUNTS):
        pair = data_root / f"pair_{pair_index:02d}"
        pair.mkdir()
        source = pair / "source_table.csv"
        target = pair / "target_table.csv"
        gold = pair / "ground_truth.json"
        source.write_text(
            "source_" + ",".join(f"src_{pair_index}_{col}" for col in range(source_count)) + "\nrow\n",
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
    assert {sample["col"] for sample in samples if sample["lineage_root_id"] == "pair_00"} == set(range(15))
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


def test_duplicate_headers_fail_closed(tmp_path: Path) -> None:
    staging = _make_staging(tmp_path)
    source = staging / "valentine" / "experiments" / "data" / "pair_00" / "source_table.csv"
    source.write_text("same,same\nrow,row\n", encoding="utf-8", newline="\n")
    rows = (staging / "sha256_manifest.txt").read_text(encoding="utf-8").splitlines()
    relpath = source.relative_to(staging).as_posix()
    rows = [(_sha256(source) + "  " + relpath if line.endswith(relpath) else line) for line in rows]
    (staging / "sha256_manifest.txt").write_text("\n".join(rows) + "\n",
                                                 encoding="utf-8", newline="\n")
    with pytest.raises(PackageBuildError) as exc:
        build(staging, REVISION, tmp_path / "out")
    assert exc.value.code == "duplicate_source_header"
