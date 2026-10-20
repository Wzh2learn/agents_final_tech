from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/ma_cerd_gold_public_v1.jsonl"
MANIFEST = ROOT / "SHA256SUMS.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    rows = [json.loads(line) for line in DATA.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1000, "expected 1,000 records"
    assert len({row["contract_id"] for row in rows}) == 1000, "contract IDs must be unique"
    assert {row["release_status"] for row in rows} == {"gold"}, "all records must be Gold"
    assert Counter(row["labels"]["relation"] for row in rows) == {"change": 685, "invariant": 315}
    for row in rows:
        nodes = {node["node_id"] for node in row["base_snapshot"]["joint_plan"]["nodes"]}
        impact = set(row["labels"]["impact_node_ids"])
        preserved = set(row["labels"]["preserved_node_ids"])
        assert not impact & preserved and impact | preserved == nodes
        judgment = row["oracle_bundle"]["independent_judgment"]
        assert judgment["status"] == "adjudicated" and judgment["reviewer_count"] >= 2
        assert "source_response_audit_sha256" not in judgment
        assert row["oracle_bundle"]["simulator_outcome"]["execution_mode"] == "simulator_only_shadow_mode"
    text = DATA.read_text(encoding="utf-8")
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    assert not re.search(r"(?:[A-Za-z]:[\\/]|Users[\\/])", text, re.IGNORECASE)
    family_partitions = {}
    for row in rows:
        family_partitions.setdefault(row["family_id"], set()).add(row["partition"])
    assert all(len(partitions) == 1 for partitions in family_partitions.values()), "family leakage detected"
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    for relative, expected in manifest["files"].items():
        assert sha256(ROOT / relative) == expected, f"hash mismatch: {relative}"
    print("PASS: 1,000 public Gold records, privacy boundaries, splits, and SHA-256 manifest validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
