# Independent Loop C audit of the confidence_manifest draft and protocol section 5 (model qwen3.8-max)

> Dispatched by Loop D on 2026-09-24; evidence packet inline (draft JSON, protocol section 5, contract code excerpt), no tools, 1 turn(s), cost $0.1559.
> Verdict: PASS_WITH_NOTES; five contract conditions re-derived 5/5; probe data consistent; no fabricated hash, no measured-confidence value.
> Body is the session final message verbatim.

# Independent Loop C Audit — confidence_manifest draft + Protocol §5

**Verdict: PASS_WITH_NOTES**

No fabricated hash and no measured-confidence value detected. All five contract conditions re-derive as satisfied; draft and §5 are mutually consistent on every probe datum.

## Check 1 — Five contract conditions vs. contract code excerpt: 5/5 PASS

Re-derived line-by-line against the excerpt:

1. `field`: `"none_native"` — `isinstance(str)` and truthy → `missing_confidence_field` not triggered. **PASS**
2. `source`: long non-empty string → `missing_confidence_source` not triggered. **PASS**
3. `missing_policy`: `"unmeasurable"` — exact string equality → `invalid_missing_policy` not triggered. **PASS**
4. `gain_collateral_substitution`: JSON literal `false` (unquoted boolean, not `"false"`) parses to Python `False`; `is not False` → False → `gain_collateral_substitution_forbidden` not triggered. **PASS**
5. `allowed_values`: `["low","medium","high"]` — a list, all elements strings, no duplicates; `set(values) == {"low","medium","high"}` → `invalid_confidence_vocabulary` not triggered. **PASS**

Note: the excerpt fires only when `confidence is not None`, i.e., after package binding. The draft's status `DRAFT_COMPLETE_PENDING_PACKAGE_BINDING` and §5's "入 package 时须绑定 sha256 并经独立复核" correctly represent this as a mirror-check of contract logic, not an executed gate. No overclaim.

## Check 2 — Probe claims vs. inline probe record: CONSISTENT

| Datum | Draft `source` | Protocol §5 | Match |
|---|---|---|---|
| finqa bytes | 6518 B | 6 518 B | ✓ |
| finqa sha256 prefix | `eb86779cfed6f0a2...` | `eb86779cfed6f0a2` (labeled 前16位) | ✓ |
| finqa mentions | 0 | 0 | ✓ |
| convfinqa bytes | 6164 B | 6 164 B | ✓ |
| convfinqa prefix | `c5f329640aaffa14...` | `c5f329640aaffa14` | ✓ |
| convfinqa mentions | 0 | 0 | ✓ |
| valentine bytes | 14635 B | 14 635 B | ✓ |
| valentine prefix | `3d484bddcf124bca...` | `3d484bddcf124bca` | ✓ |
| valentine mention | 1, matching-threshold code snippet, "not a per-row field" | 1, `high_confidence = matches.filter(min_score=0.7)`, **不是**逐行置信度字段 | ✓ |

All three sha256 prefixes are exactly 16 hex chars as §5 declares; all three commit pins are well-formed 40-hex strings. Draft date (2026-09-24, GB10) matches §5's probe date. The valentine snippet contains the token "confidence" inside a variable name, consistent with a mention count of 1. §5 is strictly more specific than the draft (quotes the snippet) with no contradiction.

## Check 3 — No measured confidence, no measurement claim: PASS

- `allowed_values` is vocabulary mandated by the contract, not measurement output; no per-row or per-dataset confidence value appears anywhere in the draft.
- `missing_policy: "unmeasurable"`, `field: "none_native"`, and the `notes` disclaimer ("carries no measured confidence and must not be read as one") are all anti-measurement statements. §5 mirrors this ("草案**不含任何测量置信度**，也不得被读作测量").
- The only numbers present (bytes, mention counts, `min_score=0.7` inside a quoted snippet) are probe metadata, not confidence measurements.

## Check 4 — §5 vs. sections 1–4 and red lines: NO CONTRADICTION FOUND (see Findings 1–2)

- **No download**: probe is README-only via raw.githubusercontent at pinned heads, zero-model; no dataset acquisition claimed.
- **No fabricated hashes**: only 16-char prefixes asserted, explicitly labeled as prefixes; full digests are deferred to package binding, which is the honest posture.
- **Template not a package**: draft is marked pending binding; §5 requires sha256 binding + independent review before package entry, and full replacement + re-audit if a real confidence field ever appears.

## Check 5 — No invented hashes/byte counts: PASS (within inline-verifiable scope)

Every hash-like and byte-count value appears identically in both independent inline locations, in the declared format (16-hex prefix / exact bytes / 40-hex commit). No full sha256 digest is asserted anywhere, so no unverifiable digest claim exists to fabricate. Ground-truth re-derivation is impossible without tools by design of this audit; internal consistency and format checks are clean.

## Numbered Findings

1. **[INFO]** Sections 1–4 of the protocol are not in the inline evidence, so Check 4 consistency is assessed only against the stated red lines and internal coherence of draft↔§5. No contradiction found; full cross-section verification is deferred to a loop with the complete protocol in scope.
2. **[LOW]** The three commit SHAs and byte counts are accepted as probe-record pins; they cannot be re-verified offline. Mitigation already present in §5: full sha256 binding and independent review are mandatory at package entry, which would catch any pin drift.
3. **[LOW]** `field: "none_native"` is a sentinel string that satisfies the contract's non-empty-string check but is not a real field name. Semantics are unambiguous given `source` and `missing_policy`, but package reviewers should be aware the contract's `field` check cannot distinguish "absent field, honestly declared" from "named field." No action required for the draft.
4. **[INFO]** §5's "5/5 通过" is a mirror check of contract logic against an unbound draft, not an executed gate run (the gate only fires post-binding). The draft status string and §5 wording both make this explicit — honest framing, noted for the record.
5. **[INFO]** The valentine mention count of 1 with the snippet identified as threshold code (`min_score=0.7`) is correctly excluded from being read as a native per-row confidence field, in both documents. This is the crux claim of the "no native field" conclusion and it is consistently supported.

**Conclusion:** PASS_WITH_NOTES. The draft is contract-satisfying, measurement-free, and probe-consistent; §5 does not overclaim. The notes are scope limitations and reviewer awareness items, none rising to a red-line violation. Binding to the package must still trigger the full sha256 digest computation and a fresh independent audit, as both documents already require.
