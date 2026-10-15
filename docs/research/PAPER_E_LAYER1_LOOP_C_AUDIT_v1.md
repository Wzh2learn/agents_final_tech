# Paper E Layer-1 Loop C Audit v1

> Date: 2026-10-15  
> Auditor: Loop D fresh-context re-audit after the GB10 Loop C harness produced no progress for an extended period  
> Scope: read-only audit of the Layer-1 independent-gold run; no manuscript, frozen input, or frozen result was modified

## Verdict

`CONDITIONAL / GOLD_NOT_ESTABLISHED`

The deterministic execution and arithmetic are internally consistent, and the run correctly stops at
the pre-frozen 30% insufficient-evidence ceiling. However, the contract does not establish a
usable task-level independent gold for Layer 2. The main limitation is that a fixed Levenshtein
nearest-neighbour rule over canonicalized headers is independent of the audited matcher, but it is
not equivalent to TAT-QA task truth and does not execute a downstream task.

## Inputs Audited

- `paper/PAPER_E_LAYER1_INDEPENDENT_GOLD_DESIGN_v1.md`
- `research/paper_e_layer1_20261015/LAYER1_ANALYSIS_PLAN_v1.md`
- `research/paper_e_layer1_20261015/LAYER1_RESULTS_v1.json`
- `research/paper_e_layer1_20261015/LAYER1_RECEIPT_v1.json`
- `research/paper_e_layer1_20261015/LAYER1_SUMMARY_v1.md`

The run was executed on GB10 and copied to the local repository unchanged. The two frozen input
hashes reported by Loop A were independently rechecked on GB10 and matched the expected values.

## Item Findings

| Audit item | Verdict | Finding |
|---|---|---|
| 1. Independence from the audited matcher | `CONDITIONAL` | The rule does not call or reimplement the greedy matcher. Labels derive from the injection map and source-table structure. But the rule is a string-distance proxy, not task-question or downstream-output truth. |
| 2. Outcome-blind dev split | `PASS` | The split uses only the SHA-256 of the injection identifier. It does not inspect the label, checker verdict, or perturbation family before membership is decided. |
| 3. No post-hoc fitting | `CONDITIONAL` | The plan text and implementation match, and the frozen plan hash matches. Freeze timing is nevertheless self-attested by the run rather than externally timestamped before execution. |
| 4. No silent auto-labelling | `PASS` | All 35 `INSUFFICIENT_EVIDENCE` cases remain `U`; none is converted to E or H. |
| 5. Arithmetic | `PASS` | The 2x3 contingency, label counts, co-miss rate, co-alarm rate, and U rate were independently recomputed from the 59 per-case rows and match. |
| 6. Claim boundary | `PASS` | The summary does not claim a population rate, OCR conclusion, or confirmed harmful blind spot. |

## Independent Recomputation

- Dev cases: 59
- Labels: E=12, H=12, U=35
- Checker counts: visible=48, blind=11
- Contingency:

| Checker | E | H | U |
|---|---:|---:|---:|
| visible | 6 | 11 | 31 |
| blind | 6 | 1 | 4 |

- `P(H | blind) = 1/11 = 0.090909...`
- `P(E | visible) = 6/48 = 0.125`
- `U rate = 35/59 = 0.593220...`
- All 59 dev cases have byte-identical target-column values before and after injection.

The U cases decompose into 32 `source_header_empty_after_norm` cases and 3
`nearest_neighbour_tie` cases. This matches the pre-frozen plan, which makes any empty source
header make the whole table undecidable. The result is therefore not an arithmetic bug, but it
shows that the frozen contract is too conservative for this corpus.

## Scientific Interpretation

The result is a genuine feasibility boundary:

1. It does **not** establish independent task-level gold on the current drift-v0 corpus.
2. It does **not** justify the Layer-2 premise that shared-observation checkers co-miss task-relevant errors.
3. The single `H | blind` case is exploratory only and cannot support a harmful-blind-spot claim.
4. The rule must not be relaxed after seeing the 59 labels merely to reduce U.

## Next Options

1. **Human adjudication:** have the owner or advisor adjudicate the 35 U cases using the source
   table, original header, injected header, and the actual TAT-QA task target. This is the smallest
   scientifically clean path, but it is a human decision and cannot be automated by this run.
2. **New contract:** design a v2 task-level contract bound to actual question/answer objects and a
   real downstream execution, then freeze it before a fresh case sample. This is a new scientific
   experiment and requires explicit owner authorization.
3. **Stop Layer 2:** keep Paper E as the current bounded case study and do not claim the upgraded
   shared-observation thesis.

Recommended immediate state: do not enter Layer 2 on the v1 gold. Route the 35 U cases to human
adjudication or close the upgrade branch at this feasibility boundary.

