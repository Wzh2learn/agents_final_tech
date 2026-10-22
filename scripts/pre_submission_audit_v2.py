#!/usr/bin/env python3
"""Audit the actual ICAART submission source, PDF and private artifact candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE"
DEFAULT_SOURCE = ROOT / "paper/icaart_2027_submission_v1"
IDENTITY_MARKERS = (
    "BUPT",
    "wzh6520",
    "Wzh2learn",
    "JinRongAgents",
    "github.com",
    "testuser",
    "GB10",
    "jinrong-dev",
    "@bupt",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def table_blocks(tex: str) -> list[str]:
    return re.findall(r"\\begin\{table\}.*?\\end\{table\}", tex, flags=re.DOTALL)


def load_pdf_info(pdf_path: Path) -> tuple[int, str]:
    try:
        import pypdfium2 as pdfium

        document = pdfium.PdfDocument(str(pdf_path))
        metadata = document.get_metadata_dict() or {}
        return len(document), str(metadata.get("Author") or "")
    except ImportError:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        metadata = reader.metadata or {}
        return len(reader.pages), str(metadata.get("/Author") or "")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-dir", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--report-eol", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    package_dir = args.package_dir.resolve()
    source_dir = args.source_dir.resolve()
    tex_path = source_dir / "manuscript.tex"
    pdf_path = package_dir / "PAPER_E_ICAART_REVIEW.pdf"
    manifest_path = package_dir / "PACKAGE_MANIFEST.json"
    artifact_dir = package_dir / "PAPER_E_PRIVATE_ARTIFACT_CANDIDATE"
    checks: dict[str, dict[str, Any]] = {}

    def record(name: str, ok: bool, detail: Any) -> None:
        checks[name] = {"status": "PASS" if ok else "FAIL", "detail": detail}

    evidence_command = [sys.executable, str(ROOT / "scripts/verify_claim_evidence.py")]
    if args.report_eol:
        evidence_command.append("--report-eol")
    evidence = subprocess.run(evidence_command, capture_output=True, text=True, check=False)
    evidence_ok = evidence.returncode == 0 and "WIDE_EVIDENCE_CHECK = PASS" in evidence.stdout
    record(
        "evidence_integrity",
        evidence_ok,
        {
            "command": evidence_command,
            "returncode": evidence.returncode,
            "summary": evidence.stdout.strip().splitlines()[-1:] or [],
        },
    )

    tex = tex_path.read_text(encoding="utf-8")
    canonical_path = (package_dir / json.loads(manifest_path.read_text(encoding="utf-8"))["canonical_markdown"]).resolve()
    canonical = canonical_path.read_text(encoding="utf-8")
    identity_hits = [
        f"{marker}:{path.name}"
        for path, text in ((tex_path, tex), (canonical_path, canonical))
        for marker in IDENTITY_MARKERS
        if marker in text
    ]

    try:
        pages, pdf_author = load_pdf_info(pdf_path)
        pdf_error = None
    except Exception as exc:
        pages, pdf_author = -1, ""
        pdf_error = f"{type(exc).__name__}: {exc}"
    record(
        "anonymisation",
        not identity_hits and pdf_error is None and pdf_author == "",
        {"source_hits": identity_hits, "pdf_author": pdf_author, "pdf_error": pdf_error},
    )

    blocks = table_blocks(tex)
    table_checks = []
    for index, block in enumerate(blocks, start=1):
        table_checks.append(
            {
                "table": index,
                "caption": bool(re.search(r"\\caption\{", block)),
                "nine_point_small": bool(re.search(r"\\small(?:\s|$)", block)),
                "forbidden_scriptsize": bool(re.search(r"\\scriptsize(?:\s|$)", block)),
            }
        )
    format_checks = {
        "table_count": len(blocks),
        "tables": table_checks,
        "forbidden_reference_compression": bool(
            re.search(r"\\linespread\{(?:0\.[0-9]|1\.0)\}", tex)
        ),
        "unnumbered_acknowledgments": "\\section*{\\uppercase{Acknowledgments}}" in tex,
        "small_bibliography": bool(
            re.search(r"\{\\small\s*\\bibliographystyle\{apalike\}", tex)
        ),
    }
    format_ok = (
        len(blocks) == 4
        and all(row["caption"] and row["nine_point_small"] and not row["forbidden_scriptsize"] for row in table_checks)
        and not format_checks["forbidden_reference_compression"]
        and format_checks["unnumbered_acknowledgments"]
        and format_checks["small_bibliography"]
    )
    record("source_format", format_ok, format_checks)

    try:
        import pypdfium2 as pdfium

        document = pdfium.PdfDocument(str(pdf_path))
        text = " ".join(document[index].get_textpage().get_text_range() for index in range(len(document)))
    except ImportError:
        from pypdf import PdfReader

        text = "\n".join(page.extract_text() or "" for page in PdfReader(str(pdf_path)).pages)
    unresolved = text.count("??")
    forbidden_phrases = [
        "hierarchy localizes failures",
        "confirms protocol blindness",
        "universal blind spots",
        "causal-aware checkpoint-selection validated",
        "AI created no experimental evidence",
        "AI assistance created no experimental evidence",
    ]
    forbidden_hits = [phrase for phrase in forbidden_phrases if phrase.lower() in text.lower()]
    page_ok = 0 < pages <= 12
    record(
        "compiled_pdf",
        page_ok and unresolved == 0 and not forbidden_hits,
        {
            "path": str(pdf_path),
            "sha256": sha256_file(pdf_path),
            "pages": pages,
            "unresolved_references": unresolved,
            "forbidden_phrases": forbidden_hits,
        },
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    active_texts = {
        "canonical_markdown": canonical,
        "icaart_tex": tex,
        "compiled_pdf": text,
    }
    required_values = (
        "13.821",
        "13.820514366083984",
        "0.359",
        "442/305",
        "33/2",
        "0/13",
    )
    missing_values = {
        name: [value for value in required_values if value not in content]
        for name, content in active_texts.items()
    }
    full_precision_path = artifact_dir / "inputs/FINRANK_FULL_PRECISION_ROWS.json"
    full_precision = json.loads(full_precision_path.read_text(encoding="utf-8"))
    tfidf_strict = next(
        row
        for row in full_precision["rows"]
        if row["model"] == "TF-IDF" and row["tie_policy"] == "strict-win"
    )
    raw_gap = tfidf_strict["random"] - tfidf_strict["hard"]
    rounded_cell_gap = round(tfidf_strict["random"], 3) - round(tfidf_strict["hard"], 3)
    precision_check = {
        "raw_gap": raw_gap,
        "raw_gap_display": f"{raw_gap:.3f}",
        "rounded_cell_gap": rounded_cell_gap,
        "rounded_cell_gap_display": f"{rounded_cell_gap:.3f}",
        "source_gap_field": full_precision["source_gap_fields"]["TF-IDF"]["strict-win"],
    }
    precision_ok = (
        math.isclose(raw_gap, precision_check["source_gap_field"], rel_tol=0.0, abs_tol=1e-12)
        and precision_check["raw_gap_display"] == "13.821"
        and precision_check["rounded_cell_gap_display"] == "13.820"
        and "| TF-IDF | strict-win | 77.030 | 90.850 | 13.821 |" in canonical
        and "TF-IDF & strict-win & 77.030 & 90.850 & 13.821 \\\\" in tex
    )
    nonwhite_counts = {
        name: len(re.sub(r"\s+", "", content))
        for name, content in (("canonical_markdown", canonical), ("icaart_tex", tex))
    }
    record(
        "cross_version_consistency",
        not any(missing_values.values())
        and precision_ok
        and all(10_000 <= count <= 50_000 for count in nonwhite_counts.values()),
        {
            "missing_values": missing_values,
            "precision_check": precision_check,
            "nonwhite_counts": nonwhite_counts,
        },
    )

    path_fields = ("review_pdf", "canonical_markdown")
    missing_manifest_paths = [
        field for field in path_fields if not (package_dir / manifest[field]).resolve().is_file()
    ]
    icaart_tex_manifest = Path(manifest["icaart_tex"])
    missing_manifest_paths += (
        []
        if (package_dir / icaart_tex_manifest).resolve().is_file()
        else ["icaart_tex"]
    )
    record(
        "manifest_paths",
        not missing_manifest_paths,
        {"checked": list(path_fields) + ["icaart_tex"], "missing": missing_manifest_paths},
    )

    hash_bindings = {
        "review_pdf_sha256": (sha256_file(pdf_path), str(manifest["review_pdf_sha256"]).lower()),
        "canonical_markdown_sha256": (sha256_file(canonical_path), str(manifest["canonical_markdown_sha256"]).lower()),
        "icaart_tex_sha256": (sha256_file(tex_path), str(manifest["icaart_tex_sha256"]).lower()),
        "private_artifact_candidate_sha256": (
            sha256_file(package_dir / manifest["private_artifact_candidate"]),
            str(manifest["private_artifact_candidate_sha256"]).lower(),
        ),
        "private_artifact_reproduction_receipt_sha256": (
            sha256_file(package_dir / manifest["private_artifact_reproduction_receipt"]),
            str(manifest["private_artifact_reproduction_receipt_sha256"]).lower(),
        ),
    }
    bad_hash_bindings = {
        name: {"actual": actual, "manifest": expected}
        for name, (actual, expected) in hash_bindings.items()
        if actual != expected
    }
    record("manifest_hashes", not bad_hash_bindings, bad_hash_bindings)

    required_artifact_files = (
        "README.md",
        "REPRODUCE.sh",
        "LICENSES.md",
        "MANIFEST.json",
        "REPRODUCTION_RECEIPT.json",
        "FINRANK_COMPACT_ROWS.json",
        "reproduce.py",
        "inputs/G1_SEED_REANALYSIS.json",
        "inputs/FINRANK_FULL_PRECISION_ROWS.json",
    )
    missing_artifact = [
        name for name in required_artifact_files if not (artifact_dir / name).is_file()
    ]
    artifact_manifest = json.loads((artifact_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    expected_artifact_files = {entry["path"] for entry in artifact_manifest["files"]}
    actual_artifact_files = {
        str(path.relative_to(artifact_dir)).replace("\\", "/")
        for path in artifact_dir.rglob("*")
        if path.is_file() and path.name not in {"MANIFEST.json", "REPRODUCTION_RECEIPT.json"}
    }
    artifact_entry_errors = []
    for entry in artifact_manifest["files"]:
        path = artifact_dir / entry["path"]
        if not path.is_file():
            artifact_entry_errors.append({"path": entry["path"], "error": "missing"})
            continue
        actual_hash = sha256_file(path)
        if path.stat().st_size != entry["bytes"] or actual_hash != entry["sha256"]:
            artifact_entry_errors.append(
                {
                    "path": entry["path"],
                    "error": "size_or_hash_mismatch",
                    "actual_bytes": path.stat().st_size,
                    "expected_bytes": entry["bytes"],
                    "actual_sha256": actual_hash,
                    "expected_sha256": entry["sha256"],
                }
            )
    receipt = json.loads((artifact_dir / "REPRODUCTION_RECEIPT.json").read_text(encoding="utf-8"))
    artifact_integrity = {
        "missing_required": missing_artifact,
        "missing_manifest_entries": sorted(expected_artifact_files - actual_artifact_files),
        "extra_files": sorted(actual_artifact_files - expected_artifact_files),
        "entry_errors": artifact_entry_errors,
        "receipt_status": receipt.get("status"),
    }
    record(
        "private_artifact_candidate",
        not missing_artifact
        and not artifact_integrity["missing_manifest_entries"]
        and not artifact_integrity["extra_files"]
        and not artifact_entry_errors
        and receipt.get("status") == "PASS",
        {"path": str(artifact_dir), "integrity": artifact_integrity, "public_release": False},
    )

    report = {
        "schema": "icaart_package_pre_submission_audit_v2",
        "target": {
            "package_dir": str(package_dir),
            "source_dir": str(source_dir),
            "tex": str(tex_path),
            "pdf": str(pdf_path),
        },
        "checks": checks,
        "status": "PASS" if all(item["status"] == "PASS" for item in checks.values()) else "FAIL",
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
