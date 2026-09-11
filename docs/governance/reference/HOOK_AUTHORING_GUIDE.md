# Hook Authoring Guide — Writing Your Own Runtime Guards

> Hooks are shell scripts that fire at runtime events. They're the mechanical enforcement
> layer — when a rule fails 3+ times despite being documented, you write a hook.

## Hook Lifecycle in Claude Code / Compatible Tools

```
User action (type prompt, agent calls tool, session starts/ends)
    │
    ▼
Event fires (UserPromptSubmit / PreToolUse / SessionStart / SessionEnd / PreCompact)
    │
    ▼
Hook script receives JSON on stdin → processes → exits
    │
    ├── exit 0: allow (hook passes, action proceeds)
    ├── exit 2: block (action is rejected, stderr shown to agent)
    └── stdout: injected into context (agent sees this text)
```

## Anatomy of a PreToolUse Hook (Bash)

```bash
#!/bin/bash
# Hook: [name] (version, date)
# Rule: [what discipline this enforces]
# Evidence: [which incidents led to this hook — "3 times" threshold]

# === Step 1: Read stdin (JSON from the runtime) ===
INPUT=$(cat)

# === Step 2: Parse the command (graceful degradation) ===
if ! command -v python3 >/dev/null 2>&1; then
  echo "[hook-name] ⚠️ Guard degraded: python3 unavailable, passing through" >&2
  exit 0  # NEVER silent fail-open
fi

CMD=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('command', ''))
" 2>/dev/null)

# Degradation: stdin non-empty but parse returned empty
if [ -n "$INPUT" ] && [ -z "$CMD" ]; then
  echo "[hook-name] ⚠️ Guard degraded: parse returned empty, passing through" >&2
  exit 0
fi

# === Step 3: Check if this hook even applies ===
# Early exit for irrelevant commands (most commands don't need this hook)
if ! echo "$CMD" | grep -qE 'relevant_pattern'; then
  exit 0
fi

# === Step 4: The actual check ===
# [Your logic here — grep staged files, check lock status, validate content, etc.]

if [ VIOLATION_DETECTED ]; then
  # === Step 5: Block with actionable message ===
  # IMPORTANT: sanitize CMD before echoing (prevent multi-line injection)
  CMD_SAFE=$(printf '%s' "$CMD" | tr '\n\r' '  ' | cut -c1-200)
  echo "[hook-name] Block: [what rule was violated]" >&2
  echo "Command (truncated): $CMD_SAFE" >&2
  echo "[What the user should do instead]" >&2
  exit 2
fi

exit 0
```

## The Five Design Principles（+ principle 6 appended 2026-09-12 per RW-1; this heading is preserved verbatim under the append-only discipline, so it still reads "Five" while six principles follow）

### 1. Graceful Degradation (NEVER silent fail-open)

```bash
# ❌ BAD: silently passes when python3 is missing
CMD=$(echo "$INPUT" | python3 -c "..." 2>/dev/null)

# ✅ GOOD: warns and passes (user knows guard is down)
if ! command -v python3 >/dev/null 2>&1; then
  echo "[hook-name] ⚠️ Guard degraded: python3 unavailable" >&2
  exit 0
fi
```

**Why**: A guard that silently stops working is worse than no guard — you think you're protected when you're not.

### 2. Single-line Sanitization (prevent message injection)

```bash
# ❌ BAD: multi-line command echoed directly (can forge guard messages)
echo "Blocked command: $CMD" >&2

# ✅ GOOD: collapse to single line + truncate
CMD_SAFE=$(printf '%s' "$CMD" | tr '\n\r' '  ' | cut -c1-200)
echo "Command (truncated): $CMD_SAFE" >&2
```

**Why**: A crafted multi-line command could include text that looks like `[hook-name] ✅ Passed` — the agent would think the check passed when it was actually blocked.

### 3. Narrow Scope (check only what you enforce)

```bash
# ❌ BAD: runs on every single Bash command
# (slows down everything, triggers on irrelevant commands)

# ✅ GOOD: early-exit for irrelevant commands
if ! echo "$CMD" | grep -qE '(^|[;&|]\s*)git\s+commit\b'; then
  exit 0  # Not a commit command, not our business
fi
```

### 4. Actionable Block Messages

```bash
# ❌ BAD: "Operation not allowed"
# ✅ GOOD: explains what to do instead
echo "[large-file-guard] Block: project rule 'no large files in git'" >&2
echo "Forbidden: datasets/ models/ output/ *.pt *.npy *.ckpt" >&2
echo "These directories must stay in .gitignore; for exceptions, ask the human." >&2
exit 2
```

### 5. Test with Both Positive and Negative Cases

```bash
# Test: should BLOCK
echo '{"tool_input":{"command":"git push --force origin main"}}' | bash hooks/git-commit-guard.sh
echo "Exit: $?"  # Should be 2

# Test: should PASS
echo '{"tool_input":{"command":"git push origin main"}}' | bash hooks/git-commit-guard.sh
echo "Exit: $?"  # Should be 0
```

### 6. Normalize Path Encoding Before Feeding `git` Output to Another Command

Added 2026-09-12 (RW-1; side-thread acceptance counterexample CE8). This repository uses
non-ASCII (Chinese) document filenames extensively, so the condition below is **guaranteed
to be hit** — it is not an edge case.

`git diff --name-only`, `git ls-files`, `git status --porcelain` and friends quote any
non-ASCII path by default (`core.quotepath=true`), emitting a double-quoted octal escape
string such as `"docs/19_\347\263\273....md"`. If that string is then passed to another
git command, the argument is the *literal quoted escape text* rather than a real path, so
the lookup fails — and a guard built on that lookup silently stops guarding those files.

```bash
# BAD: CJK paths come back quoted+escaped, so the later lookup always misses them
staged=$(git diff --cached --name-only --diff-filter=ACM -- "*.md")
for f in $staged; do
  git cat-file -e ":$f" || { echo "WARN unreadable"; continue; }   # always fails for CJK
  ...
done

# GOOD: pin the quoting mode on the enumeration itself
staged=$(git -c core.quotepath=false diff --cached --name-only --diff-filter=ACM -- "*.md")

# ALSO ACCEPTABLE: NUL-delimited output carries no quoting at all
git diff --cached --name-only -z --diff-filter=ACM -- "*.md" | while IFS= read -r -d '' f; do
  ...
done
```

**Rule**: any script that takes `git … --name-only` (or `--porcelain`) output and uses it as
an argument to a later command must either set `-c core.quotepath=false` on the enumeration
or use `-z` together with `read -d ''`.

**Why this is a guard defect and not a cosmetic one**: the failure mode is *fail-open*. In
the RW-1 incident the summary-recompute guard printed `WARN 无法读取 … staged blob, 本项未复核`
and then `continue`d, so the receipt check never ran for that file at all — a Chinese-named
document carrying a **mismatched** receipt block committed successfully (rc=0), while the
byte-identical block in an ASCII-named file was correctly BLOCKED (rc=1). The only variable
was the filename.

**Do not "fix" this by weakening the WARN.** The explicit `WARN … (跳过不等于通过)` semantics
are correct, and they are exactly what made the gap visible; the defect was in how paths were
enumerated, not in how unreadable paths were reported. When a guard says "could not check",
treat that as a signal to fix the enumeration — never as a reason to downgrade the message.

**Author self-check**: after writing any path-enumerating guard, exercise it with a non-ASCII
filename in both directions (must BLOCK the bad case, must PASS the good case) — see
principle 5. A guard that has only ever been tested with ASCII paths is untested.

## Hook Types by Event

### PreToolUse (on Bash commands)
**Purpose**: Block dangerous operations before they execute  
**Input**: `{"tool_input": {"command": "..."}, "tool_name": "Bash"}`  
**Best for**: git guards, file protection, resource locks  

### UserPromptSubmit
**Purpose**: Inject context based on what the user asked  
**Input**: `{"prompt": "user's message text"}`  
**Best for**: skill routing suggestions, context reminders  
**Note**: stdout is injected as system context (agent reads it)  

### SessionStart / PreCompact
**Purpose**: Remind agent of project state at session boundaries  
**Input**: minimal (event metadata)  
**Best for**: "read these files first" reminders  

### SessionEnd
**Purpose**: Remind agent to save state before exit  
**Input**: minimal  
**Best for**: "update HANDOFF before closing" reminders  

## When to Write a Hook vs. When NOT to

### WRITE a hook when:
- The same mistake has happened **3+ times** despite documentation
- The check is **mechanically determinable** (regex, file existence, exit code)
- False positives are **rare** (the pattern is specific enough)
- The blocked action is **irreversible or expensive** (force-push, large file commit)

### DON'T write a hook when:
- The rule requires **judgment** (hook can't evaluate code quality)
- It would fire on **>20% of normal commands** (noise fatigue)
- The violation is **easily reversible** (typo in a comment)
- It's a **one-time setup issue** (just fix it once)

## Hook Escalation Ladder

```
Incident #1: Document the lesson in memory/rules
Incident #2: Add to CROSS_AGENT_LESSONS, discuss in review  
Incident #3: WRITE THE HOOK — human memory has proven insufficient
```

After deploying a hook:
1. Test with positive AND negative cases
2. Monitor for false positives in the first week
3. Tune keywords/patterns based on real usage
4. Log when the hook fires (for measuring if the problem actually stopped)

## Registration (settings.json)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/your-new-hook.sh",
            "name": "your-hook-name",
            "statusMessage": "Checking [what]..."
          }
        ]
      }
    ]
  }
}
```

## Debugging Hooks

```bash
# See what the hook receives:
echo '{"tool_input":{"command":"your test command"}}' | bash .claude/hooks/your-hook.sh
echo "Exit code: $?"

# See stderr output (block messages):
echo '{"tool_input":{"command":"git push --force"}}' | bash .claude/hooks/git-commit-guard.sh 2>&1

# Check if hook is executable:
ls -la .claude/hooks/your-hook.sh  # Must have +x
```
