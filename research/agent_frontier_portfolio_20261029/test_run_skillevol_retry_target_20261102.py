from pathlib import Path

from run_skillevol_retry_target_20261102 import derive


def test_target_history_is_added_only_to_the_history_condition():
    root = Path(__file__).resolve().parents[2]
    base = (root / "research/agent_skill_method_20261029/run_skill_episode_output8192.py").read_text(encoding="utf-8")
    plain = derive(base, "no_history")
    history = derive(base, "source_program_plus_feedback")
    assert "retry-masks-auth-expiry-trap" in plain and "RETRY_SOURCE_PROJECT" not in plain
    assert "prior_feedback.txt" in history and "RETRY_SOURCE_PROJECT" in history
    agent_part, _ = history.split("from qualify_skillevol_retry_20261102 import embedded_verifier", 1)
    assert "dst=/asset" not in agent_part
