# Output-budget sensitivity: second two-arm skill pilot

Date 2026-10-29. Status: post-hoc development exploration, one task/one run per arm, not independent confirmation of a method. Original attempts and the earlier [pilot return](SKILL_PILOT_RETURN.md) remain unchanged.

## Question and contract

The preceding no-skill run stopped at a recorded 4,096-token output limit with no report, while the all-skill run passed. To test whether the no-skill result was only a no-report truncation artifact, this pair uses the same task, prompt, two original skill files for the all-skill arm, 8 POST/450,000 request-byte/300-second ceilings, Docker isolation and separate original verifier; the configured model output limit is increased from 4,096 to 8,192 for both arms. We have not independently verified that the server accepted an 8,192-token output cap; no completed step in this pair reaches either cap. The skill arm receives additional algorithm text: the experiment is a fixed-skill versus no-skill comparison, not an equal-information or dynamic selection test.

Both saved work directories contain identical trace SHA-256 `9e81b386f0d8cea16d376b041d7a7e8fed5ba65b53e989444c76cef408442c2a`. Verifier/oracle were not mounted for agent execution and were used only afterward. Original input and test assertions are unchanged; pytest 9.0.1 in a separate container is an adapted run, not official BenchFlow execution.

| Arm | Outcome | Known completed-step tokens | POSTs | Elapsed |
| --- | --- | ---: | ---: | ---: |
| no skill | `report.json` and `solve.py` generated; verifier 1 passed / 9 failed; agent exit 1 after last model request timed out | 42,085 | 6, of which final POST has no step-finish/usage | 239.464 s including verifier |
| two original skills | report generated; verifier 10 passed; agent exit 0 | 67,243 | 6, all six recorded steps | 57.852 s including verifier |

The no-skill report was available before the timed-out sixth request. Its verifier failures include interpreting prompt token counts as block counts and mismatched total hit tokens and cache outputs. Its missing final response leaves open whether it would have repaired its output with additional successful interaction. Thus this pair weakens the explanation that no-skill cannot produce a report solely because of the former output cutoff, but does not establish the final effect of skills under uninterrupted, equal-information, equal-cost evaluation. Result consistency across these two rounds is on the same task, not on an independent task family.

## Accounting and provenance

New round has 109,328 known completed-step event tokens including cache and 12 POSTs; the uncompleted last no-skill POST has UNKNOWN usage. Adding six earlier receipts gives 458,495 known tokens; the earlier timeout's unfinished POST also has UNKNOWN usage. Event totals are not independently verified backend billing; no training, paid API, or production write.

GB10 evidence root `/home/testuser/wzh/research_evidence/agent_skill_method_20261029/`:

- `llm-prefix-cache-replay__no_skill__258386/receipt.json`, SHA-256 `af70e1af34121cb5c0045a78984c276cdc79e5d5965579ad0d482e515d54fbd8`; raw SHA `f2c8a3433a895c5703be80ad2c50eef5289ec25e70396d4a02b4040c7d5b40c8`.
- `llm-prefix-cache-replay__all_skill__263034/receipt.json`, SHA-256 `be83fcb6ea598934d7d99adffbf7e6f5ba948ad976940fa0cd0fd473e24b3b61`; raw SHA `d958631d0b4c3851c35c390e789cab137e3ad566387d2f6bec594444c7b67821`.
- [`run_skill_episode_output8192.py`](run_skill_episode_output8192.py), SHA-256 on GB10 `4111a0be97845740769722e2e596871d51c7693d14d2372d7f6931b4d06e7afb`; differs from writable 4,096 pilot driver in configured per-step output ceiling only.

The full raw events, verifier output, generated programs and inputs remain on GB10. Two summary receipts are copied locally; no raw evidence has been overwritten. Repeat with another independent qualified task, more than one run, equal-information documented controls and bounded repair budgets; dynamic skill applicability or natural-version-change claims remain untested.
