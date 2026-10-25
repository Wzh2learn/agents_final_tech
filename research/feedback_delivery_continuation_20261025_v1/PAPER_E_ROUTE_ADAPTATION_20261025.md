# Paper E Route Adaptation and Submission Decision

Date: 2026-10-25, Asia/Shanghai

Status: `SCIENTIFIC_ADAPTATION_COMPLETE_OWNER_DECISION_REQUIRED`

## Decision

**Primary: ICAART 2027 Regular Paper.**

**Sequential backup: SN Computer Science, subscription publishing route,
after a terminal ICAART decision.**

This recommendation is conditional in one precise way: use ICAART only if the
Owner can authorize the existing package before the 2026-10-29 AoE deadline,
accept the author-presentation requirement and travel/registration exposure,
and confirm that SCITEPRESS proceedings will satisfy the school's recognition
rule. If any of those conditions is false, do not submit to ICAART; convert the
same two-case manuscript to the SN Computer Science package and submit there.
This is not an acceptance-rate recommendation. No reliable track-level or
overall acceptance-rate evidence was obtained.

The manuscript remains a bounded two-case measurement audit. Neither route
justifies adding C2/C3 experiments as a third case or broadening the work into
a general Agent method.

## Scientific Fit

### ICAART

The paper fits ICAART through reliable AI evaluation, measurement validity,
LLM evaluation and evidence-ranking reliability. The current manuscript's
strongest venue-specific value is that it audits what an evaluation can
observe and what a score or tie contract can support, rather than proposing
another model or benchmark.

The closest ICAART empirical audit found is Bastos et al., *Uncovering Hidden
Biases in Synthetic Java Vulnerability Data for LLM-Based Detection*. That work
identifies dataset artifacts and shows a model trained on biased data loses
accuracy after sanitization. Paper E differs by separating visibility,
detection, contract-relative harmfulness, score sensitivity, decision
stability and reproduction gap across two evaluation constructions. Jouseau et
al. propose a data-quality metric; Paper E audits existing contracts and does
not claim a universal metric.

Required scientific adaptation before upload is small but real:

1. Add one short Related Work paragraph comparing the ICAART data-quality and
   synthetic-bias audits with Paper E's measurement-object and decision-stable
   interpretation. This prevents the work from reading as an unrelated generic
   validity paper.
2. Add one bounded motivation sentence stating that staged evidence and
   ranking contracts are relevant to agent evaluators, while explicitly saying
   that neither counted case evaluates an agent system.
3. Replace the keyword `Agent Evaluation` with `AI Evaluation` or
   `Evidence-Ranking Evaluation` unless that bounded motivation is added. The
   present cases do not support an unqualified agent-evaluation keyword.
4. Resolve the ICAART AI-tool rule: the Acknowledgments names OpenAI Codex and
   affected sections, but the official guideline also asks affected sections
   to include a citation to the AI system. Add a verified software citation or
   obtain an explicit venue interpretation before upload. Do not invent a
   version or bibliographic record.

These changes do not require a third case or a new experiment. At route-analysis
time the manuscript had 40,284 non-whitespace characters and an 11-page review
PDF. The implemented manuscript adaptation now has 41,515 non-whitespace
Markdown characters and a 12-page PDF, still within the Full Paper limits. The
package manifest and 2026-10-25 package audit are the current submission-state
authority.

### SN Computer Science

SN Computer Science is a strong broad-scope Original Research route for an
empirical AI-evaluation audit. Its official scope explicitly includes
Artificial Intelligence, Machine Learning, Information Retrieval and
Multi-Agent Systems. The near-neighbor Karamousalidis and Kefalas article
combines execution, LLM-as-judge and reliability analysis in a multi-agent
logic-programming benchmark. Paper E remains distinguishable because it audits
measurement objects, tie/identity contracts, decision stability and a bounded
reproduction gap rather than building a new benchmark framework.

The journal route requires more manuscript conversion than ICAART:

1. Rewrite the 131-word unstructured abstract as a 150-250 word structured
   abstract with `Purpose`, `Methods`, `Results` and `Conclusion`.
2. Add a separate single-blind title page with authors, BUPT affiliation,
   corresponding email and ORCID fields.
3. Convert the Data Availability and Acknowledgments material into a formal
   Declarations section covering funding, competing interests, data/material/
   code availability and author contributions. LLM use must be documented in
   Methods or a suitable alternative section; the existing disclosure is close
   but should be retained explicitly.
4. Submit all editable sources, including LaTeX/BibTeX and figure sources, not
   only the PDF.
5. Keep the two-case claim boundary. Do not reframe the checklist as a
   validated journal-scale theory.

The current title and core results can remain unchanged. A possible structured
abstract is:

> **Purpose:** This study asks how evaluation conclusions should be interpreted
> when a controlled defect may be invisible to the instrument, visible but not
> consumed by a decision rule, or harmless under the evaluation's equivalence
> contract. **Methods:** We conduct a bounded measurement audit of two
> constructions: a frozen staged document evaluator with controlled
> perturbations and a nested FinQA measurement-object probe, plus a
> provenance-sensitive FinRank evidence-ranking audit with preregistered v1
> metrics and a clearly labelled post-hoc identity correction. We separate
> visibility, detection, harmfulness, score sensitivity, decision stability and
> reproduction gap. **Results:** In the staged evaluator, 96/118 header
> injections are visible, the OCR-like family is unobserved on the frozen
> surface (0/13), and flat/layered scores are affine/rank-equivalent. The FinQA
> probe exposes a measurement-object mismatch. In FinRank, tie policy moves
> absolute accuracy but preserves the hard-versus-random direction; source
> identity correction exposes overlap and gold loss while leaving an unresolved
> global reproduction gap. **Conclusion:** A six-step review checklist helps
> evaluator authors bind mutation, observation, score, ranking and reported
> claim to the same measurement object, without claiming a universal theory.

This draft is for the SNCS conversion only. It is not a new result and should
not be used to widen the ICAART claim.

## Cost, Time and Credential Comparison

| Item | ICAART 2027 Regular | SN Computer Science |
|---|---|---|
| Review | Double-blind; at least two reviewers, usually three or more | Single-blind; minimum two reviews |
| Submission timing | Second-stage Regular deadline 2026-10-29 AoE; notification 2026-12-04; camera-ready/registration 2026-12-18 | No fixed deadline found; median submission-to-first-decision 96 days |
| Publication event | Conference 2027-02-23 to 2027-02-26, Valletta; presentation is mandatory for online proceedings publication | Online-only hybrid journal; no mandatory conference presentation |
| Known fee | Early non-member speaker registration EUR 680; extra page EUR 50/page; optional early social event EUR 80; travel unknown | Submission, page and color charges are free; subscription APC is zero; optional OA APC currently GBP 2,390 / USD 3,290 / EUR 2,690 plus tax |
| Paper length | 10,000-50,000 non-whitespace characters; Full 12 pages, Short 8 pages, at most 4 paid extra pages | No fixed page count found in the checked author guidance; structured abstract 150-250 words and complete editable sources required |
| Known risk | Acceptance may be Full or Short; if Short and 11 pages are retained, 3 extra pages cost EUR 150 or the paper must be compressed. Travel and presentation are real obligations. | First decision median is not a publication guarantee; final timing and school recognition remain unknown. Conversion effort is moderate. |

Known ICAART subtotal is EUR 680-830 before travel, using early non-member
speaker registration and either no extra pages or three extra pages if accepted
as Short. The optional social event adds EUR 80. Do not present these figures
as total cost.

## Near-Neighbor Full-Text Status

The official Springer pages for Bastos et al. and Karamousalidis et al. were
read through their abstracts, metadata, notes and visible article-page text on
2026-10-25. Direct requests to the DOI PDF URLs returned HTML access pages, not
article PDFs. Therefore the comparison above is a real abstract/metadata/
visible-page comparison, not a claim of full-text replication. The same
limitation applies to the earlier route manifest's Springer neighbors.

The ICAART official date, guideline, fee and call pages were directly refreshed
on 2026-10-25. The PRIMORIS direct link returned the live login page for ICAART
2027, confirming that an upload path exists but providing no submission
authorization.

## Owner Decision Page

Owner approval is required only for these external or identity-sensitive
actions:

1. Approve ICAART primary and SNCS sequential backup, or explicitly switch to
   SNCS now because of school recognition, presentation, travel or timing.
2. Confirm author order, applicant first author, BUPT first affiliation,
   corresponding author, email and ORCID.
3. Approve the precise OpenAI Codex disclosure and provide/choose a verified
   software citation if ICAART requires one.
4. Confirm patent/restricted-technology status.
5. Approve artifact release, license and any DOI/venue-supported link.
6. Authorize submission and any copyright/permission action.
7. Approve registration and travel/presentation arrangements, or approve the
   journal route that avoids them.
8. Provide the exact school recognition rule and the exact 2027 thesis review
   date. Do not assume October 31.

No submission, payment, signature, public artifact release or external contact
was made in this adaptation.

## Sources Checked

- ICAART Important Dates: `https://icaart.scitevents.org/ImportantDates.aspx?y=2027`
- ICAART Guidelines: `https://icaart.scitevents.org/Guidelines.aspx?y=2027`
- ICAART Registration Fees: `https://icaart.scitevents.org/RegistrationFees.aspx?y=2027`
- ICAART Call for Papers and live submission link:
  `https://icaart.scitevents.org/CallForPapers.aspx?y=2027`
- SN Computer Science scope: `https://link.springer.com/journal/42979/aims-and-scope`
- SN Computer Science submission guidelines:
  `https://link.springer.com/journal/42979/submission-guidelines`
- SN Computer Science publishing and fees:
  `https://link.springer.com/journal/42979/how-to-publish-with-us`
- Bastos et al. visible article page:
  `https://doi.org/10.1007/978-3-032-25032-2_14`
- Karamousalidis and Kefalas visible article page:
  `https://doi.org/10.1007/s42979-026-05242-8`
- Existing route evidence and hashes:
  `research/loop_d_reselection_and_continuation_20261024_v1/SOURCE_MANIFEST_V1.json`

