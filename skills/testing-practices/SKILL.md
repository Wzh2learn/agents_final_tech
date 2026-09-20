---
name: testing-practices
description: Write and judge tests that catch real bugs — reproduce the defect before fixing it, hunt the untested paths that matter instead of chasing coverage percent, test system boundaries by contract, and diagnose intermittently failing tests. Use when fixing a bug, adding tests, checking coverage, integrating two systems, or when CI is red intermittently.
when_to_use: fixing a bug, "make X work", a reported defect, '"improve coverage"', after writing tests, pre-merge quality check, an API endpoint, a service integration, a webhook, a shared schema, intermittent CI failure, "passes locally fails in CI", a flaky test
---

# Testing Practices

Four disciplines, one standard: a test earns its place by being able to fail for a real reason.
Chase that, not the coverage number.

## 1. Reproduce first (fixing a bug)

The only proof you fixed a bug is a test that failed before and passes after.

1. Write the smallest test that reproduces the reported behavior.
2. Run it. **Watch it fail** for the right reason (read the assertion, not just red).
3. Only then fix the code, and re-run to watch it pass.

If the test passes before your fix, you have not reproduced the bug — keep narrowing until it fails.

## 2. Hunt the gaps that matter (coverage)

Coverage % is a vanity metric. Hunt the gaps that bite:

- **Error paths** — the 500, the timeout, the empty/null input, the malformed payload. Almost always untested.
- **Boundaries** — 0, 1, max, off-by-one, empty collection.
- **Branches** — every `if/else` and `catch` exercised, not just the happy line.
- **Concurrency / order** — anything stateful tested in isolation AND in sequence.

Skip tests that assert a constructor sets a property — worthless. Test behavior, not implementation.
Output: the 3-5 highest-risk untested paths, ranked by blast radius, with the test to add.

## 3. Test the contract, not the implementation (integrations)

Test what the two sides AGREED on, so either can change internals without breaking the other.

- Assert the **shape**: required fields, types, status codes, error format — not internal logic.
- Cover the contract's edges: missing optional fields, the documented error responses, pagination bounds, versioning.
- A contract test that breaks when a private helper is renamed is testing the wrong thing.

## 4. Diagnose intermittent failures

Run the suspect test 20x in a loop first — confirm it's actually flaky, not just broken.

Common causes, in order of likelihood:
1. **Time/order** — depends on test execution order or shared mutable state. Isolate it; run alone.
2. **Async race** — asserting before a promise/refetch resolves. Await the actual condition, not a sleep.
3. **Real network/clock/random** — mock them. Freeze time, seed RNG, stub the call.
4. **Resource leak** — a prior test left a connection/file/port open.

Fix the cause, not the symptom. `retry(3)` on a flaky test hides a real race that will bite in production.
Quarantine only as a last resort, with a ticket.

## Completion

State which discipline applied, and produce: for a bug fix, the failing-then-passing test and both run
outputs; for a coverage pass, the ranked gap list; for an integration, the asserted contract fields; for
a flaky test, the reproduction loop result and the identified cause.
