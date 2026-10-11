# EXPERIMENT_EXECUTION_PREFLIGHT Spec v2

> date: 2026-10-11 | supersedes v1 (retained at EXECUTION_PREFLIGHT_SPEC_v1.md) | scope: minimal per-experiment executable-readiness check
> why v2: PR-03 v3 showed two gaps in v1. (a) v1 check 9 accepted a FUNCTION-LEVEL fixture exercise, so it missed a runtime variable-shadowing bug that only fires inside the real `evaluate` path. (b) v1 had no attribution requirement, so a delivered result file could not be tied back to the frozen runner.
> target: `EXECUTION_PREFLIGHT_PASS`; once PASS, stop extending this infrastructure.

## Rules (unchanged from v1)
- Uses ONLY toy / fixture / schema-only / synthetic sanity objects. NEVER reads held-out outcomes, labels, or any frozen evaluation result to tune the preflight.
- Deterministic; zero model/judge calls; read-only on frozen artifacts; no commit/push.
- Runs BEFORE the experiment's formal execution; its receipt is part of the Loop C pre-result audit packet.
- A failed check stops the experiment as `PREFLIGHT_FAIL_<check>`; it never produces a scientific class.

## The 12 checks
1. `required_files_exist` - every file the experiment needs exists, with sha256 recorded.
2. `pins_resolve` - every hash/identity pin resolves (git_blob via both commands; raw_sha256 from raw bytes).
3. `schema_fields_exist` - every contract-pinned field name exists in the actual frozen payload schema.
4. `field_names_match_payload` - runtime dereferences use exactly the payload's key names (explicit alias table if a rename is intended).
5. `predicate_defined_on_population` - eligibility/gate predicates are total on the eligible domain; exclusions must follow from task semantics frozen before outcomes.
6. `scorer_oracle_total_on_allowed_inputs` - scorer/oracle defined on every allowed input class, or its NOT_EVALUABLE sub-domain is declared from task semantics.
7. `group_split_ids_resolve` - group/split identifiers resolve; mechanism-disjoint and group-disjoint rules execute on fixtures.
8. `provenance_writer_attribution` - a toy run through the FROZEN writer path emits a receipt attributed to the correct experiment_id with input/output hashes; out-of-band writers are forbidden.
9. `metric_pipeline_end_to_end_on_fixture` - **v2 REQUIREMENT**: the full metric pipeline must run END TO END on a synthetic fixture that traverses the real entry point (the same code path the formal run uses), producing a toy-labelled outcome. A function-level exercise of helpers is NO LONGER sufficient and must be recorded as `FAIL`.
10. `no_heldout_read` - the recorded read-set contains only fixtures/schema/frozen non-evaluation inputs; zero held-out reads.
11. `runtime_path_load` - **(new in v2)** import or execute every module the formal run touches, so that name-resolution defects (unbound/shadowed locals, missing imports, Python-version-gated syntax such as `zip(strict=...)`) surface in the preflight domain rather than mid-run.
12. `run_attributable` - **(new in v2)** after any execution, every emitted artifact (result/metrics/receipt) must be attributable to the frozen runner: record runner sha256, command line, git revision, and output hashes; a result that cannot be tied to the runner is `PREFLIGHT_FAIL_run_attributable`.

## Deliverables (per experiment, produced by Loop A)
- `research/positive_repair_20261011/runs/<EXP>/execution_preflight_config.json` (schema: experiment_id, required_files[path+sha256], pins[], schema_assertions, predicates[], fixture_path, writer_entrypoint, metric_entrypoint, allowed_reads[])
- `research/positive_repair_20261011/runs/<EXP>/execution_preflight_receipt.json` (per-check status + evidence + overall `EXECUTION_PREFLIGHT_PASS|PREFLIGHT_FAIL_*`; start/end UTC; model_calls=0)

## Known limit (recorded honestly)
This remains a minimal gate. It cannot prove scientific validity and it cannot catch a defect that only appears on the full frozen population. It exists to stop the class of failures seen in round 1: undefined gates, wrong field names, unbound identifiers, unattributable writers, and infeasible compute.