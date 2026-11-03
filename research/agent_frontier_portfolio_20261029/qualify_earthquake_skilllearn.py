#!/usr/bin/env python3
"""Offline qualification of a SkillLearnBench geospatial development sequence.

Runs the released Pacific reference and a transparent Africa adaptation in
separate network-free containers, and mounts each upstream test only after
the corresponding program has exited. This is not an official benchmark run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


ROOT = Path("/home/testuser/wzh/research_evidence/agent_learning_20261030")
UPSTREAM = ROOT / "SkillLearnBench/tasks/earthquake-plate-calculation"
OUT = ROOT / "earthquake_geo_qualification_20261103"
DEPS = OUT / "deps"
IMAGE = "python:3.12-slim"
FILES = ("earthquakes_2024.json", "PB2002_boundaries.json", "PB2002_plates.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, *, timeout=300):
    start = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout,
                                stdin=subprocess.DEVNULL, check=False)
        return {"exit_code": result.returncode, "stdout": result.stdout,
                "stderr": result.stderr, "wall_seconds": time.monotonic() - start}
    except subprocess.TimeoutExpired as exc:
        text = lambda value: value.decode("utf-8", errors="replace") if isinstance(value, bytes) else (value or "")
        return {"exit_code": 124, "stdout": text(exc.stdout), "stderr": text(exc.stderr),
                "wall_seconds": time.monotonic() - start}


def docker_base(work, *, work_readonly=False):
    return ["docker", "run", "--rm", "--pull", "never", "--network", "none", "--read-only",
            "--cpus", "2", "--memory", "2g", "--pids-limit", "128", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--user", f"{os.getuid()}:{os.getgid()}",
            "--tmpfs", "/tmp:rw,nosuid,size=128m", "-e", "PYTHONPATH=/deps",
            "--mount", f"type=bind,src={DEPS},dst=/deps,readonly",
            "--mount", f"type=bind,src={work},dst=/root" + (",readonly" if work_readonly else ""),
            "--workdir", "/root"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projection-controls", action="store_true")
    args = parser.parse_args()
    tasks = {n: UPSTREAM / f"earthquake-plate-calculation-{n}" for n in (1, 3)}
    for filename in FILES:
        if sha(tasks[1] / "environment" / filename) != sha(tasks[3] / "environment" / filename):
            raise ValueError(f"shared-source assumption failed: {filename}")
    source = tasks[1] / "solution/solution.py"
    other = tasks[3] / "solution/solution.py"
    if sha(source) != sha(other):
        raise ValueError("upstream reference programs are not identical")
    code = source.read_text(encoding="utf-8")
    replacements = {
        'gdf_plates["PlateName"] == "Pacific"': 'gdf_plates["PlateName"] == "Africa"',
        'gdf_boundaries["Name"].str.contains("PA")': 'gdf_boundaries["Name"].str.contains("AF")',
    }
    for old, new in replacements.items():
        if code.count(old) != 1:
            raise ValueError(f"reference fragment changed: {old}")
        code = code.replace(old, new)
    image = subprocess.check_output(["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"], text=True).strip()
    if image != "sha256:364db321fcc720859537bc04fab5c06a3be6ad0c87686a380b015a0d36c232ca":
        raise ValueError("unexpected local base image")
    if args.projection_controls:
        root = OUT / "projection_controls"
        root.mkdir(exist_ok=False)
        controls = {}
        for crs in ("EPSG:4087", "EPSG:6933", "EPSG:8857"):
            if code.count('METRIC_CRS = "EPSG:4087"') != 1:
                raise ValueError("unexpected projection declaration")
            program = code.replace('METRIC_CRS = "EPSG:4087"', f'METRIC_CRS = "{crs}"')
            case = root / crs.replace(":", "_")
            work = case / "work"
            work.mkdir(parents=True)
            code_path = case / "program.py"
            code_path.write_text(program, encoding="utf-8")
            cmd = docker_base(work)
            for filename in FILES:
                cmd += ["--mount", f"type=bind,src={tasks[3] / 'environment' / filename},dst=/root/{filename},readonly"]
            cmd += ["--mount", f"type=bind,src={code_path},dst=/code/program.py,readonly",
                    IMAGE, "python", "/code/program.py"]
            execution = run(cmd)
            (case / "program.stdout").write_text(execution.pop("stdout"), encoding="utf-8")
            (case / "program.stderr").write_text(execution.pop("stderr"), encoding="utf-8")
            test_file = tasks[3] / "tests/test_outputs.py"
            verify = docker_base(work, work_readonly=True) + [
                "--mount", f"type=bind,src={test_file},dst=/verify/test_outputs.py,readonly",
                IMAGE, "python", "/verify/test_outputs.py"]
            verification = run(verify)
            (case / "verify.stdout").write_text(verification.pop("stdout"), encoding="utf-8")
            (case / "verify.stderr").write_text(verification.pop("stderr"), encoding="utf-8")
            answer_path = work / "answer.json"
            answer = json.loads(answer_path.read_text(encoding="utf-8")) if answer_path.exists() else None
            controls[crs] = {"program_sha256": sha(code_path), "execution": execution,
                             "verification": verification,
                             "id": answer.get("id") if answer else None,
                             "distance_km": answer.get("distance_km") if answer else None}
        receipt = {"status": "POST_HOC_PROJECTION_SENSITIVITY_NOT_GEODESIC_GOLD",
                   "image": image, "controls": controls, "model_calls": 0,
                   "scope": "same Africa task and dataset; planar projections do not establish true geodesic distances"}
        (root / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2), flush=True)
        return
    run_root = OUT / "reference_controls"
    run_root.mkdir(exist_ok=False)
    cases = {}
    for case_name, program, test_id in (("pacific_reference", source.read_text(encoding="utf-8"), 1),
                                        ("africa_reference_unchanged", other.read_text(encoding="utf-8"), 3),
                                        ("africa_transparent_adaptation", code, 3)):
        case = run_root / case_name
        work = case / "work"
        work.mkdir(parents=True)
        code_path = case / "program.py"
        code_path.write_text(program, encoding="utf-8")
        cmd = docker_base(work)
        for filename in FILES:
            cmd += ["--mount", f"type=bind,src={tasks[test_id] / 'environment' / filename},dst=/root/{filename},readonly"]
        cmd += ["--mount", f"type=bind,src={code_path},dst=/code/program.py,readonly",
                IMAGE, "python", "/code/program.py"]
        execution = run(cmd)
        (case / "program.stdout").write_text(execution.pop("stdout"), encoding="utf-8")
        (case / "program.stderr").write_text(execution.pop("stderr"), encoding="utf-8")
        test_file = tasks[test_id] / "tests/test_outputs.py"
        verify = docker_base(work, work_readonly=True) + ["--mount", f"type=bind,src={test_file},dst=/verify/test_outputs.py,readonly",
                                     IMAGE, "python", "/verify/test_outputs.py"]
        verification = run(verify)
        (case / "verify.stdout").write_text(verification.pop("stdout"), encoding="utf-8")
        (case / "verify.stderr").write_text(verification.pop("stderr"), encoding="utf-8")
        answer = work / "answer.json"
        cases[case_name] = {"task": test_id, "program_sha256": sha(code_path),
                            "test_sha256": sha(test_file), "execution": execution,
                            "verification": verification,
                            "answer_sha256": sha(answer) if answer.exists() else None}
    receipt = {"status": "DEVELOPMENT_QUALIFICATION_NOT_OFFICIAL_RUN", "image": image,
               "runtime": "python:3.12-slim; installed pinned packages plus separately resolved dependencies",
               "upstream_solution_1_and_3_identical_sha256": sha(source),
               "input_sha256": {name: sha(tasks[1] / "environment" / name) for name in FILES},
               "instructions_sha256": {str(n): sha(tasks[n] / "instruction.md") for n in tasks},
               "cases": cases, "model_calls": 0,
               "limits": "same datasets and benchmark family; researcher has inspected tasks and references"}
    (run_root / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2), flush=True)


if __name__ == "__main__":
    main()
