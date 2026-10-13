# TAT-QA WP-2 Preregistration Draft Skeleton

Status: `DRAFT - NOT READY - NO PILOT AUTHORIZATION`

Task: `tatqa_wp1_loop_a`

This skeleton freezes no experiment and authorizes no model call. All actor, context, budget, window, and governance fields remain pending until owner/advisor selection and approval.

## 1. Scientific scope

- Question: whether fixed, related real execution experience changes performance on new-origin two-period table-calculation tasks.
- Independent unit: origin.
- Arms: B, E, C, S as defined by the frozen evaluation protocol.
- Primary outcomes: `correct`, `correct_other_form`, `wrong_unit`, `wrong_period`, `regressed`, `refused`, and `unknown`.
- No training, memory write-back, pilot execution, or candidate-item scoring is authorized by WP-1.

## 2. Frozen software pins

- Checker: `1dbaa0055fb235d242dc6d4d8f7adade55305c89d4c8673d328348ab21ddb723`
- Adapter: `dbb5b55bbe48c36c9b5854dfe1780e3a9ca09e08ffe58331468d61ce21f52477`
- Synthetic fixtures: `8b464f682c8ebd4004fd216b4cd69dc26bcff790c6a035fe2b2f03564d8d2345`
- Preflight receipt: `b6997cfdf54e25a8679abf00df3d8bc9bccd8a7cdc7b7abead89846c06491931`
- Implementation contract: `e281248058467de32087ae2ae4138d7506960a96f862154cff1c32ccfb740d06`

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
