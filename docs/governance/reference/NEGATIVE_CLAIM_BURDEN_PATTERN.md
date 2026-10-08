# Negative Claim Burden — "Not Found" Is a Claim, Not an Observation

> "Zero references / unused / never existed / nothing matched" is a positive assertion about the
> *entire* search space, and it carries its own burden of proof. Before any destructive action
> rests on it — evidence it against full history, account for the detector's false-positive rate,
> and record the negative as an auditable artifact. An agent that deletes on a raw "not found" is
> acting on a claim it never proved.

## The Problem

Cleanup is where this bites: dead-code elimination, pruning "unused" dependencies or assets,
trimming a knowledge base. An agent runs a scan, sees `0 references`, and deletes. But *"I did
not find a reference"* is not *"there is no reference."* The gap between them is exactly where an
autonomous agent confidently removes something load-bearing.

**Reference shape (generalized).** A mechanical "zero-references ⇒ safe to delete" scan had a
high false-positive rate — a majority of its "unused" hits actually had references it hadn't
looked in the right place for. Separately, an auditor's *negative* conclusion ("this never
existed") was overturned simply by searching full history instead of the current snapshot.

## The rules

1. **A not-found is an assertion to prove, not a fact to act on.** Flip the burden: the scan
   produced a hypothesis ("nothing uses this"); deletion waits until the hypothesis is evidenced.
2. **Search full history, not the current snapshot.** All branches, all time, generated
   artifacts, evidence records. A reference can live in a branch you didn't check, a
   recently-deleted-but-recoverable state, or a file produced at runtime.
3. **Know the detector's false-positive rate.** A scan known to be noisy earns a second,
   independent confirmation before anything is removed — one noisy detector's "empty" is not
   evidence.
4. **Record the negative as an artifact.** `safe-set = empty, checked via <method> on <date>` is
   a health *proof* worth logging (`APPEND_ONLY_LEDGER.md`), so the next audit doesn't
   re-litigate it and a *wrong* empty-set becomes catchable after the fact.
5. **The destructive action is gated on the proven negative, never the raw scan.** Move-and-fix
   in the same commit if anything turns up (`GOVERNANCE_INVENTORY.md`).

## What this does NOT give you

- **This is about *negative* claims (absence).** Positive claims ("this works", "tests pass")
  have their own discipline — the completion gate in [[verify-before-done]]. Different burden,
  different evidence.
- **A proven-empty set is a legitimate, valuable result — don't over-correct into paranoia.**
  "Found nothing" after a *properly scoped* search is a real answer; the failure is treating a
  *narrow* or *noisy* not-found as a *global* one. Pair it with a positive control so you can
  tell "clean" from "the search matched nothing because it was pointed at the wrong place"
  (the empty-set / positive-control trap in `MECHANICAL_HEALTH_CHECKS.md`).

## Related

- `GOVERNANCE_INVENTORY.md` — two evidence pieces before archiving; move-and-fix in one commit
- `ASSET_INVENTORY.md` — three probes before an asset is declared dead
- `APPEND_ONLY_LEDGER.md` — record the negative finding so it isn't re-derived
- `MECHANICAL_HEALTH_CHECKS.md` — an empty result needs a positive control (the silent-green trap)
- [[verify-before-done]] — the positive-claim twin (prove "done", here you prove "absent")
- [[code-pathology]] · [[kill-dead-code]] — where "delete on not-found" is most tempting
