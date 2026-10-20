# Independent Scientific Review

Status: `CONDITIONAL`

Reviewer role: independent scientific review (Loop C). This review used the
specified raw artifacts and read-only deterministic recomputation. No model,
judge, training, or production-memory request was made. This file is the only
file written by this review.

## Executive Verdict

**Paper E: CONDITIONAL / 收窄后继续。** The FinRank case supplies a real,
reproducible implementation-level measurement result: tie policy moves absolute
pairwise scores but does not change the hard-versus-random ordering, and the
first-occurrence source limitation reproduces. The paper can continue as a
bounded two-case measurement-audit paper after the provenance and wording
corrections below. It is not accepted as evidence for a universal audit method.

**Experience scope: CONDITIONAL, generation not authorized.** Candidate A is a
credible development question and the deterministic qualification counts are
correct. The current draft does not yet establish an actor-visible applicability
contract or per-task reference unambiguity. It is suitable for design completion
and an increment review, not for generation or an independent confirmation
claim.

## 1. Evidence Recomputed Before Reading The Main Reports

I read `GOAL_AND_RESEARCH_PLAN.md`, the frozen manuscript, the pinned FinRank
README/LICENSE/`run_baselines.py`/`FinRank.jsonl`/`results.json`,
`PRE_REGISTRATION.json`, `finrank_audit.py`, `APPLICATION_RESULTS.json`,
`SCOPE_TASK_QUALIFICATION.json`, and `SCOPE_TASK_DRAFT.json`. I recomputed the
following from the raw JSONL and official metric formulas in read-only mode:

| Check | Independent result | Assessment |
|---|---:|---|
| Records | 1,185 | Matches release and result JSON |
| Unique raw pooled texts | 5,230 | Matches paper/results; README says 5,270 |
| Non-empty passage/HN occurrences | 8,343 | Matches audit output |
| Unique trimmed texts | 4,957 | Matches audit output |
| Raw cross-role overlap | 125 texts, 293 HN occurrences, 220 records | Superseded identity rule |
| SHA1 cross-role overlap | 162 texts, 442 HN occurrences, 305 records | Matches canonical disclosure |
| First-occurrence metadata gold loss | 33 any / 2 all | Matches official results |
| Source components | 3: pharma, energy, auto | Matches qualification |
| Eligible scope records | 181 | Matches qualification |
| TF-IDF hard/random ties | 91 / 135 pairs | Matches application output |
| BM25 hard/random ties | 83 / 125 pairs | Matches application output |

I regenerated the TF-IDF and BM25 matrices under the pinned local runtime.
Both matrices were bit-for-bit equal to the stored score cache. The pairwise
counts and macro scores were also independently reproduced:

- TF-IDF: hard 77.7556/77.0298/77.3927 and random 91.9347/90.8503/91.3925
  for ties-positive/strict/half-credit; gaps 14.1792/13.8205/13.9998.
- BM25: hard 74.7801/74.0938/74.4370 and random 87.7893/86.7598/87.2745;
  gaps 13.0092/12.6660/12.8376.

These values support the narrow claim that tie policy is material for absolute
calibration (roughly 1.03--1.08 points on random accuracy) while the
hard-versus-random gap is stable within 0.36 points and retains its direction.

## 2. Paper E Review

### Findings that are supported

1. **The external object is real and inspectable.** FinRank revision
   `916dc27e77b90e294ea1b3a2cc5b0abcf07392d1`, the 1,185-record JSONL, the
   official baseline, and the released result JSON form a traceable chain.
   The README's CC BY-NC 4.0 license and its explicit curated-pool limitation
   are correctly treated as author contract, not as defects discovered here.
2. **The tie analysis is reproducible.** `run_baselines.py:76-101` makes
   gold-first stable ordering and ties-positive pairwise scoring explicit.
   The independent recomputation confirms the reported tie counts and policy
   sensitivity. The global tie-order probe stays below the preregistered
   0.5-point materiality threshold.
3. **The source-identity limitation is correctly narrowed.** The canonical
   `text_sha1` identity reproduces 442 hard-negative occurrences over 305
   records, and first-occurrence metadata produces the disclosed 33/2 gold
   loss. The raw-text 293/220 result is an earlier, less appropriate identity
   rule, not a contradiction in FinRank.
4. **The two-case framing is defensible if kept bounded.** The original
   staged case can retain its visibility/detection/harmfulness distinction;
   FinRank adds score-contract, tie-order, identity, and reproducibility
   observations. The draft correctly says the review sequence is a design
   proposal rather than a validated universal method.

### Blocking issue 1: frozen provenance is not intact

`paper_e_audit/PRE_REGISTRATION.json:3-14` declares
`FROZEN_BEFORE_APPLICATION_RESULTS` and binds
`audit_code_sha256=CE0DEFDA5F32645FE67E8292CB2D0DF26045B99B20AE3FF4CE19D164BDE771C8`.
The current `finrank_audit.py` hashes to
`1A2E0AFDF3DB12ED78DA72CB9F980F82D938AD0C7153BF20B25A906B675FE8BF`.
The preserved `APPLICATION_RESULTS_v1_raw_text_overlap.json` was written at
01:45, the source file was changed at 01:47, and `APPLICATION_RESULTS.json`
was written at 01:48. The v1/v2 outputs have identical tie, in-record, global,
and random-sampling sections; only the source-identity fields changed from
raw-text identity to the canonical SHA1/taxonomy identity.

Therefore:

- The tie and gap results can be reported as the frozen application result,
  because they are unchanged across the preserved v1 and corrected v2 runs.
- The 442/305 source result must be labelled **post-hoc identity correction**
  after the first application, unless the old script and a change record are
  supplied. It cannot be presented as a preregistered observation that
  reproduced without qualification.
- The revision draft's repeated phrase that the complete FinRank application
  is “frozen” (`PAPER_E_REVISION_DRAFT.md:5,13,93-99`) is too strong until this
  distinction is made explicit.

This is a provenance blocker for the current claim wording, not a refutation
of the numerical tie result.

### Blocking issue 2: the residual reproduction cause is over-located

The audit correctly finds exact in-record/pairwise reproduction but small
global and metadata-filtered drift (up to 0.19 and 0.16 points in the pinned
run). It also states that the cause cannot be uniquely attributed without the
original score cache or complete transitive environment
(`PAPER_E_EXTERNAL_AUDIT.md:157-165`, `PAPER_E_REVISION_DRAFT.md:204-206`).
However, the executive wording says the audit “locates” the remaining gap in
ranking/report identity (`PAPER_E_EXTERNAL_AUDIT.md:212-217`). The evidence
only supports a residual gap **consistent with** tie-order or environment
drift; it does not identify the cause. Replace “locates” with “exposes a
residual gap whose cause is unresolved.” This is a claim-precision blocker.

### Non-blocking limitations

- FinRank was audited only with deterministic TF-IDF/BM25 paths; neural
  baselines and answer generation were not rerun.
- The application is source-informed, not blind. The tie-positive policy,
  first-occurrence mapping, and author-disclosed overlap counts were visible
  before application.
- The 5,270/5,230 README discrepancy is a documentation correction, not a
  scientific discovery or evidence of benchmark failure.
- The review sequence is useful external guidance, but it has not been
  independently applied as a validated general method. Keep it as a proposed
  audit procedure and a bounded contribution.

### Paper E disposition

**CONDITIONAL_CONTINUE_AFTER_NARROWING.** Accept the revised paper direction
only after:

1. separating frozen tie findings from post-hoc identity correction in the
   abstract, methods, results, and evidence-status table;
2. replacing the over-located reproducibility claim with the unresolved-cause
   wording;
3. keeping “bounded two-case audit” and “design proposal” language, without a
   universal-method, benchmark-defect, or human-gold claim.

## 3. Experience Scope Review

### Findings that are supported

- `SCOPE_TASK_QUALIFICATION.json` independently matches the source data:
  1,185 records, 181 eligible, 12 development tasks, 12 future-development
  tasks, and 24 history candidates. The eligibility rule is not selected from
  model errors.
- Conservative exact-hash union produces three source components, with
  development=auto, history=pharma, and future=energy. The report correctly
  states that `ticker|year|form` is not a stable filing-report identity.
- Candidate A is the right development question among the three considered.
  It has a real actor action (apply/skip/abstain plus evidence selection),
  an objective supporting-passage reference, and a falsifiable possibility
  that a strong rule or ordinary solved examples explain the effect.
- The proposed H-U/H-S pair is the correct control shape: identical raw trace
  content and order isolate the scope gate from trace content. R and K are
  necessary to rule out static rules and generic few-shot explanations.
- Candidate B is deferred appropriately because the current histories do not
  contain qualified wrong-action-to-correction chains. Candidate C combines
  too many mechanisms for an interpretable first test.

### Blocking issue 3: applicability scope is not actor-visible

The study says the actor decides applicability from visible entity, period,
form, and unit scope (`EXPERIENCE_SCOPE_STUDY.md:184-217`). The actual
`SCOPE_TASK_DRAFT.json` `actor_view` exposes question, passage text,
`candidate_id`, and page number, but no structured candidate scope fields and
no explicit form/unit contract. The hidden reference contains source IDs and
scope-qualified negative lists, but that cannot be used by the actor.

This makes `APPLY / SKIP / ABSTAIN` under-specified: period may sometimes be
inferred from passage text, while filing form and unit are not consistently
visible. The future gate can become either a metadata lookup (if hidden scope
is exposed) or an impossible semantic guess (if it remains hidden). Before
generation, define an actor-visible scope schema or a deterministic text-only
scope rule, and prove on positive/negative fixtures that the gate is neither
answer leakage nor a direct gold-ID lookup.

### Blocking issue 4: reference ambiguity is not closed per task

FinRank is manually authored but has one annotator per record and no formal
inter-annotator agreement. The qualification only proves no exact gold/HN
`text_sha1` overlap. It does not prove that each of the 24 visible candidate
sets has exactly one sufficient evidence interpretation. The study itself
requires human semantic adjudication when multiple visible passages can answer
the question or when period/unit semantics are ambiguous
(`EXPERIENCE_SCOPE_STUDY.md:219-227`). That adjudication is not recorded for
the draft tasks. Until it is done, the exact evidence-set reference is a
development label, not a settled gold standard.

### Other constraints

- Three source components are sufficient for a development signal but not for
  report-level or cross-source generalization. Keep the result explicitly
  `DEVELOPMENT_ONLY`.
- The release has no stable report ID; do not call the split report-disjoint.
- The actor-visible task must never contain hidden source passage IDs,
  reference answers, or future outcomes. The current draft is structurally
  close to this requirement, but the runner contract must prove it.
- The selected history cards must be task-matched and frozen without looking
  at future outcomes. Existing TAT-QA traces cannot be relabelled as FinRank
  experience.

### Experience disposition

**CONDITIONAL / GENERATION_NOT_AUTHORIZED.** Permit design completion and one
increment review. Do not issue B0, history collection, or H-U/H-S requests
until the scope contract and per-task reference adjudication are closed.
After that, run only the preregistered development comparison. If R or K
matches H-S, or H-S only repairs formatting/tool validity, report a simple
control/interface explanation and stop the mechanism claim. With only three
source components, any positive result supports a development signal only,
not independent validation.

## 4. Remaining Scientific Disagreements

1. **Frozen versus post-hoc:** I accept the unchanged tie metrics as frozen,
   but not the corrected source-identity count as an unchanged preregistered
   result.
2. **Reproducibility cause:** I accept a residual numerical reproduction gap,
   but not the claim that ranking/report identity has been located as its
   cause.
3. **Contribution level:** FinRank adds a useful bounded measurement case and
   a concrete reporting action; it does not establish a universal audit
   method. The largest novelty threat remains generic construct-validity and
   metric-audit work, with MemRL/AWM/ExpeL threatening any stronger
   experience-mechanism claim.
4. **Experience gate:** H-U/H-S is a sound comparison design in principle,
   but the current task material does not yet give the actor a reproducible
   applicability decision surface.

## 5. Required Follow-up Before Any Next Gate

1. Add a versioned provenance note distinguishing the v1 frozen tie run,
   the v2 canonical-identity correction, and the unchanged metric sections.
2. Revise the abstract and discussion to expose, but not locate, the residual
   reproduction gap.
3. Add actor-visible scope fields or a deterministic scope contract, plus
   positive/negative/ambiguous fixtures.
4. Record per-task reference adjudication or explicitly exclude ambiguous
   tasks. Keep all exclusions and their reasons.
5. Freeze the H-U/H-S/R/K content and tool response contract before any
   generation request.

Until these are complete, the scientifically accurate outcome is:

> Paper E is a promising narrowed measurement-audit contribution with a
> provenance correction outstanding; the experience-scope candidate is a
> qualified development design, not an authorized experiment or a validated
> experience-learning mechanism.

