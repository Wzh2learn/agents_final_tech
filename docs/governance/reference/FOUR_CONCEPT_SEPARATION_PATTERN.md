# Four-Concept Separation — Agent Trust Governance

> The single most important pattern for preventing agent self-certification.
> "Fact / Completion / Judgment / Approval" are four different objects that must never
> be confused or substituted for each other.

## The Problem

In unstructured agent systems, four fundamentally different things get stored as the same
`done=true` or `status: completed`:

| What happened | What it means | What gets stored |
|--------------|--------------|-----------------|
| Script exited with code 0 | **Fact**: process terminated normally | `done=true` |
| All outputs exist on disk | **Completion**: artifacts were produced | `done=true` |
| Agent says "results look good" | **Judgment**: opinion about quality | `done=true` |
| Human says "ship it" | **Approval**: authorization to proceed | `done=true` |

When these collapse into one field, dangerous substitutions happen silently.

## The Four Concepts

### 1. Fact (EvidenceRef)
An observable event happened. A file exists. A process exited. A number was measured.
- Has timestamp, source, hash. Is append-only.
- **Key rule**: `exit_code = 0` is a fact. It does NOT mean PASS.

### 2. Completion (CheckResult)
A checker verified that required artifacts exist and meet structural criteria.
- Uses exactly 5 statuses: `PASS / FAIL / WARN / UNKNOWN / WAIT_HUMAN`
- No synonyms (not OK/SUCCESS/DONE/COMPLETED/NO_DATA/SKIPPED)
- Empty result / zero variance / stale source → always `UNKNOWN`
- `UNKNOWN` cannot promote to PASS downstream
- Security checks that can't parse → `UNKNOWN → WAIT_HUMAN` (fail-closed)

### 3. Judgment (JudgmentDraft)
An analysis and recommendation. "Based on the evidence, I think X."
- Has confidence level, weakest-link citation, suggested action
- **No approval field.** Cannot directly trigger a state transition.

### 4. Approval (ApprovalRecord)
A human (or authorized external system) says "proceed."
- Requires identity, timestamp, and digest of what was approved
- Marker-on-disk (`.done`, `.approved`) is NOT approval — it's self-certification
- Missing approval + timeout → `WAIT_HUMAN`, never "default to yes"
- "No one objected" != approved

## Real Failure Modes

| Incident pattern | Violation | What was impersonated |
|-----------------|-----------|----------------------|
| Agent claims "all done" but outputs are broken | Completion → Fact | Didn't check artifacts |
| Timeout, system picks default option | Completion → Approval | No human choice, state advanced |
| `.form_decided` marker exists → treated as approved | Fact → Approval | Marker != authorization |
| Agent recommendation propagated as decision | Judgment → Approval | Opinion treated as binding |
| `exit=0` on process that wrote garbage | Fact → Completion | "Ran" != "correct output" |

## Five-Status Enum (frozen, no synonyms)

```
PASS        — evidence proves criteria met
FAIL        — evidence proves criteria NOT met
WARN        — partially met, proceed with caution
UNKNOWN     — cannot determine (missing data, parse error, stale)
WAIT_HUMAN  — requires human decision, no default allowed
```

## Invariants (non-negotiable)

1. JudgmentDraft has no `decision`/`approved` field
2. ApprovalRecord requires `human:<name>` as approver
3. `UNKNOWN` never promotes to `PASS`
4. `exit_code=0` is a fact field, never a completion status
5. Missing approval + any timeout → `WAIT_HUMAN`, not default-proceed

## Applying Without a Formal System

Even without a ledger, apply immediately:

1. **HANDOFF files**: Separate "what ran" (fact) / "whether it worked" (completion) / "what I think" (judgment) / "what user decided" (approval)
2. **Experiment logs**: Don't write "experiment succeeded" — write: "exit 0" (fact) + "outputs correct shape" (completion) + "metrics positive" (judgment) + "user approved" (approval)
3. **Agent handoffs**: Cite evidence (fact), not opinion. "I believe it works" is judgment. "Tests 34/34 pass, exit 0" is fact + completion.
4. **Hook design**: Hooks check facts and completions. They never approve.
