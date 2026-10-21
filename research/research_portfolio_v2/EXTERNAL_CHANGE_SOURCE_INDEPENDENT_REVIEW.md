# External Change Source Independent Review

Review date: 2026-10-21

## Scope And Verdict

This is a read-only qualification of two pinned public sources:

- VersiCode at `8a53b9938707deb4c8398152e9ebc923580783a3`.
- PyMigBench at `d8ffb982d23e1bda2a844bd4a6f7b451e192bd5b`.

The comparison target is the CodeUpdateArena external-change experiment. The
question is whether either source can provide a more informative experiment:
more observable change information and/or a stronger independent oracle.

### Recommendation

1. **PyMigBench is the better primary source for external-change validity.**
   It records real GitHub migration commits, source and target library names,
   file/line change locations, API mappings, program-element mappings,
   cardinality, and change properties. A curated subset can potentially be
   upgraded to a behavioral experiment by checking out the referenced commits
   and running repository tests before and after the migration.
2. **VersiCode is the better immediate source for a controlled observability
   ablation.** Its code-editing records include paired code, dependency
   versions, release times, edit direction, and change labels. It does not
   provide independent hidden tests, and its code-editing rows are heavily
   duplicated across version transitions.
3. Neither source is a drop-in replacement for CodeUpdateArena's trusted
   update implementation plus hidden unit tests. PyMigBench can become a
   stronger oracle only after commit/test curation. VersiCode currently offers
   reference and structural metrics, not behavioral proof.

## Pinned Provenance And License

| Source | Directly verified provenance | License evidence | Qualification |
|---|---|---|---|
| VersiCode | Git `HEAD` is `8a53b9938707deb4c8398152e9ebc923580783a3`; remote is `https://github.com/wutong8023/VersiCode.git`. The tracked `data/VersiCode_Benchmark.zip` has SHA-256 `d19382947db3a5d032ad01126cc19696758b04654e21a9561fd4a7d972f06018`. | `LICENSE` is Apache License 2.0. `README.md` displays an MIT badge/link. The ZIP contains no `LICENSE` or `README`. | License identity is inconsistent. Third-party code-snippet rights and the raw-data terms are not independently verified. |
| PyMigBench | Git `HEAD` is `d8ffb982d23e1bda2a844bd4a6f7b451e192bd5b`; remote is `https://github.com/ualberta-smr/PyMigBench.git`. | `LICENSE` is MIT. The README says the data includes migrations borrowed from SALM and points to release `2.0.2`/Figshare for the paper dataset. | Repository license is clear. Separate rights/provenance for SALM-derived records and upstream repository code remain unverified. |

The VersiCode README says to email the authors for raw data, while the pinned
repository contains the benchmark ZIP. The ZIP itself has no embedded data
license. This is a provenance ambiguity, not a finding that use is prohibited.

## VersiCode: Directly Read Facts

### Benchmark payload

The tracked ZIP contains 24 entries: 14 files and 10 directories. It contains
only `code_completion` and `code_editing` JSON payloads. The extracted tree is
an untracked local convenience copy; the ZIP is the pinned source artifact.

The two code-editing files each contain 49,346 records:

- `code_editing_old_to_new.json`
- `code_editing_new_to_old.json`

Each record has:

`dependency`, `old_version`, `new_version`, `old_time`, `new_time`,
`description`, `old_code`, `new_code`, `old_name`, `new_name`, `type`,
`edit_order`, `language`, `task`, `source`, and `id`.

Direct counts from the two files:

- 16 dependencies.
- 85 unique `(old_code, new_code)` pairs in each direction.
- 83 unique `(old_name, new_name)` pairs.
- 107 unique descriptions.
- 16,579 unique dependency/version transitions.
- No empty old or new code fields.
- Every code-editing record has `type: name_change`, `source:
  library_source_code`, and `language: python`.
- The old-to-new and new-to-old record sets are the same apart from direction
  and record IDs.

Thus 49,346 rows are not 49,346 independent code changes. A family-level
experiment must group by the underlying code pair (and preferably dependency
and version transition), not treat rows as independent observations.

The completion payload includes separate token, line, and block files for
downstream application code, library source code, StackOverflow Python, and
some Java/C#/JavaScript block data. The code-editing payload is the relevant
external-change source; the completion payload is useful for auxiliary
version-aware generation checks but is not an executable change benchmark.

### Evaluation utilities

Directly read `util/evaluate/evaluate_block.py`, `evaluate_line.py`,
`evaluate_token.py`, and `clear_ans.py`:

- `evaluate_token.py` computes exact-token pass@k.
- `evaluate_line.py` computes identifier-prefix (`ISM`) and line-prefix (`PM`)
  scores against a masked target.
- `evaluate_block.py` checks syntax (`compile`), requires the target API name,
  and computes `ISM`/`PM` against the target code. For code editing, the
  active path uses `old_code`/`old_name` for new-to-old; the target
  `new_code`/`new_name` path is present but commented.
- The evaluator does not execute generated edits or run hidden behavioral
  tests.
- The scripts use hard-coded result paths and `eval()` on model-output strings;
  they are research scripts rather than a safe reusable oracle.

The code-editing generation scripts expose the dependency and both version
labels, a functionality description, and the source code. The target code is
not in the old-to-new prompt. The new-to-old script has a naming inconsistency:
it passes `new_code` into a parameter rendered as `old_code`. This should be
resolved before using that direction as a protocol.

### Actual change source

The only source marker in the editing records is `library_source_code`.
Dependency names, old/new versions, and release dates are present, but there
is no per-record upstream URL, commit SHA, file path, or source license. The
old/new snippets are concrete change evidence, but their upstream extraction
path is not directly auditable from this repository.

### Task observability and oracle

Safe observable inputs for an old-to-new task can include:

- source snippet (`old_code`);
- dependency identity;
- source and target version labels and release dates;
- functionality description;
- source API name when it is visible in the source.

Oracle-only fields must include:

- `new_code`;
- `new_name`;
- any target diff derived from the pair;
- `id` and direction bookkeeping.

The exact target pair supports exact-match, AST/token edit, identifier, and
compile checks. It does **not** establish behavioral equivalence. A stronger
oracle would require experimenter-authored tests or independent upstream
tests, neither of which is bundled here.

### Information beyond prose update text

VersiCode adds these concrete signals beyond a prose update description:

- old and target dependency versions;
- old and target release timestamps, allowing version-distance and time-gap
  analyses;
- full source and target code pairs;
- old/new API names;
- edit direction;
- change type and language/task/source labels.

The best immediate experiment is an observability ablation: prose-only versus
version metadata versus structured change metadata, with `new_code` and
`new_name` withheld as the target. The analysis must split by the 85 unique
code pairs to avoid version-expansion leakage.

## PyMigBench: Directly Read Facts

### Dataset shape

Direct parsing of the 321 tracked YAML files found:

- 321 migration records;
- 694 migration files;
- 2,989 code changes;
- 300 unique repositories;
- 320 unique commit SHAs;
- 134 unique source-target library pairs.

The README claims 3,096 code changes, 335 migrations, and 141 library pairs.
The pinned checkout therefore does not match the README count. This may be a
version/documentation drift issue; it must be resolved before treating the
README counts as ground truth.

Each migration record contains `repo`, full `commit`, `commit_url`,
`source`, `target`, `domain`, and `files`. Each file contains a path and code
changes. Each code change contains:

- a source-to-target line replacement expression;
- source and target API lists;
- source and target program-element lists;
- cardinality (`one-to-one`, `one-to-many`, etc.);
- change properties such as element-name change, argument
  addition/deletion/transformation, async/output transformation, and
  decorated-function parameter addition.

Observed property counts include 1,025 element-name changes, 578 argument
additions, 349 argument deletions, 317 argument transformations, and smaller
counts for async/output transformations and other properties. The line
expressions, API mappings, and element mappings are substantially more
structured than a prose update text.

### Actual change source

PyMigBench identifies real GitHub commits and stores the full SHA plus a
commit URL. This is stronger change-source traceability than VersiCode.
However, the YAML files contain metadata and line mappings, not the source
file bodies, patches, test commands, or test results. Reconstructing the
actual before/after code requires checking out the referenced repository
commits. That reconstruction was not performed in this offline review.

The README says v2 includes migrations borrowed from SALM. The repository does
not provide a per-record source/license partition for those borrowed records.

### Task observability and oracle

For a real migration task, observable context can include:

- pre-change source file/context from the repository at the parent commit;
- source library and target library names;
- migration domain;
- an issue-style or experimenter-written change request.

Oracle-only information should include:

- target APIs and target program elements;
- cardinality and change-property labels;
- target line ranges;
- the target commit diff;
- repository tests and expected behavior.

Showing `target_apis`, `properties`, or line mappings in the prompt would
leak much of the answer. They are valuable hidden structural labels, not
ordinary public update prose.

Independent behavioral oracle feasibility is **conditional**:

- Good in principle: the full commit SHA allows parent/current checkout and
  repository test execution.
- Not supplied: test commands, test fixtures, expected outputs, or a curated
  executable subset.
- Required work: select migrations with runnable tests, freeze both commit
  environments, run tests before and after, and retain only migrations with a
  deterministic oracle.

The bundled parser tests pass locally: `18 passed`. The library implementation
also has two practical caveats for a production harness:

- `Database.load_from_dir` uses `yaml.unsafe_load`;
- `Database.mig`, `Database.file`, and `Database.code_change` raise when an ID
  is present rather than when it is absent (`if id in ...` is inverted).

These do not invalidate the YAML records, but a new harness should parse them
with a safe loader and avoid relying on those lookup methods without repair.

### Information beyond prose update text

PyMigBench adds these concrete signals beyond prose:

- real repository and full commit identity;
- source and target library pair and domain;
- file paths and source/target line ranges;
- source and target API lists;
- source and target program-element kinds;
- cardinality;
- structured change properties.

This is the most informative source for asking whether structured external
change evidence improves migration behavior. The strongest comparison would
hold out the target diff/tests and expose only source context plus carefully
preregistered non-answer metadata, then score against hidden tests and the
target commit's structural change map.

## Comparative Judgment

| Criterion | VersiCode | PyMigBench | CodeUpdateArena context |
|---|---|---|---|
| Actual change source | Versioned library snippets, but no per-record upstream commit | Real GitHub commits with full SHAs and URLs | Synthetic public API updates |
| Observable change information | Code pair, dependency versions, release dates, edit type/name labels | Repo/commit, library pair, file/line map, APIs, elements, cardinality, properties | Public update prose/signature plus hidden reference/tests |
| Independent behavioral oracle | Not bundled; reference/compile/similarity only | Feasible only after commit/test curation | Trusted reference plus hidden tests |
| Independence risk | 85 code pairs repeated across 49,346 rows; mirrored directions | 321 records/2,989 changes, but README count drift and external checkout needed | Eight synthetic families, controlled but artificial |
| Best use now | Controlled observability and version-distance ablation | Real external-change validation after executable subset selection | Current bounded baseline |

**Conclusion:** PyMigBench should be the primary candidate for a more
informative external-change experiment because its change source is real and
its metadata exposes migration structure that prose cannot express. VersiCode
is a useful secondary source for testing whether version distance, release
time, and structured labels help, but it should not be presented as an
independent behavioral benchmark without new tests.

## Directly Read Versus Unverified

### Directly read or recomputed offline

- Both Git `HEAD` values and remotes.
- Both repository license files and README license/count statements.
- VersiCode ZIP inventory and SHA-256.
- VersiCode JSON field inventories and counts.
- PyMigBench YAML counts, field inventories, property counts, and commit/file
  totals.
- VersiCode evaluator and generation script behavior.
- PyMigBench parser/model code and local parser tests (`18 passed`).

### Unverified in this review

- Upstream URL/commit provenance for individual VersiCode snippets.
- Third-party and SALM-derived data licensing.
- Availability and executability of every PyMigBench referenced repository and
  test suite.
- Whether the README dataset release (`2.0.2`/Figshare) exactly matches this
  pinned checkout.
- Semantic correctness of VersiCode target snippets beyond the stored pair.
- Any behavior of the source projects outside the pinned metadata.

No model calls were made. No source repository was modified. This review is
about public synthetic/versioned source material and real migration metadata,
not natural production drift or general model capability.
