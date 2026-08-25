# F-J3 孤儿轨迹治理提案（只提案不动手，08-26 凌晨）

状态: 提案 | 更新: 2026-08-26 | 取代/被取代: 无

## 病灶（两案共同上游根因）

:5050 客户端 45s 超时后, sidecar/opencode 在途轨迹**不取消**继续跑完（E3 诊断:
截断时 step1 在途 44%）→ ① 08-25 01:51 judge 饱和（NF 孤儿占满 :8006, 16×90s 全超时）
② 准路完成率洼地（孤儿占 slot 抬高后续延迟 + 回落行污染统计）。即减 step 菜单 M4-a。

## 菜单（按风险升序）

| # | 杠杆 | 层 | 工作量 | 风险 | 预期效果 |
|---|------|-----|--------|------|----------|
| a | 超时即 dispose: :5050 超时分支调 opencode session abort API（若存在）或 HTTP 连接 close+session delete | adapter | 0.5d | 中（需验证 abort 语义, FK 竞争同窗） | 孤儿源头掐断, 两案同解 |
| b | sidecar 步级预算: m2-qa agent prompt 加"单步 >20s 立即收尾"硬约束 + skill 路由剪枝 | prompt/skill | 0.2d | 低（可 A/B） | 降 step 耗时, 孤儿变短 |
| c | vLLM 侧 request timeout: --request-timeout 或 priority 隔离 agent 流量与 judge/canary | 推理栈 | 需 :8006 重启窗 | 高（生产配置） | 饱和上限可控 |
| d | 双队列: judge/canary 走独立 vLLM 实例或 :8004 默认（F-J2 已部分实现协议层隔离） | 架构 | 1d+ | 中 | 结构性隔离 |

## 推荐序

b（零风险先做, 与 L1/L2 杠杆同批）→ a（随下个 :5050 代码窗, 与 FK 水位闸同窗,
交互假设检查: abort 与 cleanup_sessions 水位闸是否互触）→ d 评估 → c 最后。

## 挂起状态

等用户批窗口; 本提案不实施。F-J2 协议闸已在位（run_eval.sh 08-26）, 重跑层风险已控。
