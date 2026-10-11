[loop-c] start 2026-10-10T10:45:29Z
# Loop C Independent Audit — Graph Loop Meta-Retrospective & Governance Readiness

**Nature of document:** advisory audit report. Reports only; no repair performed.
**Audited object:** FinQA v2 formal-run failure chain, binding-v3 engineering qualification, and the governance layer added 2026-10-10 (`GRAPH_LOOP_AUTHORITY_MAP_V1`, `FORMAL_EXPERIMENT_PREFLIGHT_V1`, handoff template, preflight checker).
**Baseline (fixed before findings):** `docs/governance/audit/harness_audit_20260905/AUDIT_REPORT.md` F01–F10. Hits inside F01–F10 are reported as *family recurrences*, not new findings.

**Independence declaration:** Fresh context, Loop C, did not author any audited artifact. Reasoning chain was formed from raw artifacts, raw failure rows, and live re-execution **before** opening `graph_loop_meta_retrospective_2026-10-10.md` (read last, per independence order step 6). Mitigations actually executed: independent recomputation from raw rows rather than summary/receipt; positive-control injection against the guard; exhaustive multi-form search for negative conclusions. No self-graded artifact.

**Window accounting:** zero-endpoint, non-training. Model/endpoint/DB/training/scorer calls: **0**. Local read-only activity: pytest (local, `DEV_ONLY/NON_AUTHORITATIVE`), `docs_lint`, `git` read-only, in-process Python recomputation. No production service probed.

---

## 1. Verdicts

| Item | Verdict |
|---|---|
| Independent root-cause corrections | **4 corrections** (§3) — meta-retrospective incomplete, not wrong |
| Authority-map & state consistency | **FAIL** (dangling authority, zero recorded hashes, three different named blockers) |
| PASS-level vocabulary | **PASS** (complete, 6/6, consistent across 3 files) |
| PASS-level *usage compliance* | **FAIL** (bare `PASS` used; vocabulary itself forbids it) |
| Binding-v3 `RUNTIME_BINDING_INTEGRATION_GO` | **`YES` — `INTEGRATION_PASS`** (independently recomputed) |
| `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN` | **`NO`** |
| Remaining blocker | **one** — `END_TO_END_PREFLIGHT_PASS` unmaterialized and non-certifiable |
| Single owner | **Loop D** |
| **`VERDICT`** | **`CONDITIONAL`** |

Success exit is met on the second branch: the single remaining blocker is identified without overclaiming.

---

## 2. Root-cause tree (independently formed)

Scientific/data causes are **excluded by first-hand evidence**, not by assertion.

| Family | Cause | Class | Primary artifact / command |
|---|---|---|---|
| `SCIENTIFIC_DESIGN` | RQ/V/D/O/estimands frozen before any valid analysis attempt | **not a cause** | `finqa_v2_analysis_plan_hash_manifest.json` self-hash `b9899ad3…` verified OK; 13 bound_files |
| `DATA` | 89/30 population, IDs, split membership stable across both invalid runs | **not a cause** | recomputed: 216 candidate / 215 retained / 72 groups; E30·P30·N29 = 89; stage clusters 10/10/10 = 30 |
| `CONTRACT` | Raw provenance hash and normalized runtime hash collapsed into one field name | **primary → RUN1** | `run_finqa_v2_formal_experiment.py:538`; `finqa_independent_observation_scorer_v2.py:101-102` |
| `INTERFACE` | Runtime metadata never forwarded to the binding seam; adapter silently defaulted to `""` | **primary → RUN2** | `run_finqa_v2_binding_v2_rerun.py:254-259`; `binding_v2/finqa_v2_scorer_runtime_binding_v2.py:261-264, 294-298` |
| `TEST_COVERAGE` | 19 focused tests green while the composed runner→adapter seam was broken | **primary** | `results/finqa_v2_focused_preflight.log` (19 passed) vs 89/89 pre-scorer failures |
| `DOCUMENTATION` | Authority map cites a non-existent authority path; records no SHA-256 though preflight step 1 requires matching one | **contributing** | `GRAPH_LOOP_AUTHORITY_MAP_V1.md` |
| `STATE_MEMORY` | Three ledgers name three different "current blocker"; current status near-duplicated under a "Historical" heading | **contributing** | `STATE.md:105,108`; `THREADS.md:887-888`; `dispatch_log.md` tail |
| `ROLE_HANDOFF` | Handoff template omits 3 of the authority map's 8 mandatory fields | **contributing** | `SESSION_HANDOFF_TEMPLATE.md` vs `GRAPH_LOOP_AUTHORITY_MAP_V1.md` "Required Handoff Fields" |
| `GOVERNANCE` | Preflight checker admits silent-green bypasses; `END_TO_END_PREFLIGHT_PASS` never materialized | **primary (current blocker)** | positive-control probes below |

All nine families the contract requires are distinguished. This matches the meta-retrospective's tree shape (Required Check 1 **PASS**).

### Failure mapping (Required Check 2) — each with primary evidence

**RUN1 — `artifact_sha256_mismatch`, 89/89** → **`CONTRACT`** (hash-domain conflation)

Proven, not asserted. For `FINQA-V2-E-0ad6193ab515-03e9aee62934`:

```
manifest_artifact_sha256 (raw domain)        3d2b6c633fb7af47…   == binding_v3 raw_payload_sha256        True
scorer_payload_sha256   (normalized domain)  a5fef4593e12c15a…   == binding_v3 normalized_payload_sha256 True
equal to each other?                          False
```

The runner passed the **raw** manifest hash into the scorer's `artifact_sha256` field; the scorer validates that field against `artifact_hash(normalized_bound_payload)`. Two serialization domains, one field name. The scorer fail-closed correctly — the defect is the contract, not the scorer. All 89 rows share this shape (78 distinct hash pairs).

**RUN2 — `BINDING_TRACE_MISMATCH`, 89/89** → **`INTERFACE`** (`RUNTIME_METADATA_NOT_FORWARDED_TO_BINDING_SEAM`)

Reproduced end-to-end, field-exact:

```
metadata PRESENT (as in sample row): computed=4  mismatched_keys=0
metadata EMPTY  (silent '' defaults): computed=4 mismatched_keys=4
   diff cluster_id    expected="E:PNC/2007"  computed=""
   diff report_cluster expected="PNC/2007"   computed=""
   diff split_role    expected="evaluation"  computed=""
   diff stage         expected="E"           computed=""
```

Mechanism: `run_finqa_v2_binding_v2_rerun.py:255` passes `row["_score_payload"]` (keys: `artifact_sha256, clean, mutant, required_evidence_ids` — **no metadata**) into `adapter.score_pair`, which reads `record.get("split_role","")` etc. and so silently defaults all four to empty. `build_trace_rows` then emits 4 rows whose metadata fields are `""` while the frozen 994-row mapping holds real values → all keys mismatch on exactly those four fields. Keys were present (no `BINDING_TRACE_MISSING`/`UNEXPECTED`), which is why the error is `MISMATCH`. Sample rows *do* carry the metadata at top level — it was simply never forwarded.

**Scientific/data exclusion is affirmative:** 0 estimands, 0/10000 bootstraps, both `finqa_v2_bootstrap_replicates.jsonl` are 0 bytes, `PERMUTATION_TEST = NOT_USED`, denominators retained at 89/89 with `V/D/O=null`.

---

## 3. Independent corrections to the meta-retrospective

The diagnosis is **substantially correct** — its CONTRACT/INTERFACE/TEST_COVERAGE causes match mine exactly. Four gaps:

**C1 — `DOCUMENTATION` / Required Check 4: the authority map does not resolve, and cannot be checked.**
- Dangling authority: the Execution-scope row cites `research/finqa_v2_20261010/binding_v3/FINQA_V2_MINIMAL_RERUN_TASK_CARD.md`. That path **does not exist**; the file is at `…/binding_v2/FINQA_V2_MINIMAL_RERUN_TASK_CARD.md`. (Confirmed across name/short/alias search.)
- Zero SHA-256 recorded: `GRAPH_LOOP_AUTHORITY_MAP_V1.md` contains **0** 64-hex digests, yet `FORMAL_EXPERIMENT_PREFLIGHT_V1.md` checklist step 1 requires each authority path "exists and matches its recorded SHA-256". That check is **unexecutable as written**. The retrospective audits authority/memory but never verifies the authority map's own integrity.

**C2 — `GOVERNANCE` / Required Check 8: the preflight checker is silently green on five bypass classes and five empty-set paths.** Positive controls are present and do go red (`SILENT_DEFAULT_SOURCE`, `SCIENTIFIC_OUTPUT_EXISTS` both confirmed FAIL). But feeding known-bad inputs the tests never cover:

```
B1 .get(k,'evaluation') non-empty default  -> PASS   (should FAIL)
B2 .get(k, default='')  keyword form       -> PASS   (should FAIL)
B3 x.get(k) or 'evaluation'                -> PASS   (should FAIL)
B4 setdefault(k,'evaluation')              -> PASS   (should FAIL)
B5 empty hash_bindings                     -> PASS, 0 checks
B6 empty scientific_output_paths           -> PASS, 0 checks
B7 empty previous_invalid_runs             -> PASS, 0 checks
B8 empty expected_population               -> PASS, 0 checks
B9 empty expected_qualification            -> PASS, 0 checks
```

B1–B4 are silent-default *detection* holes (the AST scan only matches `.get(k, ""|None)`). B5–B9 are the baseline's F04 "checks that cannot fail" shape recurring: an empty result set masquerading as all-clear. Corroborating first-hand: `binding_v2`'s own `record.get("split_role","")` **is** the B1-family pattern, so the guard's blind spot is live code, not hypothetical.

**C3 — `GOVERNANCE`: `END_TO_END_PREFLIGHT_PASS` has never been materialized.** Exhaustive six-form search (full name / short name / `verification_level` key / `preflight_receipt|report|manifest` aliases / `END_TO_END` under `research/` / hidden dirs / `git ls-files`) returns **zero** preflight manifests or receipts. The only `*preflight*` artifacts are pytest logs (19 passed, 10 passed). `STATE.md` correctly holds `GOVERNANCE_READY=NO` pending this, but the retrospective's State Cleanup names a different blocker and never states that the artifact does not exist.

**C4 — `STATE_MEMORY` / Required Check 5: the ledgers do not name the same current blocker.**

| Ledger | Named current blocker |
|---|---|
| `STATE.md:105,108` | "v3 C audit **and** `END_TO_END_PREFLIGHT_PASS` are materialized" |
| `THREADS.md:887` | "`RUNTIME_BINDING_INTEGRATION_GO`" |
| `THREADS.md:888` | "C independently confirms **and** the preflight receipt is complete" |
| `dispatch_log.md` (tail) | none — asserts `FINQA-V2-BINDING-V3-QUALIFICATION -> PASS` |
| meta-retrospective `:102/:108` vs `:118` | `RUNTIME_BINDING_INTEGRATION_GO` vs three separate requirements |

Two distinct gates are used interchangeably as "the blocker". Additionally `dispatch_log.md` promotes bare `PASS` over an artifact whose own status is `QUALIFICATION_PASS_PENDING_LOOP_C_INDEPENDENT_REVIEW` — the chat/log-only promotion Required Check 5 forbids. And the three Loop C verdicts `docs/experiments/2026-10-10_loop_c_*.md` exist but are **absent from `docs/INDEX.md`** (0 hits), so by the authority map's own supersession rule they are not yet project state. The retrospective's claim that INDEX was not updated for binding-v3/C reports is **accurate** — I verified it.

Also verified precisely (not a byte-duplicate): `STATE.md:105` and `:108` are near-identical current-status paragraphs differing only by the word "now" (553 vs 549 chars), sitting under heading `## Historical objective context (2026-10-08)`.

**Baseline discipline (Required Check 3): PASS.** The retrospective fixes `harness_audit_20260905` as baseline (line 4) and names it as already identifying the same families (line 66); F01–F10 are not re-reported as new. My C2/B5–B9 and C4 are filed as **recurrences of the F04 and F07 families on new objects** (`formal_experiment_preflight.py`, current ledger set), not as fresh discoveries of those phenomena.

---

## 4. Required Checks 1–11 scorecard

| # | Check | Result |
|---|---|---|
| 1 | Root-cause tree distinguishes all 9 families | **PASS** (SCIENTIFIC_DESIGN/DATA/CONTRACT/INTERFACE/TEST_COVERAGE/DOCUMENTATION/STATE_MEMORY/ROLE_HANDOFF/GOVERNANCE all present) |
| 2 | Every FinQA failure mapped to correct family w/ primary artifact | **PASS** (my report supplies code sites + row-level hash proof; retrospective's Evidence column cited diagnosis *labels* for the CONTRACT rows) |
| 3 | harness_audit_20260905 as baseline, not re-reported | **PASS** |
| 4 | Authority map: one authority/object + explicit supersession | **FAIL** — supersession rules correct & explicit; but 1 dangling path, 0 recorded SHA-256 |
| 5 | STATE/THREADS/Dispatch/INDEX same blocker, no log-only promotion | **FAIL** — see C4 |
| 6 | PASS levels distinguish all 6 | **PASS** — 6/6 identical across `FORMAL_EXPERIMENT_PREFLIGHT_V1`, `TIERED_EVAL_PATTERN`, `SESSION_HANDOFF_TEMPLATE`. *Usage* FAIL: bare `PASS` and `SCORER_BINDING_GO = PASS` violate the vocabulary's own rule |
| 7 | Preflight doc covers the 11 items | **PASS** — authority version, hash domain, runtime metadata, IDs, split, scorer, analysis plan, seeds, integration dry-run, zero-output, previous-run immutability (+ handoff closure = 12) |
| 8 | Checker rejects silent defaults & scientific outputs in positive controls | **PARTIAL** — both named controls green→red confirmed; 9 bypass paths undocumented and open (C2) |
| 9 | Binding-v3 independently confirms the 8 properties | **PASS** — recomputed from raw rows + re-hashed (§5) |
| 10 | No frozen FinQA design/metrics/thresholds/split/source modified | **PASS** — 0 tracked files under `research/finqa_v2_20261010/` modified; `scripts/graph/frozen_hashes.txt` & `tests/test_m1_service.py` clean; analysis-plan manifest self-hash `b9899ad3…` OK |
| 11 | A/C/D handoff gaps documented + template updated | **PARTIAL** — template *was* updated (`AUTHORITY_REFS`/`IMMUTABLE`/`MUTABLE`/`PASS_LEVEL`/`PREFLIGHT_COMMAND`/`STOP_STATE`/`EVIDENCE_CLASS` present) but omits 3 of the authority map's 8: **assumptions**, **allowed/forbidden *actions*** (≠ claim boundary), **required output paths**. Residual gaps not disclosed |

---

## 5. Binding-v3 — `RUNTIME_BINDING_INTEGRATION_GO = YES` (`INTEGRATION_PASS`)

Independently recomputed from `finqa_v2_binding_v3_qualification_rows.jsonl` (not from summary/receipt):

| Required property | Independent result |
|---|---|
| Runtime bindings | **89 / 89** `binding_status=PASS` |
| Evaluation trace rows | **420 / 420** (sum of `trace_rows_expected`/`matched` = 420/420, mismatched 0; **independent** `len(trace_map)` key count = 420) |
| Four explicit metadata fields | **PASS** — `split_role, stage, cluster_id, report_cluster`; 89/89 non-null, non-empty, consistent |
| Silent defaults | **0** (summed from rows; `silent_default_count` all 0) |
| Identity / group / split drift | **0 / 0 / 0** |
| Leakage | **0** |
| Scientific outputs | **0** — filesystem scan finds only two 0-byte `finqa_v2_bootstrap_replicates.jsonl`; no estimand/V/D/O/observation-vector artifacts |
| Previous runs immutable | **PASS** — `results/` 12/12 and `results_binding_v2_rerun/` 12/12 byte-identical to receipt |

Supporting integrity: all **15** receipt hashes re-verified against file bytes (8 artifacts + 7 frozen inputs) — **15/15 OK**; receipt `self_sha256` `d85101d6…` recomputed **OK**. Stage bindings E30/N29/P30; report clusters E10/N10/P10 = 30. Corruption control → `RAW_PAYLOAD_HASH_MISMATCH`; four missing-metadata controls → `RUNTIME_METADATA_MISSING`; deterministic replay 89 equal rows. Pipeline stop boundary `BEFORE_SCIENTIFIC_SCORING`; `CONSTRUCTED_NOT_EXECUTED` ×89.

*Interface caveat (non-blocking):* the receipt declares no path base and uses two — `artifact_hashes` resolve under `binding_v3/` (test file under `binding_v3/tests/`), `frozen_input_hashes` under `research/finqa_v2_20261010/`. All resolve and all match; the ambiguity should be recorded.

This is **`INTEGRATION_PASS` only**. It does not imply `END_TO_END_PREFLIGHT_PASS` and does not authorize a formal run.

---

## 6. `GOVERNANCE_READY_FOR_NEXT_FORMAL_RUN = NO`

`STATE.md`'s own criterion is "the v3 C audit **and** `END_TO_END_PREFLIGHT_PASS` are materialized". The v3 C audit is now complete (this report). The preflight receipt **is not** — see C3. The checker that would certify it is not trustworthy — see C2. Therefore `NO`, without overclaiming.

**Remaining blocker (single):** `END_TO_END_PREFLIGHT_PASS` cannot be issued — the receipt has never been materialized, and `scripts/graph/formal_experiment_preflight.py` would certify a hollow manifest.

**Single owner: Loop D** (authority-map owner of Execution scope, Handoff and Current status). Sub-work: close the five detection bypasses and five empty-set silent-green paths in the checker; materialize the preflight manifest against the real 89/30 population; repair the Execution-scope authority path and add SHA-256 to the authority map so checklist step 1 becomes executable; add the three missing handoff fields; reconcile the blocker name across STATE/THREADS/Dispatch/INDEX and index the three Loop C reports.

---

## 7. Commands, hashes, counts, warnings

**Commands run (all local, read-only or test-only):**
```
PYTHONPATH=src ./venv/bin/python -m pytest research/finqa_v2_20261010/binding_v3/tests/test_finqa_v2_runtime_binding_v3_integration.py -q
PYTHONPATH=src ./venv/bin/python -m pytest tests/test_formal_experiment_preflight.py -q
PYTHONPATH=src ./venv/bin/python -m pytest tests/test_finqa_numeric_token_canonicalization_v2.py \
  tests/test_finqa_evidence_argument_resolver_v2.py tests/test_finqa_independent_observation_scorer_v2.py \
  tests/test_finqa_v2_execution_freeze.py tests/test_finqa_v2_scorer_runtime_binding_v2.py \
  tests/test_formal_experiment_preflight.py \
  research/finqa_v2_20261010/binding_v3/tests/test_finqa_v2_runtime_binding_v3_integration.py -q
python3 scripts/docs_lint.py --json /tmp/loop_c_docs_lint_report.json
```

**Test counts (fresh, this session):** binding-v3 integration **25 passed**; preflight **3 passed**; binding-v2 runtime **10 passed**; focused freeze/scorer/resolver/canonicalization **19 passed**; combined **57 passed in 0.48s** (19+10+3+25). All local — `DEV_ONLY / NON_AUTHORITATIVE`; GB10 remains authoritative.

**Warning list — `docs_lint`: `PASS (0 fail / 6 warn)`**, all six pre-existing staleness warnings: `docs/29_graph_engineering_roadmap.md`, `docs/32_模型升级与多agent再思考.md`, `docs/33_导师指导吸收_科研三线升级.md`, `docs/34_专利_小论文_大论文协同研究路线.md`, `docs/CLAUDE.md`, `docs/m1_coldstart_candidates.md`. One INFO (expected `DEPRECATED` registry row). Within the known-warning ceiling.

**Hashes (sha256, first 16):** HEAD `e97340387888290e` · authority map `a9e645b9cda647a9` · preflight doc `77e43f5921bcc3a1` · handoff template `38d490a2fa6f9456` · tiered-eval `2885416eaca36cd1` · preflight checker `766944b292db4bcb` · preflight tests `144a17033034a589` · binding-v3 receipt `fb0b3f4bad8c379d` (self `d85101d6…` OK) · binding-v3 summary `ef48caa482b602e6` · binding-v3 source `997d914fc1250f82` · STATE `237bd7295eda2c76` · THREADS `09bf6049ff6f2059` · INDEX `ce65c03ee3de73cd` · dispatch `3097710216f515c7` · analysis-plan manifest self `b9899ad304bf4a56` OK.

**Skill loading (per `SKILL_ROUTING` §5.3):** the contract named 8 skills; routing rule 3 caps a task at 5. Loaded **`audit-cycle`** only (the evidence-discipline layer this task is). Its anti-anchoring, positive-control and advisory-boundary clauses were applied directly; `self-eval-bias` and `verify-before-done` disciplines were applied inline rather than loaded. `systematic-debugging` / `experiment-autopsy` / `neat-freak` / `jinrong-docs-sync` / `offline-eval-playbook` **not loaded** — noted as un-loaded, per the over-equipment rule.

**Advisory boundary respected:** no audited object was modified, no repair applied, no frozen contract touched, no formal run executed or authorized. All findings are recommendations for the human owner's adjudication.

---

**`VERDICT: CONDITIONAL`** — binding-v3 engineering qualification independently confirmed at `INTEGRATION_PASS` (`RUNTIME_BINDING_INTEGRATION_GO = YES`); governance readiness **`NO`**; one blocker (`END_TO_END_PREFLIGHT_PASS` unmaterialized and non-certifiable), single owner **Loop D**.
