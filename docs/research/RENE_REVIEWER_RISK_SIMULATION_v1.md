# RENE Reviewer Risk Simulation v1

> date: 2026-10-13 | author: Loop D (internal adversarial simulation) | purpose: find the most likely rejection arguments at SANER 2027 RENE and harden the *expression*, without changing any claim, number or evidence source
> method: simulate two hostile RENE reviewers (one methodological, one domain-sceptical), enumerate rejection arguments ranked by (severity x likelihood), locate the existing defence, and apply expression-level hardening where possible
> boundary: this is not an independent review; it is a self-simulation. `LOOP_C_REVIEW_A1A7_REVISION_v1.md` records that an independent pass is still missing.

## Risk table

| # | Reviewer argument | Severity | Likelihood | Where the paper already defends | Action taken |
|---|---|---|---|---|---|
| R1 | **"This is not a negative result; it is a bespoke evaluation audit."** RENE asks for negative/null results, and the abstract frames the contribution as an audit. | HIGH | HIGH | Abstract contributions sentence; §2.3 RENE precedent paragraph | **Applied:** §1 now names three explicit negative/boundary findings (hierarchy adds nothing over the direct codebook; the matched-FPR operating point could not be resolved; one family was never observed). The RENE fit is now visible in the introduction, not only inferable. |
| R2 | **"One system, one corpus, synthetic perturbations - the results do not transfer."** | HIGH | HIGH | §1 scope sentence; §6.1 first limitation; A6 narrowing (title/abstract/conclusion now name the evaluator) | No further edit: the paper already concedes this and claims only a discipline, not a law. Ensure the response letter repeats that the contribution is the audit method, not the system's behaviour. |
| R3 | **"The structural equivalence is trivial algebra on a one-leaf rescale."** | MEDIUM | HIGH | §5.2 states it as a structural equivalence rather than a performance estimate | **Applied:** §5.2 now says the diagnosis is deliberately narrow and is *not* offered as a general algebraic result. Conceding the narrowness removes the "overselling" version of this attack; what remains is a fair description. |
| R4 | **"The non-direct 'chance' result is a scoring artefact of tie-as-incorrect."** | MEDIUM | MEDIUM | §5.5 reports the tie rule and the tie rate; A1 revision added the partial-information statement | No further edit. The paper now says the number is produced by a frozen preregistered rule and reports what the leaves can and cannot separate. |
| R5 | **"Reproducibility claim without a reachable artifact."** | HIGH | MEDIUM | Data Availability now states facts ("prepared for release"; URL not yet established) | **Action deferred to P2:** an anonymised artifact package is being assembled locally; publication is an owner decision. Until then the statement stays factual. |
| R6 | **"The FinQA section reads like a harness bug, not a scientific finding."** | MEDIUM | MEDIUM | §5.6 states the predicate is defined, the counts reproducible, and the mismatch is in un-regenerated result fields; no transfer/blindness claim | No further edit; the "boundary, not a performance number" framing is already explicit. |
| R7 | **"Novelty: mutation testing / the oracle problem already cover this."** | MEDIUM | MEDIUM | §2.2 positions against mutation and fault injection and states what is refined | Optional improvement (not applied): one sentence naming the oracle-problem lineage explicitly. Low expected value; the current §2.2 already carries the distinction. |
| R8 | **"Denominators and CIs are unstable"** (118 vs 111 vs 95; wide zero-event intervals). | LOW | MEDIUM | §4.3 statistical discipline; §5.1 reports both estimands and refuses to treat a degenerate bootstrap as a population bound | No edit; the paper already refuses the over-readings a reviewer might expect. |
| R9 | **"Long-horizon framing is unjustified."** | MEDIUM | LOW (after A6) | Title/abstract/conclusion narrowed; long-horizon appears only as motivation | No edit; A6 addressed the substance. |
| R10 | **"Why should SANER readers care about financial tables?"** | MEDIUM | MEDIUM | §1 frames staged pipelines generally; §2.1-2.2 connect to measurement validity and testing | Optional improvement (not applied): a positioning sentence tying the audit to staged AI-service pipelines. Deferred: risks drifting into new claims. |

## What the simulation concludes

- The two HIGH-severity risks that are *fixable by expression* have been addressed (R1 negative-result visibility; R3 narrow-diagnosis concession).
- The two HIGH-severity risks that are *not* fixable by expression are structural: external validity (R2, already the paper's stated limitation) and artifact reachability (R5, a P2 execution item).
- No claim was strengthened; two were explicitly narrowed further by conceding scope.

## Applied edits (this pass)

1. `§1`: added "Three of these findings are negative or boundary results: hierarchical organization adds nothing over the direct three-leaf codebook in this construction; the registered matched-FPR operating point could not be resolved on the frozen clean panel; and one defect family was never observed on the scored surface."
2. `§5.2`: appended "; the diagnosis is deliberately narrow, in that it explains why the raw protocol gap cannot be read as a ranking difference and is not offered as a general algebraic result about hierarchical evaluation."

Both are restatements of existing findings in existing evidence; no number, source or claim changed.