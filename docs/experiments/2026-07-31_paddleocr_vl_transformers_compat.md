# PaddleOCR-VL 加载失败诊断 + 视觉 OCR 并行化 (Task #7)

- 日期: 2026-07-31
- 角色: Loop A (执行层)
- 状态: 已修复(回退路径), PaddleOCR-VL 仍被环境阻塞

## 背景

`_try_paddleocr` 一直失败, 所有影像件实际只走 `vision-8004` 引擎, 且 DOCX
(6+ 图) 串行 OCR 耗时 ~200s。任务要求定位 PaddleOCR-VL 加载错误并按情况修复或
优雅降级 + 并行化视觉引擎。

## 根因 (transformers 版本不兼容)

环境 `wzh_vision` 的 transformers 为 **5.7.0**, 而 PaddleOCR-VL 随包远程代码
(`modeling_paddleocr_vl.py` / `configuration_paddleocr_vl.py`) 针对 **4.55.0**
编写 (`config.json: transformers_version=4.55.0`)。逐层复现出三处独立的内部 API
断裂, 证明这是整体版本不兼容而非单点 bug:

1. `config.json` 的 `auto_map` 只注册了 `AutoModel` / `AutoModelForCausalLM`,
   **没有** `AutoModelForImageTextToText`。原代码用 `AutoModelForImageTextToText`
   → 回落到 transformers 5.7 内置 `paddleocr_vl` 模型, 它期望 composite
   `config.text_config`, 而随包 config 是扁平结构 →
   `AttributeError: 'PaddleOCRVLConfig' object has no attribute 'text_config'`。
2. 改用 `AutoModel` (加载随包代码) 后: `ROPE_INIT_FUNCTIONS["default"]` 在 5.x
   被移除 → `KeyError: 'default'`。
3. 打补丁恢复 `default` 后: 5.x 的权重初始化要求 `RotaryEmbedding.
   compute_default_rope_parameters` mixin 方法, 4.55 版自定义类没有 →
   `AttributeError`。

继续 monkey-patch 只会暴露更深层的 5.x 内部 API 变更 (attention/cache/masking),
且可能引入静默数值错误。随包代码还硬依赖 `einops` (本环境原缺失, 已安装 0.8.2,
纯 Python 零依赖, 不影响其他模型)。

## 决策

按任务授权路径 (item 5 + 6), **不降级 transformers** (会影响 wzh_vision 其他模型):

- PaddleOCR-VL 需要 transformers ~4.55.x; 当前 5.7.0 不兼容, 记录在此。
- `scripts/m1_ocr_fallback.py`: 加载模型前做版本门控, transformers>=5.0 时打印
  稳定标记 `PADDLEOCR_INCOMPATIBLE` 并以 exit 4 快速失败 (~0.4s, 原来要等满
  120s 子进程超时)。同时把 `AutoModelForImageTextToText` 换成 `AutoModel`
  (与 auto_map 一致, 若将来降级到 4.55 可正确加载随包代码)。
- `scripts/m1_statement_parser.py::_try_paddleocr`: 捕获该标记后将
  `_PADDLEOCR_UNAVAILABLE` 锁存为 True, 后续调用直接跳过子进程。
- `scripts/m1_statement_parser.py::_try_vision_ocr`: 用 `ThreadPoolExecutor`
  并行 (默认 `M1_OCR_VISION_WORKERS=4`, 匹配 :8004 llama-server 的
  `total_slots=4`); `pool.map` 保持图片顺序即阅读顺序。单图超时由硬编码 60s
  改为可配置 `M1_OCR_VISION_TIMEOUT=120` (扫描页单图可达 ~60-70s, 避免慢页被
  静默丢弃)。

## 验证 (2026-07-31)

- `pytest tests/test_m1_service.py`: 18/18 PASS (冻结合约未触碰, 哈希一致)。
- 门控快失败: 子进程 0.4s 返回 exit 4 + 标记; 解析端第二次调用 0.0s 跳过。
- 并行保序: 6 图 × 0.2s mock, 4 worker → 0.4s, 输出顺序 img0..img5 正确。
- LU PDF (`sample_20260506_233222LU.pdf`): `ocr_used=true`,
  `ocr_engine=vision-8004`, 30.9s, 3 表, reconcile 4/4 PASS。
- 新华 DOCX (`sample_xinhua.docx`, 7 图): `ocr_used=true`,
  `ocr_engine=vision-8004`, **200s → 74s (~2.7x)**, 6 表, reconcile 4/4 PASS。

## 后续 (需 Loop D 授权)

- 若要真正启用 PaddleOCR-VL (通常比视觉引擎快一个量级): 在一个**独立** venv
  装 transformers ~4.55.x + einops, 把 `_OCR_PADDLE_PYTHON` 指向它, 避免影响
  wzh_vision 现有模型。当前未执行 (环境改动需授权)。
- 进一步提速受限于 :8004 的 4 个 slot 与 GPU 吞吐; 提高 `--parallel-slots` 或
  换更快视觉模型才能再降。
