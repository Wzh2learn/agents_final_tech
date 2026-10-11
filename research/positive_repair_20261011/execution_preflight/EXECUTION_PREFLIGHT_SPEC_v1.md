# EXPERIMENT_EXECUTION_PREFLIGHT Spec v1 (minimal)

> date: 2026-10-11 | status: SPEC (Loop D) | scope: NOT a governance project; a minimal per-experiment executable-readiness check
> rationale: round 1 showed scientific-prereg PASS != experiment executable (03 gate definition, 04 schema key + provenance writer, 07 field-name pin, 01 checker verdict defect).
> target: `EXECUTION_PREFLIGHT_PASS` per experiment. Once PASS, STOP extending this infrastructure.

## Rules
- Uses ONLY toy / fixture / schema-only / synthetic sanity objects. NEVER reads held-out outcomes, labels, or any frozen evaluation result to tune the preflight.
- Deterministic; zero model/judge calls; read-only on frozen artifacts; no commit/push.
- Runs BEFORE the experiment's formal execution; its receipt is part of the Loop C pre-result audit packet.
- A failed check stops the experiment as `PREFLIGHT_FAIL_<check>`; it never produces a scientific class.

## The 10 checks (each must record evidence + status)
1. `required_files_exist`: every file the experiment needs (prereg, implementation contract, frozen inputs, fixture) exists, with sha256 recorded.
2. `pins_resolve`: every hash/identity pin resolves (identity_rule=git_blob -> `git rev-parse HEAD:<path>` and `git hash-object <path>` equal the pinned blob; identity_rule=raw_sha256 -> raw bytes; prefix pins -> full hash recorded).
3. `schema_fields_exist`: every contract-pinned field name exists in the actual frozen payload schema (assert, don't assume).
4. `field_names_match_payload`: runtime dereferences use exactly the payload's key names (explicit alias table if a rename is intended; never silent aliasing).
5. `predicate_defined_on_population`: eligibility/gate predicates are total on the frozen population's eligible domain (dry, schema-level check); any excluded sub-domain must follow from TASK SEMANTICS frozen before seeing outcomes (no post-hoc exclusion).
6. `scorer_oracle_total_on_allowed_inputs`: the scorer/oracle is defined on every allowed input class, or its NOT_EVALUABLE sub-domain is declared from task semantics (empty-header-style edges resolved by definition, not by dropping observed cases).
7. `group_split_ids_resolve`: group/split identifiers resolve on the frozen payloads; mechanism-disjoint and group-disjoint rules execute on fixtures.
8. `provenance_writer_attribution`: a toy run through the FROZEN writer path emits a receipt attributed to the correct experiment_id with input/output hashes; out-of-band writers are forbidden.
9. `metric_pipeline_on_fixture`: the full metric pipeline runs end-to-end on a non-scientific synthetic fixture and yields a toy-labeled outcome (POSITIVE/NULL/NEGATIVE/INVALID/NOT_EVALUABLE machinery exercised).
10. `no_heldout_read`: the preflight's recorded read-set contains only fixtures/schema/frozen non-evaluation inputs; assert zero held-out reads.

## Deliverables (per experiment, produced by Loop A)
- `research/positive_repair_20261011/runs/<EXP>/execution_preflight_config.json` (schema: experiment_id, required_files[path+sha256], pins[], schema_assertions[payload+fields], predicates[], fixture_path, writer_entrypoint, metric_entrypoint, allowed_reads[])
- `research/positive_repair_20261011/runs/<EXP>/execution_preflight_receipt.json` (per-check status + evidence + overall `EXECUTION_PREFLIGHT_PASS|PREFLIGHT_FAIL_*`; start/end UTC; model_calls=0)