<!-- Managed by agent: archive scope contains history, not current instructions. Last updated: 2026-09-22 -->

# Archived Documentation Rules

## Overview

Everything in this directory is historical evidence. Root [`../../AGENTS.md`](../../AGENTS.md) remains authoritative for current behavior.

## Setup

No setup is defined here. Use current commands from the root rules and documentation index.

## Build and tests

Do not copy commands or test claims from archived documents into active guidance without re-verifying them against the current branch.

## Code style

Preserve historical snapshots as written. Add context in active documentation instead of rewriting archived facts.

## Security

Historical status never authorizes credentials, production access, service probes, or changes to the read-only MCP boundary.

## Checklist

- Treat archived metrics, paths, ports, and runtime claims as historical only.
- Use `git mv` plus an `INDEX.md` update when archiving another document.
- Do not delete archived material without explicit approval.

## Examples

Good: cite an archive file as dated evidence. Bad: present an archive file as the current runbook.

## When stuck

Use [`../INDEX.md`](../INDEX.md) to find the active source, then consult [`../../memory/STATE.md`](../../memory/STATE.md) for the current snapshot.
