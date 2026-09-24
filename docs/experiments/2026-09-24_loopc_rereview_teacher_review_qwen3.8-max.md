# Loop C re-review of the revised evaluation-track manuscript (model qwen3.8-max)

> Re-review after the 2026-09-24 seven-point revision (commit 4de4741); evidence packet inline (revised manuscript + manifest), no tools, 1 turn(s), cost $0.2287.
> Verdict: ACCEPT; all seven prior major issues ADDRESSED; remaining items editorial only.
> Body is the session final message verbatim; landed by Loop D without edits.

# RE-REVIEW — paper/teacher_review_draft_v1.md (commit 4de4741, revised 2026-09-24)

## Part 1: Status of the seven previously reported major issues

### qwen3.8-max

**M1 — Abstract lacked the different-criterion caveat between 96 visible and 112/85/13 detected: ADDRESSED.**
The abstract now states: *"These protocol-level counts use a different signal from checkpoint visibility (threshold crossings of the final mapping text, or of aggregated scores), so they are not a partition of the 96 visible injections; Section 5.2 closes the checkpoint-level accounting explicitly."* This is reinforced in Section 5.2: *"Here end-to-end detection tests whether the final mapping text changes; it is not the canonical-correspondence visibility criterion behind 96/118. A changed source-header string can therefore count as end-to-end detection even when the canonical match is preserved, explaining why 112/118 exceeds 96/118."* The apparent paradox (112 > 96) that previously read as an inconsistency is now explained mechanistically.

**M2 — Corpus, judge, and primary matcher unnamed: ADDRESSED.**
Section 4.1 now names all three with provenance: *"the base is the frozen drift-v0 table set derived from public TAT-QA tables (data/research/drift_v0/input/tatqa_tables.json, sha256 3e7e0568…)"*; *"The primary matcher is the production greedy header matcher (scripts/m1_statement_parser.py, map_headers)"*; *"Semantic leaves are scored by the M2 judge pipeline … i.e. Qwen3.6-35B-A3B (Q4_K_M GGUF) served at 127.0.0.1:8004."* The injection map is also named with hash, seed (42), and ratio (0.3). This satisfies reproducibility naming without external citation.

**M3 — The 118-injection outcome accounting did not visibly close: ADDRESSED.**
Section 5.2 now closes it explicitly: *"The 118 injections close at the checkpoint level as 96 visible plus 22 silently absorbed; by family (injections / visible / absorbed): alias variant 47/43/4, date variant 17/15/2, mixed language 20/20/0, OCR-like 13/0/13, prefix noise 16/13/3, unit suffix 5/5/0 (frozen artifact t2_visibility_sensitivity.json…)."* I verified the arithmetic: family totals sum to 118 (47+17+20+13+16+5), visible to 96 (43+15+20+0+13+5), absorbed to 22 (4+2+0+13+3+0), and 96+22=118. The per-family fractions are also consistent with the stated 0.81–1.00 visibility range in Section 5.1 (13/16 = 0.8125 … 20/20 = 1.00).

**M4 — Method not bridged to the pruned-root instantiation: ADDRESSED.**
Section 3.1 now supplies the bridge: *"The visibility audit exercises the parsing-tree leaves whose evidence is the mapping and regression artifacts; under the frozen drop rule (drop = (H_orig - H_inj) x 10, threshold 2.0) only the field hit-rate leaf responds to header drift, while QA-tree leaves keep their frozen evidence and the QA arm is reported separately (12 calls at the same endpoint). This is precisely why additional localization value remains unestablished in the current instantiation."* The reader can now trace the general 12-leaf framework to the "Pruned parsing-root drop" detection signal in Table 1, and the single-varying-leaf limitation is derived from the method rather than asserted ad hoc.

### deepseek-v4-pro

**M1 — Deferred transfer/second-dataflow arm lacked reinstatement criteria: ADDRESSED.**
Section 6 now provides explicit criteria: *"Reinstatement criteria, not a timeline: the deferred arms return only when (i) a second dataflow with a table layer passes SOURCE_GO and SPLIT_GO with UID-disjoint layers, and (ii) a second scorer independent of the :8004 judge reproduces the leaf-state cells; until both hold, the arms remain preregistered-but-unreported."* These are falsifiable conditions tied to named gates, which is what was requested; a timeline was correctly not substituted for criteria.

**M2 — Affine-equivalence finding not labelled as a degenerate case: ADDRESSED.**
Section 5.2 now carries the label in a dedicated paragraph: *"We label the affine-equivalence observation a degenerate-case result: it fixes the interpretation of the raw gap under the current single-varying-leaf instantiation and does not establish affine equivalence of the protocols in general."* The abstract's *"affinely equivalent on this corpus"* phrasing is consistent with this scoping, and the required result itself (matched-FPR equivalence, bootstrap CI [0,0]) remains intact.

**M3 — Section 5.5 mechanism case structurally disconnected from the evaluation-track contribution: ADDRESSED.**
Section 5.5 now opens with an explicit role statement: *"Role of this section: it is boundary evidence for the third stage of the broader research program, not part of the evaluation-track contribution. It is included to mark where the evaluation evidence stops and the program's prospective claims begin."* Combined with *"This is not an efficacy claim"* and the non-significant statistics (paired-bootstrap 95% interval [0, 0.1056]; 7/40 vs 4/40, exact McNemar p=0.375 — which I confirm is the exact two-sided value for 4 vs 1 discordant pairs, n=5), the section is now framed as a demarcation device rather than a smuggled second contribution. The manifest's SP-C4 status ("mechanism_case_only") matches this framing.

## Part 2: New issues introduced by the revision

**No new blocking issues. No new major issues.** Two minor observations, neither blocking:

1. **Minor (terminology).** Table 1's detection signal "Pruned parsing-root drop" uses the word "pruned" as an unexplained term of art; Section 3.1's frozen drop rule effectively defines the operation (only the field hit-rate leaf responds), but stating once that "pruning" = collapsing the parsing root to its input-responsive leaf would remove the last inferential step for the reader. Editorial only.

2. **Minor (cross-reference).** Section 5.3's "120 leaf-state cells" (judge calibration) and Section 6 limitation 3's "one judge on 28 cases" (semantic boundary analysis) are distinct analyses, but a reader skimming could conflate them; a half-sentence distinguishing the two windows would help. Neither number is contradicted elsewhere.

Consistency checks performed on the revision: all internal counts agree (95 tables; 118 injections; 96/22 split; 112/85/13 protocol counts; Table 1 fractions 0.9492, 0.7895, 0.7203, 0.2105, 0.1102 all recompute correctly from their raw counts; seed spread 0.7895−0.7556 = 0.0339). The two protected results are intact: matched-FPR affine equivalence with a 2,000-replicate bootstrap CI of [0,0], and OCR-blind 0-of-13 across all five thresholds, including the per-family closure (13/0/13). No forbidden manuscript markers appear in the text. Per the stated rules, the patent-status gate and the blank author/affiliation/venue are administrative user policy and are not counted as scientific issues.

## Part 3: Overall verdict

**ACCEPT.**

All seven major issues from both prior reviews are ADDRESSED with verifiable in-text evidence, the 118-injection accounting now closes arithmetically, the negative results are stated at exactly the scope the evidence supports, and the two findings required to remain intact do. The remaining items are editorial polish suitable for a camera-pass, not conditions of acceptance. The manuscript's central discipline — *"Null and adverse findings are retained rather than relabeled as improvements"* — is now visibly honored in the text itself, which is the appropriate standard for an evaluation-track contribution.
