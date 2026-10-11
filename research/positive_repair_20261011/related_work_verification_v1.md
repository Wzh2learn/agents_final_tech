# Related-Work Precedent Verification v1 (corrected)

> date: 2026-10-11 | Loop D | corrected pass: supersedes an earlier partial pass that marked the 2024 precedent UNVERIFIED due to a wrong URL slug and that reported wrong presenter names. NO manuscript citation added (fail-closed per owner directive).
> rule: a RENE precedent may enter related work ONLY after it is confirmed on an official SANER program/proceedings source AND a bibliographic record (Crossref DOI). Gemini-provided precedents are NOT authority.

## Method
- Verified track membership on the official conf.researchr.org SANER RENE track pages, then confirmed each record against Crossref DOI metadata (>=2 primary sources per item).
- Tooling notes: web_search returned empty this session; DBLP and OpenAlex returned HTTP 429; conf.researchr.org and api.crossref.org were reachable and used.
- Correction note: the earlier pass used `.../saner-2024-reproducibility-studies-and-negative-results-rene-track` (404). The working URL is `.../saner-2024-reproducibility-studies-and-negative-results--rene--track-` (double dash around rene and a trailing dash). The 2024 precedent IS present.

## A. RENE precedent verification (all four VERIFIED)

| # | Owner short form | Verdict | Exact title | Authors | Venue / year | DOI |
|---|---|---|---|---|---|---|
| 1 | Does the Tool Matter? | VERIFIED | Does the Tool Matter? Exploring Some Causes of Threats to Validity in Mining Software Repositories | Nicole Hoess, Carlos Paradis, Rick Kazman, Wolfgang Mauerer | SANER 2025, RENE track | 10.1109/SANER64311.2025.00067 |
| 2 | Can We Classify Flaky Tests Using Only Test Code? | VERIFIED | Can We Classify Flaky Tests Using Only Test Code? An LLM-Based Empirical Study | Alexander Berndt, Vekil Bekmyradov, Rainer Gemulla, Marcus Kessel, Thomas Bach, Sebastian Baltes | SANER 2026, RENE track | 10.1109/SANER67736.2026.00016 |
| 3 | Static Analysis Traces can help Dynamic Symbolic Execution: a Replication Study | VERIFIED | Static Analysis Traces can Help Dynamic Symbolic Execution: a Replication Study | Sriteja Kummita, Fabian Schiebel, Eric Bodden, Miao Miao, Shiyi Wei | SANER 2026, RENE track | 10.1109/SANER67736.2026.00114 |
| 4 | The Limits of the Identifiable... | VERIFIED | The Limits of the Identifiable: Challenges in Python Version Identification with Deep Learning | Marcus Gerhold, Lola Solovyeva, Vadim Zaytsev | SANER 2024, RENE track | 10.1109/SANER60148.2024.00022 |

All four are genuine SANER RENE papers. The owner short forms were truncated titles; use the full titles above. (An earlier pass reported "Luca Traini" and "Manel Abdellatif" as presenters; those attributions are NOT author lists and are not used. The Crossref author lists above are authoritative.)

## B. NIST citations

| Document | Verdict | Title | Year | DOI / URL |
|---|---|---|---|---|
| NIST AI 100-1 | VERIFIED | Artificial Intelligence Risk Management Framework (AI RMF 1.0) | 2023 | 10.6028/NIST.AI.100-1 |
| NIST AI 600-1 | VERIFIED | Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile | 2024 | 10.6028/NIST.AI.600-1 |
| NIST AI 200-2 IPD | VERIFIED as draft background only | Test, Evaluation, Validation and Verification (TEVV) - initial public draft | 2026 draft | 10.6028/NIST.AI.200-2.ipd |

Recommendation: cite AI 100-1 (MEASURE 1.2, 2.13) and AI 600-1 (MS-2.13-001 construct validity) as MOTIVATION anchors only. Keep the forbidded claim ("NIST proposes evaluator blind spots") out, and keep "NIST motivates evaluating metric/TEVV effectiveness; it does not certify our metrics". Exact passages are mapped in docs/research/nist_measurement_validity_ledger_v2.md. The manuscript already carries the AI 100-1 motivation citation in Section 1 and the References list.

## C. Venue URL
- SANER 2027 RENE CFP resolves (HTTP 200): https://conf.researchr.org/track/saner-2027/saner-2027-reproducibility-studies-and-negative-results-rene-track

## Safe to use now
- The four RENE precedents (full titles + DOIs above).
- NIST AI 100-1 and NIST AI 600-1 (motivation only).
- SANER 2027 RENE CFP URL.

## Must NOT use
- Any Gemini-supplied precedent title or page-limit claim not in this ledger (the "8+2" page limit is refuted by the official RENE page).
- NIST AI 200-2 as a stable method authority (still a draft; public comment period closed 2026-10-06).
- The owner's abbreviated precedent titles as-is (use the full titles above).

## Remaining step (before any insertion)
Run the normal citation pass and add the verified entries to paper/references_v0.md before wording any precedent into Related Work. No precedent is inserted in this pass.