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
| Figures: vector preferred (EPS), otherwise TIFF/halftone ≥300 dpi; artwork must not contain its own title or caption text | Current figures are 120-DPI PNGs, and the artwork **does** contain its own titles and footnotes | **DOES NOT FIT — production item** |
| Single-blind review | No anonymisation required | **FITS** |
| Author changes are not accepted after acceptance | All author fields are `TBD_OWNER`; must be finalised **before** submission | **OWNER DECISION** |

## The one substantive gap: figure artwork

All three figures are PNG rasters exported from SVG. The guideline asks for
vector EPS (or halftone ≥300 dpi) and asks that artwork carry no title or
caption text. Both conditions are currently violated: `fig1`, `fig2` and `fig3`
each contain a rendered title inside the image, and Figures 1 and 2 also carry
their own footnote line, which now duplicates the document caption.

This is **not fixed in this round**, because re-exporting the artwork means
re-running the figure generators and visually re-approving the plots — that is
new figure production, not manuscript revision, and it would change artifacts
already bound by `CONVERSION_MANIFEST.json` and audited by C. It is recorded
here as a concrete, bounded production task with an owner decision attached:

- keep PNG and accept the resolution requirement being met only at 120 dpi
  (Springer production will ask for better), or
- re-export SVG→EPS at submission time from the existing `.svg` sources in
  `figures/`, and drop the in-artwork titles and footnotes then.

The `.svg` sources exist next to the PNGs, so the second option is a mechanical
re-export, not a redraw.

## Route judgement

The subscription route remains a **conditional recommendation**, unchanged in
direction. Two things now support it more strongly than at the last assessment:
the paper already matches the journal's structured-abstract and numeric-citation
requirements exactly, and the venue publishes instrumentation/evaluation studies
of this length. Nothing found here supports or implies a probability of
acceptance, and no timeline is promised.
