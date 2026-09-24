# Independent Loop C audit of reports/LC-RESEARCH-001-ONLINE.md (model qwen3.8-max)

> Dispatched by Loop D on 2026-09-24; evidence packet inline (ONLINE report, zero-model facts, 95-code fail-code inventory, verified cite-key pool), no tools, 1 turn(s), cost $0.3876.
> Verdict: PASS_WITH_NOTES; no fabricated fail code, head, sha256 or venue; all REJECT triggers clear.
> Body is the session final message verbatim; Loop D response appended below.

# INDEPENDENT LOOP C AUDIT — reports/LC-RESEARCH-001-ONLINE.md

## VERDICT: **PASS_WITH_NOTES**

No fabricated fail code, head, sha256, or venue was found. All REJECT triggers are clear. Notes below concern provenance of metadata not present in the inline facts block and items unverifiable from the audit excerpt; none is disqualifying.

---

## Check-by-check results

**Check 1 — Provenance table vs zero-model facts: PASS (with one note, F1).**
Field-by-field comparison:
- `finqa`: head `0f16e2867befa6840783e58be38c9efb9229d742`, `license_http=200`, `bytes=1067`, sha256 `92c0e67b…9ac087` — all four match the facts line exactly (full strings compared, character-exact).
- `convfinqa`: head `cf3eed2d5984960bf06bb8145bcea5e80b0222a6`, 200, 1067, `5c7b6fe2…34fb4c` — exact match.
- `valentine_nyc`: head empty ("*(empty — unresolved)*" correctly reflects `head=` empty), `license_http=307`, 64 bytes, `92a6e3d1…c741b3` — exact match.
- Retrieval times: **not present in the facts block** → Finding F1.

**Check 2 — Licence scopes quoted, not paraphrased: PASS with notes (F2, F3).** The finqa quote wording matches canonical MIT permission-paragraph text ("Permission is hereby granted, free of charge, to any person obtaining a copy…"), and the Apache quote matches the canonical Apache-2.0 header lines; no paraphrase detected. However the excerpt-vs-hashed-body relationship is imperfectly labeled (F2), and the licence excerpt source block itself was not included in the audit packet (F4).

**Check 3 — Seven role drafts complete; fail codes verbatim: PASS.** Each of §3.1–§3.7 carries an explicit **Owner / Source / Machine acceptance / Dependency** quadruple. Every cited fail code was matched character-exact against the 95-code inventory: `missing_required_role` (:528), `feature_ledger_source_hash_mismatch` (:699), `licence_artifact_hash_mismatch` (:869), `parser_input_hash_mismatch` (:1007), `label_not_q3` (:781), `invalid_gold_action` (:784), `insufficient_independent_reviewers` (:796), `invalid_reviewer_label` (:804), `gold_review_mismatch` (:814), `missing_adjudication` (:818), `invalid_adjudication` (:823), `gold_adjudication_mismatch` (:827), `missing_label` (:833), `licence_not_accepted` (:847), `missing_acceptance_owner` (:849), `invalid_acceptance_time` (:851), `missing_permitted_use` (:855), `missing_confidence_field` (:886), `missing_confidence_source` (:888), `invalid_missing_policy` (:890), `gain_collateral_substitution_forbidden` (:892), `invalid_confidence_vocabulary` (:899), `ambiguous_legacy_statistical_field` (:911), `parser_contract_not_passed` (:990), `missing_parser_checker` (:992), `invalid_parser_commit` (:994), `invalid_parser_execution_time` (:996), `feature_ledger_identity_mismatch` (:740), `feature_ledger_proposal_coverage_mismatch` (:742). Zero fabricated codes. Gate names used in bindings (`artifact_integrity`, `independent_correctness`, `licence_permission`, `confidence_provenance`, `analysis_plan`, `parser_contract`) all appear as gates in the inventory. Role arithmetic is coherent: "nine required roles minus these seven leaves `source_tables` and `injection_map`" (9−7=2), and §3.3's five hash-bound artifacts `{source_tables, schema, injection_map, label_ledger, learnability_feature_ledger}` are consistent with that split.

**Check 4 — Citations/venues within pool: PASS.** All 24 keys cited in §2.1 and §4 (`fan2026agentprocessbench`, `chung2026webstep`, `wang2026gta2`, `zheng2023judge`, `li2025robustjudge`, `li2025scoringbias`, `li2024pedants`, `messing2026measurementerror`, `ross2024goodmetric`, `amrhein2022aces`, `amrhein2023aceswmt`, `moghe2024acesjournal`, `cho2025metamorphic`, `tan2026agentchaos`, `hinton2015distilling`, `gou2021kdsurvey`, `xu2024kdsurveyllm`, `qiu2025agentdistill`, `liu2025structuredagent`, `kendiukhov2026ranking`, `du2026promptranking`, `deviyani2025contextual`, `chen2026counteraction`, `ma2026mopd`) exist verbatim in the verified pool — the report uses the entire pool and nothing outside it. No venue, journal, or conference name appears anywhere; sources are described only as generic "lines". Unmapped keys are explicitly declared unmapped and not load-bearing.

**Check 5 — Call accounting / DATA_NO_GO / no bodies / no tokens: PASS (with note F5).** Arithmetic is coherent: 3 + 31 + 1 = 35; 200 − 35 = 165, matching the table ("**Total consumed** | **35**", "**Remaining headroom** | **165**"). DATA_NO_GO is stated unchanged twice (header "**DATA_NO_GO (unchanged)**" and compliance item 1, which also disclaims any gate pass: "no gate (`SOURCE_GO`, `LABEL_GO`, or any manifest precheck) is claimed passed"). No dataset bodies: only "1067 B (finqa licence), 1067 B (convfinqa licence), 64 B (valentine redirect body)" — consistent with the facts block, which lists licence probes only. No tokens: the report contains hashes, HTTP statuses, and hex commits only; no credential-shaped material anywhere.

**Check 6 — P1/P2 stream separation: PASS.** Separate source IDs and provenance rows; §2.1 (P1) and §2.2 (P2) are distinct sections; §2.2 states "No P1 hash, head, or licence statement is transferred into this lane"; §3.4 scopes the confidence field to P1 only ("for P1 this must be located in the official FinQA/ConvFinQA metadata"); §4 separates "P1 process-checkpoint suitability" from "P2 contextual schema-action framing" and states "P1 and P2 literature support is reported separately and never spliced"; the ordering rule bars P2 from entering "ahead of P1". No splice instance found.

---

## Numbered findings

**F1 — Retrieval times are not in the zero-model facts block. Severity: MINOR.**
Evidence: the table asserts "Retrieval time (UTC) | 2026-09-24T08:05Z" for all three sources, but each facts line contains only `repo=`, `head=`, `license_http=`, `bytes=`, `sha256=` — no timestamp. The value traces only to the report's own header ("Provenance snapshot time: 2026-09-24T08:05Z"), which is self-referential, and is consistent with the dispatch date ("dispatched 2026-09-24"). Not a REJECT trigger (not a head, sha256, fail code, or venue), but it is metadata presented as probe output without a quoted probe source.
Fix: label the column "Snapshot time (packet header; per-source timestamps absent from facts block)" or cite the packet line that supplies it.

**F2 — finqa licence quote lacks the "excerpt" label carried by the convfinqa row, and omits the MIT disclaimer clause. Severity: MINOR.**
Evidence: the finqa cell presents a long quote ending "…in all copies or substantial portions of the Software." with no excerpt qualifier, while the convfinqa cell says "(excerpt scope as provided inline…)". Canonical MIT text continues with the "THE SOFTWARE IS PROVIDED \"AS IS\"" disclaimer; if the hashed 1067-byte body includes it, the finqa quote is a partial excerpt of the hashed body and should say so. Quote wording itself matches canonical MIT verbatim — no paraphrase, no fabrication trigger. (Positive consistency note: equal 1067-byte counts with distinct sha256 are exactly what a 2021↔2022 copyright-year-only difference predicts, as the report itself argues.)
Fix: add "(excerpt scope as provided inline)" to the finqa row and state whether 1067 B is the full body or the excerpt's source body.

**F3 — Valentine 307 handling is correct, but the byte-count contradiction between quote and body is left implicit. Severity: INFORMATIONAL.**
Evidence: the quoted Apache header (~140 characters) demonstrably cannot be the content of the "64-byte" 307 body; the report already handles this honestly — "The 64-byte sha256 above is the hash of the redirect response, *not* of a confirmed full Apache-2.0 licence text" and "recorded as *indicative scope only*, never as accepted licence evidence" — and correctly concludes "P2 cannot pass `SOURCE_GO`". This is the desired failure behavior, not a defect.
Fix (optional): state explicitly that the inline Apache excerpt was not retrieved by the 307 probe, to preempt a reader assuming the quote is the 64-byte body.

**F4 — Contract constants and rulings cited in §3 are outside the three inline evidence blocks supplied to this audit. Severity: MINOR (unverifiable-here, not contradicted).**
Evidence: `REQUIRED_ROLES`, `LABEL_FIELDS`, `VALID_ACTIONS`, `REQUIRED_USES`, `REQUIRED_HOLM_FAMILIES` (incl. `H3a_uid_any_harm`, `H2a/H2b/H2c`, `H3a_valid_rule_retention`), `REQUIRED_NONINFERIORITY_MARGINS`, `REQUIRED_PRIMARY_METRICS`, `REQUIRED_MDE_CONTRASTS`, `COMMIT_RE`, `SHA256_RE`, rulings D7–D11, and the path "research/phase1a_learnability_baselines.py::_check_uid_floor_consistency" are attributed to the packet's contract-constants/offline-record blocks, which were not included in the audit excerpt. Nothing in them conflicts with the 95-code inventory, and all fail codes drawn from those sections verify (Check 3).
Fix: Loop D to spot-verify §3.5's 18-key list and the D11 consistency-check path against the packet's contract-constants block before acceptance.

**F5 — Turn accounting is coherent but under-decomposed. Severity: INFORMATIONAL.**
Evidence: header says "Two earlier tool-enabled attempts (30-turn cap) were aborted without output", while the table gives a single lumped "Prior aborted session turns | 31". 31 ≤ 2×30, so no cap violation, but the split (e.g., 30+1) is not shown; likewise "Canaries (failed or passed) | 3" and the preserved-stream paths ("/tmp/lc_online_result.json and /tmp/lc_online.stream equivalents") are not verifiable from inline evidence.
Fix: report per-attempt turn counts and canary identifiers in the accounting table.

---

## Suggested fixes (consolidated)

1. Annotate the Retrieval-time column with its actual source (packet snapshot header) — F1.
2. Add the "excerpt scope as provided inline" qualifier to the finqa licence cell and clarify excerpt-vs-1067-byte-body — F2.
3. Add one sentence to §1's P2 caveat noting the inline Apache excerpt was not the content of the 307/64-byte probe — F3.
4. Loop D verification pass of §3.5 constants and the `_check_uid_floor_consistency` reference against the contract-constants block — F4.
5. Decompose the 31 prior turns per attempt and name the 3 canaries — F5.

None of the fixes requires re-running the online probe or alters DATA_NO_GO. The report's core discipline — exact hash/head reproduction, honest P2 blocking, verbatim fail-code citation, closed cite-key pool, coherent 35/200 accounting, and strict P1/P2 lane separation — is confirmed. **PASS_WITH_NOTES.**

## Loop D response to findings (2026-09-24)

- F1 (retrieval times): accepted. The times live in the packet snapshot header and in
  /tmp/prov_20260924/retrieved_at.txt on GB10: finqa and convfinqa 2026-09-24T08:05:05Z,
  valentine_nyc 2026-09-24T08:05:21Z. The report table cites them; their storage location is now stated here.
- F2 and F3 (excerpt scope): accepted as editorial; the finqa licence excerpt is the first 14 lines of the
  1067-byte body, and the inline Apache excerpt was provided in the packet, not produced by the 307 probe.
  No re-probe is performed; both qualifiers are recorded here rather than by editing the audited report.
- F4 (constants outside the audit excerpt): spot-verified by Loop D against source at commit a0f4d3d:
  the 18-key analysis_plan list matches the validator reads documented in the DATA_NO_GO addendum B, and
  _check_uid_floor_consistency exists in research/phase1a_learnability_baselines.py (introduced by commit
  7b113fe). Nothing in the audited report conflicts with the contract.
- F5 (accounting decomposition): corrected here: the ONLINE card had exactly ONE tool-enabled aborted
  session of 31 turns (the two killed sessions audit2/review_qwen2 belonged to the audit and review lines,
  not to this card); canaries were mimo-v2.6-flash (failed, request_id d904c6d9-d91c-4bd2-83cc-b022810425ed),
  mimo-v2.6-pro (failed, request_id 711a3af0-ba21-414c-bf9a-de85b4d4afcc) and qwen3.8-max (passed, DS_OK).
- Verdict stands at PASS_WITH_NOTES; the card remains DONE with this audit attached in the queue record.
