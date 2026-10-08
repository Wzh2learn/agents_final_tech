# Governance Inventory — The Periodic Full-Domain Sweep

> Every few weeks, stop building and take inventory. Not "review the docs" — a structured
> triage that produces a decision for every asset and a named case for every mismatch.

## The Problem

Incremental work leaves incremental debt: docs that were current three weeks ago, commits whose
claims were never recorded, records claiming work that never happened. None of it is visible
from inside any single task.

A "review the docs" pass doesn't find it, because there's no forcing function — you read the
docs you already know about, confirm they look fine, and miss the structural mismatches.

## Part 1: Three Mismatch Types (the diagnostic frame)

Scan the last N commits (reference sweep: 90 commits over 3 days) and classify every mismatch
into exactly one of three types. The types matter because they have *different root causes*:

| Type | Definition | Root cause | Typical fix |
|------|-----------|-----------|------------|
| **A. Did-not-record** | The work happened; no record exists | Discipline gap at write time | Backfill the record; if recurring, add a gate |
| **B. Recorded-not-done** | A record claims work that didn't happen | **Message over-claiming** — most dangerous | Correct the record; find why the claim went unverified |
| **C. Doc-lagging** | Both happened, but the doc still describes the old state | Normal decay | Mechanical update |

Type B is the one to hunt. It's the only one that makes the record *actively misleading* —
A and C leave you under-informed, B leaves you confidently wrong.

Reference sweep found: 8 type-A, 3 type-B (new), 9 type-C. Each with severity (🔴/🟡/⚪) and
a named case ID so recurrence is trackable.

### The B-family discovery pattern

Type-B cases cluster into families. Reference example: a commit message claimed "6 corruption
instances fixed" but the fix script had failed silently mid-run — the message was written from
the *intent*, not the *result*. The family root cause: **a shell orchestration chain with no
exit gate**, so a failed step didn't stop the commit.

The family fix wasn't "write more accurate messages" — it was `python step || exit 1` in the
orchestration chain. Type-B cases almost always have a structural root cause.

## Part 2: Four-Bucket Document Triage

Every document goes in exactly one bucket. No "we'll decide later" bucket — that's how you
get 118 undecided files.

| Bucket | Criterion | Action |
|--------|----------|--------|
| 🟢 **Keep top-level** | Actively referenced, current, load-bearing | Nothing |
| 🟡 **Archive** | Superseded or stale — **requires two pieces of evidence** | Move to `archived/`, fix live references |
| 🟠 **Merge / absorb** | Content is valid but belongs inside another doc | Merge, leave a pointer |
| ⚪ **Already archived — recheck** | In `archived/` already; verify nothing live still points to it | Fix dangling references |

### The two-evidence rule for archiving

Never archive on vibes. Each 🟡 needs:
1. **Last-touch date** (`git log -1 --format=%ci -- <file>`)
2. **Live reference count** (`grep -rn "<filename>" --include="*.md" . | grep -v archived/`)

If reference count > 0, you must fix those references *in the same commit* as the move.
Otherwise you've traded a stale doc for a dangling link — a worse failure, because dangling
links break automated checks and stale docs merely mislead humans.

### The most dangerous cell

> **The index of the archive directory.**

When you move 28 files into `archived/`, the archive's own README index is the thing most
likely to be wrong afterward — and it's the thing a future reader trusts most, because it
*looks* authoritative. Verify it explicitly, last, after all moves are done.

## Part 2.5: Anti-bloat is three layers, and the cheapest is at creation time

A periodic sweep is the *last* line against asset bloat, not the only one. Bloat is fought at
three layers, cheapest first:

1. **At creation** — classify on the way in (see `AGENT_COLLABORATION_PROTOCOL.md` ch.8:
   every new doc gets a lifecycle layer, every new script names the live config it serves,
   every new test names its still-live anchor, all registered in the same commit). Thirty
   seconds at creation beats an hour of archaeology later.
2. **Observable trend** — a growth sentinel that only NOTEs (never blocks): plot asset counts
   over time so bloat is *visible* before it's a crisis. It reports, it does not gate.
3. **Comprehensibility audit** — the periodic human sweep below, whose real question is "can a
   newcomer still navigate this?": entry points reachable, structure layer un-rotted, archive
   rate healthy, orphan docs, navigation coverage.

If you find yourself running the Part-3 sweep to catch things layer 1 should have classified,
that is the signal to move the check upstream, not to sweep harder.

## Part 3: The Seven Faces (completion contract)

An inventory is complete only when every "face" of the project has an explicit status.
Don't allow implicit "probably fine".

| Face | Question | Evidence |
|------|----------|----------|
| **Code** | What's actually implemented? | Current branch, configs, tests |
| **Runtime** | What do users actually get? | Deploy markers, live endpoints |
| **Docs** | Is the human-facing answer current? | README, architecture, runbooks |
| **Rules** | Are agent constraints consistent and free of dead references? | CLAUDE.md/AGENTS.md, hooks |
| **Memory** | Is persisted memory still accurate? | Memory file review |
| **Workspace** | Any un-integrated residue? | Untracked files, stale branches, worktrees |
| **Evidence** | Do the evidence chains verify? | Ledger replay, audit findings vs. baseline |

Mark each: `verified-current` / `changed-and-verified` / `pending` / `out-of-scope` /
`not-applicable`. **`not-applicable` is a legitimate answer** — a project with no deployment
has no runtime face. Fabricating evidence for an inapplicable face is worse than declaring it.

## Part 4: Cross-Tool Staleness Check

If you run multiple AI tools (or mirrored config directories), each has its own hooks/skills
that drift independently:

```bash
# Hook inventory: registered vs. existing vs. executable
for h in $(jq -r '.hooks[][]?.hooks[]?.command' .claude/settings.json 2>/dev/null); do
  [ -f "$h" ] || echo "MISSING: $h"
  [ -x "$h" ] || echo "NOT EXECUTABLE: $h"
done

# Skill frontmatter validity (a skill with broken frontmatter silently never loads)
for s in .claude/skills/*/SKILL.md; do
  head -1 "$s" | grep -q '^---$' || echo "BAD FRONTMATTER: $s"
done

# Mirror drift between tool directories
diff -rq .claude/skills/ .other-tool/skills/ 2>&1 | head
```

Reference sweep found 5 stale hooks and 4 stale skills — including a skill whose frontmatter
had been broken for weeks (so it had never loaded, and nobody noticed because nothing errors
when a skill silently doesn't load).

## Part 5: The Report Format

```markdown
# Governance Inventory — YYYY-MM-DD

## §0 Seven-Face Status Table
| Face | Status | Evidence | Notes |
|------|--------|----------|-------|

## §1 Commit Mismatches (N commits scanned)
### A. Did-not-record (n; 🔴x / 🟡y / ⚪z)
| # | Commit | What happened | What's missing | Severity | Case ID |
### B. Recorded-not-done (n)
| # | Record | Claim | Reality | Root cause | Case ID |
### C. Doc-lagging (n)

## §2 Document Triage (N files)
### 🟢 Keep (n) / 🟡 Archive (n, with two-evidence each) / 🟠 Merge (n) / ⚪ Recheck (n)

## §3 Cross-Tool Staleness
### Hooks (n checked) / Skills (n checked)

## §4 New Findings This Sweep
[Things no prior sweep caught — these are the highest-value output]

## §5 Actions
| Action | Owner | Blocking? |
```

## Part 6: Discipline Rules

1. **Every asset gets a decision.** No "revisit later" bucket. If you genuinely can't decide,
   use a quarantine state with a ≤3-day TTL (see `KNOWLEDGE_REGISTRY.md`).

2. **Two evidence pieces before archiving.** Last-touch + reference count. Both, always.

3. **Move and fix in the same commit.** Never leave a dangling-reference window.

4. **Name every mismatch case.** A case ID (`B-4`, `B-5`, `B-6`) makes recurrence visible.
   Reference case: the same family recurring as B-4 → B-5 → B-6 is what triggered the
   structural fix. Without IDs, three incidents look like three unrelated slips.

5. **Report new findings separately.** The section listing what *no prior sweep caught* is
   the highest-value part of the report — it tells you where your checks are blind.

6. **Convert repeat findings to mechanical checks.** If a sweep finds the same class of issue
   twice, that class belongs in the doctor (see `MECHANICAL_HEALTH_CHECKS.md`), not in the
   next sweep's findings.

7. **A sweep report that will drive deletions must itself be audited before anyone acts on it.**
   The inventory's output becomes the *execution order* for a cleanup batch, so an error in the
   report amplifies into destructive action. Gate it with three checks before approval:
   - **No round-number claims.** "19 archive candidates" when only 17 are named invites the
     executor to pad the list to hit 19 — and the only things left to pad with are in-flight
     assets. Lock the execution scope to the *named list*, never to an aggregate count.
   - **No half-quoted verdicts.** A report citing a decision must quote its *retention clause*
     too, not just the conclusion that supports the proposed deletion.
   - **Internal counts must agree.** If the report states the domain size three times and the
     three disagree, the report is already stale — fix it before it drives anything.

8. **Register environment artifacts so a later sweep doesn't misread them as regressions.** A
   test that goes red because of the *environment* (a narrow terminal truncating `ps` output,
   a numpy/torch version) is not a regression — but the next auditor can't tell. Record such
   reds in a known-artifact baseline alongside the tool versions, so "red for an environment
   reason" is distinguishable from "red for a real reason." (The dual of "zero findings is a
   legal result": zero *real* regressions with environment-red still needs an explicit record,
   not a silent pass.) Record it **and** schedule the real fix — pin the test to logic not
   platform (mock the platform dependency, per `MECHANICAL_HEALTH_CHECKS.md` gate mechanics) —
   so the artifact registry does not quietly become a home for permanently-brittle tests.

9. **Every gate traces to a real incident — and run the reverse direction too.** No gate is
   invented from theory; each is paid for by a specific miss (in `MECHANICAL_HEALTH_CHECKS.md`
   nearly every rule cites the incident that bought it). Periodically walk the gates *backwards*: a gate
   nobody can tie to a real incident is either undocumented (find and record it) or theory-debt
   (challenge it — a gate that never caught anything real is noise that trains people to bypass
   gates); and a gate whose originating incident *can no longer occur* — the code path is gone,
   the platform changed — is a retirement candidate, under the same owner approval as any
   retirement (`SKILL_LIBRARY_GOVERNANCE.md`). Provenance runs both ways: an incident earns a
   gate, and a gate must keep earning its incident.

## Cadence

| Trigger | Scope |
|---------|-------|
| Every ~2-4 weeks | Full seven-face sweep |
| After a big refactor / directory reorg | Faces: docs + rules + evidence (path breakage focus) |
| After an incident | The face the incident touched + a mismatch-type scan of recent commits |
| Before a handoff | Full sweep — this is what makes the handoff trustworthy |

## Relationship to Other Patterns

- `MECHANICAL_HEALTH_CHECKS.md` — where repeat findings graduate to (sweep finds it twice → doctor checks it forever)
- `KNOWLEDGE_REGISTRY.md` — the triage output populates the registry; the registry's orphan check prevents the next drift
- `SUPERSEDE_CHAIN.md` — how archived conclusions stay traceable instead of vanishing
- [`neat-freak`](../../skills/loop-engineering/neat-freak/) skill — the per-session version of this; the inventory is the periodic deep version
