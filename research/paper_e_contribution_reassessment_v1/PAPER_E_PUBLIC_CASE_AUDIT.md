# Paper E Public-Case Audit

Status: `OFFLINE_APPLICATION_COMPLETE`

This is an exploratory/post-hoc application of the Paper E audit sequence to three public papers. It is not a new model experiment, not human semantic gold, and not independent validation of a universal method.

## Boundary

Full Markdown was retrieved through DeepSeek Fetch on 2026-10-19 and stored in:

- `D:/AIRcommend/JinRongAgents/tmp/deepseek_fetch/finrank.json`
- `D:/AIRcommend/JinRongAgents/tmp/deepseek_fetch/verifin.json`
- `D:/AIRcommend/JinRongAgents/tmp/deepseek_fetch/same_number_citation_swaps.json`

The audit used the sequence in `PAPER_E_POSITIONING_DRAFT.md`:

1. identify the observation surface;
2. bind the mutation/evidence to the recomputed measurement object;
3. inspect score and threshold identifiability;
4. state the equivalence/acceptance contract;
5. determine whether the result changes interpretation or decision.

The audit does not rerun any paper's code, download a new data source, or issue actor/judge requests.

## Verdict

`INTERPRETATION_CHANGED_IN_ALL_THREE_CASES`

The sequence is useful as a concrete review discipline, but the papers also show that generic construct-validity and evidence-verification checklists are already active research areas. Paper E remains defensible only as a case-specific audit of staged observation surfaces and measurement-object binding.

## Case 1: FinRank

Source: *FinRank: An Evidence-Grounded Benchmark for Financial Question Answering and Retrieval over SEC Filings*, arXiv:2608.07400.

### Audit

- **Observation surface:** question, filing metadata, gold supporting passages, per-question hard negatives, pooled and in-record retrieval corpora.
- **Measurement objects:** passage retrieval, reranking, hard-negative discrimination, multi-passage evidence, answer generation and query rewriting are separate tasks.
- **Binding:** supporting passages are ground-truth retrieval targets and constrain faithful generation; hard negatives carry originating ticker/year/document type.
- **Identifiability:** the paper reports retrieval and reranking results, but explicitly leaves answer generation and faithfulness to future work. Hard-versus-random negatives are the control that isolates discrimination difficulty.
- **Interpretation change:** the checklist prevents reading retrieval metrics as end-to-end financial-QA correctness. It also forces hard-negative overlap artifacts and single-annotator review into the limitation boundary.

### Decision consequence

FinRank supports the value of separating evidence selection from answer production. It also means Candidate B must not claim novelty for financial evidence binding. Its unique question must be whether real experience changes the binding action beyond FinRank-style hard negatives, generic rules and ordinary context.

## Case 2: VeriFin

Source: *VeriFin: A Neurosymbolic Framework for Verifying LLM-Generated Financial Claims*, arXiv:2608.10213.

### Audit

- **Observation surface:** filed XBRL facts, concepts, periods, units, contexts, formula authority and candidate claim.
- **Measurement objects:** `Verified`, `Violated` and `Abstain` are distinct outcomes; false-accept risk is separate from false-reject and coverage.
- **Binding:** candidate generation is decoupled from authoritative facts and formulas; Z3 checks a constraint system; abstention is explicit when operands or formula authority are ambiguous.
- **Identifiability:** same candidate pools isolate verifier behavior. The paper reports zero observed false accepts while retaining high coverage, but semantic-parsing and formula-authorization errors remain possible before solver entry.
- **Interpretation change:** the checklist prevents treating arithmetic execution or linguistic formula context as sufficient verification. It forces formula provenance, operand role, unit, period and abstention into the acceptance contract.

### Decision consequence

VeriFin is a strong independent example that the paper's measurement-object language is useful. It is also a novelty threat: financial claim verification already uses source-grounded, candidate-independent checks. Paper E must focus on staged evaluator observability and structural score identifiability rather than acceptance control in general.

## Case 3: Same-Number Citation Swaps

Source: *Same-Number Citation Swaps: Stress-Testing Jev as a Financial Evidence Judge*, arXiv:2610.08675.

### Audit

- **Observation surface:** cited cells, rows, headers, text spans, calculation traces, numerical key and source excerpts.
- **Measurement objects:** numerical correctness, cited-role support and acceptance are explicitly separate.
- **Binding:** cited-role support is anchored to the actual emitted pointer; arithmetic order and unit conversion are evaluated separately.
- **Identifiability:** same-number swaps and equivalent-fact controls isolate role recognition from number matching. The paper distinguishes prospective collection from post-hoc extensions and reports that independent human confirmation of natural labels is incomplete.
- **Interpretation change:** the checklist prevents a key-matching answer from being treated as supported evidence and prevents acceptance from being treated as semantic truth. It also requires explicit reporting of exploratory analyses and label uncertainty.

### Decision consequence

This is the closest concrete precedent to Paper E's proposed review sequence. The transferable craft is the separation of endpoints and the prospective/exploratory boundary. The non-transferable part is the specific staged document-evaluator result: flat/layered affine equivalence and direct-leaf instrumentation attribution.

## What Paper E can still claim

`KEEP`:

- A staged evaluator can observe a perturbation while its decision rule ignores it.
- A raw score gap can be structurally unidentifiable when score constructions are affine/rank-equivalent.
- Stage localization can be supplied by direct instrumentation rather than hierarchy.
- Mutation, observation and outcome must share a causally updated measurement object.

`NARROW`:

- The proposed checklist is an application-ready design sequence, not a validated universal method.
- The public-case application demonstrates interpretation changes, but it is not a second implementation-level replication.

`DO NOT CLAIM`:

- A generic construct-validity framework.
- A new financial claim verifier or financial QA benchmark.
- A detector ranking or universal blind-spot taxonomy.

## Residual blocker

The remaining decision-critical gap is one second **causally aligned staged dataflow** where the review rule is frozen before reading outcomes and an independent reviewer records whether the interpretation or decision changes. The three public papers show external usefulness and provide strong writing controls, but they do not replace that implementation-level validation.

## Bottom line

`Paper E: NARROW_AND_CONTINUE`.

The offline application changed the interpretation of all three public cases and confirms that the checklist prevents specific over-readings. It does not establish a general method contribution. The next paper revision should make the staged observation-boundary and score-identifiability case central, use Same-Number Citation Swaps as the closest writing model, and reserve generic checklist language for a bounded design proposal.
