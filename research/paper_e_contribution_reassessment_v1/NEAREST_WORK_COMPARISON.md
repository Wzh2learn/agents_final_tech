# Bounded Nearest-Work Comparison

Status: `LITERATURE_CHECK_2026-10-19`.

## Scope and reading method

Five papers were read from full text and form the comparison set. The search targeted four overlaps: construct/measurement validity, behavioral or mutation-style testing and oracle design, staged/process-level evaluation, and incremental information beyond simple metrics or baselines. Three additional canonical records were checked only through Crossref/official DOI metadata because accessible full text was not obtained; they are recorded as gaps, not as full-text comparisons.

The comparison asks a narrow question: does Paper E add a distinct, useful measurement-audit result for staged document evaluation, or merely rename established evaluation-validity practice?

## Core five: full-text comparison

| work and verifiable source | actual reading scope | substantive overlap with Paper E | possible incremental contribution of Paper E | novelty risk / current judgment |
|---|---|---|---|---|
| Ross et al., *What Makes a Good Metric? Evaluating Automatic Metrics for Text-to-Image Consistency* (COLM 2024), arXiv:2412.13989, [paper](https://arxiv.org/abs/2412.13989) | Full PDF: abstract, construct-validity desiderata, metric correlations, sensitivity analyses, component ablations, shortcut analysis, discussion/limitations. | Strong overlap in asking whether a metric measures the intended construct; checks incremental information over CLIPScore, sensitivity to text/image, ablations of components, and shortcut reliance. | Paper E studies a **staged observation surface** rather than only metric inputs: it distinguishes checkpoint visibility from decision detection and contract-relative harm, proves affine/rank equivalence for two score constructions, and audits whether perturbation, observation and outcome share a causally updated object. | **Largest threat.** If Paper E claims only “audit metric validity with ablations,” Ross et al. covers the idea. The paper is defensible only if the staged observation/dataflow binding and structural-equivalence diagnosis are central and demonstrably change interpretation. |
| Ribeiro et al., *Beyond Accuracy: Behavioral Testing of NLP Models with CheckList* (ACL 2020), arXiv:2005.04118, [paper](https://arxiv.org/abs/2005.04118) | Full PDF: abstract/motivation, capability × test-type matrix, invariance/directional tests, generation tooling, three task applications, user studies, discussion/conclusion. | Broad overlap in moving beyond aggregate accuracy, using targeted perturbations and behavioral tests, and making failure locations actionable. | CheckList tests model behavior through capabilities and test types; Paper E audits the **evaluator** itself: whether injected defects reach any observation, whether the protocol consumes them, and whether score construction identifies comparisons. | CheckList makes a generic “behavioral audit” claim old. Paper E must not sell perturbation testing as new; it can contribute evaluator-side observability and measurement-object binding. |
| Cho, Ruberto & Terragni, *Metamorphic Testing of Large Language Models for Natural Language Processing* (2025), arXiv:2511.02108, [paper](https://arxiv.org/abs/2511.02108) | Full PDF: oracle-problem motivation, formal metamorphic relation/oracle definitions, 191-relation review, 36-relation experiment design, failure-rate and oracle-confusion analysis, manual error analysis, discussion/limitations. | Direct overlap with oracle substitution, perturbation relations, fault exposure without labels, and the distinction between a metamorphic relation violation and source-output correctness. | Paper E's injection may be visible while harmfulness remains contract-relative, and its FinQA case shows that a valid predicate can fail to estimate detection when downstream result fields are not recomputed from the mutation. It therefore audits the **binding of transformation to measurement object**, not only input-output relations. | Metamorphic testing already formalizes relation-based oracles. Paper E should cite it as the nearest oracle/perturbation precedent and avoid “new oracle-free testing” language. |
| Yao et al., *τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains* (2024), arXiv:2406.12045, [paper](https://arxiv.org/abs/2406.12045) | Full PDF: task/POMDP construction, database/API and policy surfaces, binary reward, pass^k, task construction, failure taxonomy, policy ablation, cost and limitations. | Strong overlap in tool-mediated evaluation, multi-stage behavior, explicit reward definitions, consistency across trials and separating instruction/policy/tool failures. | τ-bench measures agent task outcomes and reliability under user/tool interaction. Paper E studies whether an evaluation protocol can observe and identify failures before the final outcome, including structural non-identifiability between score constructions and stage instrumentation. | τ-bench makes broad “tool-agent evaluation needs process evidence” claims familiar. Paper E must keep the document-evaluation measurement case and avoid claiming a new agent benchmark. |
| Liu et al., *AgentBench: Evaluating LLMs as Agents* (ICLR 2024), arXiv:2308.03688, [paper](https://arxiv.org/abs/2308.03688) | Full PDF: interactive evaluation definition, environment composition, success-rate/F1 metrics, finish-reason taxonomy, failure analysis, limitations and implications. | Overlap in staged interactive evaluation, separating invalid format/action, timeouts and task failures, and using environment/tool traces to interpret aggregate success. | AgentBench categorizes agent finish reasons and environment performance; Paper E formalizes a measurement-chain audit for document pipelines, with explicit visibility/detection/harmfulness and an ablation that tests whether hierarchy adds information beyond direct instrumentation. | AgentBench covers process-aware agent evaluation. Paper E's novelty cannot be “stages matter”; it must be the observation-boundary and measurement-object diagnosis in document evaluation. |

## Additional canonical records: metadata-only

These records inform terminology and search boundaries but are **not counted as full-text evidence**:

| work | source checked | reading limitation | relevance |
|---|---|---|---|
| Cronbach & Meehl, *Construct Validity in Psychological Tests* (1955), DOI [10.1037/h0040957](https://doi.org/10.1037/h0040957) | Crossref metadata and DOI landing record; APA PDF endpoint returned HTTP 403. | No full text read in this sprint. | Canonical construct-validity vocabulary; supports careful wording around intended constructs, not a novelty claim by itself. |
| Barr et al., *The Oracle Problem in Software Testing: A Survey* (2015), DOI [10.1109/TSE.2014.2372785](https://doi.org/10.1109/TSE.2014.2372785) | Crossref metadata and DOI record; IEEE PDF endpoint returned HTTP 418. | No full text read in this sprint. | Directly relevant to oracle adequacy; full-text overlap remains unresolved. |
| Papadakis et al., *Mutation Testing Advances: An Analysis and Survey* (2019), DOI [10.1016/bs.adcom.2018.03.015](https://doi.org/10.1016/bs.adcom.2018.03.015) | Crossref metadata and Elsevier API record; API rate-limited without full text. | No full text read in this sprint. | Relevant to mutation operators and kill/survival interpretation; do not claim uniqueness against it without a later full-text check. |

## Overlap map

### Established before Paper E

- Aggregate accuracy can hide actionable failures.
- Perturbation or mutation testing needs a valid oracle/equivalence relation.
- A metric should show construct validity, sensitivity and incremental information.
- Tool-agent evaluation should separate invalid format/action, timeout and semantic failure.
- Process/stage information is useful for diagnosing agent behavior.

### Plausibly specific to this manuscript

1. A staged document-evaluator case makes three separate objects explicit: checkpoint visibility, protocol detection and contract-relative harmfulness.
2. A deterministic score-algebra audit shows a raw flat/hierarchical detection gap can be structurally uninformative when scores are affine/rank-equivalent.
3. A stage-aligned localization result is paired with a direct-codebook ablation that attributes the separability to instrumentation rather than hierarchy.
4. A second dataflow fails because the mutation, detector and outcome fields do not share a recomputed measurement object, yielding a boundary diagnosis rather than a performance estimate.
5. The resulting review sequence is concrete enough for an evaluator author to apply, while remaining a proposal until independently used.

## Threat assessment

The largest threat is Ross et al.: its construct-validity desiderata, metric correlation, sensitivity and component ablation already cover the broad “audit whether a metric measures the right thing” contribution. Cho et al. is the largest oracle/perturbation threat: metamorphic relations already replace explicit labels. τ-bench and AgentBench are threats to any claim that staged/tool evaluation or failure taxonomies are new.

Paper E survives those threats only under a narrow positioning: **a reproducible measurement audit of observation surfaces and dataflow binding in staged document evaluation, where score structure and instrumentation boundaries change what a comparison can identify.** The proposed checklist must be presented as an application-ready design proposal, not a validated universal method.

## Literature gaps that affect the decision

1. Barr and Papadakis full texts must be checked before submission if the paper retains broad oracle/mutation-testing novelty language.
2. A second, causally aligned dataflow is needed to test whether the proposed review sequence changes an evaluation decision outside the current carrier construction.
3. A current official call-for-papers check is required before naming a venue or track; no venue recommendation is made in this sprint.

## Supplemental full-text craft and method check

The following six papers were fetched as full Markdown through the DeepSeek Fetch API on 2026-10-19. They are used for method and writing analysis, not added to the original eight-paper novelty count.

| paper | how the paper is built | what we should copy | what we must not claim |
|---|---|---|---|
| *Measurement Without Validity: The Compounding Reliability Problem in Agentic AI Evaluation* (arXiv:2608.00794) | Opens with deployment/regulatory stakes, names the structural gap as compounding rather than additive measurement error, introduces a three-layer validity model, reports a structured literature scan, then gives prescriptions and threats-to-validity sections. | Keep a named measurement decomposition, separate conceptual bounds from proved results, and write an explicit “what this paper does not claim” section. | Its general compounding-validity model and eight prescriptions already cover the broad audit/checklist territory. |
| *Measuring What Matters: Construct Validity in Large Language Model Benchmarks* (NeurIPS 2025 / arXiv:2511.04703) | Systematic review of 445 benchmarks from a 46,114-paper corpus; a 21-item codebook, two-round review, inter-rater check, then eight recommendations and a checklist. | Use a transparent coding scheme and report review reliability when the contribution is an audit procedure. | A generic construct-validity checklist is not new. |
| *Same-Number Citation Swaps: Stress-Testing Jev as a Financial Evidence Judge* (arXiv:2610.08675) | Separates numerical correctness, cited-role support and acceptance; combines a prospectively collected bank with post-hoc constructed swaps; reports source review, controls, costs, failure conditions and limits. | Keep endpoints separate, distinguish prospective and exploratory analyses, report call costs and exact failure conditions. | It already demonstrates that same-number/equivalent-fact controls are needed for financial evidence verification. |
| *Rethinking the Role of Tool Graph Memory in Multi-Turn Tool Use* (arXiv:2610.21571) | Tests memory versus no-memory and random/no-guidance controls across nine models and two benchmarks; measures calls/tokens; performs manual failure analysis and ablation; proposes lightweight insight memory. | Match extra calls/tokens across arms and include random/no-guidance controls before attributing gains to experience. | A memory benefit cannot be claimed from extra computation or more tool calls alone. |
| *FinRank: An Evidence-Grounded Benchmark for Financial Question Answering and Retrieval over SEC Filings* (arXiv:2608.07400) | Builds 1,185 records over 22 companies, documents question-generation criteria, hard-negative taxonomy, splits, baselines, stratified ablations, limitations and dataset card. | Borrow source identity, hard-negative construction, stratified reporting and explicit non-deployment scope. | Candidate B is not a new financial-QA benchmark contribution; FinRank already covers provenance-sensitive evidence discrimination. |
| *VeriFin: A Neurosymbolic Framework for Verifying LLM-Generated Financial Claims* (arXiv:2608.10213) | Frames verification as false-accept control; separates candidate generation from XBRL grounding, independent formula establishment and Z3 checking; includes abstention, repair and robustness. | Separate answer generation, operand binding, formula authority and acceptance; treat abstention as an outcome. | Do not claim that arithmetic checking alone verifies financial claims; period/unit/line-item/formula binding is already the central problem. |

### Craft-level conclusion

The strongest papers share a repeatable structure: a concrete operational failure, a named measurement object, a control that isolates the claimed mechanism, an explicit cost/validity boundary, and a limitation section that identifies exactly what the evidence does not support. Paper E should follow that structure, but its specific contribution must remain the staged observation surface and measurement-object binding case.
