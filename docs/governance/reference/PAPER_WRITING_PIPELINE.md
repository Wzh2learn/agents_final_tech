# Paper Writing Pipeline — Multi-Phase Architecture Reference

> A 10-phase pipeline for end-to-end research paper generation.
> This is an architecture reference — not a tool you install, but a pattern you implement
> using your own AI agents and the skills in this repo.

## Pipeline Overview

```
User Input (topic / brief / existing draft)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Engine                          │
│                                                                 │
│  Phase 1      Phase 1.5      Phase 2      Phase 3               │
│  Topic        Literature     Outline      Section               │
│  Exploration  Knowledge Base Generation   Writing               │
│                                                                 │
│  Phase 4/4A     Phase 5       Phase 6      Phase 7              │
│  Experiment/    Analysis &    Paper        3-Round               │
│  Argumentation  Writing      Integration  Review                │
│                                                                 │
│  Phase 8        Phase 9       Phase 10                          │
│  Fix Loop       External     Experiment                         │
│  (review→fix)   Polish       Design Plan                        │
└─────────────────────────────────────────────────────────────────┘
        │                       │                    │
        ▼                       ▼                    ▼
   Final Paper (.tex)     Review Report       Design Proposals
```

## Phase Definitions

### Phase 1: Topic Exploration
**Input**: Research domain keywords or broad direction  
**Output**: 3-5 refined research directions with novelty assessment  
**Agent**: Research Agent  
**Skill**: `dream-engine` (idea generation) + web search  

### Phase 1.5: Literature Knowledge Base
**Input**: Selected topic  
**Output**: Structured literature survey + research gap analysis  
**Agent**: Research Agent  
**Skills**: `pdf-ingestion` + `deep-research`  
**Key output**: Papers indexed by READING_NOTES_INDEX_TEMPLATE format  

### Phase 2: Outline Generation
**Input**: Literature analysis + selected direction  
**Output**: Paper outline (sections, subsections, key arguments per section)  
**Agent**: Writing Agent  
**Constraint**: Outline must map 1:1 to final paper structure  

### Phase 3: Section Writing
**Input**: Outline + literature KB + experiment results (if available)  
**Output**: Full draft sections in Markdown  
**Agent**: Writing Agent  
**Pattern**: Write section-by-section, maintain cross-section coherence  
**Skill**: `research-paper-pipeline` (if available)  

### Phase 4: Experiment / Argumentation (discipline-dependent)
**STEM variant (Phase 4)**:
- Generate experiment code → run → evaluate → iterate until quality threshold
- Closed-loop: code generation → execution → AI evaluation → improvement → re-run
- Exit when: evaluation score ≥ threshold OR max iterations reached

**Non-STEM variant (Phase 4A)**:
- Argumentation strengthening (humanities)
- Case analysis (social science)  
- Literature synthesis (survey papers)

### Phase 5: Analysis Writing
**Input**: Experiment results + figures  
**Output**: Results & Analysis sections  
**Agent**: Writing Agent  
**Key**: Numbers must trace to specific experiment logs (evidence linkable)  

### Phase 6: Paper Integration
**Input**: All sections  
**Output**: Complete paper (Markdown + LaTeX)  
**Mechanical step**: Section concatenation + cross-reference resolution + format conversion  

### Phase 7: Three-Round Review
**Input**: Complete paper  
**Output**: Review report with scored issues  
**Pattern**: Three independent review passes (structure → content → presentation)  
**Skill**: `paper-polish-and-audit`  
**Key**: Reviewer must NOT have access to the writing context (fresh eyes, no self-eval bias)  

### Phase 8: Fix Loop (Review → Fix → Re-review)
**Input**: Review issues  
**Output**: Revised paper  
**Pattern**:
```
For each issue:
  1. Map issue → specific section
  2. Fix only that section (don't touch unrelated text)
  3. Re-review the fix
  4. If quality improved → keep; if degraded → rollback
```
**Max iterations**: 3 rounds (diminishing returns beyond)

### Phase 9: External Polish
**Input**: Post-fix paper  
**Output**: Publication-ready paper  
**Focus**: Language polish, AI-pattern removal, formatting compliance  
**Skill**: `paper-polish-and-audit` (AI pattern removal checklist)  

### Phase 10: Experiment Design Plan (optional)
**Input**: Completed survey/paper  
**Output**: 3 innovative experiment proposals  
**Use case**: When the paper is a literature review that should suggest future work  

## Key Architecture Decisions

### 1. Phase separation = quality gates
Each phase produces a discrete artifact. The next phase reads the artifact, not the conversation context. This prevents context rot and enables parallel work.

### 2. Reviewer isolation (Phase 7)
The reviewer MUST be a fresh agent with no access to writing reasoning. Same-context review is self-eval bias (see `self-eval-bias` skill). Spawn a new agent or use a different model.

### 3. Fix loop with rollback (Phase 8)
Every fix is compared against the pre-fix version. If the fix degrades quality (measured by re-review), it's automatically rolled back. This prevents "fixing" that introduces new problems.

### 4. Evidence-linked numbers
Every quantitative claim in the paper must trace to:
- A specific experiment log file path
- A specific query/command that produced it
- A timestamp proving it's from the current run, not stale

### 5. Discipline profiles
Different disciplines need different Phase 4 implementations:
| Discipline | Phase 4 | Literature sources | Review criteria |
|-----------|---------|-------------------|----------------|
| STEM | Code + simulation | arXiv, Semantic Scholar | Reproducibility, novelty |
| Humanities | Argumentation | Scholar, library DBs | Depth of analysis |
| Social Science | Case analysis | Scholar, government data | Methodology rigor |
| Survey | Synthesis | All sources | Coverage, taxonomy |

## Mapping to Skills in This Repo

| Phase | Primary skill | Supporting skills |
|-------|--------------|-------------------|
| 1 | `dream-engine` | — |
| 1.5 | `pdf-ingestion` | `READING_NOTES_INDEX_TEMPLATE` |
| 2 | `spec-first` | `sprint-contract` |
| 3 | — (writing) | `context-budget` |
| 4 | `eval-harness` | `systematic-debugging` |
| 7 | `paper-polish-and-audit` | `self-eval-bias`, `adversarial-verify` |
| 8 | `verify-before-done` | — |
| 9 | `paper-polish-and-audit` | — |
