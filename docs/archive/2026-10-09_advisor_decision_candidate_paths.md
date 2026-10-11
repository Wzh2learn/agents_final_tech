> SUPERSEDED_BY: [`../../side_handoff.md`](../../side_handoff.md) | Historical Advisor candidate paths; archived after the 2026-10-11 session handoff.

# Advisor-Gated Candidate Paths: Multi-leaf vs Second Dataflow

> **For agentic workers:** REQUIRED SUB-SKILL: use `executing-plans` only after explicit user/mentor approval. This document is a decision-gated plan. It is not an execution authorization.
>
> **Status:** `AWAITING_ADVISOR_DECISION / RECOMMENDATION_ONLY / DO_NOT_EXECUTE`

**Goal:** Prepare two mutually exclusive evidence paths without searching for a source, downloading data, running an adapter, launching an experiment, or invoking a model.

**Architecture:** Path M strengthens the existing Stage E measurement instrument by making more than one scored leaf responsive. Path D tests transfer to a second dataflow whose source, split, perturbation, observability, and harmfulness contracts are frozen before acquisition or execution.

**Tech Stack:** Existing frozen Stage E evidence contracts; GB10-only execution for any future authorized run; no training stack, no new data source, and no model call in this plan.

## Global Constraints

- Keep `COMPLETE_FOR_FORMAL_NEGATIVE_PATH_B`, `DATA_NO_GO / RQ2 NOT_IDENTIFIED`, and Stage E internal-only status unchanged.
- Do not alter frozen thresholds, split rules, claim boundaries, TAT-DQA boundaries, or existing harmfulness definitions.
- Do not search for or select a new source, download data, implement an adapter, run A0-A3, Phase 2, B5, or training.
- Preserve null/adverse outcomes and missing-evidence labels exactly.
- GB10 is the only permitted future runtime/validation plane; the five current GB10 dirty files remain untouched.

---

## Decision Gate

- [ ] **Step 1:** Advisor chooses exactly one path: `M` or `D`.
- [ ] **Step 2:** User freezes the corresponding question, claim namespace, success/null/failure rules, and authorization matrix.
- [ ] **Step 3:** Only after explicit GO, create the first task card for the selected path.
- [ ] **Step 4:** Keep the unselected path at `AWAITING_ADVISOR_DECISION`; do not merge the two paths.

---

## Path M: multi-leaf / multi-stage injection

> **Status:** `AWAITING_ADVISOR_DECISION / DO_NOT_EXECUTE`

### Scientific question

Can a controlled injection make more than one scored leaf respond, so that hierarchy and localization become measurable rather than confounded by a single responsive leaf?

### Minimal experiment

Use the existing frozen public tabular corpus and the existing six defect families: alias variation, mixed language, unit suffix, date variation, OCR-like character substitution, and prefix noise. Create a preregistered multi-stage injection matrix with at least two independently responsive scored leaves. Keep the current thresholds, seeds, matcher set, normalization set, matched-FPR procedure, and missing-evidence policy fixed. Do not add a new semantic family without a separately approved annotation contract.

### Leaves that must respond

- Required minimum: the existing responsive `field hit-rate` parsing leaf plus one additional parsing leaf selected before injection generation from the frozen parsing tree (`table regression`, `document status`, `document throughput`, or `reconciliation equations`).
- The second leaf must have an evidence artifact and a predeclared response predicate; it cannot be selected after observing results.
- QA-tree leaves do not count toward the minimum unless their evidence contract is independently valid for the injected input.

### Defect family contract

- Reuse the six frozen families and balance family counts before execution.
- Multi-stage combinations must state the stage order, affected leaves, expected evidence surface, and whether the family is intended to test visibility, detection, or localization.
- OCR-like cases remain a visibility-blind control unless a new, separately approved protocol changes that role.

### Preregistration requirements

- Freeze leaf set, injection counts, stage order, family balance, thresholds, seeds, matchers, normalization, FPR matching, and stopping rules.
- Define `visible`, `detected`, `localized`, `harmful`, `equivalent`, and `unresolved` separately.
- Freeze the analysis table before the first run and retain all null/adverse cases.
- State explicitly that this experiment does not change the frozen Stage E claim boundary.

### Success / null / failure interpretation

- **Success:** at matched FPR, at least two leaves respond and the preregistered hierarchy analysis shows a reproducible decomposition or localization increment under the frozen criterion. Scope remains the current corpus and synthetic perturbations.
- **Null:** more than one leaf responds, but flat/hierarchical discriminability and localization do not improve. This strengthens the current evidence ceiling.
- **Failure:** the second leaf cannot be made responsive, or the injection violates the evidence contract. This is an observability/protocol failure, not evidence that hierarchy is ineffective.

### Authorization required

User/mentor approval for the multi-leaf question, injection design, evidence contract, GB10 execution window, and any new annotation/review work. No source download or model/training authorization is implied.

---

## Path D: changed-pipeline second dataflow

> **Status:** `AWAITING_ADVISOR_DECISION / DO_NOT_EXECUTE`

### Source structural requirements

- Exact source/task-definition annex with repository, revision, paths, file hashes, owner, licence scope, and permitted uses.
- Real table layer with source, target, process/checkpoint evidence, action/target semantics, and independent correctness evidence on the same sample UID.
- At least 40 conservative independent origin clusters under the frozen grouping rule.
- A changed pipeline structure that is not merely a renamed copy of the current flow.

### Independence and UID requirements

- UID-disjoint proposal/train/dev/gate/sealed roles; no shared lineage root across roles.
- Non-empty split layers and independently reviewable cluster/UID manifests.
- No post-hoc origin grouping or split repair after looking at results.

### Controlled perturbation requirements

- Freeze defect ontology, severity, stage placement, family balance, and clean/injected pairing before execution.
- Keep the current visibility/detection thresholds and matched-FPR comparison unchanged.
- Do not generate action/target labels from hidden ground truth; record missing stages as `unmeasurable`.

### Observability and harmfulness contract

- Freeze separate definitions for checkpoint visibility, protocol detection, and harmfulness.
- Use the advisor-selected harmfulness construct only as a primary reporting definition; if parallel constructs are selected, report them separately.
- Require independent visibility receipts and a scorer that is independent of the current semantic-judge endpoint.
- Bind all source, adapter, split, annotation, and review artifacts before interpreting results.

### Success / partial transfer / failure interpretation

- **Success:** the second dataflow satisfies all source/UID/observability contracts and reproduces the preregistered visibility profile without changing frozen criteria. This supports a bounded external-validity claim.
- **Partial transfer:** only structural or subset clauses pass. Report clause-level boundary evidence; do not claim cross-domain validity.
- **Failure:** the source fails independence, bridge, licence, or observability requirements. Record a data/task-definition boundary; do not call it E-D-R falsification.

### Authorization required

Separate approvals for source annex, data acquisition, licence, adapter/task definition, independent scorer, reviewer receipts, split/power/MDE evidence, and the GB10 execution window. No source search or download is authorized by this plan.

---

## Handoff

Both paths stop here. The first post-decision task card must be a **decision-freeze and authorization gate** card, not an experiment or source-search card.
