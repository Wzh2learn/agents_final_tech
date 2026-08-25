# Design Document Template — Implementation-Ready Spec

> The bridge between "research-driven-design output" and "Code Agent implementation".
> This is what the Code Agent receives: precise enough to implement without guessing,
> constrained enough that review is mechanical (does it match the spec?).

## When to produce this

- After `research-driven-design` skill outputs a direction
- After `sprint-contract` defines "done"
- Before Code Agent writes the first line of implementation code
- For any feature that touches model architecture or training pipeline

## Template

```markdown
# Design: [Feature Name] (date)

> Upstream: [Goal Card / Sprint Contract that authorized this]
> Status: 📋 Draft / ✅ Approved for implementation / ⏸️ Shelved (with reason)

## 1. Objective & Constraints

**Objective**: [One sentence — what this adds to the system]

**Hard constraints** (non-negotiable, from Goal Card §二):
| Constraint | Implication for this design |
|-----------|---------------------------|
| [Constraint 1] | [What it rules out] |
| [Constraint 2] | [What it forces] |

## 2. Code-Verified Insertion Point

> Don't design in the abstract. Read the actual code and cite the exact lines.

**Current code paths** (verified by reading src/):
- **Training path**: `src/model.py:L483` — `[exact current code]`
- **Inference path**: `src/model.py:L1526` — `[exact current code]`

**Symmetry requirement**: [Training and inference paths must be symmetric / differ in X way]

## 3. Implementation Specification

```python
# === Shared function (both paths use this) ===
def _new_module(self, x):
    """[Docstring: what it does, input/output shapes]"""
    # [Implementation with shape annotations]
    return result  # (B, ..., D)

# === Training path modification ===
# Before: [exact line being modified]
# After:
[new code]

# === Inference path modification ===
# Before: [exact line being modified]  
# After:
[new code]
```

**Why shared function**: [prevent drift between train/inference — cite the anti-pattern]

## 4. Key Design Decisions (each with rationale)

| Decision | Choice | Alternatives considered | Rationale |
|----------|--------|------------------------|-----------|
| [Decision 1] | [What we chose] | [What we didn't] | [Why — evidence-based] |
| [Decision 2] | ... | ... | ... |

## 5. Parameters & Configuration

| Parameter | Default | Range | Env var | Notes |
|-----------|---------|-------|---------|-------|
| [param_1] | [value] | [min-max] | `FEATURE_PARAM_1` | [Why this default] |

**Feature gate**: `ENV_VAR=1` (default OFF — zero-change path must be bit-identical to current)

## 6. Pre-registered Judgment

| Criterion | Threshold | Measurement method |
|-----------|-----------|-------------------|
| Success | [metric > X] | [Exact eval command] |
| Quality floor | [metric > Y] | [Same eval, lower bar] |
| Kill condition | [metric < Z OR divergence] | [Early stopping signal] |

**Prediction if hypothesis correct**: [Expected metric value — written BEFORE experiment]

## 7. Test & Verification Plan

- [ ] Unit test: feature gate OFF → output bit-identical to current version
- [ ] Unit test: feature gate ON → output shape correct, gradients flow
- [ ] Smoke test: 100-step training, loss decreases, no NaN
- [ ] Full eval: run pre-registered judgment criteria
- [ ] DDP safety: multi-GPU produces same result as single-GPU

## 8. Rollback & Exit

- **Rollback**: set `ENV_VAR=0` → immediate revert, zero code change needed
- **Shelve condition**: if pre-registered kill condition hits, shelve design (don't delete)
- **Supersede note**: if shelved, record WHY in §8 of Goal Card
```

## Design Principles

1. **Code-verified, not imagined** — every insertion point cites actual file:line
2. **Feature-gated by default** — new features default OFF, existing path unchanged
3. **Train/inference symmetric** — shared function prevents drift
4. **Pre-registered judgment** — write success criteria BEFORE seeing results
5. **Reviewable mechanically** — reviewer checks "does implementation match spec?"
6. **Reversible** — env var toggle, no code surgery to revert

## Anti-patterns

- **"Just implement it and see"** — skipping the spec leads to scope creep and unverifiable code
- **Design without reading code** — "add a module after the encoder" without citing the exact line
- **No feature gate** — makes rollback require a revert commit instead of an env change
- **Asymmetric train/inference** — most production bugs come from these paths diverging
- **No kill condition** — zombie features that "might work with more tuning" never get killed
