# TQ-3 Prompt Templates v1 (fixed; do not customize per input)

> Status: PREPARED. Not executed this round. Substitutions use {} placeholders.
> actor: 1 call per input (12 planned). B checker: 1 call per actor output (12).
> C checker: 1 call per actor output (12). Total planned 36; infra retries <= 4; cap 40.

## 1. actor template

System prompt (fixed):
You answer financial table questions. Use only the provided table and paragraphs.
Return strict JSON only. Do not add commentary outside the JSON.

User prompt:
Question: {question}

Table (2D array; row 0 contains headers):
{table_json}

Paragraphs:
{paragraphs_json}

Return JSON with exactly these fields:
{"task_id": "{task_id}", "answer": <string or number>, "evidence": [{"table_row": <int>, "table_col": <int>}], "notes": "<optional>"}

Rules: "answer" is the final answer only. "evidence" lists the cells you used
(may be empty). No text outside the JSON.

## 2. B checker template (same-source verification)

System prompt (fixed):
You are a careful verifier of a financial table QA answer. You must check the
candidate answer against the provided material and report concrete evidence.

User prompt:
Material:
- Question: {question}
- Table (2D array; row 0 contains headers): {table_json}
- Paragraphs: {paragraphs_json}

Candidate answer (from another system):
{actor_output_json}

Tasks:
1. Check whether the candidate answer is consistent with the table/paragraphs.
2. If the task is arithmetic, recompute from the cells the candidate cites; if
   citations are missing or wrong, identify your own cells and recompute under
   the stated unit/period of the question.
3. Decide: accept / alarm / abstain. "alarm" requires a concrete contradiction
   point (quote the cell or paragraph). "abstain" if the evidence is
   insufficient or the task is ambiguous.

Return JSON: {"decision": "accept|alarm|abstain", "reason": "...", "contradiction_points": ["..."], "recompute": "<optional>"}

## 3. C checker template (independent-path task verification)

System prompt (fixed):
You independently solve the task from the provided material, then compare with
a candidate answer. Do not reuse the candidate's reasoning or citations; solve
it yourself first.

User prompt:
Material:
- Question: {question}
- Table (2D array; row 0 contains headers): {table_json}
- Paragraphs: {paragraphs_json}

Candidate final answer:
{candidate_answer_only}

Tasks:
1. Solve the question yourself from the table/paragraphs.
2. Compare your answer with the candidate answer (equivalent formats allowed,
   e.g. 0.47 vs 47% for a ratio).
3. Decide: accept / alarm / abstain. "alarm" requires a concrete contradiction
   point. "abstain" if you cannot solve it confidently from the material.

Return JSON: {"decision": "accept|alarm|abstain", "reason": "...", "own_answer": "...", "contradiction_points": ["..."]}

## 4. Substitution and access rules (hard)

- {candidate_answer_only} = the "answer" field of the actor output only.
  C must not receive the actor "evidence" or "notes" (path independence).
- B and C receive the SAME input block and the SAME actor output file; C is
  additionally restricted as above. Both arms use the same call budget (1 call).
- Neither B nor C may receive: dev_panel/reference/*, dev_panel/scoring/*,
  specs_rev1/*, injection information, or any answer key material.
- Retries: infrastructure errors only, <= 4 total across all arms; content
  retries are forbidden. If more calls are needed, shrink scope; never exceed
  40 total requests without a new authorization.
