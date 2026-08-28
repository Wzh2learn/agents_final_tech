# 仓外资产普查登记（两轮扫描合并终版）

> 状态: 活跃（台账件; 仓外大件下载即登记规则自本件生效） | 更新: 2026-08-29 | 取代/被取代: 无（承接 2026-08-29_research_assets_inventory.md 的 research 五件, 本件为全域终版）
> 纪律: 清理候选等批不擅动; 用户暂缓区未来扫描跳过; 不开新服务不跑 OpenAI4S（论文优先, 工具克制）

## 一、GB10 ~/wzh/research 五件（详见 research_assets_inventory.md）

OpenAI4S（目录 ~/wzh/research/openai4s_probe, PKU-YuanGroup @ ec37053, 克隆未运行, 长期候选）/ m0_lit（5 篇记忆·自进化全文, 已接科研线）/ academic_skills_audit（本仓学术技能源仓库, 08-29 漂移检查零漂移）/ tabfm 仓库（google-research @ d8678b6 v1.0.1）/ openai4s_data_probe（空工作区）

## 二、GB10 权重（实测 08-29, 原 8 件未登记补录）

| 权重 | 位置 | 大小 | 状态/佐证 |
|---|---|---|---|
| Qwen3.8-27B-FP8 | models/hf/ | 29G | **:8006 生产在役**（vllm-probe 容器） |
| qwen3-vl-8b-instruct | models/hf/ | 17G | vision 链路在役（:8004 视觉） |
| qwen3-embedding-0.6b | models/hf/ | 1.2G | 本地 embedding 在役（.env LOCAL_EMBEDDING_MODEL_PATH） |
| qwen3-reranker-0.6b | models/hf/ | 1.2G | reranker 在役 |
| Qwen3.8-27B-DSpark-vLLM | models/hf/ | 2.6G | DSpark 实验遗留（生产已退出, 权重留盘先例） |
| tabfm-1.0.0-pytorch | models/hf/ | 13G | 表格基础模型, 挂探索线待定性 |
| tabpfn_3 | models/hf/ | **32K** | 疑似占位无权重（仅配置文件, 如实记） |
| paddleocr-vl-1.6 | models/hf/ | 1.8G | **挂 C4 线候选**（视觉臂备选读图器） |
| bge-m3 | models/hf/ | 2.2G | 疑遗留（embedding 已切 qwen3-embedding-0.6b）, 确认后清理候选 |
| bge-reranker-v2-m3 | models/hf/ | 2.2G | 同上（与 bge-m3 为两件不同模型, 非同款重复） |
| minicpm5-1b / minicpm-v-4.6 | models/hf/ | 2.1G / 2.5G | 小模型矩阵历史实验件, 闲置 |
| qwen3-4b / qwen3-8b / qwen3-14b / qwen3-vl-8b | models/gguf/ | 合计 21G | 4b:8002 / 8b:8003 曾服役（~/wzh/logs/qwen3-{4b-8002,8b-8003}.log 佐证）, 现闲置; 14b 为 14B>8B 异常复测件 |

## 三、数据集

- **tat-dqa**: /home/testuser/wzh/datasets/tat-dqa, **1.5G**（注: 在 ~/wzh/datasets 下, 与用户暂缓区的顶层 /home/testuser/datasets 不同路径）; 全合成实验语料底座（TAT-QA 公开集）, **论文 data availability 声明必引**（注入算子/95 表/切分全部基于此）

## 四、routes_s 口径更正

~/wzh/routes_s = **dgx-spark-qwen38 配方仓（非权重）**。backlog A4 "权重下载完成"指向 models/hf:
实测 models/hf 有 Qwen3.8-27B-FP8（29G）与 DSpark 件, **未见 NVFP4 专用权重** → A4 的"权重已下"
需复核（疑指 FP8 件; SGLang+NVFP4 路线所需权重未在盘）。

## 五、本机残留（D:\AIRcommend\JinRongAgents, 实测 08-29）

| 残留 | 数量/位置 | 性质 | 处置建议（等批） |
|---|---|---|---|
| _tmp 目录 + _tmp_* 散件 | 14 件（08-18~22 分析件） | 临时分析脚本/产物 | 清理候选 |
| git bundles | 3 件（joint-m1-m2-plan / tat-dqa-current / tat-dqa-final, 7 月传输件） | 历史传输 | 清理候选 |
| side_figures_0827 / side_round3_0827 | 2 staging | 关键产出已入库（figures_k2 / Round 3 件） | 清理候选 |
| side_audit_inbound_0822 | C:\Users\王中华\（不在仓目录） | 08-22 归位后应删未删 | 清理候选 |
| side_backups / side_handoff_20260827.md | 备份与手递件 | 手递件已入库（3569ffe） | 保留观察 |
| m1.*.bak | 前端旧版备份 | D1 改版回滚兜底 | **保留至 D1 验收** |
| advisor 系列 | 专利/导师件 | 冻结 | **不碰** |

## 六、仓库内足迹注记（不处置）

- GB10 仓根: `.omc/` `.qoder/` `.agent-of-empires/`（.gitignore L59-62 已盖, 保留）; `dify/` 目录挂"甲方规则挖掘"项（backlog C5）
- GB10 config 备份链（含 20260827-loopa-routing 件）= 治理实践入账（窗口前置存档先例）
- docker: vllm-gb10 镜像 **三个 tag 同一 image ID（734134467dc5, 22.1G）**——删冗余 tag 回收≈0（层共享）, 非 44G; :8006 容器（vllm-probe）实际引用 dockerproxy.net tag → 留该 tag, 另两 tag（docker.1ms.run / hub.rat.dev）可删但零空间收益, 等批

## 七、用户暂缓区（本卡不登记不处置, 未来扫描跳过, 白名单防误报）

`/home/testuser/datasets`（含 DAIR-V2X-C 及 staging 副本）/ `mym`（光通信科研资产）/ `.openclaw`（旺财）/ 6g_v2x 关联

## 八、红线备忘（不处置只记）

本机 Downloads 有两份真实甲方件——**研究/论文/语料路径保持零接触**（甲方数据零进入红线, 贯穿全部工件）。

## 九、治理补丁（08-29 生效）

1. 漂移扫描范围扩 ~/wzh 资产目录（权重/数据集/克隆仓未登记 = 漂移候选）
2. 台账规则: **仓外大件（权重/数据集/克隆仓）下载即登记**（入本件 + THREADS 一行）
3. 暂缓区白名单（§七）入扫描配置, 防重复上报
