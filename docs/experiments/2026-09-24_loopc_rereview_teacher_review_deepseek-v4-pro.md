# Loop C re-review of the revised evaluation-track manuscript (model deepseek-v4-pro)

> Re-review after the 2026-09-24 seven-point revision (commit 4de4741); evidence packet inline (revised manuscript + manifest), no tools, 1 turn(s), cost $0.1129.
> Verdict: ACCEPT; all seven prior major issues ADDRESSED.
> Body is the session final message verbatim; landed by Loop D without edits.

# RE-REVIEW after revision

## Previously reported major issues

### qwen3.8-max

**M1 — Abstract lacked the different-criterion caveat between 96 visible and 112/85/13 detected.**
**ADDRESSED.** The revised abstract now states: "These protocol-level counts use a different signal from checkpoint visibility (threshold crossings of the final mapping text, or of aggregated scores), so they are not a partition of the 96 visible injections; Section 5.2 closes the checkpoint-level accounting explicitly."

**M2 — Corpus, judge, and primary matcher unnamed.**
**ADDRESSED.** Section 4.1 now names all three: the corpus via frozen-artifact paths and SHA-256 hashes ("derived from public TAT-QA tables…sha256 3e7e0568…"), the judge ("Qwen3.6-35B-A3B (Q4_K_M GGUF) served at 127.0.0.1:8004"), and the primary matcher ("the production greedy header matcher (scripts/m1_statement_parser.py, map_headers)").

**M3 — The 118-injection outcome accounting did not visibly close.**
**ADDRESSED.** Section 5.2 now closes the accounting explicitly: "The 118 injections close at the checkpoint level as 96 visible plus 22 silently absorbed; by family (injections / visible / absorbed): alias variant 47/43/4, date variant 17/15/2, mixed language 20/20/0, OCR-like 13/0/13, prefix noise 16/13/3, unit suffix 5/5/0." 43+15+20+0+13+5 = 96 visible; 4+2+0+13+3+0 = 22 absorbed; 96+22 = 118.

**M4 — Method description not bridged to the pruned-root instantiation.**
**ADDRESSED.** Section 3.1 now bridges the gap: "under the frozen drop rule (drop = (H_orig − H_inj) × 10, threshold 2.0) only the field hit-rate leaf responds to header drift, while QA-tree leaves keep their frozen evidence…This is precisely why additional localization value remains unestablished in the current instantiation."

### deepseek-v4-pro

**M1 — Deferred transfer/second-dataflow arm lacked reinstatement criteria.**
**ADDRESSED.** Section 6 now provides explicit reinstatement criteria: "the deferred arms return only when (i) a second dataflow with a table layer passes SOURCE_GO and SPLIT_GO with UID-disjoint layers, and (ii) a second scorer independent of the :8004 judge reproduces the leaf-state cells; until both hold, the arms remain preregistered-but-unreported."

**M2 — Affine-equivalence finding not labelled as a degenerate case.**
**ADDRESSED.** Section 5.2 now states: "We label the affine-equivalence observation a degenerate-case result: it fixes the interpretation of the raw gap under the current single-varying-leaf instantiation and does not establish affine equivalence of the protocols in general."

**M3 — Section 5.5 mechanism case structurally disconnected from the evaluation-track contribution.**
**ADDRESSED.** Section 5.5 opens with an explicit role statement: "Role of this section: it is boundary evidence for the third stage of the broader research program, not part of the evaluation-track contribution. It is included to mark where the evaluation evidence stops and the program's prospective claims begin."

---

## New blocking or major issues introduced by the revision

None. The internal accounting is now closed and self-consistent. The 118 family breakdown sums correctly (43+15+20+0+13+5 = 96 visible; 4+2+0+13+3+0 = 22 absorbed). The different-criterion caveat between visibility and protocol detection is stated in the abstract and closed in Section 5.2. The [0,0] matched-FPR bootstrap CI is explained by the single-varying-leaf construction without overclaiming. The mechanism case in Section 5.5 is explicitly demarked as non-contribution boundary evidence. No numbers are invented; the two administrative gates are treated as user policy; the OCR-blind 0-of-13 result and the affine-equivalence finding remain intact as required.

---

## Overall verdict: **ACCEPT**

All seven previously reported issues are addressed with quoted in-manuscript evidence. No new blocking or major issues are present. The revision is internally consistent, properly scoped, and the evidential claims trace to frozen artifacts enumerated in the manifest.
