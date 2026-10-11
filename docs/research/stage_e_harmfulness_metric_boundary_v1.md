# Stage E Harmfulness Metric Boundary v1

> 状态: 活跃 | 更新: 2026-10-09 | 取代/被取代: 不修改 harmfulness definition；限定旧 operational anchor 的用途

## 1. Frozen construct

`FACT`: Stage E harmfulness remains an equivalence-dependent construct. Visibility, detection and harmfulness are separate objects.

`FACT`: old D1 classes are operational anchors: `H=85`, `HI=26`, `E=7`, with `H∪HI=111`.

## 2. What the old classes support

- `FACT`: describe anchor classification counts and mechanisms.
- `FACT`: use `111` as the old matched-FPR denominator after excluding the seven operational-equivalent cases.
- `FACT`: report `H=85` anchor-visible, `HI=26` anchor-invisible, `E=7` equivalent.
- `FACT`: descriptive absorption-based harmful/blind cell is `15/111`; anchor-invisible cell is `26/111`.

## 3. What they do not support

- `FORBIDDEN`: naming `15/111` or `26/111` as semantic `HBR_canonical` or `HBR_reader`.
- `FORBIDDEN`: importing H/HI/E into Stage D as a harmful-map.
- `FORBIDDEN`: adding or relabeling harmfulness cases to complete an indicator.
- `UNVERIFIED`: canonical-contract HBR and reader-referent HBR.

## 4. Identifiability condition

`VALUE`: calculate `HBR_canonical` only after a canonical equivalence contract and complete labels are frozen. Calculate `HBR_reader` only after the reader population, referent task, rubric, blinding and label set are frozen. Until then report `NOT_IDENTIFIED / INSUFFICIENT_LABELS`.

`VALUE`: operational-anchor harmful/blind analysis belongs in an appendix or diagnostics section, not the headline metric family.
