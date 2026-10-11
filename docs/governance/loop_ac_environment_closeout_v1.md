# Loop A / Loop C Environment Neat Closeout

> 状态: 活跃 | 更新: 2026-10-09 | 取代/被取代: 收口本轮路径、派发器和陈旧入口整理；不取代科研状态文件

## Impact

This closeout removes three recurring execution hazards: personal absolute paths, SSH-foreground timeout dependence, and stale manual dispatch entries.

## Fact matrix

| Surface | Status | Evidence |
|---|---|---|
| Code | changed-and-verified | `agent_env.sh`, `agent_env_preflight.*`, `dispatch_loop_ac.ps1`, `loop_ac_launcher.sh`, orchestrator/monitor updates |
| Runtime | changed-and-verified | GB10 Codex/Claude smoke `0/0`; detached synthetic task `running -> done rc=0` |
| Docs | changed-and-verified | environment and launcher contracts; old commands redirected to current entry |
| Rules | verified-current | `AGENTS.md` / `CLAUDE.md` boundary preserved; no frozen node changed |
| Memory | out-of-scope | `memory/STATE.md`, `memory/THREADS.md` not edited by this closeout |
| Workspace | pending | Loop A research task `stage-ed-20261009` remains running; existing dirty files preserved |

## Changes

- Centralized non-secret paths through `$HOME/.config/jinrongagents/paths.env` and `scripts/graph/agent_env.sh`.
- Added Windows and GB10 preflight entries. Secrets remain in existing external carriers and are never printed.
- Added detached launcher with tmux, outer timeout, bounded HTTP-429 retry, status JSON and logs.
- Replaced manual A/C command guidance in `graph_orchestrator.sh` and `docs/17_Graph_Engineering_多层Loop设计.md`.
- Archived `supervisor_qoder.sh` and `supervisor_m1.sh` under `scripts/archive/` with `_legacy` names.
- Removed stale GLM/72B status from `loop_d_monitor.sh` and removed remote Git fetch from its status path.

## Verification

- `agent_env_preflight.ps1`: PASS on Windows.
- `agent_env_preflight.sh`: PASS on GB10.
- `loop_ac_launcher.sh preflight --smoke`: PASS on GB10.
- Synthetic detached launcher test: PASS.
- Shell syntax checks: PASS on GB10.
- `docs_lint.py --json /tmp/...`: PASS, 0 fail / 6 existing age warnings.
- `sync_skills.sh --check`: PASS, 99/99.
- Repository changed-file scan for real credential-shaped values: PASS.

## Pending

1. Loop A is still executing the authorized Stage E/Stage D research assignment.
2. The GB10 Codex configuration contains an embedded MCP bearer credential. Its value was accidentally surfaced during configuration diagnostics and should be treated as compromised until rotated. No repository file contains the value. Migration to an external secret carrier and rotation require user approval because they change authentication state.
3. Six existing docs age warnings remain; they concern historical active documents and were not silently rewritten.

## Cleanup candidates

None deleted. The two old supervisors were moved, not removed. Temporary preflight/self-test artifacts remain under `/home/testuser/wzh/loop_runs/` for audit and can be removed only after the user reviews this closeout.
