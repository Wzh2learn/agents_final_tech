[loop-c] start 2026-10-15T10:35:55Z
ACK pe-l1-v2-preresult-audit: Loop C independent auditor

The write to `research/paper_e_layer1_20261015/v2/LAYER1_V3_FINAL_AUDIT_v1.md` is blocked pending your permission — that is the only write this task needs and the only file the mandate authorizes. The full audit is drafted and ready to commit on approval. Findings below.

## Evidence re-derived (not taken on trust)

- **v1 is pinned by v3 itself.** v1 plan `a275e55a…` = `plan_sha256` inside v1 RESULTS/RECEIPT; v1 results `359c7c04…` = the pin in v3 §5. `git status` clean on all four v1 artifacts. `GOLD_NOT_ESTABLISHED` stands in SUMMARY, RESULTS, RECEIPT (`u_rate_dev=0.593 > 0.30`).
- **Labels exist for the dev 59 only:** all 59 `case_rows` are `split: "dev"` (12E/12H/35U); `held_out_injection_ids` = 59 strings with **no label field**; **no v2 or v3 label artifact exists anywhere**.
- **Manifest pin is byte-exact:** `governing_plan_sha256 = 2472751a…` = SHA-256 of the prereg's bytes. Manifest's own digest `a65f6357…` is pinned by nothing — recorded in the audit as the external anchor.
- **All four pinned inputs resolve and match**, including the checker target `logs/graph/eval/t2_visibility_sensitivity.json` = `eff82b0b…`.
- **Input structure:** 118 injections, `col` integer 0–5 for **118/118** — the string-`col` branch is unreachable on this frozen input.

## Verdicts

| # | Item | Verdict |
|---|---|---|
| 1 | v1 preserved; `GOLD_NOT_ESTABLISHED` not rewritten/suppressed | **PASS** |
| 2 | Rule change isolated | **CONDITIONAL** |
| 3 | Sample genuinely held-out | **PASS** |
| 4 | Gates pre-stated, none from held-out outcomes | **PASS** |
| 5 | No silent `U` relabelling; reasons explicit | **CONDITIONAL** |
| 6 | No premature population/OCR/blind-spot/Layer-2 claim | **PASS** |

Additional conflict check: **PASS** · V3 final check (a)–(d): **PASS** (d carries a note)

**VERDICT: CONDITIONAL**

## What blocks item 2

The six invariants (norm, split, provenance, bytewise invariance, Levenshtein, tie policy) are all verifiably unchanged from v1. But "only empty-header handling changes" is not the whole delta:

- **CE-1 — checker contamination channel.** v1 §1/§7 (and the direct predecessor's §2) bound the checker verdict to a read *only after* labels are frozen. v3 §2 drops that discipline while §5 still pins the checker target — a live artifact whose held-out visible/blind verdicts are readable at any time. Nothing in v3 makes a pre-label checker read invalid. That is the exact channel this prereg exists to protect.
- **A10 — analysis scope silently shrinks.** v1 §7's 2×3 contingency and `co_miss_rate`/`co_alarm_rate` are absent from v3 §7, yet §8.4 promises the post-result audit "recomputes counts and rates"; only `u_rate_heldout` is defined. Under §8.2's own logic ("any scope change beyond the frozen amendment = STOP") that unrecorded delta is what the clause exists to catch.
- **A3 — `norm(.)` is compressed.** v3's one-liner drops v1 §2.4's dual punctuation condition (Unicode category `P` **or** ASCII `string.punctuation`); a reimplementation from v3 text alone can change labels.

## What blocks item 5

- The sentence "every `U` gets exactly one primary reason from the closed list" was dropped (only precedence remains) — A4.
- No closed code for string-`col` resolution failure (A5) — unreachable today on the pinned input, open if inputs change.
- `source_header_set_empty` is **dead code** (step 3 already U's an empty target, and otherwise `c ∈ candidates`) — post-result invariant: its count must be 0 (A6).

## Red flags — all four checked

Dev counterfactual cited as a result: **not found** (fenced as design input; provenance unpinned, A9). Threshold/rule chosen after held-out labels: **not found** (zero held-out labels exist; 0.30 inherited from v1 §8 pre-read freeze; plan hash manifest-pinned). Stop conditions + zero-call: **strong** (`ZERO_CALL_VIOLATION` invalidates the run; v1 held `calls: 0`); gaps are a missing named code for the §8.2 scope-change stop and undefined "required input" for the checker. Replacement wording: **not found** — but the v3 failure string `GOLD_NOT_ESTABLISHED` is byte-identical to v1's status string (CE-5).

## Conflict check + V3 check

Supersession is explicit and a **strict superset** of the mandate (five documents: two plan drafts, two canonical preregs, the delta), all marked non-governing, and **no v2 label exists**, so it precedes any label at all. The column-local collision rule (v3 §2 step 4) is the single governing rule; the table-level rule, the drafts' ambiguous §3.4, and the dead `source_header_canonical_collision` code are all superseded.

(a) amendment recorded in §0 before any v3 label — **PASS**. (b) held-out 59 only, no dev stage, fixed denominator — **PASS**. (c) manifest pins the plan hash and marks five docs non-governing — **PASS**. (d) scope-change STOP clause present — **PASS with a note** (no named stop code, no receipt field).

Also recorded: the mandate's AUDIT SOURCES points at `v2/LAYER1_V3_CANONICAL_PREREG_v1.md`, which does not exist — the audited file is `v3/…` (manifest-pinned). And one held-out composite identifier's header strings were visible while I verified the entries carry no label field; that is the pre-disclosed K4 channel (D1), produced no label.

## Conditions before any held-out label (pre-label only)

- **C1** — bind the checker to post-label read and define the contingency/`co_*` rates, or drop the pin entirely; say whether it is a required input; receipt attests zero pre-freeze checker reads.
- **C2** — bind `norm(.)` to v1 §2's six-step sequence in the receipt.
- **C3** — restate exactly-one-primary-reason; add a code/stop for string-`col` resolution; record `source_header_set_empty == 0` as a post-result invariant.
- **C4** — v3 summary carries v1 §7's full triple fence (population / OCR / harmful blind spot) and qualifies the failure verdict as "v3 (held-out): `GOLD_NOT_ESTABLISHED`".

Discharge: re-freeze the plan + re-pin the manifest (permissible now — zero labels), or receipt-level attestation binding the runner. Not permissible: resolving any of C1–C4 after the first v3 label.

Please approve the write to `research/paper_e_layer1_20261015/v2/LAYER1_V3_FINAL_AUDIT_v1.md` and I'll commit the file as drafted.
