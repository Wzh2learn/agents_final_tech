# C Joint Audit - Publication And Proxy Calibration

Task ID: `publication-proxy-calibration-c-20261026`  
Role: C_INDEPENDENT_JOINT_REVIEW  
Date: 2026-10-26, Asia/Shanghai  
A snapshot: `3a21a7186f9e20ef8feb62edae0d62987fe4bf30`  
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`  
Authority Git blob: `a38252322189ccb00a1a45b7611f693ada292faf` (verified `git rev-parse HEAD:docs/research/LOOP_D_RESEARCH_PROMPT.md`)  
Authority LF SHA256: `9dcef9001ee4e71d652dc0ad496139a54f5821f11d42a21fb7816393d1db3974` (verified `sha256sum`)

## Verdict

**CONDITIONAL**

| Sub-area | Disposition |
|---|---|
| P1 public rule actor + full 24 regression | **ACCEPTED** - independently recomputed, byte-identical |
| P2 R7/R8 repair + selection + reference chain | **ACCEPTED** - independently replayed, deterministic |
| P2 scientific disposition (no information value) | **BLOCKED** - misclassified engineering gap |
| Paper E SNCS submission package | **BLOCKED** - not a complete reviewable journal manuscript or PDF |
| Budget / zero-endpoint discipline | **ACCEPTED** - 0 generation, 0 training, 0 judge, 0 production |

This is AI review, not human gold and not venue acceptance.

Four blocking defects are conclusion- or deliverable-level, not cosmetic.
Everything else is a non-blocking limitation. One bounded A remediation is
sufficient; nothing found requires discarding the P1 result or the P2
qualification artefacts.

---

## 1. Independent counts and hashes

### 1.1 Authority and snapshot

| Item | Declared | Independently measured | Status |
|---|---|---|---|
| Authority git blob | `a38252322189ccb00a1a45b7611f693ada292faf` | `a3825232...292faf` | MATCH |
| Authority LF SHA256 | `9dcef900...3974` | `9dcef900...3974` | MATCH |
| A snapshot commit | `3a21a7186f9e20ef8feb62edae0d62987fe4bf30` | present, 45 files, +6662 | MATCH |

### 1.2 Frozen P1 inputs (external to the git tree)

The P1 instances/results are **not** in the repository. They resolve from the
frozen ledger `research/natural_error_evidence_cost_20261026_v1/a_closeout/P1_SEMANTIC_LEDGER_FINAL.json`
(`source.instances_path` / `source.path`) to
`/home/testuser/wzh/research_runs/source_disjoint_confirmation_v4/`.
A tree-wide scan of 11,389 repo files found no copy at either hash.

| Input | Ledger / A claim | Measured by C | Status |
|---|---|---|---|
| instances | `00b92fb31a3ef37b69d6cb67d33723b3e94afbaddbf38e246913b9c7c8dc4d13` | `00b92fb3...4d13` | MATCH |
| results | `3723c388ff6f12a1b71314a361584bcd2678079cb86f0fc6c33865533c322e31` | `3723c388...2e31` | MATCH |
| scorer | `f51e26769cf18a30bd9d5b1f133b9832fc8ddd951915e390df45333336fb5ac5` | `f51e2676...5ac5` | MATCH |

### 1.3 P2 source identity

| Input | Declared | Measured | Status |
|---|---|---|---|
| `raw_dev` (pinned TAT-QA dev, 507 q) | `8da095a8...6af5` | `8da095a8...6af5` | MATCH |
| `row_results` | `efe13421...c9de` | `efe13421...c9de` | MATCH |
| `qualification` | `d3b3ee96...4451` | `d3b3ee96...4451` | MATCH |

`row_results` and `qualification` resolve in-repo
(`a_closeout/P2_RECOVERY_RECOMPUTE_FINAL.json`, `a_prepare/P2_TASK_QUALIFICATION.json`);
`raw_dev` resolves to
`/home/testuser/wzh/projects/agents_final_tech/data/research/tatqa_raw_2026/tatqa_dataset_dev.json`.
Source identity is genuine: `task_source = pinned TAT-QA raw dev only`,
`finqa_used = false`, `question_count = 507`.

### 1.4 Package manifest (`ALL_FILES.sha256`) - FAILS self-verification

49 entries: **4 mismatches, 3 missing**.

| Path | Manifest | Actual | Cause |
|---|---|---|---|
| `A_RETURN.md` | `ee821b7dd7e9efcb8b41e03d45fa4ccf9ca2f43d70dc763c53a0627db0ffaa5a` | `c8061e6c854f744a5960784c6f296b9eeab27c3e0815ef5ac440e6b605c45d91` | **A own defect** |
| 3 x `__pycache__/*.pyc` | - | absent | build-artefact churn |
| 4 x `__pycache__/*.pyc` | - | differs | build-artefact churn |

`A_RETURN.md` is not explained by audit activity: its git blob at the A snapshot
is `c8061e6c...`, identical to the working tree, and only one commit
(`3a21a7186`) ever touched it. The manifest was generated before `A_RETURN.md`
was finalized and never regenerated. Seven `.pyc` entries are listed that are
not tracked in git at all.

---

## 2. Paper E - BLOCKED

### 2.1 Compiled PDF is not a submission PDF (BLOCKING)

| Property | Measured |
|---|---|
| Path | `paper_e_sncs/paper_e_sncs.pdf` |
| Bytes | 3,031 |
| Page count | **1** (`/Type /Page` = 1, `/Count 1`) |
| Header | `%PDF-1.4 ... ReportLab Generated PDF document` |
| Producer | `ReportLab PDF Library - www.reportlab.com` |
| pdfTeX/LaTeX marker | **absent** |
| Extracted text | 232 words under four headings |

`compile_package_pdf.py` builds a **package cover sheet**, not the manuscript.
Its story is five hard-coded `Paragraph` entries (lines 15-28): title, one
`TBD_OWNER` line, a condensed abstract, Reviewer-pass scope, Owner fields.
The PDF text contains none of the manuscript section structure - no
Introduction, no Two Audited Cases, no Limitations, no bibliography, no figure
captions.

The real manuscript was never compiled. `A_RETURN.md:42` records
`/tmp/tectonic/tectonic paper_e_sncs.tex` - **exit 126, `Exec format error`**
(x86-64 binary on aarch64). No alternate engine was attempted.

`BUILD_RECEIPT.md:9` states the PDF is a deterministic local reportlab
rendering of the editable manuscript text. That is an overclaim: it renders
five hard-coded paragraphs, not the manuscript text.

**Additional inconsistency:** the PDF embedded abstract is **134 words**; the
manuscript/Markdown abstract is **190**. The script silently drops the
sentences beginning We inspect visibility and In-record and pairwise values.

**Impact:** A_TASK requires a compiled PDF; authority section 3 requires a
reviewable PDF of the complete journal manuscript. A one-page reportlab cover
sheet is neither. Editable-source completeness and compiled-PDF completeness
diverge completely: the source exists, the submission PDF does not.

**Smallest follow-up:** compile `paper_e_sncs.tex` with an aarch64-capable
engine (tectonic aarch64 build, or TeX Live), record engine identity and page
count in `BUILD_RECEIPT.md`, and re-hash.

### 2.2 Manuscript is an excerpt, not a complete journal paper (BLOCKING)

| | `paper_e_sncs.tex` | `source_iccart_original.tex` |
|---|---|---|
| Lines | 73 | 242 |
| Words | 752 (stripped 719) | 6,089 (stripped 5,865) |
| Class | `article` (generic) | `IEEEtran` conference |
| Tables | **0** | 4 |
| `\cite` | **0** | 14 |

Sections actually present in `paper_e_sncs.tex`:
Introduction (1 paragraph); Two Audited Cases (Case 1, Case 2 - one paragraph
each); **Reviewer Pass**; Limitations (5 sentences); Conclusion (2 sentences).

Missing relative to the complete original and to authority section 3
(complete journal manuscript; substantive adjustment of abstract, method and
limitations):

- **Related Work** - original has 3 subsections; derived has none. Closest work
  appears only as one uncited sentence inside Reviewer Pass.
- **Method** - original has 5 subsections; derived has none. A_TASK explicitly
  requires journal-relevant methods.
- **Experimental Setup** - original has 6 subsections; derived has none.
- **Results** - original has 7 subsections; collapsed into two prose paragraphs.
- **Acknowledgments**, **Data Availability** - present in original, absent here.
- **Declarations / AI disclosure** - not in the `.tex` at all; only external
  Markdown files.
- **Reviewer Pass is a `\section` of the submission** (line 55). This is an
  internal self-review artefact and is not venue-appropriate content.

The complete 6,089-word manuscript survives unchanged as
`source_iccart_original.tex`. The derivation **discarded** the journal-relevant
material rather than adapting it.

**Source-adaptation test.** Not a byte-copy - section skeletons and document
class differ entirely. But it is claim-level repackaging, not a journal
adaptation: the title is **verbatim identical**; every headline number is
reused (`96/118`, `0/13`, `442`/`305`/`33`, `0.19`/`0.16`, `post-hoc v2`,
`text_sha1`, `affine/rank-equivalent`, `hard-versus-random`); and at least
three sentences are verbatim or near-verbatim (for example the opening sentence
about final-answer scores, and the sentence about one judge on 28 cases).
Meanwhile the derived version drops the source richer quantitative detail
(tie counts 91/135/83/125, slope 0.375, 112/118, 2,382 clean records), leaving
every remaining number as a bare count with **no provenance pointer** - no
table, no artefact ID, no section reference.

The presence of `source_iccart_original.tex` is therefore **not** evidence that
the SNCS manuscript was adapted. It is evidence that a complete manuscript
existed and was compressed.

**Impact:** the whole purpose of G1 is unmet. The package cannot be sent for
review.

**Smallest follow-up:** expand `paper_e_sncs.tex` to the full manuscript - port
Related Work / Method / Setup / Results from `source_iccart_original.tex`, adapt
them to journal voice and the structured-abstract claims, add provenance
pointers for every number, move the reviewer pass into `FIRST_REVIEWER_PASS.md`,
and restore Data Availability.

### 2.3 Citations (BLOCKING)

| Check | Measured |
|---|---|
| `\cite` commands in manuscript | **0** |
| `references.bib` entries | **24** - all unused |
| `\bibliography` command | **absent** |
| hand-written `\bibitem` | 2 (`nist`, `tatqa`) - **never cited** |

The BibTeX file is completely unwired. For contrast, `source_iccart_original.tex`
issues 14 `\cite` commands whose keys match `references.bib` - the bib file is
the source `saner_rene_references`, renamed. The derivation dropped every
citation. The two hand-written bibitems are orphaned, so the closest work claim
(`paper_e_sncs.tex:56`) has **zero** supporting citation, and the bibliography
that ships is not the one the paper uses.

**Smallest follow-up:** add `\bibliography{references}`, cite the closest-work
set in a Related Work section, delete or wire the two hand-written bibitems.

### 2.4 Figure content defect (non-blocking but concrete)

| Check | Measured |
|---|---|
| `fig1_measurement_chain.svg` on disk | present |
| `fig1_measurement_chain` referenced in tex | **no** |
| `fig2_family_visibility_matrix.png` include count | **2** (lines 29, 43) |
| `fig3_localization_ablation.png` | 1 |
| `\begin{table}` | **0** |

Figure `fig:chain` (line 29) is captioned as showing the chain from injected
failure to visibility, protocol detection and contract-relative outcome harm,
and the Introduction tells the reader it summarizes the measurement chain
(`paper_e_sncs.tex:25`) - but the embedded image is the **family visibility
matrix**, the same file used again at line 43 as `fig:visibility`. Figure 1
caption and cross-reference do not describe its content, and the actual
measurement-chain figure is unused.

### 2.5 Numerical claims - VERIFIED, do not flag

| Claim | Source | Status |
|---|---|---|
| `96/118` header injections visible | `docs/research/stage_e_118_quantification_v1.md:14,20`; `paper/claim_manifest_v1.json:45` | **CORRECT** - checkpoint-level visibility |
| `0/13` OCR-like unobserved | `fig2_source.csv` (`ocr_similar` 0/13 at all gamma); same quantification doc | **CORRECT** |
| `442` / `305` / `33` FinRank | `paper/saner_rene_manuscript_v1.md:5,157`; `FIRST_REVIEWER_PASS.md:5` | **CORRECT**, post-hoc v2 clustered |
| drift `0.19` / `0.16` | `paper_e_sncs.tex:39` | consistent with original manuscript |

C explicitly checked and **rejected** a false positive: `fig2_source.csv` shows
85/118 visible at gamma 0.2, which is the *flat-protocol detection* count, not
checkpoint visibility. The `96/118` claim is a different, frozen measurement
object. `docs/research/2026-10-08_stage_e_inquiry_and_experiment_design_v1.md:113`
states explicitly that `96/118` is checkpoint-visible injections and is **not**
the protocol detection rate. `fig2_source.csv` itself is well bound: every
number carries a JSON field path with `crosscheck_status=PASS`.

Minor precision note (non-blocking): the SNCS text drops the checkpoint-level
qualifier the original carries (`paper/saner_rene_manuscript_v1.md:157`,
Checkpoint-level analysis makes 96/118 injections visible). In a paper whose
thesis is *bind observations to measurement objects*, the headline number
should keep its measurement object.

### 2.6 What is genuinely good

- **Structured abstract** - `ABSTRACT_STRUCTURED.md` has explicit
  Purpose/Methods/Results/Conclusion and is **190 words** (C count), inside the
  required 150-250. The file own 211-word label is not reproducible by any
  counting method (190 body / 195 whole file) - non-blocking.
- **Post-hoc/clustered identity** - correctly and prominently stated in the tex
  and `FIRST_REVIEWER_PASS.md:5`: post-hoc v2 clustered by `text_sha1`, not a
  second frozen application, 442/305 not independent.
- **Contribution boundary** - stated: an audit discipline, not a new evaluator
  or ranking method.
- **Two-case scope** - preserved; no C2/C3 contamination.
- **Unresolved reproduction gaps** - stated (OCR invisibility, tie-policy
  deployment effect, global/metadata drift).
- **`FIRST_REVIEWER_PASS.md`** - substantive, not a stub; covers all five angles
  A_TASK requires.
- **`OWNER_DECISION_SHEET.md`** - exactly one primary recommendation, 5 owner
  decisions, 3 explicit stop conditions.
- **`DECLARATIONS.md`** - complete 12-line field list, 6 identity fields
  `TBD_OWNER`.
- **`COVER_LETTER.md`** - addressed to SN Computer Science, signed `TBD_OWNER`.
- **Author placeholders** - `TBD_OWNER` present in `\author{}` (`TBD\_OWNER`
  escaped), `DECLARATIONS.md`, `COVER_LETTER.md`, `OWNER_DECISION_SHEET.md`.
- **Figure sources** - `fig2_source.csv` binds every number to a JSON field
  path; `figures/receipt.json` records `model_calls=0, judge_calls=0,
  endpoint_calls=0`.

### 2.7 AI disclosure (non-blocking)

`AI_USE_DISCLOSURE.md` discloses AI assistance for drafting and consistency
review of the manuscript package and correctly refuses to substitute for human
authorship. A_TASK asks for **Methods-level** disclosure and authority section 3
asks for per-section/per-code disclosure. The current text is package-level:
no list of which sections, which tools, or what was human versus AI.

### 2.8 Paper E publication readiness

**Not publication-ready.** The editable-source layer is a 752-word outline; the
compiled-PDF layer is a one-page cover sheet whose abstract does not even match
the manuscript one; citations are absent. Suitable as an internal draft
scaffold plus good supporting documents; not a submission.

---

## 3. P1 Rule Execution - ACCEPTED

### 3.1 Independent recompute

C re-ran the A runner against the frozen inputs and compared to the stored
artefact:

```
python3 research/publication_proxy_calibration_20261026_v1/p1_rule_execution/run_full_regression.py \
  --instances /home/testuser/wzh/research_runs/source_disjoint_confirmation_v4/source_disjoint_instances_v4.jsonl \
  --results   /home/testuser/wzh/research_runs/source_disjoint_confirmation_v4/source_disjoint_results_v4.jsonl \
  --output    /tmp/C_recompute_24.json
-> exit 0
```

| | A `full_24_regression.json` | C recompute |
|---|---|---|
| summary | - | **identical** |
| rows (24) | - | **identical, 0 field diffs** |

Recounted independently from row level:

| Quantity | Value |
|---|---|
| denominator | 24 |
| baseline numeric-correct | 19 |
| actor numeric-correct | 23 |
| genuine repairs | 4 (rows 1, 2, 5, 15) |
| damage to previously numeric-correct | **0** |
| direction conflicts | 1 (row 7) |
| actor programs executable | 24/24 |
| `citation_valid` | 24/24 |
| unit `UNKNOWN` | 10/24 |

All A headline numbers confirmed.

### 3.2 Actor is gold-free - PASS

Static audit of `public_actor.py` (921 lines):

- No `uid` / `UID` / `task_id` / `source_task_id` / `instance_id` branch.
- No `expected` / `gold` constant; no per-case numeric literal table.
- `solve(question, table_text)` receives exactly two arguments
  (`run_full_regression.py:73`). Gold is used only by the *runner* for scoring
  (`run_full_regression.py:76`), never passed in.
- Structure is rule-shaped: `VISIBLE_RULES`, `2_explicit_period_binding`,
  `3_change_direction`, `4_inclusive_range`, `5_label_scope`,
  `6_numeric_reference_validation` - matching the frozen
  `VISIBLE_AXIS_SCOPE_POLICY_V1`.
- Rule usage across the 24 rows: 2_explicit_period_binding x22,
  3_change_direction x20, 4_inclusive_range x2, 5_label_scope x4,
  6_numeric_reference_validation x3.

**Implements the frozen rules, not expected answers.**

### 3.3 Result identity - 23/24 is numeric program correctness ONLY

Direct answer to the C task question.

| Identity | Count |
|---|---|
| Numeric program correctness | **23/24** |
| Unit agreement with gold | **14/24** |
| Actor program == gold program (exact) | 22/24 |
| Actor evidence_refs == gold refs (exact) | 22/24 |
| **Complete semantic answer (value + unit + refs + citation)** | **13/24** |

Ten rows report `unit: UNKNOWN` where gold holds `thousand` / `million` /
`reported` (rows 1, 3, 5, 9, 11, 15, 17, 18, 19, 24).

**C verified the `UNKNOWN` behaviour is rule-conformant, not a coverage gap.**
For all ten rows the gold unit is not derivable from the visible table text:

| Rows | Unit-like tokens in visible `table_text` |
|---|---|
| 3, 5, 9, 11, 17, 18, 19 | **none at all** |
| 1, 15, 24 | only `,000` - digit-grouping *inside numbers* (`2,363`, `$1,200,000`, `(8,000)`) |

`,000` is exactly the false-role signal the authority names in section 2
correction 2. The frozen rule mandates `UNKNOWN` when direction or unit is not
legally observable. The gold units come from document-level scaling metadata
outside the actor permitted input. The P2 reference chain confirms the same
structure: row 1 unit derives from a **paragraph** (the line about US $000s),
not the table.

**So:** the 10 unit misses are not actor semantic errors - they are a
**measurement-contract gap**: the reference requires information the deployment
input excludes. A states this correctly in the thesis text.

**Conclusion: 23/24 is numeric program correctness. Complete semantic answer
correctness is 13/24.** Do not report 23/24 as complete answer correctness.

### 3.4 Repairs are heterogeneous (precise decomposition)

| Row | Item | Model value | Actor | Kind |
|---|---|---|---|---|
| 1 | `38e317da` | -15,298 | -9,005 = gold | genuine **cell-selection** repair (program exactly equals gold) |
| 2 | `72f960c0` | -2.2 | +2.2 = gold | **sign/direction** repair - magnitude and structure already right |
| 5 | `cf77f5f9` | 130,429 | 198,646 = gold | genuine **cell-selection** repair (program exactly equals gold) |
| 15 | `4c2c23e7` | `None` (`program_execution`) | 1,904,063 = gold | **completion** repair - model produced no executable program |
| 7 | `b7814ec0` | -1,955 | -1,955 | **reference defect**, not a model error |

The count of 4 is arithmetically correct under the A definition
(`not baseline.program_correct and numeric_correct`), and A correctly isolates
row 7. But 4 repairs mixes two cell-selection repairs, one completion repair,
and one sign repair.

### 3.5 The direction-reference conflict - correctly preserved

Row 7 `NAT_train_b7814ec0_7b6669a8` - What is the change in net intangible
assets between 2018 and 2019?

- gold: `R5:C2 - R5:C1` = **+1,955**
- actor: `R5:C1 - R5:C2` = **-1,955**
- policy rules: `2_explicit_period_binding`, `3_change_direction`

Row 1 `38e317da` has the same question shape (change in ... between 2018 and
2019) and the **same policy rules**, and its gold is `R11:C1 - R11:C2`.
**The reference applies opposite subtraction conventions to structurally
identical questions.** The actor applies one convention consistently.

The frozen model also produced -1,955 on row 7
(`baseline.program_value = -1955.0`) - i.e. the model error is the model
agreeing with the rule-conformant answer and disagreeing with the reference.

This corroborates the prior C re-audit
(`research/natural_error_evidence_cost_20261026_v1/audits/TASK_RESULT_C_REAUDIT.json`
check 2): 38e317da and b7814ec0 are indistinguishable under every visible
policy feature but have opposite gold signs, and that item is classified there
as a reference/scoring defect, not a model error.

A preserves the conflict rather than forcing gold - **correct behaviour** per
authority section 4 (keep UNRESOLVED with two acceptable interpretations when
direction or unit reference is disputed).

**Limitation (non-blocking):** the row records only `direction_conflict: true`.
Neither the JSON nor `P1_FULL_24_REPORT.md` records the **two acceptable
interpretations** side by side that section 4 asks for.

### 3.6 Test discovery and execution - the receipt is not a passing test receipt

| Check | Result |
|---|---|
| `pytest` importable | **NO** - `ModuleNotFoundError` (verified) |
| `python3 -m pytest --version` | **NO** - `No module named pytest` |
| A recorded command | `PYTHONPATH=src:... python3 -m pytest ...` - **exit 1**, no test collected or run |

`receipts/P1_TEST_RECEIPT.md` records that exit-1 line alongside the others as
though it were evidence. **A command that runs 0 tests is not a passing test
receipt.** The environment limitation is real and A did not fake it; the defect
is presenting a non-run as part of a test receipt.

C executed the test bodies directly:

| Suite | Discovered | Passed | Failed |
|---|---|---|---|
| `test_public_actor.py` | 3 | 3 | 0 |
| `test_matcher_regressions.py` | 3 | 3 | 0 |

So the tests are valid and pass - but under a manual harness, not the
documented command.

Additional risk (non-blocking): `test_public_actor.py:1` imports
`from public_actor import solve` while `p1_rule_execution/__init__.py` makes
the directory a package. With pytest present, package-relative import
semantics would likely fail collection. **C could not confirm this under
pytest** (pytest absent).

Also `FUTURE_EVALUATION_MATCHER.py:18` sets `HISTORICAL_PATH` **relative to
cwd**. The P2 test module raises `FileNotFoundError` when run from
`p2_proxy_calibration/` and passes only from the repo root. Portability defect.

### 3.7 P1 boundary

Correctly bounded by A as an **exposed development regression**, not new-source
generalization. The 24 items are the frozen ordinary originals with prior
exposure; nothing here licenses a generalization claim, and A does not make
one. The 19 previously numeric-correct items sustained **zero** damage.

---

## 4. P2 Proxy Calibration

### 4.1 R7/R8 repairs - genuine, verified before/after

C loaded the preserved historical matcher
(`a_closeout/P2_RECOVERY_RECOMPUTE_FINAL.py`) and the future matcher and ran
both:

| Candidate | Reference | Historical | Future |
|---|---|---|---|
| `1,496` | 1496 | True | True |
| **`1, 496`** | 1496 | **True (false positive)** | **False** `numeric_parse_failure` |
| **`14, 96`** | 1496 | **True (false positive)** | **False** `numeric_parse_failure` |
| `2,363` | 2363 | True | True |
| **`-5`** (count) | -5 | **True (false positive)** | **False** `negative_count_rejected` |
| **`(5)`** (count) | -5 | **True (false positive)** | **False** `negative_count_rejected` |
| `5` (count) | 5 | True | True |

**R7** now removes commas only when digit-adjacent
(`FUTURE_EVALUATION_MATCHER.py:51`) - matches the frozen declaration to remove
thousands separators only when a comma is between ASCII digits.
**R8** rejects negative and parenthesized-negative counts
(`FUTURE_EVALUATION_MATCHER.py:89-90`). Both are real fixes against a preserved
original. The historical file is left unchanged - satisfies the requirement to
preserve the original rules.

Residual (non-blocking, pre-existing): a spaced digit group such as `1 496`
still matches 1496 via whitespace stripping. The historical matcher behaves
identically, so this is inherited leniency, not a regression - but it is wider
than digit-adjacent only.

A also incidentally improves prior blocking finding **R2** from
`TASK_RESULT_C_REAUDIT.json` (the frozen matcher returned `numeric_parse_failure`
for `68.07%`, `68.07 percent`, `$1,496.5`). The future matcher returns
principled verdicts - `explicit_unit_conflict` for percent against an empty
`reference_scale`, `numeric_isclose` for `$1,496.5`. Behaviour is consistent
with the frozen declared rule. However, that prior required fix also asked to
**extend self-tests** for percent/dollar/scale;
`test_matcher_regressions.py` contains no such tests. Partial closure.

### 4.2 The two counterexamples - one tested, one not; repair is fixture-shaped

Authority section 2 correction 2 names two counterexample classes:
(a) a digit matching as a **substring** of a larger number (5 inside 2015);
(b) the same number in a **wrong semantic role**.

| Class | Covered by a regression test? | Actually blocked? |
|---|---|---|
| (a) substring - 5 inside 2015 | **NO test** | Yes, incidentally: `_numeric_literals` extracts `2015` as one literal |
| (b) wrong role | one test | **Only for that fixture** |

`test_classifier_counterexamples_require_visible_role_context` passes, but:

- Test 1 (expected 17, source has 42) is trivially false - the expected value
  is absent. It tests nothing about roles.
- Test 2 (`table row: 42` vs `units shipped?`) fails on **lexical overlap
  absence**, not role reasoning.
- **C minimal perturbation breaks it:**
  `numeric_role_match` on question `How many units were shipped?` with source
  `units returned: 42` and expected 42 -> **True**. Wrong role (returns is not
  shipments) is accepted.

Root cause: `numeric_role_match` (`FUTURE_EVALUATION_MATCHER.py:101-111`) has
exactly one role signal - non-empty intersection of question and source tokens.
That is lexical co-occurrence, not semantic role. The function is also **new**;
the historical matcher has no `numeric_role_match` at all (`AttributeError`),
so the repair adds a parallel helper rather than correcting the classifier the
counterexamples were drawn from.

Authority section 5.1 does **not** require a general semantic oracle - it
requires that the counterexamples block automatic certification of sufficiency
and route to pending adjudication. **No adjudication/pending mechanism exists
anywhere in the package** (C grepped for adjudicat / pending / sufficien /
auto-certif across all `.py`, `.md`, `.json`). `numeric_role_match` returns a
bare bool as if it settled the question.

Latent only - zero generation occurred, so nothing was mis-certified yet. Must
be fixed before generation.

### 4.3 12-UID selection - pre-output, deterministic, well stratified

C replayed `select_and_reference.py` from the three hash-pinned sources:

```
python3 .../select_and_reference.py --row-results ... --raw-dev ... --qualification ... --output-dir /tmp/c_select_replay
-> exit 0; output identical to stored P2_SELECTION_RECEIPT.json (same 12 UIDs, counts, hashes)
```

| Property | Value | Requirement | Status |
|---|---|---|---|
| Panel size | 12 | <=12 | PASS |
| Seed | 20261026 | fixed | PASS |
| `model_output_viewed` | **false** | before output | PASS |
| Denominator preserved | screen 507, future_eval 506 | preserve 507 | PASS |
| Excluded | 1 (`NOT_MODEL_READY`, ambiguous direction/scale) | per frozen rule | PASS |
| Replacements | `[]` | recorded | PASS |
| UID binding | `selected_uids` == reference-chain `question_uid` | consistent | PASS |

Panel composition (C counted from `P2_REFERENCE_CHAIN.json`):

- `proxy_disagreement`: **8 disagree / 4 agree** - covers both, as required.
- `source_requirement`: **4 both / 4 paragraph / 4 table**.
- `answer_type`: arithmetic 4, multi-span 3, span 3, count 2.
- `role`: table 8, paragraph 4.

This is a well-constructed development panel. The single exclusion is
legitimate: `question_uid 81fc6048...`, gold `68.07` from
`(3,901-2,321)/2,321`, where the gold percent interpretation and hidden percent
scale are not legally observable - the same measurement-contract class as the
P1 unit residuals.

### 4.4 Reference chain - genuine, correctly identified

Schema `p2_question_table_role_unit_program_answer_chain_v1`, 12 rows, each
with question -> table_text -> role -> unit -> program -> answer plus
supporting paragraphs.

`review_identity` on every row:
automated AI review; not human gold or a complete semantic oracle - satisfies
the authority section 5.1 identity requirement exactly.

C spot-verified values against the visible tables:

| Row | Claim | Table | Status |
|---|---|---|---|
| 1 | 10,425.5 = `(9,660+11,191)/2` | `R4` trade receivables 9,660 / 11,191 | **correct** |
| 2 | `155`, `113` payroll taxes | `R3` 155 / 113 | **correct** |
| 3 | `96,168` Canada external revenue | `R3 C1` 96,168 | **correct** |

### 4.5 Formal preflight - FAIL, and the classification is wrong

`P2_FORMAL_PREFLIGHT_RECEIPT.json` - 10 PASS, **2 FAIL**:

| Check | Status | Detail |
|---|---|---|
| `analysis_plan` | **FAIL** | three-arm P2 runner->adapter->scorer contract is **absent** from this task namespace |
| `integration_dry_run` | **FAIL** | cannot execute runner to adapter to scorer-input seam **without a P2 adapter/runner implementation** |

**Both failures state absence of an implementation. Neither is an observation
about the proxy.**

### 4.6 Engineering gap vs scientific observation - BLOCKING

**Classification: in-scope engineering qualification gap. Not a scientific
observation.**

Evidence that it is in-scope:

1. **Authority line 90 explicitly grants A the runner:**
   `A: same dedicated GB10 worktree, owns the G1 derived package, the new
   research directory and raw/runner; first complete section 4 and 5
   qualification` - A *owns* `raw/runner`, and must complete section 4/5
   qualification before generation.
2. **A_TASK G3 step 4** requires A to run the formal preflight including a
   **runner-to-adapter-to-scorer dry run**. A dry run of a chain presupposes
   the chain exists; building it is the work.
3. **A_TASK ownership list** names `research/.../raw/` as a directory A is to
   create and own. **`raw/` was never created** (verified: path absent).
4. **No runner, adapter, or scorer file exists anywhere in the package**
   (verified by searching for runner / adapter / scorer).

What A did instead (`A_RETURN.md:12`):

> **P2: no information value yet; stop this generation candidate.**

That is the misclassification: the absence of an in-scope artefact is
converted into a scientific finding about the proxy.

**What CAN be concluded with zero model calls:**

- R7/R8 behave as declared on tested fixtures (4.1).
- A 12-UID panel exists, selected before output, deterministic, well stratified.
- A reference chain exists with correctly recorded AI review identity.
- The three-arm experiment was **not** run; there is no answer/cost comparison.
- Generation was correctly stopped before any model call.
- The offline proxy information value is **unmeasured**.

**What CANNOT be concluded with zero model calls:**

- Whether the offline proxy predicts complete answers or actual cost - the
  entire G3 question.
- Whether full context is more accurate, cheaper, or whether restricted
  context is harmful.
- **That the proxy has no information value.** Information value is a property
  of the proxy-to-measured-answer/cost relation, and no answers or costs were
  measured.
- Any 2pp non-equivalence.

Authority section 5 is explicit that this is a **diagnostic experiment whose
result is allowed to be unknown** and must not be blocked on unproven benefit.
The escape clause in section 5 (if not even an 8-12 item panel or actor with a
clear reference chain can be established) does **not** apply: the panel and
the reference chain *were* built.

The A next-experiment note (`A_RETURN.md:14`) is to add a hash-bound P2 runner,
visible-context adapter and scorer-input builder - i.e. A names the missing
in-scope artefact as future work.

**Impact:** as written, G3 would be closed as no information value on an
engineering gap. That would permanently mis-seed the C3 candidate and the
thesis narrative.

**Smallest follow-up:** implement the hash-bound three-arm
runner->adapter->scorer-input chain under `raw/` (already A-owned), run the
zero-output dry run on all 12 UIDs, re-run the preflight to
`END_TO_END_PREFLIGHT_PASS`, and only then execute the frozen 3-arm design.
**Re-label the current disposition** from no information value to
`ENGINEERING_QUALIFICATION_GAP_NOT_YET_MEASURED`. Stopping generation was
correct and should stand.

### 4.7 Cost accounting

| Category | Value | Status |
|---|---|---|
| P2 generation calls | 0 | verified consistent across `P2_GENERATION_STOP_RECEIPT.json`, `ZERO_TRAINING_EVIDENCE.md`, preflight |
| P2 generation tokens | 0 | consistent |
| Training calls / tokens | 0 / 0 | consistent |
| Judge calls | 0 | consistent (`figures/receipt.json` also 0) |
| Endpoint calls | 0 | consistent |
| Production / database probes | 0 | C ran none; A package shows none |
| Hard caps preserved | 48 calls / 240,000 tokens unused | PASS |

**Unmeasured category recorded wrongly (non-blocking but required by the
task):** `A_RETURN.md:48` and `ZERO_TRAINING_EVIDENCE.md:8` state
`A usage is NOT_APPLICABLE_NO_CALL`. That conflates two things. Zero
*scientific generation* is true. The **A harness itself** demonstrably ran -
45 files, +6,662 lines - so its input/cache/output/reasoning are **UNKNOWN,
not not-applicable**. Authority section 2.6 and section 8 require exactly this
split (do not equate zero scientific generation with zero cost; keep unknown
cache/subscription fees as UNKNOWN; account harness cost and research-sample
cost separately).

Correct entry: scientific generation 0; **harness tokens `UNKNOWN`, harness
fees `UNKNOWN`** - matching the schema already used in the Phase B
`TASK_RESULT_C.json`.

Also unmeasured and unrecorded: wall-clock, and the tectonic `Exec format
error` attempt.

### 4.8 Exposure boundary - PASS

Frozen `P1_SEMANTIC_LEDGER_FINAL.json` denominators match the A report exactly
(24 ordinary originals, 19 correct controls, 5 diagnosed candidates, 4 genuine
errors, 1 reference defect). The 507 TAT-QA dev questions retain exposed
development identity; the 12-UID panel is drawn from that same 507. No
new-source claim is made anywhere. `finqa_used: false`.

---

## 5. Blocking defects

| ID | Area | Location | Evidence | Impact | Smallest follow-up |
|---|---|---|---|---|---|
| **B1** | P2 | `A_RETURN.md:12`; `p2_proxy_calibration/receipts/P2_FORMAL_PREFLIGHT_RECEIPT.json:36-50` | Both FAILs are implementation absent; authority line 90 grants A `raw/runner`; `raw/` never created; no runner/adapter/scorer exists | G3 closed as no information value on an engineering gap; would wrongly terminate the C3 candidate | Implement hash-bound runner->adapter->scorer under `raw/`, dry-run 12 UIDs, re-run preflight to `END_TO_END_PREFLIGHT_PASS`, then run the 3 arms. **Re-label** disposition `ENGINEERING_QUALIFICATION_GAP_NOT_YET_MEASURED`. Keep the generation stop. |
| **B2** | Paper E | `paper_e_sncs/paper_e_sncs.pdf`; `compile_package_pdf.py:15-29`; `BUILD_RECEIPT.md:9` | 1 page, 3,031 B, ReportLab; PDF abstract 134 w vs manuscript 190 w; manuscript never compiled (tectonic exit 126) | No reviewable submission PDF exists | Compile the real `.tex` with an aarch64-capable engine; record engine + page count in `BUILD_RECEIPT.md`; make the PDF a true rendering; re-hash |
| **B3** | Paper E | `paper_e_sncs/paper_e_sncs.tex` (73 lines / 752 words) vs `source_iccart_original.tex` (242 / 6,089) | Method, Related Work, Experimental Setup, Data Availability dropped; Results collapsed; Reviewer Pass as a section in the submission; 0 tables | G1 core deliverable unmet | Port and adapt Method / Related Work / Setup / Results from the original; add provenance pointers for every number; move reviewer pass to `FIRST_REVIEWER_PASS.md` |
| **B4** | Paper E | `paper_e_sncs/paper_e_sncs.tex:55-72`; `references.bib` | 0 `\cite`; 24 BibTeX entries unused; no `\bibliography`; 2 `\bibitem` never cited | Closest-work claim unsupported; shipped bibliography is not the one used | Add `\bibliography{references}`, cite closest work, drop/wire the 2 orphan bibitems |

## 6. Non-blocking limitations

| ID | Area | Location | Finding | Follow-up |
|---|---|---|---|---|
| N1 | P1 | `P1_FULL_24_REPORT.md`, `A_RETURN.md:10` | 23/24 is numeric program correctness; complete semantic is **13/24**; unit agreement 14/24 | State both identities side by side wherever 23/24 appears |
| N2 | P1 | `full_24_regression.json` row 7 | Only `direction_conflict: true`; the two acceptable interpretations are not recorded | Record both readings, mark `UNRESOLVED` per authority section 4 |
| N3 | P1 | `receipts/P1_TEST_RECEIPT.md:3` | Exit-1 pytest line presented in a test receipt; 0 tests ran. Tests pass 3/3 under a manual harness | Run tests under a working harness; fix the bare import against `__init__.py` |
| N4 | P2 | `FUTURE_EVALUATION_MATCHER.py:18` | `HISTORICAL_PATH` is cwd-relative; tests fail outside repo root | Anchor to the module file location |
| N5 | P2 | `FUTURE_EVALUATION_MATCHER.py:101-111` | `numeric_role_match` is lexical overlap, not role semantics; wrong-role source wrongly accepted; no substring (5-in-2015) test; no pending-adjudication routing | Implement the adjudication state authority section 5.1 requires; add both counterexample classes as tests |
| N6 | P2 | `test_matcher_regressions.py` | Prior R2 fix asked for percent/dollar/scale self-tests; none present | Add them |
| N7 | P2 | `FUTURE_EVALUATION_MATCHER.py:56` | Spaced digit group still matches via whitespace stripping; pre-existing but wider than digit-adjacent only | Narrow or declare |
| N8 | Paper E | `paper_e_sncs.tex:25,29,43` | `fig1_measurement_chain.svg` unused; `fig2...png` embedded twice; Figure 1 caption/cross-ref do not match its image | Use `fig1...svg` for `fig:chain`; remove the duplicate |
| N9 | Paper E | `ABSTRACT_STRUCTURED.md:1` | Labels itself 211 words; actual 190 (still inside 150-250) | Correct the label |
| N10 | Paper E | `paper_e_sncs.tex:21,36` | Drops the checkpoint-level qualifier on `96/118` that the original carries | Restore the measurement-object qualifier |
| N11 | Paper E | `AI_USE_DISCLOSURE.md` | Package-level only; authority section 3 wants per-section/per-code disclosure | Enumerate sections and code that used AI |
| N12 | Paper E | `paper_e_sncs.tex` | Every number is a bare count with no provenance pointer (source had richer detail: tie counts 91/135/83/125, slope 0.375, 112/118, 2,382 clean records) | Add table/artefact references |
| N13 | Package | `ALL_FILES.sha256` | `A_RETURN.md` hash wrong vs its own git blob; 7 `.pyc` entries untracked in git | Regenerate manifest from final files; drop `.pyc` |
| N14 | Package | `raw/` | Listed in A_TASK ownership; never created | Create with the P2 runner (B1) |
| N15 | Accounting | `A_RETURN.md:48`, `ZERO_TRAINING_EVIDENCE.md:8` | `A usage = NOT_APPLICABLE_NO_CALL` conflates zero scientific generation with zero harness cost | Record `harness_tokens: UNKNOWN`, `harness_fees: UNKNOWN` |
| N16 | Thesis | `EVIDENCE_TABLE.md` new row | 7 cells against a 4-column table - malformed markdown | Reformat |
| N17 | Thesis | `EVIDENCE_TABLE.md` pre-existing P2 row | Still asserts 506 independent complete semantic references, potential is an upper bound on true answer accuracy, and measured actual cost shows no benefit - the extrapolations authority section 2 corrections 3 and 5 order corrected | Correct while the file is open |
| N18 | Governance | `A_EXECUTION_CONTRACT.md:49-50` | Loaded 5 skills (cap OK) but 2 outside the A authority list (`paper-review-check` is the **C** skill; `testing-practices`, `paper-polish-and-audit` unlisted) | Keep A to `research-writing-skill` / `executing-plans` / `structured-output` / `verify-before-done` |

## 7. Ownership, boundaries, and integrity

| Check | Result |
|---|---|
| A touched `memory/STATE.md` / `THREADS.md` / `DECISIONS.md` | **NO** |
| A touched `docs/research/LOOP_D_RESEARCH_PROMPT.md` | **NO** |
| A touched `tests/test_m1_service.py`, `scripts/graph/frozen_hashes.txt`, docs 33/34 | **NO** |
| Committed `.env` / credentials / weights / logs | **NO** |
| A modified frozen evidence or old score files | **NO** |
| Commit contains only owned paths | **YES** - 45 files, all under the owned set plus the two owned thesis files and package scaffolding |
| C modified any A artefact | **NO** - C wrote only under `audits/` |

Ownership was respected. The A stop-before-generation on a failed preflight
was **correct** and is preserved.

## 8. Old-failure reserve

**Justified - yes, for one bounded A remediation.**

B1 is a conclusion-level error (it would wrongly close G3). B2-B4 are
deliverable-level for G1. Authority section 8 reserves the old-failure
contingency for blockers affecting conclusion, safety, or reproducibility.
B1 affects conclusion; B2/B4 affect reproducibility and the reviewability the
G1 deliverable exists to provide.

Scope discipline for the remediation:

- **One A dispatch.** Build `raw/` runner->adapter->scorer, complete the SNCS
  manuscript and compile it, wire citations, re-label the P2 disposition.
- **Do not** spend it on prose polishing (N8-N12, N16) - those are disclose-once.
- **Do not** start generation inside the remediation; generation follows
  `END_TO_END_PREFLIGHT_PASS` as a separate authorized step within the existing
  48-call / 240k cap.
- **P1 does not need re-running**; it is independently reproduced and accepted.

## 9. Commands executed by C (exit status)

| # | Command | Exit |
|---|---|---|
| 1 | `git rev-parse HEAD:docs/research/LOOP_D_RESEARCH_PROMPT.md` | 0 |
| 2 | `sha256sum docs/research/LOOP_D_RESEARCH_PROMPT.md` | 0 |
| 3 | `python3 .../run_full_regression.py --instances <frozen> --results <frozen> --output /tmp/C_recompute_24.json` | **0** |
| 4 | `python3 -c <diff A artefact vs C recompute>` | 0 - rows identical, summary identical |
| 5 | `python3 -c <independent row-level recount>` | 0 |
| 6 | `python3 -c <unit/program/refs identity>` | 0 |
| 7 | `python3 -c <gold-unit visibility test on 10 UNKNOWN rows>` | 0 |
| 8 | `python3 -c import pytest` | **1** - `ModuleNotFoundError` |
| 9 | `python3 -m pytest --version` | **1** - `No module named pytest` |
| 10 | `python3 -c <execute test_public_actor.py bodies>` | 0 - 3/3 pass |
| 11 | `python3 -c <execute test_matcher_regressions.py bodies>` from `p2_proxy_calibration/` | **1** - `FileNotFoundError` |
| 12 | `python3 -c <execute test_matcher_regressions.py bodies>` from repo root | 0 - 3/3 pass |
| 13 | `python3 -c <historical vs future matcher, R7/R8>` | 0 |
| 14 | `python3 -c <numeric_role_match perturbation>` | 0 - wrong-role source wrongly True |
| 15 | `python3 .../select_and_reference.py ... --output-dir /tmp/c_select_replay` | **0** - output identical to stored receipt |
| 16 | `python3 -c <PDF page count / producer probe>` | 0 - 1 page, ReportLab |
| 17 | `python3 -c <tex structure, cite, bibliography, figure census>` | 0 |
| 18 | `python3 -c <source_iccart_original.tex vs paper_e_sncs.tex>` | 0 |
| 19 | `python3 -c <ALL_FILES.sha256 integrity>` | 0 - 4 mismatch, 3 missing |
| 20 | `python3 -c <hash-scan for frozen inputs>` | 0 - P1 instances/results external; raw_dev external |
| 21 | `python3 -c <P2 panel composition and UID binding>` | 0 |

## 10. Excluded / unverified

| Item | Status | Reason |
|---|---|---|
| Full LaTeX compile of `paper_e_sncs.tex` | UNVERIFIED | no aarch64 TeX engine in the C environment; the A tectonic attempt failed exit 126 |
| pytest-collected execution of the test modules | UNVERIFIED | pytest not installed; bodies executed manually instead |
| Whether the bare `public_actor` import collects under pytest | UNVERIFIED | cannot run pytest |
| Human/venue review of Paper E | OUT OF SCOPE | AI review is not human gold or acceptance |
| Model / judge / training / canary / production / DB probes | EXCLUDED | zero-endpoint; C made **0** such calls |
| A-owned source, labels, manuscripts, receipts, raw, thesis text, memory ledgers | EXCLUDED | read-only boundary; nothing modified |

## 11. Independent AI review

This report is an independent AI review. It is not human gold, not a venue
decision, and not a claim of acceptance or school recognition. Counts marked
independently recomputed were reproduced by C from hash-pinned inputs; counts
marked verified were checked first-hand; inferences are labelled as such in
the machine-readable result.

