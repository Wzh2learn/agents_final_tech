# Paper E Layer-1 Independent Gold Analysis Plan v1

> Status: **FROZEN BEFORE ANY CASE WAS READ**
> Freeze date: 2026-10-15
> Authority: `paper/PAPER_E_LAYER1_INDEPENDENT_GOLD_DESIGN_v1.md`
> Scope: deterministic, zero-call task-level gold for the frozen drift-v0 header-drift injections

## 1. Scope and precedence

This plan freezes the complete decision contract before any content from
`injection_map.json`, `tatqa_tables.json`, `injected_tables.json`, or
`t2_visibility_sensitivity.json` is read. Only file existence and SHA-256 metadata were
checked before this file was written. The audited greedy header matcher and the semantic judge
are not inputs to any label. The checker verdict is read only after all dev labels are computed
and is used only for the comparison contingency.

The contract will not be changed after case data are read. Any input absence, expected-hash
mismatch, ambiguous rule, undecidable non-`U` case, or dev `U` rate greater than 30% invokes
the prescribed stop condition. A `U` case remains `U` and is listed for human adjudication.

## 2. Fixed canonicalization `norm(.)`

For a header value `x`, `norm(x)` is computed by this exact sequence:

1. If `x` is not a JSON string, return the marker `NON_STRING`; the case is `U`.
2. Apply Unicode NFKC normalization (`unicodedata.normalize("NFKC", x)`).
3. Apply Unicode case folding (`result.casefold()`).
4. Replace every character satisfying either condition with one ASCII space (`U+0020`):
   its Unicode general category begins with `P` (`unicodedata.category(ch).startswith("P")`),
   or it belongs to Python's ASCII `string.punctuation` set.
   Thus `_`, `-`, `.`, `/`, `%`-adjacent ASCII punctuation, and Unicode punctuation are
   normalized identically; `_` is removed as a separate-token marker.
5. Replace every maximal run of Unicode whitespace (`re.sub(r"\\s+", " ", ...)`) with one
   ASCII space.
6. Strip leading and trailing ASCII spaces.

The result is compared only as a UTF-8 string. There is no tokenization, stemming, synonym
expansion, fuzzy match learned from results, greedy assignment, threshold fitted to outcomes,
or semantic scoring.

## 3. Injection identifier and outcome-blind dev split

The injection identifier is:

1. If the injection entry has a non-empty string field `injection_id`, that exact string.
2. Otherwise, the following composite string, built without consulting any label or checker
   verdict:

   `json(uid, ensure_ascii=False, separators=(",", ":"))` + `U+001F` +
   `json(col, ...)` + `U+001F` +
   `json(original, ...)` + `U+001F` +
   `json(injected, ...)` + `U+001F` +
   `json(type, ...)` + `U+001F` +
   `json(variant, ...)` + `U+001F` +
   `json(seed_component, ...)`

   Missing fields are encoded as JSON `null`, not omitted. The seven JSON encodings are in
   that fixed order and joined by literal U+001F.

Compute:

`d = int.from_bytes(sha256(injection_id.encode("utf-8")).digest(), "big")`

The case is **dev** iff `d mod 10 < 5`; otherwise it is held out. This gives a fixed,
outcome-blind 50% SHA-256 split. The same injection identifier is used to join the frozen
checker verdict; joining never changes membership or a label.

## 4. Source-table resolution and collision pre-check

The injection's `uid` resolves exactly one frozen source table and the corresponding injected
table. A source table's clean header row `H` is the ordered list of its column headers. The
injection column `c` is resolved as follows:

1. If `c` is a JSON integer, it is a zero-based source-header position and must be in range.
2. If `c` is a JSON string, it must exactly equal exactly one source header string.
3. Otherwise, or if resolution is missing/ambiguous/out of range, the case is `U`.

All source-table headers must be JSON strings. Compute `norm` for every position in `H`.
If any two distinct positions in `H` share the same non-empty canonical header, the source
table has a colliding canonical header and every case on that table is `U`. If any source
header is empty after `norm`, or any table/header/row structure needed for comparison is
missing, every affected case is `U`.

Before scoring, the resolved source position must contain the injection's `original` header
exactly as a JSON string. A mismatch is insufficient provenance and yields `U`.

## 5. Value-invariance check

For each case, locate the source and injected table using the same `uid`, row order, and
resolved column position/index. Extract only that column's data-cell values, excluding the
header cell. Serialize the extracted value list with:

`json.dumps(values, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")`

Compare the clean serialization and injected serialization **byte for byte**. Equality yields
`value_invariant = true`. Missing extraction, a serialization failure, row-count/order mismatch,
or any byte difference yields `value_invariant = false` and the case is `U`. No deep equality,
numeric tolerance, normalization, or model judgment substitutes for this bytewise check.

## 6. Fixed binding rule, tie policy, and three-way labels

Let `o = norm(original)`, `i = norm(injected)`, and let the candidate columns be the distinct
positions of frozen source `H`. Candidate distance is ordinary Levenshtein edit distance over
the canonical strings, with unit cost 1 for insertion, deletion, or substitution and no other
weights. The candidate's bound column is its source position.

Apply the following rules in this exact priority order:

1. **`INSUFFICIENT_EVIDENCE` (U) first:** any source-integrity/collision/empty-normalization
   failure above; `i == ""`; `value_invariant == false`; no computable unique comparison; or a
   binding tie.
2. **Direct preserved correspondence (E):** if `i == o`, bind to the unique source position
   whose canonical header equals `o`. With the source-collision pre-check passed, that position
   is `c`; label `LEGAL_VARIATION`.
3. **Unique nearest neighbour:** compute `distance(i, norm(H[p]))` for every source position `p`.
   If the minimum distance is attained at exactly one position `p_min`, bind to `p_min`.
   If attained at two or more distinct positions, label `INSUFFICIENT_EVIDENCE (U)`.
4. If the unique bound position equals `c`, label `LEGAL_VARIATION (E)`; otherwise label
   `HARMFUL_ERROR (H)`. There is no absolute-distance cutoff: a successful unique binding is
   sufficient for identity preservation, while a unique binding to another column is harmful.
   A hypothetical non-empty `i` with no candidate is `HARMFUL_ERROR` only if the aggregation
   would consume different values; on a non-empty source `H`, nearest-neighbour existence makes
   this branch unreachable.

Every case receives exactly one label from `{LEGAL_VARIATION, HARMFUL_ERROR,
INSUFFICIENT_EVIDENCE}`. No `U` is converted after the fact.

## 7. Checker comparison, contingency, and rates

After labels are frozen, read only the frozen visible/blind verdict associated with the same
injection identifier. Build the ordered 2×3 contingency:

| checker verdict | E | H | U |
|---|---:|---:|---:|
| visible | count | count | count |
| blind | count | count | count |

Rates use only dev cases:

- `co_miss_rate = P(gold=H | checker=blind) = n(blind,H) / n(blind)`, or `null` if
  `n(blind) == 0`.
- `co_alarm_rate = P(gold=E | checker=visible) = n(visible,E) / n(visible)`, or `null` if
  `n(visible) == 0`.
- `u_rate = n(U) / n(dev)`, or `null` if `n(dev) == 0`.

The evidence is descriptive of this dev analysis only. It cannot support a population rate,
OCR conclusion, or claim of a confirmed harmful blind spot.

## 8. Frozen stop conditions

Report and stop without changing this plan or expanding the run if:

- any required input file is absent (`INPUT_MISSING`);
- either expected input hash differs (`HASH_MISMATCH`): injection map
  `d761240586b1597cbc02d823aa5c785a6fb6d47f112c36b705951717f64ac66e`
  and source tables
  `3e7e056889c5207f6ab9ff0541e980393c658f044cce3dc5a22fedb976e64302`;
- this split or `norm(.)` is found not to be implementable unambiguously (`RULE_AMBIGUOUS`);
- a case is not decided by the contract and is not clearly `U`;
- `u_rate > 0.30` (`GOLD_NOT_ESTABLISHED`).

Model calls, judge calls, endpoint calls, network calls, and training calls are all fixed at
zero for this run.
