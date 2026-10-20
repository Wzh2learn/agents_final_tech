# TQ Chain Run Summary - TQ-4 / 20261016T082849Z_430d927a

> status=COMPLETED; stop=None; scientific_gold_validity=NOT_ESTABLISHED

## Part 1（受控扰动部分）
| task | answer | scoring_v21 | legality | B | C |
|---|---|---|---|---|---|
| N1 | 1.5% | MATCH | True | alarm | alarm |
| N2 | $22,448 | MATCH | True | accept | accept |
| N3 | 0.68% | MATCH | True | accept | accept |
| N4 | 63.4 | MATCH | True | accept | accept |

part1 summary: {"valid": 4, "match_over_planned": 1.0, "match_over_valid": 1.0, "legality": {"legal": 4, "illegal": 0}, "b_decisions": {"alarm": 1, "accept": 3}, "c_decisions": {"alarm": 1, "accept": 3}, "label": "\u65e7\u6c60\u65b0\u589e\u4efb\u52a1\u7684\u53d7\u63a7\u6270\u52a8\u90e8\u5206\uff08\u975e\u81ea\u7136\u5931\u8d25\u5206\u5e03\uff1b\u65e0\u539f\u59cb\u7248\u5bf9\u7167\uff09"}

## Part 2（人工候选）
| candidate | answer_kind+legality | B | C |
|---|---|---|---|
| Q02-C1 | correct+legal | accept | accept |
| Q02-C2 | correct+illegal | alarm | accept |
| Q02-C3 | incorrect+legal | alarm | alarm |
| Q02-C4 | incorrect+illegal | alarm | alarm |
| Q03-C1 | correct+legal | accept | abstain |
| Q03-C2 | correct+illegal | alarm | abstain |
| Q03-C3 | incorrect+legal | accept | accept |
| Q03-C4 | incorrect+illegal | alarm | accept |
| Q04-C1 | correct+legal | accept | accept |
| Q04-C2 | correct+illegal | invalid | accept |
| Q04-C3 | incorrect+legal | alarm | abstain |
| Q04-C4 | incorrect+illegal | alarm | abstain |

matrix: {"correct+legal": {"b": {"accept": 3}, "c": {"accept": 2, "abstain": 1}}, "correct+illegal": {"b": {"alarm": 2, "invalid": 1}, "c": {"accept": 2, "abstain": 1}}, "incorrect+legal": {"b": {"alarm": 2, "accept": 1}, "c": {"alarm": 1, "accept": 1, "abstain": 1}}, "incorrect+illegal": {"b": {"alarm": 3}, "c": {"alarm": 1, "accept": 1, "abstain": 1}}}
duplicate pairs: [{"pair": ["Q02-C1", "Q02-C2"], "c_decisions": ["accept", "accept"], "c_agree": true, "identical_c_prompt": true}, {"pair": ["Q02-C3", "Q02-C4"], "c_decisions": ["alarm", "alarm"], "c_agree": true, "identical_c_prompt": true}, {"pair": ["Q03-C1", "Q03-C2"], "c_decisions": ["abstain", "abstain"], "c_agree": true, "identical_c_prompt": true}, {"pair": ["Q03-C3", "Q03-C4"], "c_decisions": ["accept", "accept"], "c_agree": true, "identical_c_prompt": true}, {"pair": ["Q04-C1", "Q04-C2"], "c_decisions": ["accept", "accept"], "c_agree": true, "identical_c_prompt": true}, {"pair": ["Q04-C3", "Q04-C4"], "c_decisions": ["abstain", "abstain"], "c_agree": true, "identical_c_prompt": true}]

## Cost
{"run_gen_attempts": 36, "run_retries": 0, "run_tokens_settled": 40205, "run_aux_ops": 72, "master_entries_for_run": 72, "master_gen_attempts": 36, "master_settled_tokens": 40205, "first_request_utc": "2026-10-16T08:29:02Z"}

## Notes
- Part 1 与 Part 2 分开记账、分开评价；不得混算错误率。
- C = 同模型、独立上下文核验（可见候选答案；看不到引用）。C 的 C1/C2、C3/C4 为相同刺激重复调用，不能当独立证据，也不能声称 C 对引用变化不敏感。
- B 的总体 accept 不能自动当作候选引用支持性已验证；引用支持性在无可判定记录时为 NOT_ASSESSED。
- 机械合法性、参考匹配、模型核验决策三者分列；均不构成 confirmatory 结论。
- scientific_gold_validity = NOT_ESTABLISHED；无 confirmatory claim。
