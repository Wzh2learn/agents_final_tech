# Loop A Remediation Task: Complete Publication And Run Calibration

Task ID: `publication-proxy-calibration-remediate-a-20261026`
Date: 2026-10-26, Asia/Shanghai
Authorization: old failure reserve, one bounded A remediation
A prior snapshot: `3a21a7186f9e20ef8feb62edae0d62987fe4bf30`
C audit snapshot: `e0b39df8a85585654828d5e82ffe0f27e3bae2c9`
Authority: `docs/research/LOOP_D_RESEARCH_PROMPT.md`
Authority Git blob: `a38252322189ccb00a1a45b7611f693ada292faf`
Authority LF SHA256: `9dcef9001ee4e71d652dc0ad496139a54f5821f11d42a21fb7816393d1db3974`

## Boundary

This is the final authorized A dispatch for the round. Preserve the prior A
commit and C audit. Work only on the existing task-owned research directory,
the two thesis files already owned by A, and new remediation receipts. Do not
edit frozen inputs, historical scores, memory ledgers, the unique prompt,
production services, credentials, or unrelated changes. No training, old R/E,
judge, production, or external submission is authorized.

The C audit found four blocking defects. Fix all four and the selected
non-blocking items that affect result identity or reproducibility. Do not spend
the dispatch on general prose polishing.

## 1. Complete Paper E SNCS Package

Replace the excerpt with a complete journal-derived manuscript while retaining
exactly the two existing cases:

- port and adapt the complete Introduction, Related Work, Method/Measurement
  Contract, Experimental Setup, Results, Discussion/Limitations and Data
  Availability from `source_iccart_original.tex` and the canonical manuscript;
- wire `references.bib` with a real bibliography and in-text citations,
  including the closest-work set; remove orphan hand-written entries;
- keep the 150-250 word structured abstract consistent everywhere;
- retain the checkpoint-level qualifier for `96/118`, post-hoc/clustered
  FinRank identity, and the unresolved reproduction gaps;
- use the actual measurement-chain figure once and the visibility figure once;
- keep the first-reviewer analysis outside the submission body;
- enumerate AI use by manuscript section and code/tool use;
- retain all author, affiliation, corresponding, funding, patent, artifact and
  submission fields as `TBD_OWNER` where not authorized.

Produce a reviewable PDF containing the complete manuscript, not a cover sheet.
Try only locally available, non-paid build tools. If GB10 has no compatible TeX
engine, produce a deterministic full-content fallback PDF from the complete
manuscript and explicitly record that it is not a TeX-engine compilation. Keep
the exact LaTeX canonical and leave a clean build command for D to compile
through the approved document tool. Record engine/fallback identity, page
count, text count and hashes in `BUILD_RECEIPT.md`.

## 2. Preserve And Clarify P1

Do not rerun or alter the accepted public actor/regression. Correct the result
identity and receipts:

- `23/24` is numeric program correctness;
- `13/24` is complete semantic answer correctness;
- unit agreement is `14/24`; the 10 rule-conformant unit UNKNOWNs are not
  numeric failures;
- preserve the reference-direction conflict with both acceptable readings and
  `UNRESOLVED`;
- make tests actually execute under a working local harness and report the
  true pass count. A `Ran 0 tests` command is a failure, not evidence.

## 3. Build P2 Runner And Complete The Real Calibration

Create `raw/` and implement a hash-bound three-arm chain:

`runner -> visible-context adapter -> model actor -> strict parser -> scorer
input builder`.

The actor sees only the question and the selected visible table/paragraph
context. It must not see gold answers, derivations, reference chains, hidden
scales, source labels, UIDs or per-item expected values. The scorer may use the
frozen reference chain only after generation.

Before generation:

- keep the frozen 12 UIDs, seed, exclusions and replacement list;
- keep R7/R8 repaired and preserve the historical matcher;
- add tri-state semantic handling for wrong-role/substring ambiguity:
  `ACCEPT`, `REJECT`, or `PENDING_ADJUDICATION`; do not silently certify the
  lexical role matcher as a complete semantic oracle;
- run a zero-output dry run for all 12 items through runner, adapter,
  scorer-input construction and hash/trace checks;
- rerun the formal preflight and reach
  `END_TO_END_PREFLIGHT_PASS`. Any failure stops before generation and must be
  reported as an engineering qualification gap, never as evidence that the
  proxy has no information value.

If and only if the preflight passes, use one fixed local research actor at
`/home/testuser/wzh/models/hf/Qwen3-4B` or another already authorized local
checkpoint that passes interface qualification. Do not use an old R/E or
trained checkpoint. Freeze model revision/hash, dtype, tokenizer, decoding,
maximum output, prompt template and calculator before output.

Run the primary comparison on the same 12 items:

- table + top-3;
- table + top-5;
- table + all.

Primary generation budget is 12 x 3 = 36 calls. At most 12 additional calls
are allowed only for preregistered interface positives, preserved failures, or
bounded retries. Hard cap 48 generation calls and 240,000 generation tokens.
All attempts and failures count. Training remains zero.

For each raw response preserve:

- complete answer, numeric value where applicable, unit, direction, evidence
  references and any UNKNOWN/clarification;
- strict format and parse outcome;
- semantic result against the frozen reviewable reference chain, including
  `PENDING_ADJUDICATION`;
- wrong answer/error delivery, reasonable UNKNOWN, unnecessary refusal and
  unsupported detail;
- actual non-padding input/output tokens, cached tokens if available, wall
  time, retry identity and total calls.

Report paired item-level differences by arm, answer accuracy, error-delivery
risk, coverage/UNKNOWN, context size, measured tokens/calls/latency, and
total cost. Keep old 507-item proxy counts and visible characters separate.
Do not claim 2-point noninferiority, generalization, or an upper/lower bound
from this 12-item development panel.

Scientific disposition must distinguish:

- proxy/reference defect;
- retrieval/context omission;
- actor reading or reasoning error;
- parser/interface failure;
- semantic matcher pending adjudication;
- actual cost/risk tradeoff.

## 4. Accounting And Thesis

Regenerate `ALL_FILES.sha256` from final tracked task files only. Record A
harness input/cache/output/reasoning separately from scientific model calls,
and retain UNKNOWN for Claude/subscription/cash fees.

Correct the Chinese thesis evidence row and add a concise paragraph covering:

- numeric versus semantic P1 identity;
- engineering qualification versus scientific information value;
- real answer/risk/cost result if the three-arm run occurred;
- Paper E's complete two-case journal scope and remaining limitations.

Do not state that Paper E is accepted, published or school-recognized.

## Completion Evidence

Return `A_REMEDIATION_RETURN.md`, exact commands/status, complete raw and
cost ledgers, preflight receipt, full Paper E source/PDF/build receipt, P1
identity/test correction, and a commit containing only owned paths. Preserve
prior negative results and failed attempts. D will integrate and independently
run deterministic checks; no additional C dispatch remains.
