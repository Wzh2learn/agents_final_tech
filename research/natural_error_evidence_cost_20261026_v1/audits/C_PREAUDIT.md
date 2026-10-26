# C Independent Candidate Qualification Pre-Audit

Task ID: natural-error-cost-preaudit-c-20261026
Goal ID: NATURAL_ERROR_EVIDENCE_COST_20261026
Authority commit: 622b386986ca66c8119263e146f3d3e73c33e260
Role: C independent audit. Zero model, judge, training, production or
confirmation calls. Zero database calls. A artifacts were read only.

## Integrity of audited inputs

| Input | SHA-256 | Status |
|---|---|---|
| A_PREPARE_TASK.md | b14cbcda5544b70cf172713e89d6d804e6e76459c59359835ae00c86e8880050 | matches A |
| D_STAGE_GATE.md | 384ef47ce94331e5ca70721999e04e14af1f02607f90071a4fb98d7cab9285d7 | matches A |
| P1 frozen results source_disjoint_results_v4.jsonl | 3723c388ff6f12a1b71314a361584bcd2678079cb86f0fc6c33865533c322e31 | matches A |
| P1 frozen instances source_disjoint_instances_v4.jsonl | 00b92fb31a3ef37b69d6cb67d33723b3e94afbaddbf38e246913b9c7c8dc4d13 | matches A |
| P2 pinned TAT-QA dev tatqa_dataset_dev.json | 8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5 | matches A |
| Prior exposure qualification SOURCE_EXPOSURE_QUALIFICATION.json | 39045142db73586504e0504b0f7e2ad73bbabd373075d57ae2d5aca9e94bdfaa | matches A |
| All 9 hashed A outputs | see A_PREPARE_RESULT.output_sha256 | all OK |

## Verdicts

| Candidate | Verdict | Basis |
|---|---|---|
| P1_VISIBLE_SEMANTIC_ROLE_BINDING | CONDITIONAL | Blocked conclusion survives, but one of five is a reference defect rather than a model error, and the 5/5 rule-replay claim is not reproducible (4/5). |
| P2_TABLE_TEXT_EVIDENCE_COST | CONDITIONAL | Task qualification verified exactly; the cost screen rests on unpublished recovery code and cannot be independently reproduced at the 2.0 pp margin. |

Recommended primary for D: none (NO_GO on the model stage). See Recommendation.

## Check 1 - P1 candidates are natural original errors with complete references

Recomputed from the frozen source, not from A labels.

- Population reproduces exactly: ordinary arm x original = 24,
  program_correct True 19, False 5. All five failing rows are variant=original
  in ordinary_answer_execution_sft; related/irrelevant variants (96 rows) and
  the visible_program_filter_sft arm are correctly excluded.
- A transcribed the five model programs and the five gold expected objects
  faithfully from the frozen rows.
- Visible decision space is legal for all five: every prompt carries the full
  rendered table including the period/person axis labels (the R1 year row or
  the columns header line), so no candidate depends on hidden structure.

Four of five are genuine model semantic errors under the visible evidence:
NAT_train_38e317da (bound the 2018/2017 columns for a 2019-vs-2018 question),
NAT_train_72f960c0 (reversed subtraction on the 2019/2018 columns),
NAT_train_cf77f5f9 (range sum bound only the endpoints, dropped the interior
2018 column), NAT_train_4c2c23e7 (aggregated down rows for Chris Lien instead
of across the three named person columns, plus a non-numeric operand).

The fifth does not qualify. See finding F1.

## Check 2 - reference/scoring defects separated from model errors

**F1 (blocking).** NAT_train_b7814ec0_7b6669a8 is a reference/scoring
defect, not a model semantic error.

- Visible axis: R1 labels C1=2019, C2=2018. Row R5 holds 3,552 and 5,507
  (in thousands).
- Frozen gold: R5:C2 minus R5:C1 = 5,507 - 3,552 = +1,955 = 2018 minus 2019.
- Model output: R5:C1 minus R5:C2 = 3,552 - 5,507 = -1,955 = 2019 minus 2018.
- The frozen scorer (evaluate_target in
  research/natural_program_learning_20261024_v2/run_natural_program_experiment_v2.py)
  marks correctness by numeric equality, so the model was scored wrong.
- Across all 24 frozen originals, 19 of 20 change/difference items use
  later-minus-earlier given the visible period labels. This includes five
  identically phrased items: NAT_train_38e317da (change between 2018 and 2019
  gives -9,005 = 2019-2018), NAT_train_f897bcf7 (+368),
  NAT_train_c2535a25 (-29), NAT_train_df62465f (+1.6),
  NAT_train_85d4834f (+1,249). NAT_train_b7814ec0 is the only inversion in the
  set.
- Therefore the frozen gold direction is inconsistent with the set own
  convention and with identically phrased items. Under the dominant convention
  the model program is correct and the gold is sign-inverted. This is a
  reference/scoring defect and must not be counted as a natural model error or
  as a complete semantic reference.

The remaining separation work is correct. The one P2 hidden-scale item
(question_uid 81fc6048-7510-4c55-aa3c-4c9f1f5b8bcb, gold 68.07 from
(3,901-2,321)/2,321, raw scale field percent while the question never says
percent) is flagged NOT_MODEL_READY and excluded from answer-risk scoring;
unobservable unit scale is not blamed on the model. P2
actual_model_answer_risk is honestly UNKNOWN_ZERO_GENERATION. No item was
labelled a reasonable UNKNOWN that should have been a model error.

Minor, non-blocking: NAT_train_cf77f5f9 (total revenue in Thailand between
2017 to 2019) keeps the inclusive-range gold; the question wording is loose
but the inclusive reading is dominant. Record the caveat.

**F2 (blocking).** The claimed simple-control replay is not
reproducible. A reports label_period_unit_rules.repaired_candidates: 5 and
deterministic_replay_pass, but the A-stated rule for NAT_train_b7814ec0 is
"Apply latest-minus-previous", which yields -1,955 and contradicts the
A-recorded gold +1,955. Under one consistent deployable policy the honest
replay is 4/5 (the fifth is F1). Additionally the per-candidate
simple_control_result strings are instance-keyed recipes rather than one
frozen policy; a deployable control must be a single policy applicable without
gold. MECHANISM_NEIGHBORS.md row 2 (repairs all five frozen natural failures)
inherits the same defect.

After both fixes the P1 gate is unchanged: 4 natural model errors, all
explained by one visible-only period/label/scope rule policy, residual = 0,
which is still below the stage gate requirement of at least two residual
failures. BLOCKED_AFTER_SIMPLE_CONTROLS stands, on corrected evidence.

The remaining control claims check out: full table/header restoration was
already satisfied (prompts contain the whole table and no context text exists
for these tasks), fixed calculator and strict normalization repair 0 (values
execute correctly; the failures are binding/direction), and no neutral-retry
artifact exists in the frozen run set, so not_present is correct.

## Check 3 - no gold/reference leakage into proposed actor inputs

Accepted. P1_PROBE_CONTRACT_DRAFT.fixed_execution explicitly sets
gold_inputs_to_actor, hidden_unit_scales_to_actor and reference_row_ids_to_actor
to false, keeps the frozen output contract, and the proposed transformation
adds only roles derived from visible text. Gold programs, answers and evidence
refs live only under offline_reference_only in the ledger and
offline_reference in REAL_EXAMPLES.jsonl. The five P1 visible_actor_evidence
lists contain visible table rows only (no gold refs, answers, programs or
scales). P2 ranking declares gold_relevance_used_for_ranking false; the TAT-QA
raw scale annotation appears only in offline reference fields.

**F3 (fix before any release).** P1 scoring.primary (exact structured
program and deterministic value) is not the frozen metric (program_correct is
numeric equality). A released probe scored that way would not be comparable to
the frozen ordinary outputs it is measured against.

## Check 4 - P2 table-text qualification

Recomputed directly from the pinned raw (hash verified):

- 278 records, 1,668 questions; answer_from is table 772, table-text 507,
  text 389. The 507 figure is exact. The 389 text-only questions are the prior
  no-go set and are not used as a task; retrieval is described as
  record-internal everywhere and is never labelled report/corpus retrieval.
- Answer types reproduce exactly: arithmetic 205, span 181, multi-span 101,
  count 20. Answers present 507. Arithmetic+count derivations non-empty 225.
- The 507 questions span 156 distinct table uids, matching record_clusters 156.
- The complete semantic reference claim (506 complete, 1 excluded) is
  consistent with the single hidden-percent item verified above.

**F4 (blocking for the cost screen).** No recompute program was
published for the load-bearing numbers (semantic_reference_potential
229/460/414/491/293/506, source_requirement_counts 229/246/31/1, character
volumes, the fixed local stopword list). Independent recomputation of the
fully specified parts brackets A but does not reproduce it:

| Quantity | C variant 1 (binary query weights) | C variant 2 (idf query) | A |
|---|---|---|---|
| gold recovery top-3 | 431 | 444 | 440 |
| gold recovery top-5 | 483 | 487 | 485 |
| gold recovery top-1 plus neighbors | 357 | 377 | 358 |
| gold recovery all paragraphs | 507 | 507 | 507 |
| table-only visible chars | 240,475 (json rendering) | not applicable | 237,907 |

Gold-paragraph recovery is plausible within about 2 percent and the character
proxy within about 1-8 percent of faithful renderings. But the semantic-ceiling
rule (exact or semantically equivalent operand recovery plus visible
scale/precision rules) is underspecified, and the C recovery attempts disagree
materially with A in both directions (C table-only 388-405 vs A 229; C
all-context 413 vs A 506). The 2.0 pp non-inferiority screen, which is the
sole basis for qualified_challenger being null, is not independently verified.

What is robust without the program: always_expand is legally complete by
construction (table plus every paragraph of the same record) for 506/507; the
only frontier that is margin-plausible on the A numbers, larger_topk_5, fails
both frozen cost budgets (86.36 percent of always-expand characters vs the 75
percent budget), so it cannot be a qualified challenger at any margin; and all
cost-passing frontiers show large semantic gaps in every variant computed here.
The challenger-free conclusion is likely correct, but it must be carried by a
published, re-runnable screen rather than by unverifiable counts.

## Check 5 - baseline deployability, margin and budget freeze

Accepted on deployability: table-only, deterministic record-internal TF-IDF
top-k, fixed top-1 neighbor, always-expand and the transparent stop/expand
rule are all record-internal, deterministic, gold-free at ranking time, priced
in the same character proxy, and explicitly barred from being reported as
token/latency savings. All see the same record-level information.

Accepted on freeze with a caveat: frozen_before_output declares
noninferiority_margin_percentage_points -2.0 and two budgets (at most 75
percent and at most 50 percent of always-expand characters, at most 3
deterministic actions), identically in P2_TASK_QUALIFICATION.json and
P2_PROBE_CONTRACT_DRAFT.json, before any generation (generation is 0). The C
robustness check shows the no-challenger outcome is insensitive to any margin
in the open interval (0, 2.96 pp) given the cost conjunct, so the margin value
is not what makes the screen negative.

**F5 (fix before any release).** There is no pre-registration receipt
carrying a hash and time predating the frontier computation, and
full_semantic_answer_accuracy has no frozen answer-matching rule (span,
multi-span normalization and scale handling). Freeze both before generation.

## Check 6 - exposure and source clusters

Accepted, recomputed from SOURCE_EXPOSURE_QUALIFICATION.json (hash matches):
question-level roles over the 507 are UNASSIGNED 472, reserve 21, history 7,
development 1, excluded_pending_review 6; exposure categories are
STRUCTURAL_SCAN_ONLY 448, PROGRAM_GENERATED_NO_CONTEXT_EVIDENCE 22,
METHOD_DEVELOPMENT_OR_DIAGNOSTIC 16, MODEL_OR_FEEDBACK_EXPOSURE 14,
EXPOSURE_UNKNOWN 6, PROGRAM_GENERATED_REFERENCE_PENDING_REVIEW 1. Both
distributions match A exactly. The proposed post-selection development count 6
equals 1 prior plus 5 newly selected, consistent. All five selected
development examples exist in the pinned raw as answer_from=table-text, with
matching question text, record/question indices and cluster ids (cluster_0596,
cluster_1151, cluster_0385, cluster_1707, cluster_1826), each previously
STRUCTURAL_SCAN_ONLY and UNASSIGNED. The five P1 examples are registered as
prior frozen exposure and not as new development. All ten REAL_EXAMPLES rows
are covered by the register.

## Check 7 - mechanism neighbors

Accepted. Five tabulated neighbors plus the transparent stop/expand rule are
materially differentiated along the mechanism axis: execution-only layer,
deterministic visible-only role/period/scope resolution, constrained program
filtering, record-internal retrieval policy, full-record expansion, and a
transparent stop rule. Novelty is explicitly disclaimed for
table+text+calculator and generic adaptive retrieval, and P1/P2 are not merged
into one claim. The only corrections needed are the 5/5 repair claim (F2) and
the unverified 229/507 ceiling quoted in the table (F4).

## Blocking fixes before D relies on these cards

1. **F1** Reclassify NAT_train_b7814ec0_7b6669a8 as reference/scoring
   defect (inverted change direction). Do not count it as a natural model
   error and do not claim a complete semantic reference for it. State the
   convention conflict with the five identically phrased items.
2. **F2** Replace the 5/5 replay claim with one frozen, gold-free rule
   policy and report 4/5; correct MECHANISM_NEIGHBORS.md row 2.
3. **F3** Align the P1 probe primary metric with the frozen scorer, or
   declare and justify a dual metric before any release.
4. **F4** Publish the P2 recovery/ranking program plus the exact table
   and paragraph serialization, the stopword list and the operand/scale
   matching rules; C must re-run and confirm or revise the margin screen before
   the no-challenger result is used as a no-go basis.
5. **F5** Add a pre-registration receipt for the margin and budgets and
   freeze the full_semantic_answer_accuracy matching rule before generation.

Non-blocking: fix the ledger actor-visibility transcription. Candidate 2
header is recorded as C1=2019 | C2=2018 while the frozen prompt has
C1=Notes | C2=2019 | C3=2018, and relevant_visible_rows for candidates 1, 3
and 4 repeat the target row while omitting the year-label row the diagnosis
relies on. Conclusions are unaffected because the full table is visible, but
the ledger is not checkable as written.

## Recommendation (advisory evidence for D only)

No primary. Both cards are conditional and both stage-gate preference tests
fail: P1 has zero residual after visible-only simple controls (F2 corrected),
and P2 has no cost frontier inside the frozen margin and budgets (F4 pending
verification). Per D_STAGE_GATE.md no candidate is forced; the conformant
disposition is NO_GO on the model stage and continued Paper E and thesis work.

If D elects to revive one candidate after the blocking fixes, the only one
whose task is already legally qualified is P2_TABLE_TEXT_EVIDENCE_COST, and
only if the re-run margin screen still returns no qualified challenger or a
challenger that passes one frozen budget. P1 must not be revived on the
current evidence: its five failures include one reference defect and its
remaining four are fully explained by deterministic visible-only rules.

## Reproduction notes

All counts above were recomputed in this session from the frozen P1 run files
under /home/testuser/wzh/research_runs/source_disjoint_confirmation_v4/ and
the pinned TAT-QA dev raw, using only read-only parsing. No file outside
research/natural_error_evidence_cost_20261026_v1/audits/ was modified.
