# 相关工作 v3（m0_lit 五篇全文接入, 三簇补强）

> 状态: 草稿 v3.1（Voyager/MemGPT 在线核验, 待复核清零; 承 v3） | 更新: 2026-08-29 | 取代: v2（v1/v2 保留备查）
> 语料: ~/wzh/research/m0_lit/（fulltext ×5 + batch 元数据）

## 1 簇二补强 · agent 记忆: 从机制谱系到评测谱系

v2 已列机制谱系（Mem0 事实 / AWM 过程 / MemGPT 分层 / Voyager 技能 / ExpeL 经验）。m0_lit
补上**评测与巩固**两支, 使簇二在论文里形成"机制 × 评测"双轴:

1. **MemoryAgentBench**（hu2025memoryagentbench）: 记忆智能体四核心能力 = 精确检索 /
   测试时学习 / 长程理解 / 选择性遗忘; 现有系统无一全能。**与本文对位**: 选择性遗忘的
   工程对偶正是门控的回归约束（collateral < −ε 拒收 = 不让有害经验入记忆）; 本文基线窗
   的三基线 null 可置于该评测框架下讨论（记忆质量 ≠ 记忆存在）。
2. **Evo-Memory**（wei2025evomemory）: 首个面向测试时学习的自进化记忆基准, 区分"被动检索
   应答"与"跨任务流积累复用"。**与本文对位**: VGRM 属后者（规则库跨表积累）, 且本文给出
   积累有界的保证（命题 1）——基准系只度量能力, 本文补充安全性维度。
3. **RecMem**（dai2026recmem）: 基于循环的记忆巩固, 把语义簇的短期交互固化为长期记忆
   （认知科学 transient→long-term 对映）。**与本文对位**: 固化（建议→规则）即巩固; 本文增量
   = 巩固的**准入判据**（gain≥τ ∧ collateral≥−ε）与回归界, RecMem 系无此约束。

## 2 簇三补强 · 自进化: 参数侧与规则侧的分野

1. **Q-Evolve**（zhang2026qevolve, ICML）: in-distribution RL 自进化——自动过程奖励标注 +
   策略学习共进化（AlfWorld/WebShop/ScienceWorld）。**与本文对位**: 参数侧自进化的代表;
   本文 = 规则侧免训练对偶。结构同源性值得明写: 他们的过程奖励 ↔ 本文 gain/collateral
   都是"步级监督信号", 区别在信号作用于参数还是显式规则库——后者可审计、可回滚、零训练
   成本, 代价是表达能力受限于规则形态。
2. **Self-Evolving Coding Agents 综述**（zhou2026secoding）: 对象中心分类学（框架/记忆/
   技能/工具/模型/协作六类更新对象）。**与本文对位**: 本文规则库+技能库 = 其"记忆+技能"
   对象类; 门控固化 = 该分类学下带准入约束的更新策略实例。投稿定位用此综述作分类坐标,
   声明本文在"文档管线"这一新应用域的实例化贡献。

## 3 BibTeX 增量（五篇, 作者经 OpenAlex 实查 08-29, arXiv 预印本）

```bibtex
@article{hu2025memoryagentbench,
  title   = {Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions},
  author  = {Hu, Yannan and Wang, Yu and McAuley, Julian},
  journal = {arXiv preprint arXiv:2507.05257}, year = {2025}}

@article{wei2025evomemory,
  title   = {Evo-Memory: Benchmarking LLM Agent Test-time Learning with Self-Evolving Memory},
  author  = {Wei, Tianxin and Sachdeva, Noveen and Coleman, Benjamin and He, Zhankui and Bei, Yuanchen and Ning, Xuying},
  journal = {arXiv preprint arXiv:2511.20857}, year = {2025}}

@article{dai2026recmem,
  title   = {RecMem: Recurrence-based Memory Consolidation for Efficient and Effective Long-Running LLM Agents},
  author  = {Dai, Zijie and Deng, Shiyuan and Guan, Sheng and Tian, Yizhou and Yao, Xin and Yan, Xiao},
  journal = {arXiv preprint arXiv:2605.16045}, year = {2026}}

@inproceedings{zhang2026qevolve,
  title     = {Self-evolving LLM agents with in-distribution Optimization},
  author    = {Zhang, Yudi and Fang, Meng and Chen, Zhenfang and Pechenizkiy, Mykola},
  booktitle = {ICML}, year = {2026},
  note      = {arXiv:2606.07367}}

@article{zhou2026secoding,
  title   = {Self-Evolving Coding Agents},
  author  = {Zhou, Hao and Hu, Haichuan and Shang, Ye and Zhang, Quanjun},
  journal = {arXiv preprint arXiv:2608.03392}, year = {2026}}
```

## 4 BibTeX 增量二（Voyager / MemGPT 在线核验, 08-29 待复核清零）

```bibtex
@article{wang2023voyager,
  title   = {Voyager: An Open-Ended Embodied Agent with Large Language Models},
  author  = {Wang, Guanzhi and Xie, Yuqi and Jiang, Yunfan and Mandlekar, Ajay and Xiao, Chaowei and others},
  journal = {arXiv preprint arXiv:2305.16291}, year = {2023},
  note    = {OpenAlex 在线核验 08-29}}

@article{packer2023memgpt,
  title   = {MemGPT: Towards LLMs as Operating Systems},
  author  = {Packer, Charles and Wooders, Sarah and Lin, Kevin and Fang, Vivian and Patil, Shishir G.},
  journal = {arXiv preprint arXiv:2310.08560}, year = {2023},
  note    = {OpenAlex 在线核验 08-29}}
```

## 5 三簇现状自查

- 簇一（变异测试）: v2 已完备, 本批无增量
- 簇二（记忆）: 机制 × 评测双轴成立（+3 篇）
- 簇三（自进化）: 参数侧/规则侧分野 + 分类学坐标成立（+2 篇）
- 全部 13 条引文: CrossRef 实查 4 / OpenAlex 实查 7 / **待复核 0（08-29 清零）**
