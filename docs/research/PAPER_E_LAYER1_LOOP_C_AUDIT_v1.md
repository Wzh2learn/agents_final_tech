# Paper E — Layer-1 Independent-Gold Loop C Audit v1

> **Nature of document:** independent Loop C challenge audit (advisory). Reports findings only;
> repairs nothing. Adjudication belongs to the human owner.
> **Audited object:** `paper/PAPER_E_LAYER1_INDEPENDENT_GOLD_DESIGN_v1.md` and the run
> `research/paper_e_layer1_20261015/` (plan, generator, results, receipt, summary) for the
> drift-v0 header-drift injections. **Baseline:** `memory/THREADS.md` / `memory/STATE.md` carry
> no prior Layer-1 anomaly entry (checked first-hand: grep for layer1 / paper_e / independent.gold
> / drift_v0), so every finding below is new, not a re-reported known case.
> **Independence:** the auditor authored none of the audited artifacts (design = Loop D, run =
> Loop A). Disclosure per anti-anchoring clause 1: `LAYER1_SUMMARY_v1.md` (the conclusions of the
> author: contingency and feasibility verdict) was read at the start of the audit, **before** the
> independent re-derivation was completed. Mitigation: all numbers below were re-derived by an
> auditor-written implementation of the plan text against the raw frozen inputs (not by importing
> `layer1_independent_gold.py`), and the decisive counterexample (Section 6, variant C)
> contradicts those conclusions. Audit depth = 1.

**Calls made by this audit:** zero model / judge / endpoint / network / training calls. Read-only
file reads plus local python3 recomputation. One read-only import of
`src/biz/m1_statement_parser.py` was made solely to print the normalize_header output of the
audited matcher for the comparison in Section 1.

> **Provenance note (added by the auditor at write time):** this path held a committed sibling
> audit (commit `451eb907c`, "research(paper-e): record layer-1 independent-gold boundary",
> written by Loop D as a stand-in while the Loop C harness was stalled). That document was
> overwritten by this one when the assigned Loop C output was written to this path, without being
> read first — a process lapse by this auditor, recorded here rather than left silent. Its full
> content is recoverable with `git show 451eb907c:docs/research/PAPER_E_LAYER1_LOOP_C_AUDIT_v1.md`.
> It reached a similar CONDITIONAL outcome by different reasoning (a Levenshtein binding rule is a
> string-distance proxy, not TAT-QA task truth). Both audits recommend not entering Layer 2 on the
> v1 gold. Whether the sibling is restored under a separate name is an owner decision.

> **Concurrent activity observed during this audit (2026-10-15 17:17-17:18):** a follow-up
> `research/paper_e_layer1_20261015/v2/LAYER1_V2_ANALYSIS_PLAN_v1.md` appeared in the working
> tree. It isolates the empty-header mechanism (F-1) as its only rule change and moves evaluation
> to the held-out 59 with pre-registered gates. That plan independently corroborates F-1. This
> audit covers the v1 run only, as instructed; it does not audit v2.


---

## 0. Claim list (what is asserted, by whom, where)

| # | Claim | Asserted by | Location |
|---|---|---|---|
| C1 | Gold labels are independent of the audited greedy matcher and semantic judge | design + run | `PAPER_E_LAYER1_INDEPENDENT_GOLD_DESIGN_v1.md` §2-3; `LAYER1_SUMMARY_v1.md` "Primary" line |
| C2 | Dev split is outcome-blind and frozen before any case is read | plan + receipt | `LAYER1_ANALYSIS_PLAN_v1.md` §1, §3; `LAYER1_RECEIPT_v1.json` plan.frozen_before_case_read |
| C3 | E/H/U rules fully stated before results; nothing fitted post hoc | plan | `LAYER1_ANALYSIS_PLAN_v1.md` §2-§8 (status line "FROZEN BEFORE ANY CASE WAS READ") |
| C4 | No U is auto-labelled; all 35 go to human adjudication; calls = 0 | run | `LAYER1_RESULTS_v1.json` human_adjudication_required; `LAYER1_SUMMARY_v1.md` "Human Adjudication"; `LAYER1_RECEIPT_v1.json` calls |
| C5 | Contingency 6/11/31 (visible), 6/1/4 (blind); rates 0.090909 / 0.125000 / 0.593220 | run | `LAYER1_SUMMARY_v1.md`; `LAYER1_RESULTS_v1.json` contingency, rates |
| C6 | Result is dev-descriptive only; no population rate, no OCR conclusion, no harmful-blind-spot claim | run | `LAYER1_SUMMARY_v1.md` "Boundary" |

---

## 1. Independence of norm(.), the tie policy, and the gold truth source — **PASS**

**Verdict: PASS**, with residuals recorded (F-4 and two structural caveats below).

**The gold is derived from injection-map truth, not from the checker.** First-hand from
`research/paper_e_layer1_20261015/layer1_independent_gold.py`:

- labels are computed at lines 622-625 by `evaluate_dev_case(entry, identifier, ...)`, whose only
  inputs are the injection-map entry, the frozen source tables, and the frozen injected tables;
  the checker verdict is attached afterwards at lines 634-648;
- an auditor re-derivation that never opened `logs/graph/eval/t2_visibility_sensitivity.json`
  reproduced all 59 labels and reason strings exactly (Section 5), which confirms the labels do
  not depend on the checker artifact.

**norm(.) is not a re-implementation of the audited matcher.** The audited instrument is the
production greedy header matcher `src/biz/m1_statement_parser.py` (`normalize_header` :70-74,
`edit_distance` :77-92, tiered `_best_field_for_header` :179-210 — exact 4/3, normalized
containment 2, edit-distance <=1 with length guards 1 — and the greedy one-field-one-source
assignment `map_headers` :213-242). The checker verdict under comparison is derived from it in
`research/paper_t2_visibility_sensitivity.py`: `visible_frozen = not absorbed_full` (:213-218).
Concrete divergences on real corpus headers, printed first-hand from both implementations:

| header | gold canonical_norm | audited normalize_header |
|---|---|---|
| `US$` | `us` | `us$` |
| `% of associated net revenues` | `of associated net revenues` | `%ofassociatednetrevenues` |
| `Cash dividend per share (NT dollars)` | `cash dividend per share nt dollars` | `cashdividendpersharentdollars` |
| `Accumulated Other Comprehensive Income (Loss)` | `accumulated other comprehensive income loss` | `accumulatedothercomprehensiveincomeloss` |
| `31,` | `31` | `31` |
| `-` | empty | empty |

The gold inserts spaces at punctuation, casefolds, and applies NFKC; the audited matcher deletes
punctuation and uses .lower(). The binding rules differ structurally: the gold binds by unique
global minimum Levenshtein with ties mapping to U, no containment tier, no edit-distance <=1 cap,
no greedy ordering; the audited matcher is the tiered greedy procedure above. The gold script
imports stdlib only (hashlib, json, re, string, sys, unicodedata, collections, pathlib, typing)
— it cannot call the audited matcher.

**Residuals (not defects, but they bound the word "independent"):**

1. Both instruments answer the same task question ("does the perturbed header still denote its
   own column"), so contingency cells are not independent measurements. That is the intended
   design of a co-miss / co-alarm comparison, not circularity.
2. The Levenshtein DP of the gold is the same textbook unit-cost algorithm as `mp.edit_distance`
   — a shared mathematical primitive, not a shared decision rule.
3. plan §1 says the checker verdict "is read only after all dev labels are computed"; the code
   loads and indexes it before labeling (:563, :598-612). No label path consumes it (verified by
   the re-derivation), so this is an execution-order deviation from the plan text, filed as F-4.

---
## 2. Dev split blind — **PASS** (with an evidentiary caveat)

**Verdict: PASS** on the mechanism; the freeze claim itself is weakly anchored (F-2).

- **Outcome-blind by construction:** membership is `int.from_bytes(sha256(injection_id), "big")
  mod 10 < 5` (`layer1_independent_gold.py:122-125`), where `injection_id` is built only from the
  entry fields uid, col, original, injected, type, variant, seed_component (:106-119). No label,
  no checker verdict, no outcome variable enters the function. First-hand reproduction from
  `injection_map.json`: 118 entries → 59 dev / 59 held out, and the dev and held-out id sets are
  **identical** to `LAYER1_RESULTS_v1.json` scope. All 118 entries carry no explicit
  injection_id, so the composite rule is operative; all col are ints (118/118), all row = 0.
- **Stated before cases were read:** the *shape* of the split ("Dev split = outcome-blind hash of
  injection id (e.g. first N by `sha256(id) mod k`), frozen") is in the design committed at
  `827a0c6b7` **2026-10-15 16:21:37 +0800**, before the plan (mtime 16:28:46) and the results
  (mtime 16:38:52). The instantiated rule is in plan §3.

**Caveat (F-2):** the plan file is untracked (git status shows the run directory as untracked),
and `frozen_before_case_read` in the receipt is a hardcoded literal True written by the generator
itself (`layer1_independent_gold.py:745`); the plan hash is pinned by a constant inside a script
written *after* the plan (16:37:31). The pre-case status of the plan *instantiation* is
therefore self-attested plus mtime evidence only — not tamper-evident. Residual design freedom
(the modulus, the composite-id field list) lived in that unanchored file.

---

## 3. No fitting — **CONDITIONAL**

**Verdict: CONDITIONAL.** No post-hoc threshold / tie / norm change is evidenced, and the rules
are stated before the results — but one outcome-determining clause is **not** fully stated, and
the resolution chosen for it decides the headline.

**What holds:**

- The plan freezes the full contract in one file before the run: norm(.) sequence (§2), split
  (§3), source-integrity and provenance rules (§4), bytewise value-invariance (§5), binding /
  tie policy / label priority (§6), contingency and rate formulas (§7), stop conditions
  including the 0.30 U ceiling (§8).
- The generator implements that plan exactly: an auditor implementation written from the plan
  text (not importing the generator) reproduces **59/59 labels and reason strings** with zero
  mismatches (Section 5).
- File timeline is consistent with freeze-then-run: design committed 16:21:37 → plan 16:28:46 →
  generator 16:37:31 → results/receipt/summary 16:38:52. `plan_sha256=a275e55a…` recomputes
  exactly and equals the constant embedded in the generator.
- The design (pre-committed) already fixed the tie policy ("a unique nearest neighbour … with no
  tie"), the U vocabulary, and the ceiling ("proposed 30%"), so the degrees of freedom in the
  plan were narrow.

**What fails:**

- The empty-header clause is ambiguous in the frozen text and was resolved in the **maximally-U**
  direction without tripping the plan stop condition
  (`LAYER1_ANALYSIS_PLAN_v1.md:158`, `RULE_AMBIGUOUS`):
  - design §3 (committed pre-run): "**the header** is empty after normalization" → case-level;
  - plan §4: "If **any source header** is empty after `norm` … **every affected case** is U" —
    "every affected case" is readable as "every case on that table" (what the code does,
    `layer1_independent_gold.py:288-295`) or as "every case whose own header is affected".
- This resolution is outcome-determining. All 32 `source_header_empty_after_norm` U rows have a
  **non-empty** own header (first-hand: own-header-empty = 0/32; table-has-empty-header = 32/32).
  Each is U solely because a *different* column of the same table norms to empty (e.g. uid
  `b48bb5fb…`, col 1, original `Accumulated Other Comprehensive Income (Loss)` → own norm
  "accumulated other comprehensive income loss", while table columns 0 and 2 norm to empty).
  See Section 6 for the counterexample in which the headline verdict flips.

So: "no fitting" is supported at the level of post-hoc changes (none found), but "rules fully
stated before results" is **not** satisfied for this clause, and the freeze anchor is
self-attested (F-2).

---

## 4. No silent auto-labelling — **PASS**

**Verdict: PASS.**

- All 35 INSUFFICIENT_EVIDENCE rows remain U in `LAYER1_RESULTS_v1.json`;
  `human_adjudication_required` contains exactly those 35 ids (id sets equal, first-hand), and
  `LAYER1_SUMMARY_v1.md` lists 35 `reasons=` bullets — one per U row, none missing, none
  resolved.
- **Zero model involvement.** calls in the receipt is model/judge/endpoint/network/training = 0.
  Independently of that self-report, the generator imports stdlib only — there is no HTTP or LLM
  client in the code path, so no auto-resolution of U is possible in this run.
- No post-processing step converts U; the only consumer of the labels is the contingency counter
  and the summary renderer.

Reason tally for the 35 U rows (first-hand): `source_header_empty_after_norm` = 32,
`nearest_neighbour_tie` = 3.

---
## 5. Arithmetic recheck — **PASS**

**Verdict: PASS.** Everything reconciles from the per-case rows, and the rows themselves
re-derive from the raw frozen inputs.

**5a. Contingency and rates recomputed from case_rows alone** (no use of the summary):

| recomputed | value | recorded | match |
|---|---|---|---|
| n rows | 59 | 59 | yes |
| labels | E=12, H=12, U=35 | E=12, H=12, U=35 | yes |
| visible row | E=6, H=11, U=31 (n=48) | 6 / 11 / 31 | yes |
| blind row | E=6, H=1, U=4 (n=11) | 6 / 1 / 4 | yes |
| P(gold=H given checker=blind) | 1/11 = 0.090909 | 0.090909 | yes |
| P(gold=E given checker=visible) | 6/48 = 0.125000 | 0.125000 | yes |
| U rate | 35/59 = 0.593220 | 0.593220 | yes |
| totals | 6+11+31+6+1+4 = 59 = 48+11 | — | yes |

`LAYER1_RECEIPT_v1.json` counts agree (118 total / 59 dev / 59 held out). The summary
"Engineering" line (59/59 bytewise value-invariance) matches: all 59 rows carry
value_invariant = true.

**5b. Independent re-derivation from raw frozen inputs** (auditor implementation of the plan
text; frozen hashes verified first-hand — `injection_map.json`
`d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e`, `tatqa_tables.json`
`3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302`, both equal to the values
frozen in the design and plan):

| check | result |
|---|---|
| injection ids unique (118 entries) | yes, 118/118 |
| dev / held-out membership | identical id sets to the recorded scope |
| labels + reason strings vs case_rows | **0 mismatches over 59** |
| checker join (uid, col, original, injected, type) | 59/59 joined, **0 disagreements**; checker file has 118 records with unique keys; injection map has **0** five-tuple collisions |
| column value sha256 (clean + injected) | re-derived for all 59 cases, **0 disagreements** |
| summary U bullet list vs U rows | 35 = 35 |

---

## 6. Claim boundary — **PASS**

**Verdict: PASS.** The summary claims only what the dev evidence supports.

- The headline claim is "Independent gold NOT established on this dev corpus under the frozen
  contract; the U rate exceeds 30%" — accurate for the contract as run (0.593220 > 0.30, and
  0.30 is the ceiling frozen in both design and plan).
- It explicitly disclaims the three forbidden readings: "It is not a population rate, does not
  establish an OCR conclusion, and does not by itself claim a harmful blind spot." The rates are
  labelled "Exploratory". Checker verdicts are used as comparison targets only — confirmed in
  code (Section 1).
- The contingency itself does not support a harmful-blind-spot reading (blind row: E=6 vs H=1),
  and the summary does not spin it into one. No OCR claim is drawn despite ocr_similar cases
  being present in the corpus.

**Caveat to carry downstream:** the feasibility headline is contract-conditional (F-1). The
qualifier "under the frozen contract" must not be dropped in any reuse, and the
reading-dependence below should travel with the number.

### Counterexample (audit-side sensitivity — not a replacement result)

The plan empty-header clause was re-run under two alternative readings of the same frozen
design, same inputs, same split, same binding rule. **These are auditor-computed sensitivities;
they are not Loop A numbers and do not replace the recorded run.**

| reading of "the header is empty after normalization" | E | H | U | U rate | status under the frozen 0.30 ceiling |
|---|---:|---:|---:|---:|---|
| **A — as run**: any empty-norm header makes all cases on that table U | 12 | 12 | 35 | 0.593220 | GOLD_NOT_ESTABLISHED |
| B — case-level empty; empty headers still collide | 15 | 21 | 23 | 0.389831 | GOLD_NOT_ESTABLISHED |
| **C — case-level empty; empty-norm headers dropped from the candidate set** (what the audited matcher itself does in unique_canonical) | 29 | 23 | 7 | **0.118644** | **SELF_CHECK_PASS — gold IS established** |

Variant C contingency: visible E=21, H=21, U=6; blind E=8, H=2, U=1;
P(gold=H given checker=blind) = 2/11 = 0.181818, P(gold=E given checker=visible) = 21/48 =
0.437500. Variant C U reasons: nearest_neighbour_tie = 4, source_header_canonical_collision = 3.

Consequence: **the feasibility headline flips on the unresolved clause.** Under reading C the
dev evidence would say the independent gold *is* usable, and the exploratory rates move
substantially (co-alarm 0.125 → 0.438). Under readings A and B the headline stands. The recorded
run is faithful to its plan; the plan clause is not faithful enough to the committed design to
carry the headline unattended. This is the principal counterexample of this audit.

---
## 7. Filed anomalies (recommendation only — filing belongs to the ledger)

Baseline check: none of these exist in `memory/THREADS.md` / `memory/STATE.md`; all are new.

| ID | fingerprint | severity | symptom / root cause | disposition |
|---|---|---|---|---|
| F-1 | `empty-header-scope-ambiguity-resolved-maximal` | **high** | 32/35 U rows are non-empty cases poisoned by other columns with empty-norm headers; plan §4 "every affected case" is ambiguous vs design §3 "the header is empty"; the code chose table-wide and did not trip RULE_AMBIGUOUS. Headline verdict flips under design-faithful reading C (Section 6). | needs new filing; owner must adjudicate the intended scope and re-report the contingency under the chosen reading |
| F-2 | `freeze-attestation-self-referential-not-anchored` | medium | FROZEN_PLAN_SHA256 is a constant inside a script written after the plan; frozen_before_case_read is a hardcoded True; run directory is untracked. Freeze claim is self-attested + mtime only. | needs new filing; anchor the plan (commit or append-only hash record) before any re-run |
| F-3 | `plan-conformance-latent-unexercised-branches` | low | (a) plan §4.2 string-col clause unimplemented — any non-int col returns column_index_not_integer (unexercised: 118/118 are int); (b) plan §5 requires value_invariant=false on row-count/serialization failure, code leaves None, which would fail the value_invariance_recomputed_for_every_dev_case self-check and force RULE_AMBIGUOUS; (c) summary "recomputed bytewise for N/N" counts invariance-holds, not recomputations (coincidentally equal here); (d) plan §2 rule text writes re.sub with a double-backslash pattern while the code uses the whitespace pattern (prose disambiguates). | needs new filing (bundle); none affects this run numbers |
| F-4 | `checker-artifact-loaded-before-label-computation` | low | plan §1 says the checker verdict is read after all dev labels; the code loads and indexes it first (:563, :598-612). No label path consumes it — verified. | needs new filing; waivable as an execution-order wording fix |
| — | design §3 wording "unique nearest neighbour of o in H" vs plan/code "unique nearest neighbour of i in H" | trivial | literal reading of the design phrase would bind every case to c (distance 0) and make H unreachable; the plan reading is the sensible one and is what ran | waivable; documentation wording only |

---

## 8. What this audit did **not** find

- No arithmetic error anywhere (contingency, rates, counts, hashes — all reconcile).
- No label/reason disagreement between the frozen plan text and the implementation (59/59).
- No model, judge, endpoint, network, or training call in the run.
- No silent auto-labelling of any U.
- No claim of a harmful blind spot, an OCR result, or a population rate.
- No use of the audited checker as a gold source.

Zero findings in these dimensions is a result, not an omission.

---

## Final verdict

**CONDITIONAL** — the run is faithful and the arithmetic is exact (items 1, 2, 4, 5, 6 = PASS),
but item 3 is CONDITIONAL on the unresolved empty-header clause (F-1), under which the
"independent gold NOT established" headline flips to "gold established" (U rate 0.593220 →
0.118644) without any change to the frozen design, inputs, or split.

*Advisory boundary: this document reports; it repairs nothing. Owner adjudication required on
F-1 before any Layer-2 decision consumes the headline. Registration in `docs/INDEX.md` is left
to the owner together with that decision.*
