# OpenCode 交付链端到端验证（2026-08-05）

> 状态: 活跃（交付链验证基线） | 更新: 2026-08-05 | 取代/被取代: 无
> 环境: GB10（testuser@10.129.237.26），OpenCode 1.18.3，模型 gb10/qwen3.6-35b-a3b（:8004 llama.cpp，mmproj 多模态），PG pgvector :15432，生产 :5050 全程未动。

## 1. 结论一览

| 环节 | 结果 | 证据 |
|---|---|---|
| S1 MCP 启动修复 | PASS | 3 个 start 脚本 PYTHON_BIN venv-first/conda-fallback；rag/vision/tabular smoke 全过；vision 经 :8004 mmproj 实测推理成功（5.7s 出 markdown 表） |
| S2 OpenCode 运行时 | PASS | 单轮问答 7.9s 正确；stability 20/20 all_passed（11.3/12.2/13.0s min/avg/max） |
| S3 M1 链 | PASS | m1-extraction 47.4s（6 样本 100% 解析，勾稽非 SKIP 全 PASS）+ evidence-verifier 31.2s（verdict PASS，仅凭 compact summary） |
| S3 M2 链 Q1 | PASS | m2-qa 带引用回答 总资产=4,013****.83（sample_jiaxing_minan_20231031.pdf / p0_table_2），与 :5050/api/m2/ask 交叉一致 |
| S3 M2 链 Q2 | PARTIAL | m2-qa 找到文档+日期+币种并诚实拒答数值（未编造）；API 同问命中 资产总值=2216****.90（rerank 0.989）。根因见 §4 |
| S3 tabular-runner | PASS | tabpfn v2，推理 1.685s，2 行二分类输出维度正确 |
| S4 skill 层 | PASS | skills.paths 注册仓库 skills/ + 新增 graph-loop-rules skill，会话内可见 |

## 2. 关键修复（本轮提交）

1. **opencode run 挂起根因**：opencode run 会读 stdin 直到 EOF；经 ssh 前台运行时 stdin 是永不关闭的通道 → 永久静默挂起。修复：非交互调用一律 `< /dev/null`（或后台/tmux）。此前 07-29 的验证未复现是因当时调用方式不同。
2. **subagent 不能 CLI 直调**：`mode: "subagent"` 的 agent 被 `opencode run --agent` 拒绝并回退 build。修复：m1-extraction / evidence-verifier / m2-qa 改 `mode: "all"`（保留被 task 编排的能力）。
3. **tabular-runner 无终态输出**：steps=2 不够（工具调用占 1 步）。修复：steps 2→4。
4. **MCP 进程缺 embedding key**：knowledge_search 报 "创建 Embeddings 失败: 未找到 API Key 环境变量 (SILICONFLOW_API_KEY)"，vector=0 bm25=0 全走 fallback。排查确认该 key 在 :5050 进程 environ、.env、仓库、shell rc 中均不存在——**生产 :5050 同样处于降级检索态**（答案分数来自本地 bge-reranker 对 fallback 候选的重排）。修复：start_mcp_server.sh 加载项目 .env（目前仅 PGDATABASE_URL，key 回归后自动生效）；MCP 与 :5050 检索行为对齐（同一 rag_service）。
5. **MCP stdio 协议卫生**：config_loader.py / bm25_retriever.py 的 print 写到 stdout 污染 JSON-RPC 流（客户端报 Failed to parse JSONRPC message）。修复：改 file=sys.stderr。
6. **m2-qa 检索策略 prompt**：fallback 排序=查询词在 chunk 内的包含计数，查询越完整命中越好；prompt 改为"首查必须逐字用用户完整问题"。

## 3. 逐环节证据

### S1 MCP
- smoke rag: knowledge_list_collections 返回 3 collections（knowledge_base / tat-dqa-joint-v1-validation / m1_parsed_statements），is_error=false
- smoke vision discovery: {"tools": ["vision_ocr_extract"]}
- smoke tabular: {"status": "pass", "tools": ["tabular_classify"]}
- vision 实测：M1_VLM_ENDPOINT=:8004/v1/chat/completions + M1_VLM_MODEL=Qwen3.6-35B-A3B-Q4_K_M.gguf + JINRONG_VISION_ALLOWED_ROOTS（路径白名单，默认项目 assets/data）→ is_error=false；直连 curl 5.7s 输出 markdown 表
- :8007 停摆（预期），vision MCP 以 :8004 mmproj 替代验证通过

### S2 OpenCode 运行时
- 二进制 ~/.opencode/bin/opencode 1.18.3（2026-07-16）
- 单轮：`opencode run -m gb10/qwen3.6-35b-a3b "Reply with 2."` → "2"，exit 0，7.9s
- stability：scripts/run_mcp_opencode_stability.py --runs 20 --timeout 120 --model gb10/qwen3.6-35b-a3b → {"runs":20,"passed":20,"all_passed":true}

### S3 多 agent
- M1 链：m1-extraction（bash allow）执行 scripts/m1_statement_parser.py 解析 ~/wzh/m1_samples 顶层 6 样本 → /tmp/opencode/m1_compact_summary.json；evidence-verifier（steps 4，仅读 compact summary）出 verdict：6/6 PASS，unmapped 全 0，SKIP 项按协议接受。注意：模型摘要对中文样本名有轻微转写噪音（福兮/嘉信敏安），verifier 表格内名称正确，不影响判定。
- M2 链：m2-qa Q1（37.7s）带文档/表/字段引用，与 API 数值一致；Q2（61s）诚实拒答数值（见 §4）。API 交叉：Q1 4,013****.83 / Q2 22,16****.90（duration 1.7-2.4s，含本地 rerank）。
- tabular-runner：合成 8 训练行/2 预测行 → jinrong-tabular_tabular_classify → success / tabpfn v2 / 1.685s / 2×2。观察：模型最终输出了概率值，违反其自身 prompt"不打印概率"约束（演示无害，记录在案）。

## 4. 已知差距与修复建议（不在本轮实施）

1. **检索降级（系统级，最高优先级）**：SILICONFLOW_API_KEY 缺失 → vector+BM25 双失效，:5050 与 MCP 同为 fallback+本地 rerank。表现为答案质量对查询措辞高度敏感（Q2 差距根源：fallback 候选集排序后目标 chunk 落在中位，35B 从 10 条结果中未提取到）。修复：由用户决策是否恢复 embedding key（红线：不碰 API key，等用户提供）；或在 ingest 时把 product_name 中文写进 chunk 文本，降低对拼音 sample_id 的依赖。
2. **knowledge_get_source 默认 collection=knowledge_base**：跨集合查源需显式传 collection_name，agent 易漏传。建议把默认值改为"跟随最近一次 search 的 collection"或必填。
3. **M2 链无 rerank 参数透传**：knowledge_search 默认 use_rerank=True 已够用，但 rerank top_n 不可控（config default_top_n=5）。

## 5. 复现命令（GB10）

```bash
cd ~/wzh/projects/agents_final_tech
export PGDATABASE_URL='postgresql://postgres:postgres@127.0.0.1:15432/vector_db'
# 单轮（务必 </dev/null）
bash scripts/run_opencode_gb10.sh run -m gb10/qwen3.6-35b-a3b "Reply with 2." < /dev/null
# M1 链
bash scripts/run_opencode_gb10.sh run --agent m1-extraction "Parse the M1 counterparty statements now." < /dev/null
bash scripts/run_opencode_gb10.sh run --agent evidence-verifier "Verify the M1 extraction results now." < /dev/null
# M2 链
bash scripts/run_opencode_gb10.sh run --agent m2-qa "问题：嘉兴民安的总资产是多少？" < /dev/null
# tabular
bash scripts/run_opencode_tabular.sh run --agent tabular-runner "<合成数据指令>" < /dev/null
# stability
./venv/bin/python scripts/run_mcp_opencode_stability.py --runs 20 --timeout 120 --model gb10/qwen3.6-35b-a3b --output-dir /tmp/oc_stability
```
