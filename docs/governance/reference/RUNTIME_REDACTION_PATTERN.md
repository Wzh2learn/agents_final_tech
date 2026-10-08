# Runtime Redaction Pattern

> Status: active governance reference | Adapted for JinRongAgents from `skills-loop-engineering`.
> This pattern governs data in motion; at-rest scanning remains a separate check.

## Purpose

A repository scan proves tracked artifacts are clean. It cannot prevent credentials, private
sample content, or identifying paths from entering prompts, tool output, handoffs, logs, or
telemetry while work is running.

## Live Surfaces

| Surface | Required interception |
|---|---|
| Prompt or external API request | Redact before the request is constructed |
| Tool/command output | Redact before output re-enters agent context |
| Handoff, State, Threads, or task cards | Redact before durable write |
| Logs and telemetry | Redact at the logging/capture call |
| Public or shared artifacts | Remove real names, home paths, internal domains, and private data |

## Rules

1. Redact at capture or egress, never only at display/read time.
2. Use a default-deny exclusion set for `password`, `secret`, `token`, `key`, credentials, real
   home paths, user identifiers, and private sample content.
3. Record that a field was excluded; never record its value.
4. Treat third-party egress as publication because upstream retention cannot be revoked.
5. Prefer handles, hashes, or references over raw sensitive values.
6. Assume pattern matching is incomplete. Combine redaction with least privilege and rotation.

## Required Receipt

Durable runtime reports record:

- capture surface;
- excluded field names or classes, without values;
- destination trust boundary;
- whether the redaction was mechanically checked or manually reviewed;
- residual risk when novel secret shapes may have been missed.

## Relationship to Secret Scan

[`scripts/graph/tools/secret_scan.sh`](../../../scripts/graph/tools/secret_scan.sh) checks tracked
artifacts and optional Git history. This pattern covers in-motion data that never appears in the
repository scan scope. Neither replaces the other.

## Related

- [`UNTRUSTED_CHANNEL_DEFENSE_PATTERN.md`](UNTRUSTED_CHANNEL_DEFENSE_PATTERN.md) - inbound content boundary
- [`GROUND_TRUTH_ISOLATION_PATTERN.md`](GROUND_TRUTH_ISOLATION_PATTERN.md) - answer-key isolation
- [`../../../skills/secret-scan/`](../../../skills/secret-scan/) - at-rest secret review discipline
