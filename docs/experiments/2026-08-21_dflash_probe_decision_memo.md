# D4 决策备忘：DFlash 探针臂 GO/NO-GO

状态: 终稿 NO-GO | 更新: 2026-08-21 01:55 | 类型: 只调研不动手（决策输入）
术语口径: DSpark ≠ DFlash ≠ DFlash2（同族独立方法，见 drafter 台账 08-21 条目）

## 1 事实核查（本轮实测）

| 项 | 结论 | 证据 |
|---|---|---|
| DFlash2 合入状态 | **未合入**，排除 | vllm-project/vllm PR #52816 "[Spec Decode] DFlash2: local convolution + candidate selector" state=open, merged=false, updated 2026-08-20（GitHub API 实测） |
| DFlash2 权重 | 无公开权重 | 用户已核 + PR 未合无发布渠道 |
| 官方 dflash/dspark drafter × Qwen3.8-27B | 无 DFlash 规格官方 drafter；DSpark 官方 drafter 在用（ebaa091） | drafter 台账 |
| 社区 DFlash drafter | **rwmacy/qwen3.8-27b-dflash-drafter-fp8-b70 存在** | hf-mirror API 实测：sha 94f8b9cc, lastModified 08-16, Apache-2.0, downloads 243/likes 2, specforge 训练, **config architectures=DSparkDraftModel（custom_code auto_map）** |
| 我们镜像的引擎支持 | qwen3_dflash.py 与 qwen3_dspark.py 均在位 | docker exec 实测 vllm/model_executor/models/ |

## 2 风险清单（开臂前必读）

1. **架构名疑点**：rwmacy 仓库名为 dflash 但 config architectures=DSparkDraftModel——可能是 specforge 统一导出格式或命名混用；加载走 method=dflash 还是 method=dspark 需探针首步确认，加载失败即 NO-GO 不恋战；
2. **训练硬件/目标差异**：按 Intel Arc Pro B70 + FP8 目标训练（b70 后缀）；drafter 对目标量化不敏感（台账结论 6）但跨引擎/跨硬件训练分布差异是接受率干扰因子；
3. **custom_code 安全**：trust_remote_code 仓库，下载前须人审 config.json 与建模代码（只读审计，不执行其中任何安装指令）；
4. **内存预算**：drafter ~2.5GiB 级，:8007 探针位独立，预算门照走。

## 3 决策规则（用户给定）

- 若 D2 结论为"DSpark 在 agent 流量（xhigh+XML）接受率天然低（<1.5）而其他段 >2.5" → **建议 GO**：开 :8007 DFlash 探针对比臂，协议 = 同 10 题固定矩阵 + 同流量分段（D2 同协议），对照接受率与延迟；
- 否则（各段接受率均匀低 → 是流量本质而非 drafter 选型问题；或 agent 段接受率不低 → DSpark 无更换理由） → **NO-GO**，维持 DSpark，优化方向转超时预算/思考档位路由。

## 4 D2 实测代入与结论（终稿）

D2 分段数据（2026-08-21_d2_acceptance_segmentation.md）：xhigh+XML 段接受率 1.517（未破判据的 1.5），且**全段无任何 >2.5 的流量**（生产 agent 路 1.09-1.29 / freeform 1.76）。判据后半不成立 → 按决策规则**不开探针臂**。

叠加本轮独立证据，结论加固为 **NO-GO（双因）**：

1. **规则因**：D2 坐实接受率是全局对齐问题而非流量选型问题——换一个同族 drafter 不改变局面；
2. **工程因**：现存唯一 27B DFlash drafter（rwmacy）README 自证——SpecForge 训练的 drafter 在 stock vLLM 的 dflash 采样路径存在 off-by-one（位置 j 应预测 anchor+j+1，stock 按 BERT 式 1..k 采样），**不打 rmacy/vllm fork 补丁接受率崩至 ~24%**；在我们 vllm-gb10 镜像上开臂等于测一个已知损坏的配置，结论无信息量；公平对比需要换整个 serving 栈（fork 镜像, XPU 向调优, GB10 适配未验证）——那不是探针臂, 是栈迁移项目；
3. **血缘因**：rwmacy drafter 是 RadixArk DSpark drafter（我们现役）的 warm-start 微调（761 ShareGPT + 200 领域样本, 440 步）——同血缘小增量微调, 差异化空间有限。

**NO-GO 复核条件（满足其一可重开评估）**：
- vLLM 上游合入 dflash 采样 off-by-one 修复（盯 PR/commit）且出现官方 Qwen3.8-27B DFlash drafter 权重；
- DFlash2（PR #52816）合入 + 权重出现（已入盯梢，见 §5）；
- drafter v2 上游迭代（Koopah 先例 +6.8%）证明同血缘微调收益可观，再评估自训微调路线。

## 5 DFlash2 版本盯梢（入 drafter ledger）

- 盯 PR #52816 合入状态 + 官方权重出现；复核命令：GitHub API pulls/52816（state/merged 字段）；
- 合入且权重出现 → 重开 DFlash2 探针评估（届时引擎版本升级一并评估，见 vLLM 版本升级长期台账）。

## 6 口径更正注记（2026-08-22, T1 漂移扫荡）

- 本备忘文中"xhigh"均指受控直打探针段（显式传 reasoning_effort=xhigh 直打 :8006）, 非生产接线口径; 生产 m2-qa thinking 当时实际 OFF（见 2026-08-22_l2_sidecar_context_measurement.md §7）。
- NO-GO 结论不受本更正影响（基于镜像事实判定: 现镜像不含 DFlash2DraftModel + 权重事实）。
