# Paper E Word Conversion Package

Status: `READY_FOR_D_PANDOC_3_2_1`.

`paper_e_word.md` is the sole manuscript body for this package. It is generated
from the tracked complete two-case source
`research/adaptive_mechanism_20261027_v1/paper_e_formal_build/paper_e_sncs.tex`.
No P1, P2 or new-family result is added. Numeric bracket citations and all 24
formatted entries are already embedded, so the normal conversion command does
not run citeproc and does not create a second bibliography.

`references.bib` and `numeric-bracket.csl` preserve the bibliographic source and
numeric-bracket style assets for audit and regeneration. `reference_style.docx`
sets 10 pt Times New Roman for Normal text where Word/Pandoc applies the
reference style. Author, affiliation, corresponding author, funding, patent,
AI-disclosure approval and artifact/submission fields remain `TBD_OWNER`.

## D conversion

Run `CONVERSION_COMMAND.txt` with local Pandoc 3.2.1. Produce exactly one
manuscript DOCX named `paper_e.docx`; transfer that file to GB10 for LibreOffice
rendering. This package does not claim that conversion has run here.

## Expected visual checks after D conversion

1. Title, structured abstract, five keywords and all section headings are present.
2. Exactly three figures render without stretching or missing-image boxes.
3. All four tables remain editable and do not overflow page margins.
4. Equations remain legible; inline mathematical notation is not converted to body text errors.
5. Numeric citations `[1]` through `[24]` and the complete reference list are present exactly once.
6. `TBD_OWNER` fields remain visible; no raw BibTeX field or ICAART author-kit boilerplate appears.
7. Normal body text is 10 pt Times New Roman where the reference DOCX supports it.
8. The conclusion retains the two-case boundary and publication-status caveats.

These are expected checks for D, not completed visual acceptance in A.
