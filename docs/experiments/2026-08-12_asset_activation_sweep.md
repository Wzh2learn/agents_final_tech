# 休眠资产激活摸排 (Q1)

> 日期: 2026-08-12 | 方法: 每资产先核实状态再 ≤15min 探针, 全部只读/瞬态, 未改生产配置
> 底座: docs/21 + 2026-08-07 全量盘点 + docs/28 | 红线: 未加载 72B / 未重启 :5050 / 未改生产配置

## 资产盘点表

| # | 资产 | 状态 | 探针证据 | 建议 |
|---|---|---|---|---|
| 1 | :8005 Qwen3-14B | 在跑、基本空转（仅旧审计偶用） | thinking 开: 28s/200tok 且全耗在 reasoning_content, content 为空; `/no_think` 关思考: **4.4s 输出合法 judge JSON** {"score":5,"reason":...} (130 tokens) | **发送后激活**: eval judge/一致性检查分流到 :8005 (改 m2_eval_judge.py 端点 env + /no_think, ~0.5d), :8004 腾给 OCR 兜底/LLM 映射/答案生成 |
| 2 | tabular_mcp_server.tabular_classify | 可用（opencode stdio 注册, tabpfn） | smoke --run-synthetic **PASS** 1.4s 输出维度 [3,2]; 08-05 e2e runner PASS | **维持现状**: classify 是"表格数据上做 ML 分类"(TabPFN), 不是文档图片表格区域检测, 对 TraFax/nanhua 残余 (OCR 文本无表格线/备注表) **无表格边界检测价值**; 留作 agent 演示资产 |
| 3 | vision_mcp_server.vision_ocr_extract | 可用（后端 qwen3-vl→:8004, 非 PaddleOCR） | MCP client 真调 **PASS**: TraFax 首页 OCR 出真实文本 (232.9s @3530×4990 全幅, 18.4GiB); 两个坑实测: max_new_tokens 硬上限 512; image_path 必须在 allowed roots (默认 项目 assets/data, env JINRONG_VISION_ALLOWED_ROOTS 可覆盖) | **发送后激活**: opencode.json mcp env 加 JINRONG_VISION_ALLOWED_ROOTS 指向样本目录 (~10min 配置+冒烟), agent 即可对任意样本图 OCR; 全幅慢, 只作 agent 辅助不入解析热路径 |
| 4 | qwen_harness_tools (web_search/code_interpreter/web_extractor) | 历史被调 1 次 (07-31 Loop C R7 审计), 近期无证据 | 今日演示 web_search "Docling latest release table structure": 高质量结构化产出 — Docling v2.119.0 (2026-08-10) / TableFormer v2 专攻无边框金融表格 / Granite-Docling-258M VLM TEDS≈0.97 — 直接成为发后队列 #4 Docling 探针的前置情报 | **保持活跃**: 定为对标调研/情报收集标准工具 (docs/28 各 gap 调研都用它), 不再闲置 |
| 5 | OpenCode tabular-researcher agent | 跑过 1 次 (07-28 subagent session "Tabular classification job"), 08-05 e2e 只测了 runner | opencode.log:3968-3973 session 证据 (model=qwen3-14b) | **维持休眠**: tabpfn 演示价值已由 runner 覆盖, researcher 的研究职能无当前场景; 有表格 ML 需求再启 |
| 6 | zhikuncode docker | healthy Up 8d, :8090 (容器 8080) "AI Code Assistant" Vite Web UI | docker port + HTTP 200 + title | **保留不动**: 用户自有编码助手, 非本项目资产, 不入项目治理台账 |
| 7 | VLM 降采样代码 (_vlm_downsample) | 保留资产, flag 在位 | parser:618-648 `M1_VLM_MAX_PX` 默认 1600; docs/21 §401 / docs/18 Phase4 / THREADS 4.2 均已记录实验结论 (延迟达标但 TraFax 劣化 → :8007 VERIFIED-CLOSED) | **确认保留**: 仅修 THREADS:21 陈旧表述"优化候选" (4.2 已做完), 一行卫生 |
| 8 | loop_d_monitor.sh (附带发现) | 陈旧: 检查 :5000 旧端口、缺 :4096/:8100、无三方 HEAD、无 dispatch 时长 | 代码阅读 | **并入 Q4 L1**: 升级为 status.sh (不双轨), 把辅助线 ad hoc 核验 snippet 固化 |

## Top 3 激活建议（按 ROI）

1. **:8005 judge 分流** (~0.5d, 发送后): m2_eval_judge.py / judge_consistency.py 加 JUDGE_ENDPOINT env 指向 :8005 + /no_think 前缀。收益: eval judge 从 :8004 35B 每问 ~15-30s → 14B ~4-5s (实测), :8004 并发压力减半。风险: 14B 判分质量需一轮与 35B 对照 (judge 一致性脚本现成)。
2. **vision MCP 接入样本目录** (~10min 配置 + 冒烟, 发送后): opencode.json jinrong-vision 增 env JINRONG_VISION_ALLOWED_ROOTS=~/wzh/m1_samples; m1-gap-triage skill 追加"可让 agent 调 vision_ocr_extract 看图"。收益: agent 审计/triage 获得独立 OCR 通道 (与 parser 热路径的 vision-8004 同后端, 口径一致)。
3. **status.sh 一页健康** (0.5d, 并入 Q4 L1): 三方 HEAD 对齐 / Loop B 上次 PASS / 端口快照 (:5050/:4096/:8004/:8005/:8100) / 距上次 dispatch 时长 — 替代陈旧 loop_d_monitor.sh, 沉淀辅助线核验 snippet。

## 不做（附理由）
- tabular classify 接残余 case: 工具能力与问题域不匹配 (见 #2)。
- tabular-researcher 复活: 无场景, 避免刷存在感。
- zhikuncode: 非项目资产。
