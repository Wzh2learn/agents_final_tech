import json
from pathlib import Path


def test_model_visible_contract_is_explicit():
    tasks = json.loads((Path(__file__).parent / "TASKS.json").read_text(encoding="utf-8"))["tasks"]
    assert len(tasks) == 6
    for task in tasks:
        plan_prompt = task["plan"]["prompt"]
        assert all(key in plan_prompt for key in ("action", "arguments", "reason_code"))
        assert "Do not use a key named tool" in plan_prompt
        assert task["plan"]["expected"]["action"] in plan_prompt
        consume_prompt = task["consume"]["prompt"]
        assert all(key in consume_prompt for key in ("status", "facts", "evidence_ids"))
        assert task["consume"]["expected"]["status"] in consume_prompt
        assert all(evidence_id in consume_prompt for evidence_id in task["consume"]["evidence_ids"])
