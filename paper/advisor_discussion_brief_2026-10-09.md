# 导师讨论 Brief：Stage E 证据边界与下一块独立证据

> 状态: `ADVISOR_DISCUSSION_DRAFT / NOT_APPROVED / INTERNAL_ONLY`
> 日期: 2026-10-09
> 范围: 仅供导师内部讨论；不得投稿、上传 arXiv、公开代码或外发。
> 事实口径: `COMPLETE_FOR_FORMAL_NEGATIVE_PATH_B` 不等于 Evaluate-Distill-Evolve 全闭环完成。

## A. 30 秒研究故事

当前 Stage E 研究的不是“怎样造一个更强的检测器”，而是审计长周期文档 AI 的评价协议是否具有 measurement validity。论文把三个常被总分混淆的构念分开：checkpoint-level visibility、protocol-level detection、equivalence-dependent harmfulness。层级 checkpoint forest 只是让证据可分解、可追溯的 evidence instrument，不是已经证明更敏感或更准的算法。当前最核心的发现是：可见不等于检出，原始协议差异在 matched-FPR 校准后消失，因此不能把 hierarchy 写成天然的判别优势。

## B. 已成立的关键结论

1. 冻结公开表格语料包含 **95 tables / 118 synthetic injections**；checkpoint-level visibility 为 **96/118**。
2. OCR-like perturbations 在五个阈值下均为 **0/13 visible**，说明当前 evaluator 对该缺陷族存在明确盲区。
3. flat / hierarchical 的 raw protocol gap 不能解释为 discriminability；在 matched-FPR 下，当前 single-responsive-leaf 情形中两种协议为 affine equivalent，protocol-difference interval 为 `[0,0]`。
4. hierarchy 的已成立价值是 evidence decomposition 和 per-family visibility reporting；当前没有成立额外 detection sensitivity 或 localization gain。
5. PSO control 仅保留为 null/control evidence，不作为论文贡献。

## C. 当前最重要的 evidence ceiling

- 证据来自单一公开表格域。
- 缺陷由 synthetic perturbations 产生。
- 当前只有一个 scored leaf 对注入输入响应，因此 localization 仍不成立。
- changed-pipeline second dataflow 尚未形成可用证据。
- independent second scorer 尚未闭合；已停止的 step-level route 测量对象不同。
- harmfulness 是 criterion-dependent construct，不能脱离 equivalence definition 解释。

## D. 大论文 Evaluate-Distill-Evolve 状态

| 阶段 | 当前状态 | 允许的表述 |
|---|---|---|
| Evaluate | mature | Stage E 已有成熟的 measurement-validity / meta-evaluation 证据 |
| Distill | `DATA_NO_GO / RQ2 NOT_IDENTIFIED` | 数据与 same-sample bridge 未满足，不能写成蒸馏结果 |
| Evolve | mechanism evidence only | 只有机制、协议与回滚设计，不是持续安全提升结果 |

## E. 请导师拍板的两个问题

### 1. 下一块独立证据优先什么？

- **Option M:** multi-leaf / multi-stage injection
- **Option D:** changed-pipeline second dataflow

### 2. harmfulness 以什么定义为主？

- **Option A:** canonical equivalence
- **Option B:** reader-referent equivalence
- **Option C:** 两者作为 parallel constructs 分开报告

> 本 Brief 只用于决策准备，不修改现有 harmfulness 定义、不重新标注、不改 frozen claim boundary。
