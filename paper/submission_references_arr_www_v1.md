# 小论文投稿引用映射与 BibTeX（ARR / WWW v1）

> 状态：投稿准备件，不是新增文献综述 | 更新：2026-10-03
> 来源：`paper/teacher_review_draft_v1.md` References + `paper/references_v0.md`
> 纪律：只收录主稿已引用且仓内已核验的条目；不新增论文、不补猜 venue、不写未核 CFP。

## 1 主稿引用映射

| 主稿行文标签 | cite key | 标识 | venue 口径 |
|---|---|---|---|
| Amrhein et al., 2022 | `amrhein2022aces` | arXiv:2210.15615 | arXiv preprint |
| Amrhein et al., 2023 | `amrhein2023aceswmt` | arXiv:2311.01153 | arXiv preprint |
| Moghe et al., 2024 | `moghe2024acesjournal` | arXiv:2401.16313 | arXiv preprint |
| Deviyani and Diaz, 2025 | `deviyani2025contextual` | arXiv:2503.19828 | arXiv preprint |
| Kendiukhov, 2026 | `kendiukhov2026ranking` | arXiv:2603.03493 | arXiv preprint |
| Du et al., 2026 | `du2026promptranking` | arXiv:2606.24381 | arXiv preprint |
| Ross et al., 2024 | `ross2024goodmetric` | arXiv:2412.13989 | arXiv preprint |
| Fan et al., 2026 | `fan2026agentprocessbench` | arXiv:2603.14465 | arXiv preprint |
| Chung et al., 2026 | `chung2026webstep` | arXiv:2606.15673 | arXiv preprint |
| Wang et al., 2026 | `wang2026gta2` | arXiv:2604.15715 | arXiv preprint |
| Cho et al., 2025 | `cho2025metamorphic` | arXiv:2511.02108 | arXiv preprint |
| Tan et al., 2026 | `tan2026agentchaos` | arXiv:2608.06790 | arXiv preprint |
| Zheng et al., 2023 | `zheng2023judge` | arXiv:2306.05685 | arXiv preprint |
| Li et al., 2025a | `li2025scoringbias` | arXiv:2506.22316 | arXiv preprint |
| Li et al., 2025b | `li2025robustjudge` | arXiv:2506.09443 | arXiv preprint |


## 2 投稿版 BibTeX（15 条）

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

@article{fan2026agentprocessbench,
  title   = {AgentProcessBench: Diagnosing Step-Level Process Quality in Tool-Using Agents},
  author  = {Fan, Shengda and Ye, Xuyan and Huo, Yupeng and others},
  journal = {arXiv preprint arXiv:2603.14465}, year = {2026}}

@article{chung2026webstep,
  title   = {Where Did It Go Wrong? Process-Level Evaluation of Web Agents with Semantic State Tracking},
  author  = {Chung, Jiwan and Byun, JiHyuk and Vineet, Vibhav and Kim, Seon Joo},
  journal = {arXiv preprint arXiv:2606.15673}, year = {2026}}

@article{wang2026gta2,
  title   = {GTA-2: Benchmarking General Tool Agents from Atomic Tool-Use to Open-Ended Workflows},
  author  = {Wang, Jize and others},
  journal = {arXiv preprint arXiv:2604.15715}, year = {2026}}

@article{cho2025metamorphic,
  title   = {Metamorphic Testing of Large Language Models for Natural Language Processing},
  author  = {Cho, Steven and Ruberto, Stefano and Terragni, Valerio},
  journal = {arXiv preprint arXiv:2511.02108}, year = {2025}}

@article{tan2026agentchaos,
  title   = {AgentChaos: Chaos Engineering for Agent Systems via Programmatic Fault Injection},
  author  = {Tan, Gou and Sun, Zhensu and Shi, Jieke and others},
  journal = {arXiv preprint arXiv:2608.06790}, year = {2026}}

@article{zheng2023judge,
  title   = {Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena},
  author  = {Zheng, Lianmin and Chiang, Wei-Lin and Sheng, Ying and others},
  journal = {arXiv preprint arXiv:2306.05685}, year = {2023}}

@article{li2025scoringbias,
  title   = {Evaluating Scoring Bias in LLM-as-a-Judge},
  author  = {Li, Qingquan and Dou, Shaoyu and Shao, Kailai and Chen, Chao and Hu, Haixiang},
  journal = {arXiv preprint arXiv:2506.22316}, year = {2025}}

@article{li2025robustjudge,
  title   = {LLMs Cannot Reliably Judge (Yet?): A Comprehensive Assessment on the Robustness of LLM-as-a-Judge},
  author  = {Li, Songze and Xu, Chuokun and Wang, Jiaying and others},
  journal = {arXiv preprint arXiv:2506.09443}, year = {2025}}
```

## 3 投稿前引用检查

消歧规则：同一作者年份按题名/引用顺序固定后不得漂移；本稿 `2025a = scoringbias`、`2025b = robustjudge`。GTA-2 只使用 `arXiv:2604.15715`；同名机器人操作论文 `arXiv:2609.09808` 属显式排除项，不进入 §1 映射或 BibTeX。

1. venue 模板确定后只调整 BibTeX entry type、作者缩写和引用顺序；标识与题名不得无证据改动。
2. 未核 venue 继续写 `arXiv preprint`；不得把 ICSME/COLUM/KD 候选 venue 直接升级为已核。
3. 正文与 References 的 15 条引用集合必须一一对应；新增或删除引用需重跑 claim/引用审计。
4. 专利未确认前，本件只随内部投稿准备包流转，不外发。
