# Goal Contract: Stage E Quantify -> Stress-test -> Transfer -> Distill

Date: 2026-10-09
Mode: NEW ANALYSIS / EXTERNAL REPRODUCTION
Execution boundary: local analysis and approved public-source inspection only.

## Goal

Produce the missing Stage E observability quantification, metric precedent and NIST/ITIL framing, a frozen multi-leaf protocol, and a bounded derived-process-supervision design for Stage D, without changing any frozen Stage E result or advancing Stage R.

## Done When

1. The 12 requested Markdown deliverables exist under `agents_final_tech/docs/research/`.
2. Stage E derived statistics are computed from the frozen JSON artifacts and are reproducible by a checked analysis script.
3. Visibility-threshold and visibility-by-detection figures exist in PNG and SVG with source data receipts.
4. Literature and official governance claims are separated from project interpretation and unsupported claims are marked.
5. PRM800K and Math-Shepherd are audited from official paper/repository/data metadata; existing external-source audits are reused rather than repeated.
6. The final report answers all 17 required research questions and ends with exactly three next actions.
7. Frozen Stage E values and boundaries remain byte-for-byte unchanged where applicable.
8. No model, judge, training, GPU, production service, credential, Phase 2, Stage R, or E-D-R action occurs.

## Never Touch

- `tests/test_m1_service.py`, `scripts/graph/frozen_hashes.txt`, `docs/m1_schema/`, frozen hashes and schemas.
- `paper/teacher_review_draft_v1.md`, `paper/claim_manifest_v1.json`, existing frozen evaluation JSON files, or their historical reports.
- Production endpoints, services, databases, credentials, model configuration, `agents_final_tech` production code, or GB10 dirty runtime files.
- Harmfulness definitions, 95/118, 96/118, 0/13, matched-FPR, or the Stage E claim boundary.

## Stop If

- A source identity, revision, or licence cannot be established.
- Derived statistics cannot be tied to frozen input hashes.
- An existing passing deterministic check begins failing.
- More than 20 files outside this task's intended deliverables/support artifacts change.
- Any requested action would require training, model calls, production access, or frozen-boundary modification.
