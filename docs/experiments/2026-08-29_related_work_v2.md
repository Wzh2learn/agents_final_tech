# 相关工作 v2（Phase 2 扩展: Voyager 技能库 / MemGPT / mutation score 方法论补强）

> 状态: 草稿 v2（承 v1 三簇, 补三块） | 更新: 2026-08-29 | 检索: CrossRef 实查（08-29 01:1x）+ arXiv 条目标待复核（网络限制）
> 衔接: 论文三创新点逐簇挂钩——I1 门控固化 ↔ 记忆谱系+自进化; I2 盲锥 ↔ 变异测试谱系; I3 多模型泛化 ↔ 谱系背景

## 1 v1 三簇承继（见 2026-08-29_related_work_draft.md, 此处增量）

## 2 增量一 · 技能库谱系（Voyager）与本文规则库的对照

Voyager（wang2023voyager, arXiv 待复核）首次把"可执行技能持续增长"作为开放域 agent 的核心机制:
技能 = 可复用代码单元, 经验证后入库, 检索调用。本文规则库与技能库同构于"经验的外显化+检索复用",
但有两点本质差异, 恰是贡献所在:
1. **准入机制**: Voyager 技能入库靠执行成功反馈（无回归概念）; 本文规则固化经门控 G(τ,ε)
   的**回归约束**（collateral 分量）——对抗臂实证（门拒高置信错列 100%）说明准入约束是
   外显记忆在对抗输入下不劣化的关键。
2. **单元粒度**: 技能 = 过程（how-to）; 规则 = 声明式映射（what-is）。AWM 的过程记忆介于二者之间,
   本文基线窗实测: 过程记忆（awm）与事实记忆（mem0）在声明式任务上均无增量——任务结构决定
   记忆形态的收益边界, 该观察可作讨论节的"记忆形态-任务结构匹配"论点。

## 3 增量二 · MemGPT 与记忆分层谱系

MemGPT（packer2023memgpt, arXiv 待复核）把操作系统的分页思想引入 LLM 上下文管理
（工作记忆/外存分层 + 自主换页）。本文未采用分层记忆, 因表头映射的"记忆"天然可全量外显
（规则库可枚举可读）, 无上下文容量压力; 但 MemGPT 的"自主记忆管理"与本文预留的学习门
（bandit 决定何时固化）共享同一问题意识——何时写记忆。讨论节可引为"记忆管理策略"坐标。

## 4 增量三 · mutation score 方法论（盲锥章度量学锚点）

变异测试中变异分数（mutation score = 被杀变异体占比）长期作为测试充分性度量
（jia2011mutation; 变异分数与测试充分性的相关性实证见 felbinger2016mutation, CrossRef 实查）。
本文的移植与偏移:
1. 变异分数 → **判别率谱**: 从单一标量升级为按缺陷类型的谱（六类注入分类学）, 盲区 = 谱的塌缩方向;
2. 测试充分性 → **管线盲区度量**: 度量对象从测试套件换成生产管线本身（自我审计）;
3. 等价变异问题 → **等价变异对映**（盲锥命题 2 校正项, 留白）;
4. 本文新增: **吸收机制分解**（匹配层兜底路径的 match_tier 分解）——变异测试谱系无此概念,
   因代码变异无"被静默吞掉"的对应物; 这是文档管线特有的失效模式, 构成方法学增量。

## 5 BibTeX 增量（v1 §4 基础上追加）

```bibtex
@article{wang2023voyager,
  title   = {Voyager: An Open-Ended Embodied Agent with Large Language Models},
  author  = {Wang, Guanzhi and Xie, Yuqi and Jiang, Yunfan and others},
  journal = {arXiv preprint arXiv:2305.16291}, year = {2023},
  note    = {[待复核]}}

@article{packer2023memgpt,
  title   = {MemGPT: Towards LLMs as Operating Systems},
  author  = {Packer, Charles and Wooders, Sarah and Lin, Kevin and others},
  journal = {arXiv preprint arXiv:2310.08560}, year = {2023},
  note    = {[待复核]}}

@inproceedings{felbinger2016mutation,
  title     = {Empirical Study of Correlation Between Mutation Score and Model Inference Based Test Suite Adequacy Criteria},
  author    = {Felbinger, Stefan and Wotawa, Franz and Nica, Mihai},
  booktitle = {IEEE/ACM International Workshop on Mutation Analysis (Mutation)},
  year      = {2016}, doi = {10.1145/2896921.2896923}}
```

## 6 覆盖度自查（对照论文三创新点）

- I1 门控固化: 记忆谱系（Mem0/AWM/MemGPT/Voyager/ExpeL）+ 自进化谱系（综述）+ 学习门（bandit→DPO 背景）✓
- I2 盲锥: 变异测试谱系（起源+综述+度量学）+ 吸收机制增量声明 ✓
- I3 多模型泛化: 谱系背景够用, 无专门相关工作（如实注记: 小模型矩阵属实验贡献非方法谱系）
- 欠账: arXiv 五条待在线复核; ExpRAG 指称仍待侧线核定
