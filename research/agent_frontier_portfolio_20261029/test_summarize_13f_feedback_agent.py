import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research.agent_frontier_portfolio_20261029.run_13f_feedback_agent import CONDITIONS, history_message
from research.agent_frontier_portfolio_20261029.summarize_13f_feedback_agent import summarize


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class FeedbackAgentSummaryTest(unittest.TestCase):
    def test_binds_history_and_raw_to_every_condition(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive_digest = hashlib.sha256(b"data").hexdigest()
            put(root / "manifest.json", {"archive_sha256_raw": archive_digest})
            history = {"previous_count": 1, "source_raw_sha256": hashlib.sha256(b"raw").hexdigest(),
                       "contract_checker": {"verdict": "accepted", "expected": 1},
                       "upstream_checker": {"verdict": "rejected", "expected": 2}}
            put(root / "agent_history.json", history)
            history_digest = hashlib.sha256((root / "agent_history.json").read_bytes()).hexdigest()
            for condition in CONDITIONS:
                task = "financial-feedback-t1" if condition == "source" else "financial-feedback-t2"
                case = root / "agent_runs" / (task + "__no_skill__" + condition)
                (case / "work").mkdir(parents=True)
                (case / "work/13f_q3.zip").write_bytes(b"data")
                (case / "raw.jsonl").write_bytes(b"raw")
                put(case / "work/count.json", {"count": 1})
                put(root / "tasks" / task / "verifier/expected.json", {"count": 1})
                put(case / "intervention.json", {"condition": condition, "task": task,
                    "task_assets": {"expected_sha256": hashlib.sha256((root / "tasks" / task / "verifier/expected.json").read_bytes()).hexdigest()},
                    "history_sha256": None if condition in ("source", "no_history") else history_digest,
                    "history_message": history_message(condition, history)})
                put(case / "receipt.json", {"raw_sha256": hashlib.sha256(b"raw").hexdigest(),
                    "agent_exit": 0, "verifier_exit": 0, "model_http_requests": [],
                    "step_finish_tokens": [], "post_content_lengths": [], "elapsed_seconds": 1})
            result = summarize(root)
            self.assertTrue(result["previous_checker_conflict"])
            self.assertTrue(all(c["correct_under_explicit_contract"] for c in result["cases"].values()))
            (root / "agent_history.json").write_text('{}')
            with self.assertRaises(ValueError):
                summarize(root)


if __name__ == "__main__":
    unittest.main()
