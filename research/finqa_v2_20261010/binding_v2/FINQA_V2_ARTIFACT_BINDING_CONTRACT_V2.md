# FinQA v2 Artifact Binding Contract V2

- Task: `finqa-v2-binding-repair-a-20261010`
- Namespace: `binding_v2`
- Scope: superseding engineering binding contract only; no scientific rerun
- Old run: `FORMAL_RUN_INVALID`
- Old scientific status: `SECOND_FLOW_INVALID`
- Loop C stop: independent audit before any formal rerun

## Root-Cause Decision

The frozen paired-artifact manifest binds the raw stored payload:

```text
raw_payload_sha256 = sha256(canonical_json(raw stored artifact))
```

The unchanged `score_pair` validates its runtime bound payload:

```text
normalized_payload_sha256 =
  sha256(canonical_json(score_pair bound_payload))
```

The scorer normalizes each step with `op_family`, canonicalizes step fields,
and sorts evidence IDs before hashing. The raw manifest hash therefore differs
from the scorer-runtime hash even when the stored artifact is unchanged.
All 215 frozen pairs and all 89 old evaluation failures replay this
`artifact_sha256_mismatch` without content or identity drift.

## Hash Domains

| Domain | Definition | Authority |
|---|---|---|
| `raw_payload_sha256` | SHA-256 of canonical JSON of the raw stored artifact | provenance / manifest binding |
| `normalized_payload_sha256` | SHA-256 of canonical JSON of the scorer bound payload | scorer runtime binding |

The adapter supplies `normalized_payload_sha256` to the unchanged scorer while
returning `raw_payload_sha256` separately. Neither hash is substituted for the
other, and no stored paired artifact is rewritten.

## Frozen Normalization

- Function: `finqa_independent_observation_scorer_v2.py::_normalized_steps + artifact_hash`
- Version: `finqa_v2_scorer_normalization_20261010_v1`
- Scorer source SHA-256: recorded in the JSON contract
- Replay: 215/215 pairs; 994/994 side-specific steps
- Raw `op -> op_family` full-match replay: 994/994

The normalization is deterministic and replayable. It is **not bijective**:
`add`, `divide`, `minus`, `multiply`, and `sum` collapse multiple raw op
variants into one family. The raw op identity remains recoverable through the
one-to-one trace mapping; the contract claims `BIJECTIVE_OR_TRACEABLE`, not
bijectivity.

## Trace Contract

Each mapping row records:

- source `artifact_id` and `sample_id`;
- `step_side`, zero-based `step_index`, and stable
  `trace_key = {artifact_id}::{clean|mutant}::{step_index:04d}`;
- raw and normalized step identity;
- raw and normalized step payload hashes;
- raw and normalized pair payload hashes;
- normalization function and version;
- split/stage/group metadata used only for linkage checks, never hash input.

The mapping contains exactly 994 rows: 497 clean steps and 497 mutant steps
across exactly 215 artifacts. Any missing, unexpected, duplicated, or
mismatched trace row fails closed.

## Required Invariants

The binding-v2 audit verifies:

- `DETERMINISTIC`: normalization and op-family replay are deterministic;
- `SEMANTICS_PRESERVING`: raw hashes, step counts, evidence, answers, and the
  frozen scorer measurement surface remain unchanged;
- `BIJECTIVE_OR_TRACEABLE`: every step has one raw-to-normalized trace key;
- `NO_LEAKAGE`: labels, outcomes, stage labels, split/group fields, result
  fields, and IDs are absent from hash inputs;
- `NO_SAMPLE_ID_CHANGE`: source, sample, artifact, split, and group membership
  remain invariant.

All five flags are `true`. If any is false or unverified, the required result
is `BINDING_REPAIR_NOT_AUTHORIZED`.

## Runtime Boundary

`finqa_v2_scorer_runtime_binding_v2.py` is the minimal adapter. It:

1. recomputes the raw provenance hash;
2. independently reconstructs the scorer-normalized payload hash;
3. validates the complete trace before calling the scorer;
4. passes only the normalized hash into unchanged `score_pair`;
5. returns both hashes and trace keys separately;
6. fails closed on corruption, missing trace keys, unexpected trace keys,
   mapping hash drift, or accounting drift.

Synthetic fixtures are used for adapter scoring tests. Frozen-pair hash
replay and mapping accounting are read-only; no new formal scoring is run.

## Preserved Invalid Run

The complete old `FORMAL_RUN_INVALID` run remains unchanged and is not
scientifically superseded. Its output hashes are frozen in the JSON contract
and checked by the binding-v2 tests. SOURCE/ID/JOIN/SPLIT populations,
memberships, metrics, thresholds, analysis plan, task card, sample IDs, result
files, and the old scorer are unchanged.

## Outputs

- `FINQA_V2_ARTIFACT_BINDING_CONTRACT_V2.md`
- `finqa_v2_artifact_binding_contract_v2.json`
- `finqa_v2_raw_normalized_mapping.jsonl`
- `finqa_v2_normalization_audit.json`
- `finqa_v2_scorer_runtime_binding_v2.py`
- `tests/test_finqa_v2_scorer_runtime_binding_v2.py`
- `finqa_v2_binding_v2_reproduction.log`
- `finqa_v2_binding_v2_tests.log`
- `finqa_v2_binding_v2_receipt.json`

This repair stops at Loop C independent audit. It does not authorize a
formal rerun.
