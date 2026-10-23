# Governance Return

Date: 2026-10-23, Asia/Shanghai

Status: `RESEARCH_BASELINE_READY_WITH_LOCAL_GAPS`

Scope: pre-research governance and asset continuation. This return is a
scientific baseline and execution handoff, not a new experiment, submission,
human gold, blind review, or contribution certification.

## 1. What Was Corrected

1. **G3 `5/43` was overinterpreted.** The depth-2 tree selected 40 of 400 rows
   with 43 target-useful expansions. The same-budget hypergeometric expectation
   is 4.3 and `P(X>=5)=0.4347520938`; the exact central 95% range is 1-8.
   Therefore `5/43` is compatible with random variation. The old “weak
   learnable signal” wording is withdrawn in current materials; the old report
   remains preserved as dated evidence.

2. **G3 threshold protocol was misdescribed.** `G3_VISIBLE_FEATURE_PREDICTION_V5.py`
   records inner thresholds, but final decisions use globally averaged OOF
   scores and one top-10% cutoff over all 400 rows. This is a development
   ranking diagnostic, not nested frozen-threshold execution. Selecting 40 rows
   is action-count matching, not cost matching.

3. **G3 oracle is headroom, not utility.** Always-expand reaches
   `187/400` BOTH at `64,338.065` mean context chars; oracle-selective reaches
   `187/400` at `37,292.0075`. This establishes only target-defined coverage and
   context-cost headroom. It does not establish downstream action gain or total
   cost saving, and the 357 rows without target gain may contain other useful
   information.

4. **G2 state recovery and action use were conflated.** Plain bundle facts/actions
   are `2/8` and `1/8`; evidence-decision bundle facts/actions are `3/8` and
   `1/8`. Some generated bundles lose positive current facts, so the result
   cannot show that a correct sufficient state is ignored. Current synthesis
   separates old-state invalidation, sufficient current-state recovery, and
   downstream use.

5. **G2 independent-review counts were wrong.** The case-level validated JSON
   gives plain action `1 grounded / 6 reasonable / 1 unnecessary refusal` and
   decision action `1 / 5 / 2`, not `1 + 7 reasonable` for both arms. Both
   `09949c3c` action rows remain unnecessary refusals. The old review remains
   an auxiliary AI review with its own stale hash; current summaries use the
   case-level JSON.

6. **Retrieval and provenance limits were clarified.** G2 BM25 removes stopwords
   and short tokens; G3 retains them and indexes session/time and role prefixes,
   so `0.430` versus `0.4675` BOTH coverage is not a method comparison. G3 call
   1 raw is lost and its usage is supported only by a mutable GB10 server log;
   call 2 raw hashes match the aggregate but its receipt is not self-describing.
   This is an engineering/provenance gap and `UNEVALUATED_NO_VALID_DECISION`,
   not a model-policy accuracy result.

## 2. Reusable Assets

The most valuable assets for the next stage are:

1. `STALE_400_DEV` plus `G2_MEASUREMENT_CONTRACT` and
   `G2_FIXED_STATE_RUN`: same evidence, fixed actor, semantic categories and
   current raws. Saves construction of a new state benchmark.
2. `G3_EVIDENCE_RUNNER` and `G3_EVIDENCE_RESULTS`: deterministic 400-row
   KEEP/EXPAND replay and cost accounting. Saves a new retrieval harness.
3. `ADAPTIVE_V3_ENV`: transparent policy replay, fixed repairer and cost curve.
   Saves a new mechanism environment.
4. `PARTRIDGE_REPLAY` and `NTRIP_MIGRATION_CASE`: real source, tests and oracle
   boundaries. Saves software-change task construction.
5. `MACERD-PUBLIC-ZIP`: authoritative public task/evaluator source, SHA-256
   `f0373675...ab62c`. Saves a future condition/evidence task; use the ZIP, not
   the drifted extracted tree.
6. `LORA_SMOKE_CHAIN` plus Qwen3-4B/8B and PEFT/TRL: verified GB10 training
   plumbing. Saves environment setup, not scientific labels.
7. `PAPER_E_CANONICAL`, `PAPER_E_CLAIM_MATRIX` and `PAPER_E_ARTIFACT`: mature
   two-case manuscript, claim chain and offline reproduction. Saves Paper E
   reconstruction.
8. `Q3-VALENTINE_LABELS`, `VGMC_RULE_CORPUS` and `DPO_V0`: failure constraints
   and supervision-gate design. They are evidence/lessons only, not gold.

Asset qualifications: STALE's data license and unseen split are unresolved;
MA-CERD's extracted `release/` has four documentation hash drifts and fails
`validate_release.py`; VersiCode has inconsistent license declarations and no
safe behavioral oracle; PyMigBench has `FROZEN_ZERO_TASKS` after 36 candidates;
the local VGMC corpus is missing. None of these blocks Card 1/2 development,
but each blocks the corresponding external, training or benchmark claim.

## 3. What Remains Stopped And What Is Worth Exploring

Stopped without a general negative claim:

- FinRank H/K on the current panel;
- the old G2 consumption/migration verifier as a method extension;
- the old complex G3 planner;
- the scope panel as a novel scope-aware method;
- the exhausted CodeUpdateArena prose-update arm;
- direct reuse of Q3/VGMC/DPO labels as training gold.

Worth exploring:

- `RQ-U`: information-matched state sufficiency and downstream action use;
- `RQ-A`: effective evidence expansion with same-budget random and strong
  cheap controls;
- `ALT-L`: a new CodeUpdateArena-style or public document-state task with
  executable supervision, only after source/license/split qualification.

The old failures are useful design constraints: fixed `No`/`UNKNOWN` is not
completion, stale detection is not state recovery, tool calls are not result
consumption, safety can be mere abstention, rows are not independent samples,
oracle is diagnostic, and an interface failure is not a scientific negative.

## 4. Three Experiment Cards

| Card | Readiness | First entry | What it can decide |
|---|---|---|---|
| 1. State information-loss localization | `READY_FOR_DEVELOPMENT_START`; unseen confirmation split missing | `venv\Scripts\python.exe -m pytest -q ...test_g2_fixed_state_transfer_probe_v5.py ...test_g2_evaluation_contract.py` | Whether failure is old-state invalidation, missing sufficient current facts, or downstream action use |
| 2. Effective evidence expansion and total cost | Offline ready; model leg needs a valid KEEP/EXPAND contract | GB10 `G3_incremental_evidence_probe.py offline --data ... --protocol ...` | Whether a non-oracle policy beats same-budget random and cheap rules at matched total cost |
| 3. Small-model learning alternative | Data qualification/dry-run only; training not startable | `venv\Scripts\python.exe research/validate_stage_d_training_readiness.py --help`; task-specific config is a later prerequisite | Whether independently checked conditional supervision adds executable task value over no-training/generic/filtering |

Cards 1 and 2 may start bounded development work. Card 3 may start source/task
qualification and a dry-run only. No card is a completed experiment.

## 5. Recommended Research Order

**Main attack:** Card 1. It resolves the most consequential current
interpretation failure and does not require a new Memory architecture.

**Independent candidate:** Card 2. Keep it separate from Card 1 because the
decision is whether to acquire evidence, not how to use a recovered state.

**Learning fallback:** Card 3 only after a new task has an executable checker,
independent source-family split, license record and real headroom. A small
LoRA/SFT run before those conditions would only test plumbing.

Paper E continues in parallel from the existing handoff. If Card 1 reduces to a
retrieval effect and Card 2 has no downstream gain, merge the negative evidence
into the RQ-U/RQ-A boundary and select a new task rather than splitting one
pipeline into two thesis contributions.

## 6. Paper, Ledger, Git And Open Items

- **Paper E:** two-case `NARROW_AND_CONTINUE`; canonical manuscript and private
  artifact are internally reproducible. ICAART/PRIMORIS submission has not been
  performed. Owner-only items remain author identity/affiliation, AI disclosure
  approval, patent status, artifact/DOI release, submission/payment,
  presentation/travel and school recognition.
- **Resource ledger:** current Goal remains `536` accounting attempts,
  `536` physical HTTP calls, `3,713,363` accounting tokens, `113` judge calls;
  training, paid API and production Memory writes are zero. This governance
  task made zero model/judge/training calls.
- **Evidence identity:** the B deterministic recompute is offline derivation;
  the A asset audit and C scientific reconciliation are AI advisory analysis,
  not human gold or blind review. Frozen raws, protocols, reports and old
  scores were not rewritten.
- **Git:** local, `origin/main` and GB10 were all `9e43b0380588adc5b4b5b6c14481ae636349cb96`
  at check time. This task changed only current governance/summary files and
  worknotes; no `git add .`, reset, clean, push or production operation was
  performed.
- **Checks:** focused G2/G3 tests `24 passed, 2 skipped`; Paper E
  `verify_claim_evidence.py` PASS; `scripts/docs_lint.py` `0 fail / 0 warn`;
  JSON parsing PASS; `git diff --check` reported line-ending warnings only.
  Full repository tests were not run because no executable source changed.
- **Local gaps:** STALE license/unseen split, G2 source path/hash declaration,
  G3 call-1 raw/durable usage receipt, MA-CERD ZIP-versus-extracted-tree
  integrity choice, VersiCode license/oracle, PyMigBench zero retained tasks and
  missing VGMC corpus. Each is scoped to one route and does not block the
  complete baseline.

## Final Rulings

科研基线: READY_WITH_LOCAL_GAPS

后续方法贡献: NOT_ESTABLISHED

