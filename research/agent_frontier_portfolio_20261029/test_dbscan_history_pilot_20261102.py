import pytest

from run_dbscan_history_pilot_20261102 import add_history


def test_history_only_changes_the_declared_episode_inputs_and_label():
    base = ("case=ROOT/(task+'__'+arm+'__'+str(os.getpid()))\n"
            "(work/'data').mkdir()\n"
            "Use available tools to implement and execute your solution.\n"
            "receipt={'task':task,'arm':arm")
    changed = add_history(base)
    assert "prior_source_code" in changed
    assert "prior_solution.py" in changed and "prior_instructions.txt" in changed
    assert "follow the current task instructions" in changed


def test_ambiguous_base_is_rejected():
    with pytest.raises(ValueError):
        add_history("unexpected runner")
