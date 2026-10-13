# Loop C Independent Audit - A1-A7 Revision (v2 + v3 close-out)

> date: 2026-10-13 | method: designed launcher (`scripts/graph/loop_ac_launcher.sh`, detached tmux on GB10, `claude` read-only) - NOT the app sub-agent facility, which failed for every dispatch this session (see `DELEGATION_HARNESS_FAILURE_AUDIT_v1.md`)
> final status: `INDEPENDENCE DELIVERED` - v3: item application PASS / claim boundary PASS; the package-consistency residual was one auditor-prescribed single-word caption fix, applied and machine-re-verified on both hosts. No third model audit (bounded per the one-re-audit discipline).
> raw logs: `research/positive_repair_20261011/loop_c_independent_audit_v2_result_raw.log`, `research/positive_repair_20261011/loop_c_independent_audit_v3_result_raw.log`

## 1. Chain of record

| Step | Task id | Result |
|---|---|---|
| Independent audit v2 | `a1a7-independent-audit-20261013` (rc=0, 05:00:48Z) | CONDITIONAL - nine residuals (A2 scope-lock naming; Section 4.3 noun; A7 tense; Section 1 scoping; Figure 3 caption spin; Section 5.1 attribution; abstract package stale; Figure 3 definition vs built figure; checklist/.tex wording) |
| Residual fix pass | commit `6655201` (LOCAL=origin=GB10) | 9/9 fixed: scope-lock row renamed; Section 4.3 resolved-wording; "prepared for release" tense; per-clause scoping; neutral caption; criterion-based 4/7 attribution; abstract package = verbatim manuscript abstract; figure_3 definitions aligned to the built ablation figure; checklist wording + .tex header; scope-lock pin corrected to the GB10 raw-byte (LF) hash `4c951e618ed6f5ffa8af84aeb6e55eb75b3a90b88cc36d660714f78aaa35f213`; docs + mirror manifests byte-identical |
| Independent re-audit v3 | `a1a7-reaudit-v3-20261013` (rc=0, 05:51:25Z) | items = PASS (9/9 RESOLVED); claim boundary = PASS; package consistency = CONDITIONAL (N1); independent = CONDITIONAL |
| Prescribed micro-fix | this close-out commit | N1 fixed exactly as prescribed (delete "also"); N2(b) bare "scored surface" -> "frozen scored surface"; rebuild; `PRE_SUBMISSION_AUDIT = PASS` + `WIDE_EVIDENCE_CHECK = PASS` on LOCAL and GB10 |

## 2. v3 findings and disposition

- **N1** (introduced by the (e) fix): the Figure 3 caption read "the majority-class macro-F1 reference (0.1667) is **also** plotted", implying the uniform-class baseline (0.3333) was plotted too; it is not (Panel A carries exactly one reference bar). Disposition: the word was deleted exactly as the auditor prescribed; the caption now reads "(0.1667) is plotted."; verified in the rebuilt PDF text.
- **N2** (minor, pre-existing): (a) Section 1 compresses two separately-stated findings into one clause - recorded only; the split is stated two sentences earlier and v3 passed items/claim boundary. (b) bare "the scored surface" -> fixed to "the frozen scored surface".
- **N3** (minor): "reproducible from the scripts prepared for release" - tense is factual; external reproducibility untested; recorded only.

## 3. v3 method note (disclosed by the auditor)

The v3 session's permission gate denied `python3`/`pdfinfo`/`pdftotext` (Loop C runs read-only without bypass flags), so it could not execute the two scripts; it read them and replicated every assertion manually (15/15 hashes; figure bindings; 21/21 citations; prereg pins; page/anonymity/forbidden checks). Loop D then ran both scripts natively on LOCAL and GB10: `WIDE_EVIDENCE_CHECK = PASS`, `PRE_SUBMISSION_AUDIT = PASS` (including the PDF `/Author` metadata surface, which the manual replication could not read).

## 4. What is claimed / not claimed

- Claimed: an independent, read-only audit via the designed channel verified all nine residuals and the claim boundary; the single word-level defect it found in the fix pass was removed exactly as prescribed and machine-re-verified on both hosts.
- Not claimed: permanent PASS beyond this frozen revision; scientific acceptance; any author/submission action (owner-gated). No third model re-run was performed (bounded discipline; this record is the audit closure).
