# Confirmation review of camera-pass commit a0f4d3d (model qwen3.8-max)

> Dispatched 2026-09-24; evidence packet inline (camera-pass diff, the two re-review minors, current manuscript); no tools; 1 turn(s), cost $0.1880.
> Verdict: ACCEPT - both minors closed; diff is a clean editorial pass with zero numeric, protected-result or claim-scope drift; manuscript at head stands ACCEPTed.
> Body verbatim.

**Task 1 — Minor 1 (pruned terminology) closed: PASS**

The diff hunk at §3.1 appends exactly the requested one-time definition:

> "In Table 1, the label 'pruned parsing-root drop' denotes exactly this operation: the parsing root is collapsed to its single input-responsive leaf (the field hit-rate leaf) and the drop rule above is applied there."

This matches the re-review's requested fix verbatim in substance ("stating once that pruning = collapsing the parsing root to its input-responsive leaf"). Verification points:
- The sentence explicitly binds to the Table 1 row label ("In Table 1, the label 'pruned parsing-root drop'"), so the term of art is no longer unexplained at point of use.
- "the drop rule above" resolves unambiguously to the frozen rule stated earlier in the same paragraph: "(drop = (H_orig - H_inj) x 10, threshold 2.0)".
- Internal consistency holds: the same paragraph states "only the field hit-rate leaf responds to header drift," and §5.2 states "only one scored leaf varies with the input" — so "single input-responsive leaf (the field hit-rate leaf)" is consistent with the manuscript's own account, not a new claim.
- The sentence is present, character-identical, in the inline current manuscript head at §3.1.

**Task 2 — Minor 2 (120-cell vs 28-case window conflation) closed: PASS**

The diff adds the distinguishing clause bidirectionally:

§5.3 (calibration side): "Judge calibration covers 120 leaf-state cells; **this calibration window is distinct from the 28-case semantic boundary analysis reported in Section 6.**"

§6 limitation 3 (boundary-analysis side): "...mixed-language and unit-suffix families receive no calls in that window **(a separate window from the 120-cell judge calibration of Section 5.3)**."

Verification points:
- Both cross-references are accurate against the manuscript structure: the "one judge on 28 cases" semantic boundary analysis is in Section 6 limitation 3, and the "120 leaf-state cells" judge calibration is in Section 5.3.
- Counts are consistent across the two mentions (120 / 120-cell; 28 cases / 28-case) — no number was altered or introduced inconsistently.
- This exceeds the "half-sentence" the re-review asked for by disambiguating from both directions, eliminating the conflation risk for readers entering either section first.
- Both clauses appear, character-identical, in the inline current manuscript head.

**Task 3 — No new blocking/major issue; no numeric, protected-result, or claim-scope change: PASS**

Character-level comparison of the three changed lines (diff "+" lines vs. inline current manuscript head):

1. **§3.1 line:** the shared prefix ("The twelve scored nodes are five in the parsing tree ... remains unestablished in the current instantiation.") is byte-identical between the "−" line, the "+" line, and the head manuscript; the only delta is the appended definitional sentence, which matches the head exactly. Numbers on this line — "five", "seven", "v0.1.0", "x 10", "threshold 2.0", "12 calls" — are unchanged between "−" and "+". The added sentence introduces no numeric value.
2. **§5.3 line:** the only delta is "cells." → "cells; this calibration window is distinct from the 28-case semantic boundary analysis reported in Section 6." All numeric content — "120 leaf-state cells", "0–5", "at most 0.5", "0–10", "at most 0.22", "as much as 7.0" — is identical between "−" and "+". The remainder of the paragraph ("In the control-state comparison ... cell-level interchangeability.") is character-identical across all three versions.
3. **§6 line:** the only delta is insertion of the parenthetical "(a separate window from the 120-cell judge calibration of Section 5.3)" before the period after "that window". All protected results on this line — "one judge on 28 cases", "0.952381 to 0.597015" — are unchanged. The remainder ("Four limitations bound the claim ... score construction rather than allocation.") is character-identical.

Scope check: all three insertions are purely definitional/cross-referential prose. No empirical claim is added, strengthened, or weakened; the degenerate-case framing, the "additional localization value remains unestablished" hedge, and all limitation boundaries are untouched. No new blocking or major issue arises.

Two non-blocking editorial notes (below the minor threshold, no action required): (a) the §3.1 sentence quotes the label in lowercase ('pruned parsing-root drop') while Table 1 capitalizes it ("Pruned parsing-root drop") — trivial casing variance; (b) the commit message references proposal §5.6 and DOCX regeneration, but the camera-pass diff is manuscript-only, so nothing outside `paper/teacher_review_draft_v1.md` affects this verdict.

**Overall verdict: ACCEPT**

Both minor observations from the dual-model re-review are fully closed by the camera-pass diff; the diff is a clean editorial pass with zero numeric, protected-result, or claim-scope drift. The manuscript at head a0f4d3d stands ACCEPTed.
