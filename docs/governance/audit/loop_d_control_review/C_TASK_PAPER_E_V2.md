# Loop C — single fixed-snapshot review of the revised Paper E

Date issued: 2026-10-28, Asia/Shanghai.
Dispatch number: **29 of a cumulative cap of 29**. This is the only C launch in
this round. There is no reserve, no retry and no follow-up dispatch.

## Your role

You are an **independent reviewer**. You did not write this manuscript, this
revision or this render. Report what you find; do not repair anything, do not
edit any file, do not commit, push or delete.

Your conclusions are advisory. Loop D adjudicates them against evidence. Being
wrong in a documented way is acceptable; being vague is not.

## The object under review — one frozen snapshot

Commit: **`08be054734082b62969a132c1a0222278e8348db`**
Branch: `integration/paper-e-word-20261028`
Repository: `~/wzh/projects/agents_final_tech` (on this machine)

Review **only this commit**. Do not review `main`, do not review the research
branch, do not review any other worktree on this machine, and do not review the
previous round's render.

## Whitelisted inputs (read these; do not go hunting elsewhere)

| What | Path (relative to the repository) |
|---|---|
| Production manuscript source | `research/word_scoring_new_family_20261027_v1/paper_e_word/paper_e_revision_v2.md` |
| Rendered DOCX | `research/word_scoring_new_family_20261027_v1/paper_e_word/paper_e_revision_v2.docx` |
| Rendered PDF | `research/word_scoring_new_family_20261027_v1/paper_e_word/rendered_v2/paper_e_revision_v2.pdf` |
| Page images (14) | `research/word_scoring_new_family_20261027_v1/paper_e_word/rendered_v2/page-NN.png` |
| Page hashes | `research/word_scoring_new_family_20261027_v1/paper_e_word/D_PAGE_HASHES_V2.sha256` |
| Conversion manifest | `research/word_scoring_new_family_20261027_v1/paper_e_word/CONVERSION_MANIFEST_V2.json` |
| Build commands | `research/word_scoring_new_family_20261027_v1/paper_e_word/BUILD_COMMANDS_V2.md` |
| Build scripts | `.../paper_e_word/build_revision_v2.py`, `polish_docx_v2.py`, `verify_revision_v2.py` |
| Build log | `.../paper_e_word/REVISION_V2_BUILD_LOG.json` |
| Lint receipt | `research/word_scoring_new_family_20261027_v1/validation/REVISION_V2_LINT.json` |
| D's revision notes | `.../paper_e_word/D_REVISION_NOTES_20261028.md` |
| Journal fit note | `.../paper_e_word/SNCS_GUIDELINE_CHECK_20261028.md` |
| Frozen extraction (for diffing) | `.../paper_e_word/paper_e_word.md` |
| Canonical TeX (authority for restored text) | `research/adaptive_mechanism_20261027_v1/paper_e_word/../../paper_e_formal_build/paper_e_sncs.tex` → exact path `research/adaptive_mechanism_20261027_v1/paper_e_formal_build/paper_e_sncs.tex` |
| Reference database | `.../paper_e_word/references.bib` |
| Prior C audit (context only) | `research/word_scoring_new_family_20261027_v1/audits/C_JOINT_AUDIT.md` |

`D_REVISION_NOTES_20261028.md` and `SNCS_GUIDELINE_CHECK_20261028.md` are **D's
claims about D's own work**. Read them last, and only to compare against what you
found yourself. Do not treat them as evidence.

## Scope — four questions, nothing else

### Q1. Do the two-case claims and the numbers hold together?

Check internal consistency of the manuscript as rendered:

- every fraction, interval, count and percentage agrees with every other place it
  appears, and with the table cells that display it;
- the family rows close (118 injections split into visible and absorbed);
- the FinRank table's displayed gaps are consistent with its own rounded cells
  **and** with the note that explains why one gap differs in the last digit;
- the abstract, the results sections and the conclusion support each other, and
  nothing in the conclusion asserts more than the two cases support;
- pre-registered and post-hoc material is distinguishable wherever it matters.

You do **not** need to re-derive any scientific result, re-run any model, or
audit the upstream research history. The claim is bounded to two cases and the
manuscript says so; check that it actually does.

### Q2. Are the four layout defect classes really closed?

The previous audit found four: fused tables/caption/list, "six-step" with five
steps, unnumbered or uncaptioned exhibits, and reference-manufacturing defects.
Verify independently, from the PDF pages and the DOCX XML (not from the notes):

- every table is a real editable Word table, has a caption above it, a header
  row, and a number that matches its in-text reference and its order of
  appearance;
- every figure has caption text as document body text, not as image alt text;
- every list renders as a list with visible markers, and no list is swallowed
  into a paragraph;
- no heading, table row, caption or formula is truncated, fused, or replaced by a
  placeholder;
- all 14 pages: look at them. A contact sheet or a spot check does not count.

### Q3. Is the bibliography correct now?

- 24 entries, numbered 1–24, cited in the text, every entry cited at least once;
- each in-text number points at the reference it is supposed to point at. Pick at
  least six citation groups across different sections and check the mapping
  against the entry's own title and authors, not against a list of keys;
- no BibTeX residue, no mangled corporate author, no doubled punctuation;
- the entry that the previous audit flagged twice is fixed.

### Q4. Does the package meet the stated venue requirements?

The venue is SN Computer Science (subscription route, conditional). Check only
what is checkable from the artifacts plus the public guideline:

- structured abstract with the required parts and a length inside the stated band;
- keyword count inside the stated band;
- numbered bracketed citations, consecutive reference numbering;
- a "Statements and Declarations" section carrying the statements the guideline
  requires;
- AI use described in the methods, not only in the acknowledgments.

State explicitly whether the reference author-name form matches the venue's
published style, and whether the figure artwork meets the venue's resolution and
"no in-artwork title" requirement. If it does not, say so plainly; D expects at
least one unresolved item here.

## Explicitly out of scope

- Re-auditing the D/T/M diagnostic, the scoring contract, the raw responses, the
  budget ledger, or the historical artifact manifest.
- Re-running any model, judge, training, or PDF build.
- Proposing new experiments, new claims, or a different paper.
- Reviewing other branches, other worktrees, or other manuscripts on this
  machine.
- Rewriting, editing or committing anything.

## Hard limits — stop at whichever comes first

- **Maximum 20 tool calls.** Count every shell command, every file read, every
  image view, every subprocess.
- **Maximum 30 minutes of wall clock.**
- At the limit, stop and submit whatever you have. A partial report that states
  what you did not reach is worth more than a complete-sounding guess.
- **No sub-agents, no delegation, no background jobs, no retry loops.** You are
  one process. If a command fails, record it and move on; do not retry it more
  than once.
- Do not install anything. Do not modify any file in the repository. Do not touch
  the network except for the public guideline check in Q4.

## Budget honesty

At the end of your report, state separately:

- how many tool calls you actually used, and the wall-clock time;
- what you could not check within the limit;
- whether any part of your review is a soft limit that you could not enforce.

If you cannot measure something, write `UNKNOWN`. Do not estimate silently.

## Output

Write your report to:

`research/word_scoring_new_family_20261027_v1/audits/C_PAPER_E_V2_REVIEW.md`

(That single file is the one permitted write. Create it; do not modify anything
else.)

Structure:

1. **Verdict** — one of `ACCEPTED_FOR_AUTHOR_HANDLING`,
   `CONDITIONAL`, `REJECTED`, with one sentence of justification.
2. **Blocking defects** — table of `ID | defect | carrier (path:line or page)`.
3. **Non-blocking defects and limitations** — same table shape.
4. **Q1–Q4 findings**, each with the commands you ran and what you saw.
5. **What you did not check within the limit.**
6. **Cost and limit accounting.**

Be concrete. "Several issues remain" is not a finding. "Table 3 caption reads
'Table 3.' but the in-text reference on page 9 says 'Table 2'" is.
