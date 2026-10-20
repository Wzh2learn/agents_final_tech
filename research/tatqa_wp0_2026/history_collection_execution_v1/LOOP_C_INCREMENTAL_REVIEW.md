# Loop C Incremental Review — COLLECTION_EXECUTION_READINESS

- Task id: `collection-execution-readiness-review-20261018-r1`
- Reviewer role: Loop C independent reviewer (bounded, read-only, incremental)
- Review date: 2026-10-18
- Scope: `research/tatqa_wp0_2026/history_collection_execution_v1/` and its pinned input identities only
- **Verdict: `CONDITIONAL`**
- **Blocker count: 2 (NOT zero)**

**Online collection remains unauthorized.** This review grants no authorization and makes no request.

---

## 1. Verdict summary

| Required check | Result |
|---|---|
| Actor-visible task free of UID / cluster ID / source item ID / rank / hidden reference | **PASS** (0 findings) |
| Actor-visible task free of **gold** | **FAIL** — 4 of 12 executed history tasks expose the answer in an evidence column (BLOCKER-2) |
| References independently recomputed; gold not used for ordering | **PASS** (32/32) |
| Adapter/requests gated behind valid authorization (bundle hash + window) | **PASS** |
| Raw overwrite / crash terminal / request identity / budget caps enforced | **PASS** |
| Invalid output paths enforced | **FAIL** — one reachable uncaught exception aborts the run (BLOCKER-1) |
| Fixture adapter clearly non-generative, not a scientific result | **PASS** |
| Proposed window is a proposal only; no request or service start | **PASS** |

---

## 2. Mechanical recomputation performed

All findings come from independent recomputation against the pinned inputs, not from reading the package's own claims. No reviewed file was modified.

| Artifact | Check | Result |
|---|---|---|
| `TASK_REFERENCE_MANIFEST.json` | counts 12/16/4 + 3 fixtures | 32 tasks + 3 fixtures, matches declared |
| | selection_rank = `sha256(seed:bucket:cluster_id:item_id)` | 32/32 recomputed equal |
| | selection order ascending by rank within cluster | 22/22 clusters OK |
| | `selection_position` = rank order index | 32/32 OK |
| | uniqueness / isolation | no duplicate source items; no UID or cluster spans buckets |
| | references recomputed from actor evidence only | 32/32 `delta = late - early`, exact |
| | candidate gold agreement flag | 32/32 correct, `REFERENCE_RECOMPUTED` |
| pinned inputs | `candidate_items_v2.json` sha256 | **MATCH** (`5f61f2a4…38aa`) |
| | `history_collection_offline_v1/SPLIT_PROPOSAL.json` sha256 | **MATCH** (`287b6c6a…0e72`) |
| | 32 selections vs candidate pool + split placement | 0 issues |
| | `qualified_candidates` per (bucket, cluster) | 22/22, pool size exactly 2 |
| `EXECUTION_PLAN.json` | 54 unique request keys | 54/54 unique; 27 plan + 27 consume |
| | 48 history + 6 fixture | 12 history × 2 attempts × 2 stages = 48; 3 fixtures × 2 = 6 |
| | budget 54 / 600000 / reserve 10240 / retry 0 / concurrency 1 | matches plan, policy, bundle, and authorization schema |
| `RUNTIME_IDENTITY_SNAPSHOT.json` | server binary sha256 recomputed | **MATCH** (`037e0241…bd55d`) |
| | model artifact | exists; size matches pinned bytes (21,166,757,728). 21 GB sha256 **not** recomputed — see N-5 |
| | tokenizer binding | `embedded_in_model_artifact`, bound by model sha256 — consistent |
| | all 8 `checks` | all true |
| `PRE_COLLECTION_EXECUTION_BUNDLE.json` | 22/22 artifact hashes | **all MATCH** |
| | receipt `implementation_hashes` / `test_hashes` (local + GB10) | **all MATCH** |
| | `RUNTIME_IDENTITY_SNAPSHOT.artifact_hashes` | **all MATCH** |
| tests | local re-run of `tests/test_execution_v1.py` | 11 ran, 0 failures, 0 errors |

Selection determinism is genuine: the rank key is `sha256(TASK_SELECT_SEED:bucket:cluster_id:item_id)`. Gold is used only as a validity filter, never as an ordering key.

---

## 3. Actor/hidden isolation

The hidden record holds `source_item_id`, `source_uid`, `source_cluster_id`, `selection_rank`, `selection_position`, `row_index`, period column indices, and `reference`. None appear in `actor_task`, as key or value.

Independently scanned every `actor_task` JSON blob for forbidden identity/reference tokens and hidden identity values: **0 findings across 32 tasks**. `actor_task.item_id == task_id` for all 32. The runner never renders `task["hidden"]` into a prompt.

Identity isolation passes. Gold does not — see BLOCKER-2.

---

## 4. Runtime identity and authorization gating

`RUNTIME_IDENTITY_SNAPSHOT.json` is hash/parse-only, binding model id + path + sha256, the embedded tokenizer via the model sha256, chat template sha256 + length, the llama-server binary sha256 + bytes, generation policy, and limits. All eight self-checks true; `blockers` empty.

Gating order in `collection_runner.main()` is correct:

1. `verify_bundle(...)` requires no blockers, ready status, and every artifact hash.
2. `preflight` returns with `model_calls: 0`.
3. `execute` requires authorization and raw root.
4. `validate_authorization(...)` binds bundle hash, caps, timezone, duration, and active UTC window.
5. Only then is `HttpChatAdapter` constructed.

Independently reproduced: with the current bundle, `verify_bundle` raises `ValueError: bundle_has_blockers`. No `EXECUTION_AUTHORIZATION.json` exists.

---

## 5. Persistence, budget, and output-path enforcement

`ImmutableRawStore` re-verification passed:

- Raw overwrite prohibited.
- Crash is terminal.
- Request identity is enforced.
- Path traversal and invalid IDs are rejected.
- Budget construction/reserve/settle caps are enforced.
- Produced request keys must equal all 54 planned keys in exact order.

Strict JSON rejects unknown keys, non-finite answers, missing explicit nulls, oversized bodies, and booleans where numbers are required. The calculator is AST-whitelisted.

---

## 6. Blockers

### BLOCKER-1 — `ZeroDivisionError` escapes the invalid-output handler and aborts the whole run

`execution_core.evaluate_expression` maps `ast.Div` to `operator.truediv`. Division by zero raises `ZeroDivisionError`, while `collection_runner.run_attempt` catches only `ValueError`.

Reproduced with an in-process stub adapter:

```text
RUN_ABORTED -> ZeroDivisionError float division by zero
adapter calls made: 1
budget snapshot: {"requests": 1, "reserved_tokens": 0, "actual_tokens": 2, ...}
results recorded: 0
raw request dirs: 1
EXECUTION_RESULT.json written: False
```

This blocks because one malformed plan consumes a request and unwinds the single-shot run before remaining slots execute.

Targeted fix: contain arithmetic exceptions as `INVALID_PLAN` / `TOOL_ERROR`, rerun affected tests, and regenerate hashes.

### BLOCKER-2 — actor-visible evidence contains the gold answer for 4 of the 12 executed history tasks

The faithful two-row projection includes precomputed change columns equal to the requested signed difference:

| task | non-period column | actor-visible cell | gold delta |
|---|---|---|---|
| H03 | `Change` | `(0.4)` | -0.4 |
| H07 | `$ CHANGE` | `86` | 86 |
| H08 | `Change` | `(48.9)` | -48.9 |
| H12 | `Change` | `(11.9)` | -11.9 |

This is source-content answer leakage, not hidden-field leakage. It contaminates arithmetic measurement for one third of the executed history arm.

Targeted fix: project only `row_label` and the two period columns, rerun isolation tests, and regenerate manifest/bundle hashes.

---

## 7. Non-blocking notes

- **N-1** — `IMPLEMENTATION_PLAN.md` is stale.
- **N-2** — chronologically inverted period labels in four future tasks; no effect on the 54-slot history run.
- **N-3** — budget does not explicitly track outstanding reservations; current call path settles once.
- **N-4** — authorization window is not cross-checked against `COLLECTION_WINDOW_PROPOSAL.json`.
- **N-5** — this review did not recompute the 21 GB model hash; the runtime builder did.
- **N-6** — `hidden_reference` remains in `EXECUTION_RESULT.json` under `raw_root`, which must never be actor-visible.

---

## 8. Zero-call accounting for this review

| kind | count |
|---|---:|
| model calls | 0 |
| endpoint / network calls | 0 |
| judge calls | 0 |
| training calls | 0 |
| collection / pilot calls | 0 |
| service starts | 0 |

Only in-process stub adapters and local tests were used. The proposed 2026-10-19 20:00–21:30 Asia/Shanghai window remains a proposal.

---

## 9. Fixture adapter assessment — PASS

The three fixtures are hard-coded synthetic rows, use the same independent-reference path, and are not drawn from TAT-QA. Their adapter calls are non-generative and separately accounted.

---

## 10. Required disposition

- **Blocker count: 2 — NOT zero.**
- **BLOCKER-1**: uncaught `ZeroDivisionError`.
- **BLOCKER-2**: gold answer visible in actor evidence for 4/12 history tasks.
- **Verdict: `CONDITIONAL`.**

Both blockers are narrowly fixable and need targeted re-check only. This is contract-scoped mechanical verification, not human semantic gold. **Online collection remains unauthorized.**
