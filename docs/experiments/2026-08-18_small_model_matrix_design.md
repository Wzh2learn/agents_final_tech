# 小模型矩阵实验设计（K4，科研探索 4/6）
> 前置: 演示冻结窗（08-18 00:30 起至明日演示结束）内本设计只产出不执行；全部候选加载/执行均待演示结束、STATE.md 解除冻结且用户批准

> 状态: 设计稿（只读，未执行） | 更新: 2026-08-18 | 类型: K4 科研探索产出（仅新增本文, 不动配置/代码/运行时）
> 依据: docs/33 §6/§2.2/§9 K4、docs/32 模型卡与三档思考实证、DECISIONS.md 08-16/08-17 模型卡与预算门、K2 `config/eval_checkpoint_trees.json`、S3 Route B 结论（Qwen3.8-35B-A3B 无官方开源权重, CLOSED）
> 目标: 回答导师业务层要求"试用其他小模型来完成任务"；一鱼两吃 = 业务选型 + 论文章 3 记忆感知路由的路由实验数据

## 0 结论速览

- 候选 6 项，其中 **5 项磁盘已有零下载成本**：:8006 27B-FP8（现网）、Qwen3-14B Q4（退位权重）、Qwen3-8B Q4、Qwen3-4B Q4、Qwen3-VL-8B Q4+mmproj（间歇验证过，VERIFIED-CLOSED）
- 需下载 1 项（小, 已算入预算）：TO BE CONFIRMED，如 Qwen3-Next-3B-A3B（hf-mirror/ModelScope x2 通道均 PD）
- **内存算术结论 = 磁盘权重全部过预算门**（见 §3 表；:8006 现状 GMEM 0.30 即实测门内证据）
- 思考档位矩阵（§5）把"1 个模型 = 数量 ×3"的维度展开：27B-A3B-14B-8B-4B × {off, low, xhigh}，一个 N 文件一次卸载一个 27B vLLM 并列
- **执行窗口本设计仅给建议，所有加载/替换需用户批准（预算门第 2 步），本设计不构成任何批准**

## 1 目标与范围（只出设计不动运行时）

- **本任务红线**：不加载任何模型；不改任何配置/代码/运行时；不调用任何推理端点（含 /health）；只读文档与工件
- 执行未来（用户拍板后）: 在独立端口（:8007 或临时 :801x 空位）起临时 llama.cpp/vLLM 服务；:8004/:8006/:8008/:5050/opencode 等一系列现网组件零触碰
- 产出即本文 + 后续（K6 汇总）注册 docs/INDEX.md；不写 memory/（收口时由 Loop D 统一更新）

## 2 固定题库（直接引用 K2 检查点协议，不另造）

题库与评分统一走 K2 检查点树，是矩阵的"尺子"，**不新建题**。同一把尺子下逐模型产出 → 按 GTA-2 Algorithm 1 聚合 Root Score（0-10）。

### 2.1 QA 树负载（文本，全部走生产同口径检索链路）

| 分组 | 规模 | 内容 | 依据 |
|---|---|---|---|
| m2_deterministic | 16 题 | tests/fixtures/m2_eval_questions.json v3（7×exact_numeric / 9×contains_keyword / 15×source_required / 1×refusal_expected + 4 道对抗题 adv_ocr_meta / adv_cross_doc / adv_refusal / adv_multiturn）| 确定性 16 题基线 16/16 |
| 数值忠实度 NF | 9 条 | scripts/m2_eval_number_faithfulness.py（6 存量抽测 + 3 对抗题：跨期诱导/不存在实体/掩码探针）| 基线 0/9 fail |
| judge 抽样 | 16 题全量或 ≥8 题子集 | scripts/m2_eval_judge.py 四维 rubric（faithfulness / numeric_correctness / citation_quality / refusal_appropriateness；reference 隔离 + 多轮拼接检索上下文）| 基线 4 维均 5.0（08-09 attack 后定稿口径）|

- 运行方式：候选侧各脚本显式 `--endpoint http://127.0.0.1:<PORT>/v1/chat/completions --model <served>`（脚本已支持：m2_model_probe_benchmark.py `deterministic` 模式 + m2_eval_number_faithfulness.py `--endpoint/--model/--out` + m2_eval_judge.py `M2_JUDGE_ENDPOINT`/`M2_JUDGE_MODEL`）
- 候选不得写生产报告路径：所有输出 `logs/graph/eval/matrix_<cand>_<task>.json`，避免覆盖基线工件
- **检索不随模型换**：PGVector 137 embeddings 固定；每个候选只换生成端点（KA 抽样跑 `m2_model_probe_benchmark.py --mode matrix` 的固定 10 题 prefill，只读 nvml 记录）

### 2.2 parse 树负载（视觉样张 scenario1）

- parse 树 5 叶（doc/table/field/reconcile）只用基线场景样本（scenario1 全量 15 源 + RAG QA 15/15 候选池），**严格走现有 m1_scenario1_regression.py 全量口径（--full-m1），不另造样本**；OCR 三源（华泰紫金/TraFax/WaveFax）留作视觉专项候选（VL-8B）验证，入场时间窗在视觉方格内
- 视觉样张：WaveFax 传真 / 嘉合 PDF 首页（与 docs/32 §2.3 一致的 2 张已验证样张），视觉专项候选（VL-8B 等）跑转写等价（等价 = 与 :8004 vision 基线转录一致，阈值 = 现行 m1_scenario1 容差 ±10pp/±1 表）
- 本矩阵不触 parse 树质量叶：parse 树根 Root Score 仅用于汇总口径，候选侧 parse 负载以表级/字段级命中（scenario1）为达成度；视觉专项按 §5.2 追加进矩阵

## 3 候选模型清单 + 内存算术（可复算，公式+数字，非拍脑袋）

### 3.0 机器口径与公式（GB10，SOP §3 基准）

- 统一内存 MemTotal = 121GB（CUDA 可见口径 130.6GB）
- 带宽 = 273GB/s（dense 解码带宽上限，27B dense FP8 单流 ~4.8 tok/s 实测）
- 生产常驻占用（近似）：:8004 A3B Q4_K_M+mmproj(−c 65536) + 检索模型栈（bge-reranker-v2-m3 + qwen3-embedding-0.6b CPU）≈ 30GB
- 系统余量硬约束 ≥10GB
- **公式 1（llama.cpp 权重预算）**：进程权重+context+KV ≈ 文件大小 ×1.125（Q4 收益, 实测主机内存近似）→ 候选权重文件 < 可用预算即准入门内
- **公式 2（vLLM GMEM 预算）**：`0.30/0.27 实测比值 × 权重 1.0 起算`；121 − 30(生产) − 10(系统余量) = 81GB vLLM 可分配上限；0.30 ≈ 39GB（27B-FP8 探针实测值）→ 27B 当且仅当运行在 :8006 现状（GMEM 0.30）才在门内；新开 vLLM 实例权重必须 ≤ ~40GB，且只许调低不许调高 GMEM
- **公式 3（并行切换规则）**：多实例并列 = 121 − 生产常驻 − 已有 vLLM(含 :8006) − 系统余量 ≥ 0；否则"停旧探针再上"（SOP §3 原句），本文给出时间窗

### 3.1 候选表（磁盘大小=文件系统实测 08-18；内存算术附公式）

| 候选 | 参数量/量化 | 磁盘文件 | 内存算术（按公式） | 预算结论 |
|---|---|---|---|---|
| C0 :8006 27B-FP8（对照/现网） | 27B dense FP8 MTP | hf/Qwen3.8-27B-FP8 ≈29GB | vLLM GMEM=0.30 ≈39GB（08-16 实测）| 门内（不动）|
| C1 Qwen3-14B Q4 | 14B Q4_K_M | gguf/qwen3-14b/Qwen3-14B-Q4_K_M.gguf = 9.0GB | llama.cpp：9.0×1.125≈10.1GB + ctx(32768) ≈ 8.9GB ≈ 19GB < 40(27B 预算下限, 见注) | 门内（零下载，退位权重）|
| C2 Qwen3-8B Q4 | 8B Q4_K_M | gguf/qwen3-8b/Qwen3-8B-Q4_K_M.gguf = 5.0GB | 5.0×1.125≈5.6GB + ctx ≈ 8.2GB ≈ 14GB | 门内（零下载）|
| C3 Qwen3-4B Q4 | 4B Q4_K_M | gguf/qwen3-4b/Qwen3-4B-Q4_K_M.gguf = 2.5GB | 2.5×1.125≈2.8GB + ctx ≈ 5.8GB ≈ 9GB | 门内（零下载）|
| C4 Qwen3-VL-8B Q4+mmproj（视觉专项）| 8B VLM Q4_K_M | gguf/qwen3-vl-8b = 5.0GB + mmproj 0.75GB | 5.75×1.125≈6.5GB + ctx ≈ 9.7GB ≈ 16GB | 门内（零下载；旧探针 VERIFIED-CLOSED，重启手册见 THREADS）|
| C5 待确认（≤14B，mini 化 open-source）| 待选 | （磁盘无，需下载）≈3–5GB | 按公式 1 预估 ≈ 4–7GB 权重段 | 下载前需过预算门复核（约 0.2h 下载+0.1h 算术=每项, 通道 hf-mirror/ModelScope 见 §4.4）|

> 注（-ngl 判定）：llama.cpp 在 GB10 可完全 offload（-ngl 999，与 :8004 同职责）；上表 ctx=32768 按 :8005 旧 14B 曾用配置（8.9GB 估按 0.014B tok/ctx 粗估），执行时以 SOP 复核为准。
> 上表"可用预算"口径 = 窗口内可用的非生产槽（≥40GB 由上表 27B 探针 + KV 估算；执行时按 §4 窗口再复核）。

**并行算术（同时最多 1 个实验实例）**：C1 19GB / C2 14GB / C3 9GB / C4 16GB / C5 ~7GB 均 < 40GB；若与 :8006（39GB）并列则超 121−30−39−10=42GB 均不足 → 一律"停 27B 探针再上"（只停 :8006 实验实例不影响生产），时间序列按 §4.3 排布；不出现 2 个实验实例同时开。

## 4 指标定义（quality-cost Pareto）

### 4.1 质量轴 Score = K2 检查点 Root Score（0-10）

- 每候选独立跑固定题库（§2）→ `scripts/eval_checkpoint_aggregate.py` 同一协议聚合 → 末端产出 Root Score（parse/qa 两树可分别报告）
- STABLE 判据沿用 K2：≥90% 叶子 ≥7 且无 hinge 叶子 ≤7
- **公式 4（Score/Cost 核心）**：Score = Root Score（0-10）；Cost = token 数（completion+reasoning 实测）× 单价代理 f(model, q)（见 4.3）
- judge 维作为路由输入的补充输出：四维均分（faithfulness/numeric/citation/refusal）另行列报（K2 已把四维映射为叶子）

### 4.2 成本轴 Cost（两档，默认 token 代理）

- **Cost_token（默认）**：`Cost = Σ(completion_tokens + reasoning_tokens) × 单价代理 u(model)`；u 由量化档位归一：u(Q4)=1.0、u(FP8)=1.4、u(BF16)=1.5（无实际计费，只是相对代理，五档候选之间可比；绝对值可并列报告 token 总数）
- **Cost_latency（候选报告同时出）**：p50 / p95 延迟（wall_ms）+ 吞吐（tok/s，由 duration_ms 与 completion/reasoning token 计数推出）
- 内存占用：PSS（运行时实测 `nvidia-smi`/`free` 口径，进程常驻 = 基线进程差值与 SOP 基准对照）列入每候选报告

### 4.3 每模型思考档位矩阵（档位即"档位-模型"一格一格跑）

按 docs/32 实证合法集（Qwen3.8 系 {off, low, medium, xhigh}，Qwen3 GGUF 同构 {off, low, medium, xhigh} 预期）：

| 档位 | off | low | medium | xhigh |
|---|---|---|---|---|
| 27B-FP8（:8006）| ✓（A 档基准 10.31s/题）| ✓（B 档 23.8s）| ✓ | ✓（C 档 60.6s）|
| A3B（:8004）| ✓（现网 1.3-1.9s/题）| — | — | —（不做，不动生产）|
| Qwen3-14B Q4 | ✓ | ✓ | ✓ | ✓ |
| Qwen3-8B Q4 | ✓ | ✓ | ✓ | ✓ |
| Qwen3-4B Q4 | ✓ | ✓ | ✓ | ✓ |
| Qwen3-VL-8B（视觉专项）| ✓ 转写 | — | — | — |

- 每个候选先跑 off（快路任务）与 xhigh（准路任务）两档票（16 题 + NF + judge 抽样）；low/medium 档只在 off/xhigh 结果需要区分度时加跑（二值矩阵 → 论文路由数据足够）
- 矩阵总格子 = 5 文本候选 × 2 档 + 4 档细分（视区分度）+ 1 视觉 = ~11 基础格，每格约 1.5-2.5h（§4.4）

### 4.4 每模型预计耗时（串行×1，并发度 1，都在独立端口）

| 候选 | 启动（换载）| 16 题 deterministic | NF 9 条 | judge 抽样 | 视觉样张 | 小计 |
|---|---|---|---|---|---|---|
| C0 :8006 27B | 0（现网）| 180s（实测 sum）| ~120s | ~300s | 72s×2 | ~20min |
| C1 14B Q4 | ~5min 冷启 | ~20min | ~10min | ~15min | — | ~50min |
| C2 8B Q4 | ~4min | ~15min | ~8min | ~12min | — | ~40min |
| C3 4B Q4 | ~3min | ~10min | ~6min | ~10min | — | ~30min |
| C4 VL-8B 视觉 | ~5min | — | — | — | 3-8min×2 文件 | ~20min |
| C5 待确认 | 下载≈20min+启动≈5min | 同 C2 量级 | 同 C2 | 同 C2 | — | ~1h |

- 全矩阵单轮（6 候选 × 2 档）= **约 0.5 天净执行**（不重叠时 4h-6h）；若按档位细分（low/medium）×候选 ≈ +2h → 建议分 2 个时隙，每时隙 4h 内（演示冻结核对窗口见 §6）

## 5 执行窗口建议（错峰条件 + 准入流程 + 回滚）

- **演示冻结窗外**：当前演示冻结窗（08-18 00:30 起，至演示结束）不执行任何加载；首个候选最早在演示结束且 STATE.md 解除冻结后
- **:8006 空闲窗口**：实验实例与生产 :8006 同唯一 GPU 槽位 → 实验时隙必须选 :8006 无生产推理时的窗口（如夜间）；:8006 只可停探针实例（不影响 :8004/:8005/:5050）
- **Loop B 不误报**：Loop B 每 30min 验证冻结节点哈希；实验进程/端口变化不触碰冻结文件；实验前后 diff `git status` 确认只多 `logs/graph/eval/matrix_*`（gitignored）；Loop B 周期以 30min 为粒度，建议实验时隙与 Loop B 周期错开（如 :40-:10 段），避免 Loop B 快照与换载窗口重叠
- **模型准入预算门流程（每候选必走，含 C0 重载/换档）**：
  1. 内存算术：按 §3 公式重算（权重文件大小/量化/Q4 系数/KV-ctx），磁盘文件为实测值
  2. 用户窗口批准：Loop D（用户）确认窗口与换载顺序；未经批准不加载（现网 :8006/:8004 属已批准驻留，实验候选全部属待批准）
  3. 执行后验证：READY 判据 curl /health + /v1/models 列表，服务名唯一不与现网冲突
- **每模型预计耗时**已列 §4.4 供用户排程；执行顺序 = C0 → C1 → C2 → C3 → C5 → C4（视觉最后，影响面小）

## 6 风险与红线

- **M1 热路径锁 :8004 不动**：:8004 A3B 是长期驻守生产组件（DECISIONS 08-17 模型拓扑定型），实验资源一律绕开；若有状态不符，立刻停止并回滚
- **实验只用 :8007 或临时端口**：C0 走 :8006 现网端（只读调用，先取样避免压测）；C1-C5 一律 :8007 或 :801x；不占用/不覆盖任何生产端口
- **回滚 SOP**：
  - llama.cpp 后端（C1/C2/C3/C4/C5）：`kill <实验 llama-server pid>` + `docker stop <实验容器>` 即退，不触碰生产
  - vLLM 后端（C0 仅取样）：`docker stop vllm-probe` 即退；生产 :8004 用 DECISIONS 08-16 记录命令重启，预计 <2min（不执行，仅留档）
  - 任何换载必须先 `bash scripts/gb10_reclaim_page_cache.sh 35`（SOP FM1 必做）；GMEM 只许调低不许调高（FM2）
- **数据红线**：甲方数据零进入论文产物（doc 级已含）；matrix_* 报告只留 stats 不留原始答案文本超过样本句（防信息泄漏，与既有 eval 工件同规）；文档/截图引用一律脱敏

## 7 验收（本文自检）

- 每候选内存算术含公式+数字（§3 表）✓
- 固定题库直接引用 K2 协议与既有脚本（§2）✓
- 指标定义含 Score/Cost + p50/p95 + 内存占用 + 档位矩阵（§4）✓
- 执行窗口与现有红线/预算门一致（§5/§6），未虚构已批准窗口（全部待用户拍板）✓
- 本任务仅新增本文，未改任何配置/代码/运行时 ✓
