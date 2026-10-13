# TAT-QA Licence Record v1

> date: 2026-10-13 | author: Loop D (WP-0 item A1) | status: `VERIFIED_FROM_PRIMARY_SOURCES`
> purpose: bind the exact licence facts for using TAT-QA as the TH3-RQ2 source family. This is a record of what the upstream states; it is not a legal opinion.

## Verified facts (fetched 2026-10-13)

| Item | Value | Evidence |
|---|---|---|
| Upstream project | TAT-QA, `https://github.com/NExTplusplus/TAT-QA` | official locator (the older `NextOpenSource/TAT-QA` path 404s) |
| Repository licence | **MIT** - "Copyright (c) 2021 Fengbin Zhu" | `LICENSE` at raw.githubusercontent.com, HTTP 200, 1,068 bytes |
| Data licence | **Creative Commons Attribution 4.0 International (CC BY 4.0)** - stated verbatim: "The TAT-QA dataset is under the license of Creative Commons (CC BY) Attribution 4.0 International" | repository `README.md`, section "License" |
| Category of the data | financial-report question answering over tables (the tables are the object we would use) | TAT-QA paper + repository README |

## Obligations we accept

1. **Attribution.** Any release (paper, artifact, derived manifest) must credit TAT-QA and link the CC BY 4.0 licence.
2. **Indicate changes.** The drift-v0 injection map and any task projection are *derivatives*; the artifact must state that the tables are derived from TAT-QA and that perturbations were added by this project.
3. **No endorsement.** We must not imply that the TAT-QA authors endorse this work.
4. **No additional restrictions.** We may not impose terms that forbid what CC BY 4.0 permits.

## Revision binding requirement

At acquisition time the downloaded files must be recorded with (a) the exact upstream commit/ref used, (b) per-file sha256, (c) fetch date. The licence record is valid for the recorded revision only.

## Deliberate exclusions

- This record does **not** cover FinQA, ConvFinQA, MultiHiertt, HiTab or any other registry candidate.
- It does **not** authorise redistribution of any third-party content that TAT-QA itself embeds beyond what CC BY 4.0 permits; if a nested licence appears in the data, it must be surfaced and reviewed before release.
- It does **not** authorise a public release of the artifact; the owner decision is "prepare only".