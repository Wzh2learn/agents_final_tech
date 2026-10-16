# Evidence Protocol v2 (for TQ-4)

> Adopted 2026-10-16 per adjudication. Applies to the TQ-4 run card and all new materials.
> Old TQ-3 materials are read-only and are NOT rewritten to this protocol.

## 1. Evidence object schema (model-visible output)

Outputs carry `evidence` as a list of typed entries:

- Cell evidence: `{"kind": "cell", "table_row": <int>, "table_col": <int>}`
  - `table_row` / `table_col` are 0-based indices into the provided table (row 0 = headers).
- Paragraph evidence: `{"kind": "paragraph", "paragraph_uid": "<uid>"}`
  - `paragraph_uid` MUST be one of the `uid` values already present in the input's `paragraphs` list.

No other kinds; no bare coordinates; no free-text locations.

## 2. Two layers, recorded separately, never merged

- Layer L - legality (mechanical, no model):
  `check_evidence_legality(table, paragraphs, evidence)` in `scorer_v2/tq4_scoring_entry.py`.
  Records: `legal` true/false plus per-entry issues (`cell_out_of_bounds` / `paragraph_uid_unknown` / `kind_invalid` / `not_object`).
  Legality is a protocol/schema judgment only. It says nothing about whether the evidence supports the answer.
- Layer S - support (semantic):
  B/C produce accept / alarm / abstain + reasons + contradiction points; support judgments are recorded in the
  B/C decision files with their own reasons. They are never converted into legality verdicts, and vice versa.

## 3. Required separation in records

Every TQ-4 result row carries both:
- `legality`: {...} (mechanical, deterministic, offline)
- `support`: {B: {...}, C: {...}} (model judgments)

Reports must not phrase legality failures as semantic errors, nor support alarms as protocol violations.

## 4. Relationship to the old (v1) panel

TQ-3 evidence entries (bare `{"table_row","table_col"}`) predate this protocol and lack `kind`.
Under protocol v2 they would be schema-illegal (`kind_invalid`) regardless of any indexing convention.
The TQ-3 interpretation corrections (see `rescoring/TQ3_RESCORE_REPORT_v1.md`) follow from this.
