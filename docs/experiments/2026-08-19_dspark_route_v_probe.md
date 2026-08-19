# DSpark Route V :8007 探针测量报告

状态: 活动 | 更新: 2026-08-19 | 取代/被取代: 无
> 对应任务卡: DSpark Track 1 任务卡 v2 (Route V 探针测量, :8006 停机窗口内)。

## 结论

**GO** — 投机解码激活确认, 确定性 16/16, NF 0/9, judge 四维 5.0 (Track C 重跑坐实, 见审计节)。
- 升档注意: xhigh 平均延迟 23.8s (较 off 6.5s 高 ~2.7 倍), adv_multiturn 单题 90.9s。
- Route V (k=7 probabilistic) 实测接受率 3.31 accepted/draft, 逐位 0.943/0.943/0.571/0.371/0.286/0.143/0.057 (off 短问答负载)。

## 环境与启动

- 容器: `vllm-dspark-v` (:8007, vLLM 0.27.2.dev0), 启动 08-19 13:10, READY 13:19 (init 301.28s, 含 torch.compile 86.92s)。
- 启动参数 (docker inspect): `vllm serve /models/model --served-model-name qwen38-27b-fp8 --gpu-memory-utilization 0.30 --max-num-seqs 32 --max-model-len 32768 --enable-prefix-caching --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_xml --limit-mm-per-prompt {"image":2} --chat-template /models/chat_template_custom.jinja --speculative-config {"method":"dspark","model":"/models/drafter","num_speculative_tokens":7,"draft_sample_method":"probabilistic"} --trust-remote-code`
- 内存算术: 预检 CUDA free 33.92/121.63 GiB 失败 → 用户批准停 :8006 → 全规格启动; 启动时 free 69.46/121.63 GiB, GMEM=0.3 (36.49 GiB 目标), consumed 27.86 GiB (weights+non-torch), peak activation 2.67 GiB, CUDAGraph 0.58 GiB, **KV cache 5.96 GiB 启用**。
- 模型: qwen38-27b-fp8, max_model_len 32768; drafter Qwen3.8-27B-DSpark-vLLM (k=7, probabilistic)。

## 投机解码激活验证 (Step 1)

- 非默认 args 含 `speculative_config={method: dspark, model: /models/drafter, num_speculative_tokens: 7, draft_sample_method: probabilistic}`; `Resolved architecture: Qwen3DSparkModel`; `Capturing model for DSpark speculator...` + dspark CUDA graphs 29/29 捕获成功。
- metrics 计数器存在且增长: `vllm:spec_decode_num_drafts_total` 110→(冒烟 3 短问答后)→ 持续增长; 期间 /metrics 209.9→226.5s 两次读取 6229→7180 (drafts +951)。
- docker logs 周期 SpecDecoding metrics: Mean acceptance length (1.31→3.48 随负载), Avg Draft acceptance rate 4.4%→35.4%。
- 冒烟: 3 条短问 thinking off 均 200 非空 (481–4716ms 含 JIT 冷); 生死线 PASS。

## Golden 样本 (Step 2) — 6 条

存放 `logs/graph/eval/dspark_route_v_golden.json` (每条 name/request/response_text/reasoning/tool_calls/latency_ms):

| name | 延迟 (ms) | 注记 |
|---|---|---|
| lossless_zh_price | 18182 | 中文金融固定题, thinking off, 拒答式说明未提供文件 (合理) |
| lossless_en_custodian | 4547 | 英文通用, 2 句完成; 无 reasoning |
| thinking_xhigh_zh | 15990 | 同题 + reasoning_effort=xhigh, reasoning 长文, content 拒答说明 |
| thinking_low_zh | 12560 | 同题 + effort=low, 拒绝原因与 xhigh 类似 (上下文缺失下诚实拒答) |
| thinking_effort_without_enable | — | 预期 400: `reasoning_effort=high` 不带 enable_thinking → 400 "Unexpected reasoning effort high. Supported types are xhigh (default), medium, and low." (记录完整错误体) |
| tool_get_weather | 1635 | tools 定义 + "北京今天天气怎么样" → `tool_calls=[{type:function, function:{name:get_weather, arguments:{"city":"北京"}}}]`; content 空, reasoning null |

**chat template 行为注记**: 请求**不带** `chat_template_kwargs` 时, 默认模板渲染成 thinking 分支 (reasoning 非空、content 空/空串) — 与"默认 thinking off"语义不符; 显式 `"chat_template_kwargs":{"enable_thinking":false}` 才走 content 分支 (reasoning null)。本项目既有矩阵/生产请求均显式传 off, 无需变更; 但裸默认调用方需注意。
校验: 首次写后 head -5 正常 (JSON 数组, 6 元素).

## 延迟矩阵 + 接受率 (Step 3)

### 确定性 16 题 (固定题库, 检索=生产同口径, temperature=0) — :8007

| 档位 | 通过 | p50 (ms) | 平均 (ms) | 最慢 (ms) | 说明 |
|---|---|---|---|---|---|
| off | 16/16 | 4286 | 6466 | 21918 (adv_multiturn) | `dsaprk_route_v_think_off_report.json` 完整 16 题 |
| xhigh | 16/16 (1 题另测) | 19546 | 23822 | 90863 (adv_multiturn 两轮) | 15 题来自矩阵 log; adv_multiturn 专测 90863ms (PASS, A2 含"无法计算占比"诚实拒答) |

- :8006 基线 (等价性对照侧): 既有 `logs/graph/eval/model_probe_matrix.json` (08-15 口径, A_off n=10 p50≈10.3s / B_effort_low p50≈23.8s / C_xhigh p50≈60.6s) 与 `model_probe_deterministic.json` (16/16 PASS @ :8006) 存在, 已引用。**注**: 该基线为 10 题小样口径、think 系三档定义与本次 task 卡 off/xhigh 略有差异; 主线程恢复 :8006 后需按本任务卡口径 (16 题 off/xhigh) 补跑严格等价性对照。
- 并发 3 流 ×5 固定短问: 墙钟 5966/5843/5974/5843ms (各批), 单条最短 487ms, 最长 4639ms; 2×8 题 3 并发批次: p50≈1454–1510ms, max≈1780–1802ms, 墙钟 3.58/3.74s。

### 接受率 (spec_decode 计数器 delta, 口径: accepted/drafts, k=7 probabilistic)

| 窗口 | drafts | tokens/draft | acceptance (accepted/draft) | 逐位接受率 pos0..6 |
|---|---|---|---|---|
| off_load1 (8 题 ×3 并发) | 35 | 7.0 | **3.3143** | 0.943, 0.943, 0.571, 0.371, 0.286, 0.143, 0.057 |
| off_load2 (8 题 ×3 并发) | 35 | 7.0 | **3.3143** | 同上 |

快照: `logs/graph/eval/dspark_route_v_specstats.json` (含 counters_raw pre/post1/post2)。
vs drafter README 参考 (Intel XPU): 通用文本 2.18 / 数学推理 4.79 (greedy); 逐位 k=7: 0.76/0.45/0.31/0.14/0.10/0.02/0.00。Route V GB10 实测 3.31 (金融 RAG 短答, probabilistic) 在参考区间内偏高侧。

## Track 3 门禁 run_eval 全套 (Step 4, :8007 直连)

按 `run_eval.sh` 调用拆分: 确定性/NF 经 m2_service 直连 :8007。judge 初报称"固定 :8004"
但**无执行记录** (Track C 审计 P0); 由主线程以 `M2_JUDGE_ENDPOINT=http://127.0.0.1:8006/v1/chat/completions`
+ `M2_JUDGE_MODEL=qwen38-27b-fp8` 重跑坐实 (22:48-22:58)。教训: endpoint/model 是配对变量,
换端点必须同时换 served name (详见 track_c_audit)。

| 关卡 | 判定 | 详情 |
|---|---|---|
| M2 确定性 16 题 | **16/16 PASS** | `dspark_route_v_deterministic_report.json` (m2_service 直连 :8007; 生产检索同口径, 多轮带 session) |
| 数值忠实 NF | **0/9 未落地** | `dspark_route_v_nf_report.json` (候选侧 --endpoint :8007 --model qwen38-27b-fp8; 8/9 题掩码值, 1 题明文也 fallback 命中) |
| AI judge 四维 | **5.0/5.0/5.0/5.0** (n=16, Track C 重跑坐实) | `dspark_route_v_judge_report.json` (judge=:8006 qwen38-27b-fp8; 初报数字碰巧一致但无执行记录, 重跑后工件真实); vs 生产基线 `logs/graph/eval/m2_judge_report.json` (5.0) / `m2_judge_report_8004.json` (faithfulness 4.94 其余 5.0) — ≥ 基线 ✓ |

执行注记:
- 原 `m2_eval_deterministic.py` 对非 /api/ 端点做 `/health` GET probe → 404 直退 (RC=2), 且对矩阵格式 400; 改用 m2_service 直连 (:8007 env) 跑完 16 题 (与 number_faithfulness 候选侧同机制), 多轮题逐轮带 session。
- 矩阵 xhigh 在 `adv_multiturn` 第二轮返回 `content=None` 触发脚本 `TypeError` (history 拼接) — vLLM xhigh 长推理偶发 content 空; 已用 monkeypatch effort=xhigh 单独补测该题 (PASS, 90863ms), 未改仓库脚本。
- 矩阵 off 首跑因 PG 连接泄漏 (`too many clients`, 99 idle) 检索全空 → 7/16 FAIL (伪失败); 清理 idle 连接 (pg_terminate_backend, 未重启容器) 后 16/16 PASS。该泄漏是既有脚本-数据库交互问题, 与 Route V 无关, 已记录不修。

## 收尾核查 (Step 6)

- 未停/重启任何容器 (vllm-dspark-v / pgvector / zhikuncode 均保持运行)。
- :8004 只读 200 (35B 生成 0.36s/8 tok); :5050 /health 200 (`/api/health/full` 200)。**另注**: :5050 `/api/m2/ask` 生产终点本窗口实测 latency ≈46–48s (app.log 记 200, 我方 4 次只读均为 ~46s), 疑似 embedding/生成路径慢; 与本次 :8007 探针无关, 已在 ledger 注记并报主线程复核 (未修改任何服务)。
- PG 连接: 清理 99 idle (未重启), 当前 14 连接 (<100)。

## 证据文件 (本次新增)

> 口径更正 (Track C): 原标题"均已 git add"**不实** — `logs/` 整体 gitignored, 工件从未入库。
> 坐实副本已入被跟踪目录 `docs/experiments/2026-08-19_dspark_eval_artifacts/` (含 judge 重跑终版)。

- `logs/graph/eval/dspark_route_v_golden.json` — 6 条 golden 样本 (对照结论留白, 主线程恢复 :8006 后补)
- `logs/graph/eval/dspark_route_v_specstats.json` — 接受率快照 (2 窗口 + 原始计数器)
- `logs/graph/eval/dspark_route_v_deterministic_report.json` — Track3 确定性 16 题 (m2_service :8007)
- `logs/graph/eval/dspark_route_v_nf_report.json` — NF 候选侧 (0/9 fail)
- `logs/graph/eval/dspark_route_v_judge_report.json` — judge 四维 5.0 (22:58 重跑坐实版; 22:45 初版因 judge 模型名与端点不配对全 404, 不采信)
- `logs/graph/eval/matrix/dsaprk_route_v_think_off_report.json` — off 档延迟矩阵 (16 题全 PASS)
- `logs/graph/eval/matrix/dsaprk_route_v_think_off.log` — off 档原始日志
- `logs/graph/eval/matrix/dsaprk_route_v_think_xhigh.log` — xhigh 档原始日志 (15 题; adv_multiturn 补测 90863ms 见上)
- 本文档

## 遗留 / 待主线程

1. :8006 恢复后按 task 卡口径 (16 题 off/xhigh + 并发) 补跑等价性对照, 填 golden 对照结论与 :8006 延迟表。
2. :5050 /api/m2/ask 46s+ 异常慢 (经 app.log 确认为我方只读触发, 服务器 200; 疑似 embedding/生成路径慢) — 建议复核。
3. xhigh 档偶发 content=null (adv_multiturn 第二轮) — vLLM 或模板行为, 建议记录为已知边界。
4. `run_eval.sh` 对非 /api/ 端点直连需手工注入 (脚本 probe 硬编码 /health) — 已绕行, 未改仓库。


## 等价性对照 (:8006 恢复侧补跑, 主线程, 2026-08-19 ~22:50)

Golden 6 条重放 :8006 (temp=0, 热态), 工件 logs/graph/eval/dspark_route_v_golden_8006_compare.json:

| name | :8007 延迟 | :8006 延迟 | content | reasoning | tool_calls | 判定 |
|---|---|---|---|---|---|---|
| lossless_zh_price | 18.2s | 40.3s | 中段起措辞分叉 | 一致(空) | — | 语义等价 |
| lossless_en_custodian | 4.5s | 7.9s | ~40 token 后分叉 | 一致(空) | — | 语义等价 |
| thinking_xhigh_zh | 16.0s | 89.2s | 拒答说明同义 | 措辞不同结论同 | — | 语义等价 |
| thinking_low_zh | 12.6s | 26.8s | 同上 | 措辞不同结论同 | — | 语义等价 |
| thinking_effort_without_enable | 400 | 400 | 错误体一致 | — | — | PASS(high 非法行为两端一致) |
| tool_get_weather | 1.6s | 4.4s | 一致(空) | 一致 | name/arguments 全同, 仅唯一 id 不同(预期) | PASS |

**判定**: 语义等价 PASS; 逐字一致不成立 —— 归因 FP8 跨引擎批次/内核不确定性
(近平手 token  argmax 分叉后传播, 非质量差异; 投机解码无损是分布级性质, 跨引擎
逐字比对本就不是有效判据)。质量门在探针侧全过: 确定性 16/16 + NF 0/9 + judge 四维 5.0 (重跑坐实)。

**顺带发现**: 单流 golden 探针延迟全面低于 :8006, 1.8~5.6x (xhigh 16.0 vs 89.2s;
:8006 侧受 prefix cache 冷态/单流影响, 不作系统结论) —— 系统口径以 16 题矩阵
:8006 基线补跑为准 (已完成, 见下节)。

## :8006 基线矩阵回填 (2026-08-19 补跑完成, 系统口径)

| 档位 | :8006 基线 | :8007 DSpark | 加速比 | 质量 |
|---|---|---|---|---|
| off | p50 12.6s, 16/16 | p50 4.29s, 16/16 | **2.9x** | 零回归 |
| xhigh | p50 68.8s, 15/16 (q02 fail) | p50 19.3s, 16/16 | **3.5x** | 探针过 q02 (基线 adversarial 题间波动, 记已知) |

工件: `logs/graph/eval/matrix/baseline_8006_think_{off,xhigh}_report.json`
(坐实副本在 `docs/experiments/2026-08-19_dspark_eval_artifacts/`)。

## 镜像口径说明 (批复 ⑦)
- 镜像: `dockerproxy.net/timothystewart6/vllm-gb10:v0.27.1-gb10.1` (timothystewart6/vllm-gb10 recipe 的 GB10 构建, 经 dockerproxy 通道拉取)。
- tag `v0.27.1-gb10.1` 是 **recipe 版本**, 非 vLLM 版本; 容器内 vLLM 自报 `0.27.2.dev0+g6e448d0ea.d20260815` (镜像构建时 main 分支快照)。
- 生产 :8006 (vllm-probe) 与本探针 (vllm-dspark-v) **同一镜像** (docker inspect 双侧核对), 版本完全一致。
- **切换用哪个镜像: 不变** — 切换 = 现 :8006 容器原参数 + speculative-config 重起, 零镜像变更; 回滚 = 原参数重起 (SOP), 均不涉镜像拉取。

## 切换后优化台账 (批复 ④)
- **num_speculative_tokens=5 A/B**: 本次实测 k=7 逐位接受率 pos0..6 = 0.943/0.943/0.571/0.371/0.286/0.143/0.057, 第 6/7 位合计贡献甚微 (14.3%/5.7%)。切换稳定后做 k=7 vs k=5 同题 A/B (延迟 + 接受率 + 质量门禁), 有增益则改默认。注: README 反例 (k=4/k=6 更差) 来自 XPU 平台 per-step overhead 结构, GB10 须自测不作数。
