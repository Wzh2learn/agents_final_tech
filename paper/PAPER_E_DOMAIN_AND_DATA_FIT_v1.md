# Paper E — Domain & Data Fit Verdict v1

> status: `READ_ONLY_ASSESSMENT` | date: 2026-10-15 | author: Loop D
> question: "我们选成多阶段文档智能管线这个领域，我们的数据集合理支撑吗？场景 ok 吗？"
> scope: this file changes no manuscript, no claim, no frozen number. It is an honest fit verdict.

## 1. What we actually have (facts, unchanged)

| Asset | Fact |
|---|---|
| Base corpus | frozen `drift-v0` table set derived from **public TAT-QA** tables; 95 tables carry injections |
| Perturbations | fully synthetic injection map, deterministic, seed 42, ratio 0.3; 118 entries in 6 families (alias 47 / mixed_lang 20 / date 17 / prefix_noise 16 / ocr_similar 13 / unit_suffix 5) |
| Audited surface | a two-root checkpoint forest (parsing tree + QA tree), 12 scored leaves; visibility audit exercises mapping/regression leaves under a frozen drop rule |
| Matcher | production greedy header matcher (+ greedy-normalized / Hungarian variants for the audit) |
| Second flow | FinQA program-perturbation corpus, 89 rows / 30 clusters, downstream result fields NOT recomputed |
| Multi-leaf study | contract-derived M/R/N on the same corpus; 72 clusters / 216 injections; constructed explicitly for the study |

## 2. What the label "multi-stage document-intelligence pipeline" implies vs what we have

A natural multi-stage document-intelligence pipeline would ingest an image/PDF, run layout
detection and OCR, segment tables, map fields to a schema, reconcile arithmetic, and answer
queries. What we have is the *evaluation instrument* of such a pipeline, instantiated on
**tabular financial documents**, with **synthetic** header perturbations.

- The **staging is real** and is the paper's object: ingestion -> table structure -> field
  mapping -> arithmetic reconciliation, plus a QA tree. The visibility audit only exercises the
  parsing-tree mapping/regression leaves; the QA arm is reported separately.
- The **corpus is real** (TAT-QA is a well-known public financial-table QA dataset) but **narrow**:
  one public financial-table domain, one second financial-reasoning dataflow (FinQA).
- The **perturbations are synthetic and thin**: header drift only. The "OCR-like" family *mimics*
  OCR token noise on headers; it is not OCR on scanned images, and it is not a natural document
  degradation distribution. No natural-failure distribution is measured.
- The **pipeline under audit is bespoke**: it is our constructed evaluator, not a third-party
  production document-AI system. This is exactly the advisor's "bespoke-system / weak external
  validity" attack surface.

## 3. Verdict

**Scenario: OK, but only under a precise name.** The defensible framing is *"a controlled
measurement-validity audit of the evaluation instrument for staged tabular document intelligence"*,
not "a study of document intelligence systems". The three constructs (visibility / detection /
harmfulness) and the observation-surface audit are genuinely about staged pipelines, and the
2026 literature (2605.19309 "How Do Document Parsers Break?"; 2609.07629 "Open Tabular Insight
Extraction") shows this is a live, recognizable area. That strengthens the positioning.

**Data support: enough for a case study / RENE negative result, not for a distributional or
universal claim.** Two public financial-table corpora + synthetic perturbations support: (i) a
family-resolved observation-boundary map, (ii) a protocol-identifiability audit, (iii) a
construction-bounded instrumentation ablation, (iv) a failed-transfer autopsy. They do **not**
support any claim about "document intelligence" as a field, nor any population blindness rate.

**The generalization that is actually available** is a change of the unit of analysis: from
"our evaluator has limits" to **"a staged evaluation surface can fail to observe the failures it
is meant to assess"**, with the document-intelligence pipeline as one instantiation. That is the
"升级后的 Paper E" the advisor endorsed. It is more defensible precisely because it claims less
about the domain and more about the measurement object.

## 4. Concrete implications

1. Keep the domain, tighten the noun: use "staged tabular document-intelligence evaluation" and
   state the perturbation construct mechanically. Do not imply OCR/vision.
2. Name the two-corpus limit explicitly; cite TAT-QA and FinQA as first-class references (currently
   they appear only as prose + artifact hashes — a reviewer will flag the missing citations).
3. Add the recent 2026 domain and validity literature (see `PAPER_E_RECENT_RELATED_WORK_2026_v1.md`)
   to show the paper sits in a live conversation.
4. External validity is only repairable by a **genuinely independent verification environment**
   (advisor Layer 3) — e.g. a second, actually-executable pipeline with its own task gold. That is
   where the biggest scientific upside is; it is also where the cost and risk are highest.
5. Do not let the domain label grow the claim. The safe sentence stays: the evidence comes from one
   staged tabular evaluator plus one failed second dataflow.
