# Loop A / Loop C Detached Launcher

> 状态: 活跃 | 更新: 2026-10-09 | 取代/被取代: 取代旧手工 tmux 派发说明；历史 supervisor 脚本保留为只读历史

## Purpose

`scripts/graph/loop_ac_launcher.sh` is the current one-shot dispatch entry for Loop A and Loop C on GB10. It keeps the process alive after SSH disconnects and makes timeout, log and status handling explicit.

## Commands

```bash
bash scripts/graph/loop_ac_launcher.sh preflight
bash scripts/graph/loop_ac_launcher.sh preflight --smoke
bash scripts/graph/loop_ac_launcher.sh start a <task-id> <prompt-file> 14400
bash scripts/graph/loop_ac_launcher.sh start c <task-id> <prompt-file> 7200
bash scripts/graph/loop_ac_launcher.sh status <task-id>
bash scripts/graph/loop_ac_launcher.sh logs <task-id> a 80
bash scripts/graph/loop_ac_launcher.sh stop <task-id> a
```

`preflight` checks executable paths and external configuration file presence without reading or printing credentials. `--smoke` adds a minimal Codex and Claude response check. `start` launches a detached tmux session, writes `$HOME/wzh/loop_runs/<task-id>/<role>.log`, and writes a status JSON file.

## Timeout and recovery

The launcher uses an outer `timeout --signal=TERM --kill-after=30s` process guard. A timeout is recorded as a failed status and is not silently retried. A transport interruption during the dispatcher SSH call does not kill the detached tmux process; reconnect and query `status` or `logs`.

## Verified launcher behavior

On 2026-10-09 the GB10 launcher passed configuration preflight, Codex/Claude minimal smoke (codex_rc=0, claude_rc=0), a synthetic detached task self-test (unning -> done, c=0), and remote shell syntax checks. The first dispatch attempt exposed an unbound heredoc variable in the generated runner; the generator now emits a quoted static runner and passes task-specific values through environment variables. This is a fixed tool defect, not a scientific result.

## Boundary

This launcher does not authorize model, judge, API, dataset, training, production-service or GPU actions. The task prompt must state the authorized scope. Loop C remains read-only and independent; it must not modify Loop A outputs.

## Related tools

`graph_orchestrator.sh` remains the Loop B daemon entry. `dispatch_precheck.sh` remains the pre-dispatch contract checker. `scripts/dev_remote_demo.ps1` is the live demo tunnel and uses the same SSH keepalive pattern. The older `scripts/archive/loop_ac_supervisor_qoder_legacy.sh` and `scripts/archive/loop_ac_supervisor_m1_legacy.sh` are archived blocking supervisors and are not current dispatch entries.
