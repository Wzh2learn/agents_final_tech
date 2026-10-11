# Math-Shepherd Reference Track Audit v1

> 状态: `PAPER_VERIFIED_REPO_DATA_BLOCKED` | 更新: 2026-10-09 | 取代/被取代: 补齐 automatic process-supervision reference；不训练

## 1. Source status

- Paper: *Math-Shepherd: Verify and Reinforce LLMs Step-by-step without Human Annotations*, ACL 2024 / arXiv `2312.08935`.
- Paper and methods: `PAPER VERIFIED`.
- Official repository/data release: `NOT ESTABLISHED`.
- Paper/data licence: `UNVERIFIED`.
- GitHub exact-name search found `dujh22/math_shepherd`, created 2025-02-18, no licence, not linked by the paper; treat as unofficial candidate only.

## 2. Method

For intermediate step `s_i`, a completer generates `N` continuations. Let decoded final answers be `A={a_j}` and gold answer `a*`:

```text
Hard: y_i = 1 if exists j: a_j=a*, else 0
Soft: y_i = (1/N) sum_j I(a_j=a*)
```

`FACT`: hard labels depend on whether any rollout reaches the gold answer; soft labels estimate the success frequency.

`FACT`: main construction samples 15 solutions per problem, removes duplicates and uses LLemma-7B as completer with `N=8`, yielding about 170k solutions.

`FACT`: experiments use GSM8K and MATH; MATH500 is used for evaluation. Verification uses the minimum PRM step score; reinforcement learning uses step-by-step PPO.

## 3. Label quality

- Gold-answer dependence: required.
- Label noise: finite rollout count, completer errors and semantic step ambiguity. The paper acknowledges some noise but reports usefulness; exact noise rate `UNVERIFIED`.
- Human labels: no.
- Evidence class: verifier/Monte-Carlo-derived process label, corresponding to L3 in the project ladder.

## 4. Comparison with PRM800K

| Dimension | PRM800K | Math-Shepherd |
|---|---|---|
| Step source | model-generated MATH solutions | model-generated GSM8K/MATH solutions |
| Process label | human `-1/0/+1` | automatic hard/soft rollout success |
| Gold answer | used by human/grading context | required for rollout success |
| Evidence level | L4 candidate after independent validation | L3 verifier-derived |
| Main risk | annotator/protocol noise | completer/finite-rollout noise |

`VALUE`: our future deterministic/verifier/checkpoint labels should record provenance and compare L2/L3/L4 rather than treating all process labels as equivalent.
