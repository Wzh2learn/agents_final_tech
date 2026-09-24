# Independent Loop C audit of reports/LC-RESEARCH-001-OFFLINE.md (model qwen3.8-max)

> Dispatched by Loop D on 2026-09-24 to close the SCOPED_PASS audit gap of card LC-RESEARCH-001-OFFLINE.
> Mode: evidence packet inline (report + contract fail-code inventory + DATA_NO_GO addendum excerpt), no tools, 1 turn(s), cost $0.8671.
> Body below is the session final message verbatim; assembled by Loop D without edits.

# Loop C Independent Audit — `LC-RESEARCH-001-OFFLINE`

**Auditor:** independent Loop C audit session (this review is the audit that §7 declares PENDING; performing it does not touch the card's GB10-side `calls=0` invariant, which scopes execution, not review).
**Basis:** the report text, the `_fail(...)` grep inventory, and the DATA_NO_GO addendum excerpt (lines 143–242), all inline. No tools used; nothing re-executed; the validator source itself was not available to me.
**Date:** 2026-09-24.

---

## VERDICT: **PASS_WITH_NOTES**

with one **blocking condition**: Finding F1 must be closed (fail-code inventory reconciliation at commit `1627a54`) **before** the acceptance criteria of §3.2, §3.3 and §3.7 are used to accept any real artifact. If reconciliation shows any of the four unverifiable codes does not exist in the validator, this verdict degrades to **REJECT** for the affected subsections.

Rationale for not rejecting outright: every claim I *can* verify against the addendum matches exactly (hashes, byte counts, 118/95, 18 keys, all verbatim tokens, nine ledger constraints, line-range architecture), `DATA_NO_GO` is intact, no gate/threshold is altered, and the one hard-check failure is attributable, on the evidence, to under-capture by the provided grep inventory rather than to fabrication (see F1 mitigation). The report's disclosure hygiene (worktree deviation, `scp`, first-run FAIL, self-triggering marker row, self-classification as `SCOPED_PASS` rather than PASS) is exemplary and argues against concealment.

---

## Check-by-check results

**Check 1 — nine roles mapped; two present roles marked do-not-redeliver with sha256: PASS.**
§2's table carries rows 1–9 plus "+1 package root", i.e. all nine `REQUIRED_ROLES` members (`source_tables`, `injection_map`, `schema`, `label_ledger`, `licence_record`, `confidence_manifest`, `analysis_plan`, `parser_contract_receipt`, `learnability_feature_ledger`) and the root. Both present roles are marked "**PRESENT in production, do not re-deliver**" with full sha256 values — `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302` (1 442 890 B) and `d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e` (36 004 B) — byte-for-byte identical to addendum D, including meta `{deterministic: true, ratio: 0.3, seed: 42, version: v0}` and "118 entries / 95 distinct uids". §5 reinforces: "`source_tables` and `injection_map` must **not** be re-delivered". The 7+1 ask matches addendum D exactly.

**Check 2 — four fields per item; cited fail codes verbatim: PARTIAL FAIL.**
All eight supplement items (§3.1–§3.8) carry Owner, Source, Acceptance and Dependency — consistent with §10's "role subsections `3.1`-`3.8` | 8, each carrying all four labels". Of **29 distinct fail codes cited**, **25 verify verbatim** in the inventory with correct gate attribution; **4 do not appear**: `label_not_q3`, `insufficient_independent_reviewers`, `licence_artifact_hash_mismatch`, `parser_input_hash_mismatch` → **F1**.

**Check 3 — no invented gates, thresholds or numbers: PASS with notes (F4, F6, F8).**
The seven gates named in §2 are exactly the seven gate labels present in the inventory (`analysis_plan`, `artifact_integrity`, `confidence_provenance`, `independent_correctness`, `layer_isolation`, `licence_permission`, `parser_contract`) — no eighth gate is invented, and per-role gate attributions match the inventory's gate column and addendum A. Every addendum-corroborable number matches exactly: 9 roles; 18 `analysis_plan` keys with all verbatim tokens (`approved`, `lineage_uid`, `proposal_dev_only`, `fixed_seed_pair_then_uid_cluster_bootstrap`, `step_down_adjusted_p_and_simultaneous_one_sided_ci`, `H3a_uid_any_harm`, `{delta_quality, delta_harm, delta_retention}` in `[0,1)`, `{action_macro_f1, harmful_map_rate}`, `{map_to, skip, hold}` int `>= 2`, `(0,1)` MDE values); the nine feature-ledger constraints; the rejected candidate's `14 253 B` / `79bc3a17…` / "4 of its 5 table identifiers are CJK" / "2479 identifiers" / overlap 0. Strong corroboration of the line-ref architecture: every addendum-B `analysis_plan` ref (`:910`, `:912`, `:918`, `:920-921`, `:924-935`, `:936-939`, `:940`, `:942`, `:946-953`, `:954`, `:956-961`, `:962-968`, `:976`) falls inside the report's cited `:909-977`, and addendum-A ledger refs fall inside §3.5's cited ranges; `LABEL_FIELDS :72-81` abuts `FEATURE_FIELDS :82-90` as in the addendum. No gate/threshold/oracle change is proposed (§3.6: the selection rule is "**not** encoded in the token and **not** implemented as an algorithm in this batch"; §5: "no gate/threshold/oracle change"). Residual unverifiable numbers are environment/power claims, attributed and non-gate-changing (F8).

**Check 4 — `DATA_NO_GO` unchanged: PASS.**
§2: "`DATA_NO_GO` stands and is **not** lifted by this card." §7: "`DATA_NO_GO` unchanged". §9: "`DATA_NO_GO` is unchanged and is not lifted by this card". §10: "`DATA_NO_GO` stated / `DATA_GO` claimed | yes / no". §4 step 10 gates any future move behind "Double deterministic precheck, zero connect, byte-identical, then **independent** review. Only that can move `DATA_NO_GO`." No `DATA_GO` claim appears anywhere.

**Check 5 — zero-connect and structural-check claims internally consistent: PASS with notes (F2, F3, F10).**
The method (§8: checker "reads only the report file and prints aggregate counts plus a verdict; it contains no network, model or endpoint code path", run under `strace -f -e trace=connect`) is consistent with the measurement (§10: "`connect()` lines in strace | **0**", "checker exit code | `0`"), and the artifact name `/tmp/lc_offline_strace2.txt` independently corroborates the disclosed two-run history ("the first run's strace already showed `connect()` = 0"). The `SCOPED_PASS` self-classification is consistent with §7's "The independent Loop C audit is **PENDING**". Gaps: the PASS verdict covers only the pre-append file (F2), and the literal "NO network" acceptance is admittedly unmet pending ratification of the re-worded line (F3).

---

## Numbered findings

**F1 — Four cited fail codes are absent from the provided inventory. Severity: HIGH (blocking condition on reliance).**
Evidence (report): §3.2 "`quality_grade == \"Q3\"` (`label_not_q3`)" and "`>= 2` distinct non-empty `reviewer_id` (`insufficient_independent_reviewers`)"; §3.1 "in `licence_record.covered_artifact_sha256` (`:856-874`, else `licence_artifact_hash_mismatch`)" and "in `parser_contract_receipt.input_sha256` (`:997-1012`, else `parser_input_hash_mismatch`)"; repeated in §3.3 and §3.7.
Evidence (inventory): the `licence_permission` block contains exactly four codes (`invalid_acceptance_time`, `licence_not_accepted`, `missing_acceptance_owner`, `missing_permitted_use`); the `parser_contract` block exactly four (`invalid_parser_commit`, `invalid_parser_execution_time`, `missing_parser_checker`, `parser_contract_not_passed`); the `independent_correctness` block fifteen, none named `label_not_q3` or `insufficient_independent_reviewers`. This contradicts the report's §1 warrant: "Every acceptance criterion quoted here is a **fail code that already exists in the validator**, not a new invention."
Mitigation (why this is not scored as fabrication): the inventory is **demonstrably non-exhaustive** — addendum A records a *measured* validator output `{"code": "missing_or_mismatched_binding"}`, and that code is also absent from the inventory, so the `grep -oE` pattern provably misses at least one real emission form (e.g. codes built in loops/variables or emitted as dict literals). The report also pins each missing code to a specific line range inside ranges that otherwise cohere with the addendum. Most likely root cause: inventory under-capture. Materiality remains high: if e.g. `label_not_q3` does not exist, a non-Q3 `label_ledger` could pass `independent_correctness`, silently voiding §3.2's acceptance.

**F2 — The structural PASS verdict does not cover the committed text; run timeline underspecified. Severity: MEDIUM.**
Evidence: §10 "This section is appended after the measured run, so the committed file's sha256 necessarily differs from `f6eef52f...`"; table rows "checked file bytes / lines | `20843` / `178`", "structural verdict | **PASS**". The honest note says run 1 failed "on exactly one assertion, `ends_with_newline = false`", yet the post-append correction says the verbatim marker enumeration "made the report trip the very assertion it reports" — implying a further, unreported failing run *after* §10 was appended, then a wording fix "(same card, before commit)" with **no reported re-run**. Net: no measured run validates the final committed artifact; the tabulated PASS/exit-0/markers-0 belongs to a file state that no longer exists. Disclosed in part, but the coverage gap is not stated as such.

**F3 — The card's literal "zero network" acceptance is unmet as executed; met only under the report's own reinterpretation, not yet ratified. Severity: MEDIUM.**
Evidence: §8 "this report's **text was authored off-box by Loop D and transferred with `scp` over the pre-existing SSH channel**. SSH transport is itself a TCP connection, so a literal reading of the card's 'NO network' cannot be satisfied by *any* card executed remotely on GB10"; "Recommendation: re-word that acceptance line to 'no connect to any service or model endpoint; SSH transport excluded'". The measured invariant itself is clean ("`connect()` lines in strace | **0**") and the disclosure is exemplary, but until the card owner/user ratifies the re-wording, acceptance is self-adjudicated by the implementer — the same class of defect §7 elsewhere refuses ("the implementer must not self-verify").

**F4 — The "34 validator line references" metric conflates §8's port tokens with contract line refs. Severity: LOW.**
Evidence: §10 "| validator line references (`:NNN`) | 34 |". Manual count of genuine contract refs in §§2–3.8 yields **28**; §8 contributes seven port tokens (`:5050`, `:8004`, `:8006`, `:8007`, `:8008`, `:4096`, `:15432`). 28 + the six ≤4-digit ports = **34**, i.e. the count is reproducible only if a bounded-digit regex counted service ports as "validator line references" and excluded `:15432`. Harmless, but the metric name overstates what was measured.

**F5 — `REQUIRED_ROLES` line-range drift between report and addendum. Severity: LOW.**
Evidence: report §2 "`REQUIRED_ROLES` (`research/phase1a_data_contract.py:29-39`) has **9** members" vs addendum A "requires **9** (`REQUIRED_ROLES`, `:29-38`)". Both agree on the count and membership; the citation ranges differ by one line (commit drift or inclusive/exclusive convention). Unreconciled citations invite future audit noise.

**F6 — D11 transcription incomplete and status stronger than its source. Severity: LOW.**
Evidence: report §3.6 "must equal the learnability config's `min_dev_uids_by_action` / `min_dev_uids_by_family`" and "(ruling D11, **now enforced**)"; addendum B "must also agree with the learnability config's `min_dev_uids_by_action` / `min_dev_uids_by_family` / **`min_dev_uids`**; a cross-artifact consistency check is **being added**". The report drops the third field and upgrades "being added" to "now enforced" (naming `_check_uid_floor_consistency`). Possibly true at `1627a54`, but not verifiable inline.

**F7 — §3.8 names no consuming gate; `LONGITUDINAL_EVIDENCE_UNAVAILABLE` is not a fail code. Severity: LOW.**
Evidence: §3.8's acceptance (partitions, `MANIFEST_ROW_FIELDS`, `future_replay` protocol) corresponds to the inventory's `layer_isolation` codes (`invalid_partition`, `missing_or_empty_partition`, `future_protocol_not_approved`, `invalid_future_protocol_fields`, …), yet §3.8 alone among the items carries no "gate" label; §10's "machine gates named | 7 / 7" holds only via §2's enumeration. Also "else the report carries `LONGITUDINAL_EVIDENCE_UNAVAILABLE` (`:27`, `:392-450`)" — that string is not in the `_fail` inventory; it reads as a report-level constant, and should be labeled as such so it is not mistaken for a validator fail code.

**F8 — Power-note numbers are not sourced in the provided evidence. Severity: LOW.**
Evidence: §4 "`H3a_uid_any_harm` is pinned to `exact_mcnemar`, so at alpha 0.05 it needs `>= 5` discordant pairs to be able to reach significance" and "The supplement target is 250-500 valid UIDs", flagged only as "carried forward (not re-derived here)" with no document cite; neither figure appears in the addendum excerpt. Assessment: not an invented *gate* — the arithmetic is correct for a **one-sided** exact McNemar (0.5⁵ = 0.03125 < 0.05 ≤ 0.5⁴ = 0.0625) and the contract does mandate one-sided methods; the `>= 2` UID floor it contrasts against is inventory-corroborated; and it explicitly changes nothing ("downgraded to exploratory **without** changing the test"). But α = 0.05 is an assumption pending ruling D8's `significance_level`, and the 250–500 target needs a citation.

**F9 — Tension between §6.2's control-plane actions and §9's single-write red line. Severity: LOW.**
Evidence: §6.2 "Dispatching the two user-authorized research cards therefore required reordering `QUEUE.yaml`" (with backup `/home/testuser/wzh/loopc_backup_20260924b/` and loader runs) vs §9 "Only file written by this card: `reports/LC-RESEARCH-001-OFFLINE.md` (this file)" and "production worktree untouched". Reconcilable — the reorder was a dispatch/control-plane act, disclosed with backup, rc values, and "No status, owner, budget or dependency field was altered" — but the report never says so explicitly, and a priority reorder touching `LC-GOV-002`'s position is governance-relevant enough to warrant an ownership sentence.

**F10 — Header pointer cites the wrong section for the measured evidence. Severity: INFO.**
Evidence: header "GB10-side calls=0 evidence: `strace -f -e trace=connect` over the verification run, section 8" — §8 is method plus the `scp` disclosure; the measured table (connect = 0, exit 0, sha) is §10.

---

## Suggested fixes (mapped to findings)

1. **(F1, blocking)** Re-derive the fail-code inventory at commit `1627a54` with a pattern that captures *all* emission forms — e.g. `grep -nE '_fail\(|"code"\s*:|code='` plus a scan for loop/variable-built codes — and reconcile the four unverified names. Annotate every fail code cited in §3 with its validator line number. If any of the four does not exist, strike or replace it and restate the affected acceptance criterion in §3.2/§3.3/§3.7; if all four exist, publish the corrected inventory alongside this audit so the §1 warrant ("a fail code that already exists in the validator") is verifiable end-to-end.
2. **(F2)** Re-run `/tmp/lc_offline_check.py` under `strace -f -e trace=connect` against the **committed** file; record run 3 (exit code, connect count, bytes/lines, sha256) in the Loop D ledger or a one-line §10 addendum. Relabel the existing table "run 2 — file state: pre-§10, sha `f6eef52f…`" and enumerate runs 1/2/3 explicitly, including the unreported run that tripped the placeholder assertion. State the assertion set was unchanged (already claimed) and attach the checker's sha256 so "no assertion was weakened" is independently checkable.
3. **(F3)** Route the re-worded acceptance line ("no connect to any service or model endpoint; SSH transport excluded") to the card owner/user for ratification; record the ruling ID (D-series) on the card and in the ledger. Until ratified, mark the card's network acceptance as "met under disclosed reinterpretation, ratification pending".
4. **(F4)** Rename the metric to "contract line refs + endpoint port tokens", or tighten the regex to refs adjacent to contract citations and exclude §8 ports; re-report (expected: 28).
5. **(F5)** Pick one citation convention for `REQUIRED_ROLES` (`:29-38` vs `:29-39`) and note the commit each reading was taken at.
6. **(F6)** Add `min_dev_uids` to the D11 sentence; cite the commit/PR in which `_check_uid_floor_consistency` landed to substantiate "now enforced" versus the addendum's "being added".
7. **(F7)** Add "gate `layer_isolation`" to §3.8's header line, and mark `LONGITUDINAL_EVIDENCE_UNAVAILABLE` explicitly as a report-level constant (`:27`), not a validator fail code.
8. **(F8)** Cite the source document for the `exact_mcnemar` pin and the 250–500 UID target (preregistration §7.1 / rulings D7–D12 / the reverification report), and label "alpha 0.05" as an assumption pending D8's `significance_level`.
9. **(F9)** Add one sentence to §6.2 or §9 stating that the `QUEUE.yaml` reorder, backup, and loader `check`/`status` runs were control-plane dispatch actions outside the card's file-write scope.
10. **(F10)** Correct the header pointer from "section 8" to "section 10" (or "sections 8 and 10").

---

## What would change this verdict

- **To REJECT:** proof that any of `label_not_q3`, `insufficient_independent_reviewers`, `licence_artifact_hash_mismatch`, `parser_input_hash_mismatch` does not exist in `research/phase1a_data_contract.py` at `1627a54` (fabricated acceptance criterion); any `DATA_GO` claim or gate/threshold/oracle change (none found); or evidence that the §10 table was reported as covering the committed text (it is not — the divergence is disclosed).
- **To PASS:** closure of F1 via the corrected inventory, plus a run-3 measurement over the committed file (F2) and owner ratification of the re-worded network acceptance (F3). F4–F10 are editorial and do not gate acceptance.

**Audit status of the card:** with this report, the independent Loop C audit required by §7 is **delivered**; the card's own `SCOPED_PASS` may be reconsidered by the control plane only after F1–F3 are closed. `DATA_NO_GO` remains in force; nothing in this audit lifts it.

## Loop D reconciliation of F1 (2026-09-24, post-audit)

- Inventory re-derived at commit 1627a54 (worktree branch gb10/lc-research-20260924) with a digit-aware,
  multiline-tolerant pattern over every  call form: **95 unique codes**
  (full list preserved at /tmp/failcode_inventory_full.txt on GB10).
- All four codes flagged by F1 exist:  (independent_correctness, :781),
   (independent_correctness, :796),
   (licence_permission, :869),
   (parser_contract, :1007).
- Root cause of F1: the inventory handed to the auditor was produced with a single-line, digit-free
  pattern, which dropped multiline calls and any code containing a digit. The auditor checked correctly
  against the inventory it was given; the inventory was the defective input, not the report.
- F1 is therefore closed as an inventory artifact: no acceptance criterion in the audited report cites a
  nonexistent validator code. The audit verdict stands at PASS_WITH_NOTES with the blocking condition
  lifted, and the corrected inventory is published alongside this section.

## Loop D reconciliation of F1 - corrected text (2026-09-24; supersedes the malformed block above)

The block above lost several quoted fragments to shell expansion when it was appended; this block
restates it in full and governs.

- Inventory re-derived at commit 1627a54 (worktree branch gb10/lc-research-20260924) with a digit-aware,
  multiline-tolerant pattern over every _fail( gates, gate-string, code-string ) call form: 95 unique
  codes; full list preserved at /tmp/failcode_inventory_full.txt on GB10.
- All four codes flagged by F1 exist in research/phase1a_data_contract.py: label_not_q3
  (independent_correctness, line 781), insufficient_independent_reviewers (independent_correctness,
  line 796), licence_artifact_hash_mismatch (licence_permission, line 869), parser_input_hash_mismatch
  (parser_contract, line 1007).
- Root cause of F1: the inventory handed to the auditor was produced with a single-line, digit-free
  pattern, which dropped multiline calls and any code containing a digit. The auditor checked correctly
  against the inventory it was given; the inventory was the defective input, not the report.
- F1 is closed as an inventory artifact: no acceptance criterion in the audited report cites a
  nonexistent validator code. The audit verdict stands at PASS_WITH_NOTES with the blocking condition
  lifted, and the corrected inventory is published alongside this section.
- Process note: the earlier block was appended through an unquoted heredoc, so shell expansion stripped
  its backticked fragments; this corrected block is appended in a separate commit and governs.
