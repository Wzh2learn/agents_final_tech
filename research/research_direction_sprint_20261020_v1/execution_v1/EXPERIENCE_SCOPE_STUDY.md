# Experience Scope Study

> Goal: `PAPER_E_EXTERNAL_AUDIT_AND_EXPERIENCE_SCOPE_V1`
> Status: `CANDIDATE_SELECTED / BLOCKED_REFERENCE_AND_TOOL_CONTRACT_PENDING / GENERATION_NOT_RUN`
> Scientific type: development design and bounded headroom qualification, not a
> learning-effect result.

## 1. Mode And Boundary

**Mode:** `portfolio-triage`, followed by a `minimal-experiment` design gate.
The decision object is which experience-reuse question should consume the next
bounded development effort.

**Evidence boundary:**

- Read the governing plan sections 2 and 6-12, repository instructions, the
  stopped same-number role summary, the current role-history ledger, the TAT-QA
  reuse decision and the 12-experience pool metadata.
- Re-read six direct neighbors from official arXiv source packages: ACE,
  MemRL, A-MEM, Agent Workflow Memory, ExpeL and Reflexion.
- Ran only deterministic, non-generative checks over the vendored FinRank
  release. The new research ledger remains `0/192` requests and `0/2,000,000`
  accounting tokens.
- OpenAlex and Semantic Scholar search endpoints returned HTTP 429 during this
  pass. The arXiv ID endpoint succeeded; search failure is not treated as proof
  that no other work exists.
- Protected exclusions: the stopped role-binding panel was not reopened; no
  model, judge, training, production-memory or paid research API was called.

This document completes an inquiry and proposes a development gate. It does not
record a human decision, independent review, authorized generation run or
accepted experimental result.

## 2. Facts And Inferences

### 2.1 Current project evidence

`FACT` The prior restricted table panel cannot identify a unique historical
experience effect. The same-number H and ordinary solved-example K arms were
both 6/6 and made the same six final decisions. The final task-matched history
collection produced five first-attempt successes and zero role-decision
corrections. See
`research/decision_space_autopsy_v1/exploratory_b0_v1/SAME_NUMBER_ROLE_EXPLORATION_SUMMARY.md`.

`FACT` The older TAT-QA panel reached 16/16 under B0 and stopped at
`CEILING_ON_THIS_PANEL`. See
`research/tatqa_wp0_2026/history_collection_execution_v1/reuse_opportunity_v1/RESEARCH_DECISION.md`.

`INFERENCE` These are bounded negative design results, not evidence that
experience is universally ineffective. They do show two recurring failure modes
in our experimental construction:

1. the prompt or preprocessing removes the decision that experience is supposed
   to change;
2. ordinary solved examples or strong rules explain the observed gain.

`FACT` The existing TAT-QA experience pool contains 12 qualified traces, but
its task is restricted table calculation. It does not carry report-period or
filing-form evidence-selection experience for FinRank. Reusing those traces as
if they were task-matched would create a relevance confound.

### 2.2 Candidate comparison

| Candidate | Real actor action | Experience-only information | Strongest alternative explanation | Evidence status | Decision |
|---|---|---|---|---|---|
| A. Applicability scope and error transfer | Decide `APPLY / SKIP / ABSTAIN` for each historical experience, then select evidence passage IDs and consume them in a real tool call | A task-matched executed trace ties a scope condition to a later-useful or harmful evidence action | Static period/form/unit rules, ordinary solved examples, or fixed retrieval already explain the effect | Natural FinRank conflicts exist; task-matched histories do not yet exist | **SELECT FOR DEVELOPMENT PREP** |
| B. Feedback granularity and update content | After execution feedback, decide which action or experience field to keep, revise or discard | Action-level feedback separates a lucky correct answer from a reliable action | More complete answers or more tokens explain the effect; Reflexion/ACE already cover feedback-driven context updates | Current histories lack reliable wrong-action-to-correction chains | `DEFER_NEEDS_QUALIFIED_FEEDBACK` |
| C. Conflict and invalidation recovery | When old and new experiences conflict, retain, override or stop reuse | Source authority and validity interval explain why a previously useful action is now unsafe | Recency, source priority or a static conflict rule already resolves the problem | Requires multi-round updates and controlled conflicts; cost is highest | `DEFER_AFTER_A` |

`VALUE` Candidate A is selected because it has an objective public reference,
a concrete harmful action (choosing a superficially similar wrong-period or
wrong-form passage), a role for experience that is not precomputed, and a clean
stop result if strong rules or solved examples explain everything.

Candidate B is scientifically reasonable but currently lacks the evidence type
it claims to study. Candidate C is important for continual adaptation, but its
first experiment would combine conflict detection, source authority and update
policy, making a null result hard to interpret.

## 3. Direct Nearest Work

All six papers were read from official arXiv source packages saved under
`experience_scope/sources/`. The reading was targeted rather than a new broad
survey.

### ACE

**Read:** method, cost/results excerpts, ablations and limitations in
`sources/ace_2510.04618/sections/design_CR.tex`, `results_CR.tex`, and
`limitations_CR.tex`.

`CONFIRMED` ACE represents context as structured playbook bullets with
metadata, helpful/harmful counters, incremental delta updates and a
Generator-Reflector-Curator workflow. It explicitly warns that noisy or
misleading feedback can pollute the context and that simple tasks may need only
one rule.

**Threat:** adding conditions or counters to an experience is not new.

**Possible increment:** ACE adapts and curates context; the proposed study
would freeze experiences and separately test an actor-visible applicability
gate against an unscoped identical experience. Its target is negative transfer
under known period/form/unit scope, not context evolution quality.

### MemRL

**Read:** method, retrieval/utility update, transfer and merge analysis,
limitations in `sources/memrl_2601.03192/mem_rl.tex` around lines 402-545,
840-930, 1788-1855 and 2251-2265.

`CONFIRMED` MemRL is the largest novelty threat. It explicitly states that
semantic similarity does not imply utility, uses Intent-Experience-Utility
triplets, and separates semantic recall from feedback-learned value selection.
It also reports cross-task memory merging and discusses task-similarity limits,
credit assignment and reward-hacking risk.

**Threat:** "do not retrieve a similar but useless experience" is already
covered.

**Possible increment:** do not propose another learned utility score. Test a
predeclared, auditable applicability contract and measure when it prevents
wrong-period evidence transfer. If a strong rule or ordinary examples match
that result, stop rather than rebranding it as a new memory mechanism.

### Agent Workflow Memory

**Read:** task/workflow method, Mind2Web results and the offline-plus-online
appendix in `sources/awm_2409.07429/sections/method.tex`,
`sections/results/mind2web.tex`, and `appendix/experiments.tex`.

`CONFIRMED` AWM shows that reusable workflows can bias actions away from the
current environment, that agents struggle to diverge from a workflow when it is
irrelevant, and that offline and online workflows can be mutually incompatible.

**Threat:** generic workflow negative transfer is not new.

**Possible increment:** isolate one measurable scope dimension in financial
evidence selection and test explicit use/ignore/reject behavior with matched
content. The claim must remain task-specific.

### A-MEM

**Read:** note construction, linking, evolution, retrieval, ablation and
limitations in `sources/amem_2502.12110/neurips_2025.tex` around lines 268-340
and 526-645.

`CONFIRMED` A-MEM already gives memories contextual descriptions, tags,
keywords, links and evolving attributes.

**Threat:** structured scope metadata is not a contribution by itself.

**Possible increment:** only the falsifiable decision to refuse or ignore a
memory under a mismatched condition, and the measured reduction of negative
transfer, could distinguish the study.

### ExpeL

**Read:** experience gathering, insight extraction, transfer, ablations and
limitations in `sources/expel_2308.10144/main.tex` around lines 259-320 and
421-545.

`CONFIRMED` ExpeL combines extracted insights with retrieved successful
trajectories. Its ablations show that task-similarity retrieval beats random or
reason-similarity retrieval and that hallucinated reflections can hurt.

**Threat:** ordinary examples and stronger retrieval are necessary controls;
historical metadata cannot claim credit for content that a solved example
already supplies.

### Reflexion

**Read:** Actor/Evaluator/Self-Reflection loop, episodic feedback memory,
ablation and limitations in `sources/reflexion_2303.11366/main.tex` around
lines 298-422 and 699-758.

`CONFIRMED` Reflexion covers verbal feedback and repeated attempts on the same
task. Its ablation shows that execution checks and self-reflection serve
different roles.

**Threat:** Candidate B is close to this work and needs a genuinely different
update unit or feedback qualification claim. Candidate A does not claim
correction learning and therefore does not need to manufacture failed retries.

## 4. Selected Candidate: Scope-Gated Evidence Experience

### 4.1 Practical task

An analyst agent receives a financial question over filing excerpts and must
select the passages that actually support the requested entity, reporting
period, document form and unit. A previous experience can help when its scope
matches, but applying it to the wrong period or form can select a superficially
similar hard negative.

The actor must make two real decisions:

1. for each fixed historical card: `APPLY`, `SKIP`, or `ABSTAIN`;
2. call a deterministic evidence tool with selected `candidate_id` values,
   consume the returned text, and produce the final answer.

The tool never reveals the answer or gold IDs. Invalid IDs, empty selections
and malformed actions fail closed.

The v2 actor view now exposes an explicit `question_scope` containing target
entity, requested years/dates, form when stated and unit when stated. Every
candidate exposes a `visible_source_scope` containing ticker, filing year and
document form, with `UNRESOLVED` for any missing field. These fields are present
for gold and non-gold candidates alike; no gold label or supporting ID is placed
in `actor_view`.

### 4.2 Experience information

A task-matched history card may contain only an actual trace:

- visible source scope: entity, period, form and unit fields that were visible
  to the actor;
- actor-selected evidence IDs and parameters;
- actual tool return;
- actual answer;
- independently computed reference match and evidence-set match;
- a later real attempt when one exists.

It must not contain a newly invented `lesson`, hidden coordinates, future
answers or a post-hoc correction. Successful first attempts are eligible for
applicability research; they do not become correction-learning evidence.

### 4.3 Reference

`FACT` FinRank provides 1,185 manually authored records with answers,
supporting passages and curated hard negatives. Its README reports CC BY-NC
4.0, single annotator per record and no formal inter-annotator agreement.

The independent reference is the recorded supporting-passage set plus answer.
Human semantic adjudication is required if more than one visible passage can
answer the request or if period/unit semantics are not unique. Such cases are
excluded rather than silently relabeled.

The conservative per-task v2 audit checked all 24 drafts. It found:

- 5 tasks with a hard negative that is whitespace-identical to gold for another
  FinRank record, hence `POTENTIAL_VISIBLE_ALTERNATIVE_SUPPORT`;
- 19 tasks where semantic alternative support could not be ruled out by
  deterministic checks;
- 22 tasks with a unique explicit period set and 2 with unresolved period-role
  conflicts;
- 6 tasks with explicit output-unit sets, 17 without an explicit requested unit
  and 1 partially explicit multi-output case.

All 24 are marked `REQUIRES_HUMAN_SEMANTIC_ADJUDICATION` with
`BLOCKED_PENDING_HUMAN_SEMANTIC_ADJUDICATION`. This is a qualification state,
not a new human gold judgment.

### 4.4 Necessary controls

Five arms are justified for this specific mechanism, not as a restoration of
the old five-arm panel:

| Arm | Content | Alternative explanation isolated |
|---|---|---|
| B0 | No experience | task/model baseline |
| R | Strong static entity/period/form/unit applicability rule | explicit rules suffice |
| K | Ordinary solved examples with matched count and approximate length | generic few-shot examples suffice |
| H-U | Identical task-matched historical traces without the explicit gate | trace content alone |
| H-S | The same traces with the explicit `APPLY/SKIP/ABSTAIN` gate | proposed scope mechanism |

H-U and H-S must use the same card order and raw trace content. Retrieval is
fixed before results; no claim is made about learned retrieval. If H-S does not
separate from H-U, the scope gate is not identified.

### 4.5 Metrics

- **Primary:** paired exact evidence-set success difference `H-S - H-U`,
  summarized by source/report cluster, across a preregistered mix of applicable
  and inapplicable experience opportunities.
- **Required retention check:** on applicable cases, H-S must not lose to the
  best of B0/R/K by a predeclared tolerance.
- **Behavior:** applicability action, wrong-transfer rate, evidence precision
  and recall, tool success, answer/reference match, answer/tool-return
  consistency, UNKNOWN/REFUSE and format failures.
- **Cost:** requests, tokens, context length and experience-construction time.

The sample must be paired. Questions from the same conservative source cluster
are not independent samples. With only three connected source components in
FinRank, the current panel can produce a development signal but not a
cross-report generalization claim.

### 4.6 Falsification and stop rules

Stop the candidate before generation if any of the following remains true after
the independent increment review:

1. actor-visible metadata makes the gate a direct key lookup;
2. the task-matched history selection cannot be frozen without using future
   outcomes;
3. H-U and H-S cannot share the same trace content and order;
4. the reference requires undisclosed semantic judgment;
5. source clusters overlap across history/development/future in the conservative
   exact-text graph.

After generation:

- if R or K matches H-S, report that simple controls explain the effect;
- if H-S only improves formatting or tool validity, report an interface gain;
- if H-S improves applicable cases by causing new errors on inapplicable cases,
  the scope mechanism fails;
- if the result is driven by one ticker or one source component, report
  `UNRESOLVED_SOURCE_HETEROGENEITY`;
- do not move to training or a new memory algorithm from a small positive
  development signal.

### 4.7 Tool contract draft

`SCOPE_TASK_DRAFT.json` now contains a `DRAFT_NOT_EXECUTED` contract for:

1. `plan`: output `APPLY/SKIP/ABSTAIN` actions and selected evidence IDs;
2. `evidence_lookup`: validate IDs and return only visible passage text plus
   visible source scope;
3. `consume`: answer only after consuming the actual tool return, with
   `ANSWER/UNKNOWN/REFUSE` and separate used-ID reporting.

This is a contract draft only. No runner, fixture, request or service was
created.

## 5. Offline Qualification Result

The deterministic script
`experience_scope/qualify_finrank_scope_tasks.py` generated:

- `experience_scope/SCOPE_TASK_QUALIFICATION.json`;
- `experience_scope/SCOPE_TASK_DRAFT.json`.

`this re-verification` results:

- 1,185 records read;
- 181 eligible records have an explicit `20xx` period in the question and at
  least one same-company hard negative from a different filing year or form;
- no eligible record has exact `text_sha1` overlap between a gold passage and
  hard negative;
- 24 tasks remain a blocked draft: 12 development and 12 future development
  holdout; 24 history-collection candidates were selected without model output;
- all 24 task references require human semantic adjudication; 5 have potential
  visible alternative support and 19 remain semantically unresolved;
- a stopword-filtered lexical top-k probe exactly recovered only 72/181 gold
  sets (`0.39779`);
- a simple visible year/form rule produced 98 records with at least one gold
  match, 19 hard-only matches and 64 abstentions.

These probes show remaining decision space. They are not model baselines and
cannot establish that experience will help.

`FACT` Conservative union over every exact shared passage hash collapses the
22 tickers into three source components:

1. pharmaceutical tickers;
2. automotive tickers;
3. energy tickers.

The release lacks a stable filing report ID. `ticker|year|form` can merge
multiple quarterly filings, so report-level independence is `UNRESOLVED`.
The proposed split is history=pharma, development=auto, future holdout=energy.
It is suitable for development feasibility and error-transfer opportunity
analysis, not independent confirmation.

## 6. Recommendation

**Recommendation:** keep generation blocked. Complete human semantic
adjudication of the 24 references and instantiate/test the three-phase tool
contract before requesting any generation decision.

The preferred next unit of work is:

1. adjudicate or exclude each task with possible alternative support, period
   role conflict or unit ambiguity;
2. instantiate the draft evidence tool contract with invalid-output fixtures;
3. construct task-matched history cards only from the fixed pharma history
   candidates, with raw traces and no invented lessons;
4. freeze H-U/H-S/B0/R/K content and the 12-task auto development panel;
5. obtain one independent scientific review of reference ambiguity, source
   isolation and control sufficiency.

If that review has no real blocker, the next run should be a small B0 plus
task-matched history collection, followed by the paired development comparison.
The generation gate is explicitly
`BLOCKED_REFERENCE_AND_TOOL_CONTRACT_PENDING`; the current qualification
artifact is not authorization to generate.

**Conditions:** this recommendation applies only to the FinRank evidence
selection task with fixed source components and a deterministic tool. It fails
if the gate becomes a metadata lookup, if references remain ambiguous, or if
ordinary examples/rules explain all gains.

**Risk and exit:** the largest risk is that MemRL/AWM/ExpeL already explain the
mechanism as utility-aware retrieval or workflow relevance. The exit is
therefore strict: no separation from H-U, R and K means no new mechanism claim
and no further algorithm work.

**First independently verifiable action:** review the generated
`SCOPE_TASK_QUALIFICATION.json` and `SCOPE_TASK_DRAFT.json` against the source
FinRank records, then decide whether the proposed task-matched collection is
scientifically identifiable.

## 7. Evidence And Accounting

Official arXiv source packages:

| Work | arXiv | Read scope | Source archive SHA-256 |
|---|---|---|---|
| ACE | 2510.04618 | design, results/ablation, limitations | `BDE13621A2ECBA5B97D8C916FF6AEF4AF1AA40983958A007638349CA2EDACD48` |
| MemRL | 2601.03192 | method, transfer/merge, limitations | `A4AAF25DC370B8CA3252D085D300C02F6A9AF55FE10296DEB6847B30E40CB41D` |
| A-MEM | 2502.12110 | method, ablation, limitations | `D112E92606A562A0369E2E8CDDADAD88AC8D448D66C24EE9B63E808C2C84E42B` |
| AWM | 2409.07429 | method, Mind2Web, offline/online appendix | `976E88E6BF9E3566A0FFF894C7D478E032E838D6E709276B04BEB4CCA2E892BE` |
| ExpeL | 2308.10144 | method, transfer, ablation, limitations | `05939C3F8692979DAF3D359223612295B008632C9B3E2E4DCBA6E28ECD5E4D7A` |
| Reflexion | 2303.11366 | loop/memory, ablation, limitations | `D70B771F527D912CE48DA430CCD697FB09AAEABBFBFDA404441943D398550304` |

FinRank input SHA-256:
`b763ef4d58706370bd32f828b94852d2aa19f5227cb603481dd230d8121360ac`.

Current new generation ledger remains zero. Public-source downloads total
approximately 18 MB, below the 200 MB bound. No paid research API, judge,
training or production-memory write occurred.
