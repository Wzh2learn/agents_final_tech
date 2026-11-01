"""Check scientific attribution in the document-centered backup draft."""

import collections
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKUP = Path(__file__).resolve().parent / "paper_e_icdar_working.md"


def test_family_counts_match_frozen_injections():
    data = json.loads((ROOT / "logs/graph/eval/checkpoint_discrimination_tables_v2.json").read_text(encoding="utf-8"))
    rows = [row for table in data["tables"] for row in table["injections"]]
    actual = collections.defaultdict(lambda: [0, 0])
    for row in rows:
        actual[row["type"]][0] += bool(row["visible"])
        actual[row["type"]][1] += 1
    text = BACKUP.read_text(encoding="utf-8")
    assert len(rows) == 118
    for key, label in (("alias_variant", "alias variants"), ("date_variant", "date variants"),
                       ("mixed_lang", "mixed-language variants"), ("ocr_similar", "OCR-like variants"),
                       ("prefix_noise", "prefix-noise variants"), ("unit_suffix", "unit-suffix variants")):
        visible, total = actual[key]
        assert f"{visible}/{total} {label}" in text


def test_backup_preserves_corrected_map_and_document_scope():
    text = BACKUP.read_text(encoding="utf-8")
    assert "TF-IDF's MAP@10 from approximately 0.2200 to 0.1162" in text
    assert "not page-image OCR outputs" in text
    assert "without a page-image recognition experiment" in text
    assert "not establish a universally validated audit method" in text
