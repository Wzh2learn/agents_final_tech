---
id: TASK-20261008-STAGEE-INQUIRY-A1
risk: low
window: none
premises:
  - id: P1
    claim: "GB10 repository HEAD is e97340387888290e69fbfff122ab163de971b37e."
    falsify: "test \"$(git rev-parse HEAD)\" = e97340387888290e69fbfff122ab163de971b37e"
  - id: P2
    claim: "The Stage E source hash is abab44657e17936badf371a606198886ccd333a4c1489600c8922f78a6c57e80."
    falsify: "sha256sum paper/teacher_review_draft_v1.md"
  - id: P3
    claim: "This task is metadata, analysis, and design only; no dataset body, ground truth, experimental model endpoint, Phase 2, training, submission, or external release is authorized."
    falsify: "rg -n 'download|ground_truth|8004|8006|8008|Phase 2|training|submit|arXiv' docs/experiments/2026-10-08_stage_e_inquiry_loop_a_task_card.md"
  - id: P4
    claim: "Public scholarly and repository metadata can be checked without credentials."
    falsify: "curl -fsS --max-time 20 'https://api.crossref.org/works/10.18653%2Fv1%2F2021.emnlp-main.300' >/tmp/stage_e_meta_probe.json"
acceptance:
  - "python3 -m json.tool docs/datasets/2026-10-08_stage_e_public_source_metadata_audit_v1.json >/tmp/stage_e_metadata_json_check.txt"
  - "rg -n '^## (1|2|3|4|5|6|7|8|9|10|11|12)\\.' docs/research/2026-10-08_stage_e_inquiry_and_experiment_design_v1.md"
  - "rg -n '96/118|0/13|112/118|85/118|13/118|\\[0,0\\]|51/58/37|8 conservative|DATA_NO_GO|RQ2 NOT_IDENTIFIED' docs/research/2026-10-08_stage_e_inquiry_and_experiment_design_v1.md"
  - "git diff --check"
  - "python3 scripts/docs_lint.py --json /tmp/stage_e_inquiry_docs_lint.json"
rollback: "No production or frozen artifact is changed. If a generated report is inconsistent, delete only the newly generated report/JSON and leave all pre-existing files untouched."
redlines:
  - "Do not download dataset archives or data bodies."
  - "Do not read ground_truth.json, target labels, hidden splits, private samples, model weights, or credential files."
  - "Do not call or probe :5050, :8004, :8006, :8008, :4096, judge endpoints, canaries, or any model API."
  - "Do not run A0-A3, Phase 2, B5, Q3/B0-B4 reruns, training, or formal experiments."
  - "Do not modify frozen tests, frozen hashes, schema baselines, docs/33*, docs/34*, TAT-DQA boundaries, or existing evidence artifacts."
  - "Do not submit, upload to arXiv, publish code, or perform external release."
  - "Do not use git add -A, git commit --amend, --no-verify, force push, or rewrite history."
  - "Do not turn exploratory, PILOT_ONLY, planned, or metadata-only evidence into confirmatory evidence."
skills:
  - "inquiry-methods"
  - "paper-lookup"
  - "paper-review-check"
  - "research-driven-design"
---

# Task Card: Stage E Inquiry, Source Audit, and Experiment Design

## 1. Goal

Produce one evidence-disciplined Stage E research package that explains the current measurement-validity paper, audits public source metadata without downloading data, and specifies the next experiments as executable but unauthorized designs.

Done means all of the following exist on GB10:

1. `docs/datasets/2026-10-08_stage_e_public_source_metadata_audit_v1.json`
2. `docs/research/2026-10-08_stage_e_inquiry_and_experiment_design_v1.md`
3. A short status entry in `memory/STATE.md`, open decisions in `memory/THREADS.md`, and one append-only dispatch receipt in `logs/graph/dispatch_log.md`.

The report must follow the user's requested order:

1. 小论文内容双层详解
2. 小论文研究对象双层详解
3. 方法和结果双层详解
4. 现在可做 / 需授权 / 需新数据
5. 经典工作与开源数据集候选表
6. 其他研究思路
7. 跨领域借解方案
8. 最优先的实验路线
9. 一份可以直接写进 task card 的实验设计
10. 仍需用户拍板的决策项
11. `FACT / INFERENCE / VALUE / UNVERIFIED` 证据分级
12. 明确列出没有执行的事项

## 1.5 Skill Loading

Load no more than these four skills, if present in the GB10 skill installation:

- `inquiry-methods`
- `paper-lookup`
- `paper-review-check`
- `research-driven-design`

If a skill is unavailable, state that explicitly and follow the contract in this card. Do not install or sync skills.

## 1.6 Research and collaboration protocol

The task is split into two durable stages:

- **Stage A, evidence acquisition and fact check:** query metadata, write the JSON audit and a compact claim fact-check appendix first. Every query, URL, access date, HTTP status, and `UNVERIFIED` gap must be persisted.
- **Stage B, synthesis and report:** read only the Stage A artifacts plus the listed repository authorities to write the full report. If the session is interrupted, redo only Stage B from the saved artifacts.

Use the following inquiry modes sequentially, and label each output block with its mode:

1. `dual-explanation` for sections 1-3.
2. `steelman-decision` and `minimal-experiment` for the priority and experiment decisions.
3. `domain-research` and `fact-check` for the literature and dataset table.
4. `expert-panel`, `first-principles`, and `cross-domain-borrowing` for alternative paths and translated protocols.

Do not imitate or attribute positions to real experts. Keep `FACT`, `INFERENCE`, `VALUE`, and `UNVERIFIED` separate. External metadata is metadata, not a raw experimental artifact.

## 2. Premises

| # | Premise | One-minute falsification | Required result |
|---|---|---|---|
| P1 | GB10 checkout is at the current local/origin/GB10 head | `git -C /home/testuser/wzh/projects/agents_final_tech rev-parse HEAD` | exact `e97340387888290e69fbfff122ab163de971b37e` |
| P2 | Stage E source is the canonical teacher-review draft | `sha256sum paper/teacher_review_draft_v1.md` | `abab44657e17936badf371a606198886ccd333a4c1489600c8922f78a6c57e80` |
| P3 | The task is metadata/design-only | inspect this card and the command log | zero downloads, zero model endpoints, zero training/Phase 2 |
| P4 | Public metadata APIs are reachable without secrets | one Crossref or arXiv request | HTTP success or explicit `UNVERIFIED` fallback |
| P5 | Existing dirty runtime files are not overwritten | `git status --short` before and after | only allowed report/JSON/memory/dispatch paths change |

If a premise fails, stop the affected branch and report `BLOCKED`; do not improvise a new source, revision, label ontology, or authorization.

## 3. Evidence boundary and source order

Read and cite the actual files, not conversation summaries:

1. `AGENTS.md`
2. `memory/CORE.md`
3. `memory/STATE.md`
4. `memory/THREADS.md` current top entries and open decisions
5. `docs/research/README.md`
6. `side_handoff.md`
7. `paper/teacher_review_draft_v1.md`
8. `paper/claim_manifest_v1.json`
9. `paper/research_asset_map_v2.md`
10. `paper/teacher_review_readiness_v2.md`
11. `docs/experiments/SUMMARY_q3_label_and_baselines.md`
12. `docs/experiments/SUMMARY_stage_d_readiness_and_model_sync.md`

For source metadata, use paper APIs and repository metadata only. Preferred order:

- Crossref DOI lookup
- arXiv Atom metadata
- Semantic Scholar or OpenAlex when reachable
- official GitHub/GitLab repository metadata and README/LICENSE
- Zenodo record metadata
- Hugging Face dataset metadata

Do not use an API key, print credentials, or fetch a dataset body. A README or LICENSE is metadata documentation; an archive, CSV/JSON data body, ground truth, or model shard is not.

## 4. Fixed scientific baseline

Treat these as current facts unless an actual artifact contradicts them:

- Identity: evaluation-protocol measurement-validity / meta-evaluation paper, not a detector paper and not a complete Evaluate-Distill-Evolve paper.
- Title: `Visibility Is Not Detection: Auditing Blind Spots in Long-Horizon Document AI Evaluation`.
- Corpus: 95 tables and 118 synthetic header-drift injections across 6 perturbation families.
- Visibility: `96/118`; OCR-like visibility `0/13` across 5 thresholds.
- Raw protocol detection: end-to-end `112/118`, flat `85/118`, hierarchical `13/118`.
- Matched-FPR calibration: flat and hierarchical protocol difference interval `[0,0]`.
- Only one scored leaf changes with the injected input in the current construction.
- C1 construct separation: visibility / detection / harmfulness.
- C2 evidence instrument: hierarchical checkpoint evidence plus per-family visibility profiles.
- C3 protocol audit: thresholds, matcher, seed, normalization, matched-FPR and weight-search controls.
- Hierarchy is an evidence instrument, not an algorithmic superiority claim.
- `[0,0]` is a degenerate-case explanatory diagnostic, not a general theorem.
- PSO is an informative null.
- Stage R is mechanism/boundary evidence only; Stage D is `DATA_NO_GO / RQ2 NOT_IDENTIFIED`.
- Q3 is exploratory `map_to=51 / skip=58 / hold=37`.
- Valentine has 551 complete tasks but only 8 conservative independent origin components and no native trajectory/checkpoint bridge.
- Q3, B0-B4, Track B, PILOT_ONLY, and planned arms cannot be written as Stage D/RQ2/Stage R/RQ4/training/submission results.

Do not modify any frozen criterion, frozen hash, TAT-DQA boundary, or existing evidence number.

## 5. Required analysis

### Sections 1-3: dual explanation

For each of sections 1-3 provide a beginner layer and an expert layer.

The beginner layer must use ordinary language and one concrete example. The expert layer must define the measurement object, observation surface, decision predicate, denominator, and scope limit.

Explain at minimum:

- Why final-answer correctness is insufficient to establish reliability.
- The exact distinction between checkpoint visibility, protocol detection, and equivalence-dependent harmfulness.
- What the parsing tree and QA tree do.
- Leaf score, local normalized sibling weights, threshold, hinge leaves, and missing evidence.
- Why only one input-responsive leaf limits localization.
- Why the raw hierarchy gap becomes a threshold/operating-point artifact after matched-FPR calibration.
- The meaning of every number `95 / 118 / 96/118 / 0/13 / 112/118 / 85/118 / 13/118 / [0,0]`.
- What is a result, an interpretation, a limitation, and future work.
- The three C1/C2/C3 contributions.
- A term map, likely misunderstandings, and exactly 3 understanding checks.

### Section 4: action classes

Create three tables with the same fields:

- prerequisite
- required artifact
- risk
- question answered
- stop condition

Class A is allowed now: read-only curation, metadata-only source screening, licence/provenance/native bridge audit, claim-evidence reconciliation, protocol/split/power/stop-condition design, static audit of existing artifacts.

Class B needs new experiment authorization: multi-leaf responsiveness, second dataflow adapter, independent scorer, harmfulness definition comparison, and any Q3/B0-B4/Stage D extension.

Class C needs new data or new licence: new benchmark download, more pair clusters, correctness joins, new action/target labels, or student training.

### Section 5: source and dataset audit

At minimum audit these rows and do not treat a paper as proof that a dataset is usable:

1. FinQA
2. TAT-QA
3. TabFact
4. WikiTableQuestions
5. PubTables-1M
6. FeTaQA
7. Valentine
8. schema matching benchmark family, including Magellan/DeepMatcher or the exact public benchmark actually verified
9. table fact verification benchmark family, including InfoTabS or the exact public benchmark actually verified
10. financial document/table QA family, including MultiHiertt and HiTab/ConvFinQA where verified

For every row answer all ten fields:

1. exact paper and dataset name
2. DOI and official repository / Zenodo / Hugging Face / GitHub entry
3. licence and whether the licence is for code, paper, or data
4. scale and task structure
5. table layer presence
6. checkpoint, process trace, action/target, and correctness bridge
7. independent lineage / origin clusters
8. support for visibility / detection / harmfulness constructs
9. whether it can only support external validity rather than Stage D
10. exact annex required before download

If only paper metadata is verified, write `UNVERIFIED` for dataset licence, revision, lineage, or bridge. Record query URLs, access date `2026-10-08`, response status, and fallback source in the JSON audit. Never infer a licence from a repository code licence.

### Sections 6-8: alternatives and cross-domain transfer

Use at least these perspectives:

- measurement science / psychometrics
- software reliability, mutation testing, canary and rollback
- clinical endpoint separation and blinding
- financial risk out-of-time validation
- aviation flight-recorder/intent separation
- software observability and shadow deployment

For each distant domain state the structural analogy, transferable mechanism, failure condition, and one concrete JinRongAgents protocol translation. Distinguish:

- experiments that can strengthen current Stage E
- experiments that only serve future Stage D/RQ2
- high-risk experiments that could change the research direction

A negative result is not a license to fabricate a positive result. A future path is not a current result.

### Section 9: executable experiment design

Include a complete design table and a paste-ready task-card block for the highest-priority experiment. It must specify:

1. research question
2. hypotheses and preregistered predictions
3. independent unit and cluster
4. split and UID/origin isolation
5. metrics
6. harmful-map risk limit
7. baselines
8. stop conditions
9. data, licence, checkpoint, and gold-isolation requirements
10. cost, time, and resources
11. what can run first and what must wait
12. exploratory versus confirmatory status

Priority order is fixed:

1. metadata-only dataset/source annex audit
2. multi-leaf synthetic experiment
3. independent scorer reproduction
4. second dataflow feasibility
5. harmfulness definition comparison
6. Stage D necessity re-evaluation
7. only after all gates pass, training

For Stage D-related designs, retain the approved risk limit `harmful-map risk upper <= 0.10` in primary, pair-invalid, and salted slices. For Stage E-only designs, do not borrow this as a Stage E claim; report harmfulness as parallel constructs unless the user explicitly chooses one.

Recommended design boundary for the first experiment: use the existing frozen corpus only as a new, explicitly named synthetic protocol namespace; never rewrite the frozen Stage E numbers. Use table-level clusters, pre-register the injection/leaf matrix and thresholds before reading results, calibrate operating points on clean tables, and report visibility-by-detection-by-harmfulness cells separately.

## 6. Required evidence labels

Use exactly:

- `FACT`: mechanically supported by a repository artifact or verified metadata record.
- `INFERENCE`: derived from facts; include the reasoning chain.
- `VALUE`: priority, preference, or normative judgment.
- `UNVERIFIED`: plausible but missing a source, licence, revision, bridge, or receipt.

For external checks also use `CONFIRMED`, `NEEDS_NARROWING`, `CONTESTED`, `INSUFFICIENT_EVIDENCE`, or `WRONG`.

## 7. Stop and exit conditions

Stop the affected branch immediately if any of the following occurs:

- a request would download a dataset body or read ground truth
- an endpoint, judge, canary, model, training process, Phase 2, or service would be touched
- a candidate requires an unapproved source, revision, file scope, schema, action ontology, or licence
- a metadata source is rate-limited after one retry; mark `UNVERIFIED`, do not guess
- a required number cannot be traced to an actual artifact
- the report would upgrade exploratory or planned evidence to confirmatory evidence
- patent, submission, arXiv, code release, or external distribution is proposed

Success exit: the two new files validate, the report has all 12 sections, every external claim has a source/date or `UNVERIFIED`, the design is explicitly `DESIGN_ONLY_NOT_AUTHORIZED`, and the dispatch receipt reports zero forbidden calls.

Failure exit: write `BLOCKED` with the missing source or gate and stop. Do not invent an annex or a result.

## 8. Verification evidence

Run only static/read-only checks after writing:

```bash
sha256sum paper/teacher_review_draft_v1.md
python3 -m json.tool docs/datasets/2026-10-08_stage_e_public_source_metadata_audit_v1.json >/tmp/stage_e_metadata_json_check.txt
rg -n '^## (1|2|3|4|5|6|7|8|9|10|11|12)\.' docs/research/2026-10-08_stage_e_inquiry_and_experiment_design_v1.md
rg -n '96/118|0/13|112/118|85/118|13/118|\[0,0\]|51/58/37|8 conservative|DATA_NO_GO|RQ2 NOT_IDENTIFIED' docs/research/2026-10-08_stage_e_inquiry_and_experiment_design_v1.md
git diff --check
python3 scripts/docs_lint.py --json /tmp/stage_e_inquiry_docs_lint.json
git status --short
```

Report every command, exit code, warning, and unverified surface. Do not run the full pytest suite because this is a zero-endpoint research/report task; record that it was not run rather than implying it passed.

## 9. Dispatch and accounting

- Execute on GB10 only.
- Use one Codex Loop A session in a dedicated tmux session.
- HTTP metadata budget: at most 80 requests total, one retry per 429/403, no API keys.
- No calls to model endpoints. The Codex Loop A invocation itself is the only authorized model execution.
- Preserve logs and hashes. Do not write secrets, raw data bodies, or sample text.
- Append one final entry to `logs/graph/dispatch_log.md` with task id, result, changed paths, verification commands, call counts, and commit as `NOT_AUTHORIZED`.
- Do not commit or push unless the user separately authorizes it. Existing uncommitted or untracked work must be preserved.
