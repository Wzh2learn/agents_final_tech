# PR-EXP-04 Implementation Contract

> Frozen before N2 generation and before any N2 response observation.
> experiment_id: `PR-EXP-04` | prereg: `research/positive_repair_20261011/preregs/PR-EXP-04_prereg_v2.md`
> prereg_sha256: `c28574b19748ff6cb626cd484af4c08256aa6b449fe9f8a8d1db6aa89a76b038`

## 1. Authority and scope

- The scientific contract is prereg v2 sections 2-7. The prereg has no separately headed implementation-contract section; this file enumerates every implementation item required by those sections, the Loop A assignment, and the binding residual-notes addendum.
- Binding addendum: `research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md`.
- Shared term contract: `research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md`.
- This is one deterministic Track P supporting experiment only. It never counts toward the repair count.
- No model/judge call, training, production service, database, network, commit, push, prereg edit, threshold hunt, shared-surface edit, or mutation-label read beyond the frozen generation rules is authorized.
- Frozen multileaf carriers, D3 inputs, drift outputs, `config/eval_checkpoint_trees.json`, tests, and frozen-hash files are read-only.
- Missing required input, source, population metadata, label, leaf, group, or CI input stops with `INPUT_MISSING`. Hash disagreement stops with `HASH_MISMATCH`; authority disagreement stops with `PREREG_MISMATCH`.

## 2. Verified identities

- Every raw identity below was verified before implementation execution.
- Canonicalizer identity rule is `git_blob`: `git rev-parse HEAD:scripts/m1_statement_parser.py` = `def5161dd17fc14345d340879174ed01e0277626`; `git hash-object scripts/m1_statement_parser.py` = `def5161dd17fc14345d340879174ed01e0277626`.
- Verified canonicalizer raw sha256 on this host: `747b7eb6e5d33a33a2d34572d0491aac212c0c01100890daff18cb6ae64d372b` (informational only; EOL presentation may differ).
- GB10-only inputs actually used and fully pinned: drift tables sha256 `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302`; injection map sha256 `d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e`.

## 3. Enumerated verdict-relevant inventory

### 3.1 Population, groups, and class counts

- N1 mechanism population is the unchanged frozen 216-row paired carrier: M=72/R=72/N=72, with 72 total groups and 24 N-stage groups.
- N2 mechanism population is the same frozen M/R=144 stage-anchor rows plus 72 new N2 rows: M=72/R=72/N=72, with the N mechanism carried by 24 new held-out table UIDs.
- Shared M/R rows are disclosed common stage anchors because only the N mechanism changes. For every target cluster, that cluster is removed from the source population before centroids are fit; no target group contributes to its own centroid.
- N2 group identity is the held-out table UID, serialized as cluster `N2:<uid>`. N1 N groups are `N:<uid>`.
- N2 UIDs must be disjoint from all frozen M/N table UIDs and all drift injection-map UIDs. N1-N2 N UID intersection must be zero.
- N1 descriptive attrition and N2 attrition are reported separately. A selected N2 row that fails generation/contract retention is not silently replaced.
- N2-to-N1 may be optimistic because method-development history exists on N1 carriers; this is declared and never tuned away.

### 3.2 N2 deterministic generation rule

- Seed: `20261011`.
- Candidate UID rank: ascending SHA-256 of `20261011:pr-exp-04-n2-cluster:<uid>`.
- Candidate exclusion: UID absent from the frozen sample manifest's table UIDs and absent from `data/research/drift_v0/output/injection_map.json`.
- Eligibility: at least one frozen row/column-total identity and at least three distinct LHS cells whose parsed table value matches the frozen identity value within `0.01` and has absolute magnitude `>0.02`.
- Select the first 24 eligible groups. Within a group, rank distinct LHS cells by ascending SHA-256 of `20261011:pr-exp-04-n2-operand:<uid>:<row>:<col>:<canonical-identity>` and take the first three.
- Repeat 1: `operator_drop` — remove the selected LHS cell from the evaluated relation; table values are unchanged.
- Repeat 2: `coefficient_duplicate` — duplicate the selected LHS cell in the evaluated relation; table values are unchanged.
- Repeat 3: `sign_flip` — replace the selected table operand by its additive inverse; relation structure is unchanged.
- Each mode makes exactly one mechanism edit. The baseline source identity must pass and the N2 evaluated relation/replacement must fail through the frozen `identity_passes` reconciliation path.
- N2 UIDs are fixed before response observation. Exactly two pure generations must be byte-identical; any mismatch is `INVALID`.
- Selection rationale is determinism and executor ownership, not expected response performance.

### 3.3 Harness equivalence

- Regenerate all 72 frozen N1 N rows through the same N2 harness evaluation path.
- Canonical response-vector bytes are compared row-by-row against frozen `multileaf_paired_artifacts.jsonl`.
- Required: 72/72 byte-identical, zero mismatches. Failure is `INVALID`.
- N1 descriptive visibility is reported as the frozen observed 72/72 numerator/denominator; attrition is separately reported.

### 3.4 Visibility/evaluability gate

- Surface: exactly the frozen 12 leaves from `config/eval_checkpoint_trees.json`.
- A row is visible when at least one leaf is nonzero under the frozen response rule.
- Row gate: visible N2 rows `>= ceil((2/3) * generated N2 rows)`.
- Group gate: distinct held-out N2 groups with at least one visible row `>= 6`.
- Failure is exactly `MECHANISM_NOT_EVALUABLE`, canonical label `NOT_EVALUABLE`; it is never merged into `NULL`.
- Cluster-bootstrap 95% CIs use seed `20261012`, 10,000 replicates, percentile endpoints.

### 3.5 Feature surface and feature ban

Verbatim prereg feature ban:

> features may only use the frozen 12-leaf response surface + frozen contract-check outputs; provenance/mechanism-identifier features are forbidden (pinned in the implementation contract).

- Classifier inputs contain only frozen response-vector coordinates and contract checks permitted by that sentence.
- `mechanism`, provenance, UID, generation mode, transformation name, mutation labels, and mechanism identifiers are excluded from features.

### 3.6 Nearest-centroid, LOCO, and controls

- Labels: fixed class order `M`, `R`, `N`.
- For each target cluster, remove that cluster from the source population, compute one mean centroid per class, use Euclidean distance, and predict the unique nearest class.
- Tie rule: absolute tolerance `1e-12`; more than one tied minimum serializes `__TIE__` and is scored incorrect.
- Directions: N1→N2 and N2→N1 with identical code, population shape, and bootstrap procedure.
- Direct-codebook control uses the same classifier restricted to `parse.field.hit_rate`, `qa.retrieval.source_required`, and `parse.reconcile.equations`.
- Frozen direct references are reported unchanged: full `1.0`, direct `1.0`, non-direct `0.3333`.
- Responsive-leaf overlap reports N1 and N2 responsive sets, intersection, union, raw counts, and Jaccard.
- Shared-generation-harness confound is recorded: equivalence controls implementation confounding but cannot rule out harness-specific visibility.

### 3.7 Metrics, uncertainty, and raw accounting

- Primary per direction: macro-F1 and top-1 accuracy on stage identification.
- Macro-F1 reports TP/FP/FN, F1 numerator/denominator for M/R/N, sum numerator, class denominator, and point.
- Top-1 reports correct numerator and row denominator.
- Cluster bootstrap resamples target groups with replacement using seed `20261012`, 10,000 replicates; percentile 2.5%/97.5% endpoints.
- Same seed, replicate count, and procedure are used in both directions and both feature sets.
- Deterministic controls report exact numerator/denominator; set overlap reports CI as not applicable with reason.

### 3.8 Frozen numeric baselines

- Chance top-1: `1/3`.
- Uniform-class macro-F1: `1/3`.
- Majority macro-F1: `1/6`.
- Frozen ablation references: full `1.0`; direct `1.0`; non-direct `0.3333`.
- Materiality margin: `m=0.05`.

### 3.9 SOURCE_LOCAL_RESPONSE operational test

- Binding PR-EXP-04 operational branch: fingerprint-bound `NULL` branch + direct-codebook control + responsive-leaf overlap report.
- Duplicate-catch, specificity/no-op, and constant-1 arms are not applicable because PR-EXP-04 creates no new oracle channel; they are explicitly marked not applicable rather than silently treated as passes.

### 3.10 Outcome taxonomy and priority

Exactly one label is selected after gates, in this frozen priority:

1. `INVALID`: deviation, harness-equivalence failure, nondeterministic N2, or mechanism-set UID leakage.
2. `NOT_EVALUABLE`: visibility gate failure or fewer than six groups for a CI.
3. `NEGATIVE`: any direction macro-F1 point `< 1/3 - 0.05`.
4. `SUPPORTED`: both direction points `>= 1/3`, at least one macro-F1 CI low `> 1/3`, direct control reported, overlap report attached.
5. `NULL`: all remaining cases, including all directions within `m` of `1/3` or CI including `1/3` without meeting `SUPPORTED`.

- The result is supporting-only and `counts_toward_repair_count=false`.

### 3.11 Cost and preflight

- Zero model/judge calls; zero network/database/training/production calls.
- Runtime is measured from preflight start to receipt end.
- Formal preflight must reach `END_TO_END_PREFLIGHT_PASS` with exact population trace and zero scientific result files before the scorer run.
- Independent post-run recomputation must reach `FORMAL_RUN_PASS` before receipt finalization.

## 4. Input hashes

BEGIN_IMPLEMENTATION_CONTRACT_JSON
{
  "input_hashes": {
    "config/eval_checkpoint_trees.json": "0931d952e40e80a930a335a3ac7180f35812000248c4f23a5f71e5a9b316bf25",
    "data/research/drift_v0/input/tatqa_tables.json": "3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302",
    "data/research/drift_v0/output/injection_map.json": "d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e",
    "research/positive_repair_20261011/contracts/SOURCE_LOCAL_RESPONSE_v1.md": "4c3d6f06ff49e4aa3bfd7f575c3e03d8d4c675909074d4275745c219b9240290",
    "research/positive_repair_20261011/contracts/shared_surface_freeze_v1.json": "d084e7f66cbc3f6f841683c57e97286d9a049a611d787fcb245dbea453f811a4",
    "research/positive_repair_20261011/loop_a_cards/residual_notes_v1.md": "a87758a125f9ea0625f1c3b891fa465f55929e2e01d19bc6c9f2ef7479bbb569",
    "research/positive_repair_20261011/preregs/PR-EXP-04_prereg_v2.md": "c28574b19748ff6cb626cd484af4c08256aa6b449fe9f8a8d1db6aa89a76b038",
    "research/stage_e_method_revision_20261009/build_multileaf_freeze.py": "1c78a7349b989b3701f1820c70d3b0c784c0428455ddabe0e176ff292c0c27c1",
    "research/stage_e_method_revision_20261009/multileaf_freeze.json": "7239feb678dcbecc4f1bb374cc37e313fd0a74354a23349caa556419fabfa34d",
    "research/stage_e_multileaf_20261010/multileaf_mechanism_generalization_audit.json": "bd412df8d7d8f38b748b6a01c3fd90d070baf48287ee81983d1595c1b9def6ef",
    "research/stage_e_multileaf_20261010/multileaf_preresult_freeze_manifest.json": "15639e1e6014bab79620d2a845645fa89f0977ae53c1d5db367aaed7c32e5163",
    "research/stage_e_multileaf_20261010/multileaf_preresult_sample_manifest.json": "8e9121f2c1c030f1db7626c56bed6c82bef89d119cd952b3514a91ff1e691693",
    "research/stage_e_multileaf_20261010/results/multileaf_paired_artifacts.jsonl": "39c3a2c5c37949928b1250ec41ddf04059524853032dff2173cebec36265e53f",
    "research/stage_e_multileaf_20261010/results/multileaf_prediction_rows.jsonl": "37bb360133e4c85129a13f9d56db04d57ec2202ad0409491c20f79bd892afa06",
    "research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json": "0518c5bfc40bf2b4e82312887b9426bbb8833df326d4d782cd1cbe63d052571d",
    "research/stage_e_multileaf_20261010/run_multileaf_formal.py": "d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4"
  },
  "source_hashes": {
    "research/positive_repair_20261011/runs/PR-EXP-04/run_pr_exp_04.py": "945f936e229b9df252a9e495c4de45c56a5da0f32ccd049bec4f2587ec63c8f3",
    "research/positive_repair_20261011/runs/PR-EXP-04/validate_pr_exp_04.py": "dad54b0a68399c50a2697161603cc6f37e888a7f3588d6b7768a9aa8b45ba93f"
  },
  "parameters": {
    "bootstrap_replicates": 10000,
    "bootstrap_seed": 20261012,
    "classes": ["M", "R", "N"],
    "class_counts_each_mechanism": {"M": 72, "R": 72, "N": 72},
    "direct_leaves": {
      "M": "parse.field.hit_rate",
      "R": "qa.retrieval.source_required",
      "N": "parse.reconcile.equations"
    },
    "generation_seed": 20261011,
    "margin": 0.05,
    "n1_n_groups": 24,
    "n2_groups": 24,
    "n2_rows": 72,
    "n2_rows_per_group": 3,
    "tie_absolute_tolerance": 1e-12
  },
  "source_local_operational_test": "fingerprint_bound_null_branch_plus_direct_codebook_plus_responsive_leaf_overlap",
  "unpinned_input_semantics": "INPUT_MISSING"
}
END_IMPLEMENTATION_CONTRACT_JSON

## 5. Source-file hashes

- `research/positive_repair_20261011/runs/PR-EXP-04/run_pr_exp_04.py`: `945f936e229b9df252a9e495c4de45c56a5da0f32ccd049bec4f2587ec63c8f3`
- `research/positive_repair_20261011/runs/PR-EXP-04/validate_pr_exp_04.py`: `dad54b0a68399c50a2697161603cc6f37e888a7f3588d6b7768a9aa8b45ba93f`
- Frozen runner: `d99e94364b3e45ce1fc2b28e6f69ed7cce3514dfbca63a735280aa534da5a4a4`
- Frozen N-sample generator: `1c78a7349b989b3701f1820c70d3b0c784c0428455ddabe0e176ff292c0c27c1`

## 6. Stop and acceptance predicates

- [ ] Shared and contract hashes pass before generation.
- [ ] N1 response vectors are 72/72 byte-identical through the N2 harness.
- [ ] Two N2 generations are byte-identical.
- [ ] N1-N2 N UIDs are disjoint and all required class counts are recorded.
- [ ] Visibility numerator/denominator and responding-group count meet the frozen gates.
- [ ] Both directions, direct control, overlap, baselines, raw metrics, and cluster-bootstrap CIs are reported.
- [ ] Exactly one canonical outcome label is emitted.
- [ ] Independent validation reaches `FORMAL_RUN_PASS`.
- [ ] Receipt is valid JSON with zero model calls and no deviations unless a stop condition occurs.
