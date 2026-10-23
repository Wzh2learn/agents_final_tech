# Financial Feedback Learning And Delivery Experiment V1

Date: 2026-10-24

Status: `PROTOCOL_FROZEN / EXECUTION_IN_PROGRESS`

This directory contains one experiment-specific runner for the current
research cycle:

- C2: compare ordinary answer/execution-filtered LoRA SFT with cheap consistency
  and evidence-dependency feedback filtering on derived financial-table tasks.
- C3: freeze generated answers and replay a strong all-check delivery rule versus
  a calibrated risk policy.

The source is TAT-QA real financial tables under CC BY 4.0. Questions and
candidate corruptions are deterministic project derivatives. Controlled
corruptions are mechanism probes, not estimates of natural error frequency.

Canonical files:

- `EXPERIMENT_PROTOCOL.json`: frozen task, split, arm, metric and stop rules.
- `feedback_learning_core.py`: deterministic task generation and scoring.
- `run_feedback_learning_experiment.py`: GB10 dataset, SFT, generation and
  analysis entry point.
- `test_feedback_learning_experiment.py`: focused deterministic tests.

Runtime data, adapters and raw generations are written to a GB10 run directory
outside Git. Only small receipts, summaries, scripts and protocols are
versioned here.
