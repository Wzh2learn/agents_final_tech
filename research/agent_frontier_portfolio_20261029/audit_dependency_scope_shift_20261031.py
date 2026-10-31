#!/usr/bin/env python3
"""Compare three public dependency-audit contracts with privileged controls.

Published reference CSVs are used only to qualify the verifier.  These files
are not Agent outputs or independent vulnerability ground truth.
"""

import argparse
import csv
import hashlib
import io
import json
import runpy
import subprocess
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_reference(test):
    cls = runpy.run_path(str(test))["TestSecurityAuditTask"]
    text = cls.EXPECTED_CSV_CONTENT.strip()
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows or reader.fieldnames != cls.EXPECTED_HEADERS:
        raise ValueError(f"Missing reference rows or header mismatch: {test}")
    return reader.fieldnames, rows


def write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(args):
    args.output.mkdir(parents=True, exist_ok=False)
    image_id = subprocess.check_output(
        ["docker", "image", "inspect", args.image, "--format", "{{.Id}}"], text=True
    ).strip()
    tests = {i: args.tasks / f"dependency-vulnerability-check-{i}/tests/test_outputs.py"
             for i in (1, 2, 3)}
    references = {i: parse_reference(test) for i, test in tests.items()}
    fixtures = {}
    for i, (header, rows) in references.items():
        fixtures[f"reference_{i}"] = (header, rows)
        if i in (2, 3):
            # Preserve the last row for each key, matching the source predicate.
            # This deliberately omits other published vulnerabilities.
            last = {(row["Package"], row["Version"]): row for row in rows}
            fixtures[f"reference_{i}_omit_shadowed"] = (header, list(last.values()))
    results = []
    for fixture_name, (header, rows) in fixtures.items():
        fixture_path = args.output / "fixtures" / fixture_name / "security_audit.csv"
        fixture_path.parent.mkdir(parents=True)
        write_csv(fixture_path, header, rows)
        targets = (1, 2, 3) if "omit_shadowed" not in fixture_name else (int(fixture_name.split("_")[1]),)
        for target in targets:
            log = args.output / "runs" / f"{fixture_name}_against_{target}.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            command = ["docker", "run", "--rm", "--network", "none", "--read-only",
                       "--user", "0:0", "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
                       "-e", "PYTHONPATH=/deps", "-e", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
                       "-e", "PYTHONDONTWRITEBYTECODE=1",
                       "-v", f"{args.site_packages.resolve()}:/deps:ro",
                       "-v", f"{tests[target].resolve()}:/tests/test_outputs.py:ro",
                       "-v", f"{fixture_path.resolve()}:/root/security_audit.csv:ro",
                       args.image, "python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                       "/tests/test_outputs.py"]
            completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       text=True, timeout=60)
            log.write_text(completed.stdout, encoding="utf-8")
            results.append({"fixture": fixture_name, "rows": len(rows), "target": target,
                            "exit_code": completed.returncode, "fixture_sha256": sha(fixture_path),
                            "test_sha256": sha(tests[target]), "log_sha256": sha(log)})
    summary = {"status": "POSTHOC_PRIVILEGED_REFERENCE_CONTROLS_NOT_AGENT_OUTPUTS",
               "benchmark_commit": "726e1f79b96b0cb3d729d0e55a1c847e0b5353ae",
               "image_id": image_id, "pytest": "9.0.1 via mounted research venv",
               "source_sha256": sha(Path(__file__)), "runs": results}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps([{"fixture": x["fixture"], "rows": x["rows"], "target": x["target"],
                       "exit_code": x["exit_code"]} for x in results]))
    for target in (1, 2, 3):
        if next(x for x in results if x["fixture"] == f"reference_{target}"
                and x["target"] == target)["exit_code"] != 0:
            raise SystemExit("Infrastructure/control failure: own-reference control failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--site-packages", type=Path, required=True)
    parser.add_argument("--image", default="python-sandbox:latest")
    run(parser.parse_args())
