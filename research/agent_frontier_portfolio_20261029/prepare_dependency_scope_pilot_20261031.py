#!/usr/bin/env python3
"""Freeze two visible tasks and one experience-writing task for local Agents."""

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


EXPECTED_COMMIT = "726e1f79b96b0cb3d729d0e55a1c847e0b5353ae"
EXPECTED_ASSETS = {
    "lock": "a2a42a3255e814e75bed9958c40cd9b35de7331b310bfeb8f93306d806643d44",
    "archive": "e67dd9144e93897c5e2dbe4228e3444e4818130923e39389f32164a01bb62d0f",
    "db": "30478db8b8393e41e549ea5df7dff96e99e3c6de199b71f1a920527a23306e21",
    "binary": "a4708c81ab60f965c16bfbab52222ee5370a5a6ca16221e0947c0bbee9ca6ac9",
    "scan": "fb04b02db6381cf5ac2eedc4635148cba110627c6fcbcf96f8e694053d982095",
    "base": "4111a0be97845740769722e2e596871d51c7693d14d2372d7f6931b4d06e7afb",
}
NOTE = """
This is an offline research environment. The `trivy` executable is in PATH
and its frozen database is at `/root/trivy-cache`. The input file is already
in `/root`. Do not access the network or attempt to update the database.
"""
LEARN = """
Read `/root/previous_history.md`, which describes an earlier task, selected
tool events, its output and recorded evaluator feedback. Write a reusable
procedural skill to `/root/experience.md` in at most 4,000 characters.
Base the skill on what the history actually supports, including useful actions,
observed problems, any uncertainty and the conditions in which the advice is
applicable. Do not invent a later task, its answer or unseen results.
"""
LEARN_TEST = '''from pathlib import Path

def test_experience_file():
    path = Path('/root/experience.md')
    assert path.is_file()
    content = path.read_text(encoding='utf-8').strip()
    assert 0 < len(content) <= 4000
'''


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True,
                        help="SkillLearnBench checkout root")
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--native-skills", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    commit = subprocess.check_output(["git", "-C", str(args.upstream), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(args.upstream), "status", "--porcelain"], text=True)
    if commit != EXPECTED_COMMIT or dirty:
        raise ValueError("upstream checkout is not the frozen clean revision")
    root = args.upstream / "tasks/dependency-vulnerability-check"
    inputs = {"lock": root / "dependency-vulnerability-check-1/environment/package-lock.json",
              "archive": args.assets / "db.zip", "db": args.assets / "trivy-cache/db/trivy.db",
              "binary": args.assets / "trivy", "scan": args.assets / "scan/trivy-report.json",
              "base": args.base}
    for key, path in inputs.items():
        if sha(path) != EXPECTED_ASSETS[key]:
            raise ValueError("frozen asset changed: " + key)
    other_lock = root / "dependency-vulnerability-check-3/environment/package-lock.json"
    if sha(other_lock) != EXPECTED_ASSETS["lock"]:
        raise ValueError("target dependency input changed")
    args.output.mkdir(parents=True, exist_ok=False)
    tasks = args.output / "tasks"
    for name, number in (("dependency-scope-source", 1), ("dependency-scope-target", 3)):
        source = root / f"dependency-vulnerability-check-{number}"
        dest = tasks / name
        (dest / "verifier").mkdir(parents=True)
        instruction = (source / "instruction.md").read_text(encoding="utf-8")
        (dest / "task.md").write_text("---\nschema_version: '1.0'\n---\n" + instruction + NOTE, encoding="utf-8")
        shutil.copy2(source / "tests/test_outputs.py", dest / "verifier/test_outputs.py")
        if number == 3:
            shutil.copytree(args.native_skills, dest / "environment/skills")
    learning = tasks / "dependency-scope-learn"
    (learning / "verifier").mkdir(parents=True)
    (learning / "task.md").write_text("---\nschema_version: '1.0'\n---\n" + LEARN, encoding="utf-8")
    (learning / "verifier/test_outputs.py").write_text(LEARN_TEST, encoding="utf-8")
    manifest = {"status": "FROZEN_DEVELOPMENT_NOT_OFFICIAL_HARNESS", "upstream_commit": commit,
                "assets_sha256": EXPECTED_ASSETS, "tasks": {}}
    for path in sorted(tasks.rglob("*")):
        if path.is_file():
            manifest["tasks"][str(path.relative_to(tasks)).replace("\\", "/")] = sha(path)
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "frozen_files": len(manifest["tasks"])}))


if __name__ == "__main__":
    main()
