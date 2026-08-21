# D2 接受率流量分段诊断 — DSpark 生产实效核心数据

状态: 活跃 | 更新: 2026-08-21 01:50 | 类型: D2 纯观测诊断（零配置改动）
工件: logs/graph/eval/d2_acceptance_segments.json（GB10）; scripts/graph/d2_segments.py（驱动器, 含段 C filter bug 已注记）
方法: vLLM /metrics spec_decode 计数器分段差值（drafts / accepted / 逐位 per_pos）; kiosk 背景窗 180s 实测 0 流量（kiosk QA 稀疏, 背景扣除≈0）

## 1 分段接受率表

| 段 | 流量类型 | drafts | accepted | 接受率 | 备注 |
|---|---|---|---|---|---|
| A kiosk 背景窗 180s | kiosk 演示循环 | 0 | 0 | N/A | kiosk 不持续打 :8006 |
| B eval 确定性 16 题（经 :5050, route=on, 798s） | 生产 agent xhigh（45s 截断轨迹） | 1072 | ~1382 | **1.289** | 每题 agent 尝试→超时→回落 |
| C1 手动 ask1（经 :5050） | 生产 agent xhigh | 53 | 64 | **1.208** | 47s, 回落直连出答 |
| C2 手动 ask2（经 :5050） | 生产 agent xhigh | 70 | 76 | **1.086** | 46s, 同上 |
| D1 受控 XML/xhigh（直打 :8006） | 合成 agent 风格（工具调用结构化） | 238 | 361 | **1.517** | 600 token, 38s |
| D2 受控 freeform/xhigh（直打 :8006） | 合成自由文本 | 196 | 345 | **1.760** | 540 token, 31s |
| 参照: 探针固定题库 thinking-off（08-19） | 短答负载 | — | — | 3.31 | 离群高值, 非生产形态 |

（段 C 驱动器 filter bug 匹配 0 题, 手动补测两 ask 入报告；逐位分布见 JSON per_pos_pct）

## 2 结论（对照用户判据）

用户判据："若 xhigh+XML 段接受率 <1.5 而其他段 >2.5 → drafter 与 agent 流量不匹配"。
实测：**XML 段 1.517（未破 1.5），且不存在任何 >2.5 的段**——判据后半不成立。

1. **接受率全段均匀低（1.09-1.76）**：不是 drafter 与某类流量不匹配，是 drafter-target 在 GB10 生产分布上的整体对齐水平；探针 3.31 是 thinking-off 短答固定题库的离群高值，不能作为生产预期（与切换窗"生产 1.26 vs 探针 3.31"一致并扩展）；
2. **真实 agent 路（1.09-1.29）低于合成受控（1.52-1.76）**：sidecar 真实轨迹含长上下文 + 16 skill 元数据 + 工具调用结构，且被 45s 超时截断，接受率比干净合成 prompt 更低——agent 路是接受率洼地，也是延迟主战场；
3. **D4 触发条件不成立** → 按规则不开 DFlash 探针对比臂（且 D4 独立证据另行加固 NO-GO，见决策备忘）；
4. **D3 k 裁剪不是主杠杆**：接受率均匀低意味着草稿整体价值低，裁尾部只省草稿开销不动接受率；方案保留待批但推荐度维持中低；
5. 真正杠杆方向（只记账不动手）：① 思考档位作为路由维度（快准菜单已有骨架）② drafter v2 上游迭代盯梢（Koopah 先例 +6.8%）③ sidecar 上下文瘦身（skill 元数据裁剪——与延迟排查靶子同源）④ 超时预算重议（T3 已做 45s，数据支持不再盲抬）。

## 3 口径与纪律

- 段 B 流量经 :5050 生产端点（用户既定口径"eval 经生产端点积累真实样本"）, B4 计入 16 行；段 D 直打 :8006 不经 :5050, 不污染 B4；
- kiosk 未暂停（D2 为观测, 背景窗实测其 :8006 贡献≈0）；
- 未改任何配置；逐位分布与全部原始计数入 JSON 工件。

## 4 口径更正注记（2026-08-22, T1 漂移扫荡）

- 本报告 B/C 段口径中出现的"生产 agent xhigh"标签系 08-19 批复措辞; 当时生产实况为 thinking OFF（opencode.json 无 reasoning_effort + thinking_inject_proxy 默认注入 enable_thinking:false, 见 2026-08-22_l2_sidecar_context_measurement.md §7）。
- 接受率数字不受影响: 全部为 /metrics spec_decode 计数器差值实测, 与 thinking 标签无关。
- D1/D2 受控段（直打 :8006、显式传参）不受本更正影响。
