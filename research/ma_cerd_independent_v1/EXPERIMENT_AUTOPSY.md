# Experiment Autopsy

Date: 2026-10-20
Scope: FinRank feedback probes, MA-CERD independent baselines, matched
feedback, staged derivation, graph oracle, and uncertainty-queue adjudication.

## Experiment Matrix

| Experiment | Main result | Main confound | Judgment |
|---|---|---|---|
| FinRank Tier 1/2 | exact-match appeared best | retention intensity, prior quality, form failures | ordering not usable |
| MA-CERD matched feedback | four arms identical | feedback semantics were isolated | feedback text is not the bottleneck |
| Fresh derivation | relation 8/15 after explicit enums | schema and output representation | schema matters, not enough |
| Staged derivation | relation 8/15, node accuracy 0.424 | missing dependency structure | node localization is the bottleneck |
| Graph resource oracle | relation 0.831, impact F1 0.626 | O1/O3 disagreement | graph propagation helps |
| Transparent adjudicator + graph | relation 0.881, handling 0.839 | train-family calibration | strongest public-input baseline |
| Uncertainty model probe | relation 0.624, handling 0.012 | hard queue has unresolved structure | no LLM gain on hard queue |

## Autopsy

### Observation 1: contract formatting dominated early failures

FinRank V1/V2 produced wrapper objects, malformed JSON and unit/scorer errors.
These were not evidence-learning failures. The exact-match/feedback ordering
was therefore form-conditioned.

Mechanism: output representation and validator semantics were under-specified.
The model optimized a different serialization target from the scorer.

Prediction: once direct-object schema is fixed, form failures disappear but
semantic localization remains difficult. This was confirmed by the MA-CERD
fresh-derivation probe.

### Observation 2: prior anchoring suppresses revision

In the MA-CERD matched experiment, correct priors were always retained and
wrong priors were never repaired across all four arms. Fresh derivation removed
the prior and improved relation from 0/15 to 8/15 after schema clarification.

Mechanism: prior output is a high-salience token sequence. Natural-language
feedback does not force a new derivation pass.

Prediction: a no-prior or staged derivation should improve relation but not
necessarily node localization. Confirmed: relation improved, node accuracy
remained low.

### Observation 3: the information bottleneck is dependency structure

Staged derivation reduced output complexity but still produced impact/preserved
F1 below 0.4 on the same tasks. The graph/resource oracle, using explicit
candidate propagation, reached substantially better set F1.

Mechanism: public task JSON describes facts and a plan graph but not a complete
mapping from requirement/evidence interventions to affected nodes. O2/O3
contain hidden adjudication and simulator structure.

Prediction: a graph or simulator trace should help more than another feedback
prompt. The transparent adjudicator and graph baseline support this.

### Observation 4: disagreement is a first-class uncertainty signal

MA-CERD O1/O2/O3 alignment is heterogeneous. `o1_only_disagrees` and
`blocking_requirements` are the error concentration. The model did not improve
this queue over the transparent baseline.

Mechanism: disagreement is not random noise; it marks cases where public rule
evidence does not determine Gold semantics.

Prediction: selective routing to a richer dependency/simulator trace or human
review is better than forcing one model to resolve all cases.

## Action Plan

| Priority | Action | Expected information |
|---|---|---|
| P0 | Keep signature-rule + resource-graph + calibrated handling as the default path | High-confidence subset should remain above 0.9 relation/handling |
| P0 | Route `blocking_requirements` and `o1_only_disagrees` to an uncertainty queue | Separates coverage from risk |
| P1 | Add explicit dependency edges or simulator traces for the uncertainty queue | Tests whether missing structure, not model capability, is limiting |
| P1 | Use model only for explanation/abstention on the queue | Avoids paying for solved cases |
| P2 | Run family-cluster bootstrap on future comparative studies | Prevents treating correlated interventions as independent |

## Literature Cross-Check Boundary

The project's nearest-work record includes *Rethinking the Role of Tool Graph
Memory in Multi-Turn Tool Use* (arXiv:2610.21571), which warns that memory
benefits require matched calls/tokens and random or no-guidance controls. The
MA-CERD matched-feedback probe and tool-first baseline respect that boundary:
feedback text was matched, deterministic tool structure carried most of the
gain, and the uncertainty queue remained unsolved. This is a local
cross-check, not a claim of exhaustive literature coverage; the paper's full
text was not newly read in this closeout.

## Versioning Note

`archive/FRESH_DERIVATION_RESULT_pre_schema_v1.json` is the superseded
pre-schema probe
(relation `0/15`). `FRESH_DERIVATION_RESULT_V2.json` is the current corrected
probe (relation `8/15`) used in the matrix above. Both remain preserved with
their original request counts and tokens.

## Ruling

`TOOL_FIRST_WITH_SELECTIVE_ESCALATION`.

The scientific contribution of this exploration is not a winning feedback
contract. It is a reproducible diagnosis of where language-model experience
fails and a concrete architecture that separates public-rule reasoning, graph
propagation, calibrated handling and uncertainty escalation.
