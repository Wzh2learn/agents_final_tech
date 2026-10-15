[loop-c] start 2026-10-15T12:29:46Z
All checks are complete. Per the prompt's own constraint (`GOAL`: "do not change any file"; `FORBIDDEN`: "no edits"), I am **not** writing `V4_LOOP_C_POSTRESULT_AUDIT_v1.md` — the full audit follows inline.

---

# V4 Loop C — Post-Result Independent Audit

**Role:** Loop C independent auditor · read-only · zero model/judge/network/training calls
**Independence:** label derivation implemented from contract text + raw frozen inputs only; `run_v4.py` was never imported. It was read *after* derivation solely to audit freeze ordering (CHECK 5).

## 1. Pin hashes — all match

| Artifact | Pinned | Actual | |
|---|---|---|---|
| `LAYER1_V4_COMPACT_CONTRACT_v3.json` | `322c3b38…8aa` | `322c3b38…8aa` | OK |
| `run_v4.py` | `55893b65…8d4` | `55893b65…8d4` | OK |
| `V4_RESULTS_v1.json` | `b412c3cb…7d2` | `b412c3cb…7d2` | OK |
| `V4_RECEIPT_v1.json` | `e2123cc5…7b7` | `e2123cc5…7b7` | OK |
| `V4_HELDOUT_LABELS_FROZEN_v1.json` | `c17e31af…6cf` | `c17e31af…6cf` | OK |

Contract-declared raw inputs also verified: `injection_map` `d7612405…`, `tatqa_tables` `3e7e0568…`, `injected_tables` `827092cf…`, `checker_target` `eff82b0b…`, `v1_results` `359c7c04…` — **all match**.

## 2. Independent re-derivation of the 59 held-out labels — 0 mismatches

Re-derived from contract text (norm = NFKC → casefold → P\* / `string.punctuation` → space → collapse → strip; unit-cost Levenshtein; guard precedence `header_non_string > injected_header_empty > source_header_empty_col_local > source_header_collision_col_local > equality/unique-nearest > tie`).

| Field | Mismatches / 59 |
|---|---|
| `label` | **0** |
| `reason` | **0** |
| `binding` | **0** |
| `nearest_distances` | **0** |
| id set vs frozen | **exact** |

Re-derived reason counts: `unique_nearest_neighbour_target` 29, `unique_nearest_neighbour_other_column` 18, `nearest_neighbour_tie` 9, `source_header_canonical_collision_column_local` 3. Provenance (`source[uid][col]==original`, `injected[uid][col]==injected`) passed 59/59.

Semantics cross-checked against the frozen fixtures (F9 confirms collision outranks equality; F2/F7 confirm non-empty candidates only) — consistent, and the derivation did not depend on them.

## 3. Recomputed rates — all match exactly

| Quantity | Recomputed | Reported | |
|---|---|---|---|
| E / H / U | 29 / 18 / 12 | 29 / 18 / 12 | OK |
| `u_rate_heldout` | 12/59 = `0.2033898305084746` | same | OK (bit-exact) |
| gate | ≤0.30 → `GOLD_ESTABLISHED_ON_HELDOUT` | same | OK |
| visible E/H/U | 19 / 17 / 12 (n=48) | same | OK |
| blind E/H/U | 10 / 1 / 0 (n=11) | same | OK |
| `co_miss` | 1/11 = `0.09090909090909091` | same | OK |
| `co_alarm` | 19/48 = `0.3958333333333333` | same | OK |

Visibility taken from the checker's `visible_frozen`, joined on `(uid, col)`; join verified faithful (original/injected/type agree on 59/59) and reproduces the per-row `checker_verdict` field with 0 mismatches. *(A bare `Counter` drops zero-count keys — my first pass printed "CONTINGENCY MATCH: False" for that reason alone; zero-filling reproduces the reported table exactly.)*

## 4. Held-out only — confirmed

118 injections = 59 held-out + 59 dev. All 59 case rows are `split: "heldout"`; the frozen file matches the results id set exactly. **Zero dev `injection_id` occurrences in any v4 artifact.** The decision metric is held-out-only by contract (`label_scope: heldout_only`, `dev_label_policy: not_used`).

## 5. Checker read after freeze — confirmed at code and byte level

`run_v4.py` ordering:

```
320  check_inputs(contract, skip=("checker_target",))   # checker explicitly excluded
336  labels_json = json.dumps(rows, ...)
337  labels_sha  = sha256_bytes(labels_json)
339  frozen.write_bytes(labels_json)                    # FREEZE WRITTEN
342  if sha256_file(checker_path) != ...                 # checker hashed only now
344  checker = load_json(checker_path)                   # checker read only now
353  row["checker_verdict"] = checker_lookup[key]        # joined after freeze
```

The checker is read at exactly one site (line 344); every earlier mention is the deliberate `skip`. Structural corroboration: the frozen file's bytes are **byte-identical** to the results rows with only `checker_verdict` removed (`sort_keys=True`, compact), and the frozen rows carry no `checker_verdict` key.

## 6. Mismatches

**No label mismatch. No arithmetic mismatch. No counterexample.**

## 7. Claim boundary — confirmed

`V4_SUMMARY_v1.md:12` and `V4_RESULTS_v1.json.boundary` both state the disclaimer verbatim: descriptive held-out feasibility only; no population, OCR, or harmful-blind-spot claim. A scan for population/generalization/real-world-OCR/blind-spot/guarantee language found no claim outside those disclaimers.

## Non-blocking notes

**N1 — `injection_id_definition` underdetermines `ensure_ascii` (reproducibility pin gap).** The contract says `json.dumps` of the seven fields without specifying encoding. The two readings diverge, and Chinese characters in `injected`/`variant` make this material:

| Reading | held-out / dev | id set vs frozen |
|---|---|---|
| `json.dumps` default (`ensure_ascii=True`) | **60 / 58** | **differs** |
| `json.dumps(..., ensure_ascii=False)` | 59 / 59 | exact |

Counterexample: entry `uid=b48bb5fb…`, `injected="income(收入)"` — the default reading emits `income(收入)`, the frozen artifacts contain the literal characters. Only `ensure_ascii=False` reproduces the pinned 59. The frozen artifacts fully determine the sample, so **no re-run is needed**; but a reader re-deriving from the contract text alone would select a different 60-row set.

**N2 — rows are clustered, not independent.** 24/59 held-out rows sit on tables with >1 changed header cell; 17/59 come from tables carrying >1 held-out injection (multi-injection tables share one injected header row). Labels are unaffected (provenance passed on all 59; the candidate set is the *source* header row), but `u_rate_heldout` is a clustered sample rate. The existing boundary already forbids a population reading, which is exactly the exposure this creates.

**N3 — `value_invariant` means data-region invariance.** Header row excluded. Verified: 0 data-region cell differences across all 59. Column hashes reproduce 59/59 under `json.dumps(values, ensure_ascii=False, separators=(",",":"))` over rows ≥ 1; `clean_column_sha256 == injected_column_sha256` on all 59; `clean_value_count == n_rows - 1` on all 59. *(Whole-column comparison including the header shows 24 rows with differences — expected, and not a defect.)*

**N4 — `checker_read_policy` names the table shape but not the visibility field.** The runner uses `visible_frozen`. `visible_by_gamma["0.2"]` would yield visible E=16 H=17 U=9 / blind E=13 H=1 U=3 — a different table. The reported `co_miss`/`co_alarm` match `visible_frozen` exactly; worth naming the field in the contract.

---

**Bottom line:** every number and every one of the 59 labels verifies exactly, from contract text and raw inputs, with the runner uninvolved. Freeze ordering is genuinely clean — the checker cannot have influenced any label. The single defect is a documentation pin: `injection_id_definition` should record `ensure_ascii=False` before this is cited as independently reproducible from the contract text alone. That is a one-line contract-text fix; it does not touch any result.

**VERDICT: CONDITIONAL**
*Condition: pin `ensure_ascii=False` in `injection_id_definition` (N1). No result, label, or rate change is required or recommended; no re-run needed.*
