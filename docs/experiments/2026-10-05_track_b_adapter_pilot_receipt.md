# Track B within-origin process adapter pilot receipt（2026-10-05）

> Status: `TRACK_B_WITHIN_ORIGIN_PILOT_ARTIFACT_CLOSED / CORRECTNESS_NOT_RUN`
> Evidence level: exploratory only
> Dataset revision: `5d5163f04da304985bd51a476ccf7653de3979c3`
> Boundary: no confirmatory RQ2, Stage D, Stage R, RQ4, training, or full E-D-R claim

## 1. Input and implementation

The pilot uses the existing 10 NYC trajectory pairs in the approved GB10 staging root:

- staging root: `/home/testuser/wzh/phase1a_staging_20260925`
- input SHA-256 manifest: `c11d26f8fe58ea13b443bd4be8c7f946fa53778f84dc360f929060a7e46ba7dd`
- input bytes manifest: `cb217c0e0af50ae00689d4441b5ee633e561818fb536621c023153ab6135cbdb`
- adapter: `research/valentine_process_checkpoint_adapter.py`
- adapter contract: `valentine-process-checkpoint-adapter-v1`
- focused adapter tests on GB10: `11 passed`

The adapter reads source/target headers, `<pair>_full.json`, and `<pair>_trajectory.json`. `ground_truth.json` and `_result.json` are presence-only inputs. The outputs record `ground_truth_read=false`, `embedded_gold_exposed=false`, `source_gold_used_for_correctness=false`, `correctness_status=NOT_RUN`, and `paper_result=false`.

## 2. Sealed output

Stable GB10 evidence root:

```text
/home/testuser/wzh/track_b_adapter_20261005_seal/
```

The root contains the original primary and sensitivity outputs plus `sha256_manifest.txt`. It has 9 files and 923,755 bytes. `sha256sum -c sha256_manifest.txt` passes for 8/8 payload files. The manifest file SHA-256 is:

```text
dc388959150c98ffa7639108e1e80e306c346317b1cdced632ab66593960a04b
```

### Primary: `quarantine-primary`

| Field | Value |
|---|---:|
| pairs | 10 |
| source columns | 146 |
| target headers | 160 |
| events | 657 |
| invalid action references | 3 |
| correctness | `NOT_RUN` |

Payload hashes:

| File | SHA-256 |
|---|---|
| `checkpoint_events.jsonl` | `0605a7c62f2cc2d107535d3bf9efabb08b0d4c0127f6a7913985030f89ec4d77` |
| `checkpoint_summary.json` | `85010fa2fd78ca43d72a29743e129770afa841d2e4f0e4de94b54f53c76430b1` |
| `manifest.json` | `3adf9f8a962a1f016d4793bc81890ba42c68a2f088ecdc8e532ac3cb802fb1cd` |
| `quarantine_events.jsonl` | `fb24002ad568d51e9e3953def0311099b81fcd98803a58c257747ff50d390fc8` |

### Mandatory sensitivity: `pair-invalid-sensitivity`

The DSNY pair is excluded as a whole. The analysis retains 9 pairs / 130 source columns.

| Field | Value |
|---|---:|
| pairs | 9 |
| source columns | 130 |
| target headers | 160 |
| events | 573 |
| invalid action references | 3 |
| correctness | `NOT_RUN` |

Payload hashes:

| File | SHA-256 |
|---|---|
| `checkpoint_events.jsonl` | `b1ccc64406e30a780387cc8ac4e5d9c040eb805c36f41f80f785b0359078ed01` |
| `checkpoint_summary.json` | `dc8e186c4d4517d087cc59a76b35afaeb78c4c9094193b05152b5d155f9667a3` |
| `manifest.json` | `8e9ddebf22ff0d0f9fe1e9cfa1e83f417f1a9c5a733117440447ec1bd7deb77d` |
| `quarantine_events.jsonl` | `fb24002ad568d51e9e3953def0311099b81fcd98803a58c257747ff50d390fc8` |

## 3. Event-stage coverage

The event stream contains real tool-call state from the staged trajectory. It is not reconstructed from ground truth.

| Requested stage | Observed evidence | Coverage |
|---|---|---|
| candidate generation | `retrieve_candidates` (2), `retrieve_candidates_batch` (154 primary / 137 sensitivity) | covered |
| scoring | `compare_values` (9), `batch_compare_values` (148 / 123), `compute_value_overlap` (8) | covered |
| assignment | `record_match` (5), `batch_record_match` (181 / 157) | covered |
| accept/reject | the only `revoke_match` is one of the quarantined invalid references; no valid revoke event remains | unmeasurable in the valid stream |
| revision/rewrite | raw/final equality is recorded per event, but no separate rewrite/revision event is present | partial only; not a full trace |
| finalization | `finalize_all_matches` (146 / 130) | covered |

Absent or partial stages remain `unmeasurable/not_present`; they are not fabricated.

## 4. Evidence boundary

This pilot proves that a gold-free adapter can extract a partial process/checkpoint view from the existing within-origin NYC trajectories. It does not prove action-policy transfer, correctness, dedicated-student necessity, cross-origin generalization, safe continual improvement, or the Evaluate-Distill-Evolve loop.

Q3 corrected labels and B0-B4 results remain separate exploratory evidence. Correctness may only be joined later from sealed source ground truth after independent review and final-ledger binding; this receipt performs no such join. The confirmatory route remains `DATA_NO_GO / RQ2 NOT_IDENTIFIED`.
