# WP-1 Implementation Contract

Task: `tatqa_wp1_loop_a`

Scope: implement the thin checker, deterministic adapter, synthetic fixture runner, preflight receipt, and preregistration draft for TAT-QA WP-1. This contract authorizes no candidate-item scoring, model call, endpoint call, episode collection, training, service access, database access, network access, commit, or push.

Write paths:

- `research/tatqa_wp0_2026/wp1/`
- `data/research/tatqa_wp0_2026/wp1/`

Runtime and style:

- Python 3.12 standard library only.
- UTF-8 input and LF-terminated JSON/Markdown outputs.
- Synthetic fixtures only for execution.
- Fail closed if any fixture obligation or preflight check fails.

## 1. Module list and signatures

### `research/tatqa_wp0_2026/wp1/checker.py`

```python
SCALES: dict[str, Decimal]
REQUIRED_RUNTIME_FIELDS: frozenset[str]
CORRECT_OUTCOMES: frozenset[str]
OUTCOME_CLASSES: frozenset[str]

@dataclass(frozen=True)
class Gold:
    late_value: Decimal
    early_value: Decimal
    delta_source: Decimal
    delta_target: Decimal
    source_unit: str
    target_unit: str

@dataclass(frozen=True)
class PreparedItem:
    item_id: str
    origin_id: str
    row_label: str
    late_period: str
    early_period: str
    gold: Gold

def normalize_unit(unit: str | None) -> str: ...
def parse_numeric_cell(value: str | int | float) -> Decimal: ...
def conversion_factor(source_unit: str, target_unit: str) -> Decimal: ...
def recompute_gold(item: Mapping[str, Any]) -> Gold: ...
def prepare_item(item: Mapping[str, Any]) -> PreparedItem: ...
def parse_answer(answer_text: str) -> dict[str, Any] | None: ...
def score_prepared(prepared: PreparedItem, answer_text: str) -> dict[str, str]: ...
def score_item(item: Mapping[str, Any], answer_text: str) -> dict[str, str]: ...
def apply_regression(base_outcome: str, arm_outcome: str) -> str: ...
def aggregate_outcomes(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]: ...
def paired_origin_differences(
    records: Iterable[Mapping[str, Any]],
    left_arm: str,
    right_arm: str,
) -> dict[str, Any]: ...
```

Gold construction is separated from answer parsing. `score_item` constructs `PreparedItem` before it passes `answer_text` into `score_prepared`. Numeric parsing removes thousands separators and treats surrounding parentheses as negative. Supported scale keys are `unit`, `thousand`, `million`, `billion`, and `percent`; conversion uses the ratio of their scale exponents.

Outcome precedence:

1. Literal `REFUSED` -> `refused`.
2. Literal `UNKNOWN`, timeout marker, or unparseable JSON -> `unknown`.
3. Row mismatch -> `wrong`.
4. Reversed period order with both values negated -> `correct_other_form`.
5. Any other period mismatch -> `wrong_period`.
6. Source value correct and target value wrong -> `wrong_unit`.
7. Both values correct -> `correct`.
8. Otherwise -> `wrong`.

`regressed` is assigned only by `apply_regression` when a B outcome in `{correct, correct_other_form}` becomes a non-correct answer other than `refused` or `unknown`; refusals and unknowns remain first-class.

The eight-class vocabulary is therefore `correct`, `correct_other_form`, `wrong_unit`, `wrong_period`, `wrong`, `regressed`, `refused`, and `unknown`.

### `research/tatqa_wp0_2026/wp1/adapter.py`

```python
ARMS: frozenset[str]
CONTEXT_HOOK_TYPES: Mapping[str, str]
ANSWER_FORMAT: str

@dataclass(frozen=True)
class ContextHook:
    arm: str
    hook_type: str
    text: str

@dataclass(frozen=True)
class Projection:
    row_label: str
    period_late: str
    period_early: str
    source_unit: str
    target_unit: str
    requested_quantity: str
    table: list[list[str]]

def runtime_payload_from_candidate(item: Mapping[str, Any]) -> dict[str, Any]: ...
def projection_from_candidate(item: Mapping[str, Any]) -> Projection: ...
def validate_context_hook(hook: ContextHook) -> None: ...
def build_prompt(item: Mapping[str, Any], hook: ContextHook) -> str: ...
def count_context_tokens(text: str) -> int: ...
def context_token_delta(
    e_text: str,
    c_text: str,
    relative_limit: Decimal = Decimal("0.05"),
) -> dict[str, Any]: ...
```

The prompt is deterministic UTF-8 JSON text with no timestamp, random value, item id, origin id, gold field, gold value key, or hidden recomputation rule. The complete table is serialized without truncation. Arm hooks are typed as `none`, `experience`, `matched_experience`, or `static_rules`; the adapter serializes supplied typed placeholder text and does not construct real experience blocks.

Token accounting uses a documented deterministic lexical proxy: non-whitespace tokens from `re.findall(r"\\S+", text)`. It is not a model tokenizer estimate.

### `research/tatqa_wp0_2026/wp1/provenance.py`

```python
TASK: str

def task_provenance() -> dict[str, Any]: ...
def attributed_payload(payload: Mapping[str, Any]) -> dict[str, Any]: ...
def write_json_lf(path: str | Path, payload: Mapping[str, Any]) -> None: ...
```

The writer attributes every generated receipt to `tatqa_wp1_loop_a`, records `model_calls=0`, and records `endpoint_calls=0`.

### `research/tatqa_wp0_2026/wp1/run_fixtures.py`

```python
WORK_DIR: Path
DATA_OUT_DIR: Path
FIXTURE_PATH: Path

def load_synthetic_fixtures() -> dict[str, Any]: ...
def fixture_item(fixture: Mapping[str, Any]) -> dict[str, Any]: ...
def run_checks(fixtures: Mapping[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]: ...
def write_outputs(fixtures: Mapping[str, Any], obligations: list[dict[str, Any]], metrics: dict[str, Any]) -> None: ...
def main() -> int: ...
```

### `research/tatqa_wp0_2026/wp1/fixtures/synthetic_fixtures.json`

Schema: `tatqa_wp1_synthetic_fixtures_v1`.

Required fixtures:

- `normal_unit`: ordinary two-cell recomputation.
- `parentheses_negative`: parenthesized early value becomes negative.
- `thousands_separator`: comma-separated cells are parsed as thousands separators.
- `thousand_to_unit`
- `million_to_thousand`
- `billion_to_million`
- `percent_to_percent`

The first seven fixtures provide seven hand-built recomputations, including the two mandated parsing cases and all four mandated conversions. Answer fixtures exercise all eight outcome classes; `unparseable` is an input case that resolves to `unknown`.

The E and C placeholder contexts are synthetic strings with a measured lexical token delta declared in the fixture file. They are not episodes and are not real experience blocks.

## 2. Fixture obligations

`run_fixtures.py` must execute exactly these seven obligations and emit one result object per obligation:

1. `prompt_byte_determinism`: build every fixture with an identical hook twice for each arm B/E/C/S and compare encoded UTF-8 bytes.
2. `hidden_gold_search`: reject hidden key names; for `delta_source`/`delta_target`, search both canonical plain-decimal needles and exact `str()`/fixture-render forms when they differ, across the full projection and the raw-cell precondition.
3. `hidden_gold_positive_control`: inject every generated needle into a synthetic projection and require the guard to fire, including `1300`/`1300.0` and negative `-55`.
4. `gold_recomputation`: compare `recompute_gold` results to at least five hand-computed expected values, including parentheses-negative and thousands-separator cases.
5. `scale_conversions`: compare all four specified unit conversions.
6. `unknown_and_refused`: classify literal `UNKNOWN` and `REFUSED` correctly, plus unparseable JSON as unknown.
7. `ec_token_delta`: compute lexical token counts, absolute delta, relative delta, and pass/fail against the fixture's 5% limit.

Additional non-obligation synthetic checks are permitted only to exercise the declared checker taxonomy, regression helper, provenance writer, and metric pipeline. They must use fixture origin/item ids only.

Every `score_item` call in `run_fixtures.py` is routed through one instrumented fixture wrapper. The wrapper records fixture id, item id, origin id, input kind, and call-site label, rejects non-synthetic identities, and derives `scoring_inputs_all_synthetic`.

## 3. Preflight schema

`research/tatqa_wp0_2026/wp1/PREFLIGHT_RECEIPT.json` uses schema `tatqa_wp1_preflight_receipt_v1` and contains:

```json
{
  "schema": "tatqa_wp1_preflight_receipt_v1",
  "spec_revision": "1.2",
  "task": "tatqa_wp1_loop_a",
  "status": "PASS",
  "provenance": {},
  "required_files": {},
  "runtime_schema": {},
  "checker_domain": {},
  "identifier_resolution": {},
  "metric_pipeline": {},
  "scoring_inputs": {},
  "safety": {},
  "checks": []
}
```

The preflight reads only the pinned candidate/origin metadata needed to validate structure, field names, checker-domain coverage, and identifier resolution. It does not call `recompute_gold`, `score_item`, or any metric on candidate items and does not read any candidate gold field.

Every receipt safety boolean is a labelled object with `value` and `basis`; `basis` is `derived` or `attested: true`. `scoring_inputs_all_synthetic` is derived from the instrumented call log.

## 4. Generated receipt schemas

The canonical `FIXTURE_RECEIPT` is `data/research/tatqa_wp0_2026/wp1/FIXTURE_RECEIPT.json`. The runner writes the same LF JSON bytes to `research/tatqa_wp0_2026/wp1/FIXTURE_RECEIPT.json` as a tracked repository mirror and asserts byte identity. It uses schema `tatqa_wp1_fixture_receipt_v1` and contains `spec_revision`, `task`, `status`, `provenance`, `obligations`, `taxonomy_checks`, `regression_check`, `metric_pipeline`, `scoring_inputs`, `safety`, `receipt_paths`, `cost`, and `deviations`.

`research/tatqa_wp0_2026/wp1/PREREG_DRAFT_SKELETON.md` is a draft-only Markdown file. Actor revision, model, settings, real episode context, analysis implementation, budget/window, and advisor/owner decisions remain exactly `PENDING`.

`research/tatqa_wp0_2026/wp1/WP1_RECEIPT.json` uses schema `tatqa_wp1_receipt_v1` and contains:

```json
{
  "spec_revision": "1.2",
  "task": "tatqa_wp1_loop_a",
  "status": "PASS",
  "start_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "end_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "input_verification": {
    "hashes": {},
    "counts": {},
    "status": "PASS"
  },
  "artifact_hashes": {
    "checker": "",
    "adapter": "",
    "fixtures": "",
    "preflight": "",
    "contract": "",
    "fixture_receipt": ""
  },
  "fixture_results": [],
  "preflight_results": [],
  "scoring_inputs": {},
  "safety": {},
  "fixture_receipt": {},
  "cost": {
    "model_calls": 0,
    "endpoint_calls": 0
  },
  "unverified_items": [],
  "deviations": []
}
```

## 5. Exact commands

The implementation must not run a model, endpoint, service, database, training command, network command, loop verifier, commit, or push.

After this contract is written, hash it before creating or running implementation files:

```bash
cd /home/testuser/wzh/projects/agents_final_tech
sha256sum research/tatqa_wp0_2026/wp1/implementation_contract.md > research/tatqa_wp0_2026/wp1/implementation_contract.sha256
sha256sum -c research/tatqa_wp0_2026/wp1/implementation_contract.sha256
```

Implementation and validation:

```bash
cd /home/testuser/wzh/projects/agents_final_tech
python3 -m py_compile research/tatqa_wp0_2026/wp1/checker.py research/tatqa_wp0_2026/wp1/adapter.py research/tatqa_wp0_2026/wp1/provenance.py research/tatqa_wp0_2026/wp1/run_fixtures.py
python3 research/tatqa_wp0_2026/wp1/run_fixtures.py
python3 -m json.tool research/tatqa_wp0_2026/wp1/PREFLIGHT_RECEIPT.json >/dev/null
python3 -m json.tool data/research/tatqa_wp0_2026/wp1/FIXTURE_RECEIPT.json >/dev/null
python3 -m json.tool research/tatqa_wp0_2026/wp1/WP1_RECEIPT.json >/dev/null
```

Final artifact verification:

```bash
cd /home/testuser/wzh/projects/agents_final_tech
sha256sum research/tatqa_wp0_2026/wp1/checker.py research/tatqa_wp0_2026/wp1/adapter.py research/tatqa_wp0_2026/wp1/fixtures/synthetic_fixtures.json research/tatqa_wp0_2026/wp1/PREFLIGHT_RECEIPT.json research/tatqa_wp0_2026/wp1/implementation_contract.md
git status --short -- research/tatqa_wp0_2026/wp1 data/research/tatqa_wp0_2026/wp1
```

## 6. Stop conditions

- Pinned input hash mismatch: report `HASH_MISMATCH` and stop.
- Any of the seven fixture obligations fails: report `SOFTWARE_NOT_QUALIFIED` with the failed obligation and stop without changing the fixture to force a pass.
- Any required forbidden action: stop and report the blocked requirement.
- No scientific result, pilot result, candidate-item score, or held-out outcome is permitted in any receipt.

## 7. Revision 1.1 completion addendum (2026-10-13)

Run 1 (`tatqa-wp1-20261013`) failed closed on `hidden_gold_search` because the original check searched the actor-visible raw cells `late_value` and `early_value`. Revision 1.1 of the governing contract supersedes only that obligation.

The run-2 implementation of `hidden_gold_search`:

- retains the exact forbidden-name search from run 1;
- searches only the checker-rendered `delta_source` and `delta_target` strings;
- applies boundary-aware matching to the full serialized actor-visible projection for every fixture, requiring zero matches and applying no length filter;
- excludes `late_value` and `early_value` from the answer-value search set;
- requires the same boundary-aware search to return zero matches over raw table cells and period labels alone for every fixture, so the search is non-vacuous.

The seven synthetic fixture numbers require no adjustment because all seven satisfy the fixture-design precondition. No checker, adapter, provenance module, pinned input, or scientific item was changed.

Run 2 uses run id `tatqa-wp1b-20261013`. On a passing run it emits these artifacts:

- `research/tatqa_wp0_2026/wp1/PREFLIGHT_RECEIPT.json`
- `data/research/tatqa_wp0_2026/wp1/FIXTURE_RECEIPT.json`
- `research/tatqa_wp0_2026/wp1/WP1_RECEIPT.json`

The generated receipts carry zero model and endpoint calls, per-obligation results, the requested artifact hashes, unverified items, and deviations. This addendum does not change any other obligation or stop condition.

## 8. Revision 1.2 completion addendum (2026-10-13)

Run 3 (`tatqa-wp1c-20261013`) is the final bounded completion under specification revision 1.2:

- answer-value needles use canonical plain-decimal rendering with no trailing zeros or exponent and additionally search exact checker/fixture `str()` forms when different;
- the mandatory positive control injects every needle, including the `1300`/`1300.0` pair and negative `-55`, and fails if any injection is silent;
- byte determinism covers all seven fixtures across all four arms B/E/C/S;
- taxonomy exercises all eight classes including `wrong`, while `regressed` excludes only `refused`/`unknown` from otherwise non-correct answers;
- all safety booleans in generated receipts carry `derived` or `attested: true` basis labels;
- `scoring_inputs_all_synthetic` derives from the instrumented `score_item` call log;
- `WP1_RECEIPT.artifact_hashes.fixture_receipt` pins the canonical data receipt, whose tracked repository mirror is byte-identical;
- all three receipts declare `spec_revision: "1.2"`, and the preregistration skeleton lists the eight outcomes plus pending protocol/item/split/actor freezes and identity-only `target_unit` assignment.

This addendum and the preceding run-2 addendum remain historical evidence for run 1/2; run 3 extends those artifacts in place without weakening the specification.
