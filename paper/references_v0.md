# Paper references v0 — cited entries (verified in-repo only)

> 状态: 引用表（2026-09-21, Loop D 主线程, 批 #9-A）| 供 `paper/draft_v0_s1_s2_s6.md` 的 Related work 小节使用
> 纪律: **只用仓内已核验条目**; venue 未在官方 API 核到的**不标 venue**, 一律写 `arXiv preprint`;
> 逐条给 arXiv ID 或 DOI。来源池 = `docs/experiments/2026-08-31_related_work_v4.md`（四簇, 经 arXiv API 实查）
> 与 `docs/experiments/2026-09-20_kd_literature_candidates.md`（KD 候选, arXiv 官方 API 已核）。
> 本件不新增任何未经核验的条目, 不引用未核 CFP。

## 1 Related work 四簇引用（12 条）

| cite key | 题名 | 年 | arXiv ID | venue |
|---|---|---|---|---|
| `amrhein2022aces` | ACES: Translation Accuracy Challenge Sets for Evaluating Machine Translation Metrics | 2022 | arXiv:2210.15615 | arXiv preprint |
| `amrhein2023aceswmt` | ACES: Translation Accuracy Challenge Sets at WMT 2023 | 2023 | arXiv:2311.01153 | arXiv preprint |
| `moghe2024acesjournal` | Machine Translation Meta Evaluation through Translation Accuracy Challenge Sets | 2024 | arXiv:2401.16313 | arXiv preprint |
| `deviyani2025contextual` | Contextual Metric Meta-Evaluation by Measuring Local Metric Accuracy | 2025 | arXiv:2503.19828 | arXiv preprint |
| `kendiukhov2026ranking` | Quantifying Ranking Instability Across Evaluation Protocol Axes in Gene Regulatory Network Benchmarking | 2026 | arXiv:2603.03493 | arXiv preprint |
| `du2026promptranking` | On the Stability of Prompt Ranking in Large Language Model Evaluation | 2026 | arXiv:2606.24381 | arXiv preprint |
| `ross2024goodmetric` | What makes a good metric? Evaluating automatic metrics for text-to-image consistency | 2024 | arXiv:2412.13989 | arXiv preprint |
| `messing2026measurementerror` | Hidden Measurement Error in LLM Pipelines Distorts Annotation, Evaluation, and Benchmarking | 2026 | arXiv:2604.11581 | arXiv preprint |
| `fan2026agentprocessbench` | AgentProcessBench: Diagnosing Step-Level Process Quality in Tool-Using Agents | 2026 | arXiv:2603.14465 | arXiv preprint |
| `chung2026webstep` | Where Did It Go Wrong? Process-Level Evaluation of Web Agents with Semantic State Tracking | 2026 | arXiv:2606.15673 | arXiv preprint |
| `cho2025metamorphic` | Metamorphic Testing of Large Language Models for Natural Language Processing | 2025 | arXiv:2511.02108 | arXiv preprint |
| `tan2026agentchaos` | AgentChaos: Chaos Engineering for Agent Systems via Programmatic Fault Injection | 2026 | arXiv:2608.06790 | arXiv preprint |
| `li2024pedants` | PEDANTS: Cheap but Effective and Interpretable Answer Equivalence | 2024 | arXiv:2402.11161 | arXiv preprint |
| `zheng2023judge` | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | 2023 | arXiv:2306.05685 | arXiv preprint |
| `li2025robustjudge` | LLMs Cannot Reliably Judge (Yet?): A Comprehensive Assessment on the Robustness of LLM-as-a-Judge | 2025 | arXiv:2506.09443 | arXiv preprint |
| `li2025scoringbias` | Evaluating Scoring Bias in LLM-as-a-Judge | 2025 | arXiv:2506.22316 | arXiv preprint |

## 2 m9 引用（1 条: Algorithm 1 的原始出处）

| cite key | 题名 | 年 | arXiv ID | venue |
|---|---|---|---|---|
| `wang2026gta2` | GTA-2: Benchmarking General Tool Agents from Atomic Tool-Use to Open-Ended Workflows | 2026 | arXiv:2604.15715 | arXiv preprint |

- 该件是 Algorithm 1（recursive checkpoint scoring）的**原始出处**，m9 由此闭环。
- **同名歧义已判**：另有 arXiv:2609.09808 的同名 GTA-2 属机器人操作方向，**不引**。
- **一律以 arXiv 版引用**：本仓 hbkeyan 目录下的 PDF 属仓外材料，不作唯一出处。

## 3 KD / agent distillation（future work，5 条）

| cite key | 题名 | 年 | arXiv ID / DOI | venue |
|---|---|---|---|---|
| `hinton2015distilling` | Distilling the Knowledge in a Neural Network | 2015 | arXiv:1503.02531 · DOI 10.48550/arxiv.1503.02531 | arXiv preprint（venue 待另核） |
| `xu2024kdsurveyllm` | A Survey on Knowledge Distillation of Large Language Models | 2024 | arXiv:2402.13116 · DOI 10.48550/arxiv.2402.13116 | arXiv preprint（venue 待另核） |
| `qiu2025agentdistill` | AgentDistill: Training-Free Agent Distillation with Generalizable MCP Boxes | 2025 | arXiv:2506.14728 | arXiv preprint（venue 待另核） |
| `liu2025structuredagent` | Structured Agent Distillation for Large Language Model | 2025 | arXiv:2505.13820 | arXiv preprint（venue 待另核） |
| `chen2026counteraction` | Counteraction-Aware Multi-Teacher On-Policy Distillation for General Capability Recovery with Domain Preservation | 2026 | arXiv:2605.27115 | arXiv preprint（venue 待另核） |
| `ma2026mopd` | MOPD: Multi-Teacher On-Policy Distillation for Capability Integration in LLM Post-Training | 2026 | arXiv:2606.30406 | arXiv preprint（venue 待另核） |

## 4 BibTeX（逐条: Related work 12 + m9 1 + KD 6 = 19 条）

```bibtex
@article{amrhein2022aces,
  title   = {ACES: Translation Accuracy Challenge Sets for Evaluating Machine Translation Metrics},
  author  = {Amrhein, Chantal and Moghe, Nikita and Guillou, Liane},
  journal = {arXiv preprint arXiv:2210.15615}, year = {2022}}

@article{amrhein2023aceswmt,
  title   = {ACES: Translation Accuracy Challenge Sets at WMT 2023},
  author  = {Amrhein, Chantal and Moghe, Nikita and Guillou, Liane},
  journal = {arXiv preprint arXiv:2311.01153}, year = {2023}}

@article{moghe2024acesjournal,
  title   = {Machine Translation Meta Evaluation through Translation Accuracy Challenge Sets},
  author  = {Moghe, Nikita and Fazla, Arnisa and Amrhein, Chantal and others},
  journal = {arXiv preprint arXiv:2401.16313}, year = {2024}}

@article{deviyani2025contextual,
  title   = {Contextual Metric Meta-Evaluation by Measuring Local Metric Accuracy},
  author  = {Deviyani, Athiya and Diaz, Fernando},
  journal = {arXiv preprint arXiv:2503.19828}, year = {2025}}

@article{kendiukhov2026ranking,
  title   = {Quantifying Ranking Instability Across Evaluation Protocol Axes in Gene Regulatory Network Benchmarking},
  author  = {Kendiukhov, Ihor},
  journal = {arXiv preprint arXiv:2603.03493}, year = {2026}}

@article{du2026promptranking,
  title   = {On the Stability of Prompt Ranking in Large Language Model Evaluation},
  author  = {Du, Shaoshuai and Liang, Penghao and Shen, Yixian and others},
  journal = {arXiv preprint arXiv:2606.24381}, year = {2026}}

@article{ross2024goodmetric,
  title   = {What makes a good metric? Evaluating automatic metrics for text-to-image consistency},
  author  = {Ross, Candace and Hall, Melissa and Romero Soriano, Adriana and Williams, Adina},
  journal = {arXiv preprint arXiv:2412.13989}, year = {2024}}

@article{messing2026measurementerror,
  title   = {Hidden Measurement Error in LLM Pipelines Distorts Annotation, Evaluation, and Benchmarking},
  author  = {Messing, Solomon},
  journal = {arXiv preprint arXiv:2604.11581}, year = {2026}}

@article{fan2026agentprocessbench,
  title   = {AgentProcessBench: Diagnosing Step-Level Process Quality in Tool-Using Agents},
  author  = {Fan, Shengda and Ye, Xuyan and Huo, Yupeng and others},
  journal = {arXiv preprint arXiv:2603.14465}, year = {2026}}

@article{chung2026webstep,
  title   = {Where Did It Go Wrong? Process-Level Evaluation of Web Agents with Semantic State Tracking},
  author  = {Chung, Jiwan and Byun, JiHyuk and Vineet, Vibhav and Kim, Seon Joo},
  journal = {arXiv preprint arXiv:2606.15673}, year = {2026}}

@article{cho2025metamorphic,
  title   = {Metamorphic Testing of Large Language Models for Natural Language Processing},
  author  = {Cho, Steven and Ruberto, Stefano and Terragni, Valerio},
  journal = {arXiv preprint arXiv:2511.02108}, year = {2025}}

@article{tan2026agentchaos,
  title   = {AgentChaos: Chaos Engineering for Agent Systems via Programmatic Fault Injection},
  author  = {Tan, Gou and Sun, Zhensu and Shi, Jieke and others},
  journal = {arXiv preprint arXiv:2608.06790}, year = {2026}}

@article{li2024pedants,
  title   = {PEDANTS: Cheap but Effective and Interpretable Answer Equivalence},
  author  = {Li, Zongxia and Mondal, Ishani and Liang, Yijun and Nghiem, Huy and Boyd-Graber, Jordan Lee},
  journal = {arXiv preprint arXiv:2402.11161}, year = {2024}}

@article{zheng2023judge,
  title   = {Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena},
  author  = {Zheng, Lianmin and Chiang, Wei-Lin and Sheng, Ying and others},
  journal = {arXiv preprint arXiv:2306.05685}, year = {2023}}

@article{li2025robustjudge,
  title   = {LLMs Cannot Reliably Judge (Yet?): A Comprehensive Assessment on the Robustness of LLM-as-a-Judge},
  author  = {Li, Songze and Xu, Chuokun and Wang, Jiaying and others},
  journal = {arXiv preprint arXiv:2506.09443}, year = {2025}}

@article{li2025scoringbias,
  title   = {Evaluating Scoring Bias in LLM-as-a-Judge},
  author  = {Li, Qingquan and Dou, Shaoyu and Shao, Kailai and Chen, Chao and Hu, Haixiang},
  journal = {arXiv preprint arXiv:2506.22316}, year = {2025}}

@article{wang2026gta2,
  title   = {GTA-2: Benchmarking General Tool Agents from Atomic Tool-Use to Open-Ended Workflows},
  author  = {Wang, Jize and others},
  journal = {arXiv preprint arXiv:2604.15715}, year = {2026}}

@article{hinton2015distilling,
  title   = {Distilling the Knowledge in a Neural Network},
  author  = {Hinton, Geoffrey E. and Vinyals, Oriol and Dean, Jeff},
  journal = {arXiv preprint arXiv:1503.02531}, year = {2015}}

@article{xu2024kdsurveyllm,
  title   = {A Survey on Knowledge Distillation of Large Language Models},
  author  = {Xu, Xiaohan and Li, Ming and Tao, Chongyang and others},
  journal = {arXiv preprint arXiv:2402.13116}, year = {2024}}

@article{qiu2025agentdistill,
  title   = {AgentDistill: Training-Free Agent Distillation with Generalizable MCP Boxes},
  author  = {Qiu, Jiahao and others},
  journal = {arXiv preprint arXiv:2506.14728}, year = {2025}}

@article{liu2025structuredagent,
  title   = {Structured Agent Distillation for Large Language Model},
  author  = {Liu, Jun and others},
  journal = {arXiv preprint arXiv:2505.13820}, year = {2025}}

@article{chen2026counteraction,
  title   = {Counteraction-Aware Multi-Teacher On-Policy Distillation for General Capability Recovery with Domain Preservation},
  author  = {Chen, Tianlei and others},
  journal = {arXiv preprint arXiv:2605.27115}, year = {2026}}

@article{ma2026mopd,
  title   = {MOPD: Multi-Teacher On-Policy Distillation for Capability Integration in LLM Post-Training},
  author  = {Ma, Wenhan and others},
  journal = {arXiv preprint arXiv:2606.30406}, year = {2026}}

```

## 5 未核实项（不入引用）

- **所有本表 venue 列**：除 `10.1007/s11263-021-01453-z`（IJCV, OpenAlex 已核）之外, 本表条目一律写 arXiv preprint;
  `cho2025metamorphic` 的 ICSME 与 `chung2026webstep` 的 COLM 标签**在 arXiv 元数据中无 venue 记录, 故本表不标**。
- **KD 条目的 venue**：全部待另核（承 `2026-09-20_kd_literature_candidates.md` §8）。
- **MOPD 系列机构归属**：未经官方源核实, 不在正文出现。
