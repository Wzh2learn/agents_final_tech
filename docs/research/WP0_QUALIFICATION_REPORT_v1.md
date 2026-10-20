# WP0_QUALIFICATION_REPORT_v1.md

> date: 2026-10-13 | author: Loop D (executing the WP-0 read-only qualification) | status: `QUALIFICATION_REPORT_ONLY / G-RQ=PENDING / G-M=PENDING / EXPERIMENT_NOT_RUN` (TAT-QA update 2026-10-13: see Sec.10; A1-A6 closed)
> authority: [论文 E 投稿门禁](../PAPER_E_SUBMISSION_READINESS_GATE_v1.md), [SANER 科学裁决](SANER_SCIENTIFIC_ADJUDICATION_v1.md), [研究执行入口](../archive/2026-10-20_entry_consolidation/MASTER_RESEARCH_EXECUTION_ENTRY_v1.md), [执行蓝图](THESIS_EXECUTION_BLUEPRINT_v1.md), [WP-0 task card](../archive/2026-10-20_entry_consolidation/thesis_experience_v1_task_card.md)
> Rule applied: read-only material verification. No download, no data-body access, no model call, no runner, no production service. Nothing was inferred where the record is silent.

## 1. WP-0 checklist status (task card §6)

| # | WP-0 item | Status | Evidence |
|---|---|---|---|
| 1 | Exact source / revision / licence / file scope, experience-development-pilot IDs, origin and near-duplicate grouping | **PARTIAL** | Ten candidate sources are recorded with paper IDs, official repos, checked default heads and repo-level SPDX in `docs/datasets/paper-public-source-registry-v1.json`; **none is download-approved** (`download_approved: false` on every row, registry status `METADATA_ONLY_NOT_DOWNLOAD_APPROVAL`). No origin-level or near-duplicate grouping exists for any candidate, and no experience/development/pilot IDs exist. |
| 2 | Reference-target vs real-execution design chain | **DESIGN ONLY** | The task card defines the target (two-period increase/decrease with unit unification) and requires independent verification of field, period, unit and arithmetic. No concrete question/field/period binding exists in the repository. |
| 3 | Experience legally obtainable; feedback rights; structural relevance; alternative explanations | **NOT SATISFIED** | No history pool exists (no executed episodes, no independent feedback, no corrections). Feedback-rights review is unperformed. The card already names the alternative explanations to control (static rules, plain few-shot). |
| 4 | Closest existing mechanisms read; what remains unknown; why a minimal test is warranted | **PARTIAL** | The card names ACE, MemRL, TRUSTMEM and PMD and explicitly declines any novelty claim; the single retained `H / NOT_IDENTIFIED` question (a nearest-neighbour-unexplained separation between fact-supported feedback and future-task utility) is stated but not yet identified in any concrete task. |
| 5 | Qualification appendix with G-RQ / G-M recommendations and unresolved dependencies | **THIS DOCUMENT** | See sections 3-7. |

## 2. Is the data usable?

**No, not as the pilot population.** What exists is a *metadata* layer, not a qualified corpus.

- `paper-public-source-registry-v1.json` (verified 2026-09-23, metadata only) lists ten candidates with repo-level licences: TAT-QA (MIT repo; README-reported CC BY 4.0, flagged re-check at fetch), FinQA (MIT repo; **README silent on the data licence at the recorded head**), ConvFinQA, MultiHiertt, HiTab (NOASSERTION; C-UDA-1.0 review required), GitTables (CC0-1.0 repo; corpus provenance review required), Sherlock/VizNet, HybridQA, OTT-QA, Valentine/NYC (Apache-2.0 repo; NYC Open Data upstream terms govern the data).
- `docs/datasets/2026-09-24_dB_licence_evidence.md` records the licence-text measurements and explicitly corrects one registry row: the FinQA README carries **no** licence statement at the recorded head, so the data licence is unresolved rather than CC BY.
- `docs/datasets/2026-10-05_rq2_candidate_source_screening_v1.md`: `METADATA_ONLY_SCREENING / NO_DOWNLOAD / RQ2_NOT_IDENTIFIED`.
- Policy fields forbid treating a source namespace as a row-level cluster and forbid cluster crossing across role layers, which is exactly what the WP-0 origin requirement needs from a real corpus.
- The repository's own `data/` tree holds only `sessions.db` and production rule documents under `data/local_bucket/documents/`; neither is research data, and the rule documents are the product's own material.

**Fitness for the specified task is unestablished.** The registry's `role_fit` fields were written for the earlier Stage-D roles, not for "two-period increase/decrease with unit unification". No candidate has been assessed for whether its tables actually carry two aligned periods, a unit column, and independently verifiable reference answers.

## 3. Sources and licences

| Source | Repo licence (recorded) | Data licence state | WP-0 blocker |
|---|---|---|---|
| FinQA | MIT | README silent at recorded head; upstream unstated | data licence unresolved |
| TAT-QA | MIT | README-reported CC BY 4.0 to re-check at fetch | unverified at fetch; historical-only until exposure audit |
| ConvFinQA | MIT | review required | linked extension, not an independent test source |
| MultiHiertt | MIT | external package scope review required | conditional external source |
| Valentine / NYC | Apache-2.0 | NYC Open Data upstream terms govern | upstream redistribution compatibility must be signed |
| HiTab | NOASSERTION | C-UDA-1.0 review required | licence ambiguous |
| GitTables | CC0-1.0 | corpus provenance review required | no pairwise gold without adapter |

**Conclusion:** the repository can name candidates, but it cannot yet certify *any* licence for the new task's data use, and every row is explicitly not download-approved.

## 4. Actor revision

**Not available.** `docs/datasets/2026-10-05_model_training_go_application_v1.md` records `MODEL_GO = PENDING` ("exact model/tokenizer revision and weight licence are not approved") and `TRAINING_GO = PENDING`. Two Qwen3 artifacts (4B, 8B) have GB10 validation receipts, but those receipts predate this route and explicitly are not `MODEL_GO`. The blueprint requires one frozen actor revision, model, tool set, generation settings and output budget; none is frozen.

## 5. Experience-construction feasibility

**Not feasible yet.** The E arm needs one or two *真实执行* episodes from other origins, each with independent outcome feedback and a correction that was actually executed. Today:

- there are no executed two-period episodes, hence no feedback and no corrections;
- the feedback right is unreviewed (see section 3);
- the C arm requires matched unrelated experience with <=5% context-token difference, which needs a pool large enough to sample matched pairs - unavailable;
- the blueprint's own guard applies: the E/C context must be built from frozen field projections, and the pool must be frozen before the pilot.

So the E/C construction depends on materials that do not exist. What *can* be built read-only is the projection schema and the selection rule, which is design, not data.

## 6. Method-innovation space

**Nothing identified, and the card says so.** `METHOD_NOVELTY = NOT_IDENTIFIED`. ACE already uses generation/reflection/consolidation with natural execution feedback; MemRL studies environment-feedback-driven memory utility and retrieval; TRUSTMEM verifies memory-transformation coverage/retention/fidelity; PMD forms cross-task program memory and distils it into parameters. The card retains exactly one hypothesis: whether a fact-supported-feedback to future-utility separation exists that is unexplained by the nearest neighbours. That is an *entry point*, not a contribution, and it must not be promoted by documentation completeness.

## 7. Recommendation

**G-RQ (research question): recommend `HOLD / NOT QUALIFIED YET`.** The question and its evidence requirements are coherent and bounded; the materials to instantiate it are absent. Recommend the owner decide the *source and licence* first, because every other WP-0 item depends on it.

**G-M (method necessity): recommend `HOLD`.** Nothing in the record identifies an unexplained residual, and the nearest neighbours are strong. Recording this as "method not needed yet" is compatible with a positive E-vs-B/C effect later.

**Should the pilot be entered now? NO.** The stop rule applies: no exact licence, no independent source, no reference target and no experience trace means the panel is `SOURCE_INSUFFICIENT`. Entering it would require either unverified data or an artificially thinned panel, and the card forbids both.

**What would change the answer (the minimum decision set for the owner):**
1. Choose one candidate family and authorise a licence/scope review for that specific use.
2. Confirm whether an origin-level grouping (>=8 origins) can be derived from that source, with near-duplicate isolation.
3. Freeze one actor revision and its tool set.
4. Decide the feedback right: what historical feedback may be shown to the actor, from where.
5. Only then bind the pilot budget (300 requests) and window.

## 8. Risks

| Risk | Why it matters |
|---|---|
| Sourcing by convenience | Using the closed Stage-E/FinQA material or a re-split of the 95-table corpus would create an invalid panel; the card explicitly forbids it |
| Licence drift | FinQA's data licence is unresolved at the recorded head; TAT-QA's CC BY rests on a README statement that must be re-checked at fetch |
| Actor provenance | If the actor revision at experience-collection time differs from the pilot revision, the E-arm effect is not attributable |
| Documentation-as-progress | The design, the entry and the blueprint are complete; that must not be read as `TASK_QUALIFIED` |
| Method novelty | Even a positive pilot may be fully explained by ACE/MemRL-class mechanisms |

## 9. Traceability (what was read for this report)

`docs/archive/2026-10-20_entry_consolidation/MASTER_RESEARCH_EXECUTION_ENTRY_v1.md`; `docs/research/THESIS_EXECUTION_BLUEPRINT_v1.md` §2-§3; `docs/archive/2026-10-20_entry_consolidation/thesis_experience_v1_task_card.md`; `docs/datasets/paper-public-source-registry-v1.json`; `docs/datasets/2026-09-24_dB_licence_evidence.md`; `docs/datasets/2026-10-05_rq2_candidate_source_screening_v1.md`; `docs/datasets/2026-10-05_model_training_go_application_v1.md`; repository `data/` inventory; `research/thesis_experience_v1/` existence check (absent).

**No Git-tracked data body was opened, nothing was downloaded, no model or service was called, and no runner was created. This report does not authorise WP-1 or WP-2.**

## 10. Update 2026-10-13 - TAT-QA A1-A6 executed (supersedes the TAT-QA rows above)

The owner selected TAT-QA and authorised the raw fetch; items A1-A6 of `WP0_TATQA_PACKAGE_v1.md` Sec.6 are executed with receipts. Details: `WP0_TATQA_QUALIFICATION_APPENDIX_v1.md`.

- Checklist item 1: SATISFIED for TAT-QA - licence verified (MIT repo + CC BY 4.0 data); raw fetched 2026-10-13T05:07:45Z (2,479 records, sha256-gated); origin rule instantiated (182 origins; 60 candidate items from 60 distinct origins).
- Checklist item 2: CONTRACTED - adapter/checker contract filed (fixtures are WP-1 work).
- Checklist item 3: licence cleared for TAT-QA data use; feedback-right definition still OPEN; actor revision still NOT frozen.
- Checklist items 4-5: mechanism reading unchanged; the appendix replaces the earlier "no materials" verdict for TAT-QA only.

Recommendations (owner-advisor decides): G-RQ -> QUALIFIED_CONDITIONAL (remaining bindings: feedback right; actor revision freeze; budget/window). G-M -> HOLD unchanged; `METHOD_NOVELTY = NOT_IDENTIFIED`.

No WP-1/WP-2 authorisation is granted here; nothing was trained or run. Other candidate sources remain at their earlier metadata-only states.