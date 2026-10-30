#!/usr/bin/env python3
"""Construct a visibly invalid static-output control for dialogue verifier audit."""
import hashlib
import json
import shutil
import sys
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(source, target):
    source, target = Path(source), Path(target)
    target.mkdir(parents=True, exist_ok=False)
    for name in ("dialogue.json", "script.txt"):
        shutil.copyfile(source / name, target / name)
    dot = (source / "dialogue.dot").read_text(encoding="utf8")
    if dot.count("node [shape=box, style=rounded]") != 1:
        raise ValueError("Unexpected DOT input; do not mutate another format")
    dot = dot.replace("node [shape=box, style=rounded]", "node [shape=diamond, style=rounded]")
    (target / "dialogue.dot").write_text(dot, encoding="utf8")
    print(json.dumps({"source_hashes": {n: sha(source / n) for n in ("dialogue.json", "dialogue.dot", "script.txt")},
                      "output_hashes": {n: sha(target / n) for n in ("dialogue.json", "dialogue.dot", "script.txt")},
                      "omitted": "solution.py",
                      "mutation": "default all nodes to diamond; not a faithful visualization"}))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: prepare_dialogue_verifier_control.py source-work new-output-dir")
    main(*sys.argv[1:])
