# TQ-4 Prompt Templates v2 (frozen for the TQ-4 run)

> Basis: TQ-3 prompt_templates.md with the actor output schema updated to Evidence Protocol v2.
> B/C template text is unchanged from v1. Substitutions use {} placeholders.
> Part 2 reuses the same templates with a candidate object in place of the actor output.

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
{"task_id": "{task_id}", "answer": <string or number>, "evidence": [{"kind": "cell", "table_row": <int, 0-based>, "table_col": <int, 0-based>}, {"kind": "paragraph", "paragraph_uid": "<uid shown in the provided paragraphs>"}], "notes": "<optional>"}

Rules: "answer" is the final answer only. "evidence" lists the typed locations you used (cell entries use 0-based
coordinates; paragraph entries use the uid shown in the provided paragraphs; the list may be empty). No text outside the JSON.

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

## 3. C checker template (independent-context task verification; candidate answer visible)

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

- {candidate_answer_only} = the "answer" field of the actor/candidate output only; C must not receive evidence/notes.
- Part 2: {actor_output_json} = the frozen candidate object (answer + evidence); B sees it in full, C as above.
- Neither B nor C may receive: reference/scoring material, injection information, or any answer key.
- Retries: infrastructure only, <= 4 total across both parts; content retries forbidden; cap 40 total requests.
