#!/usr/bin/env python3
"""Create a manual, narrowly scoped skill repair from a source-only witness."""

import argparse
import hashlib
import json
from pathlib import Path


SKILL_SHA = "92f13d4cb7abbf334d4a837049222bea28638fd8d815a2f70fd590877d9900b9"
WITNESS_SHA = "c2fbb7788a18332d6e3e1900efa78606068ee3f6a17a9643460f1e3f4f66e1a2"


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError("expected exactly one skill passage: " + before[:80])
    return text.replace(before, after, 1)


def repair(text):
    old = """### 3. Patch metadata.json to Prevent Offline DB Download Failures
Trivy checks `DownloadedAt` + TTL to decide if a DB update is needed. Without network, this will fail. Patch far into the future:
```
# Edit /root/.cache/trivy/db/metadata.json
# Set NextUpdate to 2099-01-01
# Set DownloadedAt to a recent date
```"""
    new = """### 3. Preserve the Metadata of the Frozen Cache
Keep the copied metadata unchanged. For the tested Trivy 0.65.0 setup with a
fresh pre-populated local database, `--skip-db-update` completed an offline
source-task scan without changing its metadata. If that command fails in a
different environment, report the failure rather than inventing dates."""
    text = replace_once(text, old, new)
    text = replace_once(text, "trivy fs --scanners vuln --cache-dir /root/.cache/trivy --severity HIGH,CRITICAL",
                        "trivy fs --skip-db-update --scanners vuln --cache-dir /root/.cache/trivy --severity HIGH,CRITICAL")
    text = replace_once(text,
        "**CRITICAL: Do NOT use `--skip-db-update` on the first run — trivy rejects it before any successful DB load.**",
        "**The source-task test supports `--skip-db-update` for this frozen pre-populated cache; verify other setups.**")
    text = replace_once(text,
        "- `--skip-db-update` fails on first run — require at least one successful DB load first",
        "- `--skip-db-update` worked on the tested fresh pre-populated source cache; no general guarantee follows")
    text = replace_once(text,
        "- No network = no DB updates — always pre-populate cache and patch metadata.json with future dates",
        "- No network = no DB updates — preserve cache metadata and report a failed offline scan")
    text = replace_once(text,
        "Audit third-party dependencies for HIGH/CRITICAL vulnerabilities using trivy with a frozen local DB cache in an offline environment.",
        "Audit third-party dependencies for HIGH/CRITICAL vulnerabilities using trivy with a frozen local DB cache in an offline environment. "
        "This severity scope is from the earlier task; follow the current task when it differs.")
    return text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--witness", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    skill_bytes, witness_bytes = args.skill.read_bytes(), args.witness.read_bytes()
    if hashlib.sha256(skill_bytes).hexdigest() != SKILL_SHA or hashlib.sha256(witness_bytes).hexdigest() != WITNESS_SHA:
        raise ValueError("skill or source witness changed")
    witness = json.loads(witness_bytes)
    if not witness.get("supports_bounded_repair"):
        raise ValueError("source witness does not support the narrow repair")
    args.output.mkdir(parents=True, exist_ok=False)
    repaired = repair(skill_bytes.decode("utf-8")).encode("utf-8")
    (args.output / "experience_verified_v1.md").write_bytes(repaired)
    receipt = {"status": "MANUAL_RULE_DRIVEN_DEVELOPMENT_REPAIR", "original_skill_sha256": SKILL_SHA,
               "source_witness_sha256": WITNESS_SHA, "repaired_skill_sha256": hashlib.sha256(repaired).hexdigest(),
               "changes": ["remove future-date advice", "scope skip-db-update to tested cache",
                           "clarify source severity is overridden by current task"],
               "unverified_example_code_preserved": True, "model_calls": 0}
    (args.output / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
