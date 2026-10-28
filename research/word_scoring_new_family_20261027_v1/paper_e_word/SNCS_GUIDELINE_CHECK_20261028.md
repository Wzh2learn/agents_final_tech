# SN Computer Science — submission-guideline fit check

Date: 2026-10-28. Read-only check of the journal's public author guidelines and
three published articles. No submission, no account action, no contact with the
editorial office.

Sources consulted:

- `https://link.springer.com/journal/42979/submission-guidelines` (fetched 2026-10-28)
- Published articles used as format exemplars (all SN Computer Science, Vol. 7, 2026):
  - `10.1007/s42979-026-05360-3` — Optimizing semantic blocking in entity resolution (Original Research)
  - `10.1007/s42979-026-05404-8` — Deep hybrid CNN–LSTM intrusion detection (Original Research)
  - `10.1007/s42979-026-05359-w` — Multi-scale convolutional pyramid network (Original Research)

## Requirement-by-requirement fit

| Guideline requirement | Manuscript state after this revision | Verdict |
|---|---|---|
| Structured abstract, 150–250 words, four parts **Purpose / Methods / Results / Conclusion** | Exactly those four bold labels; 191 words of prose, 195 with the labels, 208 including the Keywords line | **FITS** |
| Keywords, 4–6 | 5 | **FITS** |
| Text citations as numbers in square brackets | `[1] … [24]`, ascending, no group out of order | **FITS** |
| Reference list numbered consecutively, DOI where available | 24 numbered entries, every one carrying an arXiv id or DOI | **FITS** |
| Reference author form `Family Initials, Family Initials.` (as in the published exemplars) | All 21 author-bearing entries converted from full given names with ampersands, e.g. `Christophides V, Efthymiou V, …`; corporate authors (NIST ×2, OpenAI) left as-is | **FITS** (was not) |
| At most three heading levels | Two (`##`, `###`) | **FITS** |
| "Statements and Declarations" section required, before the reference list | Renamed and restructured; now contains Author details, Funding, Competing interests, Ethics approval, Consent to participate/publish, Data and code availability, Authors' contributions, plus patent/licence/channel fields | **FITS** (was not) |
| Generative-AI use described in Methods | New §4.7 "Analysis tooling and AI assistance", with the detailed disclosure retained in the Acknowledgments | **FITS** (was not) |
| Word submission, .docx, 10 pt Times Roman body, editable tables (not spreadsheets), italics for emphasis, no field-function page numbers | `.docx`, Times New Roman, four native Word tables, italics preserved, no field codes | **FITS** |
| Figures: vector preferred (EPS); raster minima are **per image type** — line art 1200 dpi, halftone 300 dpi, combination 600 dpi; artwork must not contain its own title or caption text | Rebuilt from source: titles/subtitles/footnotes removed, art cropped to content, rasterised at 1200 dpi (Figure 1, line art) and 600 dpi (Figures 2–3, combination). The vector sources are kept for submission | **FITS** (was not) |
| Single-blind review | No anonymisation required | **FITS** |
| Author changes are not accepted after acceptance | All author fields are `TBD_OWNER`; must be finalised **before** submission | **OWNER DECISION** |

## Figures — corrected assessment (supersedes the first version of this note)

The first version of this section applied a single "≥300 dpi" threshold to all
three figures and reported them as "120-DPI PNGs". Both statements were wrong,
in opposite directions:

- the guideline's raster minima are **per image type**: line art 1200 dpi,
  halftone 300 dpi, combination 600 dpi. Applying the halftone number to a
  vector-style diagram is an over-generalisation;
- 120 dpi is the **page-render** resolution used for the per-page PNGs, not the
  artwork's own resolution. The old artwork was 246–277 dpi at its placed
  width, which is a different (and smaller) failure than the one stated.

What was actually wrong, and what has been done:

| Defect | Measure | Action |
|---|---|---|
| In-artwork titles, subtitles and caption/footnote lines in all three images | seen on pages 02/08/10 of the C-reviewed render | removed at the source: the rebuild drops text with `font-size="36"` (title) or `fill="#59677a"` (muted subtitle/footnote colour), and nothing else. Axes, legends, nodes, panel labels and value annotations are retained |
| Resolution below the type-specific minimum | old art 277/277/246 dpi at 6.5 in, no `pHYs` chunk | re-exported from the SVG source: SVG → vector PDF (LibreOffice) → raster at the required dpi. Figure 1 is line art at 1200 dpi (7813 px); Figures 2–3 are combination art at 600 dpi (3907 px). No DPI metadata was edited and no old PNG was upscaled |
| Canvas mostly white, so the drawing sat small inside its box | titles and footnotes occupied the top and bottom thirds | canvas cropped to the content bounding box with 16 units of padding |

**Still below the recommendation, and reported as such:** on-page type at the
6.5 in placed width is 5.7 pt for Figure 1, 5.7–7.3 pt for Figure 2 and
7.0–8.2 pt for Figure 3, against a recommended 8–12 pt. Figure 1's stage
headers were the worst offenders (4.6 pt) and were raised to the 21-unit body
size, which fits their 310-unit boxes; the remaining shortfall cannot be fixed
without re-laying out the diagrams, because type size on the page is fixed by
the ratio of font size to canvas width. That is a design change, not a
re-export, and it is not attempted here.

Font family is DejaVu Sans, a sans-serif; the guideline prefers Helvetica or
Arial. Left as is for the same reason.

## Route judgement

The subscription route remains a **conditional recommendation**, unchanged in
direction. Two things now support it more strongly than at the last assessment:
the paper already matches the journal's structured-abstract and numeric-citation
requirements exactly, and the venue publishes instrumentation/evaluation studies
of this length. Nothing found here supports or implies a probability of
acceptance, and no timeline is promised.
