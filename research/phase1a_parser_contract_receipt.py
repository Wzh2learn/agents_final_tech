"""Produce the phase1a parser_contract_receipt artifact (zero model, zero connect).

Checker procedure (protocol doc section 7): run the production header mapper
over original and injected headers, apply the frozen drop rule
(drop10 = (h_orig - h_inj) * 10, threshold 2.0) exactly as the frozen
checkpoint_discrimination_tables_v2 caliber, aggregate per family, optionally
reconcile against a frozen reference artifact, and emit a receipt whose fields
satisfy the contract gate `parser_contract` (status PASS, checker non-empty,
40-hex commit, ISO executed_at, input_sha256 over the three inputs).

Canonical fields follow the frozen caliber: unique normalized columns of the
ORIGINAL header (self-canonical, as in research/paper_t2_visibility_sensitivity.py);
the schema role contributes hash binding only. No data is invented: every
record derives from the supplied source_tables / injection_map files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_SCRIPTS = REPO / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import m1_statement_parser as mp  # noqa: E402  read-only import of the production matcher

DROP_THRESHOLD = 2.0
HEX40 = set("0123456789abcdef")


class ReceiptError(ValueError):
    """Fail-closed rejection with a machine-readable code."""

    def __init__(self, code: str, **detail: object) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def install_network_guard() -> None:
    """Any connect attempt raises; observed port set stays empty."""

    def _blocked(*_a: object, **_k: object) -> object:
        raise ReceiptError("zero_connect_violation")

    socket.socket.connect = _blocked  # type: ignore[method-assign]
    socket.create_connection = _blocked  # type: ignore[assignment]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unique_canonical(header: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for h in header:
        k = mp.normalize_header(h)
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(str(h))
    return out


def _map_header(header: list[str], canonicals: list[str]) -> dict[str, str]:
    fields = [mp.SchemaField(std, [std]) for std in canonicals]
    table = mp.SchemaTable(
        table_name="receipt", layout="grid", header_region_keywords=[], fields=fields
    )
    mapping, _unmapped = mp.map_headers(header, table)
    return mapping


def _h_rate(header: list[str], canonicals: list[str]) -> tuple[float, dict[str, str]]:
    n = len(canonicals)
    mapping = _map_header(header, canonicals)
    return (len(mapping) / n if n else 1.0), mapping


def compute(
    source_tables: dict,
    injection_map: dict,
    reference: dict | None,
) -> dict:
    by_uid = {t["uid"]: t["table"] for t in source_tables.get("tables", [])}
    entries: dict[str, list[dict]] = {}
    for e in injection_map.get("mapping", []):
        uid = e.get("uid")
        if not isinstance(uid, str) or not uid:
            raise ReceiptError("invalid_injection_entry", entry=e)
        entries.setdefault(uid, []).append(e)
    tables: list[dict] = []
    injections: list[dict] = []
    for uid in sorted(by_uid):
        inj_header = [str(c) if c is not None else "" for c in by_uid[uid][0]]
        orig_header = list(inj_header)
        for e in entries.get(uid, []):
            col = e.get("col")
            if not isinstance(col, int) or not 0 <= col < len(orig_header):
                raise ReceiptError("invalid_injection_entry", uid=uid, col=col)
            orig_header[col] = e["original"]
        canonicals = _unique_canonical(orig_header)
        h_orig, map_orig = _h_rate(orig_header, canonicals)
        h_inj, map_inj = _h_rate(inj_header, canonicals)
        drop10_full = round((h_orig - h_inj) * 10.0, 4)
        rows = []
        for e in sorted(entries.get(uid, []), key=lambda x: x["col"]):
            single = list(orig_header)
            single[e["col"]] = e["injected"]
            h_s, _map_s = _h_rate(single, canonicals)
            dH = round((h_orig - h_s) * 10.0, 4) / 10.0
            target_c = next(
                (c for c in canonicals
                 if mp.normalize_header(c) == mp.normalize_header(e["original"])),
                None,
            )
            absorbed_full = bool(target_c) and map_inj.get(target_c) == e["injected"]
            rows.append({
                "uid": uid, "col": e["col"], "type": e.get("type"),
                "original": e["original"], "injected": e["injected"],
                "canonical": target_c, "h_orig": round(h_orig, 6),
                "h_single": round(h_s, 6), "dH": round(dH, 6),
                "drop10": round(dH * 10.0, 4),
                "absorbed_full_injection": absorbed_full,
                "visible_frozen": not absorbed_full,
            })
        injections.extend(rows)
        tables.append({
            "uid": uid, "n_canonical": len(canonicals), "n_injections": len(rows),
            "h_orig": round(h_orig, 6), "h_inj": round(h_inj, 6),
            "drop10": drop10_full, "discriminated": drop10_full >= DROP_THRESHOLD,
        })
    by_family: dict[str, dict[str, int]] = {}
    for r in injections:
        fam = str(r["type"])
        slot = by_family.setdefault(fam, {"n": 0, "visible": 0, "absorbed": 0})
        slot["n"] += 1
        slot["visible" if r["visible_frozen"] else "absorbed"] += 1
    reasons: list[str] = []
    reconciliation = None
    if reference is not None:
        ref_tables = reference.get("g3_detail", {}).get("tables_discriminated_recomputed")
        got_tables = sum(1 for t in tables if t["discriminated"])
        ref_by_type = reference.get("g3_detail", {}).get("by_type_recomputed", {})
        fam_mismatch = {
            fam: {"ref": ref_by_type[fam], "got": by_family.get(fam)}
            for fam in ref_by_type
            if ref_by_type[fam]["n_injections"] != by_family.get(fam, {}).get("n")
            or ref_by_type[fam]["n_visible"] != by_family.get(fam, {}).get("visible")
        }
        reconciliation = {
            "tables_discriminated_ref": ref_tables,
            "tables_discriminated_got": got_tables,
            "family_mismatches": fam_mismatch,
        }
        if ref_tables is not None and ref_tables != got_tables:
            reasons.append("reconciliation_tables_discriminated_mismatch")
        if fam_mismatch:
            reasons.append("reconciliation_family_mismatch")
    return {
        "status": "FAIL" if reasons else "PASS",
        "checker": "research/phase1a_parser_contract_receipt.py",
        "drop_threshold": DROP_THRESHOLD,
        "tables": tables,
        "injections": injections,
        "by_family": by_family,
        "reconciliation": reconciliation,
        "reasons": reasons,
        "observed_ports": [],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-tables", required=True, type=Path)
    ap.add_argument("--schema", required=True, type=Path)
    ap.add_argument("--injection-map", required=True, type=Path)
    ap.add_argument("--reference", type=Path, default=None)
    ap.add_argument("--commit", required=True)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    commit = args.commit.strip()
    if len(commit) != 40 or not set(commit) <= HEX40:
        raise ReceiptError("invalid_parser_commit", commit=commit)
    install_network_guard()
    source = json.loads(args.source_tables.read_text(encoding="utf-8"))
    imap = json.loads(args.injection_map.read_text(encoding="utf-8"))
    ref = json.loads(args.reference.read_text(encoding="utf-8")) if args.reference else None
    first = compute(source, imap, ref)
    second = compute(source, imap, ref)
    if json.dumps(first, sort_keys=True) != json.dumps(second, sort_keys=True):
        raise ReceiptError("nondeterministic_compute")
    first["commit"] = commit
    first["executed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    first["input_sha256"] = {
        "source_tables": sha256_file(args.source_tables),
        "schema": sha256_file(args.schema),
        "injection_map": sha256_file(args.injection_map),
    }
    args.out.write_text(
        json.dumps(first, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"wrote {args.out} status={first['status']} reasons={first['reasons']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())