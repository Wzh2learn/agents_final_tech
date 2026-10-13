# TAT-QA WP-2 Preregistration Draft Skeleton

Status: `DRAFT - NOT READY - NO PILOT AUTHORIZATION`

Task: `tatqa_wp1_loop_a`

Spec revision: `1.2`

This skeleton freezes no experiment and authorizes no model call. All actor, context, budget, window, and governance fields remain pending until owner/advisor selection and approval.

## 1. Scientific scope

- Question: whether fixed, related real execution experience changes performance on new-origin two-period table-calculation tasks.
- Independent unit: origin.
- Arms: B, E, C, S as defined by the frozen evaluation protocol.
- Outcomes: `correct`, `correct_other_form`, `wrong_unit`, `wrong_period`, `wrong`, `regressed`, `refused`, and `unknown`.
- No training, memory write-back, pilot execution, or candidate-item scoring is authorized by WP-1.
- Protocol revision and protocol pin: `PENDING`.
- Item/split freeze receipt: `PENDING`.
- Actor freeze: `PENDING`.
- `target_unit` assignment: `PENDING` (identity-only conversion today across the 60 frozen candidates).

## 2. Frozen software pins

- Checker: `c919845b051a7cfbebfdc782ba4c9dcbd99cac8b950b46f8bd908fcdc2cb12f1`
- Adapter: `dbb5b55bbe48c36c9b5854dfe1780e3a9ca09e08ffe58331468d61ce21f52477`
- Synthetic fixtures: `acbe79d9c0c1123dcfcc4cbc764cd0bcc6a6359fad4530c814d546497f036a85`
- Preflight receipt: `4fe47548fcd6de852e16d85e3466d732ee80dec479df2214dc29e178d0f79925`
- Implementation contract: `9a715c8f5b56ec016a33e0187f4c507b5e1ad119dace5311aebc1057a705e7eb`

## 3. Actor freeze

- Actor revision: `PENDING`
- Model identity: `PENDING`
- Model settings: `PENDING`
- Calculator/tool implementation hash: `PENDING`
- Adapter settings: `PENDING`

## 4. Experience context

- Episode-source contract: `PENDING`
- Real E blocks: `PENDING`
- Real C blocks: `PENDING`
- Origin-disjointness receipt: `PENDING`
- Near-duplicate isolation receipt: `PENDING`
- E/C token-delta receipt: `PENDING`
- S rules: `PENDING`

## 5. Evaluation and analysis

- Frozen item/split receipt: `PENDING`
- Pilot task list: `PENDING`
- Repeat count and ordering: `PENDING`
- Analysis script hash: `PENDING`
- Bootstrap method and seed: `PENDING`
- Origin-level difference table: `PENDING`

## 6. Budget, window, and governance

- Owner authorization: `PENDING`
- Advisor authorization: `PENDING`
- Budget/window binding: `PENDING`
- Start/end UTC: `PENDING`
- Model-call budget: `PENDING`
- Endpoint-call budget: `PENDING`
- Judge-call budget: `0`

## 7. Stop rules

- Leakage or bridge failure: `STOP_THIS_PANEL`
- B ceiling on both repeats: `STOP_THIS_PANEL`
- Any unauthorized model, judge, endpoint, database, or service call: stop and report.
- Fixture or checker failure: report `SOFTWARE_NOT_QUALIFIED`; never weaken the failing test.
