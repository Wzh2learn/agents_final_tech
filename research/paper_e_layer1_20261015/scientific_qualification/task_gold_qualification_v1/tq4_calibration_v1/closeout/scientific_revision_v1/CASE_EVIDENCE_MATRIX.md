# CASE_EVIDENCE_MATRIX

> Scope: TQ-5 source-separation developmental run `20261017T072340Z_5d8942bd`, cases T01/T07/T08/T10/T12.
> This matrix preserves the frozen scorer and raw run. It separates source facts, model behavior, and semantic questions that remain open.
> Evidence labels: **直接事实** = readable in frozen material, raw response, prompt, or manifest; **模型输出** = a model-produced string/decision, not ground truth; **待裁决** = requires a task-level semantic judgment or independent adjudication.

## Measurement layers

| layer | what it establishes | what it does not establish |
|---|---|---|
| frozen numeric score | whether the stored answer is numerically within the frozen tolerance | semantic correctness when notation, scope, or precision is underspecified |
| evidence-location legality | whether cited coordinates/UIDs exist and have the required type | that the cited evidence supports the answer |
| B decision | answer-plus-evidence verification in the B prompt surface | an independent human gold label |
| C decision | same-model, separate-context answer comparison in the C prompt surface | an independent oracle or method-superiority result |
| strict output validity | whether the response was parseable under the frozen JSON contract | the truth of any prose outside valid JSON |

The C role is therefore described as **same-model independent-context answer comparison**, not an independent solver. B sees the actor answer, evidence and notes in its prompt; C sees the material and candidate final answer only.

## Summary matrix

| case | frozen score | evidence legality | B | C | direct reading |
|---|---|---|---|---|---|
| T01 | NO_MATCH | legal | accept | accept | source notation, signed reference, and parser normalization diverge |
| T07 | NO_MATCH | illegal | abstain | invalid | reference denominator and question scope are not established; actor output is internally inconsistent |
| T08 | NO_MATCH | legal | alarm | accept | a dated paragraph has provenance but may not satisfy the all-years task scope |
| T10 | NO_MATCH | legal | accept | invalid | rounded output conflicts with a two-decimal frozen tolerance; C prose is not a decision |
| T12 | NO_MATCH | legal | accept | accept | rounded output conflicts with a two-decimal frozen tolerance |

---

## T01 — signed accounting notation

### Question constraints

- Question: `What is the increase/ (decrease) in Pre-tax margin from 2017 to 2018`.
- Period: 2017 -> 2018.
- Quantity: pre-tax margin change; the source table labels the final column `Yr.-to-Yr. Percent/ Margin Change`.
- Output form: the question asks for an increase/decrease but does not specify signed decimal versus source display notation.

### Original material

- Table row `Pre-tax margin`: 2018 = `10.2%`, 2017 = `12.6%`, displayed change = `(2.4)pts.`.
- The actor prompt contains the same table and the two margin values.

### Reference path

- `panel/reference/T01.json`: official answer `-2.4`, derivation `10.2-12.6`, `answer_from=table`, `scale=percent`.
- `panel/scoring/T01.json`: `compare_mode=numeric`, `expected=-2.4`, `abs_tolerance=0.05`.
- Frozen result: `NO_MATCH`; the parser's normalized actor value is `+2.4`, while the reference is `-2.4`.

### Actor output

- Raw: `runs/20261017T072340Z_5d8942bd/raw/0001_actor_T01_original.json`.
- Valid JSON; answer exactly `(2.4)pts.`.
- Evidence: `cell(table_row=10, table_col=3)`.
- Notes say the table explicitly lists `(2.4)pts.` in the last column.

### B/C decisions

- B raw `0013_b_T01_original.json`: valid `accept`; it verifies the cited cell and treats the displayed value as matching the requested increase/decrease.
- C raw `0014_c_T01_original.json`: valid `accept`; `own_answer=(2.4)pts.` and its reason explicitly explains `10.2% - 12.6% = -2.4%`.

### Direct facts

- The source display, actor answer, and B/C answers contain the parenthesized form.
- The frozen numeric scorer preserves a `NO_MATCH` result.
- C's reasoning contains a signed calculation while its final answer remains the source display form.

### Semantic issues still open

- Whether `(2.4)pts.` must be normalized to `-2.4` for scoring.
- Whether the task requests a signed numeric answer or accepts the table's accounting display.
- Whether the discrepancy is a scorer-format limitation, a notation-policy mismatch, or both.
- Status: `UNSCORABLE_FOR_PROVEN_ERROR`; do not count this as a demonstrated actor error or reference error.

---

## T07 — missing denominator and internally inconsistent actor output

### Question constraints

- Question: `What is the value of Kyocera resale products as a percentage of AVX's total sales in 2019?`.
- Period: fiscal 2019.
- Quantity: a percentage with a required denominator named as `AVX's total sales`.

### Original material

- Paragraph `9b4b774f-b16c-4c9c-8570-27e422d1c420`: Kyocera resale-product sales were `$318,928`, `$296,316`, and `$18,951` in fiscal 2017/2018/2019.
- Table row `Product and equipment sales to affliates`: `$30,303`, `$26,069`, `$10,436` for 2017/2018/2019.
- The supplied table contains no `Total Sales` row or other explicit AVX total-sales value.

### Reference path

- `panel/reference/T07.json`: official answer `181.59`, derivation `18,951/10,436`, `answer_from=table-text`, `scale=percent`.
- `panel/scoring/T07.json`: `expected=181.59`, `abs_tolerance=0.005`.
- Frozen result: `NO_MATCH`.

### Actor output

- Raw: `0007_actor_T07_original.json`.
- Valid JSON; answer `0.002`.
- Evidence: paragraph UID `9b4b...` plus `cell(table_row=2, table_col=4)`.
- Mechanical legality is false: the cell is `cell_out_of_bounds`.
- Notes explicitly state that total sales are absent and that the question cannot be answered accurately from the supplied material, then nevertheless return `0.002` because the format requires a string or number.

### B/C decisions

- B raw `0025_b_T07_original.json`: valid `abstain`; B states that the required total-sales denominator is missing and that the material is insufficient.
- C raw `0026_c_T07_original.json`: `json_parse_error`, `finish_reason=length`, 2,048 completion tokens. The prose repeatedly says total sales are missing, discusses external AVX revenue figures, and is not converted into an accept/alarm/abstain decision.

### Direct facts

- The reference path divides the paragraph numerator by an affiliate-sales table row, while the question names total sales.
- Actor `answer=0.002` conflicts with its own notes' stated insufficiency.
- B's valid decision is `abstain`; C has no valid decision.
- The frozen evidence checker reports one out-of-bounds citation.

### Semantic issues still open

- Whether `Product and equipment sales to affliates` is an intended proxy for `total sales` under the source record.
- Whether the question/reference pair is semantically qualified at all.
- How to adjudicate an actor whose notes reject the task but whose final field supplies a number.
- Status: `UNSCORABLE`; do not convert the frozen `NO_MATCH` into a model-error label.

---

## T08 — provenance is not task-scope satisfaction

### Question constraints

- Question: `About how many common shares were there in total for all years?`.
- Period/scope phrase: `for all years` over the table's 2017, 2018, and 2019 rows.
- Quantity: common shares, with table units stated as millions except per-share amounts.

### Original material

- Table: 2017 dividends `$119.7`, per-share `$0.64`; 2018 `102.9`, `$0.64`; 2019 `99.1`, `$0.64`; total dividends `$321.7`.
- Paragraph `93af6cb1-6058-4f72-b556-49018e175fc6`: `154.7 million` shares issued and outstanding **as of February 21, 2020**.
- The paragraph has a real source location and date; it does not state a 2017-2019 aggregate share count.

### Reference path

- `panel/reference/T08.json`: official answer `502.66`, derivation `321.7/0.64`, `answer_from=table`, `scale=million`.
- `panel/scoring/T08.json`: `expected=502.66`, `abs_tolerance=0.005`.
- Frozen result: `NO_MATCH`.

### Actor output

- Raw: `0008_actor_T08_original.json`.
- Valid JSON; answer `154.7 million`.
- Evidence: paragraph UID `93af...`.
- Notes say the paragraph's 154.7 million figure is the only explicit share count in the supplied text.

### B/C decisions

- B raw `0028_b_T08_original.json`: valid `alarm`, with three contradiction points: the cited paragraph is dated 2020, the question asks for all years, and the table's historical rows are 2017-2019.
- C raw `0027_c_T08_original.json`: valid `accept`, `own_answer=154.7 million`; it treats the paragraph as the only explicit total share count.
- B's prompt contains the actor's answer, evidence, and notes. C's prompt contains the material and the final answer only.

### Direct facts

- The actor answer has a source citation and a date.
- The cited date is outside the table's 2017-2019 period.
- B and C receive different candidate information surfaces: B sees evidence/notes; C sees only the final answer.
- The reference arithmetic is reproducible from the table, but its interpretation of `all years` is not independently adjudicated.

### Semantic issues still open

- Whether `for all years` means summing implied annual share counts (`321.7/0.64`), averaging, or asking for a point-in-time count.
- Whether a dated paragraph can satisfy a historical aggregate question merely because it has a citation.
- Status: `REFERENCE_UNCERTAINTY`; use the case to discuss **provenance versus scope satisfaction**, not to claim a common checker blind spot or method superiority.

---

## T10 — precision policy and wrong-period evidence

### Question constraints

- Question: `What was the percentage change in total revenue between 2017 and 2018?`.
- Period: 2017 -> 2018; the table's explicit variance column is `2019 vs. 2018`, not the requested period.
- Output precision: not specified in the question.

### Original material

- Table total row: 2019 `$39,005`, 2018 `$36,709`, 2017 `$35,705`; variance column for 2019 vs. 2018 is `6%`.
- Paragraph `e1c36869-8727-4353-a315-f2f0fb257254`: amounts and percentages may not recalculate due to rounding.
- The actor prompt contains the table and paragraph.

### Reference path

- `panel/reference/T10.json`: official answer `2.81`, derivation `(36,709-35,705)/35,705`, `answer_from=table-text`, `scale=percent`.
- `panel/scoring/T10.json`: `expected=2.81`, `abs_tolerance=0.005`.
- Frozen result: `NO_MATCH`.

### Actor output

- Raw: `0010_actor_T10_original.json`.
- Valid JSON; answer `3%`.
- Evidence: row 6, columns 4, 2, and 3. Column 4 is the wrong-period variance cell; columns 2 and 3 are the requested 2018 and 2017 totals.
- Notes compute `(36,709-35,705)/35,705 = 2.81%` and round to `3%`.

### B/C decisions

- B raw `0032_b_T10_original.json`: valid `accept`; recompute field records `2.81% -> 3%`.
- C raw `0031_c_T10_original.json`: `json_parse_error`, `finish_reason=length`, 2,048 completion tokens. Its prose starts with `decision: alarm`, repeatedly concludes the rounded answer is acceptable, and ends with a partial `Decision: Accept`; none of this is a valid model decision.

### Direct facts

- The actor arithmetic is documented and agrees with the reference derivation before rounding.
- The frozen scorer rejects `3%` because its tolerance is `0.005` around `2.81`.
- B accepts the rounded form; C's text is invalid and internally oscillates.
- Evidence-location legality is true even though one cited cell concerns the wrong period; citation support was not separately scored.

### Semantic issues still open

- Whether the question's missing precision requirement permits whole-percent rounding.
- Whether the frozen tolerance is a deliberate answer contract or an implicit precision requirement.
- Whether wrong-period evidence should change the support judgment even when coordinates are legal.
- Status: `UNSCORABLE_FOR_PROVEN_ERROR`; keep frozen `NO_MATCH` and do not call the actor wrong without semantic adjudication.

---

## T12 — rounding against reference precision

### Question constraints

- Question: `What was the percentage change in revenues between 2018 and 2019?`.
- Period: 2018 -> 2019.
- Output precision: not specified in the question.

### Original material

- Table revenue row: 2019 `$1,177.2`, 2018 `$1,114.0`, 2017 `$1,051.6`.
- The table is in millions and the question asks for percentage change.

### Reference path

- `panel/reference/T12.json`: official answer `5.67`, derivation `(1,177.2-1,114.0)/1,114.0`, `answer_from=table`, `scale=percent`.
- `panel/scoring/T12.json`: `expected=5.67`, `abs_tolerance=0.005`.
- Frozen result: `NO_MATCH`.

### Actor output

- Raw: `0012_actor_T12_original.json`.
- Valid JSON; answer `5.7%`.
- Evidence: row 1, columns 2 and 1 (2019 and 2018 revenue cells).
- Notes compute `0.05655...` and round to `5.7%`.

### B/C decisions

- B raw `0036_b_T12_original.json`: valid `accept`; recompute field records `0.056553... -> 5.7%`.
- C raw `0035_c_T12_original.json`: valid `accept`, `own_answer=5.7%`; it independently computes approximately `5.673%` and rounds to one decimal.

### Direct facts

- Actor, B, and C use the same two table cells and the same calculation.
- The frozen scorer expects two decimals (`5.67`) and rejects the one-decimal rendering (`5.7%`).
- No evidence-location violation or output parse failure occurs.

### Semantic issues still open

- Whether one-decimal rounding is an acceptable answer for an unspecified precision question.
- Whether the reference's decimal count should define a hard response precision contract.
- Status: `UNSCORABLE_FOR_PROVEN_ERROR`; report as a precision-policy mismatch, not a confirmed semantic error.

## Cross-case interpretation

1. A `NO_MATCH` can arise from notation normalization (T01), missing/incorrect reference scope (T07/T08), or precision policy (T10/T12). The frozen label alone does not identify the cause.
2. A valid citation is not proof of task-scope satisfaction (T08), and a legal coordinate is not proof of evidential support (T10).
3. B and C are not comparable oracle methods: B sees answer/evidence/notes, while C sees answer only and is a same-model, independent-context comparison. Their decisions cannot support C-vs-B superiority.
4. C's invalid prose remains invalid even when it contains an apparent decision or a plausible explanation (T07/T10).
5. Independent human semantic gold is required for a final error/accuracy claim, but not for the directly verifiable artifact, arithmetic, parser, and prompt-surface facts recorded above.
