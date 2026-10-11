# Agent Runtime Environment Contract

> 状态: 活跃 | 更新: 2026-10-09 | 取代/被取代: 取代散落的个人绝对路径与旧环境说明

## Rule

Repository scripts must resolve runtime paths through `scripts/graph/agent_env.sh`. The default paths are home-relative:

- `CODEX_HOME=$HOME/.codex`
- `CLAUDE_CONFIG_DIR=$HOME/.claude`
- `OPENALEX_CONFIG=$HOME/.config/openalex.env`
- `CODEX_API_ENV=$CODEX_HOME/token_plan.env` or `CODEX_AUTH_FILE=$CODEX_HOME/auth.json`
- `AGENT_RUNTIME_ROOT=$HOME/wzh/loop_runs`
- `AGENT_PROJECT_ROOT=$HOME/wzh/projects/agents_final_tech`

Optional overrides belong in `$HOME/.config/jinrongagents/paths.env` or `JINRONG_AGENT_PATHS_FILE`. That file must contain paths only, never API keys, tokens, passwords, or authorization headers.

## Secrets

Secret values stay in their existing external files: `token_plan.env` or `auth.json`, Claude settings, and `openalex.env`. They are loaded only into process memory by the runtime that needs them. They are not copied into the repository, prompt, log, status JSON, or reports.

## Verification

```bash
bash scripts/graph/agent_env_preflight.sh
bash scripts/graph/loop_ac_launcher.sh preflight --smoke
```

The preflight prints only paths, versions, and pass/fail state. The smoke validates Codex and Claude with a minimal response. HTTP/API retries are bounded and recorded by the launcher.
