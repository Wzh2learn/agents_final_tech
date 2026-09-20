# 批 #8-B 双模型 Loop C 审稿 — 差异对照表（不合并结论, 不替用户仲裁）

> 状态: 对照表（2026-09-21, Loop D 主线程; **只做差异对照, 不做仲裁**）
> 两份独立报告: [qwen3.8-max](./2026-09-21_loopc_review_qwen3.8-max.md)（24 134 B / 162 行） · [deepseek-v4-pro](./2026-09-21_loopc_review_deepseek-v4-pro.md)（21 162 B / 253 行）
> 运行环境: **均在 GB10 上跑**（`claude --bare --model <m> -p "$(cat <prompt>)"`, 两独立会话, 无共享上下文, 无 resume）
> 统一 prompt: `/tmp/loopc_dual_review/loopc_dual_review_prompt.md`, sha256 `485b9462fdabb9326dac6c8c081430859a9ccdbe79a0bfd13620c546346847eb`（768 B, LF-only）
> 前置: 连通性验证 `claude --bare --model deepseek-v4-pro -p "Reply with exactly: DS_OK"` → 输出 `DS_OK`, exit 0

## 1 总体判定

| 维度 | qwen3.8-max | deepseek-v4-pro | 是否一致 |
|---|---|---|---|
| 总体判定 | **REVISE** | **REVISE**（"修改后可达 ACCEPT"） | **一致** |
| Blocking 数 | 2 | 2 | 一致 |
| Major 数 | 4 | 5 | 接近（deepseek 多 1） |
| Minor 数 | 10 | 5 | 差异（qwen 更细） |
| 是否要求新实验 | 否（均为文本修订） | 否（均为文本修订） | 一致 |

## 2 Blocking 级差异对照（关键：两模型独立命中同一段）

| # | qwen3.8-max | deepseek-v4-pro |
|---|---|---|
| B1 | **hinge 叶"缺失证据给 0 分"的方法描述与冻结配置直接矛盾** — 实测 `config/eval_checkpoint_trees.json`: 5 个 hinge 叶中仅 `parse.doc.ok` 的 `missing_score=0`, 另 4 个 hinge 叶（`qa.retrieval.source_required` / `qa.numeric.exact` / `qa.numeric.number_grounding` / `qa.refusal.deterministic`）均为 5; 反向也不成立（4 个**非** hinge 的 parse 叶全为 0）。**真实策略是按树分**（parse 树全 0 / qa 树全 5）。落点 = draft :62-63 / :122-127 / :533 与对位表 §2①。风险 = **高**（读者顺论文给的 config 指针第一步即可证伪正文）。 | **S1 "hierarchical evaluation" 与 S4 同名异义, 引发数字矛盾** — S1 的 75/95 实为 **flat** 协议（`t1` E1.2_flat）, 96/118 不匹配任何协议层数字（flat 85 / hierarchical 13）, 实为**第三种口径**（检查点级可见性）。风险 = **desk-reject risk**。 |
| B2 | **S1 第二段把 flat/判别臂口径的头条数字冠以 "hierarchical"** — 与同节第四段（13/118）及 Table 1（E1.2 flat 75/95）直接冲突; 另 96/118（未被吸收）与 85/118（过阈值）是两个口径未区分。风险 = **高**。 | **S1 先亮 75/95+96/118、S4 才揭示层级协议仅 13/118 ⇒ 选择性呈现印象** — 叙事弧线令审稿人怀疑隐瞒。 |

## 3 交集与分歧（机械对照）

| 议题 | qwen3.8-max | deepseek-v4-pro | 标记 |
|---|---|---|---|
| **S1 ¶2 的 75/95 + 96/118 口径** | 命中（B2: 冠错名 + 96 vs 85 未区分） | 命中（B1+B2: 同名异义 + 选择性呈现） | **两模型交集** |
| **Algorithm 1 行号重复（28 出现两次）** | 命中（m1） | 命中（M1） | **两模型交集** |
| **advisor 盘点件相对当前草稿过期** | 命中（M4: draft 19 788 B → 实测 39 528 B, 两条硬阻塞已关闭） | 命中（m4: [TODO] 与已解决状态漂移） | **两模型交集** |
| **S6 门控案例定位/披露** | 命中（M3: 未披露 7/7 全由 gain 维拦截、ε 维零点火） | 命中（m3: 门控案例定位摇摆） | **两模型交集** |
| **对位表 hinge 叶数说明** | 命中（在 B1 内: "5 个 hinge 叶中仅 1 个满足"） | 命中（m5: 缺"hinge 叶数为 3 但 config 中为 5"的明确说明） | **两模型交集** |
| **S2 "latency 是一等计分维度"无工件支撑** | 命中（M1） | — | **仅 qwen** |
| **S4 judge 校准段预注册判据口径错位** | 命中（M2: 预注册界是逐维 0-5 量表, 被挪用于树根 0-10） | — | **仅 qwen** |
| **伪代码"exactly as implemented"省略三处细节** | 命中（m2: 全零权重保护 / round 舍入 / binary 内部口径） | — | **仅 qwen** |
| **对位表细节（root_sr 分母 / docstring 行号 / <=7 vs >=7 / 08-18 旧档）** | 命中（m3 / m4 / m5） | — | **仅 qwen** |
| **指针错挂（120 leaf-state cells）** | 命中（m6: 120 在 t4 e1_5.cells_total） | — | **仅 qwen** |
| **与 mutation testing 的对位句缺失** | 命中（m10） | — | **仅 qwen** |
| **S3/S7 内部注记与论文正文混杂** | 未单列 | 命中（M2+M3, 列为 major） | **仅 deepseek** |
| **S7 前瞻句 + 更正注记构成读者迷宫** | 未单列 | 命中（M4） | **仅 deepseek** |
| **gamma 网格符号不当** | — | 命中（M5） | **仅 deepseek** |
| **S2 专家权重缺引入理由** | — | 命中（m1） | **仅 deepseek** |
| **S4 "12 leaf units vs 2 root units" 可比性声明不足** | — | 命中（m2） | **仅 deepseek** |

## 4 Algorithm 1 与实现一致性 — 两模型结论对照

| 维度 | qwen3.8-max | deepseek-v4-pro |
|---|---|---|
| 总评 | "核心聚合逻辑逐行一致, 一致性水平高; 3 处偏差（1 Blocking + 2 Minor）" | 见其 §5, 方向一致: 实现一致性高, 问题集中在 hinge 缺失分数与对位表细节 |
| 逐行复核 | 明列 8 组"论文行号 → 代码行号"一致点 | 已独立复核 `eval_checkpoint_aggregate.py` 与 config |
| 唯一实质错误 | hinge 缺失分数声称（B1） | hinge 叶数说明（m5） |

## 5 两模型的独立运行证据（互不可见）

| 项 | qwen3.8-max | deepseek-v4-pro |
|---|---|---|
| 运行时刻（GB10） | 2026-09-21 01:40:49 起 | 2026-09-21 02:05:41 起 |
| exit code | 0 | 0 |
| 输出字节 | 24 134 | 21 162 |
| 输出行数 | 162 | 253 |
| 是否联网/引外部文献 | 否（报告自述"未联网, 未引用任何未核实外部文献"） | 否 |

## 6 未做（明确边界）

- **未合并结论**: 两份报告各自完整保留, 本表只做机械对照。
- **未替用户仲裁**: 不判断哪一份更对, 不裁定 B1 取哪一条修法。
- **未重跑**: 每模型只跑一次, 无重试、无 resume。
- **未修改任何被审文件**: 三份审查对象零改动。

## 7 供用户裁定时可能需要的信息

1. **两模型在 S1 ¶2 上给出互补判据**: qwen 指出"96/118 与 85/118 是两个口径", deepseek 指出"96/118 实为第三种口径（检查点级可见性）"。二者可合并理解, 本表不代为合并。
2. **同一项严重度定级有差异**: Algorithm 1 行号重复, qwen 列 Minor、deepseek 列 Major。
3. **qwen 偏"可机械复核的细节错误"**（指针错挂、行号偏一、分母备注）, **deepseek 偏"结构性/叙事性风险"**（内部注记混杂、读者迷宫、选择性呈现印象）。
4. 两份都指出 **advisor 盘点件相对当前草稿已过期**（18:31 快照 vs 当晚 23:33 的 T7 回填）。