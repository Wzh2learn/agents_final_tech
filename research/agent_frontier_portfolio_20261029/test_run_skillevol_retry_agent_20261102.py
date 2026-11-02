from pathlib import Path

import pytest

from run_skillevol_retry_agent_20261102 import derive


def test_derived_agent_does_not_mount_the_verifier_until_after_execution():
    root = Path(__file__).resolve().parents[2]
    base = root / "research/agent_skill_method_20261029/run_skill_episode_output8192.py"
    text = derive(base.read_text(encoding="utf-8"))
    agent_part, verifier_part = text.split("from qualify_skillevol_retry_20261102 import embedded_verifier", 1)
    assert "shutil.copytree(src/'environment',work/'task')" in agent_part
    assert "dst=/asset" not in agent_part and "src / \"solution\"" not in agent_part
    assert "dst=/asset,readonly" in verifier_part and "dst=/project,readonly" in verifier_part


def test_changed_harness_is_rejected():
    with pytest.raises(ValueError):
        derive("unexpected base")
