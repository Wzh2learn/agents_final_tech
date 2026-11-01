#!/usr/bin/env python3
"""Run the previous project harness into a separate repair pilot directory."""

import hashlib
import json
from pathlib import Path
import sys


PINNED = "368baa9fd1c4f679b73abaafdd21d02ec6027d8441502bc73a970a96038848b6"


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in {"react", "node"} or sys.argv[2] != "target_generated_skill":
        raise SystemExit("usage: run_verified_skill PROJECT target_generated_skill [adapter options]")
    source = Path(__file__).resolve().parent / "run_cross_project_cvss_20261031.py"
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != PINNED:
        raise ValueError("cross-project adapter changed")
    text = data.decode("utf-8")
    before = "dependency_cross_project_20261101/"
    after = "skill_verification_pilot_20261101/"
    if text.count(before) != 1:
        raise ValueError("unexpected output directory fragment")
    text = text.replace(before, after)
    compile(text, str(source), "exec")
    print(json.dumps({"status": "POSTHOC_MANUAL_SKILL_REPAIR", "adapter_sha256": PINNED,
                      "derived_sha256": hashlib.sha256(text.encode()).hexdigest()}), flush=True)
    sys.argv[0] = str(source)
    exec(compile(text, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})


if __name__ == "__main__":
    main()
