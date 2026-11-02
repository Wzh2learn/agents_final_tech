import json
from pathlib import Path

import pytest

import run_dbscan_agent_pilot_20261102 as pilot


def test_agent_gate_requires_unchanged_projection_and_both_reference_proofs(tmp_path, monkeypatch):
    projection = tmp_path / "projection" / "data"
    projection.mkdir(parents=True)
    source_hashes = {"a.csv": "source-a", "b.csv": "source-b"}
    projected_hashes = {}
    for name in source_hashes:
        path = projection / name
        path.write_text("file_rad,x,y,frame_file\nimage,1,2,image.png\n", encoding="utf-8")
        projected_hashes[name] = pilot.sha(path)
    monkeypatch.setattr(pilot, "DATA", source_hashes)
    monkeypatch.setattr(pilot, "PROJECTED_DATA", projected_hashes)
    monkeypatch.setattr(pilot, "SOURCES", {1: "source-1", 2: "source-2"})
    expected = {}
    for version in (1, 2):
        folder = tmp_path / "proofs" / f"task{version}"
        (folder / "work").mkdir(parents=True)
        (folder / "work/pareto_frontier.csv").write_text(f"result-{version}\n", encoding="utf-8")
        (folder / "verifier.stdout").write_text("8 passed\n", encoding="utf-8")
        expected[version] = pilot.sha(folder / "work/pareto_frontier.csv")
    monkeypatch.setattr(pilot, "EXPECTED", expected)
    manifest = {"fields": pilot.PROJECTION_FIELDS,
                "files": {name: {"source_sha256": source_hashes[name], "projection_sha256": digest,
                                 "row_order_and_selected_values_equal": True}
                          for name, digest in projected_hashes.items()}}
    (projection.parent / "receipt.json").write_text(json.dumps(manifest), encoding="utf-8")
    for version in (1, 2):
        folder = tmp_path / "proofs" / f"task{version}"
        receipt = {"task": version, "source_sha256": pilot.SOURCES[version],
                   "runner_sha256": pilot.sha(Path(pilot.reference_runner.__file__).resolve()),
                   "expected_sha256": expected[version], "test_sha256": pilot.TEST_HASH,
                   "image": pilot.IMAGE, "data_source": "four_column_projection",
                   "data_sha256": projected_hashes, "original_data_sha256": source_hashes,
                   "solver": {"exit_code": 0},
                   "verifier": {"exit_code": 0, "stdout_sha256": pilot.sha(folder / "verifier.stdout")},
                   "output_sha256": expected[version]}
        (folder / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
    proofs = tmp_path / "proofs"
    assert set(pilot.verify_projection(projection, proofs)["reference_runs"]) == {"1", "2"}

    (projection / "a.csv").write_text("file_rad,x,y,frame_file,user_name\n", encoding="utf-8")
    with pytest.raises(ValueError, match="projected dataset changed"):
        pilot.verify_projection(projection, proofs)

    (projection / "a.csv").write_text("file_rad,x,y,frame_file\nimage,1,2,image.png\n", encoding="utf-8")
    receipt_path = proofs / "task2/receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["data_source"] = "original_source"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="compatibility proof invalid"):
        pilot.verify_projection(projection, proofs)
