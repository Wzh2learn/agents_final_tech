# Loop C Lead architecture and control-plane contract

## Authority and non-competition

Loop D (user plus the main thread) owns research questions, paper positioning, priority, frozen oracle/threshold/protocol, endpoint and training release, publication, main integration, and final accept/reject. Loop C Lead is the GB10 execution coordinator: it reads persistent state, converts an approved objective into one bounded card, dispatches at most one modifying Loop A, collects evidence, requests a fresh C Audit, and records the result. Loop A executes only declared paths. Loop B remains mechanical verification. A fresh C Audit is read-only and cannot inherit the Lead's conclusion. Loop C cannot merge or push main, change frozen rules, open endpoints, restart services, train, delete unclear user assets, or publish.

## State machine

IDLE -> PLANNED -> CARD_READY -> RUNNING -> COLLECTING -> AUDIT_PENDING -> AUDITING -> ACCEPTED. Explicit exits are RUNNING -> BLOCKED for a missing prerequisite, AUDITING -> REPAIR_PENDING for at most one bounded correction, AUDITING -> REJECTED for insufficient evidence, and any state -> STOPPED when STOP exists. A stale or malformed ACTIVE.json blocks dispatch; it never authorizes a blind rerun. After an atomic checkpoint, ACCEPTED -> PLANNED may select the next dependency-satisfied card. The same failure twice becomes a diagnostic card; the same blocker three rounds stops and enters DECISIONS_PENDING.md.

## Persistent control surface

The control root is outside Git: ~/.jinrong-loop-c/.

- GOAL.md: approved objective, authority split, and redlines; no credentials.
- QUEUE.yaml: JSON-compatible YAML 1.2 task list validated by the controller; id, mode, dependencies, status, model, worktree/branch, owned/forbidden paths, outputs, stop conditions, max attempts.
- ACTIVE.json: exactly one claimed task, worktree, owned paths, PID/session, start time, and state.
- CHECKPOINT.md: last result, report, worktree, paths, and next entry; written with os.replace.
- DECISIONS_PENDING.md: decisions reserved for Loop D/user.
- STOP: presence blocks all new dispatch; only explicit resume removes it.
- cards/, reports/, logs/: immutable cards, A/C reports, and control logs; no secrets.

## Scheduling loop

Every round reloads GOAL, QUEUE, CHECKPOINT, Loop B state and Git/worktree status. It refuses work when STOP exists, ACTIVE is running, dependencies are unmet, forbidden paths/endpoints are requested, or queue schema is invalid. It claims exactly one READY task atomically, writes the card, dispatches Loop A with the declared model and endpoint budget, records rc/diff/numstat/hashes, then sends a new C Audit. At most one targeted repair is allowed. The round ends by atomically updating CHECKPOINT, queue status, and ACTIVE. A model call is never retried blindly.

## Commands

After source ~/.bashrc on GB10:

    export JINRONG_LOOP_C_HOME="$HOME/.jinrong-loop-c"
    python3 "$JINRONG_LOOP_C_HOME/loop_c_lead.py" check
    python3 "$JINRONG_LOOP_C_HOME/loop_c_lead.py" status
    python3 "$JINRONG_LOOP_C_HOME/loop_c_lead.py" start
    python3 "$JINRONG_LOOP_C_HOME/loop_c_lead.py" complete TASK_ID PASS --report "$HOME/.jinrong-loop-c/reports/TASK_ID.md"
    python3 "$JINRONG_LOOP_C_HOME/loop_c_lead.py" pause "reason"
    python3 "$JINRONG_LOOP_C_HOME/loop_c_lead.py" resume
    python3 "$JINRONG_LOOP_C_HOME/loop_c_lead.py" stop

start claims one card; it does not invoke an unbounded agent. Dispatch uses the card's model/profile and records the returned session/PID.

## Git work surface

Worktree /home/testuser/wzh/projects/agents_final_tech_loop_c, branch gb10/loop-c-lead-20260923, base origin/main at the initialization commit recorded in CHECKPOINT. It is never the production checkout. Loop C may make small auditable commits there; Loop D reviews integration and controls main.

## Initial queue and permission matrix

Initial ready cards are LC-GOV-002 (read-only governance/archive inventory) and LC-RESEARCH-001 (offline evidence-map/data-supplement design). LC-A2-EXPAND waits for a future exact scope; LC-DATA-SUPPLEMENT waits for complete source/schema/licence/correctness evidence; LC-PHASE1A remains behind DATA_NO_GO; LC-PHASE2 remains blocked and unstarted. Only one modifying A may run; read-only audits can run separately.

Lead may read evidence, dispatch bounded cards, and advance owned governance/design work. Loop D/user must decide core claims, frozen rules, endpoints, restart, training, deletion of unclear assets, main integration, and publication.

Current boundary: Phase 1a is DATA_NO_GO, Phase 2 unstarted. Control-plane, governance, documentation, archive candidates, and experiment design may proceed; no baselines or speculative paper numbers may be manufactured.

## Four work modes

- LEAD reads the goal, queue, checkpoint, Loop B state, and Git state; selects one dependency-satisfied card; dispatches at most one modifying Loop A; and owns stop conditions.
- RESEARCH maps hypotheses, approved offline tools, power limits, and evidence-to-claim links; it cannot change the final paper positioning or frozen protocol.
- GOVERNANCE reconciles docs, memory, Git dirty-file ownership, archive candidates, and regenerable reports; ambiguous user assets are registered and left untouched.
- AUDIT is a fresh read-only Loop C session. It reviews the Lead or Loop A result, cannot edit audited files, and cannot inherit the Lead session conclusion. One Claude session never performs both Lead and independent Audit roles.
