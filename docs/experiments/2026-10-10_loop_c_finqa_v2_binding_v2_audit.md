[loop-c] start 2026-10-10T09:04:36Z
All checks are complete and triangulated. Zero-endpoint confirmed (`endpoint_calls=0, model_calls=0, training_runs=0, frozen_pairs_scored=0`). Old run: 12/12 immutability digests match, `superseded_scientifically=False`. My independent conclusions were formed before reading Loop A's and match exactly. Here is the complete audit report.

---

# FinQA v2 Binding V2 — Independent Audit (Loop C)

**Nature of document.** Advisory independent audit report. It reports and recommends; it does **not** repair, and it does not adjudicate. No artifact was modified.

**Audited object & baseline.** The `research/finqa_v2_20261010/binding_v2/` repair (Loop A) and its claim that the old invalid run's raw/normalized `artifact_sha256` mismatch is *only* a deterministic serialization/normalization contract mismatch. **Baseline known anomaly:** the old formal run failed closed with 89/89 `artifact_sha256_mismatch` (`run_status=FORMAL_RUN_INVALID`). Anything outside that baseline is a new finding.

**Independence declaration.** Fresh-context Loop C. I did **not** build any artifact under audit (Loop A did) — this is not a self-audit. Independence order was enforced: (1) I read the raw frozen paired-artifact manifest and the **unchanged** scorer source first; (2) I independently recomputed raw + normalized hashes and the 994-step map in `/tmp` **before** opening any Loop A conclusion; (3) I exercised positive controls against the guard; (4) I inspected source for leakage/semantics; **only then** (5) did I read Loop A's contract / mapping / receipt / normalization-audit and compare. **Prior-conclusion ingestion disclosed:** Loop A's decision flags, root-cause text, and accounting were read at the final comparison step only, after my chain was formed; the binding_v2 *source* (implementation) was read mid-audit to design positive controls — it contains no decision flags. Early reads were limited to the old run's failure log and status fields (the baseline premise stated in the task). My independent numbers match Loop A's exactly (215/215 hashes, 994/994 steps) — agreement is reported as corroboration, not manufactured as a finding.

---

## 1. Root-cause classification

**`RAW_NORMALIZED_HASH_DOMAIN_MISMATCH` — an engineering hash-binding (contract) mismatch. Confirmed first-hand.**

Two different byte-serializations are hashed under one field name `artifact_sha256`:

| Hash domain | Definition (canonical JSON, `sort_keys`, compact, `ensure_ascii=false`) | Where it lives |
|---|---|---|
| **Raw** | `sha256(canonical_json(raw stored artifact))` — steps carry **`op`** | frozen manifest `artifact_sha256` (provenance) |
| **Normalized** | `sha256(canonical_json(score_pair bound_payload))` — steps carry **`op_family`** | unchanged scorer's runtime `artifact_sha256` check |

I independently reproduced both: raw hash `== manifest.artifact_sha256` on **215/215**; normalized hash triangulated across **three** implementations (my recompute / unchanged `score_pair` / binding_v2 `normalized_payload_from_record`) on **215/215**. The entire byte delta on all frozen inputs is the step field `op → op_family`; evidence sorting, required-order preservation, and answer coercion are **no-ops** (I measured 0 reorderings, 0 coercions, 0 value drift). The scorer verifies `artifact_sha256` against the *normalized* payload while the manifest stored the *raw* payload hash — so every call failed closed with `artifact_sha256_mismatch`. Not a data or semantic defect.

## 2. Engineering-binding-bug verdict

**TRUE — this is an engineering binding bug, not a scientific invalidation.** The frozen data, scorer, estimands, and memberships are sound; only which hash is bound/checked was inconsistent. Repairable at the binding layer without touching any frozen payload or the scorer (verified: scorer `sha256` unchanged = `b48ed17c…667e5`, matching the contract's recorded digest).

## 3. Decision flags (independently assigned)

| Flag | Verdict | First-hand basis |
|---|---|---|
| **DETERMINISTIC** | **TRUE** | Two independent replay passes → identical 215 normalized hashes; `op_family` pure over 994 ops; 3-way triangulation 215/215. `sorted()` + `sort_keys` eliminate iteration-order nondeterminism. |
| **SEMANTICS_PRESERVING** | **TRUE** | 0 value drift on `arg1/arg2/res/answer`; 0 non-str coercions; evidence-id **set** preserved (0 reorderings). Measurement object unchanged — the scorer natively measures at `op_family` grain (`operator_consistency` compares `op_family`), so normalization aligns to the scorer's own semantics rather than altering them. |
| **BIJECTIVE_OR_TRACEABLE** | **TRUE (via TRACEABILITY — explicitly NOT bijective)** | `op→op_family` is **lossy**: 35 raw ops → 6 families; 5 families collapse variants (add 8, divide 9, minus 8, multiply 7, sum 2); 992/994 steps sit in lossy families. Raw identity remains fully recoverable via `trace_key = artifact_id::step_side::step_index` (994 unique keys, one row/step, `raw_step_identity` retained). Do **not** call this bijective. |
| **NO_LEAKAGE** | **TRUE** | Normalized payload = `{required_evidence_ids, clean{evidence_ids,steps,answer}, mutant{…}}` only. 215/215 exclude `artifact_id/sample_id/label/outcome/stage/split/group/result`. Raw payload strips runtime metadata. Scorer `label_blind=True`; `answer` is a measured observation input, not an experimental outcome. |
| **NO_SAMPLE_ID_CHANGE** | **TRUE** | `sample_id` is runtime metadata, **not** in the raw or normalized hashed payload; normalization cannot touch it. Identity is bound at the trace/manifest layer; positive control 5a proves a changed `sample_id` is rejected. |

## 4. Exact accounting — 215 pairs / 994 steps

- **215** frozen retained pairs (216 candidate injections − 1 excluded-before-split). ✅ exact
- **994** step instances = **497 clean + 497 mutant** (equal per pair; scorer enforces step-count parity). ✅ exact
- **994 unique trace keys**, format `artifact_id::(clean|mutant)::NNNN`, one row per step, 215 distinct artifacts. ✅ exact
- Independent map equals Loop A's mapping **994/994** (raw op, op_family, arg1/arg2/res, trace_key). ✅
- Old-run denominator preserved separately: 89 attempted evaluation records → 89 scorer failures, 0 successes (not part of the 215 scored set).

## 5. Semantic-preservation evidence

- arg/res/answer string identity: **0** differences between raw and normalized (`str()` coercion is identity on these all-string fields).
- evidence_id **set** preserved on every side; only byte order is canonicalized, and all sides were already sorted (0 reorderings).
- required_evidence_ids order preserved (the scorer's `required` list keeps source order).
- Measurement surface unchanged: normalization reuses the scorer's own `_normalized_steps` + `artifact_hash` verbatim; scorer file byte-identical to its frozen digest.
- Raw stored artifacts, split/group membership, and stage/label/outcome/result fields are untouched and excluded from both hashed payloads.

## 6. Positive-control results (injected, each must fail closed)

Built a clean record + expected trace rows, then injected one corruption at a time against the real binding seam:

| # | Injected corruption | Guard response | Fail-closed? |
|---|---|---|---|
| 1 | Corrupted raw payload (tampered arg) | `RAW_PAYLOAD_HASH_MISMATCH` | ✅ |
| 2 | Corrupted normalized payload / step hash | `BINDING_TRACE_MISMATCH` | ✅ |
| 3 | Missing trace key (row dropped / blank key) | `BINDING_TRACE_MISSING` / `EXPECTED_TRACE_KEY_MISSING` | ✅ |
| 4 | Unexpected trace key (extra / duplicate) | `BINDING_TRACE_UNEXPECTED` / `EXPECTED_TRACE_KEY_DUPLICATE` | ✅ |
| 5 | Changed sample / group ID | `BINDING_TRACE_MISMATCH` (via `score_stored_pair`) | ✅ |

**Negative control:** an unchanged record correctly **passes** (the guard is not trivially "always fail"). **9/9 controls fail closed.**

*Honest artifact:* my first attempt at control #5 reported "fail-open" — that was **my harness error** (I called `score_pair` and passed the original `sample_id` as an argument while only tampering the record field; `score_pair` trusts the caller's `sample_id`). Re-tested at the real `score_stored_pair` seam (which reads `sample_id` from the record), changed sample/group ID **does** fail closed (5a/5b/5c). The corrected result is what stands.

## 7. Inherited gates (valid without re-freeze)

Frozen and unchanged — the rerun inherits these: frozen **sample** / **split** / **paired-artifact** / **scorer-binding** manifests; the **unchanged scorer**; the **analysis plan** and frozen **estimands**; metrics/thresholds; **SOURCE/ID/JOIN/SPLIT** populations and memberships; the **old invalid-run results** (immutability verified: 12/12 recorded digests match current bytes, `failure_hidden_or_removed=False`, `superseded_scientifically=False`).

## 8. Gates requiring a new freeze

- **Freeze the binding_v2 layer** as the authoritative engineering binding before the rerun: `finqa_v2_artifact_binding_contract_v2.json`, `finqa_v2_raw_normalized_mapping.jsonl`, and the runtime adapter — hash-pinned (contract already records `mapping_sha256` / `input_sha256`).
- The **minimal formal rerun's own outputs** (scorer observation vectors, frozen estimands, bootstrap) must be freshly frozen with a new execution receipt — scope strictly limited to **formal scorer + frozen estimands + bootstrap**.
- Mandatory handling condition: **retain the raw↔normalized trace map** for the life of the analysis (it is the only bridge across the lossy `op→op_family` collapse). Already satisfied by the current mapping.

## 9. `SCORER_BINDING_GO = PASS`

All five flags independently TRUE; deterministic; fail-closed controls 9/9; exact 215/994 accounting; scorer unmodified; old run intact & unsuperseded; zero frozen-pair scorer output produced during repair (`frozen_pairs_scored=0, new_formal_scoring_calls=0, endpoint_calls=0, model_calls=0, training_runs=0`).

## 10. `VERDICT: PASS`

The binding-v2 repair is **authorized for a minimal formal rerun limited to the formal scorer, frozen estimands, and bootstrap.**

## 11. Scientific reason

The raw/normalized hash mismatch is a **deterministic, semantics-preserving, leakage-free, sample-identity-preserving serialization/normalization contract mismatch between two documented hash domains** — an engineering binding bug, not a scientific defect. The frozen pairs, split/group memberships, estimands, and the measurement object are unchanged and remain valid; the old invalid run is preserved and unsuperseded (`scientific_status=SECOND_FLOW_INVALID`, `superseded_scientifically=False`). Because the defect is confined to which hash is bound/checked, reconciling it (as binding_v2 does — binding both raw and normalized hashes) does not alter any scientific quantity, so a minimal formal rerun on the frozen estimands is scientifically justified. The rerun must not interpret the observation vector as semantic correctness: the scorer sets `semantic_correctness_claim=False`, and the claim boundary forbids visibility/hierarchy/localization transfer claims.

## 12. Strongest counterexample / failure scenario

**Lossy `op→op_family` collapse is non-injective.** Two distinct raw operators that share a family (e.g. `add1-1` vs `add2-3`) with identical `arg1/arg2/res` normalize to **identical** steps; 992/994 steps live in lossy families. Consequently:

- If the raw↔normalized **trace map is discarded**, or a consumer treats the normalized `op_family` as the raw operator, raw operator identity **silagently collapses** and cannot be recovered from the normalized payload alone. A mutation that swaps a raw op *within* the same family (e.g. `add1-1`→`add2-1`) changes the **raw** hash but leaves the **normalized/scorer** hash identical — invisible to the scorer-hash check alone.
- **Mitigation (verified present):** the binding binds **both** hash domains (raw catches the intra-family swap via `RAW_PAYLOAD_HASH_MISMATCH`), retains `raw_step_identity` per 994 unique trace keys, and documents `bijective=false / lossy=true`. The repair is safe **only while the trace map is retained and `op_family` is never reported as the raw operator**.

This is a documented, mitigated caveat — not a blocker to authorization. It is filed as a standing handling condition (§8), not as a new defect.

---

**Anomaly dispositions (audit-cycle step 5).** *Already in baseline (known):* the `artifact_sha256_mismatch` / `RAW_NORMALIZED_HASH_DOMAIN_MISMATCH` defect itself. *Waivable / documented (verified correctly labeled, not a finding):* lossy `op→op_family` collapse (`bijective=false` asserted in the contract). *Needs new filing:* none — zero new anomalies; confirming the repair is sound is a legal result.

**Boundary respected.** No artifact repaired or modified; no frozen pair scored as a formal experiment; SOURCE/ID/JOIN/SPLIT untouched; stored payloads not normalized; old invalid run preserved and not hidden; traceability reported as traceability, never as bijectivity. **Zero-endpoint, non-training** reconfirmed (`endpoint_calls=0, model_calls=0, training_runs=0`). All scratch computation ran in `/tmp` only.

Adjudication of this recommendation belongs to the human owner.
