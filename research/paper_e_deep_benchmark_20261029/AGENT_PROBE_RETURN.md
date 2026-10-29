# Isolated OpenCode/Qwen qualification: bounded return

Date: 2026-10-29, GB10. Status: `MODEL_PROVIDER_WORKS_READ_ACCESS_QUALIFICATION_FAILED`; not a successful agent task or scientific confirmation.

| Physical OpenCode attempt | Result | Observability / usage |
| --- | --- | --- |
| Initial, no stdin EOF | Timeout, exit 124, 100 s, empty stdout/stderr. Existing project e2e documentation describes SSH waiting for EOF; this is a plausible explanation, not proven for this invocation. | Backend request count and tokens UNKNOWN. |
| EOF, isolated directory without project provider config | Exit 1 with `UnknownError: Unexpected server error`. The error reference was not found in the shared OpenCode log; project versus isolated provider context differed, but cause is not established. | No tool action or usage recorded; backend requests/tokens UNKNOWN. |
| EOF, isolated loopback provider with no configured API key and no configured MCP, restrictive permissions | Process exit 0 but task did not complete. Three `read` tool attempts against the synthetic public report were denied by the configured permission rules. The model then reported the permission conflict rather than answering. | Four recorded `step_finish` events: non-cache input 3,440, cache-read 8,764, output 336; sum of event total fields 12,540 tokens. Actual underlying HTTP requests were not independently counted. |

No other model calls were made in this qualification. No MCP tool action appears in the third raw trace. Process exit 0 is not task success; no conclusion is drawn about the answer accuracy or the former error's cause.

The isolated configuration permitted a specific local file but retained default-deny rules. The error output shows both allow and deny rules; a related [OpenCode issue](https://github.com/anomalyco/opencode/issues/13646) reports path-based read allow/deny behavior that resembles this result, but version-specific root cause is unconfirmed. Changing `read` to global allow would exceed the authorized public-file-only boundary. A local `bwrap` capability check failed with `setting up uid map: Permission denied`; `--pure` is not a filesystem sandbox. A safe isolation alternative remains needed before further tasks. No fourth OpenCode call was made.

Evidence root: `/home/testuser/wzh/research_evidence/paper_e_agent_probe_20261029/` (private GB10 working evidence, not publication). The synthetic input `report.txt` SHA-256 is `33e38fe7f90536823544f3e6bd5ca4e9aeb350507eecb4cb38ba68cffc517515`. First empty raw SHA-256 is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; second raw `raw_agent_probe_eof.jsonl` is `a3cee030d59449a7d7ad1d5d8990820a18d884b8c8dbb7fd45ace65cce619899`; third raw `raw_agent_probe_isolated.jsonl` is `db78a6a409eed32e2596760688bc53e42c12256d2c81373f14d60901437baf83`; its isolated, non-secret `opencode.json` is `0cbd371f168d3855778fb19c04cc5fa98b25820813b932413a458fbb3bbabab8`.

Future tasks require a verifiable file-level OS boundary and a working permission contract. Keep query ground truth outside the agent-visible workspace; preserve tool events and usage, and distinguish agent process outcome from benchmark correctness. The synthetic observational theorem fixture and this operational failure are separate evidence types.
