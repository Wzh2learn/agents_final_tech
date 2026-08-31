---
id: TASK-20260831-D2
risk: low-medium
window: daytime-zero-endpoint
status: 定稿（取代 2026-08-31_d2_cross_matcher_card_draft.md）
premises:
  - id: P1
    claim: "D1 底表冻结在位: logs/graph/eval/d1_mutant_validity_audit.json（all_pass=true, 抽验 7/7）"
    falsify: "python3 读 gates.all_pass == true"
  - id: P2
    claim: "匹配器资产: 贪心 = 生产协议匹配路径（checkpoint_discrimination 管线）; Hungarian = research/paper_t6_matching_competition.py 在库; 归一化变体本卡实现; 嵌入 = ~/wzh/models/hf/bge-m3 在位（本地加载, 零服务调用）"
    falsify: "文件/目录在位 + 脚本可导入 + bge-m3 config.json 存在"
  - id: P3
    claim: "开窗前置检查已过（主线程 08-31 记账）: codex 后端探针 PROBE_OK（模型响应正常, 目录刷新错误未复现）; canary 快照 = Loop B overall PASS / qa_canary PASS / 'Loop A may continue'（verify-report 8ccb8d6 周期）; :8004/:8006/:8100 端口监听在位"
    falsify: "THREADS #D2-PRECHECK 条目"
  - id: P4
    claim: "零端点: 全程无模型服务调用; 嵌入匹配器 = 本地 HF 模型加载（bge-m3）; 自证口径 = D1 版（AST 作用域检索 + ports 自证 + 冻结件只读）"
    falsify: "运行时断言 + 脚本静态检索"
acceptance:
  - "≥3 匹配器（贪心/归一化/Hungarian）+ 嵌入匹配器（资产可用时）下的可见性谱: 六类判别率 × γ 网格 + 谱排序对比"
  - "per-injection 迁移矩阵: 33 吸收注入（E7+HI26）× 匹配器 的状态保持/翻转全表入工件（DR-3）"
  - "R3 判据对照: 全盲类型是否在所有匹配器下存续 + 谱排序 Kendall τ"
  - "工件 logs/graph/eval/d2_cross_matcher.json（含 gates + prereg + inputs_sha256 + digest_self_consistency）+ 报告（SUMMARY-GUARD 收据）"
rollback: "git revert; 冻结件只读零改动"
redlines:
  - "零端点; 本卡不使用 :8006（如执行中认为必须端点 → 停下报主线程, 禁止静默使用; :8006 五条件条款仅在有批准的新卡内生效）"
  - "J7 端点鲁棒性窗不随本卡开启"
  - "判据冻结: R3 降级表述与下列预注册执行后不溯及"
  - "甲方标识零进入; 禁 git add -A / amend"
skills:
  - "graph-loop-rules（红线常备）"
  - "verify-before-done"
  - "executing-plans"
  - "systematic-debugging"
---

# 任务卡 D2: 跨匹配器验证（定稿, 零端点）

> 派发载体: Loop A（GB10, --profile loopa-exec）| 单窗 | 依据: Claim Set v2 R3（降级判据）+ D1 autopsy（DR-3 迁移矩阵）+ 用户 08-31 批准序列
> 判据引用: Claim Set v2 R3 降级表述（原样）: 「D2 跨匹配器若谱形显著改变 → 改为"盲区位置匹配器相关, 谱结构（存在全盲类型）匹配器无关"」。

## 1. 目标

验证可见性谱对匹配器选择的稳健性, 输出: ① 每匹配器六类谱（γ 网格）② 33 吸收注入迁移矩阵 ③ R3 判据对照（全盲存续 + 排序一致性）。全部零端点。

## 2. 预注册（冻结, 执行后不溯及）

- **P-1（编辑距离族, 贪心/归一化/Hungarian）**: ocr_similar 全盲存续（0/13）; 六类谱排序对生产贪心谱 Kendall τ ≥ 0.8。不满足 → R3 降级条款自动生效并入报告, 不静默改判。
- **P-2（嵌入匹配器, 探索性）**: 不设通过/失败判据（新打分基）; 报告谱 + 迁移; 用于"盲区位置匹配器相关性"判定（两个方向都是合法答案）。
- **P-3（等价稳定性）**: 7 等价注入在编辑距离族匹配器下保持吸收-等价; 翻转 = 发现（逐条报告, 不判失败）。
- **P-4（零端点自证）**: ports=[]、model_calls=0、AST 作用域检索零 http 客户端、冻结件只读（inputs sha 核对, 含 D1 工件）。
- **P-5（完整性）**: 33×(匹配器数) 迁移矩阵无缺格。

## 3. 动作序

0. 前提一分钟证伪（P1-P4, 含 bge-m3 加载冒烟; 加载失败 → 嵌入件降级为"资产不可用"如实记账, 其余照跑, 不静默跳过）。
1. 归一化匹配器实现（编辑距离按表头长度归一化打分, 与贪心同接口）+ 既有贪心/Hungarian 接口统一（header → canonical field 分配 + 打分）。
2. 嵌入匹配器: bge-m3 本地加载, 表头与候选字段嵌入余弦分配（阈值 = 预注册固定值, 从 control 表分布定标后冻结, 写入工件）。
3. 每匹配器 × γ 网格重跑可见性判定（确定性协议, D1 同口径）→ 谱 + 逐注入状态。
4. 迁移矩阵（33 吸收 × 匹配器）+ R3 对照 + 门（P-1..P-5 → gates）+ digest_self_consistency。
5. 工件 + 报告 + SUMMARY-GUARD 收据（summary_recompute_guard.py gen）+ commit（逐路径）+ 汇报。

## 4. 中止与退出

- 中止: D1 底表摘要失配 → 停报; bge-m3 加载失败 → 嵌入件降级照跑; 任何认为需要端点的时刻 → 停报, 禁止静默使用。
- 成功退出: 工件 + 报告 + 收据 + commit + §5 汇报。

## 5. 汇报格式

执行结果 / 工件路径 / 数字摘要（每匹配器谱 + τ + 全盲存续 + 迁移矩阵要点 + 嵌入谱）/ 红线自查（零端点/只读/判据冻结）/ commit hash。
---

## 加编（08-31, 改期 #1: 首跑令牌耗尽 629k 零产出 → 两阶段切分, 判据不变）

首跑事实: loop-a-d2 会话在脚本设计段耗尽令牌（tokens used 629,428）, 工件零产出, 前提证伪已通过（D1 底表 all_pass=true / sha d7d0e0e0… / T6 可导入 / 吸收层级符合预期）。改期纪律内（≤2）。

**两阶段切分（用户"确定性三件先行"口径的卡内落实）**:

- **阶段 A（本跑必须独立交付）**: 确定性三件（贪心生产路径 / 归一化变体 / Hungarian）——谱（六类 × γ 网格）+ 33 吸收注入迁移矩阵 + 预注册 P-1（全盲存续 + τ≥0.8）/ P-3（等价稳定性）/ P-4（零端点自证）/ P-5（迁移矩阵完整, 3 匹配器列）判定; 工件 `logs/graph/eval/d2_cross_matcher_det.json` + 报告 + SUMMARY-GUARD 收据 + commit。**阶段 A 完成即算本窗绿态下限**, 嵌入件不作本跑阻塞项。
- **阶段 B（紧随阶段 A 同会话续跑; 若上下文不足则独立派发, 记账不算新改期）**: 嵌入匹配器（bge-m3 本地）——预注册 P-2（探索性, 无过判）; 工件 `logs/graph/eval/d2_cross_matcher_embed.json`（独立件, 不覆写阶段 A 工件）+ 报告附节 + 收据 + commit。

**执行纪律（针对首跑失败模式）**: 脚本增量写——阶段 A 脚本先独立写通跑通交付, 再写阶段 B 扩展; 避免一次性设计四匹配器统一接口; 大文件（D1 工件/T6 脚本）按需读取键段, 不全量复读。

**判据冻结声明**: 预注册 P-1..P-5 内容零改动, 仅交付切分; R3 降级条款照旧。
