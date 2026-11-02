import csv

import pytest

from prepare_dbscan_projection_20261102 import FIELDS, project


def test_projection_preserves_rows_and_excludes_unrelated_identifiers(tmp_path):
    source, target = tmp_path / "source.csv", tmp_path / "projection.csv"
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=[*FIELDS, "user_name", "user_ip"])
        writer.writeheader()
        writer.writerow({"file_rad": "image,one", "x": "1.25", "y": "2", "frame_file": "a.png",
                         "user_name": "SYNTHETIC-NAME", "user_ip": "SYNTHETIC-IP"})
        writer.writerow({"file_rad": "image,one", "x": "1.25", "y": "2", "frame_file": "a.png",
                         "user_name": "OTHER", "user_ip": "OTHER-IP"})
    receipt = project(source, target)
    with target.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        assert reader.fieldnames == list(FIELDS)
    assert len(rows) == receipt["rows"] == 2
    assert rows[0] == rows[1]
    assert rows[0]["file_rad"] == "image,one"
    assert "SYNTHETIC" not in target.read_text(encoding="utf-8")


def test_projection_rejects_duplicate_required_header(tmp_path):
    source, target = tmp_path / "source.csv", tmp_path / "projection.csv"
    source.write_text("file_rad,x,x,y,frame_file\na,1,2,3,a.png\n", encoding="utf-8")
    with pytest.raises(ValueError, match="required columns"):
        project(source, target)
