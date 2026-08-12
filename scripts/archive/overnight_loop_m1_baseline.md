# 过夜任务：M1 规则抽取基线验证

## 背景

你在 GB10 开发机上，项目目录 `~/wzh/projects/agents_final_tech`。
M1 展示工作台代码已提交（src/biz/m1_service.py, src/web/routers/m1.py, tests/test_m1_service.py）。
TAT-DQA 数据在 ~/wzh/datasets/tat-dqa/，官方解析 JSON 在 raw/ 目录。

M1 的目标：将文档中的业务规则抽取为可校验的结构化结果。
当前 M1 service 是确定性文本规则基线（正则 + Pydantic），不依赖 OCR/VLM。

## 约束（硬性）

- 不得触碰 test_gold / test split 数据
- 不得下载新模型或新数据集
- 不得修改 CUDA、驱动、系统网络
- 不得修改 src/biz/m1_service.py 的核心逻辑（可以修 bug，不改架构）
- 如果某个步骤失败，记录并继续下一步
- 所有结果写入 docs/experiments/2026-07-28_m1_baseline.md
- 不要 push 到远程仓库

## 执行步骤

### Phase 0: 环境验证

```bash
cd ~/wzh/projects/agents_final_tech
source venv/bin/activate
python3 -m pytest tests/test_m1_service.py -v
```

确认 18 项测试全部通过。

### Phase 1: M1 API 集成测试

启动 FastAPI 应用（如果 :5000 已被占用则用 :5050）：

```bash
# 检查端口
curl -s http://localhost:5000/api/status | head -3

# 如果 5000 被占用，用 5050
python3 src/main.py -m http -p 5050 &
sleep 3
```

测试 M1 端点：
```bash
# 获取样本文档
curl -s http://localhost:5050/api/m1/sample | python3 -m json.tool | head -10

# 运行抽取
curl -s -X POST http://localhost:5050/api/m1/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "规则一：测试规则\n触发条件：当某个业务事件发生且满足预设条件时\n执行动作：系统自动执行相应操作并记录日志", "document_name": "test.txt"}' \
  | python3 -m json.tool | head -20
```

记录 API 是否正常工作。

### Phase 2: TAT-DQA 文档 M1 抽取试验

从 validation split 的官方解析 JSON 中取 5 份文档的文本内容，
用 M1 service 的 extract 方法跑规则抽取，记录：
- 每份文档抽取出多少条规则候选
- Pydantic 校验通过率
- 需要人工复核的比例
- 平均置信度

```python
import json, sys
sys.path.insert(0, "src")
from biz.m1_service import M1Service, M1ExtractionRequest

svc = M1Service()

# 读取 validation 文档
with open("/home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_dev.json") as f:
    docs = json.load(f)

results = []
for doc in docs[:5]:
    doc_id = doc.get("id", "unknown")
    # 拼接所有段落文本
    paragraphs = []
    for page in doc.get("pages", []):
        for block in page.get("blocks", []):
            if block.get("type") == "text" and block.get("text"):
                paragraphs.append(block["text"])
    text = "\n\n".join(paragraphs)
    if len(text) < 20:
        continue
    try:
        req = M1ExtractionRequest(text=text[:15000], document_name=f"tat-dqa-{doc_id}")
        res = svc.extract(req)
        results.append({
            "doc_id": doc_id,
            "chars": len(text),
            "rules": len(res.rules),
            "schema_pass": res.validation.passed,
            "schema_fail": res.validation.failed,
            "review_rate": res.metrics.get("human_review_rate", 0),
            "avg_confidence": sum(r.confidence for r in res.rules) / len(res.rules) if res.rules else 0,
        })
    except Exception as e:
        results.append({"doc_id": doc_id, "error": str(e)})

print(json.dumps(results, indent=2, ensure_ascii=False))
```

### Phase 3: PDF 文本提取对比（如果 pdfplumber 可用）

检查是否有 pdfplumber 或 PyMuPDF：
```bash
python3 -c "import pdfplumber; print('pdfplumber OK')" 2>/dev/null || \
python3 -c "import fitz; print('PyMuPDF OK')" 2>/dev/null || \
echo "NO_PDF_LIB"
```

如果有 PDF 库且 raw/ 下有解压的 PDF 文件，取 2 份做文本提取，
与官方解析 JSON 对比文本相似度（简单的字符重叠率即可）。

如果没有 PDF 库或没有解压的 PDF，记录 BLOCKED 并跳过。

### Phase 4: 结果汇总

写入 `docs/experiments/2026-07-28_m1_baseline.md`：

```markdown
# M1 规则抽取基线验证

日期: 2026-07-28
方法: 确定性文本规则基线（正则 + Pydantic）
数据: TAT-DQA validation split 前 5 份文档

## 测试结果

| 文档 ID | 字符数 | 规则数 | 校验通过 | 校验失败 | 复核率 | 平均置信度 |
|---------|--------|--------|----------|----------|--------|-----------|
| ... | ... | ... | ... | ... | ... | ... |

## API 集成测试

（记录端点测试结果）

## PDF 文本提取

（记录结果或 BLOCKED）

## 发现与限制

（由执行者填写）
```

### Phase 5: 提交

```bash
git add docs/experiments/2026-07-28_m1_baseline.md
git commit -m "exp: M1 rule extraction baseline on TAT-DQA validation

Deterministic text-rule baseline (regex + Pydantic) on 5 validation docs.
API integration test included. No model inference, no OCR."
```

## 停止条件

- 所有 Phase 完成 -> 正常结束
- Phase 0 测试失败 -> 记录错误，尝试修复后重跑
- Phase 2 全部文档失败 -> 记录原因，停止
- Phase 3 无 PDF 库 -> 标注 BLOCKED，跳过

## 不要做的事

- 不要启动模型推理服务
- 不要修改 M1 service 架构
- 不要 push
- 不要触碰 test split
