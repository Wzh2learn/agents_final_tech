# NIST / TEVV Background Evidence v1

Status: source audit and bounded governance interpretation only.

Evidence labels: `FACT`, `INFERENCE`, `VALUE`, `UNVERIFIED`.

## 1. Source record before conclusions

The machine-readable pre-conclusion register is [`source_audit_v1.json`](../../research/stage_e_stage_d_20261009/source_audit_v1.json). It records identity, URL, revision, licence status, schema/source evidence, and exact blockers.

| Source | Official URL | Revision | Licence status | Exact blocker |
|---|---|---|---|---|
| NIST AI RMF 1.0 | [landing page](https://www.nist.gov/itl/ai-risk-management-framework), [NIST.AI.100-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf), [DOI](https://doi.org/10.6028/NIST.AI.100-1) | January 2023; released 2023-01-26; official page says 1.0 is being revised | NIST technical-series statement; third-party-authored NIST works may be copyrighted | Future revision identity unavailable; framework is not a Stage E metric specification |
| NIST AI RMF Core | [official Core page](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/) | Page metadata updated 2026-06-18; represents AI RMF 1.0 and says a revision is in progress | NIST web/technical-series terms as applicable | No checkpoint-visibility or family-macro formula |
| NIST AI RMF Playbook | [official Playbook](https://airc.nist.gov/airmf-resources/playbook/) | Page metadata updated 2026-06-18; will be updated after AI RMF revision | NIST web terms; cited third-party references retain their terms | Suggestions are voluntary and provide no acceptance threshold for Stage E |
| NIST AI Resource Center / TEVV | [AIRC](https://airc.nist.gov/) | Observed 2026-10-09; no page semantic version | NIST web information unless marked copyrighted | Landing page does not define checkpoint visibility |
| NIST AI 600-1 GenAI Profile | [official PDF](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) | July 2024; official AI RMF page says released 2024-07-26 | NIST technical-series statement; third-party-authored works may be copyrighted | Profile does not prescribe this project's metrics |

`FACT`: no inspected source supplies a project-specific visibility formula, OCR threshold, matched-FPR acceptance rule, or Stage E claim boundary.

## 2. SOURCE CLAIM

`FACT`: AI RMF 1.0 organizes risk-management outcomes and actions through GOVERN, MAP, MEASURE, and MANAGE.

`FACT`: the official Core describes objective, repeatable, scalable TEVV processes with metrics, methods, and methodologies; measurement outcomes should be documented and metric efficacy verified.

`FACT`: MEASURE 1.2 addresses appropriateness and effectiveness of AI metrics; MEASURE 2.1 documents TEVV test sets, metrics, and tools; MEASURE 2.13 addresses effectiveness of employed TEVV metrics and processes.

`FACT`: the AI RMF Playbook supplies suggested actions aligned to Core subcategories. Its page says the Playbook is neither a checklist nor a sequence to follow in its entirety and that suggestions are voluntary.

`FACT`: AIRC states that it provides documents, tools, and guidance to assist testing, evaluation, verification, and validation of AI.

`FACT`: NIST AI 600-1 is a generative-AI profile extending AI RMF concepts; MEASURE 4.2 concerns documenting trustworthiness measurements across deployment contexts and the lifecycle.

`FACT`: the official AI RMF and Playbook pages state that AI RMF 1.0 is being revised and that the Playbook will follow that revision.

## 3. OUR INTERPRETATION

`INFERENCE`: Stage E's separation of checkpoint visibility, protocol detection, and operational harmfulness is consistent with TEVV's demand to document distinct measurement objects rather than collapse them into one score.

`INFERENCE`: reporting micro and macro rates, family profiles, denominator-specific results, operating-point sensitivity, and cluster-aware uncertainty is a bounded operationalization of metric documentation and effectiveness review.

`INFERENCE`: preserving `UNVERIFIED` for semantic harmfulness-conditional blindness follows the same evidence discipline as documenting unavailable or difficult-to-assess measurements.

`INFERENCE`: Playbook language supports treating governance actions as guidance rather than deriving a mandatory compliance certification from this research task.

## 4. OUR MOTIVATION

`VALUE`: the project needs an external governance vocabulary to explain why frozen values, source hashes, negative results, and unsupported claims remain visible to readers.

`VALUE`: TEVV framing motivates independent sensitivity checks, explicit operating points, and separation of evaluator visibility from downstream protocol outcomes.

`VALUE`: the project does not adopt NIST wording to inflate claim strength or imply conformity assessment.

## 5. What NIST does not establish

| Claim | Status |
|---|---|
| `96/118`, `0/13`, `112/118`, `85/118`, `13/118`, and `[0,0]` are correct | `VALUE`: project-derived from frozen artifacts, not NIST-validated |
| `visible_frozen` is the correct general definition of visibility | `UNVERIFIED`: no external general definition inspected |
| `gamma=0.2` is an official or universally appropriate threshold | `UNVERIFIED` |
| OCR `0/13` proves a population-wide rate | `UNVERIFIED`; clustered corpus observation only |
| The project conforms to NIST AI RMF or has an official NIST certification | `UNVERIFIED` and not claimed |
| AI RMF 1.0 will retain the same wording after revision | `UNVERIFIED` |

## 6. Bounded conclusion

`INFERENCE`: NIST/TEVV evidence supports the governance motivation for disciplined, documented measurement; it does not validate the Stage E statistics or authorize a protocol upgrade.

`FACT`: this review performed no model, judge, training, GPU, database, production-service, credential, Phase 2, Stage R, or E-D-R action.
