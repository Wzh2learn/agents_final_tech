# Loop C Fixed-Snapshot Joint Review: Adaptive Mechanism 2026-10-27

- Task ID: adaptive-mechanism-c-20261027
- Date: 2026-10-27 (Asia/Shanghai)
- A snapshot reviewed: 276c858839ecbd9c190b8067552c683372efc193 (verified present, type commit)
- Authority: docs/research/LOOP_D_RESEARCH_PROMPT.md
- Authority git blob: 17f6895e3f2734f5e597f1a1d7853af22ae2adf4
- Authority LF SHA256 (independently recomputed): 73da0c8a44512c4b47d677efa3a7c71b45fb7d15e582a77737c27c284f800d12 (matches)
- Reviewer identity: independent AI/automatic joint review. Not human gold, not venue acceptance, not school recognition.

## Verdict

CONDITIONAL

Three of four review areas are sound (Paper E build, Scoring V2, persistent budget). The central scientific area contains one BLOCKING defect: the reported visible-typed baseline is oracle-assisted because its actor consumes the gold answer_type field, which is not deployment-visible. Under the true deployment information boundary the reported 31 ACCEPT / 5 REASONABLE_UNKNOWN collapses to 12 ACCEPT / 19 REJECT / 5 REASONABLE_UNKNOWN. The claim that the visible-only baseline leaves zero unexplained natural residual, and therefore justifies STOP_BEFORE_GENERATION, is not supported and must be re-opened with a bounded answer-type-free test. The infrastructure, immutable raw, scoring labels and historical identity are correct and preserved, so the work is not discarded; the single blocking characterization error is bounded and fixable. No new physical generation is authorized by this review.

## Independent bindings, hashes and counts

| Item | Independent value | Status |
|---|---|---|
| A snapshot commit | 276c858839ecbd9c190b8067552c683372efc193 | present (git cat-file type commit) |
| Authority LF SHA256 | 73da0c8a44512c4b47d677efa3a7c71b45fb7d15e582a77737c27c284f800d12 | matches C_TASK |
| P2_GENERATIONS.raw.jsonl | fca487c420409a389059aefe169562ca28f58246df0b6157b6c51b7258132488 | immutable first batch |
| P2_GENERATIONS.annotated.jsonl | cf3c243e93a5f345405281a85d8e5b7a981c993fc496c4ca99b55218e34ae1b3 | read-only |
| P2_REFERENCE_CHAIN.json | 2a5340ac8a7fe8fe84d018db3f75a7aba175ff91a60d42f4d3e564d3b819e066 | read-only |
| budget ledger.jsonl | ad0535aeb3fb324c60631ca38b0bbb5a82cb509c834aefb624e025db2350fdef | matches A; 340 bytes; 1 event |
| budget schema.json | ac1090a9974d08350cbd4a699572a95c3440b92a039a22e910bb8619ca89910b | matches A |
| raw rows | 40 (= 36 primary final + 4 retries; retry_attempt 36x1 + 4x2) | verified |
| (uid,arm) groups | 36 = 12 UID x 3 arm | verified |
| selected final-attempt input | top3 8863 / top5 9780 / all 11384 | verified |
| input deltas | top5-top3 = 917; all-top5 = 1604 | verified |
| selected final totals | 30027 input, 2342 output | verified |
| historical ACCEPT | 2 / 3 / 3 (top3/top5/all) | preserved and visible |
| visible baseline rows | 36 = 31 ACCEPT + 5 REASONABLE_UNKNOWN | recomputes from rows |

## Commands executed and exit status

All commands run read-only against the fixed snapshot. No model load, no generation, no judge, no production probe.

| Command (abridged) | Result |
|---|---|
| git cat-file -t 276c858839... | commit (exit 0) |
| git cat-file -p 17f6895e3f... pipe sha256sum | 73da0c8a... matches (exit 0) |
| scoring test suite (17 tests) | Ran 17 tests OK, 0 failures 0 errors |
| baseline test suite (5 tests) | Ran 5 tests OK, 0 failures 0 errors |
| budget fault suite (7 tests) | Ran 7 tests OK, 0 failures 0 errors |
| visible_typed_baseline recompute | 36 rows = 31 ACCEPT + 5 REASONABLE_UNKNOWN |
| answer-type-free ablation (this review) | 36 rows = 12 ACCEPT + 19 REJECT + 5 REASONABLE_UNKNOWN |
| build_paper_e.sh | exit 127, BUILD_BLOCKED required TeX tool not found pdflatex |
| TeX tool search | pdflatex latex lualatex xelatex tectonic latexmk bibtex biber tex luaotfload all absent |
| check_sources.py | status PASS (with limitations below) |
| budget ledger read | 1 event ledger_initialized; 0 reservations/rows/attempts/tokens |

## 1. Paper E formal build readiness

Finding: BUILD_BLOCKED is supported. No formal build is claimed. Not blocking.

- Buildability: the source bundle is written for a normal TeX environment. build_paper_e.sh (lines 6-11) loops pdflatex then bibtex and hard-fails with exit 127 and the exact message BUILD_BLOCKED: required TeX tool not found: pdflatex. Independently reproduced (exit 127, same message).
- Tool search: independently confirmed pdflatex latex lualatex xelatex tectonic latexmk bibtex biber tex luaotfload (and kpsewhich) are absent from PATH, and no TeX trees under /usr/local/texlive, /opt/texlive, /usr/share/texlive, /usr/share/texmf, /usr/lib/texlive. A claim accurate.
- Dependency completeness: paper_e_sncs.tex, references.bib, 3 PNG + 3 SVG figures, build_paper_e.sh all present and non-empty. elsarticle-harv.bst is NOT bundled; it is declared via bibliographystyle (tex line 251) and the build script exit-2 path requires it via kpsewhich. This is a declared conditional dependency (satisfied by a standard TeX Live elsarticle install), so the bundle is directly buildable in a normal TeX environment but not self-contained for the .bst.
- Source checks substantive: mostly real. citation/bibliography identity (set equality), 24 bib entries, 24 cited keys, figure existence, structured abstract markers, declarations markers, P1/P2 exclusion regex, complete body through end document. Two-case scope, full sections and figure references verified true on manual read of the 253-line tex.
- Source check limitations (non-blocking): (a) display_formula_inventory is hardcoded pass True (check_sources.py line 104) and its note is factually wrong (the tex has two display formulas at lines 80-82 and 123-125); (b) no dedicated final-page content check exists (only section markers plus end document); (c) cross_references_resolve is near-vacuous (the manuscript uses zero backslash-ref, degrading to Figure substrings); (d) two-case / full-section checks are shallow string-presence (conclusions true on manual read but the checker alone would not catch an empty Case 2 mention).
- First-reviewer pass: FIRST_REVIEWER_PASS_V2.md is substantive, not a checkbox. Covers contribution/nearest-work separation (explicit negations), two-case interpretation changes, clustered/post-hoc identity (442/305 clustered-not-independent; 33-record post-hoc caveats), claim boundaries, reference readability. It is an AI self-review, correctly labeled, not human review.
- Fallback PDF not accepted as formal build: PASS. Zero pdf/bbl/log/aux/bst in the bundle. BUILD_BLOCKED.md line 34 labels the pre-existing 15-page fallback as a non-TeX review artifact, not a formal build.

Smallest follow-up: fix the hardcoded formula check note and either implement or drop the claimed final-page and cross-reference checks so the receipt does not overstate. Not required for BUILD_BLOCKED to stand.

## 2. Scoring V2 and zero-model rescore

Finding: VALID. Layers are separate, statuses distinct, historical identity preserved, zero-model confirmed. Not blocking.

- Test replay: 17 tests, 0 failures, 0 errors (independently run). Coverage includes positive controls (currency display equivalence, exact multi-span set, mean typed reduction, count typed reduction) AND adversarial controls matching the named defect classes: wrong unit rejects, wrong direction rejects, extra span rejects, wrong period/row rejects, missing reference strict-fails, nonexistent reference rejects, out-of-range paragraph reference rejects, numeric-equal wrong-role rejects, negative count strict-fails, numeric-array contract strict-fails, reasonable-unknown when evidence missing, unknown-count contract, unresolvable legal reference is PENDING not wrong.
- Over-strict rejection: mitigated. Correct responses reach ACCEPT (currency display, mean, count, exact set). PENDING_ADJUDICATION is kept distinct from WRONG and from STRICT_FAIL.
- Hidden gold use in scorer: none inappropriate. The scorer legitimately reads reference answer/unit/program/answer_type to grade. Reference reconstruction (string program split on ##, extract_numbers on arithmetic program, dict/list answer handling, visible paragraph raw-order to index mapping) is used only after output for grading, not fed to the actor.
- Wrong-role / extra-span / missing-ref / unit-scale conflicts: all covered by the adversarial tests above and enforced in evidence_layer (nonexistent_reference, out_of_range_reference, semantic_reference_mismatch) and unit_layer (unit_or_scale_mismatch, numeric_value_mismatch_or_direction).
- Rescore: model_calls_in_rescore = 0, generation_records_created = 0, primary_final_attempt_count = 36, selection rule = max call_number within question_uid_sha256 x arm over the immutable first 40-call batch. Verified 36 groups, 12 per arm.
- Corrected deltas: top5-top3 = 917, all-top5 = 1604 (independently recomputed from raw input_tokens). Matches A.
- Historical identity preserved: historical_score_visible records table_top3_ACCEPT 2, table_top5_ACCEPT 3, table_all_ACCEPT 3 with identity old scorer retained without reinterpretation. The 2/3/3 is not overwritten. V2 per-layer counts match A report.

Smallest follow-up: none required. Optional: surface the per-UID historical vs V2 triple in the same machine-readable row for side-by-side reading (currently split across fields).

## 3. Persistent budget guard

Finding: VALID. Reservation-before-call, raw-before-scoring, non-resetting totals and pre-load attempt/token rejection are implemented and tested. Not blocking.

- Ledger: external append-only JSONL at /home/testuser/wzh/research_runs/persistent_budget/adaptive_mechanism_20261027/ledger.jsonl, SHA256 ad0535ae... matches A. Content: exactly 1 event ledger_initialized (seq 0). 0 reservations, 0 raw rows, 0 attempts, 0 tokens, 0 loads. Hash chain valid. Append-only via open(a+b) + seek(END) + write + flush + os.fsync (ledger.py 108-117); no truncate/rewrite.
- Fault suite: 7 tests, 0 failures (independently run). Real fault injection, not shallow: scoring exception injected after raw fsync asserts on-disk re-read equality and rescore adds 0 calls; crash-after-reservation asserts uncertain reservation stays consumed (consumed_tokens retained, resume returns UNCERTAIN_RESERVATION_STOP with model_loaded False); crash-between-calls preserves earlier raw rows; output-directory change on one ledger path does not reset totals; attempt 37 and token-cap successor rejected before loader with loader-count assertions.
- Ordering (traced in runner.py generate_once): reserve and fsync (56-62) before model_loader (63); append_raw and fsync (64-69) before scorer (70). Reservation cap checks precede any event write (ledger.py 207-223).
- Separate generate/resume/rescore: rescore and resume take no model_loader parameter (structural), rescore re-reads the ledger and raises rescore_mutated_generation_ledger if it changed.
- Attempt 37 / token cap: MAX_PHYSICAL_ATTEMPTS=36, MAX_GENERATION_TOKENS=240000; both rejected inside reserve before the loader. Physical attempt ids pa-NNNNNN distinct from logical_call_id.
- shared calculator safe_calculate: AST whitelist (Expression/Constant/BinOp/UnaryOp), no eval/exec. Adversarial probes (import, open, attribute traversal, lambda, comprehension, f-string) all rejected.
- Actual generation zero: confirmed. Only 1 init event; no generation records; no real model-loading code (default_local_model_loader raises by design).

Limitations (non-blocking): (a) a caller can pass --ledger to a fresh file and obtain a new budget; fixity is operational discipline, not enforced, and the output-dir test only covers one ledger path; (b) token cap is projection-only, append_raw does not re-check reported usage against the 240k cap; (c) torn-write crash is untested (fails closed to LedgerIntegrityError); (d) the loader-stays-36/1 assertion uses a stub loader because no real loader exists, so before model loading is proven at the seam, not against a real model; (e) 0 model loads is inferred from 0 attempts plus absence of loader code, not a ledger-measured field.

Smallest follow-up: enforce a fixed ledger path (ignore or forbid --ledger override in production mode) and re-check settled usage against the cap.

## 4. Visible typed baseline and mechanism stop (central review)

Finding: BLOCKING DEFECT. The baseline is oracle-assisted, not visible-only. The zero-residual justification for STOP_BEFORE_GENERATION is not supported.

### The information boundary violation

- answer_type is a gold/reference-derived feature. In P2_REFERENCE_CHAIN.json each row carries answer_type alongside answer, program and unit (the gold annotation cluster). It labels the answer form (span / multi-span / count / arithmetic); it is not a deployment input.
- answer_type is NOT deployment-visible. Across all 40 immutable raw rows the deployed actor payload keys are exactly [arm, call_id, paragraphs, question, table]. Independently verified: union of actor_payload_keys = arm, call_id, paragraphs, question, table; answer_type present = False. The P2 model had to infer answer form; it was never told it.
- The baseline actor consumes this oracle. visible_typed_baseline.py answer_from_visible dispatches on answer_type (lines 478-513) and is fed reference[answer_type] at line 556. The only deployment-invisible input is answer_type (question and context are visible).
- The blind spot is codified in the tests. test_visible_typed_baseline.py test_actor_interface_has_no_gold_or_uid_inputs (lines 24-29) asserts the actor signature is [question, answer_type, context], whitelisting answer_type as a non-gold input. This is the mischaracterization.

### Answer-type-free ablation (this review, zero model)

Reproduced the baseline twice over the same 36 (uid,arm) final attempts: once dispatching on gold answer_type (A baseline), once with answer_type blanked so dispatch falls to question-text only.

- Oracle (A baseline, uses gold answer_type): 31 ACCEPT + 5 REASONABLE_UNKNOWN. Reproduces A exactly.
- Ablation (answer_type blanked): 12 ACCEPT + 19 REJECT + 5 REASONABLE_UNKNOWN.
- 19 of 36 attempts flip ACCEPT to REJECT without the oracle. Flips by gold answer_type: span 8, multi-span 7, count 4, arithmetic 0.

Interpretation: the arithmetic/mean and change reductions are reachable from question text alone (no oracle), so the mean signal is a real transparent typed reduction, not copied from expected values. But the span, multi-span and count reductions are selected only by the gold answer_type; without it they fall to the question-text branches (which handle only change/average/mean), emit an unknown payload, and score REJECT because the required evidence is in fact reconstructible (unsupported_unknown). So the count and span signals claimed as resolved are resolved only with the oracle.

### Recompute of the reported counts and boundary sub-claims

- 31/36 ACCEPT and 5/36 REASONABLE_UNKNOWN recompute exactly from VISIBLE_TYPED_BASELINE_ROWS.jsonl (independently re-summed). Per-UID: 7a1f65b6 top3 UNKNOWN; 7e942684 top3+top5 UNKNOWN; 9e3493de top3+top5 UNKNOWN; all others ACCEPT.
- REASONABLE_UNKNOWN is justified by absent visible evidence, not used to hide errors. All 5 carry final_reason required_evidence_not_visible and reconstruction reason required_paragraph_not_visible with a concrete missing_raw_orders (7a1f65b6 missing para 4; 9e3493de and 7e942684 missing para 7). The required paragraph is genuinely outside the reduced arm (top3/top5) and the case becomes ACCEPT at the wider arm. This sub-claim holds.
- Transparent typed reduction vs copied expected values: reduction functions (reduce_mean, count_table_threshold, count_roman_services, numeric_span, etc.) compute from visible table/paragraphs via shared safe_calculate; they do not read reference[answer]/[program]. The reductions are not gold-copying. The oracle leak is the dispatch key only.
- Fair sharing / deployment validity: the shared calculator is fine for a zero-model baseline and there is no candidate-only free-tool issue (no model arms ran). But fairness to deployment fails: the deployed model did not receive answer_type, so the baseline is not a fair proxy for a deployment actor.

### Consequence for STOP_BEFORE_GENERATION

A justified STOP on the ground that a visible-only typed reduction explains all 36 attempts with zero unexplained natural residual. That premise is false under the deployment boundary: the true visible-only baseline leaves 19 REJECT residuals that the gold answer_type oracle conceals. Therefore:

- STOP_BEFORE_GENERATION does NOT remain valid as stated (zero-residual premise unsupported).
- It becomes CONDITIONAL / must be re-opened with a specific bounded test: re-characterize the natural residuals under the answer-type-free boundary (19 REJECT, concentrated in span/multi-span/count), then decide whether a mechanism is warranted. The mean signal remains genuinely resolved and should not be re-litigated.
- The frozen 8-UID diagnostic panel was never run; running it is a legitimate bounded follow-up ONLY under the answer-type-free boundary and a fair neutral/ordinary-tool shared baseline. This review does not authorize physical generation (see below).

## Blocking defects

B1 (central, blocking): oracle-assisted baseline presented as visible-only. Path: research/adaptive_mechanism_20261027_v1/diagnostics/visible_typed_baseline.py lines 478-513 (answer_type dispatch) and 556 (fed from reference[answer_type]); test_visible_typed_baseline.py lines 24-29 (whitelists answer_type). Evidence: answer_type is a gold field in P2_REFERENCE_CHAIN.json; deployed actor_payload_keys across 40 raw rows never include answer_type; answer-type-free ablation drops ACCEPT from 31 to 12 (19 flip to REJECT). Impact: the headline claim of a strong visible-only zero-model baseline with zero unexplained residual, and the resulting STOP_BEFORE_GENERATION, are not supported and conceal hidden reference access. Smallest follow-up: reclassify the baseline as oracle-assisted in A_RETURN and thesis text; re-run residual characterization under an answer-type-free actor (or add a question-text-only type inferrer and report both); re-decide STOP against the 19 visible residuals; only then decide whether the frozen 8-UID / 36-attempt panel is justified under a fair shared baseline. Zero-model; no new generation required for the reclassification itself.

## Limitations (non-blocking)

L1: Paper E check_sources.py formula check is hardcoded pass and its note is wrong; no real final-page check; cross-reference check near-vacuous. Does not affect BUILD_BLOCKED. Follow-up: fix or drop these checks so the receipt does not overstate.
L2: elsarticle-harv.bst not bundled (declared conditional dependency). Fine for a normal TeX install; not self-contained. Follow-up: note the requirement or vendor the .bst if offline build is needed.
L3: budget --ledger override permits a fresh ledger (operational discipline, not enforced); token cap projection-only (settled usage not re-checked). Follow-up: fix ledger path and re-check settled usage.
L4: budget loader-stays-36/1 uses a stub loader (no real model loader exists); 0 model loads is inferred, not ledger-measured. Honest at the seam. Follow-up: assert against a real loader when one is plugged in.
L5: the actor hardcodes a few question-keyword branches (service list, components factored) tuned to these 12 UIDs. Visible-only apart from answer_type, but a mild dev-set overfit. Follow-up: state the overfit; a general question-text type inferrer is the principled replacement.

## Generation / training / judge / production totals

- New model calls this A task: 0. New input tokens: 0. New output tokens: 0. New retries: 0. New generation records: 0. New raw model outputs: 0.
- Training runs: 0. Judge calls: 0. Production probes: 0. Model loads: 0 (ledger has 1 init event only).
- Immutable historical first batch (preserved, not re-run): 40 calls, 33207 input, 2609 output tokens; 36 selected final attempts 30027 input / 2342 output. Historical 2/3/3 ACCEPT preserved beside V2.
- Independent AI review only. No human gold, venue acceptance, school recognition, submission, payment, public release or external contact.

## Is any new physical generation justified?

Not by this review, and not yet. The immediate required work (reclassify the baseline as oracle-assisted; re-characterize the 19 answer-type-free residuals; re-decide STOP) is zero-model. The frozen 8-UID / 36-attempt / 240,000-token diagnostic panel becomes a scientifically justified bounded test ONLY if the Owner elects to pursue a mechanism for the newly visible residuals and ONLY under the answer-type-free boundary with a fair neutral/ordinary-tool shared baseline and the existing persistent-budget reservation-before-call guard. That is an Owner resource decision outside this advisory review. Historical 2/3/3 and the second 40-call batch must not be re-run to replace failed sites.

## Claim boundaries

This report is an independent AI/automatic joint review of a fixed snapshot. It is not human gold, not venue acceptance, not school recognition, and not a complete semantic oracle. Findings separate blocking defects from limitations. Accepting the infrastructure (Paper E source, Scoring V2, persistent budget, immutable raw, historical identity) is not acceptance of the central visible-only baseline claim, which is rejected as stated.

