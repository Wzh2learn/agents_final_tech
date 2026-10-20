# Loop C Reuse Definition Targeted Re-check

Task id: `reuse-definition-review-20261019-r2`
Mode: read-only targeted re-check of the single blocker and four hardening gaps. Do not repeat source audit or issue model requests.

Verify:

1. `action_change` now treats identical plan operations with floating answer tail drift as `NO_CHANGE`; H05/H11 are corrected to `NO_CHANGE`.
2. `post_feedback_action_change` is present on every history classification row and the context pool.
3. The pool recursively rejects nested `lesson`, hidden reference, future/gold answer and fabricated correction fields.
4. `raw_complete` is derived from raw completeness, not outcome completeness.
5. Synthetic fixtures cover success, wrong answer, tool failure, UNKNOWN, REFUSE and missing-record cases; fixture detection is explicit, not task-id prefix based.

Return `ACCEPTED`, `CONDITIONAL`, or `REJECTED` with blocker count. This review authorizes no generation.
