状态: 活跃 | 更新: 2026-08-16 | 取代/被取代: 无

# 32 模型升级与多 Agent 再思考

> 模型升级专项 (2026-08-15/16) 沉淀文档。P0 侦查 + P1 探针 + P2 基准的事实记录,
> 以及旧模型约束解除后可重开的多 agent 设计菜单。**菜单只列不做, 实施需用户拍板。**
> 甲方入口仍是 docs/23; 本文档为内部技术口径。

## 1. 为什么升级: 旧栈约束盘点

| 设计点 | 旧栈约束 | 来源 |
|---|---|---|
| agent 路 18s 超时 | llama.cpp 单进程 slot 争用, agent 路实测 39-55s, 超时后 77% 流量回落直连 | THREADS A2 遗留 / B4 仪表 |
| 快路延迟天花板 | GB10 带宽 273GB/s, 27B dense FP8 单流解码 ~10-15 tok/s; A3B MoE 激活 3B 才有 2-3s 快路 | 硬件算术 |
| skill 加载上下文膨胀 | m2-qa 每轮加载 playbook + 16 skill 元数据, 35B-A3B 32k ctx 下是负担 | 延迟排查靶子 (08-15) |
| judge 自评漂移 | judge 与生成同模型同档, 无独立复核距离 | eval 基线 4.94 口径 |
| vision 链路分裂 | :8007 停摆, mmproj 挂 :8004, M1_VLM_ENDPOINT 指向经两次迁移 | THREADS VLM 条目 |
| 上下文 32k-64k | 跨表聚合/整文档 QA 受限 | llama-server -c 配置 |

## 2. Qwen3.8-27B + vLLM 探针事实 (P0-P2)

### 2.1 模型卡
- 仓库: Qwen/Qwen3.8-27B-FP8 (hf-mirror), Apache 许可
- 架构: model_type=qwen3_5, 混合 linear_attention + full_attention (每 4 层 1 个 full), 原生 VLM, MTP 1 层, 262144 ctx
- 部署: timothystewart6/vllm-gb10:v0.27.1-gb10.1 (docker, CDI GPU), 探针端口 :8006, gpu-memory-utilization 0.30 (实测值; 0.27 差 0.44GiB 失败, 只许调低不许调高), max-num-seqs 32, max-model-len 32768, 生产栈零冲突
- 回滚依据: :8004/:8005 完整 llama-server 命令行已录 (DECISIONS.md 模型卡 + dispatch_log 08-15 P0 条目)

### 2.2 思考控制实证 (chat_template.jinja + thinking-probe 4/4 PASS)
- enable_thinking 默认 true; false 时模板注入空 think 块 -> **零推理 (快路)**, 实测 reasoning=0
- reasoning_effort 合法集: **xhigh(默认) / medium / low** — prompt 引导式, 非硬 token 上限; 实测 reasoning 量单调 (46/57/118 chars, 7.7/9.3/10.7s)
- thinking_budget: 模板不存在该参数, **传入被忽略**, 行为等同默认 xhigh (实测坐实)
- "high" 非法 -> HTTP 400 (与部分外部文档口径不同, 以本机实测为准)
- vLLM 0.27 口径: reasoning 输出在 message.reasoning 字段 (非 reasoning_content)
- 启动 SOP (三次失败换来的): ① scripts/gb10_reclaim_page_cache.sh 回收 page cache (CUDA mem_get_info 不计缓存, 权重读盘又会灌满) ② GMEM=0.30 (0.27 差 0.44GiB) ③ --max-num-seqs ≤78 (混合架构 Mamba 状态块约束) ④ 挂载持久编译缓存。冷启动 ~7min, 热启动 ~5min。

### 2.3 基准数据 (P2, 全部实测)

原始报告: logs/graph/eval/model_probe_*.json (GB10, gitignored)。确定性/并发经
benchmark main() 覆写 M2_LLM_ENDPOINT 后走 m2_service 生产检索路径, 仅端点/模型
换成 :8006 (机制已核查, 非误打旧栈; 时延画像与旧栈 OLD 报告交叉印证)。

**三档思考矩阵 (固定 10 题, 探针直连路):**

| 档位 | p50 | p95 | 平均 completion |
|---|---|---|---|
| A_off (thinking off) | 10.31s | 15.76s | 49.2 tok |
| B_effort_low | 23.82s | 47.38s | 199.6 tok |
| C_effort_xhigh | 60.60s | 65.38s | 431.2 tok |

对照: 旧栈 A3B 同题 1.3-1.9s/题 (model_probe_deterministic_OLD.json), 约 6x 差距;
27B dense FP8 单流解码实测 ~4.8 tok/s, 与 GB10 273GB/s 带宽硬件算术一致。

**确定性 16 题:** 候选 16/16 PASS (6-29s/题, 首题冷态 28.9s); 旧栈 16/16 PASS
(1.3-1.9s/题)。零回归。

**并发 3 流:** makespan 70.6s vs 串行总和 207.1s (批处理层压缩 2.9x); 但单请求
wall 67-70s, 较串行劣化 ~7x → 带宽受限, 并发只提总吞吐不提单请求延迟。对照旧栈
slot 争用顽疾: vLLM 批处理不死锁不阻塞, 但本机"并发加速单请求"不成立。

**judge 四维:** 旧模型交叉评候选答案 = 忠实度/数值/引用/拒答全 5.0 (基线 4.94);
候选自评 = 5.0x4。

**NF 数值忠实:** 未对候选重跑 — 脚本锁 :5050 生产端点 (红线不重启), 数值质量由
确定性 exact_numeric + judge numeric_correctness 覆盖; 候选侧 NF 留 P3 切换验证。

**视觉 (逐字转写+表格结构, thinking off):**

| 样本 | 候选 :8006 | 旧栈 :8004 mmproj | 质量 |
|---|---|---|---|
| WaveFax 传真 | 72.2s (图 16196 tok) | 31.0s | 转写等价 |
| 嘉合 PDF 首页 | 75.7s (图 2184 tok) | 28.9s | 转写等价 |

候选图像 token 随分辨率变化, 旧栈 mmproj 固定分片 (4012/2182)。视觉质量平手、
延迟旧栈快 2.3-2.6x — M1 OCR 预算 (M1_OCR_BUDGET_SECONDS) 是硬约束, 视觉链路
切换需谨慎。注: jiahe 首轮漏传 --compare-endpoint, 已补跑对照。

### 2.4 闸门判定与切换菜单 (P2 结论; 2026-08-16 用户拍板: A 落地 + B 并行探针)

质量维度: 确定性 16/16 零回归 + judge 5.0≥4.94 + 视觉平手 → **质量 GO**。
延迟维度: A_off p50=10.31s > 8s 闸门 → **快路不达标, 全量替换不通过**。
按专项规则出两条对比路线:

| 路线 | 内容 | 工作量 | 风险 | 备注 |
|---|---|---|---|---|
| A 双模型分工 | A3B 留 :8004 (快路 1.3-1.9s + 视觉 mmproj 29-31s); :8006 27B 接 agent 验证链路 (B/C 档)、judge (C 档)、深度问答 | 0.5-1d (路由 flag + JUDGE_ENDPOINT 指向 + 档位参数) | 低 (旧栈零改动, 探针已证共存) | GB10 121GB 统一内存双栈共存已由 GMEM 0.30 实证 |
| B Qwen3.8-35B-A3B MoE 探针 | 同栈探针 35B-A3B MoE: 若快路保住 2-3s 且质量近 27B dense → 单栈全量替换可行 (视觉需重验) | 1-2h 下载 + 1h 基准 | 中 (GB10 MoE expert 加载/带宽特性未测) | 先查 hf-mirror/ModelScope 有无 FP8 版 |

推荐: **A 先行** (本周可落地收益 = 修 agent 路 39-55s 与 judge 同模型漂移两个
顽疾), **B 并行探针** (数据说话, 决定是否未来收敛单栈)。

**拍板记录 (2026-08-16)**: 路线 A 双模型落地为主线 (S4 实施), 路线 B 并行探针,
数据说话。官方 pairing 依据: Qwen 团队官方定位 "Qwen3.8-27B Dense +
Qwen3.8-35B-A3B 是一对" (27B 管质量任务, A3B 管快与并发; 出处 Qwen/Qwen3.8-27B
模型页 discussions/43, hf-mirror API 401 未能直连原文, 转述口径); 3.8 开源仅 27B
与 35B-A3B 两个规格。A/B 关系: **A = 现在落地** (27B 接验证链/judge/深度问答,
A3B 守快路+视觉), **B = 快路升级探针** (若达标, 快路同步升级 3.8 代, 单栈收敛
重新可行), 互补不互斥; B 达标后的采纳需二次拍板 (需 :8004 重启窗口)。

**B 门槛现状 (2026-08-16 22:00 实测)**: 35B-A3B 权重两通道均未发布 — hf-mirror
resolve 端点全 404 (官方 base/-FP8/unsloth/ggml-org/lmstudio-community/bartowski
GGUF), ModelScope Qwen org 3.8 系列仅 27B/27B-FP8/2.4T-A95B; 27B 官方 README
无 pairing/MoE 兄弟机型字样; hf 上 08-15 新现 distill 仓库为空占位。处置:
routeb-watch 监视器 (GB10 tmux) 每 10min 自动探测双通道, 发布即自动下载 FP8/
GGUF-Q4_K_M 至 ~/wzh/models/ (日志 ~/wzh/routeb_watch.log); S3 探针顺延至权重
到位, 不阻塞 S4。

## 3. 可重开的多 Agent 设计菜单 (只出菜单, 等拍板)

| # | 菜单项 | 内容 | 工作量 | 风险 | 推荐 |
|---|---|---|---|---|---|
| M1 | 思考档位作为一等路由维度 | "快与准"菜单从"两个后端"变为"一个模型两档思考": A_off 快路 + C_xhigh 准路; 路由开关 = chat_template_kwargs, 秒级切换无进程动作 | 0.5d | 低 | 推荐 (路线 A 核心; 注意 A 档 10.3s 基线, 只适用 agent 验证路, 交互快路仍归 A3B) |
| M2 | agent 路超时与回落预算重议 | 18s 超时按 P2 实测重定 (含 warm-up); 回落率目标从 77% 降至 <20% | 0.5d | 低 | 推荐 (18s < C 档 p50 60s, 超时必须档位感知, 否则验证路被回落机制整段吞掉) |
| M3 | judge 分档独立化 | 生成 off/low 档 + judge xhigh 档, 同模型不同档拉开复核距离; 对照跨模型 judge | 0.5d | 低 | 推荐 (P2 已验证跨评 5.0; 档位分离零成本) |
| M4 | 长上下文整文档 QA | 262k ctx 下按产品/按样本整本入库问答, 减少 chunk 截断型失真 | 1-2d | 中 (检索口径变化) | 待拍板 (需先抬 max-model-len 并重验 KV 预算) |
| M5 | vLLM 批处理夜间任务 | 全量重解析/批量核验走并发流, 吃满 continuous batching | 1d | 低 | 谨慎推荐 (并发提 makespan 但单请求慢, 只适合无人值守批处理) |
| M6 | MTP 推测解码 | vLLM speculative decoding 提快路吞吐 | 0.5d 探针 | 中 (兼容性) | 值得探针 (唯一可能突破快路带宽上限的候选杠杆) |
| M7 | vision 统一 | 单模型同时承担文本+视觉, :8007 文档引擎与 mmproj 链路收敛为一 | 1d | 中 (M1 消费者冒烟) | 短期不推荐 (实测较旧栈慢 2.3-2.6x, OCR 预算风险) |
| M8 | evidence-verifier 重定位 | 强模型下 verifier 从"逐句核对"转"抽样对抗", 省一轮调用 | 1d | 中 | 待拍板 (依赖路线 A 落地后的档位余量) |

## 4. 切换与回滚 SOP (P3 决策输入)

路线 A 获批时: "切换"退化为路由 flag + JUDGE_ENDPOINT 指向调整, 不停 :8004/:8005,
消费者按 flag 分流; 六步验证照旧 (health/full + parse 冒烟 + QA 2 条含 OCR
meta-query + compare 嘉兴民安 + route on + warm 延迟)。
路线 B 获批且数据达标时: 走全量切换 — 停旧 :8004/:8005 -> vLLM 改听 :8004
(消费者零改动: opencode gb10 provider / :5050 M2_LLM_ENDPOINT / M1_VLM_ENDPOINT /
M2_JUDGE_ENDPOINT 指向不变) -> 六步验证 -> B4 台账记切换时间点。
回滚: 旧 GGUF + llama-server 保留 48h (至 2026-08-17 18:00); 回滚 = docker stop
vllm-probe + 按 DECISIONS.md 模型卡命令行重启 llama-server, 预计 <2min。

## 5. 附录: 工件索引
- 探针基准脚本: scripts/m2_model_probe_benchmark.py (thinking-probe/matrix/deterministic/concurrency/vision)
- 探针启动脚本: scripts/vllm_probe_serve.sh; P2 一键: scripts/m2_model_probe_p2_run.sh
- page cache 回收: scripts/gb10_reclaim_page_cache.sh (生产安全, 无 sudo)
- 原始报告 (GB10, gitignored): logs/graph/eval/model_probe_{thinking-probe,matrix,deterministic,deterministic_OLD,concurrency,judge_by_old,judge_by_new,vision_wavefax,vision_jiahe}.json
