# Loop A Assignment: Stage E Quantify -> Stress-test -> Transfer -> Distill

You are Loop A executing an authorized GB10 research task.

Read these files first:

- `/home/testuser/wzh/research_stage_e_d_20261009/PROMPT.md`
- `/home/testuser/wzh/research_stage_e_d_20261009/IMPLEMENTATION_PLAN.md`
- `/home/testuser/wzh/projects/agents_final_tech/AGENTS.md`
- `/home/testuser/wzh/projects/agents_final_tech/memory/STATE.md`
- `/home/testuser/wzh/projects/agents_final_tech/memory/THREADS.md`
- `/home/testuser/wzh/projects/agents_final_tech/docs/research/README.md`

Execute the task on GB10 in:

- project: `/home/testuser/wzh/projects/agents_final_tech`
- supporting task state: `/home/testuser/wzh/research_stage_e_d_20261009`

Authorized work:

1. Recompute derived Stage E observability statistics from frozen JSON artifacts only.
2. Audit metric precedent and official NIST/TEVV and ITIL/AI-governance sources.
3. Audit PRM800K and Math-Shepherd from official paper/repository/data metadata, reusing existing Agent Distillation, ToolAlpaca, TheAgentCompany, AgentTuning, Agent-FLAN and SOD audits.
4. Write the 12 requested Markdown deliverables under `docs/research/`.
5. Generate any supporting analysis data and figures under `research/stage_e_stage_d_20261009/`.
6. Run deterministic validation and write `research/stage_e_stage_d_20261009/loop_a_receipt.json`.

The twelve deliverables are exactly:

- `stage_e_observability_metrics_v1.md`
- `stage_e_metric_precedent_review_v1.md`
- `stage_e_118_quantification_v1.md`
- `stage_e_threshold_visibility_analysis_v1.md`
- `stage_e_multileaf_protocol_v2.md`
- `nist_tevv_background_evidence_v1.md`
- `itil_ai_governance_background_evidence_v1.md`
- `stage_e_narrative_after_advisor_feedback_v1.md`
- `process_supervision_adaptation_review_v1.md`
- `derived_process_supervision_design_v1.md`
- `stage_d_minimal_experiment_v2.md`
- `stage_e_stage_d_unified_story_v1.md`

Hard boundaries:

- Preserve all frozen Stage E values and claim boundaries.
- Do not run GPU training, formal C0/C1/C2/C4, Phase 2, Stage R, E-D-R, model/judge calls, production services, databases or package installation.
- Do not use paid APIs beyond bounded public metadata/source verification.
- Do not write credentials into files, prompts, logs or reports.
- Do not commit, push, amend or rewrite Git history.
- Do not modify frozen hashes, schemas, tests, `docs/33*`, `docs/34*`, `memory/STATE.md`, `memory/THREADS.md` or existing dirty runtime logs.
- Use `./venv/bin/python` for Python on GB10. Use OpenAlex through `~/.config/openalex.env`.
- Keep evidence labels explicit: FACT, INFERENCE, VALUE, UNVERIFIED.
- A negative or unavailable result is valid; never fabricate missing labels or joins.

Before writing conclusions, record source URLs, revisions, licence status, data schema evidence and exact blockers. End by answering all 17 questions from `PROMPT.md` in `loop_a_receipt.json` and stop.
