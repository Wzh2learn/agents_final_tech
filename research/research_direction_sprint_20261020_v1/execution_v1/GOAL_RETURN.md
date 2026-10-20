# GOAL_RETURN

Goal: `PAPER_E_EXTERNAL_AUDIT_AND_EXPERIENCE_SCOPE_V1`

Status: `COMPLETED_WITH_CONDITIONAL_RULINGS`

## Independent Rulings

**Paper E: 修订后继续。**

Retain Paper E as a bounded two-case measurement-audit paper. The original
staged evaluator results remain valid for their frozen contract. The FinRank
case adds a real implementation-level result: tie policy moves absolute
pairwise scores but preserves the hard-versus-random ordering, while source
identity limitations and a residual numerical reproduction gap narrow what can
be claimed. The corrected source-identity branch is post-hoc and must remain
labelled that way. Continue revision, but do not claim a universal audit method.

**新经验候选: 仅有开发信号、证据未定。**

The selected question is whether explicit experience scope reduces wrong-scope
transfer in FinRank evidence selection. It is not a string-equality task and
has offline decision headroom. However, all 24 draft tasks still require human
semantic adjudication, the actor-visible applicability contract is only now
being made explicit, and the release exposes only three conservative source
components. Generation is not authorized. This is a qualified development
design, not an independent-validation result.

## Required Answers

### 1. 本轮改变了哪项研究判断，证据在哪里？

Two judgments changed.

First, Paper E is no longer waiting for a generic “second case.” FinRank provides
a real score-contract and identity audit with preregistered questions and
thresholds plus a transparent post-hoc identity correction. It supports a
two-case paper, but only with bounded transfer and reproducibility language.
Evidence: `PAPER_E_EXTERNAL_AUDIT.md`, `paper_e_audit/PRE_REGISTRATION_PROVENANCE.md`
and `paper_e_audit/outputs/APPLICATION_RESULTS.json`.

Second, the broad experience-scope hypothesis is narrowed to a concrete FinRank
applicability task, but it cannot enter generation. Offline probes show real
headroom and a harmful wrong-scope action; they also show that references and
visible applicability semantics are not yet closed.
Evidence: `EXPERIENCE_SCOPE_STUDY.md` and
`experience_scope/SCOPE_TASK_QUALIFICATION.json`.

### 2. Paper E 最强的一句话贡献是什么？最接近工作仍构成什么威胁？

> A reproducible measurement audit can separate score-contract sensitivity from
> decision stability in a real evidence-ranking benchmark, while exposing a
> residual reproduction gap without overstating its cause or the generality of
> the review procedure.

The largest threat remains Ross et al.'s general metric-validity audit and the
generic construct-validity frameworks of Caban and Bean et al. FinRank itself
also correctly discloses its curated-pool, overlap and first-occurrence
limitations. Paper E is distinct only when it stays with staged observation
boundaries, score-structure identifiability and measurement-object binding.

### 3. 已经完成哪份可审阅写作？

`PAPER_E_REVISION_DRAFT.md` is a complete revised manuscript, not an outline.
It includes a new title and abstract, updated introduction and related work,
the external audit method and setup, a FinRank results subsection, integrated
discussion and limitations, revised conclusion, data availability and updated
references. Frozen manuscript evidence and numbers remain unchanged.

### 4. 新经验问题排除了什么替代解释，还剩什么？

Excluded:

- pure string equality or a fully solved task: lexical top-k exactly recovered
  only 72/181 gold sets;
- a complete simple visible year/form rule: it matched at least one gold in 98
  records, selected only hard evidence in 19, and abstained in 64;
- an already available task-matched FinRank history pool: none exists;
- reuse of the stopped role-binding panel: it remains stopped.

Remaining alternatives:

- a stronger scope rule, ordinary solved examples or fixed retrieval may still
  explain every benefit;
- the current references are development labels, not settled semantic gold;
- three source components and unresolved report IDs cannot support
  independent generalization;
- the actor/tool contract has not yet been tested with generation.

### 5. 实际消耗多少请求/token/时间，哪些工作未运行？

- New generation requests: **0/192**.
- New accounting tokens: **0/2,000,000**.
- Public source material: **55,703,416 bytes / 53.12 MB**, below 200 MB.
- Paid research API, judge, training and production-memory writes: **0**.
- Coordination: three subagent lines (Paper E audit, experience design,
  independent review), recorded separately from scientific generation.
- Not run: B0, task-matched history collection, H-U/H-S/R/K comparison, neural
  FinRank reproduction, training and any role-binding-panel request.

### 6. 下一步唯一最值得做的事情、所需成本和停止条件是什么？

The next action is a human semantic adjudication of the 24 FinRank development
tasks: for each task, decide whether the visible candidate set has exactly one
supporting evidence interpretation and whether entity/period/form/unit scope is
unambiguous. At the same sitting, freeze the `plan -> evidence_lookup -> consume`
tool contract and positive/negative/ambiguous fixtures. This costs one qualified
financial-evidence reviewer session and zero model requests.

Stop the experience candidate if more than a small predeclared minority remains
ambiguous, if the task collapses to metadata lookup, or if hidden reference
information is required. If the gate closes, submit the frozen design for one
increment review and only then run the small development comparison. A result
explained by R or K, or limited to formatting/tool validity, stops the
experience-mechanism claim.

### 7. 哪些普通事项已自主解决？

- Fixed the official FinRank revision, dataset/code/result hashes and license.
- Preserved the preregistration and both v1/v2 applications with an explicit
  provenance correction.
- Recomputed tie, source-identity, metadata-loss and reproduction results.
- Completed the full Paper E revision draft.
- Compared three experience candidates and selected one with evidence.
- Built and tested the deterministic FinRank scope-task qualification.
- Added actor-visible scope fields, ambiguity flags and a tool contract draft.
- Obtained one independent scientific review and applied its blocking
  corrections without altering raw results.

## Evidence Index

- `PAPER_E_EXTERNAL_AUDIT.md`
- `PAPER_E_REVISION_DRAFT.md`
- `EXPERIENCE_SCOPE_STUDY.md`
- `INDEPENDENT_REVIEW.md`
- `RESEARCH_GENERATION_LEDGER.json`
- `paper_e_audit/PRE_REGISTRATION_PROVENANCE.md`
- `paper_e_audit/outputs/APPLICATION_RESULTS.json`
- `experience_scope/SCOPE_TASK_QUALIFICATION.json`

## Remaining Owner Decision

Provide or decline a qualified human semantic adjudication session for the 24
FinRank tasks. Without it, the experience line remains a development design and
the scientifically accurate route is to continue Paper E revision and author
review only.
