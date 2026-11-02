#!/usr/bin/env python3
"""Run two isolated DBSCAN development episodes using the pinned Agent harness."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import run_dbscan_reference_20261101 as reference_runner
from run_dbscan_reference_20261101 import DATA, EXPECTED, IMAGE, PROJECTED_DATA, SOURCES, TEST_HASH, sha


BASE_HASH = "4111a0be97845740769722e2e596871d51c7693d14d2372d7f6931b4d06e7afb"
INSTRUCTIONS = {
    1: "2cdef7629a2918e8322ceaaec2f2651e357202e15cfb9bc073836441ec92b3d8",
    2: "cef544ef4811c0306e52b6e8ce0e2885555ddb8ab4c81e1ee9c3fd05cdb8617e",
}
OUTPUT_ROOT = "/home/testuser/wzh/research_evidence/agent_learning_20261030/dbscan_agent_pilot_20261102"
PROJECTION_FIELDS = ["file_rad", "x", "y", "frame_file"]


def replace_once(text, old, new, count=1):
    if text.count(old) != count:
        raise ValueError(f"base runner fragment changed: {old[:100]!r}")
    return text.replace(old, new)


def verify_projection(projection, proof_root):
    projection_receipt = projection.parent / "receipt.json"
    manifest = json.loads(projection_receipt.read_text(encoding="utf-8"))
    if manifest.get("fields") != PROJECTION_FIELDS:
        raise ValueError("projection manifest has unexpected columns")
    for name, digest in PROJECTED_DATA.items():
        path = projection / name
        recorded = manifest.get("files", {}).get(name, {})
        if (recorded.get("source_sha256") != DATA[name] or recorded.get("projection_sha256") != digest
                or recorded.get("row_order_and_selected_values_equal") is not True):
            raise ValueError("projection manifest mismatch: " + name)
        if sha(path) != digest:
            raise ValueError("projected dataset changed: " + name)
        with path.open(encoding="utf-8", newline="") as stream:
            if next(csv.reader(stream)) != PROJECTION_FIELDS:
                raise ValueError("projected dataset has unexpected columns: " + name)
    proofs = {}
    for version in (1, 2):
        folder = proof_root / f"task{version}"
        receipt_path = folder / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if (receipt.get("task") != version or receipt.get("source_sha256") != SOURCES[version]
                or receipt.get("runner_sha256") != sha(Path(reference_runner.__file__).resolve())
                or receipt.get("expected_sha256") != EXPECTED[version]
                or receipt.get("test_sha256") != TEST_HASH
                or receipt.get("image") != IMAGE
                or receipt.get("data_source") != "four_column_projection"
                or receipt.get("data_sha256") != PROJECTED_DATA
                or receipt.get("original_data_sha256") != DATA
                or receipt.get("solver", {}).get("exit_code") != 0
                or (receipt.get("verifier") or {}).get("exit_code") != 0
                or receipt.get("output_sha256") != EXPECTED[version]):
            raise ValueError(f"projection compatibility proof invalid: task {version}")
        if sha(folder / "work/pareto_frontier.csv") != EXPECTED[version]:
            raise ValueError(f"projection output changed: task {version}")
        if sha(folder / "verifier.stdout") != receipt["verifier"]["stdout_sha256"]:
            raise ValueError(f"projection verifier output changed: task {version}")
        proofs[str(version)] = sha(receipt_path)
    return {"projection": sha(projection_receipt), "reference_runs": proofs}


def prepare(base, tasks, projection, proof_root, version):
    if sha(base) != BASE_HASH:
        raise ValueError("base runner changed")
    task = tasks / f"dbscan-parameter-tuning-{version}"
    expected = {"instruction.md": INSTRUCTIONS[version], "tests/test_outputs.py": TEST_HASH,
                "tests/expected_frontier.csv": EXPECTED[version],
                **{f"environment/data/{name}": digest for name, digest in DATA.items()}}
    for relative, digest in expected.items():
        if sha(task / relative) != digest:
            raise ValueError("frozen task asset changed: " + relative)
    projection_proofs = verify_projection(projection, proof_root)
    actual_image = subprocess.check_output(["docker", "image", "inspect", "python:3.12-slim", "--format", "{{.Id}}"],
                                           text=True).strip()
    if actual_image != IMAGE:
        raise ValueError("container image changed")
    text = base.read_text(encoding="utf-8")
    changes = [
        ("/home/testuser/wzh/research_evidence/agent_skill_method_20261029", OUTPUT_ROOT, 1),
        ("UP=Path('/home/testuser/wzh/research_evidence/agent_frontier_20261029/skillsbench_v1_1/tasks')",
         "UP=Path(os.environ['DBSCAN_TASKS_ROOT'])", 1),
        ("'dialogue-parser','tictoc-unnecessary-abort-detection') or arm",
         "'dialogue-parser','tictoc-unnecessary-abort-detection',"
         "'dbscan-parameter-tuning-1','dbscan-parameter-tuning-2') or arm", 1),
        ("body=(src/'task.md').read_text(encoding='utf8').split('---',2)[2].strip()",
         "body=(src/'instruction.md').read_text(encoding='utf8').strip()", 1),
        ("(work/'instructions.txt').write_text(body,encoding='utf8')",
         "(work/'instructions.txt').write_text(body,encoding='utf8')\n(work/'data').mkdir()", 1),
        ("'timeout':120000", "'timeout':300000", 1),
        ("[],[],120)", "[],[],300)", 2),
        ("stderr=subprocess.PIPE,timeout=300)", "stderr=subprocess.PIPE,timeout=1200)", 1),
        ("len(calls)>=8", "len(calls)>=24", 1),
        ("sum(payload_bytes)+length>450000", "sum(payload_bytes)+length>1500000", 1),
        ("calls.append('DENIED_OR_LIMIT');self.request.sendall",
         "reason=('method' if line not in allowed else 'request_cap' if len(calls)>=24 "
         "else 'missing_length' if length is None else 'post_byte_cap')\n"
         "   calls.append('DENIED:'+reason);self.request.sendall", 1),
        ("Never read an entire large trace into the conversation; inspect only the first two lines using shell head, then write code that processes the complete unmodified file.",
         "The datasets are large; inspect a small sample and implement the stated computation without printing complete datasets.", 1),
        ("'--cpus','1','--cap-drop'", "'--cpus','2','--cap-drop'", 1),
        ("'--memory','2g'", "'--memory','3g'", 1),
        ("server=Server(str(sockpath),Handler);",
         "_at=cmd.index('python:3.12-slim'); "
         "cmd[_at:_at]=['-e','PYTHONPATH=/deps','-e','OPENBLAS_NUM_THREADS=1',"
         "'-e','OMP_NUM_THREADS=1','-e','PYTHONWARNINGS=ignore::DeprecationWarning',"
         "'--mount',f'type=bind,src={DEPS},dst=/deps,readonly',"
         "'--mount',f'type=bind,src={Path(os.environ[\"DBSCAN_PROJECTED_DATA\"])},dst=/root/data,readonly']; "
         "server=Server(str(sockpath),Handler);", 1),
        ("'--mount',f'type=bind,src={work},dst={target}', '--mount',f'type=bind,src={src / \"verifier\"},dst=/verifier,readonly'",
         "'--mount',f'type=bind,src={work},dst={target},readonly', '--mount',f'type=bind,src={src / \"tests\"},dst=/verifier,readonly'", 1),
    ]
    for old, new, count in changes:
        text = replace_once(text, old, new, count)
    compile(text, str(base), "exec")
    return text, {"task_version": version, "condition": "no_history", "base_sha256": BASE_HASH,
                  "derived_sha256": hashlib.sha256(text.encode()).hexdigest(),
                  "task_assets_sha256": expected, "projected_data_sha256": PROJECTED_DATA,
                  "projection_proof_receipt_sha256": projection_proofs, "image": actual_image,
                  "max_http": 24, "max_post_bytes": 1500000, "max_step_output_tokens_configured": 8192,
                  "max_agent_wall_seconds": 1200, "cpus": 2, "memory": "3g",
                  "status": "DEVELOPMENT_ONLY_NOT_OFFICIAL_HARNESS"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("version", type=int, choices=(1, 2))
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--proof-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text, provenance = prepare(args.base, args.tasks, args.projection, args.proof_root, args.version)
    print(json.dumps(provenance), flush=True)
    if args.check:
        return
    os.environ["DBSCAN_TASKS_ROOT"] = str(args.tasks.resolve())
    os.environ["DBSCAN_PROJECTED_DATA"] = str(args.projection.resolve())
    sys.argv = [str(args.base), f"dbscan-parameter-tuning-{args.version}", "no_skill"]
    namespace = {"__name__": "__main__", "__file__": str(args.base)}
    try:
        exec(compile(text, str(args.base), "exec"), namespace)
    finally:
        case = namespace.get("case")
        if case is not None and case.is_dir():
            (case / "intervention.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
