ACK FIRST LINE: ACK pe-l1-v4-postresult: Loop C independent post-result auditor

ROLE: Loop C independent auditor on GB10. Read-only. Do not modify v4 results.

GOAL:
Independently re-derive the 59 held-out labels and recompute the rates from the frozen contract
and raw inputs. This is a post-result arithmetic and semantics audit; do not change any file and
do not re-open the design.

PIN BLOCK:
- contract v3 sha256 = 322c3b380d9f36d2603e89eef49f296d86c012497b442ec9c77b36c0adbdc8aa
- runner sha256 = 55893b65f2d4aa201f1ecdb24438a33490cc350a0311ac58d6d0f69ba86d38d4
- results sha256 = b412c3cba9da0f9db803423b03fa2fe0ff26dadf8d524252d2195701f48cd7d2
- receipt sha256 = e2123cc5c5b82adeb76711e4daf788f841453cc5f409ecfe773ba99ee8b777b7
- labels frozen sha256 = c17e31af7b808161cc36102672317ed65de4d8424b31b0852ae5a7fe079d86cf

CHECKS:
1. Verify all pin hashes.
2. Re-derive each held-out label independently from the contract text and raw frozen inputs,
   without importing run_v4.py. Compare to V4_RESULTS_v1.json case rows.
3. Recompute label_counts E/H/U, u_rate_heldout, 2x3 contingency, co_miss and co_alarm.
4. Verify only held-out rows are present; no dev label was used for any decision.
5. Verify checker verdicts were read only after the labels_frozen hash was written/reserved.
6. Report any label mismatch or arithmetic mismatch with counterexample.
7. Confirm claim boundary: no population, OCR, or harmful-blind-spot claim.

OUTPUT:
Write only if permitted: research/paper_e_layer1_20261015/v4/V4_LOOP_C_POSTRESULT_AUDIT_v1.md
Otherwise give the full audit inline.

End with VERDICT: PASS / CONDITIONAL / FAIL.

FORBIDDEN:
No design changes; no edits; no git write; no model/network/training call beyond this audit.
