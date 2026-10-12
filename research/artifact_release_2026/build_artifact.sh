#!/usr/bin/env bash
# Assemble the SANER anonymous artifact package ON GB10. Does NOT publish anything.
set -euo pipefail
REPO="${1:-$HOME/wzh/projects/agents_final_tech}"
STAGE="${2:-$HOME/artifact_release_2026_stage}"
rm -rf "$STAGE"; mkdir -p "$STAGE/files"
cd "$REPO"

copy() { # copy a repo-relative path into the staging tree, preserving structure
  local rel="$1"
  if [ ! -f "$rel" ]; then echo "MISSING: $rel" >&2; return 1; fi
  mkdir -p "$STAGE/files/$(dirname "$rel")"
  cp -p "$rel" "$STAGE/files/$rel"
}

for rel in \
  config/eval_checkpoint_trees.json \
  scripts/m1_statement_parser.py \
  scripts/eval_checkpoint_aggregate.py \
  scripts/research/drift_inject.py \
  research/k2_table_discrimination_v2.py \
  research/paper_d2_cross_matcher_det.py \
  research/stage_e_multileaf_20261010/run_multileaf_formal.py \
  research/stage_e_multileaf_20261010/analyze_multileaf_signature_ablation.py \
  docs/research/figures_saner/render_saner_figures.py \
  research/stage_e_multileaf_20261010/results/multileaf_signature_ablation.json \
  logs/graph/eval/checkpoint_discrimination_tables_v2.json \
  logs/graph/eval/t2_visibility_sensitivity.json \
  data/research/drift_v0/input/tatqa_tables.json \
  data/research/drift_v0/output/injection_map.json ; do
  copy "$rel"
done

( cd "$STAGE/files" && find . -type f -print0 | sort -z | xargs -0 sha256sum ) > "$STAGE/RELEASE_MANIFEST.sha256"
cp "$REPO/research/artifact_release_2026/README.md" "$STAGE/README.md"
tar -czf "$STAGE/../artifact_release_2026.tar.gz" -C "$STAGE" .
sha256sum "$STAGE/../artifact_release_2026.tar.gz"
echo "STAGED (not published): $STAGE ; tarball: $STAGE/../artifact_release_2026.tar.gz"