# Independent Audit Packet v1 (evidence-debt repayment)

> date: 2026-10-11 | purpose: everything a fresh-context Loop C auditor needs, so the outstanding independent audits are a single step rather than a re-derivation
> status: READY_TO_RUN | blocking: none for submission (see "Why this is not blocking")

## Outstanding independent audits (in priority order)

### A. PR-03 v3 result (branch closure)
Packet: `PR-03_v3_RESULT_v1.md`; prereg `preregs/PR-EXP-03_prereg_v3.md` (sha256 4c632300...); implementation `runs_local_mirror/PR-EXP-03-v3/experiment_v3.py`; reference `.../experiment_v2_reference.py`; contract `.../implementation_contract.md`; preflight receipt `.../execution_preflight_receipt.json`; point estimates `.../point_diagnostic_output.txt`.
Questions for the auditor:
1. Does the NEGATIVE classification follow from the frozen rule and the recorded point estimates?
2. Is the claim "the frozen v2 implementation is non-executable as delivered" verifiable from the file alone?
3. Is the claim "the frozen diagnostic bootstrap is computationally infeasible" sound (predict_loco complexity), and does the round-1 runtime (275 s) therefore not belong to that code?
4. Is the supersession of the round-1 metrics/receipt justified?
Run: `python3 scripts/verify_claim_evidence.py` (GB10) ; read the files above. Do NOT re-run the experiment.

### B. Spillover audit (PR-03 vs Track A)
Packet: `PR03_SPILLOVER_AUDIT_v1.md`.
Questions: are the three defects really confined to the Track P lineage; is the multi-leaf provenance chain independent; is any manuscript number touched?
Run: repeat the token sweep (`PR-EXP-03|positive_repair|predict_loco|field_hit|a1_table|a3_fp`) over `paper/`, `docs/research/`, `logs/graph/eval/` and the claim matrix's evidence list.

### C. Submission package (pre-submission certification)
Packet: `PDF_LAYOUT_AUDIT_v1.md`, `paper/overleaf_bundle/` (tex + bib + 4 figure assets + PDF), `ABSTRACT_REGISTRATION_PACKAGE_v1.md`, `paper/SANER_RENE_2027_REQUIREMENTS.md`.
Questions: page budget compliance; reference resolution; anonymisation (source + PDF metadata); figure integrity vs the binding manifest; no forbidden claim in the compiled text.
Run: `python3 scripts/verify_claim_evidence.py` (GB10), `python -c "import pypdfium2..."` page count, and a text scan of the bundle `.tex` for forbidden phrases.

## Evidence-debt ledger (what is still uncertified)
| Item | Why it is open | Impact if wrong |
|---|---|---|
| Loop C independence for PR-03 v3 / spillover | harness never delivered the auditor agent; audits are Loop D self-audits | branch closure rests on a self-audit (Track P is not paper evidence, so paper risk is nil) |
| PR-03 v3 diagnostic bootstrap CI | frozen `predict_loco` O(groups^2) makes the frozen 10k bootstrap infeasible | the v3 verdict is a point-estimate determination, not a completed frozen run |
| OCR `0/13` precision | wide intervals by construction (0-24.71% / 0-28.49%) | correctly reported as a boundary, not a rate estimate |
| Single-corpus evidence | one frozen public corpus + synthetic perturbations | external-validity limitation, already the paper's stated #1 limitation |

## Why this is not blocking
PR-03 is `DECLINE_CITE` and the spillover audit is CLEAN, so no manuscript claim depends on any uncertified item. These audits raise confidence in branch bookkeeping, not in the paper.

## How to run (when a real independent auditor is available)
1. Hand the auditor this packet plus the listed files (read-only).
2. Require per-question FACT/INFERENCE/UNVERIFIED labels and a final verdict line per audit.
3. Record the verdicts back into the registry (`POSITIVE_REPAIR_REGISTRY_v1.json`) and this packet.