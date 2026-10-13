# RENE Adversarial Review v1 (three reviewer personas)

> date: 2026-10-13 | author: Loop D internal adversarial pass | status: `EXPRESSION-LEVEL REVIEW ONLY`
> boundary: no claim changed, no experiment added, no number touched. This is a self-simulation, **not** an independent review; the independent pass is still outstanding (see `LOOP_C_REVIEW_A1A7_REVISION_v1.md`).
> companion: `RENE_REVIEWER_RISK_SIMULATION_v1.md` (risk table with applied hardenings). This document goes deeper on the three persona-level rejection arguments.

## Persona A - Software-engineering / RENE reviewer

**Strongest reject argument.** "The RENE track asks for reproducibility studies or negative results. This manuscript is a *measurement audit of the authors' own bespoke evaluator*: the corpus is synthetic, the mutations are the authors' own, and the failures are found in the authors' own instrument. The three 'negative' findings are consequences of one frozen configuration rather than findings about a class of systems; and the artifact is not actually reachable, so even the reproducibility half of RENE is unmet."

**Existing defence in the manuscript.** §1 now names the three negative/boundary findings explicitly; §2.3 positions against four verified RENE papers (two of them negative results, one a replication) and states the shared concern with measurement validity; §6.1 opens with the single-corpus limitation; the Data Availability statement states facts rather than a release that has not happened.

**Remaining wording risk.** The paper never says, in one clause a RENE chair can quote, *why this is a negative result rather than a system report*. The current framing invites the "bespoke" read. **Recommended expression fix (no claim change):** one sentence in §1 stating that the findings are negative results about an *instrument* class - a protocol that cannot separate its own protocols and cannot observe a whole defect family - rather than a performance report about one pipeline.

## Persona B - AI-evaluation reviewer

**Strongest reject argument.** "The paper claims to speak to long-horizon AI evaluation but measures none of it. There is no horizon manipulation, no agent trajectory, no error-propagation measurement; the single 'second dataflow' failed for construction reasons. So the contribution to how the AI-evaluation community should evaluate systems is a plausible analogy, not evidence."

**Existing defence.** A6 narrowed the title, abstract opening and conclusion to the staged document-intelligence evaluator; the three constructs (visibility / detection / harmfulness) are operationalised with explicit denominators; §6.3 ends with a design recommendation rather than a law.

**Remaining wording risk.** §1's opening sentence still gestures at "tool-using agents and long-horizon workflows" before the scope sentence arrives. That ordering is defensible (motivation first), but a hostile reader can quote the first sentence alone. **Recommended expression fix:** move the scope sentence *before* the analogy, so the very first claim a reader meets is the measured one.

## Persona C - Skeptical reviewer

**Strongest reject argument.** "Three of the four headline findings dissolve on inspection. (i) The 'structural equivalence' is a one-leaf rescale - algebra, not discovery. (ii) The 'unobserved family' is 13 items that a single judge called referentially equivalent; the paper now admits it cannot tell whether they were harmless, so the headline number measures the authors' matcher, not the system. (iii) The second dataflow's zero detection follows from the authors' own construction - they say so. What is left is a well-organised list of things the authors' harness cannot see."

**Existing defence.** §5.2 concedes narrowness and explains why the structural result is still diagnostic (it forecloses reading the raw protocol gap as a ranking difference); §5.1 discloses the single-judge equivalence and explicitly refuses to read the non-response as harmful false negatives; §5.6 states the predicate is defined and refuses any transfer or ability claim; §5.5 reports the ablation beside the positive result rather than after it.

**Remaining wording risk.** The skeptical read is *close to the paper's own text*, which is good for honesty and risky for perceived contribution. The defence is currently spread across sections; a reviewer skimming the abstract may still take away "0/13 = blind spot" and "1.0 = hierarchy works". **Recommended expression fix:** the abstract already discloses benign absorption; add the *consequence* clause so the takeaway cannot be the naive one - namely that the audit's product is the *boundary map and the refusal of three over-readings*, not a detector ranking.

## Consolidated wording risks (all three personas)

| # | Risk | Persona | Fix type | Applied? |
|---|---|---|---|---|
| W1 | No quotable "this is a negative result about an instrument" clause | A | expression | **to apply** |
| W2 | Motivation sentence precedes the scope sentence in §1 | B | expression (reorder) | **to apply** |
| W3 | Abstract takeaway can still read as blind spot + hierarchy works | C | expression (add consequence clause) | **to apply** |

None of the three fixes introduces a claim, a number, or a new experiment. All three are restatements of what the paper already says elsewhere.