# Scoring V3 Paired-Control Contract

Scoring V3 is a zero-model development rescore. It imports structural helpers
from immutable Scoring V2 and changes only the following boundaries:

1. **Independent role-only citation.** A row-only citation such as
   `TABLE:R1` is legal only when `required_evidence` records an independent
   binding derived from the question, row/period labels, source annotations or
   a reviewable reference chain. The scorer never scans gold numeric values to
   choose the row. Correct role accepts, wrong role rejects, and an
   indistinguishable role returns `PENDING_ADJUDICATION`.
2. **Required evidence support.** Every `operand_id` is evaluated separately.
   All exact bindings pass; any absent operand rejects; any broad binding
   without row/role binding returns `PENDING_ADJUDICATION`. Mixed exact and
   broad support therefore cannot automatically pass the complete contract.
3. **Single-element numeric span.** If `answer` is a one-element list whose
   element is numeric, `numeric_value` must equal that element. Contradiction
   returns `REJECT` through the numeric layer rather than a format-only
   reinterpretation.

Paired controls use synthetic and mutated responses. They prove implementation
boundaries only and are not natural model error rates. Pure rescore covers the
immutable first 40-call raw batch (36 final attempts) and the saved oracle,
blank-type and question-only outputs. Scoring V2, original raw, historical
manifests and V2 results are not rewritten.
