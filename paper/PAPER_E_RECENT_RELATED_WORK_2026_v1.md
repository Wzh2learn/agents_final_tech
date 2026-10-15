# Paper E — Recent Related Work (2025–2026) v1

> status: `REFERENCE_CANDIDATES_NOT_YET_INSERTED` | date: 2026-10-15 | author: Loop D
> purpose: answer "相关工作是近期的吗？要更近期的" and give a verified insertion pool.
> verification: titles/authors/dates/abstracts pulled first-party from the arXiv Atom API on
> 2026-10-15 (primary source = arXiv abstract page). Venue/DOI is NOT asserted unless stated.
> This file changes no manuscript, no claim, no frozen number. Nothing here is inserted yet.

## 1. Direct answer: are the three advisor-cited works recent?

| Advisor-cited work | Year | Recency verdict |
|---|---|---|
| Offutt, "test oracle" | classic (pre-2010s body) | **NOT recent by design** — a classic anchor for the oracle problem, not a 2026 neighbour |
| ACES (Amrhein et al.) | 2022 (+2023, +2024 journal) | **dated** — challenge-set meta-evaluation is now a crowded, newer space |
| "Auditing the Audit" (arXiv 2607.02586) | 2026 | **recent** — this one holds up |

So the mix is one classic + one dated + one recent. The manuscript's own Section 2 already
cites several 2024–2026 works, so the paper is not stale overall; but the *specific* trio is
not a good "recent wall". Below is a verified 2025–2026 pool that is closer to the upgraded thesis.

## 2. Verified 2026 pool, grouped by what it supports

### Cluster A — measurement / evaluation validity (the upgraded thesis anchor)

| id | date | title | one-line relevance |
|---|---|---|---|
| 2609.25173 | 2026-09-21 | Attack Success Rate Is Not a Number: On Measurement Validity in Agentic AI Security Evaluation | ASR is a family of metrics under unspecified design axes; cross-paper comparison unsupported. Closest analogue to "a count is not an identified quantity". |
| 2609.13642 | 2026-09-12 | When Compliance Data Masquerades as Evaluation: Measurement Validity for Deployed AI Systems | Data useful for monitoring is not automatically a valid benchmark; proposes an explicit evaluation contract. |
| 2609.33153 | 2026-09-27 | What Does a Skill Actually Do? Estimands and Evaluation Validity for Tool and Skill Use in LLM Agents | Reported gains refer to different estimands; paired-run designs do not identify an invocation effect. Direct support for "define the measurement object first". |
| 2511.04703 | 2025-11-03 | Measuring what Matters: Construct Validity in LLM Benchmarks | 29-expert review of 445 benchmarks; construct-validity failure patterns + recommendations. |
| 2602.15532 | 2026-02-17 | Quantifying construct validity in large language model evaluations | Formal models that separate capabilities from benchmark results; measurement-error aware. |
| 2608.29420 | 2026-08-29 | One Capability or Many? Structural and Predictive Tests of Benchmark Validity… | Structural and predictive validity tests can disagree; pre-registered thresholds. |
| 2603.15121 | 2026-03-16 | Establishing Construct Validity in LLM Capability Benchmarks Requires Nomological Networks | Normative framing (Cronbach–Meehl / Messick / Borsboom) for what a construct-validity claim must include. |

### Cluster B — silent failures / process-level evaluation / observation contracts

| id | date | title | one-line relevance |
|---|---|---|---|
| 2609.32691 | 2026-09-26 | Silent Failures in Agentic Security Evaluation: A Validated Harness… | Audits a benchmark harness, finds four defect classes each yielding "a plausible, publishable, and incorrect number". The single best neighbour for our audit posture. |
| 2610.14115 | 2026-10-09 | The Silent Failures in Agentic Data Science | Downstream-performance-only evaluation masks methodological failures (leakage, bad validation). |
| 2610.06163 | 2026-10-05 | Where Did the Repair First Go Wrong? Localizing the Origins of Silent Failures… | Silent failures give no observable failure signal; needs trace-based, not observed-failure-based attribution. |
| 2605.17281 | 2026-05-17 | ContractBench: Can LLM Agents Preserve Observation Contracts? | Introduces "observation contracts"; deterministic, SHA-256-verified, programmatic evaluation. |
| 2609.02246 | 2026-09-02 | LLM-as-a-Judge Is Not an Oracle: Why Self-Improving Agents Need Deterministic Guardrails | Enumerates eleven ways an LLM-judge evaluation signal failed; judge demoted from oracle to advisor. |
| 2609.12191 | 2026-09-10 | GAUGE: When Not to Trust LLM-as-a-Judge in User-Simulated Evaluation… | Separates ranking validity from construct validity; satisfaction carries ~no information about success. |

### Cluster C — document-intelligence auditing / table & document QA evaluation (domain anchor)

| id | date | title | one-line relevance |
|---|---|---|---|
| 2605.19309 | 2026-05-19 | How Do Document Parsers Break? Auditing Structural Vulnerability in Document Intelligence | Output-level audit of document layout-analysis pipelines; "Footprint Bias": area-centric robustness mis-tracks structural loss. Closest domain neighbour to our evaluation-instrument audit. |
| 2609.07629 | 2026-09-07 | Open Tabular Insight Extraction: Where Do We Stand, and Where Should We Go? | Systematic review across table QA / text-to-SQL / data-analysis; benchmarks "largely unfit" for open settings. Supports our table-centric evaluation-validity framing. |
| 2608.15064 | 2026-08-15 | LongDocBench: Benchmarking TOC Hierarchy and Contextual Relationship Recovery in Long Documents | Hierarchy-recovery benchmark; usable as a "hierarchy alone is insufficient" neighbour. |
| 2609.03395 | 2026-09-03 | TabScope: Question-Adaptive Scope Selection for Table Question Answering | Recent table-QA method work; only needed if we want an in-domain method baseline neighbour. |

## 3. Recommended insertion map (proposal only)

- §2.1 (measurement/construct validity): add 2609.25173, 2609.13642, 2609.33153, 2511.04703.
- §2.2 (testing / oracles / diagnosability): add 2609.32691, 2605.17281, 2610.06163.
- new §2.x (document-intelligence evaluation): add 2605.19309, 2609.07629.
- Keep NIST AI 100-1 / AI 600-1 as the normative motivation; do not let the new cites enlarge any claim.

## 4. Caveats and discipline

- All rows are arXiv preprints unless a venue is separately verified. Do not assert a venue/DOI
  from this file alone; if a paper is later found published (e.g. at SANER RENE 2027), update to
  the proceedings entry via the normal citation-verification path.
- Two of these (2609.32691, 2605.19309) are directly about auditing an evaluation artifact. They
  *support the posture* of Paper E; they do not transfer any of Paper E's numbers.
- Adding this literature must not change any frozen number, split, threshold, or claim. It is a
  positioning and defence change only.
