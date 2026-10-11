# PR-02 Feasibility Fact-Check v1 (read-only)

> date: 2026-10-11 | question: is "observation-placement distance decay" currently identifiable on authoritative evidence?
> verdict: **NOT_CURRENTLY_IDENTIFIED** (label also: INTERESTING_HYPOTHESIS). Do not construct a graph distance post-hoc and draw a decay curve.

## Five required conditions (owner-ordered) and findings
1. Authoritative dependency graph: **NO (only design-level)**. The causal-MVP design document contains a dependency subgraph, but it is a DESIGN artifact whose edges are partly `DESIGN_EDGE` and whose HIGH-severity aliasing was filed by audit; it is not frozen evidence and is not authoritative for distance semantics.
2. Checkpoint-to-stage distance: **NO definition exists**. No artifact defines a distance metric between a fault stage and a checkpoint (tree depth, execution order, or graph distance); none was preregistered.
3. Propagation edge records: **NO**. Frozen artifacts are leaf-level only (miner finding: paired artifacts carry baseline/injected leaf scores; no intermediate/pipeline state hashes). The MVP RIPR `raw_state_*` fields are `NOT_IDENTIFIABLE` throughout; `dependency_path_status = DEV_ONLY_DESIGN_PATH_PRESENT_NO_RAW_STATE_PROOF`. Therefore no propagation edge can be measured from existing data.
4. Meaningful non-direct state variation: **NO on current carriers**. On the 216-row multi-leaf surface, 8 of 12 leaf columns are identically zero, and the non-direct subset alone decodes at 0.3333 (chance) with tie rate 0.6667; there is no non-direct variation to trace decay over.
5. Headroom on current carriers: **NO** (same ceiling as the failed PR-06: full vector 1.0 = direct 3-leaf codebook 1.0).

## Consequence
PR-02 remains a hypothesis. A real test would require NEW instrumentation (intermediate state hashes / propagation records) and a preregistered distance definition - i.e., a different dataflow or a new namespace with new instrumentation, outside the current round. No execution authorized.