# WP-0 TAT-QA Package v1

> date: 2026-10-13 | author: Loop D | status: `A1-A6 EXECUTED / ORIGIN RULE INSTANTIATED (182 origins; 60 candidate items; receipts on GB10) / NO_EXPERIMENT`
> owner decision applied: WP-0 source family = **TAT-QA**. Purpose: finish the qualification for TAT-QA and leave a Loop-A-executable entry. No method development, no Memory/SFT/DPO, no scope expansion.
> parent: [WP0_ENTRY_PACKAGE_v1.md](WP0_ENTRY_PACKAGE_v1.md), [WP0_QUALIFICATION_REPORT_v1.md](WP0_QUALIFICATION_REPORT_v1.md), [task card](thesis_experience_v1_task_card.md)

## 1. Licence / source feasibility (VERIFIED today from primary sources)

| Item | Finding | Source |
|---|---|---|
| Repository licence | **MIT** ("Copyright (c) 2021 Fengbin Zhu"), fetched 200, 1068 bytes | `raw.githubusercontent.com/NExTplusplus/TAT-QA/master/LICENSE` |
| Data licence | **CC BY 4.0**, stated explicitly: "The TAT-QA dataset is under the license of Creative Commons (CC BY) Attribution 4.0 International" | TAT-QA `README.md` (same host) |
| Registry flag | The registry's `README_REPORTS_CC_BY_4_0_RECHECK_AT_FETCH` is now **confirmed at the recorded revision** (the recheck is done; the statement exists and is unambiguous) | this check |
| Official locator | `https://github.com/NExTplusplus/TAT-QA` (the earlier `NextOpenSource/TAT-QA` path 404s; already recorded in the drift-injection doc) | local record |
| Attribution obligations | CC BY 4.0: attribute the source, indicate changes (the injection map is our derivative), no endorsement implication | CC BY 4.0 terms |
| Local projection already in hand | `data/research/drift_v0/input/tatqa_tables.json` - 2,479 normalized tables `{table, uid}` (2,201 train + 278 dev) | GB10 + drift_injection_v0 doc |

**Verdict:** licence feasibility = **PASS (conditional)**. The CC BY obligation is satisfiable: the released artifact must carry the attribution and mark the derived injection map as a modification. No non-commercial or redistribution restriction applies.

## 2. Task-feasibility sizing (measured on the frozen 2,479-table projection)

| Measurement | Value | Meaning |
|---|---|---|
| Tables with >= 2 year-like header columns | **792 (31.9%)** | multi-period structure exists in quantity |
| Tables whose header carries a unit/scale marker | **395 (15.9%)** | unit normalisation is a real operation in this corpus |
| **Tables with both** | **188 (7.6%)** | the feasible pool for "two-period increase/decrease with unit unification" |
| Column-count distribution | 3 cols: 955; 4: 916; 5: 347; 6: 228; 7-9: 33 | wide enough for period/unit layouts |
| Example header | `['', '2019 %', '2018 %', '2017 %']` | period labels live in the header; values in rows |
| Example header | `['', '2019 €m', '2018 €m', '2017 €m']` | period + unit co-located |

188 candidate tables comfortably exceed the blueprint's 16 pilot + 4 development items even after near-duplicate removal.

## 3. Origin grouping design (the binding constraint)

**Finding (measured):** the normalized projection carries only `{table, uid}`; `uid` is a random UUID. There is **no company/report identifier**. Attempts to recover one from table content are unreliable: a company-name pattern matches 91 distinct strings corpus-wide, and only 28 among multi-period tables, with heavy false positives from accounting vocabulary ("Net Inc", "Salary & Non-Equity Inc", "WEEKS CHANGE NORMALISE"). **Origin grouping therefore cannot be built from the current projection.**

Options, in preference order:

| Option | Rule | Cost | Verdict |
|---|---|---|---|
| **A (recommended)** | Obtain the **raw TAT-QA records** (public, CC BY 4.0): each record carries the table plus its source `paragraphs` with `order`. Group tables whose paragraph sets/near-duplicates coincide, and use that group as the origin (report-level). | one small public download - **needs owner authorisation** (WP-0 is scoped read-only) | the only route that yields genuine report-level origins |
| B | Define origin = company named in the table, where present | zero download | **rejected:** coverage 6.9% of tables and mostly false positives |
| C | Define origin = header-signature cluster | zero download | **rejected:** a signature like `('', '2019', '2018')` occurs 155 times across different issuers; a shape cluster is not an independent origin, and the registry policy already forbids treating a namespace as a row-level cluster |

**Resolution (2026-10-13):** Option A executed under owner authorisation. Raw records fetched (2,479 records; receipt `data/research/tatqa_raw_2026/FETCH_RECEIPT.txt` on GB10, fetch 2026-10-13T05:07:45Z); origin rule = one raw record (paragraph-context signature; near-unique 2,467/2,479); build receipt `data/research/tatqa_wp0_2026/GENERATION_RECEIPT.json`: 182 origins, 176 with >= 2 usable rows, 60 candidate items from 60 distinct origins. Frozen facts and gate recommendations: `WP0_TATQA_QUALIFICATION_APPENDIX_v1.md` Sec.3-5.

## 4. Task contract (specification only)

- **Unit of submission:** one item = one table + one requested quantity.
- **Item schema:** `{item_id, origin_id, table, period_columns:[p_late, p_early], unit_column or unit_cell, row_selector, requested_quantity="increase/decrease", target_unit}`.
- **Reference target (gold):** recomputed independently from the source cells: `delta = value(late) - value(early)` on the selected row, rescaled to `target_unit` by the stated scale factor. Gold must be produced by a checker that reads only the table, never the actor's output.
- **Actor obligations:** choose the row, the two period columns, the unit relation and the arithmetic parameter; call a calculator tool; the answer must consume the tool's returned value.
- **Tool contract:** deterministic calculator, records inputs and output; no gold access; errors are recorded, not silently repaired.
- **Exclusions:** no growth rate, no multi-hop reasoning, no new domain, no long-horizon tasks.

## 5. Evaluation contract

- **Arms (frozen):** B no-experience; E 1-2 real executed episodes from *other* origins with independent feedback and actually-executed corrections; C matched unrelated experience (<=5% context-token delta); S static unit/period rules frozen at development.
- **Primary endpoint:** answer correctness including unit and period. Report `E-B`, `E-C`, `E-S`, and `C-B`; count corrections, regressions, refusals, UNKNOWN and cost.
- **Independent unit:** the origin (8 unseen for the pilot), not the 16 tasks and not the 32 repeats.
- **Scale / budget (blueprint):** pool 8 episodes from >=4 origins; development 4 tasks from >=2 origins; pilot 16 tasks from 8 unseen origins; 4 x 16 x 2 = 128 episodes; <=256 model calls; history+development <=40; retries <=4; **hard cap 300 request attempts; 0 judge calls**.
- **Gates:** `CONTINUE_EXPLORATORY` needs E-B and E-C each >= +12.5pp, >=3 net-positive origins each, no origin contributing >50% of its corrections, both repeats non-reversing, behaviour consistent. `STOP_THIS_PANEL` on leakage/bridge failure or a B ceiling. `UNDETERMINED` otherwise. `NEW_METHOD_NOT_NECESSARY_ON_THIS_PANEL` if S solves everything.
- **Anti-leakage:** test answers never enter experience; near-duplicate isolation across arms; context projections keep feedback and corrections intact for E and C.

## 6. Loop A executable work package (WP-0 completion, no experiment)

| # | Step | Deliverable | Check | Stop |
|---|---|---|---|---|
| A1 | Draft the TAT-QA `licence_record` (attribution text, modification note, revision binding) | `docs/datasets/tatqa_licence_record_v1.md` | CC BY obligations covered; revision pinned | if the owner narrows away from TAT-QA | **DONE** |
| A2 | Request and (if authorised) fetch the raw TAT-QA records; verify the file digests against the public release | acquisition receipt with hashes | hashes resolve; no private data | **needs owner authorisation** | **DONE** (authorised; receipt on GB10) |
| A3 | Build the origin rule (paragraph/coincidence grouping) and emit `origin_manifest.json` with >=8 origins | designer script + manifest | >=8 origins; near-duplicate isolation demonstrated on fixtures | if <8 origins emerge, report `SOURCE_INSUFFICIENT` | **DONE** (182 origins) |
| A4 | Instantiate the item schema on the 188-table feasible pool; produce a candidate item list (not a pilot) | `candidate_items_v1.json` | every gold recomputed by the checker, not by a model | if <16 eligible items survive, report | **DONE** (60 items / 60 origins) |
| A5 | Write the task-adapter + checker contracts (specification, no implementation) | `task_adapter_contract_v1.md`, `checker_contract_v1.md` | gold isolation; tool-consumption rule; deterministic fixture check | - | **DONE** (`WP0_TATQA_ADAPTER_CHECKER_CONTRACT_v1.md`) |
| A6 | Assemble the quality appendix for G-RQ / G-M | appendix in this package | unresolved dependencies listed | - | **DONE** (`WP0_TATQA_QUALIFICATION_APPENDIX_v1.md`) |

**Not in this package:** runner implementation (WP-1), any model call, any training, any pilot run (WP-2).

## 7. What still needs the owner

1. ~~Authorise the raw TAT-QA acquisition~~ -> **DONE** (fetch receipt 2026-10-13).
2. The feedback right: what historical feedback may be shown to the actor. [OPEN]
3. The actor revision freeze (MODEL_GO pending). [OPEN]
4. Bind the budget/window at the WP-1/WP-2 gate (300 attempt cap, 0 judge calls). [OPEN]

## 8. A6 appendix

See `WP0_TATQA_QUALIFICATION_APPENDIX_v1.md` for the frozen measured facts, the G-RQ/G-M recommendations, and the unresolved dependencies.

**No model call, no runner, no experiment, no training was performed. The only external action was the owner-authorised raw fetch (receipt above). This package does not authorise WP-1 or WP-2.**