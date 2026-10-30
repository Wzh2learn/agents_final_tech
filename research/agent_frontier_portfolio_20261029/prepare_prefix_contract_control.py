#!/usr/bin/env python3
"""Visible-contract deterministic repair of one frozen development artifact."""
from pathlib import Path
import hashlib
import json
import shutil
import sys


def main(source, target):
    source, target = Path(source), Path(target)
    target.mkdir(parents=True, exist_ok=False)
    for n in ("config.json", "trace.jsonl"):
        shutil.copyfile(source / n, target / n)
    text = (source / "solve.py").read_text(encoding="utf8")
    changes = [
        ("prompt_tokens = input_length // block_size", "prompt_tokens = input_length"),
        ("final_cache_blocks = sorted(list(location_map.keys()))",
         "final_cache_blocks = sum(loc is not None for loc in location_map.values())"),
        ("{len(final_cache_blocks)}", "{final_cache_blocks}"),
    ]
    for old, new in changes:
        if text.count(old) != 1:
            raise ValueError("Unexpected input version: " + old)
        text = text.replace(old, new)
    (target / "solve.py").write_text(text, encoding="utf8")
    (target / "solve.py").chmod(0o666)
    print(json.dumps({"original_solve_sha256": hashlib.sha256((source / "solve.py").read_bytes()).hexdigest(),
                      "control_solve_sha256": hashlib.sha256((target / "solve.py").read_bytes()).hexdigest(),
                      "scope": "visible unit and resident-count corrections only; no policy edits"}))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: prepare_prefix_contract_control.py old-work new-work")
    main(*sys.argv[1:])
