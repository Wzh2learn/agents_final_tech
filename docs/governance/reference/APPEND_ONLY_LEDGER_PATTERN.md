# Append-Only Ledger Pattern — Tamper-Evident Agent State

> A minimal pattern for agent state that detects accidental modification,
> supports replay, and maintains evidence chains across sessions.

## The Problem

Agent state in typical projects lives in Markdown files, git commits, and markers.
Three failure modes:
1. **Silent overwrite**: Agent edits a status field, old value gone
2. **Fake completion**: Agent touches `.done` marker; no proof work was actually done
3. **Lost history**: After compaction, "what happened when" requires git archaeology

## Core: Single-Writer JSONL + Hash Chain

```
file: ledger/<run-id>.jsonl

Line 1: {"envelope":{...,"prev_digest":"sha256:000...000"},"payload":{...}}  <- GENESIS
Line 2: {"envelope":{...,"prev_digest":"sha256:<hash-of-line-1>"},"payload":{...}}
Line 3: {"envelope":{...,"prev_digest":"sha256:<hash-of-line-2>"},"payload":{...}}
```

**Properties**:
- **Append-only**: New records appended, never overwrite
- **Hash-chained**: Each line's `prev_digest` = SHA256 of previous line
- **Single writer**: One process per ledger file (no concurrency needed)
- **GENESIS**: First line `prev_digest = "sha256:" + "0"*64`
- **Replay**: Read from line 1, verify each hash → detect any modification

## Minimal Envelope

```json
{
  "record_id": "CR-run-001-0007",
  "type": "CheckResult",
  "run_id": "experiment-batch-2026-09",
  "actor": "main_agent",
  "occurred_at": "2026-09-01T14:30:00Z",
  "recorded_at": "2026-09-01T14:30:05Z",
  "source_refs": ["commit:abc123", "logs/exp_001.log"],
  "payload_digest": "sha256:...",
  "prev_digest": "sha256:..."
}
```

Key: `occurred_at` vs `recorded_at` gap = measurable backfill latency.

## Digest Construction (deterministic)

```python
import json, hashlib

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')

def digest(obj):
    return "sha256:" + hashlib.sha256(canonical(obj)).hexdigest()

# Per record: build payload → payload_digest → set prev_digest → append → update ledger_head
```

## Verification (20 lines)

```python
def verify_ledger(filepath):
    GENESIS = "sha256:" + "0" * 64
    prev = GENESIS
    for i, line in enumerate(open(filepath)):
        record = json.loads(line)
        assert record["envelope"]["prev_digest"] == prev, f"Chain break at line {i}"
        assert record["envelope"]["payload_digest"] == digest(record["payload"])
        prev = digest(record)
    return True
```

## What This Gives You

| Capability | How |
|-----------|-----|
| Detect accidental edits | Modified line breaks hash chain forward |
| Replay state | Read from GENESIS, apply each record in order |
| Measure backfill rate | `recorded_at - occurred_at` across records |
| Audit trail | Who did what when, with source pointers, append-only |
| Evidence chain | Links to four-concept records (fact→check→judgment→approval) |

## What This Does NOT Give You (honest declaration)

- **Not tamper-resistant** against same-account malicious actor — can recompute entire chain
- **Not distributed** — single writer only, no concurrency
- **Not externally anchored** — without external signed timestamp, chain is self-referential

**Always be honest about these limitations.** Over-claiming security = worse than no security.

## Integration with Four-Concept Separation

| Record type | Concept | Stores |
|-------------|---------|--------|
| `EvidenceRef` | Fact | File hashes, exit codes, measurements |
| `CheckResult` | Completion | 5-status check with evidence refs |
| `JudgmentDraft` | Judgment | Analysis, confidence, suggestion (NO decision) |
| `ApprovalRecord` | Approval | Human identity, choice, request digest |
| `EvolutionRecord` | Meta | Incidents, rule proposals, supersede events |

## Three Levels of Adoption

**Level 1 — Manual**: Structure EXPERIMENTS_LOG entries with four concepts separated. No code needed.

**Level 2 — Simple script**: 100-line Python appending JSONL with hash chains. 20-line verify.

**Level 3 — Full system**: Typed records, CLI (append/verify/replay), doctor tool, external anchor.

## Historical Import

When adopting on existing projects:
- Import with `legacy_import: true` flag
- Historical imports don't count toward "zero backfill" metrics
- Only prospective records measured for system health

## External implementation status

The external `tools/loopkit_ledger.py` implementation and its `tools/LOOPKIT_LEDGER.md` guide are not imported into this repository. Current Markdown ledgers remain authoritative; importing a stronger hash-chain implementation requires a separate dependency and migration decision.

Three decisions in it that this document argues for and the code enforces:

- The chain covers the **whole line including the envelope**, so rewriting `actor` or a
  timestamp is as detectable as editing the payload.
- A line never contains its own digest — no self-reference, nothing to get wrong about
  what is hashed.
- `verify` (is the chain authentic?) and `audit` (is what it says plausible?) are separate
  commands, and audit findings never enter the ledger.
