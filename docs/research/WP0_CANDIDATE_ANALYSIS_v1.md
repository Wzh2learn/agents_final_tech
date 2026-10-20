# WP0 Candidate Analysis v1

> date: 2026-10-13 | author: Loop D (read-only forward preparation) | status: `PREPARATION_ONLY / NO_EXPERIMENT / NO_DOWNLOAD`
> parent: [WP0_QUALIFICATION_REPORT_v1.md](WP0_QUALIFICATION_REPORT_v1.md) | authority: [task card](../archive/2026-10-20_entry_consolidation/thesis_experience_v1_task_card.md), [blueprint](THESIS_EXECUTION_BLUEPRINT_v1.md), [entry](../archive/2026-10-20_entry_consolidation/MASTER_RESEARCH_EXECUTION_ENTRY_v1.md)
> purpose: so that the next session does not start from zero. Nothing here authorises a download, a run, or a new RQ.

## 1. Candidate task-source ranking (fit to "two-period increase/decrease with unit unification")

Criteria: (a) does the source actually contain two aligned periods per record; (b) is a unit/scale column present or derivable; (c) can reference answers be independently recomputed from the source; (d) can >= 8 origin groups be formed; (e) licence clarity; (f) independence from material already used by this project.

| Rank | Source | (a) two periods | (b) units | (c) independent gold | (d) >=8 origins | (e) licence | (f) exposure | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | **TAT-QA** | likely (financial statements) | possible | yes, arithmetic from the table | likely (per-report groups) | MIT repo; README-reported CC BY 4.0 - **recheck at fetch** | **used by this project's Stage E carrier** - exposure audit required | **best fit, but needs an exposure audit + licence recheck** |
| 2 | **MultiHiertt** | likely | possible | yes | likely | MIT repo; external package scope review required | unused here | strong alternative; licence scope must be reviewed |
| 3 | **FinQA** | partial (mostly single-table) | partial | yes (programs) | likely | MIT repo; **README silent on data licence at recorded head** | **used by this project's second dataflow** | licence unresolved + exposure; not first choice |
| 4 | **HiTab** | partial | possible | partial | likely | **NOASSERTION**; C-UDA-1.0 review required | unused | licence risk; keep as stress material only |
| 5 | ConvFinQA | partial | partial | yes | shares FinQA lineage | MIT | linked to a used source | **excluded** (not an independent test source) |
| 6 | GitTables | n/a | n/a | no pairwise gold | n/a | CC0-1.0 | unused | proposal/pretraining only; not a task source |
| 7 | Sherlock/VizNet | n/a | n/a | type labels only | n/a | MIT + upstream | unused | baseline/pretrain only |
| 8 | HybridQA / OTT-QA | no | no | yes | yes | MIT | unused | wrong domain (Wikipedia); not the required task |
| 9 | Valentine/NYC | no | no | match gold | yes | Apache-2.0 + NYC terms | used for schema pilot | wrong task for TH3-RQ2 |

**New candidate worth a decision (not in the registry):** public US SEC filings (EDGAR 10-K/10-Q) are US-government public domain, carry genuine multi-period tables with explicit units, and support per-company origin grouping. It is **not** in the registry, would be **new data acquisition**, and therefore **needs owner authorisation** before any fetch. Stated here only as an option, not as a plan.

## 2. Licence feasibility

| Source | What signing would require |
|---|---|
| TAT-QA | Re-verify the CC BY 4.0 statement at the fetched revision (the registry flags it as README-reported); retain attribution; confirm redistribution compatibility for a released artifact |
| MultiHiertt | Review the external package scope (the data ships outside the repo licence) and record the upstream terms |
| FinQA | **Blocking until resolved:** the repository licence covers code; the data licence is unstated at the recorded head. Either obtain an upstream statement or record an accepted-risk decision |
| HiTab | Resolve NOASSERTION; C-UDA-1.0 has redistribution constraints |
| Valentine/NYC | Confirm NYC Open Data upstream terms cover the intended use |

**Common requirement:** every row needs a signed `licence_record` naming the exact revision, the permitted uses (experience collection / evaluation / artifact release), and the attribution obligations.

## 3. Literature gap map (from recorded material only; no new search)

| Neighbour | What it already covers | What it leaves open for TH3-RQ2 |
|---|---|---|
| ACE | experience manual built by generation + reflection + consolidation, using natural execution feedback | whether a *fact-supported* (not self-graded) feedback channel changes future-task utility |
| MemRL | environment-feedback-driven memory utility and retrieval | the same, on a different task family and with paired controls |
| TRUSTMEM | coverage / retention / fidelity of memory transformations | does not test downstream task utility |
| PMD | cross-task program experience distilled into parameters | parameter distillation, not the minimal context-reuse question |

**Retained single hypothesis (from the task card):** whether a nearest-neighbour-unexplained separation exists between fact-supported past feedback and future-task utility, beyond static rules, plain few-shot, and the adapted existing methods. **Still `NOT_IDENTIFIED`.**

## 4. Minimal experiment design (ready to instantiate, not implemented)

- **Task contract:** two-period increase/decrease with unit unification; per item: two period columns, a unit column (or a derivable scale), and a reference answer recomputable from the source; the actor must choose fields, periods, unit relation and the arithmetic parameter, and must call a calculator tool whose result the answer consumes.
- **Arms (frozen from the blueprint):** B no experience; E 1-2 real executed episodes from *other* origins with independent feedback and actually-executed corrections; C matched unrelated experience (<=5% context-token delta); S static unit/period rules frozen at development time.
- **Scale:** pool 8 episodes from >=4 origins; development 4 tasks from >=2 origins; pilot 16 tasks from 8 unseen origins (2 each); 4 arms x 16 tasks x 2 repeats = 128 episodes, <=256 model calls, history+development <=40, retries <=4; **hard cap 300 request attempts, 0 judge calls**.
- **Independent unit:** the 8 origins, not the 16 tasks or 32 repeats.
- **Primary endpoint:** answer correctness including unit and period. Report E-B, E-C, E-S and C-B; count corrected, regressed, refusals, UNKNOWN and cost.
- **Gates:** `CONTINUE_EXPLORATORY` requires E-B and E-C each >= +12.5pp with >=3 net-positive origins each, no origin contributing >50% of its corrections, both repeats not reversing, and behaviour consistent with the gain. `STOP_THIS_PANEL` on leakage/bridge failure or a ceiling in B. `UNDETERMINED` otherwise.
- **Pre-instantiation blockers:** licence record; origin grouping; frozen actor revision; feedback-right decision; budget window. (Same five as the qualification report.)

## 5. What the next session can do without new authorisation

1. Draft the `licence_record` for the top-ranked source (TAT-QA) from its official pages - metadata only, no fetch.
2. Draft the origin-grouping rule (how a report/company becomes an origin, and how near-duplicates are isolated) against the source's schema document.
3. Draft the task-adapter contract (field/period/unit extraction, gold recomputation, tool-consumption check) as a specification only.
4. Rank the candidate sources once more if the owner narrows to a family.

## 6. What still needs the owner

- Which source family to pursue (and, if SEC EDGAR is attractive, authorisation for new acquisition).
- The feedback right: what historical feedback may be shown to the actor and from where.
- The actor revision freeze.
- Any actual download, run, or budget window.

**No download, no model call, no runner, no experiment. This document prepares work; it does not authorise it.**