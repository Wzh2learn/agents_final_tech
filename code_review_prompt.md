# 代码审查与修复行动清单（统一执行版）

更新时间：2026-02-10  
适用项目：`JinRongAgents`

## 0. 本轮验收结论（基于当前仓库代码 + 本地回归）

### 0.1 总结
- 结论：**核心修复已落地**，剩余主要是手工 UI 走查与截图复验。
- 当前状态：6个验收项中，`5项已实现（1、2、3、4、5）`，`1项持续有效（6）`。
- 已解除阻断：`src/web/static/knowledge.js` 已重建为单实现版本，不再有重复声明导致的脚本中断。

### 0.2 逐项状态

1) 多知识库
- 状态：**已实现（待手工复验）**。
- 证据：
  - `GET /api/knowledge/collections` 返回集合列表：`src/web/routers/knowledge.py`
  - 前端统一从该接口拉取并渲染侧边栏+概览卡片：`src/web/static/knowledge.js` (`loadCollections`, `enterKnowledgeBase`, `switchCollection`)
  - 页面路由别名统一（`documents -> collection-detail`）：`src/web/static/knowledge.js` (`getPageAlias`, `switchPage`)
  - 模板返回按钮已对齐 `collection-detail`：`src/web/templates/knowledge.html`

2) 每个知识库独立上传/查询
- 状态：**基本达标**。
- 证据：
  - 前端上传携带 `collection_name`：`src/web/static/knowledge.js`
  - 后端 upload 接收并透传：`src/web/routers/knowledge.py`
  - 入库按目标集合：`src/biz/rag_service.py` 的 `ingest_file(..., collection_name=...)`
  - 文档列表按 `collection_name` 过滤：`src/web/routers/knowledge.py` 的 `/documents`

3) 父子分段（Hierarchical）
- 状态：**已实现（待手工复验）**。
- 证据：
  - 后端层级结构输出包含 `is_parent/parent_id/children/display_title`：`src/tools/document_hierarchy.py`
  - 前端详情页已展示父/子块 badge、归属信息、`<details>` 展开全文：`src/web/static/knowledge.js` (`renderHierarchy`, `buildSegmentCard`)

4) 溯源在聊天回答中展示（非知识库页独立入口）
- 状态：**已实现（含二级回退）**。
- 证据：
  - 聊天接口有 fallback：`src/web/routers/chat.py` 在无 trace 且 `needs_rag` 时调用 `smart_retrieve`
  - 若仍为空，继续调用本地兜底片段回退，保证 `sources` 结构可用：`src/web/routers/chat.py`
  - 前端聊天有来源渲染与无来源占位：`src/web/static/script.js`
  - 知识库后端仍保留 `/traceability` API（虽前端已不应强调该入口）

5) 聊天输入区 UI + 下一步建议
- 状态：**已实现（触发点已调整）**。
- 证据：
  - `/api/chat/suggestions` 可用，且有无 API_KEY 的规则兜底：`src/web/routers/chat.py`
  - 建议触发已从“用户输入”改为“AI 最终回答”：`src/web/static/script.js` (`sendMessage` finally)

6) Rerank 排序
- 状态：**基本达标**（非预留，链路可生效）。
- 证据：
  - UI 保存 `use_rerank/rerank_top_n`：`src/web/static/knowledge.js`
  - 后端写入 runtime setting：`src/web/routers/knowledge.py`
  - `smart_retrieve -> _maybe_rerank -> rerank_documents.invoke` 生效路径完整：`src/biz/rag_service.py`
  - 配置开关来源：`config/app_config.json` (`rerank.enabled`, `rag.force_rerank`, `rag.use_rerank_by_default`)

### 0.3 本地截图证据（待复验更新）
- 知识库概览：`image/review_evidence/knowledge_overview.png`
- 聊天页（回答+来源区域/建议区域状态）：`image/review_evidence/chat_response_sources_suggestions.png`

### 0.4 2026-02-10 第二轮执行增量（implementation_guide 对齐）
- `P1 视觉与交互`：修复 `knowledge.html` 中知识库详情页文档区域结构，恢复“文档列表 + 搜索 + 上传”联动布局；知识库卡片支持 `active` 选中态。
- `P1 分段/检索标签`：`knowledge.js` 不再硬编码标签，改为按 `/api/knowledge/collection-settings` 动态显示 `chunk_mode` 与 `retrieval_mode + rerank`。
- `P2 代码质量`：`knowledge.js` 与 `script.js` 的 `apiCall` 增加统一超时（默认 30s）；聊天发送接口设置 120s 超时。
- `P2 上传反馈`：上传改为 `XMLHttpRequest` 进度回调，新增上传进度条与状态（等待/上传中/成功/失败）。
- `P3 后端稳定性`：`smart_retrieve` 增加集合名有效性校验，目标集合无效时自动回退到可用集合；`chat.py` fallback 同步增加可用集合过滤，降低向量 API 失败导致空来源风险。
- `本地回归`：
  - `node --check src/web/static/knowledge.js` ✅
  - `node --check src/web/static/script.js` ✅
  - `pytest tests/test_minimal_retrieval_eval.py -q` ✅ `1 passed`

### 0.5 2026-02-10 第三轮执行增量（UI 走查问题修复）
- `总览入口恢复`：新增侧边栏固定入口“总览”，并在详情页头部增加“返回总览”按钮，避免只能通过隐蔽返回路径切换。
- `子知识库页面修复`：修复 `page-collection-detail` 的 DOM 结构断裂（统计卡片后缺失闭合导致布局异常），恢复“文档列表/搜索/上传”区块的完整渲染。
- `滚动与可读性`：统一 `kb-main`、文档列表、分段详情的可滚动高度，解决“父子块显示不全、无法下拉”。
- `父/子块判定增强`：前端 `isParentNode` 增加 `chunk_type/parent_id/virtual_parent` 联合判断，避免历史脏元数据导致“父块/子块标记错位”。
- `外部噪音说明`：浏览器控制台 `content-script.js` 的 `/ai/wr/user/conf` `HTTP 0` 为扩展注入脚本错误，非本项目后端接口。

### 0.6 2026-02-10 第四轮执行增量（编码与 CRUD）
- `后端路由重建`：`src/web/routers/knowledge.py` 重建为 UTF-8 干净版本，修复历史编码破损引发的语法风险，并保留原有接口。
- `知识库 CRUD`：新增 `POST/PATCH/DELETE /api/knowledge/collections`，支持创建、重命名、删除知识库（可选连带文档删除）。
- `文档 CRUD 补齐`：新增 `PATCH /api/knowledge/documents/{doc_id}` 实现文档重命名；上传/删除/重命名后统一清理缓存与 BM25 索引缓存。
- `下载链路修复`：`/api/knowledge/documents/{doc_id}/download` 优先从文档元数据 `object_key` 下载，避免重命名后原文件下载失败。
- `前端接线`：`knowledge.js` 已接入新建/重命名/删除知识库、重命名文档，并对知识库/文档名增加显示层乱码修复（仅显示层，不改原始键值）。
- `聊天页可见文案`：`script.js` 修复一批用户可见乱码文案（网络错误、会话列表、来源标签、父子块标识等）为简体中文。

### 0.7 2026-02-20 第五轮执行增量（文档内容在线编辑）
- `后端能力`：新增 `PATCH /api/knowledge/documents/{doc_id}/chunks/{chunk_id}`，支持在线修改 chunk 文本，并在可用时同步重算向量。
- `数据层能力`：`DocumentManager.update_chunk_content` 已支持按 `collection_name + doc_id + chunk_id` 精确更新分段内容、写入 `edited_manually/updated_at` 元数据。
- `层级输出增强`：`document_hierarchy` 返回节点 `id`，前端可直接定位并编辑具体 chunk。
- `前端编辑面板`：文档详情页新增“在线编辑分段”面板，支持一键载入、保存修改、失败提示与成功后自动刷新统计/列表/分段详情。
- `一致性保障`：分段编辑后统一触发缓存清理（app cache + BM25 cache），确保后续 chat 检索读取最新内容。
- `已验证`：
  - `python -m py_compile src/web/routers/knowledge.py src/storage/database/document_manager.py src/tools/document_hierarchy.py` ✅
  - `node --check src/web/static/knowledge.js` ✅
  - `pytest tests/test_minimal_retrieval_eval.py -q` ✅ `1 passed`

---

## 1. 本轮必须修复（P0）

### 1.1 前端阻断：knowledge.js 语法与页面联动

#### 问题
- `selectedDocuments` 重复声明，导致脚本报错并中断执行。
- 页面切换目标与模板 ID 不一致（`documents` vs `collection-detail`）。
- 切库后未完整刷新“概览统计/最近上传/文档列表/详情”。

#### 行动
- 删除重复的全局变量声明（保留一处）。
- 统一 `switchPage()` 与模板 `id="page-*"` 的映射。
- 修正 `enterKnowledgeBase()` 和切库事件，确保刷新：
  - 概览统计
  - 最近上传
  - 文档列表
  - 文档详情（若当前处于详情页）
- 清理失效 DOM 选择器（如 `#page-documents`、`#doc-list-kb-name`、`#recent-documents` 等需与模板一致）。

#### 验收
- 页面不再出现 JS 语法错误。
- `/knowledge` 能展示全部知识库卡片。
- 切换库后四类数据都能刷新。

### 1.2 后端检索阻断：smart_retrieve 因向量 API 失败返回空结果

#### 现象
- `chat.py` fallback 已调用 `smart_retrieve`，但 `sources` 仍为空。
- 离线/网络受限时，Embedding API 连接失败导致向量检索路径失效，最终空结果。

#### 根因
- `smart_retrieve` 同时依赖向量检索与 BM25，但当前流程对“向量失败场景”的降级不充分，且在当前环境下 BM25 也未形成可用回传，导致总结果为空。

#### 修复目标
- 即使向量 API 不可用，也要保证：
  - `smart_retrieve` 返回非空候选（至少来自 BM25/本地兜底）
  - `chat` 的 `sources` 尽量非空（金融/规则类问题）

#### 具体改造（建议顺序）
1. 在 `smart_retrieve` 中增强容错：
   - 向量检索异常不影响 BM25 路径执行。
   - 明确记录每路召回数量与错误原因（便于排查）。
2. 增加“最小可用兜底检索”：
   - 若向量+BM25均空，按 `collection_name` 查询最近文档片段（本地数据库）返回前N条，标记 `fallback=true`。
3. 在 `chat.py` fallback 中加入二级回退：
   - `smart_retrieve` 为空时，调用本地兜底检索函数，保证 `sources` 结构完整。
4. 前端 `renderSources` 保持兼容：
   - 支持 `fallback source` 的字段展示。

#### 验收
- 在禁网或 API_KEY 无效场景下，`/api/chat` 对规则类问题 `sources` 不为 `[]`。
- 日志可清晰看到“向量失败 -> BM25/兜底成功”的路径。

---

## 2. 次优先级修复（P1）

### 2.1 父子分段 UI 完整落地
- 在文档详情中展示父/子块标记（badge）。
- 支持“展开全文/收起”。
- 子块显示所属父块信息（`parent_id` 或展示标题）。

### 2.2 聊天“下一步建议”改为基于 AI 回答触发
- 触发参数从用户输入改为最新 AI 回复文本（可附上下文）。
- 保留现有 suggestions 接口与兜底逻辑。

### 2.3 溯源入口治理
- 知识库页不再提供独立“溯源”入口（UI）。
- 后端 `/traceability` 可暂保留为内部调试接口，但不在页面主流程暴露。

---

## 3. 代码审查清单（执行时逐项打勾）

### 3.1 前端
- [x] `knowledge.js` 无重复声明、无失效选择器
- [x] `switchPage` / 模板 ID 一一对应
- [x] 切库刷新链路完整
- [x] 文档详情父子层级可视化达标
- [x] `script.js` 建议触发点改为 AI 回复

### 3.2 后端
- [x] `smart_retrieve` 对向量失败具备稳定降级
- [x] `chat.py` 具备二级来源兜底
- [x] `sources` 字段结构统一并兼容前端渲染
- [x] rerank 开关路径可追踪、日志可见
- [x] 文档分段在线编辑 API 已落地（含缓存失效）
- [x] 文档层级输出包含 chunk 唯一标识（前端可编辑）

### 3.3 联调与验证
- [ ] `/api/knowledge/collections` 返回与 UI 一致（待手工页面复验）
- [ ] `/api/knowledge/documents?collection_name=...` 数据隔离正确（待手工页面复验）
- [ ] `/api/chat` 在向量失败场景仍返回来源（需联调复验）
- [x] `/api/chat/suggestions` 在无 API_KEY 场景仍有兜底输出（代码路径已具备）

---

## 4. 执行顺序（最新状态）
1. [x] 修 `knowledge.js` 阻断问题（语法 + 页面映射 + 切库刷新）。
2. [x] 修 `smart_retrieve` 降级与 `chat` 二级来源兜底（先可用，再优化）。
3. [x] 补齐父子分段 UI 展示细节。
4. [x] 调整建议触发为“基于 AI 回答”。
5. [x] 补齐知识库/文档 CRUD（含知识库增删改、文档重命名）。
6. [x] 补齐“在线编辑 chunk 文本”接口与前端编辑面板。
7. [ ] 完成手工回归与截图复验（`/knowledge`、`/chat`）。

---

## 5. 禁止事项
- 不引入新前端框架（保持原生 JS + Jinja2）。
- 不破坏现有 API 契约。
- 不做与验收目标无关的大重构。
- 不删除用户已有数据。

---

## 6. 交付要求
- 提供每次修改的文件清单与关键变更点。
- 提供回归结果（命令 + 关键输出摘要）。
- 提供最终 2 张截图：
  - `/knowledge` 概览
  - `/chat` 回答含来源与建议
