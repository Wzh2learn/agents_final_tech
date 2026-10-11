# VENUE_PORTABILITY_NOTE_v1.md

> date: 2026-10-11 | READ-ONLY estimate | owner is deciding the venue (SANER RENE default). This note does NOT change the manuscript and does NOT open a branch.
> Scope: estimate the work to port the current manuscript (SANER RENE: NegativeResult) to (B) CAIN 2027 Research and (C) ICST 2027 Research. Effort scale: LOW / MEDIUM / HIGH.

## Baseline (current, SANER RENE)
Framing: a measurement-validity / negative-result audit of an observation surface, with construct separation (visibility vs detection vs harmfulness), a protocol-identifiability null, a construction-bounded instrumentation result, and a FinQA failed-transfer autopsy. Format: IEEEtran 10pt conference, 10 pages + 2 references-only pages, double-anonymous.

## B. SANER RENE -> CAIN 2027 Research
CAIN (Conference on AI Engineering) is AI-engineering focused: an AI-engineering lens (building/evaluating AI-enabled systems) is expected, with a research/industry split and its own template and limits.

| Component | Effort | Why |
|---|---|---|
| Title/abstract framing | MEDIUM | Reframe from "long-horizon AI evaluation" measurement-validity to "AI-engineering evaluation practice"; keep the construct separation, but foreground the AI-engineering practice takeaway. |
| Introduction | MEDIUM | Motivation must lead with AI-engineering evaluation practice (LLM/pipeline evaluation), not software-analysis evaluation. |
| Contribution wording | MEDIUM | Contributions are domain-general but must be phrased as AI-engineering guidance (how to report AI-system evaluation surfaces). |
| Related work | HIGH | Our three layers are SE-testing/meta-evaluation centric; CAIN expects AI-engineering literature (LLM evaluation, AI system engineering). A substantial new layer is required. |
| Experiments | MEDIUM | The controlled pipeline study fits, but the reviewer framing (AI system, not document intelligence only) needs restatement; no new experiments required. |
| Template | LOW | IEEE-style template; page limits and anonymization policy differ and must be confirmed on the CAIN 2027 CFP. |
| Overall | MEDIUM-HIGH | Real reframing plus a largely new related-work layer; experiments reusable. |

## C. SANER RENE -> ICST 2027 Research
ICST (software testing) is a strong fit for oracle insensitivity, mutation/fault injection, and diagnosability.

| Component | Effort | Why |
|---|---|---|
| Title/abstract framing | LOW-MEDIUM | Retitle toward the oracle/diagnosability question (for example, "oracle insensitivity and observation-surface diagnosability"); the detection/visibility separation maps directly. |
| Introduction | MEDIUM | Lead with the testing/oracle problem; the AI-evaluation framing becomes secondary. |
| Contribution wording | MEDIUM | Same three contributions, rephrased in testing terms (oracle insensitivity, RIPR/failed propagation, diagnosability). |
| Related work | MEDIUM | Add the oracle-problem / RIPR / test-oracle literature; the mutation/fault-injection layer already fits and can be deepened. |
| Experiments | LOW | Fault injection, controlled checkpoints and failure-family analysis are native to ICST; no new experiments required. |
| Template | LOW | IEEE template; confirm ICST 2027 limits and anonymity policy on its CFP. |
| Overall | LOW-MEDIUM | Best fit; mostly wording and a deepened testing related-work layer. |

## Summary
- ICST 2027 Research: LOW-MEDIUM (best fit; experiments native).
- CAIN 2027 Research: MEDIUM-HIGH (needs a real AI-engineering reframe and a new related-work layer).
- D/E (EASE 2027 R&NR / Research, strengthened ISSTA 2027): not estimated here; a follow-up note can add them.

## Constraint
No manuscript edit is made under this note. The port portability decision belongs to the owner, and PRIMARY_ROUTE remains SANER RENE until the owner decides.