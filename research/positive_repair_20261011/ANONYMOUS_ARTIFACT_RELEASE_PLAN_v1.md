# Anonymous Artifact Release Plan v1

> date: 2026-10-11 | status: DRAFT (do NOT publish before the venue/author owner decision) | purpose: minimal contents for the anonymized artifact referenced by the Data Availability statement.

## Release trigger (all required)
- Owner finalizes the venue decision (SANER RENE default) and the author list (H1).
- The anonymized repository is created and tested by a second person for de-anonymization (per SANER double-anonymous guidance).
- No proprietary/client data is included.

## Minimal contents (to reproduce the reported numbers)
1. Frozen data/results carriers: the drift-v0 input table set and injection map (`data/research/drift_v0/input/tatqa_tables.json`, `.../output/injection_map.json`) with the sha256 values pinned in the manuscript.
2. Checkpoint config: `config/eval_checkpoint_trees.json` (v0.1.0).
3. Scripts needed to reproduce reported numbers: the header matcher (`scripts/m1_statement_parser.py`), the aggregator (`scripts/eval_checkpoint_aggregate.py`), the drift injector (`scripts/research/drift_inject.py`), the K2 visibility computation (`research/k2_table_discrimination_v2.py`), the cross-matcher audit (`research/paper_d2_cross_matcher_det.py`), and the multi-leaf runner (`research/stage_e_multileaf_20261010/run_multileaf_formal.py`).
4. Configs and seeds: injection seed 42 / ratio 0.3; bootstrap seed 20260830; the threshold grid and fold rule as reported.
5. Environment requirements: Python 3.9+, stdlib only for the deterministic scripts; the semantic judge is a third-party model (Qwen3.6-35B-A3B Q4_K_M GGUF) cited rather than redistributed.
6. README: how to run each script, expected outputs, and the mapping from script output to each manuscript table/figure number.
7. Figure-generation scripts: `docs/research/figures_saner/render_saner_figures.py` and the figure source-binding manifest.

## Excluded
- The FinQA second dataflow is described by its frozen activation record; its execution is reproducible from the released scripts but the outcome is a boundary record, not a capability result.
- Any file that would reveal authorship, institutions, host names, or absolute paths.

## Not authorized yet
No public or private artifact release, and no hosted DOI, until the owner confirms the venue and authorship. The Data Availability statement in the manuscript points to an anonymized repository placeholder to be filled at submission time.
## External dependencies (not redistributable)
- Semantic judge: Qwen3.6-35B-A3B (Q4_K_M GGUF) served at 127.0.0.1:8004. Third-party weights; cite and document the access path, do NOT redistribute. Reproduction of the semantic-leaf scoring requires the reader to obtain the same model.
- TeX toolchain: not vendored. See paper/overleaf_bundle/BUILD_README.md ("Toolchain bootstrap") for the exact tectonic release and sha256, or compile on Overleaf.
- Python: the deterministic scripts are stdlib-only (plus numpy for the multi-leaf analysis); the judge path needs a model server.
- GB10 is the authoritative run host. There is currently no second-host verification path for the frozen carriers; a mirror + a second-host recompute is the recommended future hardening.
