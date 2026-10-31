#!/usr/bin/env python3
"""Read-only exact-byte overlap scan for SkillLearnBench task environments.

An identical file is evidence of byte overlap, not necessarily the whole task or
benchmark contamination. Different hashes do not establish source separation.
No file contents are copied into the output.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess


def sha_file(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def scan(tasks):
    assets = defaultdict(list)
    instances = {}
    skipped_symlinks = 0
    skipped_empty_files = 0
    for family in sorted(p for p in tasks.iterdir() if p.is_dir()):
        for instance in sorted(p for p in family.iterdir() if p.is_dir()):
            environment = instance / "environment"
            if not environment.is_dir():
                continue
            instance_key = f"{family.name}/{instance.name}"
            hashes = set()
            count = 0
            for path in sorted(environment.rglob("*")):
                if path.is_symlink():
                    skipped_symlinks += 1
                    continue
                if not path.is_file():
                    continue
                relative = path.relative_to(environment)
                if path.name.lower() == "dockerfile" or "skills" in relative.parts:
                    continue
                if path.stat().st_size == 0:
                    skipped_empty_files += 1
                    continue
                digest = sha_file(path)
                count += 1
                hashes.add(digest)
                assets[digest].append({"instance": instance_key, "file": relative.as_posix()})
            instances[instance_key] = {"asset_count": count, "content_hashes": hashes}

    shared_groups = []
    for digest, rows in assets.items():
        unique_instances = {row["instance"] for row in rows}
        if len(unique_instances) < 2:
            continue
        families = {name.split("/", 1)[0] for name in unique_instances}
        shared_groups.append({"sha256": digest, "distinct_instances": len(unique_instances),
                              "distinct_families": len(families), "occurrences": rows[:25],
                              "occurrences_truncated": max(0, len(rows) - 25)})
    shared_groups.sort(key=lambda g: (-g["distinct_families"], -g["distinct_instances"], g["sha256"]))
    dataset_groups = defaultdict(list)
    for name, value in instances.items():
        if value["content_hashes"]:
            dataset_groups[tuple(sorted(value["content_hashes"]))].append(name)
    same_sets = [sorted(names) for names in dataset_groups.values() if len(names) > 1]
    same_sets.sort()
    return {
        "task_families": len({name.split("/", 1)[0] for name in instances}),
        "task_instances": len(instances),
        "instances_with_no_scanned_assets": sum(not item["asset_count"] for item in instances.values()),
        "physical_asset_files": sum(item["asset_count"] for item in instances.values()),
        "distinct_asset_hashes": len(assets), "skipped_symlinks": skipped_symlinks,
        "skipped_empty_files": skipped_empty_files,
        "shared_byte_hash_groups": len(shared_groups),
        "shared_across_families_groups": sum(row["distinct_families"] > 1 for row in shared_groups),
        "identical_nonempty_content_sets": same_sets,
        "top_shared_hash_groups": shared_groups[:30],
        "limitations": ["only exact-byte matches; semantic and model-pretraining overlap are not tested",
                        "environment assets exclude Dockerfiles, skills directories and empty files",
                        "identical inputs can support intentionally different instructions or evaluation contracts",
                        "a directory-based instance is not necessarily an independent dataset or official split"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repository", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    result = scan(args.repository / "tasks")
    result["source_commit"] = subprocess.check_output(["git", "-C", str(args.repository), "rev-parse", "HEAD"], text=True).strip()
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("top_shared_hash_groups", "identical_nonempty_content_sets")}))


if __name__ == "__main__":
    main()
