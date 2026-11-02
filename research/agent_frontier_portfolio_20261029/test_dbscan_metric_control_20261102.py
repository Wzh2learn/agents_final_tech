import pytest

from run_dbscan_metric_control_20261102 import OLD_COMMENT, ORIGINAL, adapt


def test_single_metric_change_is_explicit_and_reversible():
    source = OLD_COMMENT + "\n" + ORIGINAL
    changed = adapt(source)
    assert "metric='chebyshev'" in changed and "Standard Chebyshev" in changed
    assert changed.count("metric='chebyshev'") == 1


def test_unexpected_source_does_not_silently_change():
    with pytest.raises(ValueError):
        adapt(OLD_COMMENT + "\n" + ORIGINAL + "\n" + ORIGINAL)
