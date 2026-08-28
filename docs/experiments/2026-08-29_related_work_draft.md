# 相关工作检索与综述节草稿（论文线并行件, 零端点）

> 状态: 草稿 | 更新: 2026-08-29 | 检索口径: CrossRef API 实查（08-29 00:2x, GB10）; arXiv 条目因网络限制未能在线复核, 已显式标注"待复核"
> 三簇: 变异测试谱系 / agent 记忆（Mem0·AWM·经验检索） / training-free 自进化

## 1 簇一 · 变异测试谱系（盲锥章的方法学源头）

变异测试以"受控注入变异 + 判别是否被杀死"度量测试充分性。谱系起点为 DeMillo 等 1978 年的
测试数据选择工作（变异思想的提出）; Jia & Harman 2011 的 TSE 综述系统化了变异算子、
变异充分性与等价变异（等价变异对映 = 本文盲锥命题 2 假阳性校正项的直接概念来源）。
本文移植: 变异对象从代码语句换成文档表头漂移, 判别信号从测试断言换成管线检查点响应差,
"杀死率"换成判别率谱, 盲区 = 判别率塌缩方向。

## 2 簇二 · agent 记忆机制（小 A 基线对照族）

Mem0（2025）给出生产级 agent 的可扩展长期记忆（抽取-检索-更新闭环）; AWM（Wang et al.,
NeurIPS 2024）把记忆单元从事实升级为可迁移的工作流/过程; 经验检索一族（用户口径 "ExpRAG",
以 ExpeL（AAAI 2024）为已核实锚点——该词无单一经典出处, 待侧线核定指称）主张从轨迹中
抽取经验供后续检索复用。本文关系: 三族构成小 A 的基线对照（事实记忆/过程记忆/静态示例）,
08-28 基线窗实测三基线与 no-gate 不可分（ΔH 逐位 0）——在表头映射任务上, 记忆机制的
增量让位于显式规则库, 该 null 是本文的实证贡献之一而非背景。

## 3 簇三 · training-free 自进化（VGRM 的定位坐标）

自进化综述谱系（Zhang et al. 2024 综述, 待复核）将免训练的反馈固化与参数内化（RL/SFT）
分列两级。本文 VGRM = 免训练一级: 建议经门控 G(τ,ε) 固化为显式规则（命题 1 有界回归保证）,
RL 内化为预留钩子（bandit 门 → DPO 路线, 首批偏好对已生成 60 对）。定位主张: 门控价值 =
f(碰撞暴露 × 单次碰撞危害)（Round 3 D1 裁定, 对抗臂实证）。

## 4 BibTeX（CrossRef 实查条目含 doi; arXiv 条目标 [待复核]）

```bibtex
@article{demillo1978hints,
  title   = {Hints on Test Data Selection: Help for the Practicing Programmer},
  author  = {DeMillo, Richard A. and Lipton, Richard J. and Sayward, Frederick G.},
  journal = {Computer}, year = {1978},
  doi     = {10.1109/C-M.1978.218136}}

@article{jia2011mutation,
  title   = {An Analysis and Survey of the Development of Mutation Testing},
  author  = {Jia, Yue and Harman, Mark},
  journal = {IEEE Transactions on Software Engineering},
  volume  = {37}, number = {5}, year = {2011},
  doi     = {10.1109/TSE.2010.62}}

@inproceedings{wang2024awm,
  title     = {Agent Workflow Memory},
  author    = {Wang, Zora Zhiruo and Mao, Jiayuan and Fried, Daniel and Neubig, Graham},
  booktitle = {NeurIPS}, year = {2024},
  note      = {arXiv:2409.07429 [待复核]}}

@article{mem0_2025,
  title   = {Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory},
  author  = {{Mem0 Research Team}},
  journal = {arXiv preprint arXiv:2504.19413}, year = {2025},
  note    = {[待复核, 作者全名单待补]}}

@inproceedings{zhao2024expel,
  title     = {ExpeL: LLM Agents Are Experiential Learners},
  author    = {Zhao, Andrew and Huang, Daniel and Xu, Quentin and others},
  booktitle = {Proceedings of the AAAI Conference on Artificial Intelligence},
  volume    = {38}, number = {17}, year = {2024},
  doi       = {10.1609/aaai.v38i17.29936}}

@article{zhang2024selfevolution,
  title   = {A Survey on Self-Evolution of Large Language Models},
  author  = {Zhang, Zhexin and Xue, Zhengxiao and others},
  journal = {arXiv preprint arXiv:2404.01754}, year = {2024},
  note    = {[待复核, 作者全名单待补]}}
```

## 5 欠账与衔接

- arXiv 三条（AWM/Mem0/自进化综述）待网络可达时在线复核（GB10 对 arxiv.org 不通, 本次经实知的元数据草录, 已逐条标注）
- "ExpRAG" 指称待侧线核定（现以经验检索族 + ExpeL 锚点代称）
- 盲锥章 v1 与小 A 方法章引用本件 §4 键名
