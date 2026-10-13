# PDF Layout Audit v1

> date: 2026-10-11 | artifact: paper/overleaf_bundle/saner_rene_manuscript_v1.pdf | result: PASS

## Compile
- Method actually used: portable tectonic 0.15.0 (single-file, user-space; downloaded to D:\AIRcommend\_tools\tectonic, outside the repo). No system TeX install; GB10 untouched.
- Command: `tectonic saner_rene_manuscript_v1.tex` (runs bibtex internally; 6 passes settled the .bbl).
- Result: compiled PDF, 285 KB, exit code 0.

## Structural QA
- Total pages: 8.
- Body: Sections I-VII + VIII Data Availability span pages 1-7; Appendix A on page 8. Content (main + appendix) is 8 pages, within the RENE 10-page limit (figures and appendices included).
- References: 21 numbered entries, roughly one page (lower half of page 7 + top of page 8); within the 2-page references allowance.
- Figures: Figure 1 (vector PDF re-render), Figure 2 (matrix), Figure 3 (ablation bars) all render; captions complete and claim-safe.
- Tables: the visibility-by-detection table and Table 1 (protocol detection) both render inside the column after `p{}`-column and tabcolsep fixes.
- Equations: the aggregation recursion S(n) and the threshold set Gamma render correctly.
- Citations: all 21 resolve; zero "??" and zero LaTeX citation warnings.
- Overfull \hbox: 0.
- Underfull \hbox: 63 (cosmetic; reduced from 196 by switching table p-columns to ragged-right (>{\raggedright\arraybackslash}); the remainder is one artifact/path paragraph with long break-resistant tokens plus normal short final lines). No visible defect.
- Two-column balance, section headings, and float placement: acceptable; no broken headings or runaway floats observed.

## Visual QA (page images rendered at 2.2x and inspected)
- Page 1: title, "Anonymous Submission", abstract, Figure 1, 2-column layout.
- Pages 2-4: 3-layer related work with resolved numeric citations; both equations; visibility table.
- Pages 5-6: Figure 2 and Figure 3 with complete captions; Table 1.
- Pages 7-8: Discussion, Conclusion, Data Availability, References [1]-[21], Appendix A.

## Anonymity / metadata
- Source anonymization: PASS (0 identity strings).
- PDF metadata: Title set to the paper title; Author empty; no author/host/user/path leakage. Creator "LaTeX with hyperref", Producer "xdvipdfmx (0.1)" are generic tool names.
- No CJK and no mojibake in the rendered PDF.

## Verdict
PDF_LAYOUT_AUDIT = PASS. The compiled PDF exists, page count verified, references resolved, figures visually verified, no overfull boxes, metadata anonymous.
## Language pass (2026-10-11)
- Normalised spelling to US English: localisation -> localization (3), organisation -> organization (2).
- Replaced 5 spaced-hyphen dashes with grammatical punctuation (comma/colon/clause); kept the one inside the math expression (H_orig - H_inj).
- Rebuilt the .tex, the bundle and the PDF afterwards: still 8 pages, 0 overfull, 63 underfull, metadata anonymous, no forbidden claim introduced. All reported numbers are unchanged (spot-checked: 96/118, 0/13, 2,382, 0.375, 1.0, 0.3333, 0.6667, 0.1667, 89/89, 112/118, 75/95, 20/95).

## Addendum 2026-10-13 (residual-pass rebuild)
> scope: A1-A7 residual completion (A2/A7 wording, Figure 3 definition + caption, Section 1 scoping, Section 4.3, Section 5.1 attribution) + LF re-pin; no number change.
- Rebuild: `python paper/_md2tex.py` -> `python paper/_to_bundle_tex.py` -> `tectonic saner_rene_manuscript_v1.tex` (portable tectonic 0.15.0); exit 0.
- Result: 9 pages, 0 overfull; underfull warnings remain the cosmetic class (long break-resistant tokens / short final lines) seen in the earlier build. PDF 289 KiB.
- References 21/21 resolved; `??` = 0. Metadata Author empty; Title set; no CJK; identity-token scan clean.
- Machine audit: `PRE_SUBMISSION_AUDIT = PASS`; `WIDE_EVIDENCE_CHECK = PASS` after the scope-lock re-pin (docs + mirror manifests byte-identical; pin = GB10 raw-byte LF hash `4c951e618ed6f5ffa8af84aeb6e55eb75b3a90b88cc36d660714f78aaa35f213`).
- Figure 3 caption now reads "...equals the uniform-class macro-F1 baseline (0.3333); the majority-class macro-F1 reference (0.1667) is plotted." (the word "also" was deleted on 2026-10-13 as the Loop C v3 prescribed fix; final rebuild: 9 pages, 0 overfull, audit PASS.) Panels A/B (macro-F1 / top-1) unchanged from the frozen figure.

## Language pass (2026-10-13, final English edit)
- 14 expression-only edits applied to the manuscript: abstract dash clause -> colon/comma; "The same shift" -> "The same pattern"; "refine ... into" -> "decompose ... into"; "from its abstract" -> "based on its abstract"; "hypothesises" -> "hypothesizes" (US); the 'Pruned parsing-root drop' label italicized; "so that checkpoint" -> "so that the checkpoint"; score ranges "0-10"/"0-5" -> en dash; Figure 2 caption "x" -> multiplication sign; "has observed FPR zero" -> "has an observed FPR of zero"; "range contracts" -> "range shrinks"; "reported as failed" -> "this failure is reported"; the 5.5 heading restructured; plus two source blank-line fixes.
- Abstract resynced verbatim into the registration package and the submission handoff.
- Rebuild: md2tex -> bundle -> tectonic, exit 0; 9 pages; 0 overfull; `PRE_SUBMISSION_AUDIT = PASS`; `WIDE_EVIDENCE_CHECK = PASS`; `??` = 0; no number, claim, or evidence-hash change.

## Presentation fix (2026-10-13d)
- Removed the two inline sha256 strings from Section 4.1 (machine-residue reading; the hashes remain in the frozen evidence record / artifact manifest). Replacement text: "content hash in the artifact manifest" (x2).
- Rebuild: md2tex -> bundle -> tectonic; exit 0; 9 pages; 0 overfull; `PRE_SUBMISSION_AUDIT = PASS`; `WIDE_EVIDENCE_CHECK = PASS`; PDF text contains no "sha256". No number, claim, or evidence-hash change.
