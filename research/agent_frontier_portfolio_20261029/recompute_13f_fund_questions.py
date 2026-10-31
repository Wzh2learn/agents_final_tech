#!/usr/bin/env python3
"""Recompute two exposed SkillLearnBench fund questions from one 13F archive.

Reference answers are opened only after the source-derived figures are
computed. The instrumented source is a public development task; this is not an
independent confirmation, financial advice or total-AUM verification.
"""
import argparse
import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile


TARGET_PERIOD = "30-SEP-2025"
MANAGERS = {"financial-analysis-1": "renaissance technologies",
            "financial-analysis-2": "bridgewater associates"}


def iter_rows(archive, basename):
    members = [name for name in archive.namelist() if name == basename or name.endswith("/" + basename)]
    if len(members) != 1:
        raise ValueError("expected exactly one " + basename)
    with archive.open(members[0]) as binary:
        with io.TextIOWrapper(binary, encoding="utf-8-sig", errors="strict", newline="") as text:
            yield from csv.DictReader(text, delimiter="\t")


def select_unique(covers, period_by_accession, name):
    matches = [r for r in covers if name in r["FILINGMANAGER_NAME"].casefold()
               and period_by_accession.get(r["ACCESSION_NUMBER"]) == TARGET_PERIOD]
    if len(matches) != 1:
        raise ValueError("target manager and period are not uniquely identified")
    return matches[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive", type=Path)
    ap.add_argument("task_root", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    with ZipFile(args.archive) as source:
        periods = {r["ACCESSION_NUMBER"]: r["PERIODOFREPORT"] for r in iter_rows(source, "SUBMISSION.tsv")}
        covers = list(iter_rows(source, "COVERPAGE.tsv"))
        chosen = {task: select_unique(covers, periods, manager) for task, manager in MANAGERS.items()}
        selected = {row["ACCESSION_NUMBER"]: task for task, row in chosen.items()}
        summary = {selected[row["ACCESSION_NUMBER"]]: row for row in iter_rows(source, "SUMMARYPAGE.tsv")
                   if row["ACCESSION_NUMBER"] in selected}
        if set(summary) != set(MANAGERS):
            raise ValueError("a selected manager has no summary")
        details = {task: {"row_count": 0, "cusips": set(), "issuers": set(), "option_rows": 0, "value_sum": Decimal(0)}
                   for task in MANAGERS}
        for row in iter_rows(source, "INFOTABLE.tsv"):
            task = selected.get(row["ACCESSION_NUMBER"])
            if task is None:
                continue
            entry = details[task]
            entry["row_count"] += 1
            entry["value_sum"] += Decimal(row["VALUE"].strip())
            if row["CUSIP"].strip():
                entry["cusips"].add(row["CUSIP"].strip())
            if row["NAMEOFISSUER"].strip():
                entry["issuers"].add(row["NAMEOFISSUER"].strip().casefold())
            if row["PUTCALL"].strip():
                entry["option_rows"] += 1
    results = {}
    for task, manager in chosen.items():
        entry = details[task]
        computed = {"manager_name": manager["FILINGMANAGER_NAME"], "period": TARGET_PERIOD,
                    "summary_entry_total": int(summary[task]["TABLEENTRYTOTAL"]),
                    "summary_value_raw": int(summary[task]["TABLEVALUETOTAL"]),
                    "sum_infotable_values_raw": str(entry["value_sum"]),
                    "sum_equals_summary_value": entry["value_sum"] == Decimal(summary[task]["TABLEVALUETOTAL"]),
                    "infotable_rows": entry["row_count"], "distinct_cusips": len(entry["cusips"]),
                    "distinct_issuer_strings": len(entry["issuers"]), "option_rows": entry["option_rows"]}
        reference_path = args.task_root / task / "tests/expected_output.json"
        expected = json.loads(reference_path.read_text(encoding="utf-8"))
        computed["reference_q1"] = expected["q1_answer"]
        computed["reference_q2"] = expected["q2_answer"]
        computed["reference_sha256_raw"] = hashlib.sha256(reference_path.read_bytes()).hexdigest()
        computed["reference_q1_divided_by_summary_value"] = expected["q1_answer"] / computed["summary_value_raw"]
        computed["reference_q1_equals_infotable_sum"] = Decimal(str(expected["q1_answer"])) == entry["value_sum"]
        computed["reference_q2_equals_infotable_rows"] = expected["q2_answer"] == computed["infotable_rows"]
        computed["reference_q2_equals_distinct_cusips"] = expected["q2_answer"] == computed["distinct_cusips"]
        results[task] = computed
    result = {"status": "POST_HOC_DEVELOPMENT_REFERENCE_CHECK", "tasks": results,
              "limitations": ["one selected filing per manager based on visible substring and period",
                              "13F reportable holdings are not a complete measure of total fund AUM",
                              "Q3 only; no return, migration or agent performance evaluated",
                              "input ZIP not byte-matched to the SEC archive"]}
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
