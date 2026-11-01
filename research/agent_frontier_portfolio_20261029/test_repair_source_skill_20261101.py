import pytest

from repair_source_skill_20261101 import replace_once


def test_repair_rejects_missing_or_ambiguous_evidence_passage():
    assert replace_once("prefix old suffix", "old", "new") == "prefix new suffix"
    with pytest.raises(ValueError):
        replace_once("no anchor", "old", "new")
    with pytest.raises(ValueError):
        replace_once("old old", "old", "new")
