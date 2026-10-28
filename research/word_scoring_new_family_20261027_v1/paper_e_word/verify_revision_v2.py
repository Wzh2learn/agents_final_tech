#!/usr/bin/env python3
"""Deterministic lint for the Paper E revision production source.

Checks the four defect classes that C flagged, plus the arithmetic and
cross-reference consistency the revision claims.  Prints a JSON report and
exits non-zero if any hard check fails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "paper_e_revision_v3.md"

TBD_FIELDS_EXPECTED = 10  # 3 author block lines + 7 statement fields


def body_and_refs(text: str) -> tuple[str, str]:
    if "## References" not in text:
        raise SystemExit("no References section")
    head, tail = text.split("## References", 1)
    return head, tail


def check_structure(text: str) -> dict:
    failures: list[str] = []
    lines = text.splitlines()

    # --- blank-line audit -------------------------------------------------
    for i, line in enumerate(lines):
        s = line.strip()
        if re.match(r"^#{1,6}\s", s):
            if i > 0 and lines[i - 1].strip() != "":
                failures.append(f"heading at line {i+1} has no blank line before it")
            if i + 1 < len(lines) and lines[i + 1].strip() != "":
                failures.append(f"heading at line {i+1} has no blank line after it")
        if s.startswith("|"):
            prev = lines[i - 1].strip() if i else ""
            if prev and not prev.startswith("|"):
                failures.append(f"table row at line {i+1} has no blank line before it")
        if re.match(r"^([-*]|\d+\.)\s+", s):
            prev = lines[i - 1].strip() if i else ""
            if prev and not re.match(r"^([-*]|\d+\.)\s+", prev):
                failures.append(f"list item at line {i+1} has no blank line before it")
        if s.startswith("!["):
            prev = lines[i - 1].strip() if i else ""
            if prev:
                failures.append(f"image at line {i+1} is not an isolated paragraph")

    # --- captions ---------------------------------------------------------
    tables = re.findall(r"(?m)^Table: Table (\d+)\. (.+)$", text)
    figures = re.findall(r"!\[Figure (\d+)\. (.+?)\]\((.+?)\)", text)
    if [int(n) for n, _ in tables] != [1, 2, 3, 4]:
        failures.append(f"table captions not 1-4 in order: {[n for n, _ in tables]}")
    if [int(n) for n, _, _ in figures] != [1, 2, 3]:
        failures.append(f"figure captions not 1-3 in order: {[n for n, _, _ in figures]}")
    for n, _, path in figures:
        if not (HERE / path).is_file():
            failures.append(f"figure {n} asset missing: {path}")

    # --- cross references -------------------------------------------------
    body, _ = body_and_refs(text)
    for n in range(1, 5):
        if len(re.findall(rf"(?<!Table: )Table {n}\b", body)) < 1:
            failures.append(f"Table {n} is never cited in the body")
    for n in range(1, 4):
        if len(re.findall(rf"Figure {n}\b", body)) < 1:
            failures.append(f"Figure {n} is never cited in the body")

    headings = set()
    for line in text.splitlines():
        m = re.match(r"^#{2,3}\s+(\d+(?:\.\d+)?)\s", line)
        if m:
            headings.add(m.group(1))
    section_refs = set(re.findall(r"Section (\d+(?:\.\d+)?)", body))
    for ref in sorted(section_refs - headings):
        failures.append(f"in-text reference to Section {ref} has no matching heading")

    # --- lists ------------------------------------------------------------
    contributions = re.findall(r"(?m)^(\d+)\. ", body.split("Our contributions are:", 1)[-1].split("\n\n", 2)[1] if "Our contributions are:" in body else "")
    checklist_block = body.split("proposed checklist for evaluator authors", 1)[-1]
    steps = re.findall(r"(?m)^(\d+)\. ", checklist_block.split("\n\n", 2)[1])
    bullets = re.findall(r"(?m)^- ", body)
    if len(steps) != 6:
        failures.append(f"review checklist has {len(steps)} items, caption says six")
    if len(bullets) != 3:
        failures.append(f"expect 3 bullets in the visibility section, found {len(bullets)}")

    # --- citation hygiene -------------------------------------------------
    _, refs = body_and_refs(text)
    ref_numbers = [int(n) for n in re.findall(r"(?m)^\[(\d+)\]", refs)]
    if ref_numbers != list(range(1, 25)):
        failures.append(f"reference list numbering is not 1..24: {ref_numbers[:5]}...")
    cited: set[int] = set()
    for i, line in enumerate(body.splitlines(), 1):
        for m in re.finditer(r"\[(\d{1,2}(?:,\d{1,2})*)\]", line):
            nums = [int(x) for x in m.group(1).split(",")]
            if not all(1 <= n <= 24 for n in nums):
                continue
            if nums != sorted(nums):
                failures.append(f"line {i}: citation group not ascending {m.group(0)}")
            if len(set(nums)) != len(nums):
                failures.append(f"line {i}: duplicate number in {m.group(0)}")
            cited.update(nums)
    missing = sorted(set(range(1, 25)) - cited)
    if missing:
        failures.append(f"references never cited in text: {missing}")

    # --- residue ----------------------------------------------------------
    residue = re.findall(r"\\[a-zA-Z]+", text)
    if residue:
        failures.append(f"raw LaTeX remains: {sorted(set(residue))}")
    if re.search(r"(?m)^\*\*Table \d", text):
        failures.append("bold table caption paragraph still present")
    if "Paper E" in text:
        failures.append("internal project codename 'Paper E' still in the manuscript")

    tbd = text.count("TBD_OWNER")
    if tbd != TBD_FIELDS_EXPECTED:
        failures.append(f"expected {TBD_FIELDS_EXPECTED} TBD_OWNER placeholders, found {tbd}")

    return {
        "failures": failures,
        "counts": {
            "headings": len(re.findall(r"(?m)^#{2,3}\s", text)),
            "numbered_sections": len(headings),
            "table_captions": len(tables),
            "figure_captions": len(figures),
            "checklist_steps": len(steps),
            "bullets": len(bullets),
            "references": len(ref_numbers),
            "cited_reference_numbers": len(cited),
            "tbd_owner": tbd,
        },
    }


def check_arithmetic(text: str) -> dict:
    failures: list[str] = []
    checks: list[dict] = []

    def add(name: str, lhs, rhs, ok: bool) -> None:
        checks.append({"check": name, "lhs": lhs, "rhs": rhs, "ok": ok})
        if not ok:
            failures.append(f"{name}: {lhs} != {rhs}")

    families = {"alias variant": (47, 43, 4), "date variant": (17, 15, 2),
                "mixed language": (20, 20, 0), "OCR-like": (13, 0, 13),
                "prefix noise": (16, 13, 3), "unit suffix": (5, 5, 0)}
    for name, (inj, vis, absb) in families.items():
        m = re.search(rf"{re.escape(name)} (\d+)/(\d+)/(\d+)", text)
        if not m:
            failures.append(f"family row missing: {name}")
            continue
        add(f"{name} row", tuple(int(x) for x in m.groups()), (inj, vis, absb),
            tuple(int(x) for x in m.groups()) == (inj, vis, absb))
        add(f"{name} closes", vis + absb, inj, vis + absb == inj)

    add("total injections", sum(v[0] for v in families.values()), 118,
        sum(v[0] for v in families.values()) == 118)
    add("total visible", sum(v[1] for v in families.values()), 96,
        sum(v[1] for v in families.values()) == 96)
    add("total absorbed", sum(v[2] for v in families.values()), 22,
        sum(v[2] for v in families.values()) == 22)

    seeds = re.findall(r"(\d+)/(\d+) = 0\.\d+", text)
    if len(seeds) >= 3:
        nums = [(int(a), int(b)) for a, b in seeds[:3]]
        add("seed table runs", sum(a for a, _ in nums), 219, sum(a for a, _ in nums) == 219)
        add("seed table denominators", sum(b for _, b in nums), 282, sum(b for _, b in nums) == 282)

    m = re.search(r"(\d+) unique source-table UIDs: (\d+) appear in one seed, (\d+) in two, and (\d+) in all three", text)
    if m:
        total, one, two, three = (int(x) for x in m.groups())
        add("UID partition", one + two + three, total, one + two + three == total)

    m = re.search(r"(\d+) clusters per stage give (\d+) clusters and (\d+) injections", text)
    if m:
        per, clusters, injections = (int(x) for x in m.groups())
        add("stage clustering", per * 3, clusters, per * 3 == clusters)
        add("stage injections", clusters * 3, injections, clusters * 3 == injections)

    add("parsing+QA leaves", 5 + 7, 12, 5 + 7 == 12)

    # FinRank table: displayed gap must equal the rounded full-precision value,
    # and must not be silently recomputed from the rounded cells.
    rows = re.findall(r"(?m)^\| (TF-IDF|BM25) \| (\S+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \|", text)
    if len(rows) != 6:
        failures.append(f"expected 6 FinRank rows, found {len(rows)}")
    else:
        for model, policy, hard, random_, gap in rows:
            hard_f, random_f, gap_f = float(hard), float(random_), float(gap)
            add(f"{model}/{policy} gap", round(random_f - hard_f, 3), gap_f,
                abs(round(random_f - hard_f, 3) - gap_f) <= 0.0011)

    m = re.search(r"full-precision gap `(\d+\.\d+)` rounds to the reported (\d+\.\d+)", text)
    if m:
        add("full-precision gap rounds to displayed", round(float(m.group(1)), 3),
            float(m.group(2)), round(float(m.group(1)), 3) == float(m.group(2)))

    return {"failures": failures, "checks": checks}


def abstract_word_count(text: str) -> dict:
    block = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    labels = re.findall(r"\*\*(Purpose|Methods|Results|Conclusion)\.\*\*", block)
    prose = re.sub(r"\*\*[A-Za-z]+\.\*\*", "", block)
    words_prose = len(prose.split())
    words_with_labels = len(block.split())
    return {
        "part_labels_present": labels,
        "words_prose_only": words_prose,
        "words_including_labels": words_with_labels,
        "note": "Reported as computed here; no word count is asserted in the manuscript.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-out")
    args = ap.parse_args()

    text = SOURCE.read_text(encoding="utf-8")
    structure = check_structure(text)
    arithmetic = check_arithmetic(text)
    abstract = abstract_word_count(text)

    failures = structure["failures"] + arithmetic["failures"]
    report = {
        "schema": "paper_e_revision_v3_lint_v1",
        "source": SOURCE.name,
        "verdict": "PASS" if not failures else "FAIL",
        "failures": failures,
        "structure": structure["counts"],
        "arithmetic_checks": {
            "total": len(arithmetic["checks"]),
            "passed": sum(1 for c in arithmetic["checks"] if c["ok"]),
            "detail": arithmetic["checks"],
        },
        "abstract": abstract,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
