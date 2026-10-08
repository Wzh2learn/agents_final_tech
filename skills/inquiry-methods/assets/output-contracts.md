# Common Output Contracts

Apply this contract to every inquiry method.

## Evidence Labels

| Label | Meaning |
|---|---|
| `FACT` | Directly supported by a cited or mechanically verified artifact |
| `INFERENCE` | Derived from facts; include the reasoning chain |
| `VALUE` | Priority, preference, or normative judgment |
| `UNVERIFIED` | Plausible but lacks adequate evidence |
| `CONTESTED` | Sources or experts materially disagree |

For external fact checks, use `CONFIRMED`, `NEEDS_NARROWING`, `CONTESTED`, `INSUFFICIENT_EVIDENCE`, and `WRONG`.

## Required Sections

1. **Mode:** selected inquiry method and object.
2. **Boundary:** sources read, checks run, checks not run, and protected exclusions.
3. **Findings:** facts, inferences, value judgments, and unverified assumptions kept separate.
4. **Recommendation:** one sequenced recommendation rather than an unranked option list.
5. **Conditions:** where the recommendation applies and where it fails.
6. **Risks and exit:** largest risk, stop condition, and unresolved disagreement.
7. **First action:** the smallest next step that can be independently verified.

## Traceability

Use `path:line`, artifact hash, source title, source date, or command output identifier for important claims. Fresh recomputation must be labelled `this re-verification` and must not impersonate a pre-existing project conclusion.

## Completion Boundary

Distinguish these states:

- inquiry completed;
- review judgment produced;
- human decision recorded;
- execution authorized;
- experiment executed;
- result accepted.

A completed prompt is not a decision, and a decision is not an execution result.
