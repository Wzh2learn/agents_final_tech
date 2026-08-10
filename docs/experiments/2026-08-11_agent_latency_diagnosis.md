# 2026-08-11 agent 路延迟退化诊断（39-55s vs 基线 15-20s）

> 状态: 根因已定位, 修复待用户拍板 | 关联: memory/THREADS §2026-08-11, dispatch_log #LATENCY-ROOTCAUSE

## 现象
:5050 重启 + sidecar 重建后, m2-qa 手测冷 39s / 热 55s（08-09 skill 注册前口径 15-20s）。
OPENCODE_ASK_TIMEOUT=18 → route=on 全部设计内回落直连（2-4s, 答案正确带引用）, 演示不受影响但「快与准菜单」的准路叙事失效。

## 排查方法
adapter 为 throwaway session（ask 完即删, opencode_adapter.py:9-11）, 旧 transcript 不可追溯。
改直连 sidecar API 建计量会话（不经 adapter, 不自动删）+ SQLite (~/.local/share/opencode/opencode.db) trace 取每轮 time.created/completed 与 tokens。

## 证据
| 测量 | 总时 | 轮1 | 轮2 | 输出 tokens |
|---|---|---|---|---|
| 基线(原配置, warm) | 31.5s | 12.0s (in 512 + cache.read 10454, out 459, tool=knowledge_search) | 19.5s (in 3155 + cache 10962, out 1017) | 1476 |
| 变体A(摘 playbook 指令, cold) | 43.1s | 37.3s (in 10917, cache=0) | 5.5s (out 218) | 333 |
| 变体A(warm) | 22.8s | 4.2s | 18.6s (out 749) | 903 |
| 08-09 01:02 (skill 注册后, DB trace) | ~39s | in 10717 out 189 | +38.9s gap | 426 |

## 根因
1. **~11k skill 元数据上下文冷 prefill ≈ 37s**（「冷 39s」真身; opencode.json 顶层 skills.paths=skills 全量 16 skill 进 m2-qa 系统上下文; 每次 sidecar 重启后首问承担, warm 后 cache.read 命中）。
2. **输出端 reasoning ≈ 19-30s（warm）**: qwen3.6-35b thinking 默认开, 单 ask 输出 0.9-1.5k tokens, 本地 ~45-50 tok/s。
3. playbook 加载指令从未执行（skill tool 零调用）但诱发额外推理: 摘除后 warm 31.5→22.8s。
4. 08-09 前 15-20s 口径 = skill 注册前上下文小（in 380/3130）且输出短。

## 修复方案（待拍板, 均未动手; opencode.json 已还原无净变化）
| 方案 | 改动 | 预期收益 | 风险/前置 |
|---|---|---|---|
| a warm-up ask | restart_opencode_sidecar.sh 重启后发一次廉价 ask 预热 cache | 冷 43→~23s | 几乎无; 脚本级 |
| b m2-qa 禁 thinking | adapter _FORMAT_HINT 加 /no_think 或 provider chat_template_kwargs（judge 已有 enable_thinking=False 先例, m2_eval_judge.py） | warm 22.8→~8-12s | 需 :5050 重启窗口 + 16 题 eval 复验质量 |
| c skill 上下文瘦身 | m2-qa 仅注册必需 skill（opencode per-agent skills 机制待查） | 冷 prefill 37→<10s | 需调研 opencode skill 作用域 |
| a+b 组合 | | 冷/热均 ≤12s → 18s 超时内 agent 路可用, 「快与准」叙事恢复 | b 的前置 |

## 结论
演示维持直连路为主; agent 路保留回落兜底。修复按 a→(b 经 eval 守护)→c 顺序建议。
