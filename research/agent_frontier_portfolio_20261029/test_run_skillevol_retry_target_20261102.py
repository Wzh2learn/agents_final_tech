import hashlib
from pathlib import Path

from run_skillevol_retry_target_20261102 import derive


def test_target_history_is_added_only_to_the_history_condition():
    root = Path(__file__).resolve().parents[2]
    base = (root / "research/agent_skill_method_20261029/run_skill_episode_output8192.py").read_text(encoding="utf-8")
    plain = derive(base, "no_history")
    history = derive(base, "source_program_plus_feedback")
    required = derive(base, "source_program_required")
    assert "retry-masks-auth-expiry-trap" in plain and "RETRY_SOURCE_PROJECT" not in plain
    assert "prior_feedback.txt" in history and "RETRY_SOURCE_PROJECT" in history
    agent_part, _ = history.split("from qualify_skillevol_retry_20261102 import embedded_verifier", 1)
    assert "dst=/asset" not in agent_part
    required_agent, _ = required.split("from qualify_skillevol_retry_20261102 import embedded_verifier", 1)
    assert "use the read tool to inspect" in required_agent
    assert all(name in required_agent for name in ("prior_instructions.txt", "prior_retry_client.py", "prior_policy.py", "prior_feedback.txt"))
    assert "source_program_required" in required_agent and "dst=/asset" not in required_agent
    # Older conditions must retain their exact frozen derived program hashes.
    assert hashlib.sha256(plain.encode()).hexdigest() == "a6dfee45fa6a6eaa3e228f6546f9d4f2c5fbf6e9593c5269a93db5dd058f384e"
    assert hashlib.sha256(history.encode()).hexdigest() == "675521ced843f917640b201ee27c198296b2077308d2de43acd861ecabba3b1d"
