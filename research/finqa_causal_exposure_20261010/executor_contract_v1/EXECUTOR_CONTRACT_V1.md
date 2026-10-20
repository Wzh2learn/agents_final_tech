# FinQA Executor Contract V1

- Task: `finqa-executor-contract-a-20261019`
- Contract: `finqa-executor-contract-v1`
- Official revision: `0f16e2867befa6840783e58be38c9efb9229d742`
- Exit state: `EXECUTOR_FEASIBILITY_CONDITIONAL`
- Scientific output: none
- Model/judge/API/database/training/service calls: zero

## 1. Authority and boundary

This contract is an isolated executor qualification. It does not import the old
observation scorer, checkpoint scorer, fault adapter, runner, or any Paper E file.
The only external sources are the four pinned official FinQA raw files and the two
frozen staged FinQA JSON files named in the task card.

The official evaluator proves execution against `qa.exe_ans`, not a separately
formatted `qa.answer`. In `evaluate.py:417-445`, execution reads `qa.exe_ans`, executes
the program, and tests exact equality. The pinned evaluator does not define how
`qa.steps[].res` or `qa.answer` strings are rendered from raw execution values.
That missing rendering rule is an explicit blocker rather than an invitation to
repair semantics from the historical reconstructed scorer.

## 2. Officially verified semantics

### Operator grammar

`operation_list.txt:1-10` fixes ten operations:

`add`, `subtract`, `multiply`, `divide`, `exp`, `greater`, `table_sum`,
`table_average`, `table_max`, and `table_min`.

The evaluator accepts only these ten tokens after stripping `(` from each operator
position (`evaluate.py:24-25`, `evaluate.py:82-89`). The official evaluator does not
define normalized dataset forms such as `divide1-2`; executor mutation therefore
uses only the official raw family token. Dataset-only variant normalization is
`UNVERIFIED`.

### Program structure and raw tokenization

The official program tokenizer splits the program on `", "`, emits each `(` and `)`
as a token, and appends `EOF` (`finqa_utils.py:174-191`). The evaluator requires a
four-token shape for every step: operator-with-open-parenthesis, argument 1,
argument 2, and `)` (`evaluate.py:80-113`). V1 rejects every deviation with a typed
code instead of silently accepting the historical evaluator's broad exception.

### Numeric, percent, constant, `none`, and free text

The official `str_to_num` removes commas, then parses a float. If float parsing
fails, it removes every `%`, divides by 100, or removes `const_`, maps the exact
`const_m1` to `-1`, and parses the remainder (`evaluate.py:27-47`). All other text
returns `"n/a"` and execution fails.

V1 verifies the unambiguous corpus forms: numeric literals, canonical percent
literals, `const_m1`, and `const_<numeric>`. It rejects malformed percent or
constant strings that the official source would only reach through an ambiguous
substring branch. `none` is not a numeric token. It is accepted only as the
officially ignored second argument of a table operation; arithmetic `none` fails
closed. Free-text arguments fail closed as `ARGUMENT_NON_NUMERIC`.

### `#k` dependency resolution

For binary operations, `#k` is replaced with step `k`'s raw stored result before
the operation (`evaluate.py:115-133`). V1 requires the reference regex `#k` and
requires `k` to be an earlier step. Forward, malformed, or unresolved references
fail closed.

Table operations do not use `arg2`. Their `arg1` may be a literal first-column
row key (`evaluate.py:153-178`). The official code's `#k` table path references an
uninitialized or stale `num_row`; it is not a deterministic proven dependency and
is rejected as `TABLE_REFERENCE_UNSUPPORTED`.

### Table rows

Table aggregation rebuilds a dictionary keyed by the first cell, discards the key,
removes `$`, truncates at the first `(`, and applies numeric/percent/constant
parsing to every remaining cell (`evaluate.py:49-69`, `evaluate.py:153-178`).
Duplicate row keys follow Python dictionary last-write-wins. Empty-row sums are
zero; empty-row average and extrema fail. Row labels must be string keys in V1.

### Arithmetic and comparison

Binary arithmetic is Python binary float arithmetic:

- `add`, `subtract`, `multiply`, and `divide` use `+`, `-`, `*`, and `/`;
- `exp` uses `**`;
- `greater` returns `"yes"` only when left is strictly greater, otherwise `"no"`;
- therefore a comparison tie is explicitly `"no"` (`evaluate.py:134-150`).

Division by zero, invalid exponentiation, boolean-as-number use, overflow, complex
results, and non-finite values fail closed with typed V1 codes. The pinned source's
non-finite serialization behavior is not a safe contract and is not admitted.

### Precision and terminal answer

Only the final non-boolean result is rounded with Python `round(value, 5)`
(`evaluate.py:186-188`). Intermediate results are not rounded by the executor.
The terminal execution answer is that rounded float, or `"yes"`/`"no"` for
`greater`. The official evaluator compares this value to `qa.exe_ans`
(`evaluate.py:417-445`).

## 3. Unverified rules and blockers

| Code | Missing official proof | V1 behavior |
|---|---|---|
| `STEP_RES_RENDERING_UNVERIFIED` | No pinned rule converts raw intermediate floats to `qa.steps[].res` strings such as rounded percentages or text | Clean replay is unresolved; never claim per-step exactness |
| `DISPLAY_ANSWER_DERIVATION_UNVERIFIED` | No pinned rule converts terminal execution output to formatted `qa.answer` | Display answer is excluded from terminal proof |
| `NORMALIZED_OPERATOR_VARIANT_UNVERIFIED` | Pinned evaluator uses raw operation family only | Only raw operators are legal executor mutations |
| `TABLE_REFERENCE_DEPENDENCY_UNVERIFIED` | Pinned table branch reads stale/uninitialized `num_row` | Fail closed |
| `NON_FINITE_SERIALIZATION_UNVERIFIED` | Pinned source does not define a safe finite contract | Fail closed |
| `COMPLEX_EXP_BEHAVIOR_UNVERIFIED` | Pinned `exp` may produce a Python complex value and gives no terminal serialization rule | Fail closed |

Diagnostic replay comparisons are reported for transparency but labelled
non-contract. They cannot convert an unresolved record into a valid record.

## 4. Mutation contract

Legal executor mutations are exactly:

- P: change one raw `op` field to another official operator;
- N: change one binary `arg1` or `arg2` literal/reference field.

The mutation API rejects `res`, `answer`, `exe_ans`, `terminal_execution_answer`,
and every other field. It proves that exactly the selected legal field changed,
then the executor recomputes all step values and the terminal execution answer
from the mutated program. Manual substantive result/answer controls are segregated
as `SYNTHETIC_CONTROL` detector-fire fixtures and are rejected by the executor
mutation API.

## 5. Fail-closed codes

The implementation returns machine-readable codes for malformed programs,
unsupported operators, malformed/unresolved references, ambiguous percent and
constant tokens, non-numeric/free-text/`none` arithmetic arguments, division by
zero, undefined/overflow/non-finite arithmetic, invalid tables and cells, and
illegal mutation fields or families. The full contract is machine-readable in
`executor_contract_v1.json`.

## 6. Qualification result

The pinned source proves a deterministic terminal execution contract, and all
7,134 frozen records reproduce `qa.exe_ans` exactly. It does not prove the
required `qa.steps[].res` rendering or formatted `qa.answer` derivation. Therefore
the only permitted exit state is `EXECUTOR_FEASIBILITY_CONDITIONAL`.
