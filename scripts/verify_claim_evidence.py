#!/usr/bin/env python3
"""Wide evidence-integrity verifier (v2).

Groups:
  1. claim_matrix   - paper/saner_rene_claim_matrix_v1.json evidence_hashes
  2. figure_binding - docs/research/figures_saner/figure_source_binding_manifest.json outputs + source_artifacts
  3. citations      - every \cite key in the bundle .tex resolves in the .bib and every bib entry is cited
  4. prereg_pins    - PR-EXP-03 v3 prereg sha matches the value pinned in its implementation contract

Authority for raw hashes is the GB10 raw bytes. On Windows, text files may differ by Git EOL
normalisation; run with --report-eol to see the normalised comparison (LOCAL convenience only).
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def sha_eol(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()

def check_group(name, pairs, report_eol):
    """pairs: list of (label, path, expected)"""
    exact = norm = bad = miss = 0
    lines = []
    for label, p, want in pairs:
        if not p.exists():
            lines.append(f"  MISSING  {label}"); miss += 1; continue
        got = sha(p)
        if got == want:
            lines.append(f"  OK       {label}"); exact += 1; continue
        if report_eol and sha_eol(p) == want:
            lines.append(f"  OK-EOL   {label}"); norm += 1; continue
        lines.append(f"  BAD      {label}\n           want {want}\n           got  {got}"); bad += 1
    ok = bad == 0 and miss == 0 and (norm == 0 or report_eol)
    print(f"[{name}] exact {exact} | eol-normalised {norm} | bad {bad} | missing {miss} -> {'PASS' if ok else 'FAIL'}")
    for l in lines:
        if not l.strip().startswith("OK "):
            print(l)
    return ok, bad + miss

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--report-eol", action="store_true")
    a = ap.parse_args()
    failures = 0

    # 1 claim matrix
    m = json.loads((ROOT/"paper/saner_rene_claim_matrix_v1.json").read_text(encoding="utf-8"))
    pairs = [(rel, ROOT/rel, want) for rel, want in sorted(m.get("evidence_hashes", {}).items())]
    ok, f = check_group("claim_matrix", pairs, a.report_eol); failures += f

    # 2 figure binding manifest
    fm = json.loads((ROOT/"docs/research/figures_saner/figure_source_binding_manifest.json").read_text(encoding="utf-8"))
    pairs = []
    for fig, spec in fm.get("figures", {}).items():
        for o in spec.get("outputs", []):
            pairs.append((f"{fig}:{o['path']}", ROOT/o["path"], o["sha256"]))
        for s in spec.get("source_artifacts", []):
            pairs.append((f"{fig}:src:{s['path']}", ROOT/s["path"], s["sha256"]))
    ok, f = check_group("figure_binding", pairs, a.report_eol); failures += f

    # 3 citations
    tex = (ROOT/"paper/overleaf_bundle/saner_rene_manuscript_v1.tex").read_text(encoding="utf-8")
    bib = (ROOT/"paper/overleaf_bundle/saner_rene_references.bib").read_text(encoding="utf-8")
    cites = set()
    for mm in re.finditer(r"\\cite\{([^}]+)\}", tex):
        cites.update(k.strip() for k in mm.group(1).split(","))
    keys = {mm.group(1).strip() for mm in re.finditer(r"@\w+\{([^,]+),", bib)}
    missing = sorted(cites - keys); unused = sorted(keys - cites)
    c_ok = not missing and not unused
    print(f"[citations] cited {len(cites)} | bib {len(keys)} | missing {len(missing)} | unused {len(unused)} -> {'PASS' if c_ok else 'FAIL'}")
    for x in missing: print(f"  cited-but-missing: {x}")
    for x in unused: print(f"  bib-but-uncited : {x}")
    failures += len(missing) + len(unused)

    # 4 prereg pins
    run = ROOT/"research/positive_repair_20261011/runs_local_mirror/PR-EXP-03-v3"
    prereg = ROOT/"research/positive_repair_20261011/preregs/PR-EXP-03_prereg_v3.md"
    contract = run/"implementation_contract.md"
    sidecar = run/"implementation_contract.sha256"
    p_checks = []
    if prereg.exists() and contract.exists():
        rec = re.search(r"^PREREG_SHA256 = ([0-9a-f]{64})$", contract.read_text(encoding="utf-8"), re.M)
        p_checks.append(("prereg sha == contract PREREG_SHA256", rec is not None and rec.group(1) == sha(prereg)))
    if contract.exists() and sidecar.exists():
        p_checks.append(("contract sidecar matches contract", sidecar.read_text(encoding="utf-8").split()[0] == sha(contract)))
    if tex and (ROOT/"paper/overleaf_bundle/saner_rene_references.bib").exists():
        p_checks.append(("bundle tex cites the bundle bib", "saner_rene_references" in tex))
    p_ok = all(v for _, v in p_checks)
    print(f"[prereg_pins] {'PASS' if p_ok else 'FAIL'}")
    for label, v in p_checks:
        print(f"  {'OK ' if v else 'BAD'}  {label}")
    failures += sum(0 if v else 1 for _, v in p_checks)

    verdict = "PASS" if failures == 0 else "FAIL"
    print(f"\nWIDE_EVIDENCE_CHECK = {verdict}")
    return 0 if failures == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())