# E2E 性能基准：M1 解析 + M2 问答（5 样本 × 3 次）

- 日期: 2026-08-01 00:0x CST（Loop A 执行）
- HEAD: `93e001a` (Loop B PASS, frozen nodes 0 violations)
- 基准脚本: `scripts/m1_benchmark.py`（本次新增，只读测量，不改 src/）
- 服务: FastAPI :5050 (workers=2) / 推理 :8004 (Qwen3.6-35B-A3B, 4 slots) /
  辅助 :8005 / PGVector :15432
- 方法: 每样本 `POST /api/m1/parse-file` + `POST /api/m2/ask` 各 3 次取中位数，
  wall-clock（localhost 回环）。跑前用 fuxi(txt) 预热解析模块 + 嵌入/LLM 路径。
- 原始数据: `/tmp/m1_bench.json`（本次运行），运行日志 `logs/graph/benchmark_run.log`

## 1. 结果总表（中位数, ms）

| 样本 | 类型 | OCR | 表数 | parse_ms | qa_ms | total_ms |
|------|------|-----|------|----------|-------|----------|
| sample_20260506_233222LU.pdf | pdf | ✓ | 3 | 26885 | 453 | 27527 |
| sample_boshi_chuantong.pdf | pdf | — | 1 | 618 | 999 | 1604 |
| sample_fuxi_hunhe25_20231101.txt | txt | — | 2 | 12 | 1059 | 1071 |
| sample_jiaxing_minan_20231031.pdf | pdf | — | 6 | 1064 | 978 | 2035 |
| sample_xinhua.docx | docx | ✓ | 5 | 69676 | 847 | 70868 |

> 每样本 3 次取中位数。OCR 引擎均为 vision-8004（PaddleOCR-VL 仍因
> transformers 版本不兼容被锁死跳过）。

### 每样本明细 (min/med/max, ms)

| 样本 | parse min/med/max | qa min/med/max | ocr_engine |
|------|-------------------|----------------|------------|
| sample_20260506_233222LU.pdf | 24512/26885/32611 | 374/453/642 | vision-8004 |
| sample_boshi_chuantong.pdf | 605/618/1185 | 915/999/1286 | — |
| sample_fuxi_hunhe25_20231101.txt | 12/12/12 | 1013/1059/1441 | — |
| sample_jiaxing_minan_20231031.pdf | 1057/1064/2091 | 955/978/1808 | — |
| sample_xinhua.docx | 69486/69676/73989 | 841/847/1192 | vision-8004 |

## 2. 瓶颈定位

### 2.1 宏观：OCR 是唯一显著瓶颈

按 total 占比计算，影像件几乎全部时间花在 M1 解析（=OCR）上：

| 样本 | parse 占 total | 说明 |
|------|----------------|------|
| sample_xinhua.docx | 69676 / 70868 = **98.3%** | 6 张内嵌图，OCR 主导 |
| sample_20260506_233222LU.pdf | 26885 / 27527 = **97.7%** | 1 页扫描 PDF，OCR 主导 |
| sample_jiaxing_minan_20231031.pdf | 1064 / 2035 = 52% | 文本 PDF，parse≈qa |
| sample_boshi_chuantong.pdf | 618 / 1604 = 39% | 文本 PDF，qa 略大 |
| sample_fuxi_hunhe25_20231101.txt | 12 / 1071 = 1% | 纯文本，qa 主导 |

5 样本串行总耗时 ≈ 103.1s，其中两件影像件的 OCR 解析合计 96.6s，
占串行总量的 **93.7%**。文本样本（fuxi/boshi/jiaxing）整条链路均 < 2.1s，
不是优化重点。

### 2.2 M2 QA 分段计时（warm, in-process）

直接 import `biz.m2_service` 拆分（问题=LU 的 OCR 问题，3 次取中位数）：

| 阶段 | 中位 ms | runs | 说明 |
|------|---------|------|------|
| retrieve (嵌入+PGVector) | 138 | 138/105/146 | 本地 Qwen3-Embedding-0.6B + 向量/BM25 混合 |
| generate (:8004 LLM) | 157 | 579/156/157 | 首次 579 为热启动，稳态 ~157 |
| 合计 | 295 | — | retrieve + generate |

结论：**嵌入生成、PGVector 检索、M2 LLM 生成都不是瓶颈**。warm 态整条 QA
仅 ~295ms；HTTP 回环实测 0.45–1.1s（含往返 + 完整带出处答案 + 首调冷启动），
仍属亚秒级。

### 2.3 OCR 内部：分辨率不是杠杆（负结果）

对 LU.pdf 第 0 页与 xinhua.docx 第 0 张图，分别在 200/150/100 DPI（或等比
0.5/0.75/1.0）下单独送 vision-8004 计时（串行单图，避免 slot 争用）：

LU.pdf page0（单图延迟）:

| DPI | PNG bytes | ocr_ms | 输出字符 |
|-----|-----------|--------|----------|
| 200 | 1165352 | 21523 | 1334 |
| 150 | 830634 | 32542 | 1354 |
| 100 | 1528261 | 36887 | 1335 |

xinhua.docx image0（单图延迟）:

| 缩放 | 尺寸 | ocr_ms | 输出字符 |
|------|------|--------|----------|
| 1.00 | 864×1362 | 22496 | 1659 |
| 0.75 | 648×1021 | 33380 | 1509 |
| 0.50 | 432×681 | 17514 | 1650 |

观察:
- 输出字符数在各分辨率下几乎不变（LU ~1334–1354，xinhua ~1509–1659），
  说明识别内容量恒定。
- 延迟**不随分辨率单调变化**：150/100 DPI 反而常比 200 更慢，方差极大
  （17.5s–36.9s）。说明单图 OCR 延迟由 **VLM 解码吞吐（输出 token 数）+
  系统噪声**主导，而非输入图像大小/编码 prefill。
- 因此**降低渲染分辨率不能带来稳定 >20% 提速**，且会危及已冻结的 100%
  解析率。按任务约束：**不改代码**。

### 2.4 并行度：已实现

`_OCR_VISION_WORKERS=4` 匹配 llama-server 4 slots（ThreadPoolExecutor 保序并发），
即 HANDOFF 记录的 200s→74s（2.7×）优化。本次复测与之一致：
- LU.pdf = 1 页 → 单图 OCR ~21.5s + 渲染/表格化 → parse ~27s。
- xinhua.docx = 6 张内嵌图 → 4 workers 分 2 批，并发下每图延迟被 slot 争用
  抬高 → parse ~70s。图数量是 xinhua 慢于 LU 的直接原因。

## 3. 结论与建议

1. **瓶颈唯一且明确：OCR（vision-8004）**，占影像件总耗时 97–98%、5 样本
   串行总量的 93.7%。M2 的嵌入/检索/生成均亚秒，非瓶颈。
2. **并行已到位**（4 workers/4 slots）。在现有模型与硬件下，OCR 并发已接近
   slot 上限，继续加 worker 受限于 4 slots。
3. **分辨率不是杠杆**（实验负结果）：降 DPI 不稳定提速且威胁解析精度，
   不采用。默认 200 DPI 保持不变。
4. 本次为测量 + 文档任务，**未改动任何 src/ 代码**（无一项可稳定 >20%）。

后续可选方向（超出本任务范围，仅记录，不动手）:
- 修复 PaddleOCR-VL（当前 transformers>=5.0 不兼容）——若可用，纯文本 OCR
  通常远快于 VLM 解码路径，是最大潜在收益点。
- 评估更小/更快的 OCR 专用视觉模型替换 vision-8004 的解码瓶颈。
- 影像件在 OCR 前做页/图合并以减少送检图数量（xinhua 6 图是主因）。
- 如需更高并发，调大 llama-server slots（受显存约束，需单独验证）。

## 4. 复现

```bash
./venv/bin/python scripts/m1_benchmark.py --runs 3 --breakdown --json-out /tmp/m1_bench.json
# 快速冒烟（1 次、仅文本样本）:
./venv/bin/python scripts/m1_benchmark.py --runs 1 --samples fuxi --no-warmup
```

> 注：长任务需在 tmux 内运行（本仓库 exec 后台子进程会随 shell 结束被回收）。
