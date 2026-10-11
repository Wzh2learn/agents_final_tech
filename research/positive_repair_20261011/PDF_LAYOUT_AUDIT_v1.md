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