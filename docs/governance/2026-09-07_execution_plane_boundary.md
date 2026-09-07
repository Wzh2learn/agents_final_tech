---
status: 活跃（裁定件, 边界冻结）
date: 2026-09-07
source: 用户裁定 09-07（决策 3B）+ D3 阶段 B closeout 侧线角色审计
backlog: docs/29_graph_engineering_roadmap.md A23
relation: 收敛 side_handoff:4 与 STATE:80 先例的散见表述（原文不动, 不取代任何判据）
endpoint_calls: 0
---

# 执行面 / 控制面边界与 Experimental-fact test（角色漂移预防）

> 性质: 治理裁定件（非实验记录）。自 2026-09-07 起冻结。
> 背景: D3 阶段 B 收口抽验（本地, 27/27, 零端点）经侧线独立复核判定为**合法 Loop D 本地审计, 角色正确, 无漂移**; 但此前「本地能做什么」只散见于 side_handoff 与 STATE 先例, 缺单一权威定义, 存在渐进漂移风险。本件为唯一权威定义。

## 一、角色边界（冻结）

**本地 = Control / Analysis / Audit Plane**

- 拟卡与预注册
- 源码阅读、静态检查
- 既有 artifact 机械复算
- ledger 一致性抽验
- closeout、autopsy
- claim / boundary 推理
- 文档治理（STATE / THREADS / INDEX / docs）
- 为 GB10 起草执行脚本
- 纯本地 deterministic parser / schema / smoke 测试

**GB10 = Experimental Execution Plane**

- 一切正式 run
- endpoint / judge 调用、模型推理
- GPU 与运行时环境验证
- calibration、benchmark、replay、ablation、transfer
- 任何会改变论文最终数字的运行
- 任何生成正式 raw experimental artifact 的执行

**判据**: 不是「脚本在哪台机器跑」, 而是**这个动作在分析既有实验事实, 还是在创造新的实验事实**。

既有口径不变: pytest 全量基线（402 passed / 13 skipped）与 docs_lint 权威结论以 GB10 为准; 主线程直跑实验仅在 Loop A 异常时且必须显式记账（STATE:80 先例）。

## 二、Experimental-fact test（EFT 三问）

任一问落 GB10 侧 → 回 GB10。

| # | 问 | 落 GB10 侧的条件 |
|---|---|---|
| EFT-1 | **输入**: 是否只依赖已落盘的既有事实? | 需要任何现场运行时（模型服务 / 端点 / GPU / 远端环境 / 正在写入的 ledger） |
| EFT-2 | **输出**: 是否是既有事实的确定性函数（同输入必同输出、可离线复算）? | 输出含新 verdict / 新 paper-facing number / 新 raw observation |
| EFT-3 | **标签**: 产物能否诚实标注 `phase ∈ {audit, spotcheck, closeout_loop_d, autopsy}` 且 `endpoint_calls: 0`? | 它必须标 window / run / stage_X / experiment |

三条全落本地侧 → 本地允许。**判不出来 = 当作创造新事实 = 回 GB10 或先问用户**, 不靠临场感觉。

## 三、三条硬规则（防渐进漂移）

1. **本地审计脚本禁网禁派发**: 不得 import 任何 HTTP 客户端、不得含 subprocess / ssh / 派发逻辑, 必须自带 socket 封死守卫并把 `socket_attempts` 写进收据。派发只走 Loop D 显式派发链（ssh / tmux）+ 记账, 不得内嵌在审计脚本里。
2. **命名与字段即 provenance**: 本地写入 `logs/graph/eval/` 的产物, 文件名须含 `spotcheck|precheck|closeout|recompute|autopsy`, `meta` 必须含 `phase` 与 `endpoint_calls: 0`; 禁止本地生成 `*_stage_x.json` / `*_window.json` 这类形似原始实验件的产物。
3. **收据必须可复现**: 复现命令与远端取件步骤（含期望 sha256）必须写在收据或其绑定文档中; **依赖线程临时目录的镜像视同不可复现**。

## 四、本裁定适用的下一阶段边界（09-07）

- **D3 autopsy**: 本地可做（解释与机制推理, 零端点, 不产生新观测）。核心问题 = harmful / equivalent 是否依赖 scorer / matcher 的等价类定义, 以及该 scorer dependence 应写成机制主张还是 claim boundary。
- **D4**: 本地**只拟卡、只审计**（预注册设计稿 + oracle + 阈值网格 + 解冻条款, 并把 F-0907-3 的 agreement 谓词写进冻结节、列为派发硬前置）; 正式 execution 必须 GB10（Loop A + tmux 派发 + 记账 + 观察器, 派发前置检查新增「执行位 + 首次 tick 实证」两项）。拟卡阶段若冒出「验证一下端点 / 模型 / 环境」的需要 = EFT-1 命中 = 回 GB10 另开卡。
- **T7 数字合流 / neat 收口卡 / A4-A5 修复拟卡**: 本地（A4/A5 的验收跑在 GB10）。

## 五、待裁定指针（本件不自裁）

1. 收据可复现性的落地方式: 保持 v1 不动（认定 closeout 报告 §14 已满足决策 1B）, 或重跑补 `meta.reproduce` / `corpus_provenance` 生成 v2 收据 + 重生成 SUMMARY-GUARD。
2. watcher 机制修复（执行位 / crontab 注册形态）与 GB10 残留 crontab 行清理的时点（现场按 F-0907-1 保留作证据, 未动）。

## 六、首例适用记录

`research/paper_d3_stage_b_closeout.py` + `logs/graph/eval/d3_stage_b_closeout_spotcheck.json`（`phase=closeout_loop_d`, `endpoint_calls=0`, `socket_attempts=0` 已入收据）= 本边界下首个本地审计件; 侧线独立复核结论 = 合法 Loop D 本地审计, 角色正确, 无漂移; 脚本与收据全部保留（不回滚、不重做、不搬去 GB10 重跑 = 决策 1B）。

**已知不足（如实记）**: 语料冻结件 `data/research/drift_v0/input/tatqa_tables.json` 仅在 GB10, 本次抽验用其 sha 校验镜像（`3e7e0568…` 逐字相符）落于线程临时目录 ⇒ 按硬规则 3 **视同不可复现**, 处置待裁定（§五.1）。