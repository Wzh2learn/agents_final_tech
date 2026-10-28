# Quality check — 2026-10-28

## Build and visual check
- Rendered the Pandoc-generated DOCX on GB10 with LibreOffice 24.2 in a dedicated profile; output `paper_e_review_revision.pdf`, SHA-256 `6b8c368e34fea5780eb0bffdacc963ec5bfb44bf8f9b3b4912713da4352ebabb`. Eleven US-letter single-column pages. `javaldx` warning occurred; PDF was generated and inspected.
- Converted all 11 pages to PNG and visually inspected the complete contact sheet. No evident clipping; tables 1 and 2 break across pages 2–3 and 4–5 respectively, and page 11 contains only the final reference. This is a readable internal draft, not an ACM/IEEE conference-formatted PDF; table layout and pagination need final work.
- All numerical manuscript checks against historical documents are *text-to-text*, not independent reruns or a review of all raw data.

## Tables: evidence lineage
- Table 1 is a qualitative interpretation of the staged case, the FinRank tie comparison and the retrospective BEIR comparison in the original short draft. It is not evidence of any real individual changing a decision. Sources: `conference_short_20261028/conference_short.md`, sections II–V.
- Table 2: `paper_e_ijcnn2027_submission.md` section 5.2 has seed-42 table detection flat 75/95 and hierarchical 20/95, injection detection flat 85/118 and hierarchical 13/118; immediately following text gives a fitted ~0.375 slope in the single-responsive-leaf construction. Section 5.5 and former short draft give full/direct stage top-1 1.000 and non-direct 0.333. These denominators, evaluation objects and operating points must remain distinct. The registered deployment threshold remains unresolved.
- Table 3: original short draft section V reports 2/10 and 1/10 Holm-adjusted sign-flip comparisons, 36.5% list / 25.7% membership changes and 0.00005 approximate nDCG shift; it separately reports duplicate/degradation controls passed by the exact-tie rule and audit. Neither table nor provenance validation replaces a reviewer rerunning the experiments.

## Citation mapping
- Compared bibliographic section against the input short draft byte-for-byte in content: nine references preserved. Automated body/reference enumeration, expanding [1]–[3], gives references 1–9 in body and bibliography, no missing or orphan entries.
- Public primary records checked 2026-10-28: [1]–[4] https://arxiv.org/abs/2412.13989 , https://arxiv.org/abs/2608.00794 , https://arxiv.org/abs/2511.04703 , https://arxiv.org/abs/2608.07400 ; [5] https://arxiv.org/abs/2104.08663 ; [6] https://openai.com/codex/ ; [7] https://aclanthology.org/2021.acl-long.254/ ; [8] https://aclanthology.org/2021.emnlp-main.300/ ; [9] https://huggingface.co/BAAI/bge-small-en-v1.5 . These checks establish access/title and basic author mapping, not that every literature-based claim has been checked against the full texts. Original arXiv [5] title spells “Heterogenous” whereas preserved draft spells “Heterogeneous”; author must verify preferred official publication metadata before final bibliography. AI disclosure covers Codex only as a reference; all actual tools, authors and venue-required disclosures still need author confirmation.
- Model card lists BGE MIT; this does not establish permission to redistribute underlying BEIR datasets.

## New exploration
`EXPLORATORY_SIX_SYSTEM_WRITING_NOTE.md` records a suggested paragraph from parallel agent results. It is not incorporated into the PDF or presented as independently verified. Requires independent statistical review before use.

## v2, 2026-10-28
The v2 Markdown adds a separate, explicitly post-hoc six-system graded nDCG@10 paragraph and table; it does not replace the original five-system/ten-pair section. Key numbers were checked programmatically against `mc_recheck.json`: 200,000 draws per pair, SciFact p=0.006410 / Holm p=0.066000; NFCorpus p=0.001295 / Holm p=0.015540. Source `mc_recheck.json` SHA-256 recorded by experiment owner: 7038261675710b7b60b4d2b8d00450efefbd1d50839194bdfb4294e61aa54b5c. This is a transcription check, not independent statistical validation. Assumptions, within-dataset family, lack of correction across metric conditions and datasets, absence of dense-score tie evidence and absence of real-user decision are stated in the v2 text.

The v2 DOCX was built with Pandoc and rendered to PDF on GB10 LibreOffice 24.2; the resulting single-column Letter PDF has 11 pages, SHA-256 497b00564b6de4430f0ae991f396b83e0c8336500a728988157c03197ef403ed. 11-page contact sheet inspected with no apparent clipped content; tables 1 and 2 still cross pages, and this is not a submission-template PDF. Four DOCX tables and numeric text anchors passed programmatic checks. Full independent statistical review and final citation/format review remain outstanding.
