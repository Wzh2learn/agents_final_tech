审查完成。以下为报告正文：

---

# Loop C 增量安全审查报告（differential-review 方法论）

## 1. Diff 范围统计

- **范围**：`d7049b5..HEAD`（d7049b5 存在，无需回退到日期规则）
- **提交数**：15 commits（`701eae2` → `a91ff74`）
- **总量**：114 files，**+16,532 / −140**
- **代码相关**（src/ scripts/ tests/ config/）：10 files，**+658 / −11**；其余 ~15.9k 行为 `skills/` 武库文档、docs 归档重排（全部 R100 纯重命名）与实验记录

| 文件 | 变更 | 风险级别 | Blast Radius |
|---|---|---|---|
| `scripts/vlm_server_8007.py` (新) | +163 | **HIGH 关注** | 独立服务；未纳入 deploy/ 单元 |
| `scripts/m1_statement_parser.py` | +264 | **HIGH 关注** | M1 全管线：上传 API（`routers/m1.py` 引用 `PARSERS`）+ 批处理脚本 |
| `src/vision_mcp_server/service.py` | +73/−3 | MEDIUM | 仅 qwen3-vl OCR 调用路径 |
| `src/biz/m2_service.py` | +36/−2 | MEDIUM | m2 路由 + RAG QA（timeline/持仓对比） |
| `config/m1_table_schema.json` | +16/−6 | MEDIUM 重要性 | 全部 M1 表匹配（**纯增量加 8 个 synonyms，无删除**） |
| `src/web/routers/pages.py` | +6/−3 | LOW | 仅 `/api/health/full` |
| `tests/test_health_embeddings_count.py` (新) | +43 | LOW | T2 回归测试 |
| `scripts/graph/sync_skills.sh` (新) | +38 | LOW | 手动执行的分发脚本 |

## 2. 安全回归核查（焦点 1）

| 控制点 | 状态 |
|---|---|
| CORS（`src/main.py` allow_origins） | **未触碰** ✓ |
| 认证中间件（`src/web/middleware.py`，M1_API_TOKEN） | **未触碰** ✓ |
| Admin token（`src/web/routers/m1.py:199`，M1_ADMIN_TOKEN） | **未触碰** ✓ |
| 路径穿越 | vision MCP `resolve_image_path` 未改；上传仍走 `NamedTemporaryFile` + suffix 白名单（`.html` 为新增白名单项，机制未变）✓ |
| 错误信息泄露 | 主应用全局错误处理器（f76675c，"no stack traces"）**未触碰** ✓ |

## 3. Findings（按严重度排序）

### 🟠 MEDIUM

**F1 — 新增 `vlm_server_8007.py`：无认证 0.0.0.0 服务 + SSRF/本地文件读取向量**（701eae2）
- `uvicorn.run(app, host="0.0.0.0", port=8007)`，无任何 token/认证；与项目自身基线不一致（主服务 0.0.0.0:5050 有 M1_API_TOKEN 中间件保护）。
- `_decode_image` 对请求体中任意 `image_url` 直接 `urllib.request.urlopen(image_url, timeout=30)`：攻击者可发 `image_url: "file:///etc/passwd"`（urllib 支持 file:// 协议 → 本地文件读取）或指向内网服务（169.254.169.254、127.0.0.1:15432 等）→ SSRF。
- `max_tokens` 无上限校验直接作为 `max_new_tokens` → GPU 资源耗尽型 DoS。
- 500 响应返回原始 `str(e)`，偏离 f76675c 确立的"不泄露异常细节"标准。
- 缓解因素：内部推理辅助服务、开发机环境、未纳入 deploy/、不接触客户数据。**建议：绑定 127.0.0.1、白名单 image scheme、设 max_tokens 上限。**

**F2 — `_is_junk_table` 启发式可能误杀合法 2 列表格**（d9a816c→b927efe，`m1_statement_parser.py` parse_pdf）
- 判据 `non_empty <= 2 → junk`：find_tables 提取出的合法 2 列 KV 表格（对账单中常见的"标签|值"表）会被判为 junk，若坐标重建同时产出结果则**整体替换** `doc.tables`。
- 表头探测用模糊包含匹配（`t in kh or kh in t`，len≥2），存在误判表头行的可能。
- 属正确性回归风险而非安全漏洞，但 blast radius = 所有 PDF 解析路径。

**F3 — 新增主体代码测试覆盖缺口**（方法论规定：无测试 = 风险评级上调）
- 坐标表格重建（~130 LOC）、`parse_html`、`_vlm_api_call`（vision service）、`vlm_server_8007.py` 全量、m2 的 `matched_schema` 拼接行为（现有 `test_m2_compare.py` 的 mock metadata 不含该键）——均**零测试**。本范围仅 T2（embedding count）补了测试。

### 🟡 LOW

**F4 — 重复模式：两份 VLM 客户端实现**（copy-paste 残留）
- `vision_mcp_server/service.py::_vlm_api_call` 与 `m1_statement_parser.py::_vlm_ocr_one/_try_vlm_table` 重复实现 base64 payload/endpoint 逻辑，且**已开始分叉**：timeout 120s vs 60s、逐次健康检查 vs 全局缓存。

**F5 — `_vlm_available` 全局缓存永不失效**：:8007 若在首次探测失败后启动，解析器将持续走 mmproj 回退直到进程重启。

**F6 — 单测网络副作用**：`run_vision_ocr(model="qwen3-vl")` 在 runner 注入前先向 127.0.0.1:8007 发真实 HTTP 探测，单元测试触网。

**F7 — 冻结治理盲区（非违规）**：hash manifest 钉住的是 `~/wzh/m1_samples/m1_table_schema.json`，而运行时实际生效的是 `config/` override（`resolve_schema_path` 优先 LOCAL_SCHEMA）；config/ 的 synonyms 演进不在 hash 校验覆盖内。本次改动均为增量添加，未构成违规。

### ⚪ INFO

- **F8**：新增健康测试的两条用例在 PG/服务不可达时均 `pytest.skip` → CI 中可能静默不执行，T2 回归守护偏弱。
- **F9**：`/api/health/full` 免认证 + `str(e)[:100]` 为**预存在**设计（middleware.py:18-19），本 diff 未改动；现返回真实 embedding 数属预期 T2 修复。
- docs 全部为 R100 重命名或纯文档新增；`sync_skills.sh` 的 `rm -rf` 仅作用于固定枚举目标目录，可接受；`loop_c_audit_prompt.md` 仅追加 skill 注册表。

## 4. 冻结节点完整性核查（焦点 4）

| 冻结节点 | 结论 |
|---|---|
| `tests/test_m1_service.py` | diff 未触碰 ✓（`git diff --stat` 为空） |
| `scripts/graph/frozen_hashes.txt` | diff 未触碰 ✓（md5 `faa7565a…` 对应文件未变） |
| schema 冻结 hash（m1_samples 副本） | diff 未触碰 ✓（受限沙箱无法重算仓外文件 md5，以 git diff 为准） |
| `config/m1_table_schema.json` | 被修改（+8 synonyms，纯增量）——不在 manifest 钉扎范围内，见 F7 |

## 5. 覆盖限制声明

- 仓外文件（`~/wzh/m1_samples/`）无法在沙箱内重算 hash，冻结校验依赖 git diff 证据。
- 未实际运行测试套件（依赖 PG/GPU 服务）；覆盖结论基于静态分析。
- skills/ 与 docs/ 增量按 LOW 处理（非运行时代码），未逐行审读。

---

安全回归: 无（既有 CORS/认证/路径穿越/错误泄露控制均未被触碰；F1 为新增服务引入的新风险，非既有控制回归）
冻结节点完整性: 完整

END-OF-REPORT
