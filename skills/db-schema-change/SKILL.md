---
name: db-schema-change
when_to_use: reviewing a migration, "what changed in the schema", pre-deploy check, add/alter a table, column, index, or constraint
description: Change a database schema safely — diff two schema states to rank the risks, then write a reversible migration with a live-safe deploy order. Use before applying a migration, after a model change, or on "what changed in the schema".
---

# Database Schema Change

Two steps that belong in one session: judge the risk of the change, then write the change so it can
be undone and so it does not lock a hot table.

## 1. Diff the states, ranked by risk

Diff old vs new schema. Flag by risk:

- **Destructive** (high): dropped column/table, narrowed type, new NOT NULL on existing rows, dropped index a query relies on.
- **Locking** (high at scale): index without CONCURRENTLY, type change that rewrites the table.
- **Safe**: new nullable column, new table, new index CONCURRENTLY.

For each destructive change: is data lost? is it reversible? is there a backfill? Output a risk-ranked
list and a go/no-go with the safe rollout order.

## 2. Write the migration

1. Read the current schema first. Match the repo's migration tool and naming (`NNN_<verb>_<noun>`).
2. Write BOTH up and down. A migration you can't reverse is a migration you can't deploy safely.
3. **Live-safe**: on a hot table, adding a NOT NULL column with no default, or an index without
   CONCURRENTLY, takes a blocking lock. Split into steps: add nullable → backfill → add constraint.
4. Backfill large tables in batches, not one statement.
5. Never edit an already-merged migration — add a new one.

Test with a dry-run before committing. Output the migration + the exact deploy order.

## Completion

Report: the risk table from step 1 (change / class / data loss / reversible / backfill), the migration
files written (up and down paths), the dry-run command and its result, and the ordered deploy steps.
