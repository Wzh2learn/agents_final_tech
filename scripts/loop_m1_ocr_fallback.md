# 任务：M1 OCR/VLM 兜底纯图样本（用完即停，不常驻）

## 背景
GB10，项目 `~/wzh/projects/agents_final_tech`。上一轮 6 样本中 2 个是纯图
（20260506_233222LU.pdf 无文本层；xinhua.docx 内嵌 7 图零文本），纯规则产出 0。本轮用
GB10 已有视觉模型做 OCR/表格提取兜底，取文本后**进同一套近义词映射**，验证 OCR 路径能否
闭环。样本 `~/wzh/m1_samples/`（项目外，不入库，报告脱敏）。

## 约束
- 样本不入库、报告脱敏；不下载任何模型（只用 ~/wzh/models 与 wzh_vision 已有的）。
- 视觉模型**用完即停、不常驻、一次只起一个**；每页/每图 30s 超时；loop 结束 pkill 自己起的视觉进程。
- 不改 m1_service.py；不 push；不碰 TAT-DQA / test split。
- :8004（llama 文本）当前空闲，视觉模型可并存；若统一内存 OOM→降精度或 BLOCKED，不重试。

## Phase 0 验证视觉可用（不可用即 BLOCKED 记录，不无限重试）
检查 `~/miniconda3/envs/wzh_vision` 与 vision_ocr_extract MCP / 本地推理脚本
（PaddleOCR-VL / MiniCPM-V / Qwen3-VL，HANDOFF 记录已冒烟）。用 PyMuPDF 把纯图 PDF 页渲染为
/tmp PNG；python-docx 提取 docx 内嵌图片 blob 存 /tmp PNG。记录可用模型与冷启动耗时。

## Phase 1 OCR/表格提取
对每份纯图样本的每页/每图：调视觉模型取文本或表格 JSON（优先表格结构，退化为文本）。

## Phase 2 进近义词映射
OCR 文本/表格复用 m1_statement_parser 的 map_headers/normalize（文本表格用分隔符/对齐切行，
或让 VLM 直接出标准字段 JSON 再校验）。

## Phase 3 记录
每页/图：OCR 文本长度、是否抽出表格、映射命中率、置信/可疑标记；与同源 TXT（若有）对比字符重叠。脱敏。

## Phase 4 报告
`docs/experiments/$(date +%F)_m1_ocr_fallback.md`：视觉模型与冷启动、每样本 OCR→映射命中率、
失败原因分类、对"未知表头/无文本层冷启动"北极星指标的贡献、是否值得纳入主线。脱敏。

## Phase 5 收尾
确保无残留视觉进程（pkill 自己起的）；commit 脚本+报告，不 push。

## 停止条件
视觉模型加载失败/不可用→BLOCKED 记录并停；单页超时→记 TIMEOUT 继续下一页；连续 3 页失败→停。
不要常驻模型、不要 push、不要碰 TAT-DQA。
