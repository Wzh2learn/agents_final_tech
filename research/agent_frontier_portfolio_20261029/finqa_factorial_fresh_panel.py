"""Freeze a filing-disjoint FinQA TRAIN panel and materialize its native inputs."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
import shutil
import subprocess

import finqa_forward_transfer as forward


ROOT = forward.ROOT.parent / "forward64_factorial_fresh_v1"
TRAIN = forward.m.study.DATA
PRIVATE = forward.m.study.PRIVATE
TEST = PRIVATE / "finqa_correction_v1/test_pool_v1/test.json"
N = 64
PRIORITY_SALT = "finqa-forward64-factorial-k8-k18-v1"
TEACHER_TASK_BUDGETS = (8, 18)
TEACHER_TOKEN_CAP = 1_200_000
TEACHER_POST_CAP = 6 * N
POLICIES = ("ordinary_risk", "ordinary_value", "cheap37_risk", "cheap37_value")
HISTORY_FIELDS = {
    "group", "report", "filename", "id", "source_id", "task_id", "report_group",
    "filing_group", "excluded_groups", "excluded_filing_groups", "excluded_report_groups",
    "excluded_reports", "group_id", "groups", "company_year", "dataset_id",
}
GOLD_FIELDS = {"qa", "program", "program_re", "labels", "private_labels", "exe_ans", "answer"}
FILES_TO_SCAN = ("plan", "select", "reservation", "registry", "manifest", "exposure", "result")


def jq_rows(path, expression, *options):
    result = subprocess.check_output(["jq", "-c", *options, expression, str(path)], encoding="utf-8")
    return [json.loads(line) for line in result.splitlines()]


def group(report):
    company, year, _ = report.split("/", 2)
    if not company or not year:
        raise ValueError("missing company or year")
    return f"{company}/{year}"


def table_signature(table):
    normalized = tuple(tuple(re.sub(r"\s+", " ", str(cell).casefold()).strip() for cell in row) for row in table)
    return sha256(repr(normalized).encode()).hexdigest()


def referenced_groups(value, lookup, active=False):
    if isinstance(value, dict):
        for key, entry in value.items():
            if key not in GOLD_FIELDS:
                yield from referenced_groups(entry, lookup, active or key in HISTORY_FIELDS)
    elif isinstance(value, list):
        for entry in value:
            yield from referenced_groups(entry, lookup, active)
    elif active and isinstance(value, str) and value in lookup:
        yield lookup[value]


def history(catalog):
    lookup = {item["id"]: item["group"] for item in catalog}
    lookup.update({item["report"]: item["group"] for item in catalog})
    lookup.update({item["group"]: item["group"] for item in catalog})
    roots = {path for path in PRIVATE.iterdir() if path.is_dir() and "finqa" in path.name.lower()}
    roots.update(path for path in PRIVATE.parent.iterdir()
                 if path.is_dir() and any(word in path.name.lower() for word in ("finqa", "paper_e")))
    paths = set()
    for root in roots:
        for path in root.rglob("*.json"):
            name = path.name.lower()
            if (any(word in name for word in FILES_TO_SCAN)
                    and not any(word in name for word in ("label", "gold", "answer"))
                    and path.stat().st_size < 8_000_000):
                paths.add(path)
    excluded, matched, unreadable = set(), 0, 0
    for path in sorted(paths):
        try:
            value = forward.m.read(path)
        except (UnicodeDecodeError, json.JSONDecodeError):
            unreadable += 1
            continue
        groups = set(referenced_groups(value, lookup))
        matched += bool(groups)
        excluded.update(groups)
    if not excluded or not paths:
        raise RuntimeError("historical source exclusion did not find any provenance")
    return excluded, dict(roots=sorted(str(path) for path in roots), files_scanned=len(paths),
                          files_matched=matched, files_unreadable=unreadable)


def select():
    paths = (TRAIN, TRAIN.with_name("dev.json"), TEST)
    catalog = []
    for path in paths:
        for row in jq_rows(path, ".[] | {id, filename, table}"):
            catalog.append(dict(id=row["id"], report=row["filename"], group=group(row["filename"]),
                                table_sha256=table_signature(row["table"]), split=path.stem))
    excluded, audit = history(catalog)
    known_tables = {item["table_sha256"] for item in catalog if item["group"] in excluded}
    candidates = [item for item in catalog if item["split"] == "train" and item["group"] not in excluded
                  and item["table_sha256"] not in known_tables]
    audit.update(excluded_groups=sorted(excluded), eligible_rows=len(candidates),
                 eligible_groups=len({item["group"] for item in candidates}))
    groups, fingerprints, ids, chosen = set(), set(), set(), []
    candidates.sort(key=lambda item: (sha256(f"{PRIORITY_SALT}\n{item['report']}\n{item['id']}".encode()).digest(),
                                      item["report"], item["id"]))
    for item in candidates:
        if item["group"] in groups or item["table_sha256"] in fingerprints or item["id"] in ids:
            continue
        groups.add(item["group"])
        fingerprints.add(item["table_sha256"])
        ids.add(item["id"])
        chosen.append(item)
        if len(chosen) == N:
            return chosen, audit
    raise ValueError(f"only {len(chosen)} distinct eligible groups with distinct tables; expected {N}")


def prepare():
    if ROOT.exists():
        raise FileExistsError(f"Inspect the existing attempt at {ROOT}")
    tasks, audit = select()
    previous = forward.m.read(forward.ROOT / "PLAN.json")
    checkpoints = {}
    for name in ("risk", "value"):
        path = forward.ROOT.parent / forward.POLICIES[name]
        train = forward.m.read(path / "TRAIN_RESULT.json")
        if train["status"] != "TRAINED" or train["optimizer_updates"] != 434:
            raise ValueError(f"Unexpected {name} checkpoint")
        checkpoints[name] = dict(folder=str(path / "value_policy"), updates=434)
    if not all(Path(path).is_file() for path in previous["adapters"].values()):
        raise FileNotFoundError("A frozen native adapter is unavailable")
    teacher = forward.m.read(forward.av.TEACHER / "PLAN.json")
    protocol = dict(
        status="FROZEN_BEFORE_HELDOUT_PAYLOAD", cohort="forward",
        source=str(TRAIN), tasks=tasks, checkpoints=checkpoints, exclusion=audit,
        selection_salt=PRIORITY_SALT, teacher_task_budget=TEACHER_TASK_BUDGETS[0],
        secondary_task_budgets=list(TEACHER_TASK_BUDGETS), frozen_policies=POLICIES,
        teacher_token_cap=TEACHER_TOKEN_CAP, teacher_post_cap=TEACHER_POST_CAP,
        teacher_profile=teacher["model"], teacher_caps=teacher["caps"],
        primary="K8: cheap37+value versus ordinary+risk; K18 is secondary",
        scope="64 project-unexposed official TRAIN filing groups based on recorded provenance. "
              "One task per company/year. No outcome-based screening or replacements.",
        teacher_pool="One T0 realization per distinct selected task from the original first-pass snapshot.",
        scoring="Use each branch's public candidate and the same G, then host-only execution grading.",
        source_revision=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=forward.c.repo,
                                                text=True).strip(),
    )
    plan = {**previous, **protocol}
    ROOT.mkdir(mode=0o700)
    forward.m.study.new(ROOT / "PROTOCOL.json", protocol)

    # Give jq only the chosen IDs after the protocol is durable.
    task_ids = json.dumps({item["id"]: True for item in tasks})
    records = jq_rows(TRAIN, '.[] | select($chosen[.id] == true)', "--argjson", "chosen", task_ids)
    by_id = {row["id"]: row for row in records}
    if len(records) != N or len(by_id) != N:
        raise ValueError("Frozen tasks do not resolve uniquely in the official TRAIN snapshot")
    template = Path(previous["episodes"][0]["folder"]) / "inputs"
    episodes, labels = [], []
    for index, task in enumerate(tasks):
        record = by_id[task["id"]]
        if record["filename"] != task["report"] or table_signature(record["table"]) != task["table_sha256"]:
            raise ValueError("Frozen source metadata changed")
        public = forward.m.task.public_record(record)
        private = record["qa"]
        forward.m.task.canonical_answer(private["exe_ans"])
        folder = ROOT / "firstpass" / f"{index:03d}"
        inputs = folder / "inputs"
        inputs.mkdir(parents=True)
        (folder / "work").mkdir()
        (folder / "dependencies").mkdir()
        for name in ("finqa_tool.py", "executor.py", "guest.py"):
            shutil.copyfile(template / name, inputs / name)
        (inputs / "public.json").write_text(json.dumps(public, ensure_ascii=False), encoding="utf-8")
        (inputs / "task.txt").write_text(forward.m.study.prompt(public, terminal_program=True), encoding="utf-8")
        episodes.append(dict(index=index, id=task["id"], report=task["report"], group=task["group"],
                             folder=str(folder)))
        labels.append(dict(index=index, id=task["id"], report=task["report"],
                           exe_ans=private["exe_ans"], program=private["program"]))
    forward.m.study.new(ROOT / "LABELS_PRIVATE.json", labels)
    forward.m.study.new(ROOT / "PLAN.json", {**plan, "episodes": episodes})
    print(json.dumps(dict(root=str(ROOT), prepared=N, excluded_groups=len(audit["excluded_groups"]),
                          eligible_groups=audit["eligible_groups"], files_scanned=audit["files_scanned"],
                          files_unreadable=audit["files_unreadable"], seen_group_overlap=0,
                          seen_table_overlap=0, protocol_frozen_before_payload=True)), flush=True)


if __name__ == "__main__":
    prepare()
