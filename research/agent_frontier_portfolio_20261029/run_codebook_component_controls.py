#!/usr/bin/env python3
"""Post-hoc, model-free replays of one saved agent program in network-free containers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


FIND_COMPONENTS = "re.findall(r'[A-Z]+[\\d]+', seg_lower)"
FIND_COMPONENTS_FIXED = "re.findall(r'[A-Z]+[\\d]+', raw_segment.upper())"
FIND_FULL_SIGNAL = "re.findall(r'[A-Z][A-Z0-9_]*\\d[A-Z0-9_]*', raw_segment.upper())"
FIND_KEYWORD = "re.search(r'[A-Z]+[\\d]+', kw)"
FIND_KEYWORD_FIXED = "re.search(r'[A-Z]+[\\d]+', kw.upper())"
SUBSTRING = "if cr_upper in kw_upper or kw_upper in cr_upper:"
EXACT = "if cr_upper == kw_upper:"


def make_source(source, condition):
    if condition == "original_replay":
        return source
    edits = [(FIND_COMPONENTS, FIND_COMPONENTS_FIXED), (FIND_KEYWORD, FIND_KEYWORD_FIXED)]
    if condition in ("case_exact", "case_signal_exact"):
        edits.append((SUBSTRING, EXACT))
    elif condition != "case_substring":
        raise ValueError(condition)
    if condition == "case_signal_exact":
        edits.append((FIND_COMPONENTS_FIXED, FIND_FULL_SIGNAL))
    for before, after in edits:
        if source.count(before) != 1:
            raise ValueError("unexpected source fragment: " + before)
        source = source.replace(before, after)
    compile(source, "normalize.py", "exec")
    return source


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_logged(cmd, log, timeout, container_name):
    start = time.monotonic()
    with log.open("wb") as out:
        try:
            result = subprocess.run(cmd, stdout=out, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL, timeout=timeout)
            status = result.returncode
        except subprocess.TimeoutExpired:
            status = 124
            subprocess.run(["docker", "kill", container_name], stdout=out, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL, timeout=15, check=False)
    return {"exit": status, "seconds": round(time.monotonic() - start, 3)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("original_work", type=Path)
    parser.add_argument("source_task", type=Path)
    parser.add_argument("deps", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    src = (args.original_work / "normalize.py").read_text(encoding="utf-8")
    # Validate all transformations before creating any outputs or starting runs.
    variants = {mode: make_source(src, mode) for mode in ("original_replay", "case_substring", "case_exact", "case_signal_exact")}
    args.output.mkdir(parents=True, exist_ok=False)
    receipts = {}
    for mode, source in variants.items():
        case = args.output / mode
        work = case / "work"
        work.mkdir(parents=True)
        work.chmod(0o777)
        shutil.copytree(args.source_task / "environment/data", work / "data")
        for original in sorted((args.source_task / "environment/data").glob("*.csv")):
            if sha(original) != sha(work / "data" / original.name):
                raise ValueError("input copy hash mismatch: " + original.name)
        (work / "output").mkdir()
        (work / "output").chmod(0o777)
        (work / "normalize.py").write_text(source, encoding="utf-8", newline="\n")
        script_sha = sha(work / "normalize.py")
        (case / "prepared.json").write_text(json.dumps({"condition": mode, "script_sha256": script_sha,
                                                        "original_sha256": sha(args.original_work / "normalize.py")}, indent=2), encoding="utf-8")
        common = ["docker", "run", "--rm", "--pull", "never", "--network", "none", "--read-only", "--cpus", "1", "--memory", "2g", "--pids-limit", "128", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,size=128m", "--mount", f"type=bind,src={work},dst=/app", "--workdir", "/app"]
        run_name = f"codebook-component-{mode}-{os.getpid()}"
        verify_name = run_name + "-verify"
        run = run_logged(common + ["--name", run_name, "python:3.12-slim", "python", "/app/normalize.py"], case / "run.log", 300, run_name)
        verify = common + ["--name", verify_name, "-e", "PYTHONPATH=/deps", "-e", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1", "--mount", f"type=bind,src={args.deps},dst=/deps,readonly", "--mount", f"type=bind,src={args.source_task / 'verifier'},dst=/verifier,readonly", "python:3.12-slim", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "/verifier/test_outputs.py"]
        scored = run_logged(verify, case / "verifier.txt", 180, verify_name)
        output = work / "output/solution.json"
        receipts[mode] = {"run": run, "verify": scored, "script_sha256": script_sha,
                          "output_sha256": sha(output) if output.exists() else None}
        (args.output / "receipt.json").write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({mode: receipts[mode]}), flush=True)


if __name__ == "__main__":
    main()
