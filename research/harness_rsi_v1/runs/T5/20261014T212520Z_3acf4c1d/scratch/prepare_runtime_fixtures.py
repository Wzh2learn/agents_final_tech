#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--run-root", required=True)
    args = parser.parse_args()
    run_root = Path(args.run_root).resolve()
    tick_path = run_root / "recipe_fixtures/dispatch/tick_valid.json"
    document = json.loads(tick_path.read_text(encoding="utf-8"))
    observed_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    document["observed_at"] = observed_at
    document["watcher"] = str(run_root / "recipe_fixtures/dispatch/watcher.sh")
    tick_path.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"observed_at": observed_at, "tick_path": str(tick_path), "watcher": document["watcher"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
