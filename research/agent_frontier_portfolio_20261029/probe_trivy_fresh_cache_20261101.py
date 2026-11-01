#!/usr/bin/env python3
"""Test a Trivy command on a fresh source-task cache copy, without a model."""

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


ASSET_SHA = {
    "lock": "a2a42a3255e814e75bed9958c40cd9b35de7331b310bfeb8f93306d806643d44",
    "binary": "a4708c81ab60f965c16bfbab52222ee5370a5a6ca16221e0947c0bbee9ca6ac9",
    "db": "30478db8b8393e41e549ea5df7dff96e99e3c6de199b71f1a920527a23306e21",
    "report": "fb04b02db6381cf5ac2eedc4635148cba110627c6fcbcf96f8e694053d982095",
}


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def vulnerability_rows(report):
    rows = []
    for result in report.get("Results", []):
        for item in result.get("Vulnerabilities", []):
            rows.append({key: item.get(key) for key in
                         ("PkgName", "InstalledVersion", "VulnerabilityID", "Severity", "CVSS")})
    return sorted(rows, key=lambda x: (x["PkgName"], x["InstalledVersion"], x["VulnerabilityID"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--source-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files = {"lock": args.lock, "binary": args.assets / "trivy",
             "db": args.assets / "trivy-cache/db/trivy.db", "report": args.source_report}
    for key, path in files.items():
        if sha(path) != ASSET_SHA[key]:
            raise ValueError("unexpected source asset: " + key)
    args.output.mkdir(parents=True, exist_ok=False)
    cache = args.output / "cache"
    cache.mkdir()
    subprocess.run(["cp", "--reflink=auto", "-a", str(args.assets / "trivy-cache/db"), str(cache / "db")], check=True)
    # The container drops DAC capabilities and runs as root. Host-created files
    # belong to the host user; make only this isolated copy writable to Trivy.
    cache.chmod(0o777)
    (cache / "db").chmod(0o777)
    (cache / "db/trivy.db").chmod(0o666)
    (cache / "db/metadata.json").chmod(0o666)
    metadata = cache / "db/metadata.json"
    before = sha(metadata)
    container_name = "trivy-source-probe-" + str(os.getpid())
    command = ["docker", "run", "--name", container_name, "--rm", "--network", "none", "--read-only", "--cpus", "1",
               "--memory", "2g", "--pids-limit", "128", "--cap-drop", "ALL", "--security-opt",
               "no-new-privileges", "--tmpfs", "/tmp:rw,nosuid,size=128m", "--mount",
               f"type=bind,src={cache.resolve()},dst=/cache", "--mount",
               f"type=bind,src={args.lock.resolve()},dst=/input/package-lock.json,readonly", "--mount",
               f"type=bind,src={files['binary'].resolve()},dst=/usr/local/bin/trivy,readonly", "--entrypoint",
               "/usr/local/bin/trivy", "python:3.12-slim", "fs", "--skip-db-update", "--cache-dir", "/cache",
               "--scanners", "vuln", "--format", "json", "--quiet", "/input/package-lock.json"]
    try:
        run = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             timeout=300, check=False)
        code, output, error = run.returncode, run.stdout, run.stderr
    except subprocess.TimeoutExpired as exc:
        subprocess.run(["docker", "kill", container_name], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=15, check=False)
        code, output, error = 124, exc.stdout or b"", exc.stderr or b""
    (args.output / "scan.json").write_bytes(output)
    (args.output / "stderr.txt").write_bytes(error)
    reference = vulnerability_rows(json.loads(args.source_report.read_text(encoding="utf-8")))
    try:
        current = vulnerability_rows(json.loads(output))
        same = current == reference
    except (ValueError, KeyError, TypeError):
        current, same = None, False
    after = sha(metadata) if metadata.is_file() else None
    result = {"status": "SOURCE_ONLY_FRESH_PREPOPULATED_CACHE", "exit_code": code,
              "metadata_sha256_before": before, "metadata_sha256_after": after,
              "source_report_sha256": sha(args.source_report), "scan_sha256": sha(args.output / "scan.json"),
              "reference_records": len(reference), "observed_records": len(current) if current is not None else None,
              "same_identity_severity_cvss": same,
              "supports_bounded_repair": code == 0 and same and before == after,
              "model_calls": 0}
    (args.output / "receipt.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
