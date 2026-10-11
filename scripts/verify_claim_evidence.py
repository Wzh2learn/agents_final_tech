#!/usr/bin/env python3
"""Verify paper/saner_rene_claim_matrix_v1.json evidence hashes against the raw bytes on this host.
Authority for these hashes is the GB10 raw bytes; run this on GB10 for a PASS/FAIL verdict.
LOCAL on Windows may differ on text files because of Git EOL normalisation (run with --report-eol to see that)."""
import argparse, hashlib, json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1] if (pathlib.Path(__file__).resolve().parent.name == "scripts") else pathlib.Path.cwd()
MATRIX = ROOT / "paper/saner_rene_claim_matrix_v1.json"

def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-eol", action="store_true", help="also report an EOL-normalised comparison")
    a = ap.parse_args()
    m = json.loads(MATRIX.read_text(encoding="utf-8"))
    ev = m.get("evidence_hashes", {})
    ok = miss = bad = norm_ok = 0
    rows = []
    for rel, want in sorted(ev.items()):
        p = ROOT / rel
        if not p.exists():
            rows.append(("MISSING", rel, want, "")); miss += 1; continue
        got = sha(p)
        if got == want:
            rows.append(("OK", rel, want, got)); ok += 1; continue
        if a.report_eol:
            alt = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            if alt == want:
                rows.append(("OK-EOL", rel, want, got)); norm_ok += 1; continue
        rows.append(("BAD", rel, want, got)); bad += 1
    for status, rel, want, got in rows:
        if status == "OK":
            print(f"OK       {rel}")
        else:
            print(f"{status:8} {rel}\n         want {want}\n         got  {got}")
    total = len(ev)
    verdict = "PASS" if (ok == total) else ("PASS_WITH_EOL_NORMALISATION" if a.report_eol and ok + norm_ok == total else "FAIL")
    print(f"\nevidence entries: {total} | exact {ok} | eol-normalised {norm_ok} | bad {bad} | missing {miss}")
    print(f"CLAIM_EVIDENCE_HASH_CHECK = {verdict}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())