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
| 2026-08-19 | Route V (vLLM dsaprk) | :8007 | 7 | probabilistic | 固定题库 off/xhigh + 并发3 + golden 6 条 | **3.3143 accepted/draft** (off 短答负载); 逐位 0.943/0.943/0.571/0.371/0.286/0.143/0.057 | off 16题 p50 4.29s / xhigh p50 19.5s (adv_multiturn xhigh 90.9s) | Track 1 (tmux loop-a-dspark1) — 报告 docs/experiments/2026-08-19_dspark_route_v_probe.md; :8006 等价性对照已补跑: 语义等价 PASS(逐字差异归因 FP8 跨引擎不确定性, golden 单流探针快 1.8-5.6x), 见报告对照节; :8006 16 题基线矩阵补跑中 |

## 监控规则
- 复核命令: curl -s https://hf-mirror.com/api/models/Doopeworld/Qwen3.8-27B-DSpark-vLLM 取 "sha" 字段 (上游同步看 RadixArk/Qwen3.8-27B-DSpark)。
- sha 变化 → 本表加行 (新 sha/日期/来源) + 重新下载锁 revision + 重跑等价性三验。
- 每次探针/切换窗口前复核一次; 平时无需轮询。

## Revision 关系补注 (2026-08-19, Route S 解锁后)
- 本项目锁定: Doopeworld/Qwen3.8-27B-DSpark-vLLM @ ebaa091 (= RadixArk 上游权重 + config 一行 vLLM 适配)。
- RadixArk/Qwen3.8-27B-DSpark 上游 head: 85ef153 (08-16, 本项目下载时 latest)。
- Route S recipe (github.com/hasso5703/dgx-spark-qwen38, install.sh 2026-08-15 pin) 用 DRAFT_REV=923ed3a — 早于上游 head 85ef153; 两臂 drafter revision 不同, 对照报告须注明 (若 Route S 接受率与本臂不可直接比, 此为干扰因子之一)。
- 监控: 上游若出 v2 drafter (Koopah 先例 +6.8%), 三处 revision 一并更新评估。
## 术语口径: DSpark vs DFlash (2026-08-21, 专利修订版同步)

- **DSpark** = DeepSeek 半自回归投机解码 (本项目生产 :8006 采用, drafter 验证目标模型输出, 无损)。
- **DFlash / DFlash2** = 同技术族内**相互独立**的方法, 不得与 DSpark 混用或互相指代。
- 证据两条: ① 生产镜像 vLLM 源码 speculative.py L62-63 将 dspark/dflash 并列注册为不同 method; ② 上游 issue vllm-project/vllm#52816 对两者明确区分。
- 口径落点: 2026-08-21_patent_full_revised.md 全文统一 DSpark (§3.2.7 起草注记 + 附录 B 术语注记), 该专利件不出现 DFlash 指代本项目方法的情形。
