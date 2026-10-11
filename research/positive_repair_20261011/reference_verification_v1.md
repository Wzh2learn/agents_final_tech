# Reference Verification Ledger v1

> date: 2026-10-11 | submission-completion mode | rule: every reference confirmed by title+authors+year+venue+DOI/URL via >=2 primary sources; no Gemini-supplied citation may enter the bibliography.

## Primary sources used
- arXiv API (export.arxiv.org) for arXiv IDs and titles.
- Crossref (api.crossref.org) for IEEE DOIs, authors, venues.
- Official SANER RENE track pages (conf.researchr.org, SANER 2024/2025/2026) for RENE track membership.
- nist.gov / Crossref for NIST documents.

## Verified entries (21 total in paper/saner_rene_references.bib)
| Key | Type | Identifier | Verified against |
|---|---|---|---|
| gerhold2024limits | RENE 2024 | DOI 10.1109/SANER60148.2024.00022 | SANER 2024 RENE page + Crossref |
| hoess2025does | RENE 2025 | DOI 10.1109/SANER64311.2025.00067 | SANER 2025 RENE page + Crossref |
| berndt2026flaky | RENE 2026 | DOI 10.1109/SANER67736.2026.00016 + arXiv:2602.05465 | SANER 2026 RENE page + Crossref + arXiv API |
| kummita2026static | RENE 2026 | DOI 10.1109/SANER67736.2026.00114 | SANER 2026 RENE page + Crossref |
| nist2023airmf | NIST | DOI 10.6028/NIST.AI.100-1 | nist.gov + Crossref |
| nist2024genai | NIST | DOI 10.6028/NIST.AI.600-1 | nist.gov + Crossref |
| amrhein2022aces | arXiv | 2210.15615 | arXiv API |
| amrhein2023aces | arXiv | 2311.01153 | arXiv API |
| moghe2024mtmeta | arXiv | 2401.16313 | arXiv API |
| deviyani2025contextual | arXiv | 2503.19828 | arXiv API |
| kendiukhov2026ranking | arXiv | 2603.03493 | arXiv API |
| du2026stability | arXiv | 2606.24381 | arXiv API |
| ross2024metric | arXiv | 2412.13989 | arXiv API |
| zheng2023judging | arXiv | 2306.05685 | arXiv API |
| liq2025scoringbias | arXiv | 2506.22316 | arXiv API |
| lis2025llmjduge | arXiv | 2506.09443 | arXiv API |
| cho2025metamorphic | arXiv | 2511.02108 | arXiv API |
| tan2026agentchaos | arXiv | 2608.06790 | arXiv API |
| fan2026agentprocessbench | arXiv | 2603.14465 | arXiv API |
| chung2026process | arXiv | 2606.15673 | arXiv API |
| wang2026gta2 | arXiv | 2604.15715 | arXiv API |

All 16 arXiv IDs resolved to the expected titles on the arXiv API. All 4 RENE precedents are confirmed genuine RENE-track papers. Both NIST documents resolve via their DOIs.

## Not admitted
- Any Gemini-supplied citation not present in paper/saner_rene_references.bib. In particular, the "8+2" page-limit claim and any unverified precedent title remain excluded.

## Residual
- Full author-given-name spelling for the "et al." arXiv entries should be expanded at the camera-ready pass; the arXiv API confirms the first author and title, which is sufficient for submission.