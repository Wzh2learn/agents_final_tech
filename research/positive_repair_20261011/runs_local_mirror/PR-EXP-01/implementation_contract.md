# PR-EXP-01 Implementation Contract — SYNTHETIC_NULL_SUPPORT_REPAIR

Frozen before panel generation and before any scoring. This contract applies the binding `residual_notes_v1` addendum and is the execution inventory for Loop A / GB10.

## 1. Goal, done conditions, exclusions, and stops

- Goal: execute exactly one deterministic Track P experiment, PR-EXP-01, under prereg v2.
- Done: Phase 0 either proves a complete non-empty admitted panel or stops `NOT_EVALUABLE`; if admitted, freeze a calibration-only threshold before semantic harmful-side access, evaluate held-out nulls, report harmful TPR with paired cluster bootstrap CI, produce the required empirical bridge, and emit exactly one canonical label in `result.json` plus `receipt.json`.
- Exclusions: no model/judge calls, training, services, databases, network, commit/push, prereg edits, threshold hunting, label misuse, shared-surface edits, or execution of any other experiment.
- Stop conditions: `INPUT_MISSING`, `PREREG_MISMATCH`, `HASH_MISMATCH`, unpinnable scored surface (`STOP_BRANCH`), empty/unverifiable Phase 0 admission (`NOT_EVALUABLE`), or any requirement for a forbidden action.
- Invalid conditions: harmful-side involvement in selection, any post-freeze source/implementation edit, or relabeling the claim as an empirical clean-only repair.

## 2. Authority and qualification gate

| Item | Path | Verified identity |
|---|---|---|
| Scientific contract | `research/positive_repair_20261011/preregs/PR-EXP-01_prereg_v2.md` | sha256 `41c6c3cd14b5d0dd1e00abef9bd15953ba9bf1cb1d8463910270f67b94af0cd3` |
| Prereg freeze | `research/positive_repair_20261011/prereg_freeze_manifest_v2.json` | sha256 `b543953952c3af87b9db98f360b7d5b57d02a6dfe399cab8621c822b2b0dda5f` |
| Loop C pre-result re-audit | `research/positive_repair_20261011/loop_c_prereg_audit_recheck_result_raw.log` | sha256 `a437792b4ff5997e18a5f2600b9778752b037173de616263431fdec6c0f7399d`; PR-EXP-01 `PASS`, authorization present |
| Shared-surface freeze | `research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json` | current raw sha256 `d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4`; all entries verified before this contract |
| Hash-fix authority | `research/positive_repair_20261011/round_receipt_v4_hashfix.json` | sha256 `7c942208c92c49fa4e54a066e7ce479b8d23a130d2dd5fadf80a6eb4fd87aa26` |
| SOURCE_LOCAL_RESPONSE | `research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md` | raw sha256 `4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290` |
| Binding residual notes | `research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md` | raw sha256 `a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569` |
| Loop A card | `research/positive_repair_20261011/loop_a_cards/loop_a_PR-EXP-01.md` | raw sha256 `424bc01707bdd9aa075196725b0f35b8aa1193f923e68bc07cebfbd0b4aa71e8` |

Per experiment, `SOURCE_LOCAL_RESPONSE` is restricted exactly as frozen: claim object is only `SYNTHETIC_NULL_SUPPORT_REPAIR`, and source-local language is not used. The residual-note requirements—verified canonicalizer value, source-term-sheet hash, full GB10 input hashes, enumerated inventory, `INPUT_MISSING` semantics, and PR-EXP-01 edit-DSL/admission/fold/scored-surface pinning—are incorporated below.

## 3. Hash-checked verdict-relevant inventory

Any absent file or identity mismatch is `INPUT_MISSING`/`HASH_MISMATCH` and stops before scoring.

### 3.1 Shared and pre-threshold sources

| Parameter | Path | Identity |
|---|---|---|
| Frozen clean scorer | `research/stage_e_method_revision_20261009/stage_e_matched_fpr_reanalysis.py` | raw sha256 `f926c63d602db9ecbd2c64a8cdb0fff5850875a16ea88d386e905cc8bcb24489` |
| D3 contrastive implementation | `research/paper_d3_matched_fpr_stage_a.py` | raw sha256 `56f0c8519236f4420a63835bf95ea6c6853bb838d94527486519a3e9482d8f9f` |
| Tree aggregation implementation | `research/paper_t1_eval_baselines.py` | raw sha256 `01772e84efb3f579a1146c7c0b0e76f42b1e77625eee1124f901ab03b4c29f79` |
| Canonicalizer wrapper | `scripts/m1_statement_parser.py` | `identity_rule=git_blob`; `git rev-parse HEAD:...` = `def5161dd17fc14345d340879174ed01e0277626`; `git hash-object ...` = same; verified raw sha256 `747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b` (GB10 informational) |
| Canonicalizer implementation | `src/biz/m1_statement_parser.py` | raw sha256 `d4f9ed86c8d0fa466462c8132308a31bf51e7e4439042c4d147da9f99550d8a8` |
| Frozen tree | `config/eval_checkpoint_trees.json` | raw sha256 `0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25` |
| Drift corpus tables (GB10-only) | `data/research/drift_v0/input/tatqa_tables.json` | full raw sha256 `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302` |
| Injection map (GB10-only) | `data/research/drift_v0/output/injection_map.json` | full raw sha256 `d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e` |

### 3.2 Harmful-side sources, semantically opened only after threshold freeze

Hash pinning here is an inventory identity; semantic row parsing and harmful reproduction are deferred until `threshold_freeze.json` exists, is sha256-sidecar bound, and is read-only.

| Parameter | Path | raw sha256 |
|---|---|---|
| Injected corpus | `data/research/drift_v0/output/injected_tables.json` | `827092cf6af2212ae334a9ad5f7b9ea12122d90ff9117353baf79bb1936e4fa9` |
| D1 labels/scores carrier | `logs/graph/eval/d1_mutant_validity_audit.json` | `ef1d46ed9ca1ae3832f35d2796b3a51be34c912897d68b40d73c9413d8651a2b` |
| D2 deterministic carrier | `logs/graph/eval/d2_cross_matcher_det.json` | `7bb268e5da19590c9f58e71e293c3b66e4e5071f53932b41792ec8fb0ea1f146` |
| D2 embedding carrier | `logs/graph/eval/d2_cross_matcher_embed.json` | `ed3d3905e42c41ab71d4dfacc64a3609de2dd12d5e20cf9b5b363a90d29d4bbf` |
| W2 E16 carrier | `logs/graph/eval/_w2_e16_section.json` | `d02057eda97618fd57e9051babf45bf0faab3e5ba923c68cb39cafa07d6e2757` |
| Frozen D3 output carrier | `logs/graph/eval/d3_matched_fpr_stage_a.json` | `3318ac178a0c3317ce18d69663b942e289c2668f4b604082606a549172f2ab10` |

### 3.3 Frozen implementation lineage

| File | sha256 |
|---|---|
| `generate_null_panel.py` | `fbade41436b12724a1ca9ea7f58cf86cfa8d3fb01f87b1cacbedbb5b2093c0f8` |
| `check_null_panel.py` | `53a9cc017d0382869afe1ed019696d962d8d516e7343ae8373aad76616a02228` |
| `run_pr_exp_01.py` | `f66dfbeeaded20ba9dfe243ec4d3769db32cb8e6b3a110415f9166aba5fccb10` |

The three files parse as Python AST before freeze. The checker's own AST import inventory contains no module containing `generate_null_panel`; it has a separate file hash and does not import the generator.

## 4. Scored surface pinned verbatim

The frozen clean implementation is `research/stage_e_method_revision_20261009/stage_e_matched_fpr_reanalysis.py` at the pinned hash above. Its exact raw observation input and score expression are:

```python
header = d3.header_of(table["table"][0])
canonical = d3.unique_canonical(header, mp)
h, _ = d3.hit_rate(header, canonical, mp)
h_repeat = d3.hit_rate(header, canonical, mp)[0]
flat = round((h - h_repeat) * 10.0, 6)
root = d3.root_of(tb, h)
layered = round(root - d3.root_of(tb, h_repeat), 6)
```

The corresponding frozen two-observation expression is in `research/paper_d3_matched_fpr_stage_a.py` at the pinned hash:

```python
inj_hdr = header_of(corp["by_uid"][uid][0])
oh = orig_header(inj_hdr, corp["entries"][uid])
cans = unique_canonical(oh, mp)
h_o, m_o = hit_rate(oh, cans, mp)
h_f, m_f = hit_rate(inj_hdr, cans, mp)
comb10 = round((h_o - h_f) * 10.0, 6)
```

For this null panel, the scored surface is exactly the two raw row-zero header lists `[str(c) if c is not None else "" for c in table["table"][0]]`: `source_header` is `oh` and `edited_header` is the second observation. The frozen score is instantiated as:

```python
canonical = d3.unique_canonical(source_header, mp)
h_original, _ = d3.hit_rate(source_header, canonical, mp)
h_edited, _ = d3.hit_rate(edited_header, canonical, mp)
flat = round((h_original - h_edited) * 10.0, 6)
layered = round(d3.root_of(tb, h_original) - d3.root_of(tb, h_edited), 6)
```

The raw lists—not normalized keys or downstream artifacts—are the scored surface. Admission requires their canonical JSON hashes to differ.

## 5. Task-truth surface pinned exactly

For each raw header independently, the checker and generator re-run the frozen canonicalizer and downstream mapping and hash this post-canonicalization artifact:

```python
canonical_raw = d3.unique_canonical(header, mp)
fields = [mp.SchemaField(std, [std]) for std in canonical_raw]
schema_table = mp.SchemaTable(..., fields=fields)
mapping, unmapped = mp.map_headers(header, schema_table)
task_truth = {
  "canonical_normalized_keys": [mp.normalize_header(cell) for cell in canonical_raw],
  "canonical_count": len(canonical_raw),
  "mapped_standard_values_in_header_order": [mapping.get(cell) for cell in header],
  "unmapped_normalized_counts": sorted normalized-count pairs from unmapped,
}
```

Admission requires byte-identical canonical-JSON hashes of `task_truth(source_header)` and `task_truth(edited_header)`.

## 6. Null edit DSL, generator, checker, and complete panel

Candidate universe: every cell of every usable clean table, crossed with every rule below, in rule order. A table is usable when its UID is absent from the frozen injection map and `d3.unique_canonical(source_header, mp)` is non-empty.

1. `edge_space_prefix`: replace cell text `x` with `" " + x`.
2. `edge_space_suffix`: replace cell text `x` with `x + " "`.
3. `internal_single_space_removed`: if ASCII space exists, remove its first occurrence; otherwise no candidate.
4. `case_swap`: replace cell text `x` with `x.swapcase()`.

No sampling, label use, score use, harmful read, or favorable selection is allowed. The generator enumerates the full Cartesian candidate universe. The independent checker recomputes it without importing the generator, compares the exact ordered admission list and duplicate count, and requires both `raw_nonidentity=true` and `task_truth_identity=true` for every row. Panel = all and only admitted records. Empty admission, any checker mismatch, AST independence failure, or unverifiable identity stops without scoring as `NOT_EVALUABLE`.

## 7. Fold rule and partitions

Inherited fold text from `stage_e_matched_fpr_reanalysis.py`, verbatim:

```python
fold = {uid: i % N_FOLDS for i, uid in enumerate(sorted({row["uid"] for row in clean} | {row["uid"] for row in harmful}))}
```

D3 S-1 text, verbatim: `sorted(uid) index % 5; 表为最小单元, 同表 clean 版与全部 mutation 同 fold（本语料 clean 表与注入表 uid 不相交, 天然满足 S-1）`.

`N_FOLDS=5`. The union equals the sorted source-table UID universe. Frozen implementation split, declared before panel generation: calibration folds `{0,1,2}`; held-out folds `{3,4}`. Both partitions use the identical score function. Empty calibration or held-out partition after non-empty admission stops `NOT_EVALUABLE`.

## 8. Threshold, harmful ordering, metrics, and bootstrap

- Alpha `0.05`; candidate thresholds are only calibration-null score support.
- Threshold is the smallest `t` satisfying `fraction(calibration score > t) <= 0.05`; comparison is strict `>`; no interpolation and no harmful/held-out selection.
- Compute flat and layered thresholds independently under the same frozen rule.
- Write `threshold_freeze.json`, its sha256 sidecar, and chmod it read-only before held-out reporting and before any semantic harmful-side open.
- Held-out null FPR uses strict `>`; report raw numerator/denominator, rate, and 95% exact Clopper–Pearson CI.
- Only after threshold freeze: verify all harmful-source hashes, run deterministic `d3.g1_reproduce`, require `all_pass=true`, filter frozen classes `H|HI`, and require denominator `111`.
- Harmful TPR uses strict `>` at each frozen threshold; report numerator/denominator.
- Paired cluster bootstrap: resample sorted table UIDs with replacement, retain every harmful row in each sampled cluster, `N_BOOT=2000`, seed `20260830`, percentile CI at 2.5/97.5 using the frozen linear interpolation; report flat, layered, and paired difference CIs.
- Threshold selection never reads harmful rows. Harmful rows are descriptive after the threshold file is immutable.

## 9. Bridge, outcome, cost, and receipt rules

- Original result remains separate: 2,382 empirical clean rows, support `{0}`, `NOT_IDENTIFIABLE`; it is never replaced.
- Bridge recomputes the original empirical clean-row flat/layered distribution and strict-`>` FPR at the frozen synthetic thresholds, with exact CIs, explicitly labeled `non-comparable empirical-vs-synthetic read`.
- `POSITIVE` only if calibration support is greater than a single point, a threshold exists, and held-out FPR is `<=0.05` for both channels. Identifiability is an attribute, not a synonym for the label.
- `NULL` is the substantive label if support or held-out FPR contract fails.
- `NOT_EVALUABLE` is strictly limited to empty admission, unverifiable identity, or unpinnable/empty qualification surfaces; it is never `NULL`.
- `INVALID` covers forbidden selection, post-freeze edit, source mismatch during execution, or empirical-clean relabeling.
- `NEGATIVE` has no frozen decision criterion in prereg v2 and is therefore not invented or used.
- Cost ledger must show `model_calls=0`, `judge_calls=0`, training/service/database/network counts `0`.
- `receipt.json` must contain prereg and implementation-contract hashes, UTC start/end, input/output hashes, raw numerators/denominators and CIs, exactly one label, cost, unverified items, and deviations. Valid JSON only.

## 10. Frozen-artifact handling

After this contract and its sha256 sidecar are written, the contract, sidecar, generator, checker, runner, and all pre-existing frozen carriers are read-only for this run. Only files under `runs/PR-EXP-01/` created as experiment outputs may be written. Any attempted edit to a frozen source, implementation, prereg, carrier, config, test, or frozen hash is `INVALID` and stops.
