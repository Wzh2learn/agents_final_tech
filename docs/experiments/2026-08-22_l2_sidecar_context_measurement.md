# L2 sidecar context 分布测量（准路根治合并卡 Phase 2 测量部分）

日期: 2026-08-22 凌晨（只读测量, 零配置变更, 不争 slot）
数据工件: docs/experiments/2026-08-22_l2_context_report.json（完整 JSON）

## 1. 一句话结论

**单次调用 decode 占 ~60-70%（但只生成 ~45 token, 是带宽墙不是 token 量）; 单次 prefill 占 ~30-40%（~10k context, TTFT 0.5-5s）。attempt 级主导项既非 prefill 也非 decode, 是串行 step 数（p50=3, p95=5）× 每步 ~7-15s。** 另实测坐实: 生产 m2-qa 的 thinking 实际是 OFF——"xhigh 轨迹超预算"归因需更正, 08-23 L1 矩阵基线口径必须先修。

## 2. 数据源

| 源 | 窗口 | 样本 | 用途 |
|---|---|---|---|
| SOP FM9 vLLM /metrics 直方图 | 08-20 00:12 起 21.2h | n=1920 真实请求 | prompt 长度分布大样本基线 |
| opencode.log（42.5MB, 86172 行） | 08-17 双模型 era 起 | 1913 个 m2-qa 会话 | step 数/会话时长/步间间隔 |
| :8006 回滚后 live /metrics | 08-21 23:46 起 ~26min | 9 完成请求 | TTFT/e2e/token 构成现状 |
| opencode.db 残留 | 08-07/08（A3B era） | 6 会话 | step 级 input token 锚点 |

## 3. Context 分布

FM9 大样本（n=1920）: ≤1k 30.3%（title 小调用）/ 10-20k 63.2%（m2-qa 多轮）/ >20k 6.6%（后段轮次）; 平均 prompt 11,719; p95/p99 >20k。
live 现状（回滚后）: prompt 累计 94,125 / 9 完成 ≈ 10.5k/请求, 与 FM9 一致。

## 4. prefill 构成拆分（Qwen tokenizer 实测）

| 组件 | tokens | 备注 |
|---|---|---|
| m2-qa agent prompt（输出契约+策略） | 494 | opencode.json 实测 |
| m2-rag-playbook SKILL.md 全文 | 1,030 | 每会话首轮显式加载 |
| skill 清单（18 个 name+description） | 1,011 | system prompt 注入 |
| MCP 工具 docstring（3 工具） | 47 | 仅 docstring; 完整 JSON schema 更大（低估） |
| 代表性问题 | 7 | |
| **可测小计** | **~2.6k** | |
| **残差（opencode 内置 system prompt + 工具 JSON schema + 格式开销）** | **~8-10.5k** | 13,095（DB step-0 锚点, 08-08）与 10.5k（live 均值）反推 |

**构成主项是 opencode 内置 system prompt + 工具 schema（~70-80%）, 不是 skill 元数据**（skill 清单+playbook 合计 ~2k, 占 ~15-20%）。08-13 "skill 全量装载膨胀"假设部分修正: 全量 18 skill 全文若装载应为 ~35k tokens, 实测 context 10-13k 证明只装载清单+单 skill 全文。

## 5. attempt 时序分解（n=1913, 08-17 起）

- m2-qa LLM 调用数/attempt: **p50=3, p95=5, max=15**
- step0→step1 间隔（= step0 生成 + 工具 RTT + step1 prefill）: p50=7.1s, p95=35.9s
- sidecar 会话时长: p50=46.8s, p95=132.8s, max=4162s
- 单调用（live metrics）: TTFT ≤2.5s（9/12）≤5s（12/12）; e2e ≤15s（9/9 完成）; 生成 ~45 tok/请求（prompt:generation = 232:1）

attempt 算术拼接（实测, 不外推）: 3 步 × ~10s/步（TTFT ~2s + decode ~45tok@带宽限 + 工具 RTT）+ title/skill 开销 ≈ 35-50s —— 与 B4 实测 46-50s 吻合。

## 6. prefill vs decode 判定

- 单调用级: decode ≈ 60-70%（45 tok 在 ~4.8-10 tok/s 带宽限下耗 5-9s）, prefill ≈ 30-40%（10k @ TTFT 0.5-5s, APC 命中后更低）
- attempt 级: **主导项 = 串行 step 数**。prefill 每步重复发生（context 逐步增长, APC 缓解）, decode 每步只 ~45 tok
- 杠杆排序（对 45s 预算）: ① 减 step 数（3→2 即省 1/3, 改 prompt 契约/合并查询/免 skill 装载步）② 终结孤儿续跑（见 §8）③ decode 提速（投机, 接受率是前提）④ context 瘦身（残差 8-10k 是靶子, 10k→6k 每步省 ~1-2s × 3 步）

## 7. 关键更正: 生产 thinking 实际 OFF（L1 基线口径必修）

证据链四条:
1. opencode.json gb10v/m2-qa 无任何 reasoning_effort 配置（实测文件内容）
2. thinking_inject_proxy 对未显式携带 enable_thinking 的请求默认注入 enable_thinking: false（脚本 docstring + 代码）
3. live metrics 生成 ~45 tok/请求, 与 08-16 探针 thinking-off 档（45tok）逐 token 吻合; opencode.db 全部会话 reasoning=0
4. DECISIONS 08-16 结论原文: "准路高思考方向在 dense 27B 不成立, 维持 thinking off"

影响: ① B4 终判/台账中"xhigh 轨迹长度 > 45s 预算"表述机制层面不准确, 更正为"串行多步 × 每步 7-15s（thinking off）"; ② 合并卡 L1 "medium vs xhigh 基线"前提不成立——两者经现有接线都等于 off, 矩阵将变成 off-vs-off; **08-23 跑前须拍板: L1 改为 thinking off（现状）vs 显式注入 medium/xhigh 的对照, 还是先决定准路要不要开 thinking**（08-16 数据: 开 thinking 加延迟且 dense 27B 无结构化推理收益; 08-19 批复"xhigh 起步"与接线实况存在口径落差, 一并报用户裁定）。

## 8. 顺带发现（记账不动手）

1. **孤儿会话续跑**: :5050 适配层 45s 超时回落后, sidecar 会话继续跑到完（p95=133s, max=69min）——回落样本照产, slot 白占。这是"slot 争用"的实体来源之一。潜在对策: 超时后主动取消 sidecar 会话（需 opencode API 支持评估）——入 L2 方案菜单。
2. **transcript 持久化损坏**: opencode.db part/message 插入自 08-14 起持续失败（5187 次 EffectDrizzleQueryError）, message 表仅剩 08-07/08 残留 6 会话。本次测量因此依赖 log+metrics 而非 transcript。根因未深挖（疑 schema/约束漂移）, 入台账待查。
3. Loop B 08-21 23:43 周期 model_topology FAIL = 回滚重启窗内 :8006 停机时的抓取（report ts 23:43:57, 窗口 23:41-23:46）, 设计内预期, 下周期应自愈。
4. 方法学注记: log 中 permission=skill / jinrong-rag_knowledge_search 行不带 session.id, 按会话归属的 skill_loads/rag_calls 计数偏低（stream 计数不受影响）。

## 9. 对三杠杆的解读框架（L1 矩阵出来前就位）

- L1: 见 §7, 基线口径先修再跑
- L2 方案菜单（数据支持的排序）: a) step 数削减（prompt 契约改"单次检索+直接回答"变体 A/B, 预期 45s→~30s）b) 孤儿取消机制 c) system prompt/schema 瘦身（opencode 内置部分可配置性待评估, 收益 ~3-6s/attempt）——方案报批后动
- L3: DFlash2 只动 decode; 本文 §6 给出其收益上限框架——单调用 decode 占比 60-70% 且 token 量小, 投机收益取决于接受率能否离开 1.x 洼地（D2 定论）, 与 prefill 瘦身互补不互替