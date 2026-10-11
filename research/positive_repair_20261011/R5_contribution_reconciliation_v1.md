# R5 Contribution Reconciliation v1

> date: 2026-10-11 | Loop D decision (read-only reconciliation) | authority = paper/saner_rene_manuscript_scope_lock_v1.md (FROZEN_SCOPE) + paper/saner_rene_claim_matrix_v1.json (C1-C3) | NO scientific change

## The decompositions found in the repo
1. Evaluation-track draft (paper/teacher_review_draft_v1.md, 2026-09-22): 3 contributions - (C1) construct separation; (C2) quantified observation boundaries; (C3) structural protocol identifiability audit.
2. Scope lock (paper/saner_rene_manuscript_scope_lock_v1.md) = AUTHORITY: 3 contributions - (1) construct separation and observation boundaries; (2) structural identifiability and instrumentation; (3) measurement-object alignment and failed transfer.
3. Version-B proposal (research/stage_e_multileaf_20261010/loop_d_inputs/stage_e_version_b_revision_proposal_v1.md): 3 contributions - (1) construct separation and observation boundaries; (2) protocol identifiability; (3) stage-aligned instrumentation (contract-derived signature). Its item 3 does NOT include the FinQA / measurement-object contribution.
4. Internal fine-grained claim ledger (paper/claim_manifest_v1.json): 5 claims SP-C1..SP-C5.

## Canonical decision
The scope-lock decomposition is canonical (frozen). paper/saner_rene_manuscript_v1.md Section 1 already states exactly these three contributions (construct separation with quantified family-level observation boundaries; a protocol-identifiability audit including clean-only matched-FPR non-identifiability and a construction-bounded instrumentation result with its ablation; and a failed-transfer autopsy consistent with a measurement-object mismatch). No manuscript change is required.

## Mapping: manuscript contributions
- (a) Construct separation + quantified family-level observation boundaries <- draft C1+C2; scope-lock 1; V-B 1; claims SP-C1 (visibility is type-dependent, OCR-like 0/13) + SP-C3 (blind-family stability across matchers/seeds).
- (b) Protocol-identifiability audit (clean-only matched-FPR non-identifiability + construction-bounded stage-aligned instrumentation with its ablation) <- draft C3; scope-lock 2; V-B 2 + V-B 3; claim SP-C2.
- (c) Failed-transfer autopsy consistent with a measurement-object mismatch <- scope-lock 3; claim SP-C5. V-B omitted this as a numbered contribution; it appears only as V-B abstract/§4 material. The scope-lock is correct.

## 5 -> 3 claim mapping
- SP-C1 -> C1
- SP-C3 -> C1
- SP-C2 -> C2
- SP-C5 -> C3
- SP-C4 ("evaluation findings can be routed through a gated deterministic consolidation loop") -> NOT a paper claim: internal method note, superseded by the measurement-validity framing. Retired from the paper's contribution/claim set; no replacement claim added.

Result: 5 internal claims map to the 3 paper claims; SP-C4 retired.

## Superseded items (do not re-derive)
- Draft C2 as a standalone contribution is subsumed into (a).
- V-B contribution 3 (instrumentation-only) is subsumed into (b); V-B's omission of the FinQA contribution is corrected by the scope-lock.
- "Hierarchy localizes failures" and any C4 gated-consolidation claim stay FORBIDDEN/deferred per the claim matrix.

## Verification
- manuscript Section 1 contributions sentence == scope-lock 3 contributions (verbatim alignment checked).
- claim matrix holds exactly 3 allowed claims (C1-C3), the same partition.

Status: R5 CLOSED (documentation reconciliation; no claim change; manuscript already aligned). Labels: FACT / INFERENCE as noted.