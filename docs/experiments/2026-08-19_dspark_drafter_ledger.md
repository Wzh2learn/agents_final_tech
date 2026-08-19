# DSpark Drafter 版本台账 (Qwen3.8-27B)

> 用途: Qwen3.8-27B 目前只有单版 drafter (截至 2026-08-19)。本台账锁版本、盯更新、记实测接受率。
> 治理: 每次 DSpark 探针/切换前复核一次 sha (一条 curl); 有变 → 表内加行 + 重跑等价性验证。
> 先例: Koopah Qwen3.6 drafter v1→v2 接受率 +6.8% —— drafter 会迭代, 必须盯。

## Drafter 仓库登记

| 项 | Doopeworld/Qwen3.8-27B-DSpark-vLLM (vLLM-ready, 本项目采用) | RadixArk/Qwen3.8-27B-DSpark (上游原版) |
|---|---|---|
| 锁定 revision (sha) | ebaa0919226a29408fa2c8f3efc493e98189c7ed | 85ef153be924f17ce4bf62726954eeaa4a73e854 |
| lastModified | 2026-08-16T04:58:04Z | 2026-08-16T02:26:33Z |
| 文件清单 | .gitattributes / README.md / config.json / dflash.py / dspark.py / model.safetensors | 同 6 件 |
| 权重 | model.safetensors 2,718,576,122 B (~2.53GiB, BF16 1.36B 参数) | 与左列字节一致 (Doopeworld 仅改 config.json 一行架构名) |
| 权重 sha256 (LFS oid) | 9d26d5e637551c244d543c67c790bd0947f360e005c569e5851a185ffe692786 | 同 |
| architectures | Qwen3DSparkModel (vLLM registry → qwen3_dspark.Qwen3DSparkForCausalLM) | DSparkDraftModel (transformers custom_code; vLLM 直载会被路由到 DeepSeek-V4 类而失败) |
| 下载通道 | hf-mirror.com (08-19 验证 200) | hf-mirror.com |
| 训练目标 | 按 Qwen3.8-27B-FP8 训练 → 与本项目 :8006 目标模型完全匹配, 无需重量化 | 同 |

## README 关键结论 (Doopeworld 实测, Intel Arc B70 / vLLM 0.26.x XPU)
1. draft_sample_method=probabilistic 必用 —— 比 greedy 快 ~23% (52 vs 42 t/s)。
2. k=7 不可缩减 —— k=4/k=6 实测更差 (per-step overhead 主导, 先测再裁)。
3. enable_adaptive_verification 与 Qwen3.8 GDN 线性注意力层不兼容 (启动 ValueError), checkpoint 里的 confidence head 在 vLLM 下暂不可用 —— 不要开。
4. 接受率强负载相关 (greedy 口径): 通用文本 2.18 / 分步数学推理 4.79; SGLang 报告 gsm8k≈5.2 vs 诗歌≈2.9。
5. 逐位置接受率 (k=7, probabilistic): 0.76, 0.45, 0.31, 0.14, 0.10, 0.02, 0.00。
6. 目标量化无关加载: drafter 读目标模型 bf16 激活 (层 4/16/28/40/52), FP8/GPTQ/AWQ/MXFP4 均可载; 但重量化会扰动接受率。
7. 仅验证过 Intel Arc XPU; GB10 (Blackwell 统一内存) 属首测, 自本项目 2026-08-19 探针始。

## 实测接受率 (探针臂填写)

| 日期 | 臂 | 端点 | k | sample | 负载 | 接受率 | 延迟对照 :8006 | 备注 |
|---|---|---|---|---|---|---|---|---|
| 待填 | Route V (vLLM dsaprk) | :8007 | 7 | probabilistic | 固定题库 off/xhigh + 并发3 | — | — | Track 1 (tmux loop-a-dspark1) |

## 监控规则
- 复核命令: curl -s https://hf-mirror.com/api/models/Doopeworld/Qwen3.8-27B-DSpark-vLLM 取 "sha" 字段 (上游同步看 RadixArk/Qwen3.8-27B-DSpark)。
- sha 变化 → 本表加行 (新 sha/日期/来源) + 重新下载锁 revision + 重跑等价性三验。
- 每次探针/切换窗口前复核一次; 平时无需轮询。
