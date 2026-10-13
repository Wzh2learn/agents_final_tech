# WP-0 TAT-QA Qualification Appendix v1 (A6)

> date: 2026-10-13 | author: Loop D | status: `APPENDIX_FILED / G-RQ: recommend QUALIFIED_CONDITIONAL (owner-advisor decision pending) / G-M: HOLD (NOT_IDENTIFIED) / EXPERIMENT_NOT_RUN`
> scope: closes items A1-A6 of `WP0_TATQA_PACKAGE_v1.md` Sec.6. Executed: licence record, owner-authorised raw fetch, origin build, candidate-item build, contracts. Not executed: runner (WP-1), pilot (WP-2), any model call, any training, Memory/SFT/DPO.
> owners of record: [task card](thesis_experience_v1_task_card.md) (G-RQ/G-M), [blueprint](THESIS_EXECUTION_BLUEPRINT_v1.md) (numbers), [package](WP0_TATQA_PACKAGE_v1.md) (plan), [licence record](../datasets/tatqa_licence_record_v1.md).

## 1. What changed since the SOURCE_INSUFFICIENT report

| WP-0 checklist item | Before (2026-10-13 morning) | Now | Evidence |
|---|---|---|---|
| 1. Source / revision / licence / scope, IDs, origin grouping | PARTIAL (no download approval; no origin rule) | SATISFIED for TAT-QA | licence record; raw fetch receipt; origin rule instantiated (182 origins, >= 8 needed) |
| 2. Reference-target vs real-execution design chain | DESIGN ONLY | CONTRACTED (adapter + checker, fixture obligations) | `WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md` |
| 3. Experience legally obtainable; feedback rights | NOT SATISFIED | Licence cleared for TAT-QA data use; feedback-right definition still OPEN; actor revision NOT frozen | this appendix Sec.4; MODEL_GO still PENDING |
| 4. Closest mechanisms / residual | PARTIAL | Unchanged: no unexplained residual; `METHOD_NOVELTY = NOT_IDENTIFIED` | qualification report Sec.6 |
| 5. Qualification appendix | missing | This document | - |

## 2. Executed items and receipts (A1-A6)

| # | Item | Artifact | Receipt |
|---|---|---|---|
| A1 | Licence record | `docs/datasets/tatqa_licence_record_v1.md` | repo MIT (raw LICENSE 200/1068 B); data CC BY 4.0 (README, primary source) |
| A2 | Raw fetch (owner-authorised) | `scripts/research/fetch_tatqa_raw.sh` (integrity-gated: tar + JSON parse + record count) | GB10 `data/research/tatqa_raw_2026/FETCH_RECEIPT.txt`: fetch 2026-10-13T05:07:45Z; train sha256 `2df6e722cdbaaa37efcbfb280f5c9a15be29a6ec18f618ef936fe63cc6d07c69` (12,845,647 B); dev sha256 `8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5` (1,637,431 B) |
| A3+A4 | Origin build + candidate items | `research/tatqa_wp0_2026/build_origins.py` | GB10 `data/research/tatqa_wp0_2026/GENERATION_RECEIPT.json`: origins 182; origins_with_ge2_usable_rows 176; candidate_items 60 (60 distinct origins); manifest sha `3718e6fe...`; items sha `bc55fe7a...` |
| probes | p5-p9 derivation probes + README | `research/tatqa_wp0_2026/probes/`, `research/tatqa_wp0_2026/README.md` | frozen measured facts (this appendix Sec.3) |
| A5 | Adapter/checker contract | `docs/research/WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md` | projection rules; hidden-gold rule; outcome taxonomy; 6 fixture obligations; stop = SOFTWARE_NOT_QUALIFIED |
| A6 | This appendix | `docs/research/WP0_TATQA_QUALIFICATION_APPENDIX_v1.md` | -

Upstream revision: `master` observed 2026-10-13 at commit `870accc41953dcde885aabeb963d94aabdc0fbc3` (last upstream commit 2024-12-09; same day as the fetch; content is hash-gated by the receipt above; a commit-SHA pin is to be recorded again at the WP-1 freeze).

## 3. Frozen measured facts (qualification set)

- Raw archives: 2,201 train + 278 dev = 2,479 records (hashes above).
- Origin rule: origin = one raw record (unique table + unique paragraph context); paragraph-set signatures are near-unique (2,467 of 2,479 distinct), so the rule partitions without collapsing records.
- Origin count: 182 records satisfy (>= 2 year-like period columns AND a unit marker AND >= 1 numeric two-period row); 176 of them carry >= 2 usable rows. Pilot requirement is 8 unseen origins: satisfied with wide margin (the reserve of unseen origins is re-checked at item freeze).
- Candidate items: 60 items from 60 distinct origins (not a pilot; gold = recomputed from the table cells by the stated rule; no LLM and no dataset annotation used as gold).
- Annotation caveat (measured): `req_comparison=true` questions are span-type with empty `scale` and do not intersect arithmetic+scale items (measured 0); the WP-0 task is therefore constructed from cells, not taken from dataset annotations.

## 4. G-RQ recommendation - QUALIFIED_CONDITIONAL

Rationale: the minimal question is now instantiated end-to-end on licensed, hash-gated, origin-groupable materials: a verified licence, a 2,479-record raw base, an origin rule with 182 origins, a 60-item constructible pool, and drafted task/adapter/checker contracts. Nothing in the question, the target, or the planned evaluation was changed by this pass.

Binding conditions before any WP-1/WP-2 step (unchanged from the package, still OPEN):
1. Feedback right: what historical feedback may be shown to the actor, from where (owner-advisor).
2. One frozen actor revision + tool set + generation settings (MODEL_GO is still PENDING; existing Qwen3 receipts predate this route and are not MODEL_GO).
3. Budget/window binding (hard cap 300 actor request attempts, 0 judge calls; per blueprint).

Formal verdict remains with the owner-advisor (task card: "导师/owner 裁决 G-RQ/G-M"). Until that decision, `G-RQ` stays PENDING on the record; this appendix records the recommendation only.

## 5. G-M recommendation - HOLD (NOT_IDENTIFIED)

Unchanged. Materials qualification does not create method necessity: no residual unexplained by the nearest neighbours (ACE/MemRL-class mechanisms) has been identified, and no new mechanism claim is made here. If a future authorised pilot shows a residual under the frozen stop rules, G-M is re-adjudicated then. `METHOD_NOVELTY = NOT_IDENTIFIED` stands.

## 6. Not authorised / stop conditions unchanged

- Not authorised: WP-2 (pilot), any episode collection, any model sampling, any training (Memory/SFT/DPO), any production service. (WP-1 was owner-approved and executed 2026-10-13; software PASS certifies the contracts only - record: `WP1_COMPLETION_RECORD_v1.md`.)
- Stop rules unchanged (task card Sec.4; blueprint): SOURCE_INSUFFICIENT / UNDETERMINED / CEILING / leakage checks; no new significance thresholds introduced.
- No old closed material (Stage-E re-splits, FinQA, PR-03) is reused as the new panel.

## 7. Unresolved dependencies (owner-advisor)

1. Feedback-right definition.
2. Actor-revision + tool-set freeze.
3. Budget/window binding.
4. Mechanical: record the upstream commit-SHA pin again at the WP-1 freeze (this appendix records the 2026-10-13 observation).
5. Mechanical: at item freeze, confirm >= 8 unseen origins remain outside development/history.

## 8. Evidence index

- Plan: `docs/research/WP0_TATQA_PACKAGE_v1.md` (Sec.6 table; Sec.7 owners list).
- Licence: `docs/datasets/tatqa_licence_record_v1.md`.
- Fetch script + receipts: `scripts/research/fetch_tatqa_raw.sh`; GB10 `data/research/tatqa_raw_2026/FETCH_RECEIPT.{txt,sha256}`.
- Build script + receipt: `research/tatqa_wp0_2026/build_origins.py`; GB10 `data/research/tatqa_wp0_2026/GENERATION_RECEIPT.json`.
- Probes + frozen facts: `research/tatqa_wp0_2026/README.md`, `research/tatqa_wp0_2026/probes/p5-p9`.
- Contracts: `docs/research/WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md`.
- Gates: `docs/research/thesis_experience_v1_task_card.md`, `docs/research/THESIS_EXECUTION_BLUEPRINT_v1.md`, `docs/research/WP0_QUALIFICATION_REPORT_v1.md` (update Sec.10).

**This appendix does not authorise WP-1 or WP-2, does not run anything, and does not certify method novelty.**
