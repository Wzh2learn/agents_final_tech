# Camera-Ready Checklist v1 (SANER 2027 RENE)

> date: 2026-10-11 | applies AFTER acceptance | owner-facing | source of venue facts: paper/SANER_RENE_2027_REQUIREMENTS.md

## Author and identity
- [ ] Restore the frozen author list and affiliations (identical to the submitted list; SANER states the author list cannot change after acceptance and the camera-ready list must equal the submitted one).
- [ ] Add acknowledgments (prohibited at submission).
- [ ] Title changes only if reviewers/program co-chairs recommend them.

## Content obligations
- [ ] Address reviewer comments as far as possible.
- [ ] Keep the Data Availability statement but replace the anonymized repository with the public DOI-bearing repository.
- [ ] Convert any anonymized artifact links to public ones (`ANONYMOUS_ARTIFACT_RELEASE_PLAN_v1.md` lists the minimum contents).

## IEEE / IEEEtran production duties
- [ ] IEEE copyright form submitted by the deadline (camera-ready date on the CFP: 2027-01-08).
- [ ] At least one author registers at FULL (non-student) rate by the author-registration deadline.
- [ ] Verify the final PDF still uses `\documentclass[10pt,conference]{IEEEtran}` without compsoc options, 24pt title, 10pt body.
- [ ] Re-check the page budget: 10 pages including figures and appendices, plus at most 2 references-only pages.

## Preprint policy (IEEE)
- [ ] If a non-anonymized preprint exists publicly, update it to the IEEE DOI version (or post the accepted author version with the DOI). The IEEE-published version itself must not be posted.
- [ ] Never post the IEEE-formatted PDF.

## Repository side
- [ ] Tag the repository at the camera-ready commit.
- [ ] Publish the artifact (Zenodo/Figshare or equivalent) with a DOI, then link it from the paper.
- [ ] Re-run `scripts/verify_claim_evidence.py` on GB10 and archive the receipt with the camera-ready tag.

## Known residuals to close at camera-ready
- [ ] arXiv BibTeX entries: verify the expanded author lists render correctly (done: full lists pulled from the arXiv API).
- [ ] Optional polish declined for submission: Figure-3 in-figure status labels (caption carries the identities).
- [ ] `figure_source_binding_manifest.json` records a `fig2_source.csv` hash that does not match the current file; fix or drop the entry only at camera-ready (it is a convenience export, not an evidence artifact).