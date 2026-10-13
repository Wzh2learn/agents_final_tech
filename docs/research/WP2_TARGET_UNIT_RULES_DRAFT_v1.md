# WP-2 `target_unit` Rules Draft v1

> date: 2026-10-13 | status: `DRAFT_PENDING_OWNER_ADVISOR_DECISION`
> scope: target-unit assignment and period alignment at WP-2 item freeze; no production write, no item freeze, no model call.

## 1. Decision required

All 60 v1 candidates omit `target_unit`. The adapter currently treats an absent target as identity conversion. This draft enumerates the options and proposes a default, but it does not freeze the rule.

The v2 draft builder additionally exposes a source-unit resolution problem: its 352 candidates contain `source_unit=null` for 312 items, `currency` for 36, `%` for 2, and `million` for 2. These counts do not qualify the list for execution; they show why source-unit recovery and the target-unit decision must precede S7 freeze.

## 2. Options

| Option | Rule | Benefit | Risk |
|---|---|---|---|
| A. Conservative identity | Absent `target_unit` means `target_unit = source_unit`; explicit target values may use only a frozen conversion table. | Lowest ambiguity; preserves v1 candidates. | Does not exercise cross-scale reasoning. |
| B. Scale-authorized conversion | Permit `thousand -> unit`, `million -> thousand`, and `billion -> million` only when explicitly assigned. | Exercises the existing conversion contract and unit errors. | Requires a reviewed mapping and item-level assignment. |
| C. Broad unit conversion | Add currency and other cross-unit conversions. | More variety. | Requires exchange rates, denomination knowledge, and a larger failure surface; not recommended for WP-2. |

Percent handling is separate from magnitude scaling: a percentage delta is reported in percentage points, with `percent -> percent` as identity. Currency is not converted unless both currency and denomination are explicit; a generic `currency` label is insufficient.

## 3. Recommended default

Use Option A for every item unless an explicit, reviewed Option B assignment exists:

1. `target_unit` absent or null means `target_unit = source_unit`;
2. `thousand`, `million`, and `billion` conversions are integer powers of ten only;
3. `percent -> percent` is identity and the result unit is percentage points;
4. currency identity is allowed only for the same explicit currency and denomination;
5. period order is always `[late, early]`, and the source delta is `value(late) - value(early)`;
6. an equivalent early-minus-late answer must negate both deltas and retain the target unit;
7. unsupported or ambiguous labels fail closed rather than being guessed.

## 4. Examples

| Source cell pair | Source unit | Target | Gold delta |
|---|---|---|---:|
| `2.5 - 1.2` | thousand | unit | `1.3` source = `1,300` target |
| `4.2 - 1.7` | million | thousand | `2.5` source = `2,500` target |
| `3.8 - 2.1` | billion | million | `1.7` source = `1,700` target |
| `6.5% - 3.5%` | percent | percent | `3.0` percentage points |
| `(2,613) - 2,792` | explicit USD million | explicit USD million | `-5,405` million |

The last example is identity because the unit is unchanged; the minus sign must not be discarded by a thousands-separator or parentheses parser.

## 5. Residual 1: `gold_delta_source_unit`

The field name is a naming trap: its value is the delta expressed in source units, not a unit string. Resolution proposal:

- preserve the frozen JSON field name for compatibility;
- document the semantic alias `gold_delta_value_in_source_unit`;
- validate that the value is numeric and the `source_unit` field is the unit string;
- never parse `gold_delta_source_unit` as a unit.

## 6. Residual 2: absent `target_unit`

The resolution proposal is Option A identity semantics, implemented explicitly at adapter preparation:

- normalize the source unit first;
- derive `target_unit = normalized_source_unit` when the field is absent or null;
- reject explicit targets outside the frozen conversion set;
- record identity assignments in the future freeze manifest rather than silently leaving the field ambiguous.

This draft remains `PENDING_OWNER_ADVISOR_DECISION`; item v2 remains `DRAFT_NOT_FROZEN`.

## 7. Status addendum (2026-10-14)
- Owner authorization and the pilot-eligibility closure are recorded in [`WP2_F5_ELIGIBILITY_DECISION_v1.md`](WP2_F5_ELIGIBILITY_DECISION_v1.md).
- The decision sets fail-closed generic-currency exclusion and explicit null/absent source-unit identity; item freeze remains S7.
- Deterministic eligibility evidence is [`PILOT_ELIGIBILITY_RECEIPT.json`](../research/tatqa_wp0_2026/wp2/PILOT_ELIGIBILITY_RECEIPT.json).
