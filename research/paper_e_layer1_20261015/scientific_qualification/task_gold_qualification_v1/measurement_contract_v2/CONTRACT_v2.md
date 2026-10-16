# Task Measurement Contract v2

> Status: DEVELOPMENT_ONLY; AI-authored; not independent gold. Date: 2026-10-16.

## Three separate judgments

- reference_validity: traceable support for question/reference. Record computation replay, semantic mapping, and unit/period gaps separately.
- evidence_effect: whether perturbed material still supports the fixed task answer requirements. P/A/U remain provisional semantic judgments.
- system_outcome: future system output. This round is `NOT_RUN`; never derive it from evidence_effect.

## Requirements before evidence paths

Each task fixes question, object, period, unit/scale, operation direction, granularity, and tolerance. NOT_APPLICABLE needs question-based justification; UNRESOLVED cannot be renamed NOT_APPLICABLE. A reference cell set is not automatically the unique necessary evidence. Each evidence path must support all necessary dimensions and is marked SOURCE_EXPLICIT / DETERMINISTIC_DERIVATION / AI_INFERENCE / UNRESOLVED. Paths are non-exhaustive unless proven otherwise.

## Context and units

Allowed context: full paragraphs, lower-level headers, row names, footnotes, explicit table-wide unit statements. Inference from lexical nearest neighbours, financial convention, or AI reasoning is marked AI_INFERENCE and never becomes gold. A report-level unit rule may be used only when its scope is located.

## Extra year/scope words

No global rule to ignore years or to treat extra words as harmful. First decide whether the word acts on a necessary dimension. If it conflicts and cannot be resolved, keep UNDETERMINED. Q08/Q09 may remain U.

## Q06 proof burden

Keep `COLUMN_IDENTITY_UNIT_DAMAGE_CANDIDATE`. To strengthen to non-recoverable, list competing interpretations and their task meanings and show exclusion evidence. Otherwise preserve the candidate status. Do not claim formal unrecoverability.

## Offline verification boundary

Mechanical PASS only means reference operations and permission boundaries are executable. It does not establish task gold, semantic mapping, or system performance. Four negative checks are required: invalid evidence coordinate, changed-copy input hash, unresolved necessary scale, and official-reference leakage in public inputs. All must be rejected or blocked.

## Statuses

REFERENCE_REPLAY_READY / PARTIAL_REFERENCE_REPLAY / MEASUREMENT_SPEC_BLOCKED. `scientific_gold_validity` remains NOT_ESTABLISHED. Layer-2 is not authorized.
