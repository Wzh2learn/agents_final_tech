# Script Catalog

`scripts/catalog.toml` is the machine-checked inventory for this directory. It classifies every tracked script into exactly one lifecycle category without changing established command paths.

| Category | Meaning | Change rule |
|---|---|---|
| `production` | Runtime entry point, compatibility CLI, or helper reached by the application | Preserve its public command/import contract; reusable implementation belongs in `src/` |
| `operations` | Setup, deployment, maintenance, verification, or governance tooling | Default to idempotent behavior, explicit targets, and safe failure |
| `experiments` | Evaluation, benchmark, probe, demo, or research workflow | Keep generated output outside Git or under the documented evidence location |
| `archive` | Consumed prompts and historical scripts | Read-only evidence; do not use as current operating instructions |

## Adding or moving a script

1. Put reusable production logic under `src/`; keep `scripts/` as a thin entry point.
2. Add the new path to one category in `catalog.toml` in the same commit.
3. Run `PYTHONPATH=src python3 -m pytest tests/test_script_catalog.py -q`.
4. Update callers before physically moving an established script path.

The catalog records ownership, not runtime health. A `production` label does not mean a service is deployed or currently running. `run_tabular_inference.py` is a production subprocess used by `src/tabular_mcp_server/service.py`, not an isolated experiment.

## Scope and research assets

The catalog covers `scripts/` only; its `research` root means `scripts/research/`, not the repository's top-level `research/`. The research asset and evidence authority is `paper/research_asset_map_v2.md`; cross-layer entry points are in `docs/architecture/codebase_map.md`.

A script's presence is not permission to execute it. `scripts/graph/loop_b_verify.sh` includes service, model-backed QA and database checks; it is not a zero-call local test command. Only run the focused offline tests named in the current task. Formal experimental runs and remote installation checks belong to the explicitly approved GB10 execution scope.
