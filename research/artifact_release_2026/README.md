# Anonymous Artifact Package 2026 (PREPARED, NOT RELEASED)

> status: `PREPARED_NOT_RELEASED` | date: 2026-10-13 | owner decision required before any publication
> authority: `research/positive_repair_20261011/ANONYMOUS_ARTIFACT_RELEASE_PLAN_v1.md`

## What this is
The staged, anonymised artifact for the SANER RENE submission: the frozen configuration, the deterministic analysis
scripts, the two frozen result artefacts the paper's figures bind to, and the figure renderer. Data bodies are **not**
in the repository; they are added at release time from the authoritative host.

## Contents
- `MANIFEST.json` - per-file sha256 for everything staged locally, plus a `gb10_only` list.
- `build_artifact.sh` - runs on GB10: copies the staged files plus the two data bodies into `artifact_stage/`, writes a
  release manifest with fresh hashes, tars the directory, and prints the tarball sha256. It does **not** upload anything.

## What is staged locally (12 files, hashes in MANIFEST.json)
Configuration (`config/eval_checkpoint_trees.json`); the matcher, aggregator, drift injector and the two Stage-E analysis
scripts; the multi-leaf runner and its ablation analyser; the figure renderer; the multi-leaf ablation result JSON; and
the two frozen evaluation artefacts under `logs/graph/eval/`.

## Not staged (must be added on GB10 at release)
- `data/research/drift_v0/input/tatqa_tables.json` and `data/research/drift_v0/output/injection_map.json` - the frozen
  corpus carrier and injection map. They exist only on GB10. **Before release: confirm the licence scope of the public
  TAT-QA base and the injection map's derivation.**

## Release gate (all required)
1. Owner decides to publish and confirms the venue.
2. Licence scope signed for the data bodies.
3. The anonymised repository is created and tested by a second person for de-anonymisation.
4. The Data Availability statement's URL is updated to the real repository.
5. The manifest is regenerated from the released tarball and archived.

## What is deliberately absent
- No model weights. The semantic judge (Qwen3.6-35B-A3B Q4_K_M) is third-party and must be obtained by the reader.
- No intermediate runtime directories, no logs, no chat/agent transcripts.
- No author-identifying paths, host names or credentials; `build_artifact.sh` copies only the listed paths.