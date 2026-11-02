from pathlib import Path

from run_retry_feedback_controls_20261102 import FEEDBACK, derive


def test_conditions_start_from_same_project_and_receive_distinct_feedback():
    root = Path(__file__).resolve().parents[2]
    base = root / "research/agent_skill_method_20261029/run_skill_episode_output8192.py"
    text = derive(base.read_text(encoding="utf-8"))
    assert "RETRY_SOURCE_PROJECT" in text and "RETRY_FEEDBACK" in text
    assert "ignore_patterns('__pycache__','*.pyc')" in text
    assert len(set(FEEDBACK.values())) == 3
    assert "9/9" not in FEEDBACK["diagnostic"] and "9/9" in FEEDBACK["diagnostic_plus_behavior"]
