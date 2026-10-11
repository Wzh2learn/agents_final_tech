[loop-c] start 2026-10-09T18:07:46Z
Evidence gathering complete. I modified nothing, called no endpoints, and ran no training — only read-only inspection plus local SHA-256. Report follows.

---

# Loop C Independent Audit — PRM800K Reference Training Smoke v1

## Independence declaration

**Nature of this document:** advisory audit report only. I did not repair, backfill, or edit any audited object. **Audited object:** `docs/research/prm_reference_training_smoke_v1.md`, `research/prm_reference_training_smoke_20261010/`, `research/prm_reference_training_smoke_20261010_failed_triton_python_h/`, `research/stage_e_method_revision_20261009/run_prm_reference_training_smoke.py`, `docs/research/prm_c2_c4_selection_dryrun_v1.md`. **Baseline:** none supplied — this is a first-pass audit, so every finding below is "needs filing", none is a re-report of a known case.

**Self-audit identity:** I did not author any audited artifact; I was invoked as the independent Loop C auditor. No self-audit softening applies.

**Anti-anchoring disclosure (clause 1):** I ingested the author's conclusions *before* recomputing — `prm_reference_training_smoke_v1.md:74` (`VALUE`) and `:85-91` (`NOT ESTABLISHED`) were read first, because the assignment listed that file first. Mitigation, executable rather than promised: the quantitative core of this report was derived independently from primary carriers the author's text does **not** contain — `smoke_config.json` `row_hashes`, and `C2|C4/checkpoint-2/trainer_state.json` `log_history`. Those sources produced findings F1 and F6 that the author's framing never supplied, and they cut against the artifact's own table. My reasoning chain on chain-status recomputation was formed from file existence and hashes before I read §4.

**Probe count:** zero model calls, zero canaries, zero judges, zero new runs, zero network. Read-only SHA-256 was computed on 7 in-repo files. SHA-256 of `/home/testuser/wzh/models/hf/Qwen3-4B/*` was **blocked by sandbox policy** (outside the allowed working directory) — see F3.

## Evidence table

| # | Claim under test | Primary carrier | Recomputed result |
|---|---|---|---|
| E1 | Non-paper / non-formal framing | `prm_reference_training_smoke_v1.md:3,10-13`; `smoke_config.json:10,61`; `smoke_metrics.json:56-57` | **HOLDS.** `formal_training:false`, `paper_result:false`, status strings `…_NOT_PAPER_RESULT` / `PIPELINE_CLOSED`. Boundary block is explicit and triple-encoded. |
| E2 | No claim compares C2/C4 performance | `grep -rniE "outperform\|superiority\|non-inferior\|C4 (beats\|improves)"` across smoke doc, dry-run, `paper/claim_manifest_v1.json`, `memory/STATE.md`, `memory/THREADS.md` | **HOLDS.** Only hits are negative: `:74` "cannot support C2/C4 superiority or non-inferiority", `:87` listed under `NOT ESTABLISHED`, dry-run `:52` "does not … establish C4 superiority". STATE/THREADS hits are unrelated A2/B4 criteria. |
| E3 | Train/eval problem groups disjoint | `smoke_config.json:4-9,63-72` | **HOLDS.** 8 train vs 4 eval, intersection empty, no intra-list duplicates. |
| E4 | Train/eval *rows* disjoint | `smoke_config.json:20-53` | **HOLDS.** `C2_train∩C2_eval = ∅`, `C4_train∩C4_eval = ∅`, and no cross-arm train→eval overlap. |
| E5 | Data identity sufficient | `smoke_config.json:3` vs `sha256sum research/stage_e_method_revision_20261009/sources/prm800k/phase2_test.jsonl` | **HOLDS.** `6b172efa884ac8341a946dd82e06947c135b7254109fb3f7aa907c715d98aaad` — exact match to config and to the doc's `6b172efa…aaad`. |
| E6 | Config hash binds the receipt | `smoke_metrics.json:55` vs `sha256sum …/smoke_config.json` | **HOLDS.** `7db152e87209126c9dc681ce6dd8cfb9246b6b64ead8d28c93d021566a9165b5` — exact match. |
| E7 | Only the environment was repaired | `sha256sum` both `smoke_config.json` (failed vs successful) | **HOLDS for config.** Both `7db152e8…` — byte-identical. Sample/label/step/lr/eval rule provably unchanged. See F4 for the code side. |
| E8 | Failed attempt preserved | `ls -laR research/prm_reference_training_smoke_20261010_failed_triton_python_h/` | **PARTIAL.** Preserved: `smoke_config.json` + **empty** `C2/`. Absent: any stderr/traceback. Structural proof of "died before training": no `smoke_metrics.json` (writer runs at `run_prm_reference_training_smoke.py:349`), empty `C2/` after `arm_dir.mkdir` at `:153`, so death occurred inside `train_arm` before any save. |
| E9 | Chain status recomputes | metrics `:48-54` + file existence | **HOLDS, all five stages** — see F6 for how the writer derived them. |
| E10 | Counts / seed / steps / cap / hyperparameters match the doc | doc `:43-54` vs `smoke_config.json:54,73-92` and `trainer_state.json` | **HOLDS** for every parameter the doc states: seed `20261013`, steps `2`, batch `1`, cap `256`, r=`8`, alpha=`16`, `q_proj`/`v_proj`, 8/4 groups, `data_sha256` prefix+suffix. Losses `1.1002815663814545→1.100282`, `1.0986867249011993→1.098687`, `1.3998441696166992→1.399844`, `1.4015705585479736→1.401571`; runtimes `3.2427→3.24`, `1.1631→1.16`. See F5/F8 for what the doc omits. |
| E11 | No hidden extra epochs / steps | `trainer_state.json` both arms | **HOLDS.** `epoch:0.25` (= 2·1/8), `max_steps:2`, `num_train_epochs:1`, exactly 2 train log entries + 1 eval, `should_training_stop:true`, `is_hyper_param_search:false`. |
| E12 | No result-dependent tuning | `run_prm_reference_training_smoke.py:107-117,250-251` | **HOLDS.** Selection is hash-ordered + `(step_count, process_chars, row_hash)`; no loss enters. `TASK.mkdir(exist_ok=False)` + `RuntimeError` blocks silent re-run. |
| E13 | Checkpoint / eval output present | `ls` both arms | **HOLDS for checkpoints.** `checkpoint-2/` complete (adapter 11,815,504 B, `optimizer.pt`, `rng_state.pth`, `scheduler.pt`, `trainer_state.json`). `final_adapter/` = exactly the 7 files in `smoke_metrics.json:3-12,27-36`. Eval processed exactly 4 samples: `7.496 × 0.5336 = 4.0`, `12.287 × 0.3255 = 4.0`. See F7 for per-example gap. |
| E14 | Arms are genuinely distinct models | `sha256sum` adapters | **HOLDS.** C2 `63be6be2…` vs C4 `8c5f69f8…`; each equals its own `checkpoint-2` copy. |
| E15 | Doc registration | `docs/INDEX.md:185` | **HOLDS.** Both dry-run and smoke registered. |

### Chain recomputation (criterion 3)

| Stage | Metrics field | Independent basis | Verdict |
|---|---|---|---|
| dataset | `smoke_metrics.json:50` `"PASS"` | `data_sha256` matches recomputed hash; 8/4 rows present; `train_examples:8`=`len(train_problem_hashes)`, `eval_examples:4`=4 | **PASS** |
| selection | `:53` `"PASS"` | problem-hash intersection `∅`; row-hash train/eval intersection `∅` (E3, E4) | **PASS** |
| training | `:54` `"PASS"` | `arms.*.global_step:2` = `max_steps:2`; `trainer_state.json:7` `global_step:2`; 2 log entries each | **PASS** |
| checkpoint | `:49` `"PASS"` | `checkpoint-2/` and `final_adapter/` exist in both arms with non-empty `adapter_model.safetensors` | **PASS** |
| evaluation | `:51` `"PASS"` | `eval_loss` finite and bit-identical to `trainer_state.json` in-training eval | **PASS** |

`status: "PIPELINE_CLOSED"` (`:57`) recomputes: all arms `global_step==2`, `checkpoint_present`, `eval_loss` finite → closed. ✔

## Findings, by severity

### F1 — Medium-High · arms are near-identical treatments, undisclosed *(disclosure)*
`smoke_config.json:27-52` shows the two arms share **7 of 8** train row hashes and **2 of 4** eval row hashes byte-for-byte. Only index 1 of train (`6ea6fd64…` vs `92d42d5f…`) and indices 0–1 of eval differ. `C2/generation_smoke.json` and `C4/generation_smoke.json` are **byte-identical** (both `806eb89f…`). The doc says only "different selected solution texts" (`:74`) beside a side-by-side loss table. The quantified overlap is the single most load-bearing fact for reading that table and it is nowhere stated. *Violates:* receipt completeness for a document that publishes arm-wise numbers. *Fix:* state the overlap counts in §4.

### F2 — Medium · `matched_pairs_available` misstates capacity *(evidence fidelity)*
`run_prm_reference_training_smoke.py:109-125`: the collection loop `break`s once `len(pairs) >= TRAIN_PAIRS + EVAL_PAIRS` (12), then reports `"matched_pairs_available": len(pairs)`. So `smoke_config.json:57` `"matched_pairs_available": 12` is a **capped collector count**, not availability. The dry-run independently records **407** deterministically matched pairs (`prm_c2_c4_selection_dryrun_v1.md:34`). A receipt reader concludes 12 matched pairs exist in the corpus. Lines `114-117` are also a duplicated dead `break`. *Fix:* rename to `matched_pairs_collected`, or report 407 from the dry-run.

### F3 — Medium · receipt does not pin code or runtime environment *(reproducibility)*
`git ls-files` and `git log -- research/stage_e_method_revision_20261009/run_prm_reference_training_smoke.py` return **empty**; `git status --porcelain` shows `??` for the runner and both smoke directories. No `sha256` of the runner appears in config or metrics. Only `peft_version: 0.21.2` (`final_adapter/adapter_config.json:29`) is captured — no torch/transformers/trl versions, no device record. Consequently the doc's claim at `:82` that training "run end to end **on GB10**" is **unverifiable from any preserved artifact** (model-dir hashing was also sandbox-blocked, so `model_config_sha256` / `model_index_sha256` / `tokenizer_sha256` at `smoke_config.json:16-18,62` are recorded but not independently recomputable here). *Note:* not committing adapter weights is **correct** per the CLAUDE.md never-commit rule — the gap is specifically the code hash and a version/device receipt. *Fix:* add `runner_sha256` + a one-line environment stamp, or relabel the GB10 sentence as unverified-host.

### F4 — Medium · failed attempt preserved structurally, not textually *(failure provenance)*
The failed directory holds only `smoke_config.json` + empty `C2/` — **no stderr, no traceback**. The `Python.h` root cause and the CPATH repair are prose assertions at `prm_reference_training_smoke_v1.md:22-32`. What *is* proven: "failed before training" (E8 structure) and "config unchanged" (E7). What is *not* proven: that `Python.h` was the sole cause and the CPATH export the sole repair — the runner code is unpinned (F3), so a code change that left the config dict unchanged would be invisible. Mitigating corroboration: `docs/25_交付架构决策.md:83` independently records the same Triton/`Python.h` failure mode on this host for a different stack. *Fix:* preserve the traceback next to `smoke_config.json`, or mark §2's cause as prose-asserted.

### F5 — Medium · 8 "training examples" overstates what was trained on *(scope precision)*
`trainer_state.json:5` `epoch: 0.25` with 8 examples and `per_device_batch_size:1` proves only **2 of the 8** train rows were ever consumed by the 2 optimizer steps. Both arms consumed the *same* row positions (identical seed, and `log_history` step-1 losses are bit-identical). Doc `:63-74` places "Eight training examples" beside "two steps" without this. *Not false* — the dataset does hold 8 — but material. *Fix:* state "8-row train set, 2 rows consumed".

### F6 — Low-Medium · chain fields are literals, not checks *(evidence discipline)*
`run_prm_reference_training_smoke.py:342-344` writes `"dataset": "PASS"` and `"selection": "PASS"` unconditionally; `:241` defines `checkpoint_present` as `any(arm_dir.glob("checkpoint-*"))` — a directory-name test, not a content test. The underlying facts all hold (E3-E5, E13), so nothing is wrong *in the world*; but `smoke_metrics.json:50,53` are assertions by the writer, not evidence. *Fix:* derive them.

### F7 — Low · no per-example evaluation output
Only the scalar `eval_loss` is preserved. No per-row losses, so a reviewer cannot see that 2 of 4 eval rows are shared across arms (F1), nor which rows drive the held-out gap. The 2 `generation_smoke.json` rows are byte-identical across arms (F1), so that stage demonstrates pipeline continuity only.

### F8 — Low · hyperparameter record is a subset
`lora_dropout: 0.05` (`adapter_config.json:22`), `lr_scheduler_type="constant"`, `warmup_steps=0`, `gradient_accumulation_steps=1`, `completion_only_loss=False` (`run_prm_reference_training_smoke.py:174-185`) are absent from both `smoke_config.json.training` and the doc's §3 table. Recoverable from `training_args.bin` + `adapter_config.json`, so the receipt is recoverable rather than broken. Note `completion_only_loss=False` means loss covers prompt tokens, which are identical between arms within a group — further diluting arm differences.

## Strongest failure scenario

A downstream stage lifts `prm_reference_training_smoke_v1.md:71-72` — C2 train `1.100282` vs C4 `1.098687` — as a directional hint and uses "different selected solution texts" as assurance that the arms are distinct treatments. The arithmetic says otherwise:

- Step 1 is **bit-identical** across arms (`loss 0.7320161461830139`, `entropy 0.3352479934692383`, `mean_token_accuracy 0.8313725590705872`, `num_tokens 256`) — the consumed row at step 1 is shared.
- The only differing train row is at one index; both arms consumed it at step 2 (`1.468546986579895` vs `1.4653573036193848`).
- Therefore the reported train-loss gap `0.0015948414802552` is **exactly half of one step's loss difference on one differing example** — verified: `(1.468546986579895 − 1.4653573036193848)/2 = 0.0015948414802551`.
- The held-out gap has the **opposite sign** — C4 is *higher* (worse) by `0.0017263889312744` — over 4 rows of which 2 are shared, with `completion_only_loss=False` averaging in identical prompt tokens.

That is one example's arithmetic echo, not a signal about process supervision. A pilot-powering argument that imports `0.0016` as an effect size would be building on a number that is dominated by shared content and reverses direction under held-out evaluation.

## Verdict

**`VERDICT: CONDITIONAL`**

No claim in the audited set is false, and no red line is crossed: the smoke is explicitly non-paper and non-formal (E1), makes no C2/C4 performance claim (E2), has genuinely disjoint train/eval groups (E3, E4), recomputes to a closed chain (E9), matches its own document on every stated parameter (E10), shows no hidden epochs, no hyperparameter search, and no result-dependent tuning (E11, E12), and preserves the failed attempt with a byte-identical config (E7, E8). The loss values are correctly fenced at `:74` and `:85-91`. Zero findings would have been a defensible outcome on the claims themselves.

Conditional on the following, none of which requires retraining, a smoke-contract change, or any new run:

1. **F3** — add `runner_sha256` and an environment/version/device stamp, or relabel the GB10 sentence at `:82` as unverified-host.
2. **F2** — fix `selection.matched_pairs_available` semantics (407 per the dry-run, or rename the field).
3. **F1 + F5** — disclose arm overlap (7/8 train, 2/4 eval shared; generation outputs byte-identical) and that 2 of 8 train rows were consumed.
4. **F4** — preserve the failed run's traceback, or mark §2's root cause as prose-asserted.
5. **F6** — derive `chain.dataset` / `chain.selection` instead of hard-coding them.

**Strongest single blocker if the owner wants a harder line:** F1 — an arm-wise loss table published without its overlap counts is the one defect that can carry a reader from "engineering smoke" to "C4 trains slightly better". Every other finding is receipt hygiene. Per the advisory boundary I have filed these as recommendations only; adjudication is yours, and `memory/THREADS.md` is the ledger of record — I did not append to it.
