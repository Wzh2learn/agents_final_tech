# CodeUpdateArena V2 Post-Hoc Execution Revalidation

- Status: `COMPLETE_ZERO_REQUEST_REVALIDATION`
- Evidence identity: `POST_HOC_EXECUTION_REVALIDATION_PUBLIC_SYNTHETIC`
- Model calls: `0`; this re-executes only frozen V1 generated code.
- Docker image ID: `sha256:0fc8b2941cd46391b8fdd1fea784d91ad9a7a0e31a3a703ae08842c653b33d40`
- Paired all-tests-pass difference: `-1`
- Base: `3/8`, `28/50` tests.
- Update-info: `2/8`, `22/50` tests.

Candidate code is AST-restricted against marker forging and early exits.
Each hidden test emits trusted nonce-bound start/pass/completion markers.
Assertion failures are classified as test failures; pre-test failures are runtime failures.

This is public synthetic execution for development, not natural production drift
or a general model-capability claim.
