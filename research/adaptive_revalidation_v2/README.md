# Adaptive Revalidation Thin Environment

This directory contains a deterministic development-only environment for
bounded adaptive revalidation. It is mechanism evidence for candidates A and B,
not an external-task benchmark.

The checker graph has 12 executable nodes and 3 outputs. Policies issue exactly
the public tools `inspect_dependency`, `inspect_change`, and `run_target_test`.
The fixed repairer receives only an `EvidenceBundle` produced by a query policy.
The full-recompute baseline is a separate direct override and is labeled as such
in every receipt.

Run the focused tests from `agents_final_tech`:

```text
python -m pytest research/adaptive_revalidation_v2/tests -q
```

Run a deterministic replay:

```text
python -m research.adaptive_revalidation_v2 run
```

All fixture results are labeled `DEV_ONLY_AUTHORED_MECHANISM_FIXTURES`.
