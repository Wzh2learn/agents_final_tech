# Paper E Version-B Core Figure Specification v1

> Status: `FIGURE_SPEC_LOOP_C_REPAIRED` | Paper body not edited | Figure 3 generated only from frozen ablation values

## Figure 1. Measurement chain motivation

**Purpose:** motivate why long-horizon AI evaluation needs observability before detection and harm claims.

**Flow:**

```text
NIST / long-horizon service motivation
-> failure occurs in a staged pipeline
-> checkpoint visibility: did any instrument observe the failure?
-> protocol detection: did the decision rule use that observation?
-> outcome / harm: what consequence is asserted under a stated contract?
```

**Design requirements:**

- five horizontal stages with directional arrows;
- no decorative illustration; each node must name a measurement construct;
- distinguish `visibility`, `detection`, and `harm` by shape or border, not by unsupported color semantics;
- caption must state that NIST motivates measurement effectiveness, not this paper's blind-spot framework.

## Figure 2. Defect family × checkpoint visibility

**Purpose:** show the frozen Stage E observation boundary.

**Data source:** `logs/graph/eval/t2_visibility_sensitivity.json` and the frozen `checkpoint_discrimination_tables_v2.json`.

**Encoding:**

- rows: six defect families;
- columns: thresholds `0.2, 0.3, 0.5, 0.7, 0.9`;
- cell: visibility rate at that threshold;
- annotation: injection count and, where relevant, invisible/absorbed count;
- separate textual note: `0/13 OCR-like injections were visible across 11 table clusters`.

**Caption boundary:** this is a visibility matrix, not a harmfulness matrix.

## Figure 3. Multi-leaf localization and ablation

**Purpose:** show both the controlled positive result and its main boundary.

**Two panels:**

| Panel | Metric | Full vector | Direct codebook | Non-direct leaves | Baseline |
|---|---|---:|---:|---:|---:|
| A | Macro-F1 | 1.0000 | 1.0000 | 0.3333 | majority macro-F1 0.1667 |
| B | Top-1 | 1.0000 | 1.0000 | 0.3333 | chance top-1 0.3333 |

**Metric-specific identities:** non-direct top-1 `0.3333` equals chance top-1 `0.3333`; non-direct macro-F1 `0.3333` equals uniform-class macro-F1 `0.3333` but is above the plotted majority macro-F1 baseline `0.1667`. The perfect full-vector and direct-codebook bars are construct-sensitive on the explicitly instrumented controlled M/R/N surface.

**Required caption:**

> Perfect full-vector and direct-codebook bars are construct-sensitive on the explicitly instrumented controlled M/R/N observation surface. After directly targeted checkpoints are removed, non-direct top-1 equals chance (`0.3333`); non-direct macro-F1 equals the uniform-class macro-F1 baseline (`0.3333`) but remains above the plotted majority macro-F1 baseline (`0.1667`). The result reflects stage-aligned instrumentation, not emergent localization from the remaining hierarchy.

**Forbidden caption language:** `hierarchy localizes failures`, `natural failures are localized`, or `distributed downstream evidence is sufficient`.

Repaired candidate: `docs/research/figures_multileaf/fig_multileaf_localization_ablation.{png,svg}`.

## Scientific implication

Visibility requires appropriate instrumentation; hierarchy alone does not imply localization.
