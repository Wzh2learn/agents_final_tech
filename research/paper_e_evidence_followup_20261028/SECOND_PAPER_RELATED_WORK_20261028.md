# Second-paper related-work screen and research options

Date: 2026-10-28. Status: preliminary literature triage, not established novelty or a publication guarantee. Respect all project stop decisions; new data require source/underlying report disjointness, licensing and model-exposure checks. Do not portray an AI review as human gold.

| Reference | Existing overlap and reason for comparison |
| --- | --- |
| [MoCA-Agent (EMNLP 2026)](https://aclanthology.org/2026.emnlp-main.478/) | Financial/table QA includes typed claims, program generation, verification and repair. Evidence binding plus execution verification and repair alone is not a new contribution. Check availability of components and compare reproducible cost-matched implementations. |
| [T²-RAGBench (EACL 2026)](https://aclanthology.org/2026.eacl-long.8/) | Financial text/table retrieval and numerical QA, including hybrid retrievers. Candidate source only after checking underlying documents, provenance, benchmark licensing and overlap with project data. A converted benchmark is not automatically an independent corpus. |
| [FinSearchComp (ICLR 2026)](https://proceedings.iclr.cc/paper_files/paper/2026/hash/4d42358702dff82e1436550a05ade260-Abstract-Conference.html) | Open financial search and reasoning. Check tool requirements and whether tasks, references and costs can be reproduced locally before selecting it. |
| [STALE / CUPMem](https://arxiv.org/html/2605.06527) | Structured updating, outdated evidence and action readout are already studied. A multiple-change setting may be a candidate research question, not an established novelty claim; verify subsequent literature. |
| [Self-RAG (ICLR 2024)](https://proceedings.iclr.cc/paper_files/paper/2024/file/25f7be9694d7b32d5cc670927b8091e1-Paper-Conference.pdf) | Learned retrieval and reflection signals already exist; a retrieval decision alone is not novel. |
| [Corrective RAG](https://arxiv.org/html/2401.15884) | Retrieval quality drives corrective search and document refinement. Compare implementable components and retrieval availability/cost. |
| [Reflexion (NeurIPS 2023)](https://proceedings.neurips.cc/paper_files/paper/2023/hash/1b44b878bb782e6954cd888628510e90-Abstract-Conference.html) | Feedback-based reflection and language memory for future attempts already exist. Existing project results do not show feedback learning is universally ineffective. |

## Candidate A: evidence sufficiency and grounded delivery

With identical retrieved evidence and deterministic calculator, compare a plain factual bundle, transparent period/unit/source checks, a reproducible MoCA-adjacent baseline if accessible, and a clearly specified candidate. Split by source report or company, not transformed questions; independently define multiple allowable correct answers and justified UNKNOWN. Report grounded correct delivery, erroneous acceptance, unnecessary abstention, risk-coverage and total inference/tool/latency costs. First establish that natural cases remain after strong rules; if a plain facts or transparent baseline matches the candidate at matched coverage/cost, stop the claimed method. No current qualification or source independence has been demonstrated.

## Candidate B: cost-aware supplementary evidence

On genuinely new qualified natural families, fix reader and answer contract. Compare sparse/dense/hybrid search, fixed top-k, neighbor expansion, always-expand, equal-cost random and an implementable corrective-retrieval baseline. Measure not just evidence recall but grounded correct answer, error acceptance and full retrieval/inference cost. First screen offline for an observable residual beyond fixed rules. Stop if additional recall does not improve downstream outcomes or cost advantage disappears. The previously closed exact-cache and static-rule panels remain closed.

## Required next step

Read primary full texts, retrieve dataset cards and licenses, map report/UID exposure to project assets, freeze an executable reference and falsifying baseline, then assess whether a small pilot is qualified. Do not start training based on topic similarity alone.
