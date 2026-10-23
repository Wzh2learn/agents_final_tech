# Paper E ICAART 2027 Submission Handoff

Checked: 2026-10-23, Asia/Shanghai
Starting HEAD: `df58512a7a84251446d7377eee5f71a405aa6544`
Status: `OWNER_ONE_TIME_HANDOFF / EXTERNAL_ACTIONS_NOT_EXECUTED`

This is a live venue handoff for the existing two-case Paper E package. It
does not change the scientific claims, add a third case, authorize submission,
authorize payment, or release anything publicly.

## 1. Final PDF Identity

- File: `research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/PAPER_E_ICAART_REVIEW.pdf`
- SHA-256: `2041aaca97ff1b8a0cd843070c7ab4cfd9de088824e17c6d33eb1d1c11651b3a`
- Size: 287,919 bytes; 11 A4 pages.
- PDF author metadata: empty; anonymization audit: PASS.
- Canonical Markdown SHA-256: `3a914d049aca7a1e3ecb0fb1999f5a0398c3b1b44a5e4815df31d1a104c77af5`
- ICAART TeX SHA-256: `b3aab99153473952707bfc7e6dacac857be18de253838b43f7ca45e9dec8653a`
- Non-whitespace counts: Markdown 40,284; ICAART TeX 39,811. Both are within
  the live Regular Paper range.
- Package audit: `PASS`; citations 21/21; no unresolved references.

## 2. Live Venue Evidence

Official pages were fetched directly on 2026-10-23 (Asia/Shanghai). The
machine receipt records each URL, HTTP status, retrieval time and body hash.

- Venue: ICAART 2027, 19th International Conference on Agents and Artificial
  Intelligence, Valletta, Malta, 23-26 February 2027.
- Track: **Regular Paper**. The official Call for Papers describes Regular
  Papers as completed and validated research; Position Papers are for
  work-in-progress or arguable opinions. The existing Paper E is a completed
  bounded audit and therefore selects Regular Paper.
- Areas: the live Call for Papers lists Area 1 `AGENTS` and Area 2
  `ARTIFICIAL INTELLIGENCE`. The draft should select Area 2 and use the live
  form's closest topic labels for evaluation, interpretability, transparency
  and uncertainty. Do not invent a separate track.
- Second-stage Position/Regular submission: **2026-10-29 AoE (extended)**.
  Notification: **2026-12-04**. Camera-ready and registration: **2026-12-18**.
  All dates on the policy page use AoE, meaning Anywhere on Earth.
- Submission entry: the official `Submit Paper` link currently redirects to a
  PRIMORIS login page for ICAART 2027. The Call for Papers body still displays
  `PAPER SUBMISSION WILL BE AVAILABLE SOON`; therefore the live link is
  reachable, but the live form must be rechecked immediately before upload.
- Official LaTeX template:
  `https://www.scitepress.org/documents/SCITEPRESS_Conference_Latex.zip`.
  Downloaded hash: `5385a752f5da2f970236f21404405a2f5c78856c30abc96e02752f06aac20ab8`,
  matching the existing package manifest. Templates are strongly advised for
  review and mandatory for camera-ready; a malformed camera-ready can be
  excluded from the proceedings.
- Anonymity: double-blind review. The submitted PDF must contain no author
  names, personal details, acknowledgments that identify authors, or other
  identity-revealing links. The current review PDF has no author metadata and
  passed the anonymization audit. The live Guidelines say the paper should not
  exceed nine authors.
- Regular Paper submission: PDF, 10,000-50,000 non-whitespace characters,
  including references, tables, graphs and appendices. Full Paper proceedings
  limit is 12 pages; Short Paper limit is 8 pages; at most four extra pages
  are allowed for an additional fee.

## 3. Submission Field Draft

- Title: `Visibility Is Not Detection: Auditing Measurement Boundaries in Staged and Evidence-Ranking Evaluation`
- Paper type: `Regular Paper`
- Primary area: `ARTIFICIAL INTELLIGENCE`
- Topic draft: select the live form labels closest to `Explainable Artificial
  Intelligence`, `Interpretable Artificial Intelligence`, `Transparency`,
  `Uncertainty in AI`, and evaluation/reliability. The exact form labels must
  be confirmed in PRIMORIS at upload.
- Language: English.
- Keywords: `Measurement Validity, Agent Evaluation, Benchmark Auditing,
  Reproducibility.`
- Abstract draft:

  > Final-answer scores can hide whether an evaluation observed a defect,
  > consumed the observation, or treats the outcome as harmless. We audit
  > exactly two constructions. In a staged document evaluator, 96/118 header
  > injections are visible, while the OCR-like family is unobserved on the
  > frozen surface (0/13) and harmfulness remains contract-relative. Flat and
  > layered scores are affine/rank-equivalent, a clean-only panel cannot
  > identify the deployment threshold, and explicit instrumentation explains
  > perfect stage separation. A nested FinQA probe exposes a measurement-object
  > mismatch. In FinRank, tie policy moves absolute accuracy but preserves the
  > hard-versus-random direction; post-hoc text_sha1 correction finds 442
  > overlapping hard-negative occurrences across 305 records and gold loss in
  > 33 records. The bounded contribution separates visibility, detection,
  > harmfulness, score sensitivity, decision stability and reproduction gap,
  > and proposes a review checklist rather than a universal theory.

- Upload file: `PAPER_E_ICAART_REVIEW.pdf`, double-blind review copy.
- Cover letter: use the existing ICAART draft after Owner confirms the live
  submission fields and author details.
- Simultaneous submission: **not permitted**. Owner must confirm this is the
  only active submission.

## 4. Author And Affiliation Fields

The current review PDF intentionally remains anonymous. These fields belong in
PRIMORIS and the eventual camera-ready, not in the review PDF:

| Field | Required value |
|---|---|
| First author | `OWNER_REQUIRED` |
| Author order | `OWNER_REQUIRED` |
| First affiliation | BUPT; confirm official English name and exact ordering |
| Remaining affiliations | `OWNER_REQUIRED` |
| Corresponding author | `OWNER_REQUIRED` |
| Corresponding email | `OWNER_REQUIRED` |
| ORCID | `OWNER_REQUIRED` |
| Contact/address | `OWNER_REQUIRED` |
| Patent/restricted-technology status | `OWNER_REQUIRED` |

The final author count must be no more than nine under the live Guidelines.

## 5. AI Disclosure Final Candidate

The following text is already in the canonical manuscript and ICAART TeX.
It names the tool, affected parts and the offline code role while keeping
experimental outputs, deterministic computation and human/executable evidence
separate:

> Generative AI disclosure: OpenAI Codex assisted manuscript organization,
> English editing and consistency checks in the abstract, related-work framing,
> interpretation table, discussion, conclusion, acknowledgments and submission
> materials, and assisted development and revision of offline analysis and
> reproduction code used for deterministic checks. The authors verified all
> reported numbers, claims and references against cited artifacts and remain
> fully responsible for the manuscript. Experimental evidence includes
> evaluated-system and automated-judge outputs under frozen protocols;
> deterministic statistics were recomputed with the analysis scripts. These
> roles are distinct: no AI-assisted review is presented as human blind review,
> and no AI-assisted adjudication is presented as human semantic gold.

Owner must approve this exact wording and decide whether a separate OpenAI
Codex software citation is required. The live AI Tools page requires the tool
name, affected parts and a short explanation in Acknowledgments; it also
prohibits AI fabrication/manipulation of research data, code, figures or
results and prohibits using public AI platforms to generate peer-review text
for a manuscript under review.

## 6. Artifact Public Plan

- Current private candidate:
  `research/publication_thesis_goals_v1/G1_SUBMISSION_PACKAGE/PAPER_E_PRIVATE_ARTIFACT_CANDIDATE.zip`
- SHA-256: `e70d17eaf95382bd00a24c7d39d68773659d61dba6883775913d7c4a810b05da`
  (15,267 bytes).
- The candidate includes row-level reanalysis input, full-precision and compact
  FinRank extracts, reproduction scripts, manifests and a clean GB10 Python
  3.12.3 reproduction receipt. The receipt status is PASS.
- Historical preregistration, fixtures, application rows and raw score
  matrices are intentionally outside this private candidate and remain in the
  project evidence store for author-approved release.
- During double-blind review: keep the archive private; do not expose a
  repository URL that identifies the authors.
- After acceptance, Owner chooses: anonymous supplementary upload if the live
  venue supports it, or a public repository/DOI after the patent and license
  checks. Record TAT-QA source terms and FinRank CC BY-NC 4.0 before release.
- Choose a code license only after checking third-party components. No public
  release, DOI, URL or copyright transfer has been made.

## 7. Fees And Presentation

The live Registration Fees page reports EUR prices. For a paper author/speaker:

- Member/sponsor: early EUR 620; late EUR 725.
- Regular/non-member: early EUR 680; late EUR 795.
- Each additional paper: EUR 290.
- Each additional page: EUR 50 during early or late registration.
- The current PDF is 11 pages. If accepted as a Full Paper, the 12-page
  proceedings limit requires no extra page. If accepted as a Short Paper, the
  8-page baseline would require three extra pages for an 11-page camera-ready,
  or EUR 150 at the current page price, subject to final layout and venue
  approval.
- The speaker row does not list an on-site price. Stage 2 early registration is
  tied to the 2026-12-18 camera-ready/registration deadline.
- Cancellation before 2026-12-22 is refunded less a EUR 100 administrative
  fee; no refund after that date.

Presentation obligations:

- Full Papers: 25-minute oral slot. Short Papers: 20-minute oral slot or poster
  assignment. An author assigned an oral slot may elect a poster instead.
- Every accepted paper must be presented to be published in the proceedings
  and SCITEPRESS Digital Library; online publication alone is insufficient.
- The live presentation page describes both onsite and online procedures. For
  onsite posters: A0 portrait, author present for the full poster session. For
  oral talks: slides must fit the slot with at least five minutes for questions.
  Online poster and oral procedures include live presence and backup-video
  limits; a backup video does not remove the presenter-presence requirement.
- Exact Full/Short and oral/poster assignment is not known before acceptance.
  Owner must approve travel/remote arrangements and confirm the school accepts
  the actual presentation evidence.

## 8. Owner One-Time Decisions

1. Confirm ICAART Regular Paper as the sole active submission; no simultaneous
   submission.
2. Fill author order, applicant first-author status, BUPT-first affiliation,
   corresponding author, email, ORCID and contact details; keep the final
   author count at nine or fewer.
3. Confirm patent status and whether the manuscript or artifact contains
   restricted technology before submission or release.
4. Approve the exact AI disclosure above and any separate Codex citation.
5. Decide artifact release timing, anonymous supplementary versus post-review
   repository/DOI, and the code license subject to third-party terms.
6. Approve registration and travel/remote presentation costs. Confirm that
   author presentation and the eventual proceedings/SCITEPRESS evidence meet
   the school's recognition requirements.
7. Give explicit authorization for submission, copyright/permission actions
   and payment. These are external actions and are not executed here.

## 9. Evidence Status And Limits

- All eight official venue pages and the submission redirect returned HTTP 200
  after the expected HTTP-to-HTTPS redirect on 2026-10-23.
- `BODY_OBSERVED` facts above are taken from the live page text or live HTML
  table structure. The exact PRIMORIS form fields, upload acceptance and any
  venue-specific supplementary-material rule are `AUTH_REQUIRED` or
  `NOT_OBSERVED` until the Owner logs in.
- The Call for Papers text saying `PAPER SUBMISSION WILL BE AVAILABLE SOON`
  conflicts with the live login redirect. Do not claim that the submission
  form is fully open until the authenticated upload screen is checked.
- No submission, payment, copyright signature, author email or public release
  was performed.
