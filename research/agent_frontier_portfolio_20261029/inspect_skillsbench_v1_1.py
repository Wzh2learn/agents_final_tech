"""Read-only source/overlap qualification; not a data-contamination proof."""
import hashlib
import json
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1]).resolve()
registry = json.loads((root / "registry.json").read_text(encoding="utf-8"))
entry = next(x for x in registry if x.get("version") == "1.1")
tasks = entry["tasks"]
names = [x["name"] for x in tasks]
assert len(names) == len(set(names)) == 87
selected = "llm-prefix-cache-replay"
task = root / "tasks" / selected
paths = ["task.md", "environment/Dockerfile", "environment/config.json", "environment/trace.jsonl", "oracle/solve.sh", "verifier/test_outputs.py", "verifier/oracle_helpers.py", "verifier/test.sh", "environment/skills/prefix-cache-replay/SKILL.md"]
hashes = {p: hashlib.sha256((task / p).read_bytes()).hexdigest() for p in paths}
needles = ("remix/partridge", "09e89d98b5a00db44394204d2f3e70c220b51764", "daefcbe6a03e92a0bfc0c2433279b9fd3d179f6c")
suffixes = {".md", ".py", ".sh", ".json", ".toml", ".yaml", ".yml", ".txt"}
hits, checked, skipped = [], 0, 0
for name in names:
    directory = root / "tasks" / name
    for p in directory.rglob("*"):
        if not p.is_file() or (p.suffix.lower() not in suffixes and p.name != "Dockerfile"):
            continue
        if p.stat().st_size > 5_000_000:
            skipped += 1
            continue
        checked += 1
        text = p.read_text(encoding="utf-8", errors="replace").lower()
        for needle in needles:
            if needle in text:
                hits.append({"path": str(p.relative_to(root)), "needle": needle})
data = {
    "qualification": "REPOSITORY_TEXT_SCAN_ONLY_NOT_SOURCE_OR_MODEL_DECONTAMINATION",
    "git_head": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip(),
    "v1_1_task_commit_ids": sorted({x["git_commit_id"] for x in tasks}),
    "v1_1_task_count": len(names), "task": selected,
    "benchflow_requirement": entry.get("bench_version"),
    "license_sha256": hashlib.sha256((root / "LICENSE").read_bytes()).hexdigest(),
    "registry_sha256": hashlib.sha256((root / "registry.json").read_bytes()).hexdigest(),
    "selected_file_sha256": hashes,
    "parent_overlap_check": {"needles": needles, "files_checked": checked, "large_files_skipped": skipped, "hits": hits},
}
print(json.dumps(data, ensure_ascii=False, indent=2))
