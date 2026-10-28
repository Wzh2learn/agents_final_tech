# Paper E — revision notes (2026-10-28)

Scope: `PAPER_E_FIRST / INTERNAL_EXECUTION_PLAN_READY`. Loop D direct revision,
existing tooling only. No new scientific generation, no training, no judging, no
submission, no external contact, no payment.

Production source: **`paper_e_revision_v2.md`** — the only file edited by hand in
this round. `paper_e_revision_v2.docx` and `rendered_v2/paper_e_revision_v2.pdf`
are derived from it by `build_revision_v2.py` → Pandoc 3.2.1 →
`polish_docx_v2.py` → LibreOffice 24.2. `paper_e_word.md`,
`paper_e_word_fixed.md`, `references.bib` and the canonical TeX are unchanged
snapshots, hash-asserted at build time.

---

## 1. What C flagged, and what happened to it

| C ID | Defect | Disposition |
|---|---|---|
| B3 | "six-step" checklist lists five steps | **Closed.** The sixth step is missing from the Word extraction, not from the method. The canonical TeX `paper_e_sncs.tex` (`f1993042…`, the `canonical_source` already named in `CONVERSION_MANIFEST.json`) contains six `\item`s. Step 6 — *"report negative or stable results and the exact reproducibility envelope"* — is restored verbatim. No step was invented. |
| B4 | Table captions and the itemize block fused into body text | **Closed, and wider than reported.** See §2.1. |
| L1 | "208-word abstract" reproducible only under a different counter | **No manuscript change needed.** No word count is asserted anywhere in the text; the only 208 in the tree is a check inside `build_word_source.py`. Measured here: 191 words for the four-part prose, 195 with the part labels, 208 when the Keywords line is included. |
| L2 | Only 2 of 4 tables numbered | **Closed.** All four tables numbered by order of appearance: 1 interpretation corrections, 2 visibility-by-detection matrix, 3 protocol-level detection, 4 FinRank tie policy. The former "Table 2" is now Table 3 and its three in-text references were updated. Every table now has an in-text cross-reference. |
| L3 | Figures 1–2 carry their caption only as image alt text | **Closed.** Root cause was a missing blank line before the image paragraph, so Pandoc's `implicit_figures` never fired. All three figures now have real `Caption` paragraphs in the document body. |
| L4 | NIST rendered as "Standards, National Institute of & Technology"; `[13]` had a doubled period after "& et al." | **Closed.** Corporate author normalised to "National Institute of Standards and Technology" in `[10]` and `[11]`; `[13]` now reads "Bean, Andrew M., Kearns, Ryan O., Romanou, Alejandro, et al." The underlying `.bib` already carried the correct `{{National Institute…}}` corporate name; the damage came from the pre-rendered list. |
| L5 | Citation brackets out of ascending order (`[20,19]`, `[23,22]`) | **Closed — but it was a symptom of a much larger defect.** See §2.2. |
| L6 | `GENERATION_RECEIPT.json` reports `retries = 0` while `bounded_retries = 2` | **Not changed here.** It is a derived receipt of the D/T/M diagnostic, not a Paper E artifact. Rewriting it would silently mutate a frozen carrier that C audited. Recorded as a known receipt defect for the D/T/M decision card. |
| L7 | `generate_local.py:159` writes `:retry-2` under a `retry-1` path | **Not changed here**, same reason as L6. Recorded for the decision card. |

## 2. Defects found in this round that C did not report

All three were found by reading the canonical TeX against the Word extraction and
by rendering, not by re-running anything.

### 2.1 Two list items were silently deleted by the extractor, not just fused

`build_word_source.py:307-310` strips `\end{enumerate}` from the block **before**
applying a lookahead that requires `\end{enumerate}`. The regex therefore never
terminates its last item, and the final `\item` of every `enumerate` block is
dropped. Reproduced deterministically with the six-item checklist: the same
regex returns 5 items.

The canonical TeX has exactly two `enumerate` blocks, of 3 and 6 items:

- **Contribution 3 was missing entirely.** The Introduction listed two
  contributions while the abstract and conclusion both promised a checklist
  contribution. Restored verbatim from the canonical TeX.
- **Checklist step 6 was missing** (this is C's B3, now with a root cause).

The single `itemize` block (3 items) was not dropped but fused into the preceding
paragraph, because no blank line preceded it: Pandoc reads `- …` immediately
after a text line as a lazy continuation. That is C's B4. All three list blocks
are now real lists with a blank line before them.

### 2.2 Every in-text citation number pointed at the wrong reference

`fix_docx_source.py:16-19` builds the key→number map from the order of entries in
`references.bib`. The reference list at the end of the manuscript is in
first-appearance order. The two orders differ, so **all 14 in-text citation
groups were wrong**, not just the two out-of-order pairs C saw.

Example: the first sentence of §2.1 cites `[1,2,3,4]` (ACES, ACES-WMT,
MT-meta-evaluation, contextual meta-evaluation) but printed `[7,8,9,10]` (Ross,
Li, Li, NIST AI RMF). The RENE paragraph cites what should be `[20]–[23]` but
printed `[1]`–`[4]`.

The reference list itself was correct and already matched first-appearance
order. `build_revision_v2.py` now derives the numbering from the manuscript,
and **verifies** it by matching each numbered entry's title against the `.bib`
title of the key at that position (24/24). All 24 references are cited, every
group is ascending and duplicate-free.

### 2.3 List numbering and bullets did not render at all

Pandoc emits `w:pStyle w:val="Compact"` for tight-list paragraphs.
`reference_style.docx` does not define `Compact` (nor `FirstParagraph`,
`CaptionedFigure`, `ImageCaption`, `TableCaption`). LibreOffice 24.2 discards the
whole paragraph-properties block for an undefined style, which deleted the
`w:numPr` numbering and the bullet glyphs. Verified on the first render of this
round: the contributions printed as three unnumbered paragraphs.

`polish_docx_v2.py` removes the dangling style references, after which the
contributions render as `1./2./3.`, the checklist as `1.–6.`, and the
visibility list with bullets. 151 dangling references removed.

## 3. Editorial changes

Kept deliberately small; no new claim was introduced.

- **Project register → paper register.** "Paper E" removed everywhere (0
  remaining). `Within ICAART, Jouseau et al. …` → `In the ICAART proceedings, …`
  (the venue-targeting framing belonged to the abandoned ICAART route).
  "recorded in a separate autopsy" → "documented in a separate post-hoc
  analysis"; "the dated historical governance record" → "the project's dated
  analysis record"; "the evidence ledger" → "the evidence package".
- **Duplicated disclaimer merged.** §6.1 repeated the MA-CERD / adaptive
  revalidation exclusion in two consecutive sentences, once with the internal
  codename. Now one sentence, in paper voice.
- **Pre-registration vs post-hoc.** Unchanged in substance and still stated at
  every point it matters (abstract, §1, §3.5, §4.6, §5.7, §6.1). The revision
  only removed the internal-register wording around it.
- **Explicit exhibit references added.** Table 1, Table 2 and Table 4 were
  introduced without a number in the running text; each now has one. §4.2 asks
  for a one-to-one correspondence between numbering, caption and cross-reference.
- **Section numbering restored.** The Word conversion had dropped section
  numbers while the text still referenced "Section 3.1", "Section 4.5",
  "Section 5.6" and "Section 6". Headings are now numbered 1–7 with subsections
  2.1–6.3, and the lint checks that every `Section N.M` reference resolves.
- **Notation and precision.** `x` → `×`, `-` → `−`, `theta` → `θ`, `Gamma` → `Γ`,
  `p = 1/10001 = 1e-4` → `p = 1/10001 ≈ 0.0001` (1/10001 is 9.999e-5, so `=` was
  wrong by 0.01 %). **No experimental value was changed.** The FinRank table
  keeps independently rounded cells; the note explaining that 13.820514… rounds
  to 13.821 while the displayed cells subtract to 13.820 is preserved verbatim.

## 3a. Journal-fit adaptations (SN Computer Science)

Checked against the live author guidelines and three published Vol. 7 (2026)
articles; the full comparison is in `SNCS_GUIDELINE_CHECK_20261028.md`.

- **Reference author form converted.** The guideline's numeric style writes
  `Christophides V, Efthymiou V, Palpanas T …`. All 21 author-bearing entries
  were converted from full given names with ampersands to `Family Initials`;
  `[13]` keeps `et al.`; the three corporate authors (NIST ×2, OpenAI) are left
  whole. Titles, venues, years and identifiers were **not** touched.
- **Declarations section renamed and restructured.** The heading is now
  `Statements and Declarations`, and it carries the items the journal requires:
  author details, Funding, Competing interests, Ethics approval, Consent to
  participate/publish, Data and code availability, Authors' contributions, plus
  the patent / licence / channel fields. The guideline states that a missing
  statement section is returned as incomplete, so this was blocking.
- **AI use moved into the Methods.** New §4.7 "Analysis tooling and AI
  assistance" states what the writing assistant did and, explicitly, that
  semantic leaf scores come from the locally served judge pipeline rather than
  from it. The detailed disclosure stays in the Acknowledgments.
- **Abstract, keywords, citation style and heading depth already conformed**:
  four-part structured abstract at 191 words (limit 150–250), 5 keywords (limit
  4–6), bracketed numeric citations, two heading levels (limit 3). No change
  needed.
- **Not adapted, deliberately:** figure artwork. The three PNGs carry their own
  titles and footnotes and are 120 dpi; the guideline wants vector EPS or ≥300
  dpi halftone and no in-artwork titles. Re-exporting from the existing `.svg`
  sources is a mechanical but visually re-reviewed task, and it would rebind
  artifacts that C audited. Recorded as a bounded production item with an owner
  decision, not done here.

## 4. Arithmetic and consistency re-check

`verify_revision_v2.py` asserts, and passes, 28 identities, including:

- family rows close: 47/43/4, 17/15/2, 20/20/0, 13/0/13, 16/13/3, 5/5/0 sum to
  118 injections, 96 visible, 22 absorbed;
- three seeds 95+97+90 = 282 tables, 75+76+68 = 219 detected; UID partition
  29+17+73 = 119;
- 24 clusters/stage × 3 stages = 72 clusters, × 3 injections = 216;
- 5 parsing + 7 QA leaves = 12;
- all six FinRank gaps equal random − hard within rounding, and the
  full-precision gap rounds to the displayed value.

Structural counts: 4 tables (6×3, 3×3, 4×4, 7×5), 3 figures, 24 references, 3
contributions, 6 checklist steps, 10 `TBD_OWNER` placeholders, 32 numbered
headings, 0 raw LaTeX commands.

## 5. Page review

All 14 pages of `rendered_v2/paper_e_revision_v2.pdf` were inspected at
1020×1320 (120 DPI), one page at a time, not via a contact sheet.

- No clipped, overlapping or missing text; no missing glyphs for `Γ`, `θ`, `×`,
  `−`, `≈`, `≥`.
- All four tables editable, bordered, header row present, no empty cells; Table 3
  keeps its confidence-interval brackets intact.
- All three figures sharp; captions are document text below each figure.
- References 1–24 in order, ending cleanly on [24]; NIST and Bean entries fixed.
- Conclusion, Acknowledgements, Data Availability and Declarations all present.
- Page 7 carries roughly a third of a page of white space because Figure 2
  cannot start until page 8. This is normal flow-layout behaviour for a
  single-column Word manuscript and is not a clipping or fusion defect.

## 6. What is deliberately not done

- **Author identity, affiliation, corresponding author, funding, conflicts,
  patent status, artifact licence, authors' contributions, submission channel and
  fees** remain `TBD_OWNER`. Nothing was invented.
- **Figure artwork** is unchanged: PNG at 120 dpi with in-artwork titles and
  footnotes. The SNCS guideline wants vector EPS or ≥300 dpi halftone and no
  in-artwork titles. Left for a bounded production step because it would rebind
  artifacts C already audited. See `SNCS_GUIDELINE_CHECK_20261028.md`.
- **Reference title capitalisation** is left exactly as published: `[12]`, `[13]`,
  `[15]` and `[16]` use title case while the rest use sentence case. Normalising
  it would mean altering cited titles, which is a worse error than an
  inconsistent case convention. Only the author-name form was converted.
- **Heading colour.** Headings inherit the blue accent from
  `reference_style.docx`, as in the C-reviewed render. Left as is: it is a
  template property, not a manuscript defect, and the submission system
  re-formats.
- **D/T/M raw, receipts, scoring and the historical manifest** are untouched.
  L6/L7 and the `numeric_value` exact-key conflict are handled in the separate
  decision card, not by editing frozen carriers.
- **FinQA fixture absence** and the school-recognition question are outside this
  round.

## 7. Boundary

Internal Word-route revision acceptance only. It is not publisher formatting
acceptance, not submission acceptance, not school recognition, and not a claim
that the two-case contribution is sufficient for acceptance.
