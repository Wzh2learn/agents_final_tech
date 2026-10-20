# Sprint Contract

Sprint: `CONDITION_CHANGE_FEEDBACK_V1`
Started: 2026-10-20, Asia/Shanghai

## Deliverable

Build and qualify one focused, deterministic expense-reimbursement sandbox in
which a local policy change can invalidate or preserve prior experience, and
compare three feedback contracts without sending model requests.

Evidence identity: `DEV_ONLY_CONTROLLED_MECHANISM`. The cases are realistic
operational simulations, not natural public observations or human gold.

## Acceptance Predicates

- [ ] The package contains a frozen versioned policy spec, actor/reference task
      separation, and at least 12 paired pre/post-change cases across at least
      four source clusters.
- [ ] The cases include at least three decision flips, three invariant pairs,
      two naturally alternate sufficient evidence sets, and two distinguishable
      out-of-scope additions.
- [ ] An independent reference builder computes decisions and minimal
      sufficient sets from the policy spec and evidence facts; it does not read
      model output or hand-coded per-case answers.
- [ ] Frozen fixtures prove that exact-match rejects a valid alternate set,
      sufficient-set-only retains an out-of-scope extra, and composite
      `sufficiency + scope precision + answer coverage` separates both cases.
- [ ] A deterministic baseline is run under the frozen inputs and is neither
      100% nor 0%; plan sufficiency and plan precision are reported separately
      at both pre- and post-change stages.
- [ ] `python3 -B -m unittest -v test_condition_change.py` passes and a
      machine receipt verifies input hashes, case counts, zero model requests,
      and the expected contract dispositions.

## Runtime Path

```text
python3 -B build_condition_change_inputs.py --freeze
python3 -B run_feedback_probe.py --freeze
python3 -B run_feedback_probe.py --run
python3 -B -m unittest -v test_condition_change.py
python3 -B verify_condition_change.py
```

All commands run from:

`research/research_direction_sprint_20261020_v1/execution_v2/condition_change_feedback_v1/`

## Frozen Scientific Questions

1. Does a feedback contract retain valid alternative sufficient evidence sets?
2. Does it reject or revise experience containing out-of-scope additions?
3. Does a local policy change require decision revision while unrelated
   changes preserve the prior decision?
4. Is there enough deterministic headroom to justify a later bounded real-model
   comparison?

## Out Of Scope

- Model, judge, training, service, network, or production Memory calls.
- Claiming a learning effect, public generalization, or human gold.
- Reusing the stopped FinRank H panel or rewriting frozen references.
- Building a generic evaluation framework or adding unrelated task domains.

## Stop Rules

- Stop if independent references cannot be derived without per-case hand-coded
  answers.
- Stop if the three feedback contracts do not separate the frozen positive and
  negative cases.
- Stop if the deterministic baseline is at ceiling or floor.
- Stop if policy-change pairs do not contain both invariant and revision
  opportunities.
- Do not start a real-model phase from this sprint automatically.
