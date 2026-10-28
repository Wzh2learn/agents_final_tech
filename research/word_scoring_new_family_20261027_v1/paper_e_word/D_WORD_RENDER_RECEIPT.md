# D Word Conversion And Page-Render Receipt

Date: 2026-10-27, Asia/Shanghai

## Tools

- Windows Pandoc: 3.2.1 at `D:/pandocLatex2word/pandoc.exe`.
- GB10 LibreOffice: 24.2.7.2 at `/usr/bin/soffice`.
- GB10 PDF renderer: `/usr/bin/pdftoppm`, PNG at 120 DPI.
- Every LibreOffice render used a fresh `UserInstallation` profile.

## Deterministic Source Fixes

The original extracted source remains unchanged at `paper_e_word.md`.
`paper_e_word_fixed.md` is the conversion derivative and applies only
structural fixes:

- split author, affiliation and corresponding-author placeholders;
- add Markdown block boundaries around headings and pipe tables;
- convert BibTeX-key brackets to stable numeric citations;
- convert LaTeX itemize blocks to editable bullet lists;
- replace two fragile display equations with explicit editable mathematical
  text.

`polish_docx.py` then fixes Word/LibreOffice interoperability:

- use a real `Table Grid` style with visible light-gray borders;
- set explicit column widths and table-cell margins;
- replace the missing `Compact` cell style with `Normal`;
- keep table text in a readable Times New Roman size.

## Artifact Identity

| Artifact | SHA256 |
|---|---|
| `paper_e_word.md` | `2aeba0ddc6a068a12064db9372b3be03d00de2335bd0d387506eff3d3223bba9` |
| `paper_e_word_fixed.md` | `ac05bc8c578d87cff41ddec71d2990af1375b54cd71cbd76ae0a7453809a9fc1` |
| `fix_docx_source.py` | `bd9548f6cb02960e0247a0a773824e119ea687e5846c345eb6af392f7320beb8` |
| `polish_docx.py` | `731a0b614993bbd204e9e5b7acd1a12c7e6af4bbee7e69f1be5e92f2a3466998` |
| `paper_e.docx` | `227309b88ab9778bbd1ce9c181ed468773410d3afb7ec3fd6eeaaea50ad9d5e0` |
| `rendered_final/paper_e.pdf` | `231ae6e20a0b7362ce51bc3698e2947d4995a853c2077c36d065190b443a316f` |

The DOCX contains four editable Word tables with shapes 6x3, 3x3, 4x4 and
7x5. The PDF contains 14 pages.

## Visual Acceptance

All 14 latest page PNGs were inspected at full resolution. Accepted after the
final formula edit:

- author/affiliation/corresponding fields are separate readable lines;
- the title, structured abstract and five keywords are intact;
- all four tables render with repeated headers where they cross pages;
- all three figures are sharp, aligned and captioned;
- numeric citations and all 24 references are readable;
- formulas and mathematical notation are editable text without raw TeX;
- Data Availability and Declarations are present;
- no clipped text, overlap, missing glyphs, blank table cells, raw citation
  keys, truncated references or malformed final page was observed.

This is internal Word-route rendering acceptance, not formal submission,
publisher acceptance or school recognition. Author identity, patent/artifact
permission, submission and payment remain `TBD_OWNER`.
