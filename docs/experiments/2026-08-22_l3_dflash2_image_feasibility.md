# L3 DFlash2 镜像可行性评估（只评估不实施）

日期: 2026-08-22 凌晨（纯只读: 镜像内查 + GitHub API + hf-mirror 元数据; 未拉镜像未重建, 零配置变更）
结论: **可行。路径 A（等 timothystewart6 新 tag 后 pull）推荐, 路径 B（自建）后备; 当前零动作, 探针必须等 L1 基线之后（时序不变）。**

## 1. 事实核查（全部今日实测）

### PR #52816（DFlash2）— 直连复核坐实
- 状态: **MERGED**, merged_at 2026-08-21T05:27:22Z, base main, merge_sha b389ac29465b（GitHub API 直查, 覆盖 08-21 白天 "open" 快照与 08-21 夜 ledger 更新）。
- 内容: DFlash2 = 新 drafter 架构类 DFlash2DraftModel（grouped dynamic depthwise conv + candidate selector）; 现有 DFlashDraftModel checkpoint 解析不变（向后兼容）; method 仍走 dflash。

### 现镜像（dockerproxy.net/timothystewart6/vllm-gb10:v0.27.1-gb10.1, 22.1GB）
- vLLM 版本串: 0.27.2.dev0+g6e448d0ea.d20260815.cu132（= vllm main 08-15 快照, python3.12 dist-packages）。
- DFlash v1 在位: method="dflash" 合法（config/speculative.py L62/L310/L880-892 + config/vllm.py L2201/L2211）; 架构 DFlashDraftModel→qwen3_dflash.py 注册（registry.py L616）。
- DSpark 在位: method="dspark", Qwen3DSparkModel 注册（registry.py L618）——与 DSpark era 生产行为一致。
- **DFlash2DraftModel 不存在**（全库 grep 零命中）→ incoai checkpoint（architectures=["DFlash2DraftModel"]）现镜像加载必失败。
- commit 对比（GitHub compare API）: 镜像构建 commit 6e448d0ea 与合并 commit b389ac2 **diverged**（ahead 792 / behind 21）→ 合并点不在镜像谱系; 且 vLLM 最新正式 release v0.27.1（08-11）早于合并（08-21）→ **目前没有任何官方 release 含 DFlash2**。

### 权重 incoai/Qwen3.8-27B-DFlash2（只查未下）
- 3.85GB（单一 model.safetensors）, apache-2.0, Qwen3.8-27B 官方配对, tags 声明 vllm+sglang 支持; 镜像源 z-lab/Qwen3.8-27B-DFlash2。
- config 实测: architectures=["DFlash2DraftModel"], dflash_config block_size=8（→ k=8）/ conv_kernel_size=2 / conv_group_size=16 / selector_top_k=16, drafter 5 层 bf16, 262k 位置编码。
- 磁盘: GB10 空闲 2.7T（23% 占用）, 无约束; hf-mirror 通道实测可达。

## 2. 两条路径 + 一条不动

### 路径 A: 等 timothystewart6 新 tag 后 pull（推荐）
- 依据: 该仓库为可复现构建（Dockerfile + versions.env 全 SHA pin + GH Actions + GHCR）, 发布节奏 08-12/08-15/08-15 三连（v0.27.1-gb10.0/1/2）; **其 tag 实为 vllm main 快照**（现用 v0.27.1-gb10.1 内容即 0.27.2.dev0）→ 08-21 合并后出的下一个 tag（versioned 或 registry 中 30 个 sha-* 之一）大概率含 DFlash2。
- 工作量: tag 盯梢（ledger 项, 复核命令见 §4）→ dockerproxy pull ~22GB（~10-30min）→ :8007 探针验证 → GO/NO-GO → 申请 :8006 切换窗。
- 风险: 低-中。旧镜像本地保留即回滚。**注意: 新 tag = vllm main 08-15→新快照（~800 commit 跨度）, 不只 DFlash2**——等价性三连（thinking 各档 / qwen3_xml 工具解析 / chat template）必须全跑, GB10 启动 SOP 需重新标定（GMEM profiling 噪声 #48140 族行为可能变化）; 也可能顺带带入 #46932/#49760/#48140 相关修复（与 vLLM 版本升级长期台账联动记账）。

### 路径 B: 自建镜像（后备）
- recipe 在位: 仓库含 Dockerfile + versions.env + locks/ + CI workflow; 将 vllm pin 抬到 ≥b389ac2 commit, GB10 本地构建（arm64, TORCH_CUDA_ARCH_LIST=12.1a）。
- 工作量: 0.5-1d（构建链熟悉 + pin 修改 + 构建 + 验证）; 构建时长取决于 locks 命中率, 最坏 flashinfer/vllm 源码编译数小时。
- 风险: 中-高——GB10 镜像有破碎前科; 自建版本与发行 tag 分叉, 后续维护/复现难。仅路径 A 超 1 周无新 tag 且 DFlash2 仍处关键路径时启用。

### 路径 C: 不动（现状基线）
- L2 测量已给框架: attempt 级主导项 = 串行 step 数 × 带宽墙, DFlash2 只动 decode, 收益上限受接受率约束（D2 定论: agent 段 1.09-1.29 洼地）; L1/L2 做完后若瓶颈在 step 数/prefill, DFlash2 边际收益被稀释。三杠杆是组合拳不是互替。

## 3. 与 L1 时序关系（不变）
L3 探针必须等 L1 medium 矩阵基线之后（08-23/24 错峰）; 本备忘只放行"评估", 未放行任何拉取/重建/探针动作。

## 4. 盯梢与复核命令（入 drafter ledger）
- tag 列表: curl -s https://dockerproxy.net/v2/timothystewart6/vllm-gb10/tags/list
- PR/权重: 本备忘 §1 已坐实, 无需轮询; 新 tag 出现后先 docker inspect 比版本串再决定 pull。
- 权重下载缓至探针批窗（3.85GB, hf-mirror ~分钟级）, 遵守"切换窗 = 纯窗口"纪律。

## 5. 报用户拍板项
1. 路径选择: A（推荐: 被动等 tag, 零当前成本）/ B（自建）/ C（缓议）。
2. 新 tag 出现后的探针是否自动排入 L1 基线之后（默认是, 仍按合并卡流程报批）。
