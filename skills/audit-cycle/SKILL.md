---
name: audit-cycle
description: >-
  Standard audit cycle distilled from five real audits run in one week (external expert
  review / two independent responses / ledger replay / challenge audit): anchor the claims
  to be verified against a known baseline, admit first-hand evidence only, fully self-prove
  negative conclusions, file anomalies as pattern-named incidents, and stop at the advisory
  boundary. Trigger on "audit this", "double-check", "challenge", "fresh eyes", "what did we
  miss", before declaring a campaign closed, or after an external shock (expert report,
  incident, two authoritative numbers that disagree). Do not trigger for routine code review
  (use verify-before-done) or repo-wide governance sweeps (use repo-audit); audit-cycle is
  the evidence-discipline layer those call into.
when_to_use: audit, double-check, challenge, fresh eyes, "what did we miss", pre-closeout, after an external shock
compatibility: Requires filesystem and git read access. Produces advisory reports only — never modifies the audited artifacts.
metadata:
  version: "1.0.0"
  category: governance-audit
---

# Audit Cycle

Audit stops being improvised and becomes a fixed procedure. **Core stance: an audit reports,
it does not repair. Adjudication belongs to the human owner.**

## When to run

- Named request: "audit", "double-check", "challenge", "fresh eyes", "what did we miss".
- Before a closeout declaration goes out — to catch *claimed* closeout that is not actual closeout.
- After an external shock: an outside review lands, an incident is filed, two authoritative
  numbers contradict each other.
- Called into by another skill: `repo-audit`'s verification step, or `verify-before-done`
  when it needs evidence discipline behind it.

Do not run for routine code review (`verify-before-done`), whole-repo governance sweeps
(`repo-audit`), or the mechanical part of an integrity check — run the checker directly.
This skill is the evidence layer, not a re-implementation of machine checks.

## The five steps (order is not optional)

### 1. Anchor the claims — and fix a baseline first

Write the **claim list**: every "done / recorded / closed / the number is X" assertion in
scope. For each, note who asserted it, where it lives (file+line, or commit), and when.

Then fix the **baseline**: the list of already-known anomalies. A hit inside the baseline is
a known case; only a hit outside it is a new finding.

> **An audit without a baseline re-reports old cases as new findings, every time.** This is
> the single most common way an audit destroys its own credibility.

### 2. First-hand evidence only

Every claim must land on a primary carrier before you conclude anything. **Do not trust
restatements.**

| Claim about | Primary carrier |
|---|---|
| A file's content | Open the file, read that line, cite the line number |
| History | `git show <sha>` / `git log -S` — **the commit message is a claim, the diff is the fact** |
| An append-only record | Parse the log line by line; do not trust sidecars or projections (they go stale) |
| A number | Re-run it, or read the raw output file. "It was X last time" is not evidence |
| A project rule / legislation | The rulebook itself — grep it. **A commit message claiming "rule X was legislated" is not the rule.** Case: six artifacts cited a rule whose only existence was a commit message claiming it; grep of the carrier returned zero hits |

Before quoting any number, list, threshold, table name, **or rule**: grep the primary carrier first.

*Case:* a commit message claimed two records were entered; the diff contained one.

### 3. Fully self-prove negative conclusions

Before concluding "it doesn't exist / wasn't done / was missed", you must:

- Search the whole repo in **multiple forms**: full name, short name, aliases, fuzzy
  (search full name, short name, and known alias/substring forms) — to rule out "exists, in a
  different form". A fixed edit-distance threshold is a trap: an id and its prefixed variant can
  differ by many characters yet be the same entity.
- Confirm the search domain covered every possible carrier: other branches, the working
  tree, sibling directories.
- Put the search commands and their zero-hit output **into the report**.

> **The strength of a negative conclusion equals the completeness of the search.**

*Case:* a record's full identifier was `EV-<run>-0009`; searching the short form `EV-0009`
returned nothing and produced a false negative.

**Auditing a guard? Feed it a known-bad input and watch it go red.** A "clean" verdict from a
sentinel is worthless until you have seen that sentinel *fail* on purpose. Inject a positive
control — a poisoned input that must trip the guard — run it end-to-end, confirm the red, then
trust its green. The two silent-green shapes to hunt: an empty result set with no positive
control ("nothing matched" masquerading as "all clear"), and a baseline that slid past its
window so the anchor is permanently out of view. (Mechanized in `MECHANICAL_HEALTH_CHECKS.md`,
"Gate mechanics".)

### 4. Anomaly → filed as a pattern-named incident

Each confirmed anomaly gets a filing recommendation. **Fingerprint naming = object-anomaly
form**, e.g.:

- `commit-message-claims-unrecorded-entry`
- `placeholder-digest-and-future-timestamp`
- `commit-message-claims-uncommitted-workspace-file`

The fingerprint names the *pattern*, not the instance — so a recurrence with the same
fingerprint auto-groups into one family with an occurrence counter instead of spawning a
new case. The recommendation carries: severity / symptom / root cause / which premise it
violated / the fix.

The auditor only **recommends** filing. The act of recording belongs to the ledger flow
(append-only, so an auditor cannot forge an entry).

### 5. Respect the advisory boundary

Output is an advisory document: **report, do not repair.** Do not modify the audited object,
do not "fix it while I'm here", do not backfill history. Split findings into three dispositions
(already filed / needs new filing / waivable). Adjudication belongs to the human owner.

Fix three lines at the head of every report: nature of the document / audited object and
baseline / independence declaration.

## Anti-anchoring clauses

1. **When auditing an author's own work, verify the evidence independently before reading
   their conclusions.** Do not read the "conclusions / recommendations" section before forming
   your own — their framing will anchor you. (Data sections are fine.) If you ingest their
   conclusions by accident, disclose in the independence declaration exactly what you ingested
   and when, and state whether your reasoning chain had already formed.
2. **Cap audit recursion at depth=2.** An audit result may itself be audited once. Do not open
   a third layer. If depth=2 still disagrees: stop, lay out both sides' evidence, escalate to
   the human owner.
3. **Disclose self-audit identity — and make the mitigation executable.** If the auditor built
   any of the artifacts under audit, open with an independence declaration and back it with
   *actions*, not a promise: (a) each audit face gathers first-hand evidence via independent
   sub-agents running raw commands, not the author's summaries; (b) the reasoning chain is
   formed before the author's conclusions are read; (c) findings that point at the auditor's
   *own* work are recorded in full and not softened. "I checked my own work and it's fine" is
   the single least credible sentence an auditor can write; the mitigations are what make the
   rest of the report readable at all.

## Zero findings is a legal result

A challenge audit that overturns nothing has still done its job. **Confirming "no anomaly"
is a valid output — do not manufacture findings to justify the pass.**

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Report is all "new findings" but most are old cases | Step 1 skipped the baseline | Pull the known-anomaly list first; in-baseline hits get demoted to known |
| A negative conclusion is later overturned | Step 3 searched one form only | Re-search full name + short name + alias/substring forms; check whether you searched a short form and missed the full one |
| Conclusions look suspiciously like the audited party's narrative | Anti-anchoring clause 1 violated | Disclose the ingestion point; have an agent that has not read the conclusions re-verify the key evidence chain |
| Audit layers nest without end | No depth cap | Cap at depth=2; escalate disagreement |
| The auditor modified the audited object | Advisory boundary crossed | Restore the state; do the repair as a separately authorized change (append-only objects cannot be edited at all) |
| The "audit" is just the machine check re-run | Trigger mismatch | Run the checker directly; this skill is evidence discipline and interpretation, not a second copy of it |

## Related

- `verification/verify-before-done` — hostile review of a single diff; the completion contract this feeds
- `loop-engineering/repo-audit` — repo-wide governance sweep that calls into this
- `governance/patterns/GOVERNANCE_INVENTORY.md` — the three mismatch types this classifies into
- `governance/patterns/APPEND_ONLY_LEDGER.md` — why the auditor cannot forge an entry
- `governance/patterns/FOUR_CONCEPT_SEPARATION.md` — "executed successfully" and "result is recorded" are two different facts
