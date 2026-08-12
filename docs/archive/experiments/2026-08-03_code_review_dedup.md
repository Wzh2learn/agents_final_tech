# Phase 3 代码审查与去冗余综合报告

- **日期**: 2026-08-03 ~ 2026-08-04
- **方法**: requesting-code-review 模板派 4 个 Loop A reviewer（src / scripts / config+tests / 死代码专项）+ Loop C 3 项审计（review-codebase 全库体检 / differential-review 增量 / spec-to-code-compliance 文档一致性）+ code-cleanup-helper Mode A 冗余扫描；主线程按 receiving-code-review 分诊：只修明显安全项，pytest 保持全绿，不照单全收。
- **报告原文**: docs/experiments/phase3_review_src.md、phase3_review_scripts.md、phase3_review_config_tests.md、phase3_review_deadcode.md、phase3_loop_c_review_codebase.md、phase3_loop_c_differential.md、phase3_loop_c_spec_compliance.md

## 一、七份报告总览

| 报告 | 范围 | 关键结论 | 处置 |
|------|------|----------|------|
| r1 review_src | src/ 分层与安全 | C-2 collection_name 遍历（CRITICAL）；其余分层干净 | C-2 已修 |
| r2 review_scripts | scripts/ 现役/存档 | 编排脚本端口漂移 :5000→:5050（CRITICAL）；目录混乱 | 已修 + 归档 |
| r3 review_config_tests | config+tests | 测试含甲方客户真实数据（CRITICAL）；schema 校验不防 synonym 冲突 | 已脱敏；冲突校验延后 |
| r4 review_deadcode | 死代码专项 | src 5 孤儿 + scripts 11 死脚本 + 8 可归档 | 已删/归档 |
| lc1 review-codebase | 全库体检 | 评级 B（运行健康、架构欠账）；H1-H5 结构性欠账 | H 项全部延后（见四） |
| lc2 differential | scenario1 后增量 diff | 无安全回归；冻结节点完整；F1 新增 vlm_server 风险 | F1 已修，F2/F3 延后 |
| lc3 spec-compliance | docs/17/19/20 vs 代码 | 17/19/20 全部 DRIFTED | 全部已修（含 docker-compose.yml） |

## 二、本轮已修复清单

| # | 修复 | 文件 | 来源 |
|---|------|------|------|
| 1 | collection_name 遍历：upload / delete_document 两处补 `_validate_collection_name` | src/web/routers/knowledge.py | r1 C-2 |
| 2 | 编排/监控脚本端口漂移：`${M1_API_BASE:-http://127.0.0.1:5050}` 统一 | scripts/graph/graph_orchestrator.sh, loop_d_monitor.sh | r2 Critical |
| 3 | orchestrator start_loop_a/c 改为 heredoc 派活指引（一次性 codex exec 口径）；移除 72B 探针 | scripts/graph/graph_orchestrator.sh | r2 + 2026-07-31 决策 |
| 4 | 测试脱敏：ground_truth_values.json 去除客户 id/金额（全量备份在远端 ~/wzh/ground_truth_values_full.json）；test_m2_multiturn.py / test_m2_compare.py 产品名与金额替换为测试值 | tests/ | r3 Critical |
| 5 | 死代码删除：src/tools/knowledge_base.py、src/tools/rag_retriever.py、src/web/app_flask_backup.py、src/scripts/sync_dify_kb.py、src/utils/log/common.py + 11 个 debug/init 脚本 | src/, scripts/ | r4 |
| 6 | 8 个遗留脚本 git mv 至 scripts/archive/；README_scripts.md → docs/archive/ | scripts/, docs/ | r4 / lc1 M6 |
| 7 | rag_tools.py NameError（移除不存在的 AddDocumentInput 引用） | src/tools/rag_tools.py | r1 |
| 8 | vlm_server_8007.py 加固：127.0.0.1 bind、http(s)-only scheme 校验、max_tokens 上限 8192、通用 500 不泄露堆栈 | scripts/vlm_server_8007.py | lc2 F1 |
| 9 | docs/17 漂移修复 10 处：Loop C 载体、:5050 端口锚点、冻结路径 → ~/wzh/m1_samples/m1_table_schema.json、72B 历史注记、§8 索引、演进记录 + Loop A/C 派活说明 | docs/17 | lc3 |
| 10 | docs/19 漂移修复：295ms → ~689ms（含 rerank, warm）双处、Python 3.11→3.11+（实际 3.12）、表结构表述改"4 张标准业务表 + KV 网格表 + 未归类兜底"、路线图生产部署 → ✅ 基础已就绪（Phase 3）、QA 正确率 15/15 → 14/15=93%（OCR 元查询误判已评审接受） | docs/19 | lc3 19-1/2/3/5 + 诚实性对齐 |
| 11 | docs/20 + docker-compose.yml：DATABASE_URL → PGDATABASE_URL（代码唯一读取点名）、库名 m1_statements → vector_db、环境变量表对齐代码实况（M2_LLM_ENDPOINT / LOCAL_EMBEDDING_MODEL_PATH / SILICONFLOW_*） | docs/20, docker-compose.yml | lc3 20-1/2/5 |
| 12 | loop_c_audit_prompt.md 头部：Codex CLI/:8005 14B → Claude Code + qwen3.8-max 一次性派活 | scripts/graph/loop_c_audit_prompt.md | lc3 口径对齐 |

## 三、Mode A 冗余扫描（code-cleanup-helper）

- **过长文件**: scripts/m1_statement_parser.py 1917 行（单文件承载 parse/ocr/reconcile/mapping 四职责）——与 lc1 H1 合并处理。
- **硬编码端口**: `127.0.0.1:8004` 在 src/ 内仅 2 处（m2_service.py 为 env 默认值，pages.py 为静态资源引用）；scripts/ + config/ 另有 17 处（多为独立脚本默认值，可接受，生产化时随 env 清单收敛）。
- **死导出**: src/tools/__init__.py 的 ALL_TOOLS 聚合导出无调用方——保留观察（工具层注册表语义，删除收益低）。
- **目录**: scripts/ 已按本次归档分出 archive/ 层；graph/ 为现役编排目录，保持。

## 四、延后清单（分诊结论：不在整理专项内动刀）

| 项 | 来源 | 延后理由 / 后续动作 |
|----|------|---------------------|
| H1 架构倒挂：m1_statement_parser.py 提升为 src/biz/m1_parser/ 包 | lc1 | 收益最大的重构但 blast radius 大；需独立计划 + Loop B 全量回归，交付前排期 |
| H2 knowledge.py 胖路由跨层直取存储 | lc1 | 需新建 biz/knowledge_service.py 承接；与 H5 测试补强一起做 |
| H3/H4 fail-open 认证（M1_API_TOKEN / M1_ADMIN_TOKEN 未设仅 WARNING） | lc1 | 开发机有意设计（甲方演示零摩擦）；已记入 docs/20 生产清单，生产部署时切 fail-closed |
| H5 tools/ 层零单测（hybrid/bm25/rerank/splitter） | lc1 | 测试补强随 H2 排期；当前 227 tests 覆盖 m1/m2 主链路 |
| F2 `_is_junk_table` 启发式可能误杀合法 2 列表格 | lc2 | 当前 5+15 样本无误杀证据；观察项，出现回归再修 |
| F3 新增主体代码测试缺口 | lc2 | 同 H5 排期 |
| F7 config/ schema override 不在冻结 hash 覆盖内 | lc2 | 治理盲区非违规（历史改动均为增量）；是否把 config/m1_table_schema.json 纳入 frozen_hashes.txt 待甲方口径确认 |
| schema synonym 冲突校验缺失（同名源列可挂多个标准字段） | r3 | 需 schema 校验层设计；与甲方规则配置 UI 的验收标准一起定 |
| git 历史脱敏（filter-repo 清除历史中的客户数据） | r3 延伸 | 涉及改写已推送历史，需与甲方/老师确认后进行 |
| auth/dependencies.py 未使用 | r4 | 保留：认证骨架，生产化时启用 |

## 五、验证

- 基线：远端 pytest 227 passed / 13 skipped（2026-08-03 23:40）。
- 本轮变更后远端复跑：**227 passed / 13 skipped（2026-08-04，绿）**。期间发现并修复两处：
  1. 脱敏改写后的 test_m2_multiturn.py 集成测试指向了语料中不存在的实体 → 改为基于勾稽/元数据的非客户实体三轮对话断言。
  2. pytest 调用方式依赖（scripts.* 命名空间导入需要 rootdir 在 sys.path）→ pytest.ini 增加 pythonpath = .，两种调用方式均通过。
- curl 端点全健康：/health、/api/health/full、/api/metrics、/api/m1/schema、/m1 均 200。
- 冻结节点（tests/test_m1_service.py、scripts/graph/frozen_hashes.txt、schema 冻结 hash）未触碰，Loop B 持续 PASS。
