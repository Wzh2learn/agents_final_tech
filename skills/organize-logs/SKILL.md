---
name: organize-logs
description: |
  Organize experiment logs into a structured, searchable directory with per-dataset grouping,
  README index, and cross-reference to experiment overview docs. Use when logs accumulate
  in a flat directory and need to be categorized, indexed, and made discoverable.
  Triggers: "organize logs", "给 log 建索引", "整理某数据集的 log".
  Also applies for incremental archival after new experiments complete.
metadata:
  category: docs
  tags: [logs, experiment-management, organization]
---

# Organize Experiment Logs

> **Core principle**: Flat log directories become unusable past ~20 files. 
> Structured directories with README indexes make any experiment findable in <10 seconds.

## When to use
- Logs directory has accumulated 10+ unorganized log files
- New experiment just completed — archive it into the existing structure
- Need to find "that experiment from last week" and can't
- Preparing experiment results for a paper or report

## Full organization flow (first time for a dataset)

### Step 1: Inventory all logs
```bash
ls -la logs/*.log | wc -l
# Group by naming pattern
ls logs/ | sed 's/_[0-9]*\.log//' | sort -u
```

### Step 2: Identify datasets by reading log content
Don't rely solely on filenames — read the first 10 lines of each log to confirm:
- Which dataset was used
- Which model configuration was run
- Key hyperparameters (batch size, learning rate, epochs)

```bash
for f in logs/*.log; do echo "=== $f ==="; head -10 "$f"; done
```

### Step 3: Create structured subdirectories
```
logs/
├── <dataset_A>/
│   ├── README.md           # Index with best results and experiment status
│   ├── baseline/           # Baseline experiments
│   ├── ablation/           # Ablation studies
│   ├── hyperparameter/     # HP tuning runs
│   └── final/              # Final reported results
├── <dataset_B>/
│   └── ...
└── README.md               # Top-level overview pointing to each dataset
```

### Step 4: Move logs into structure
```bash
# Move with git to preserve history
git mv logs/exp_baseline_*.log logs/dataset_A/baseline/
git mv logs/exp_ablation_*.log logs/dataset_A/ablation/
```

### Step 5: Create per-dataset README
```markdown
# Dataset A Experiments

## Best Results
| Config | HR@10 | NDCG@10 | Log file | Date |
|--------|-------|---------|----------|------|
| final_v3 | 0.NNNN | 0.NNNN | final/exp_v3_0715.log | 2026-07-15 |

## Experiment History
| # | Tag | Purpose | Result | Status |
|---|-----|---------|--------|--------|
| 1 | baseline | Reproduce paper baseline | HR=0.NNNN | ✅ Done |
| 2 | ablation_gate | Remove a component | HR=0.NNNN | ✅ Done |
```

### Step 6: Update global experiment overview
Sync the per-dataset README findings back to any top-level experiment tracking document.

### Step 7: Check .gitignore
Many projects gitignore `logs/*/`. If your organized subdirectories are inside `logs/`, ensure they're not ignored:
```bash
git check-ignore logs/dataset_A/README.md
# If ignored, update .gitignore to allow the structured subdirectories
```

### Step 8: Verify and commit
```bash
git status
git add logs/
git commit -m "organize: structure dataset_A experiment logs"
```

## Incremental archival (after new experiments)

Shorter flow for archiving 1-2 new logs into an existing structure:

1. List new logs in the root `logs/` directory
2. Read first 10 lines to identify dataset + config
3. Move to the correct subdirectory
4. Update the per-dataset README with the new result
5. Update global experiment overview if result is notable
6. Commit

## Rules

- **Read log content to classify** — filenames lie, content doesn't
- **Update over preserve** — if new results supersede old ones, mark old entries as superseded
- **Absolute dates** — never write "yesterday" or "last week" in README; always ISO dates
- **Git mv, not cp** — preserve history
- **One commit per dataset organized** — makes it easy to revert if structure is wrong

## Anti-patterns
- Organizing by date instead of by purpose (date is secondary info, purpose is primary)
- Creating too many subdirectory levels (2 levels max: dataset/category)
- Leaving README as "TODO" — write it during organization, not later
- Duplicating logs (original + copy in subdirectory) — move, don't copy
