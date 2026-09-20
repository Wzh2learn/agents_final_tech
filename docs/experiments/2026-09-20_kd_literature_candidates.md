# 知识蒸馏（LLM / Agent）候选文献核验表

> 状态: 候选清单（2026-09-20, Loop D 主线程, 零端点）| 取代/被取代: 不取代任何件; 供 `docs/33` / `docs/34` / 相关工作后续取用
> 核验源: **arXiv 官方 API**（`export.arxiv.org/api/query`）+ **OpenAlex 官方 API**（`api.openalex.org/works`）; 每条字段取自官方响应原文, **不经二手站 / 营销号**
> 资格口径（用户 2026-09-20 裁定, 决策 58）: **只有 arXiv / OpenAlex 已核条目列为候选**; **venue 一律另核**; 未核实条目一律标「候选」
> 用途裁定（决策 58）: **小论文主线不改成蒸馏**; 本清单只服务 **Discussion / 大论文路线**

## 0 核验方法

- 元数据（题名 / 作者 / 年份 / arXiv ID / DOI / 版本日期）逐条拉自 **arXiv Atom API** 与 **OpenAlex Works API**; 被引数取自 OpenAlex `cited_by_count`（检索日 2026-09-20）。
- 原文证据句取自 **arXiv 摘要原文**逐字复制, 未改写润色。
- venue 列写 `arXiv preprint（待另核）` = 官方 API 中**无正式会刊 venue 记录**; 写具体期刊名 = OpenAlex 有 source 记录（仍以「另核」为最终口径）。
- **未执行**: 官方 CFP 之外未做任何投稿系统探测; 未下载 PDF; 未对外发送。

## 1 种子文献（全部已核）

| # | 题名 | 作者（首位 / 数） | 年 | arXiv / DOI | venue |
|---|---|---|---|---|---|
| 1 | Distilling the Knowledge in a Neural Network | Geoffrey E. Hinton / 3 | 2015 | arXiv:1503.02531 · DOI `10.48550/arxiv.1503.02531` | arXiv preprint（待另核） |
| 2 | Knowledge Distillation: A Survey | Jianping Gou / 4 | 2021 | DOI `10.1007/s11263-021-01453-z` | IJCV（OpenAlex 已核） |
| 3 | A Survey on Knowledge Distillation of Large Language Models | Xiaohan Xu / 9 | 2024 | arXiv:2402.13116 · DOI `10.48550/arxiv.2402.13116` | arXiv preprint（待另核） |

```bibtex
@article{hinton2015distilling,
  title   = {Distilling the Knowledge in a Neural Network},
  author  = {Hinton, Geoffrey E. and Vinyals, Oriol and Dean, Jeff},
  journal = {arXiv preprint arXiv:1503.02531}, year = {2015},
  doi     = {10.48550/arxiv.1503.02531}}

@article{gou2021kdsurvey,
  title   = {Knowledge Distillation: A Survey},
  author  = {Gou, Jianping and Yu, Baosheng and Maybank, Stephen and Tao, Dacheng},
  journal = {International Journal of Computer Vision}, year = {2021},
  doi     = {10.1007/s11263-021-01453-z}}

@article{xu2024kdsurveyllm,
  title   = {A Survey on Knowledge Distillation of Large Language Models},
  author  = {Xu, Xiaohan and Li, Ming and Tao, Chongyang and others},
  journal = {arXiv preprint arXiv:2402.13116}, year = {2024},
  doi     = {10.48550/arxiv.2402.13116}}
```

- **相关性** = 蒸馏方法的**定义与谱系基准**（Hinton = 软标签起点; Gou = 通用分类学; Xu = LLM 专用综述）。
- **原文证据句**（Hinton）: "A very simple way to improve the performance of almost any machine learning algorithm is to train many different models on the same data and then to average their predictions."
- **原文证据句**（Xu）: "Knowledge Distillation (KD) emerges as a pivotal methodology for transferring advanced capabilities from leading proprietary LLMs, such as GPT-4, to their open-source counterparts like LLaMA and Mistral."
- **DOI 纪律（实测）**: `10.1007/s11263-021-01453-c` 是 404 形态; **正确值为 `-01453-z`**。

## 2 教师侧底座技术报告（全部已核）

| # | 题名 | 作者（首位 / 数） | 年 | arXiv | venue |
|---|---|---|---|---|---|
| 4 | DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning | DeepSeek-AI / 200 | 2025 | arXiv:2501.12948（v2 2026-01-04） | arXiv preprint（待另核） |
| 5 | Qwen2.5 Technical Report | Qwen / 44 | 2024 | arXiv:2412.15115（v2 2025-01-03） | arXiv preprint（待另核） |
| 6 | The Llama 3 Herd of Models | Aaron Grattafiori / 561 | 2024 | arXiv:2407.21783（v3 2024-11-23） | arXiv preprint（待另核） |

```bibtex
@article{deepseekai2025r1,
  title   = {DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning},
  author  = {{DeepSeek-AI}},
  journal = {arXiv preprint arXiv:2501.12948}, year = {2025}}

@article{qwen2024qwen25,
  title   = {Qwen2.5 Technical Report},
  author  = {{Qwen Team}},
  journal = {arXiv preprint arXiv:2412.15115}, year = {2024}}

@article{grattafiori2024llama3herd,
  title   = {The Llama 3 Herd of Models},
  author  = {Grattafiori, Aaron and others},
  journal = {arXiv preprint arXiv:2407.21783}, year = {2024}}
```

- **相关性** = 蒸馏的**教师侧底座**（小论文不引其结论, 只用「教师模型族 + 蒸馏式数据配方」的事实坐标）。
- **原文证据句**（Qwen2.5）: "we have scaled the high-quality pre-training datasets from the previous 7 trillion tokens to 18 trillion tokens."
- **原文证据句**（Llama 3）: "Our largest model is a dense Transformer with 405B parameters and a context window of up to 128K tokens."
- **⚠ DOI 纪律（实测）**: DeepSeek-R1 与 Llama 3 的 arXiv DOI 经 OpenAlex `doi:` 检索为 **NOT_FOUND** ⇒ **引用一律只写 arXiv ID, 不写这两个 DOI**。DeepSeek-R1 另有 Nature 正式版（OpenAlex 已核）: "DeepSeek-R1 incentivizes reasoning in LLMs through reinforcement learning", DOI `10.1038/s41586-025-09422-z`, Nature, 2025-09-17, 100 署名 —— **venue 待另核**。

## 3 Agent 蒸馏（最高优先簇, 全部已核）

| # | 题名 | 作者（首位 / 数） | 年 | arXiv | venue |
|---|---|---|---|---|---|
| 7 | AgentDistill: Training-Free Agent Distillation with Generalizable MCP Boxes | Jiahao Qiu / 14 | 2025 | arXiv:2506.14728 | arXiv preprint（待另核） |
| 8 | Structured Agent Distillation for Large Language Model | Jun Liu / 13 | 2025 | arXiv:2505.13820 | arXiv preprint（待另核） |
| 9 | Chain-of-Agents: End-to-End Agent Foundation Models via Multi-Agent Distillation and Agentic RL | Weizhen Li / 30 | 2025 | arXiv:2508.13167 | arXiv preprint（待另核） |

```bibtex
@article{qiu2025agentdistill,
  title   = {AgentDistill: Training-Free Agent Distillation with Generalizable MCP Boxes},
  author  = {Qiu, Jiahao and others},
  journal = {arXiv preprint arXiv:2506.14728}, year = {2025}}

@article{liu2025structuredagent,
  title   = {Structured Agent Distillation for Large Language Model},
  author  = {Liu, Jun and others},
  journal = {arXiv preprint arXiv:2505.13820}, year = {2025}}

@article{li2025chainofagents,
  title   = {Chain-of-Agents: End-to-End Agent Foundation Models via Multi-Agent Distillation and Agentic RL},
  author  = {Li, Weizhen and others},
  journal = {arXiv preprint arXiv:2508.13167}, year = {2025}}
```

- **相关性（最高优先）** = 本仓「大论文路线」最贴题的一簇: **agent 蒸馏 vs 任务/轨迹蒸馏**, 与长流程 agent 评测（多步工具调用 + 检查点树）同构。
- **原文证据句**（AgentDistill，逐字，最贴题的一句）: "While knowledge distillation has become a mature field for compressing large language models (LLMs) into smaller ones by aligning their outputs or internal representations, the distillation of LLM-based agents, which involve planning, memory, and tool use, remains relatively underexplored."
- **原文证据句**（Structured Agent Distillation）: "our method segments trajectories into [REASON] and [ACT] spans, applying segment-specific losses to align each component with the teacher's behavior."

## 4 多教师 / 集成蒸馏（全部已核）

| # | 题名 | 作者（首位 / 数） | 年 | arXiv | venue |
|---|---|---|---|---|---|
| 10 | Exploring Knowledge Purification in Multi-Teacher Knowledge Distillation for LLMs | Ruihan Jin / 8 | 2026 | arXiv:2602.01064 | arXiv preprint（待另核） |
| 11 | Counteraction-Aware Multi-Teacher On-Policy Distillation for General Capability Recovery with Domain Preservation | Tianlei Chen / 6 | 2026 | arXiv:2605.27115 | arXiv preprint（待另核） |
| 12 | MOPD: Multi-Teacher On-Policy Distillation for Capability Integration in LLM Post-Training | Wenhan Ma / 13 | 2026 | arXiv:2606.30406 | arXiv preprint（待另核） |
| 13 | Filter, Then Reweight: Rethinking Optimization Granularity in On-Policy Distillation | Yuying Li / 9 | 2026 | arXiv:2606.02684 | arXiv preprint（待另核） |
| 14 | ACTD: Anchor-Based Cross-Tokenizer Distillation with Residual Regularization | Huiyi Zhang / 7 | 2026 | arXiv:2608.29662 | arXiv preprint（待另核） |

```bibtex
@article{jin2026purification,
  title   = {Exploring Knowledge Purification in Multi-Teacher Knowledge Distillation for LLMs},
  author  = {Jin, Ruihan and others},
  journal = {arXiv preprint arXiv:2602.01064}, year = {2026}}

@article{chen2026counteraction,
  title   = {Counteraction-Aware Multi-Teacher On-Policy Distillation for General Capability Recovery with Domain Preservation},
  author  = {Chen, Tianlei and others},
  journal = {arXiv preprint arXiv:2605.27115}, year = {2026}}

@article{ma2026mopd,
  title   = {MOPD: Multi-Teacher On-Policy Distillation for Capability Integration in LLM Post-Training},
  author  = {Ma, Wenhan and others},
  journal = {arXiv preprint arXiv:2606.30406}, year = {2026}}

@article{li2026fireopd,
  title   = {Filter, Then Reweight: Rethinking Optimization Granularity in On-Policy Distillation},
  author  = {Li, Yuying and others},
  journal = {arXiv preprint arXiv:2606.02684}, year = {2026}}

@article{zhang2026actd,
  title   = {ACTD: Anchor-Based Cross-Tokenizer Distillation with Residual Regularization},
  author  = {Zhang, Huiyi and others},
  journal = {arXiv preprint arXiv:2608.29662}, year = {2026}}
```

- **相关性** = 多教师 / 集成蒸馏（导师方向「多小模型蒸馏大模型」的最近方法面）。
- **原文证据句**（Jin）: "traditional distillation approaches face challenges related to knowledge conflicts and high resource demands, particularly when leveraging multiple teacher models."
- **原文证据句**（Chen）: "Recent Multi-Teacher On-Policy Distillation (MOPD) pipelines recover model capabilities by supervising student-generated trajectories with teacher feedback, but typically assume teacher-aligned prompt coverage ..."
- **⚠ 未核实（标候选, 不入引用）**: 「MOPD 系列由小米 & 北大提出」的**机构归属**及非官方转述的编号先后关系 —— **未经官方源核实**。

## 5 蒸馏后的评测协议 / LLM-as-Judge 实证（全部已核）

| # | 题名 | 作者（首位 / 数） | 年 | arXiv | venue |
|---|---|---|---|---|---|
| 15 | Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena | Lianmin Zheng / 13 | 2023 | arXiv:2306.05685 · DOI `10.48550/arxiv.2306.05685` | arXiv preprint（会议版待另核） |
| 16 | A Survey on LLM-as-a-Judge | Jiawei Gu / 16 | 2024 | arXiv:2411.15594 | arXiv preprint（另有 The Innovation 版 DOI `10.1016/j.xinn.2025.101253`, 待另核） |
| 17 | LLMs Cannot Reliably Judge (Yet?): A Comprehensive Assessment on the Robustness of LLM-as-a-Judge | Songze Li / 9 | 2025 | arXiv:2506.09443 | arXiv preprint（待另核） |
| 18 | TICKing All the Boxes: Generated Checklists Improve LLM Evaluation and Generation | Jonathan Cook / 5 | 2024 | arXiv:2410.03608 | arXiv preprint（待另核） |

```bibtex
@article{zheng2023mtbench,
  title   = {Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena},
  author  = {Zheng, Lianmin and Chiang, Wei-Lin and Sheng, Ying and others},
  journal = {arXiv preprint arXiv:2306.05685}, year = {2023}}

@article{gu2024judgesurvey,
  title   = {A Survey on LLM-as-a-Judge},
  author  = {Gu, Jiawei and others},
  journal = {arXiv preprint arXiv:2411.15594}, year = {2024}}

@article{li2025robustjudge,
  title   = {LLMs Cannot Reliably Judge (Yet?): A Comprehensive Assessment on the Robustness of LLM-as-a-Judge},
  author  = {Li, Songze and others},
  journal = {arXiv preprint arXiv:2506.09443}, year = {2025}}

@article{cook2024tick,
  title   = {TICKing All the Boxes: Generated Checklists Improve LLM Evaluation and Generation},
  author  = {Cook, Jonathan and others},
  journal = {arXiv preprint arXiv:2410.03608}, year = {2024}}
```

- **相关性** = 「蒸馏有没有退化」的**评测协议侧证据**: MT-Bench 给出 judge 三类**已知偏差**（position / verbosity / self-enhancement）, 与「评测器自身盲区 / 判据相对性」同构; TICK = 清单式评测（与检查点树同族）。
- **原文证据句**（MT-Bench）: "We examine the usage and limitations of LLM-as-a-judge, including position, verbosity, and self-enhancement biases, as well as limited reasoning ability ..."
- **原文证据句**（Survey）: "the emergence of \"LLM-as-a-Judge,\" where LLMs are employed as evaluators for complex tasks."

## 6 GTA-2（本仓 hbkeyan 已引条目, 同名歧义已判）

| 题名 | 作者（首位 / 数） | 年 | arXiv | venue |
|---|---|---|---|---|
| GTA-2: Benchmarking General Tool Agents from Atomic Tool-Use to Open-Ended Workflows | Jize Wang / 10 | 2026 | arXiv:2604.15715 | arXiv preprint（待另核） |

```bibtex
@article{wang2026gta2,
  title   = {GTA-2: Benchmarking General Tool Agents from Atomic Tool-Use to Open-Ended Workflows},
  author  = {Wang, Jize and others},
  journal = {arXiv preprint arXiv:2604.15715}, year = {2026}}
```

- **⚠ 同名歧义已判（实测）**: 另有 **arXiv:2609.09808**「GTA-2: A Multi-VLM Framework for Synthesizing Robot Manipulation Skills via Grounded Task Axes」= **机器人操作**方向, **与本仓无关, 不得混引**。本仓要的是 **2604.15715**。
- **相关性** = 与蓝图「hierarchical checkpoints + 缺陷可见性」**同机制家族**: 其提出 **recursive checkpoint-based evaluation**（把目标分解为可验证子目标）, 并给出 **14.39% workflow 成功率** 对照数字。
- **原文证据句**: "we propose a recursive checkpoint-based evaluation mechanism that decomposes objectives into verifiable sub-goals ... top models achieving only 14.39% success."

## 7 会议窗口（只写已核日期, 其他不写死）

用户 2026-09-20 裁定（决策 58）: **先按两个已核日期排**。

| 会议 / 通道 | 关键日期 | 官方来源（本次实取） |
|---|---|---|
| **ARR**（ACL Rolling Review）October 2026 cycle | **Submission 2026-10-12**（reviewer registration 10-14; reviews due 11-16; author response 11-24~11-30; meta-review 12-17; cycle end 12-20） | `https://aclrollingreview.org/dates` |
| **WWW 2027**（The Web Conference, Dublin） | Research track **abstract 2026-10-18 / full paper 2026-10-25** | `https://www2027.thewebconf.org/`（New & Updates, 28 Aug 2026） |

- **其他会议一律不写死**（未取得官方 CFP 日期前不进任何排期件）。
- 附带已核（**只记不排**）: WWW 2027 short paper abstract 2026-11-09 / submission 2026-11-16; workshop proposal 2026-09-28; tutorial proposal 2026-10-19; Seoul Test of Time nomination 2026-10-14。

## 8 全部未核实项（标候选, 不得入引用）

1. **所有 venue / 会议期刊字段** —— 除 §1 的 IJCV 与 §5 的 MT-Bench / Gu 两条另注外, 其余 venue **均待另核**。
2. **MOPD 系列的机构归属**及编号先后关系 —— 未经官方源核实。
3. **会议窗口外**的其他会议日期 **未核**; 未做官方 CFP 之外的投稿系统探测。
4. **本清单不构成论文引用**: 入稿前须按 `citation-management` 流程二次核验, 且**不经用户确认不得进 `docs/33` / `docs/34`**（决策 58）。