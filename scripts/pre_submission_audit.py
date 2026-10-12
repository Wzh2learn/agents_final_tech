#!/usr/bin/env python3
"""One-shot pre-submission audit for the SANER RENE package.

Groups: claim-evidence, figure binding, citations, anonymisation, format, artifact readiness.
Run on the authority host for exact hashes (GB10); LOCAL may differ on EOL for unpinned text files.
"""
from __future__ import annotations
import hashlib, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

fails = []
def group(name, ok, detail=""):
    print(f"[{name}] {'PASS' if ok else 'FAIL'} {detail}")
    if not ok: fails.append(name)

# 1 evidence + figure binding + citations + pins: delegate to the wide verifier
r = subprocess.run([sys.executable, str(ROOT/"scripts/verify_claim_evidence.py")],
                   capture_output=True, text=True)
wide_ok = "WIDE_EVIDENCE_CHECK = PASS" in r.stdout
group("evidence_integrity", wide_ok, "(claim matrix + figure binding + citations + prereg pins)")

# 2 anonymisation: source + PDF metadata
ID = ["BUPT", "wzh6520", "Wzh2learn", "JinRongAgents", "github.com", "testuser", "GB10", "jinrong-dev", "@bupt"]
scan_targets = [ROOT/"paper/saner_rene_manuscript_v1.md", ROOT/"paper/overleaf_bundle/saner_rene_manuscript_v1.tex"]
hits = []
for f in scan_targets:
    txt = f.read_text(encoding="utf-8", errors="ignore")
    hits += [f"{k} in {f.name}" for k in ID if k in txt]
meta_ok = True; meta_detail = ""
try:
    import pypdfium2 as pdfium
    d = pdfium.PdfDocument(str(ROOT/"paper/overleaf_bundle/saner_rene_manuscript_v1.pdf"))
    meta = d.get_metadata_dict()
    meta_ok = (meta.get("Author") or "") == ""
    meta_detail = f"pages={len(d)} author={meta.get('Author')!r}"
except Exception as e:
    meta_ok = False; meta_detail = f"pdf read failed: {e}"
group("anonymisation", (not hits) and meta_ok, meta_detail + ("" if not hits else f" | leaks: {hits}"))

# 3 format: page budget + forbidden claims in the compiled text
try:
    import pypdfium2 as pdfium
    d = pdfium.PdfDocument(str(ROOT/"paper/overleaf_bundle/saner_rene_manuscript_v1.pdf"))
    pages = len(d)
    full = " ".join(d[i].get_textpage().get_text_range() for i in range(pages))
    forb = ["hierarchy localizes failures", "confirms protocol blindness", "universal blind spots",
            "causal-aware checkpoint-selection validated"]
    low = full.lower()
    forb_hits = []
    for ph in forb:
        for m in re.finditer(re.escape(ph), low):
            pre = low[max(0, m.start()-24):m.start()]
            if not re.search(r"(no |not |never |without )$", pre):
                forb_hits.append(ph)
                break
    page_ok = pages <= 12
    q = full.count("??")
    group("format", page_ok and not forb_hits and q == 0,
          f"pages={pages} (<=12 incl. 2 ref pages) forbidden={forb_hits} '??'={q}")
except Exception as e:
    group("format", False, f"pdf read failed: {e}")

# 4 artifact readiness (preparation state, not release)
plan = ROOT/"research/positive_repair_20261011/ANONYMOUS_ARTIFACT_RELEASE_PLAN_v1.md"
bundle = ROOT/"paper/overleaf_bundle"
need = ["saner_rene_manuscript_v1.tex", "saner_rene_references.bib",
        "fig1_measurement_chain.pdf", "fig2_family_visibility_matrix.png",
        "fig3_localization_ablation.png", "saner_rene_manuscript_v1.pdf"]
missing = [n for n in need if not (bundle/n).exists()]
group("artifact_package", plan.exists() and not missing,
      f"plan={'present' if plan.exists() else 'MISSING'} bundle_missing={missing}")

print()
print("PRE_SUBMISSION_AUDIT = " + ("PASS" if not fails else "FAIL: " + ",".join(fails)))
print("NOTE: format/evidence checks require the GB10 (authority) host for byte-exact hashes; "
      "artifact publication remains an owner decision.")
sys.exit(0 if not fails else 1)