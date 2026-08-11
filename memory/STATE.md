# memory/STATE.md
更新: 2026-08-12 午间（T1-T4 + Q1-Q4 双专项收口）

## 模式
守护模式。等用户"已发送"信号; 信号前不开新战线、不对外发送。docs/23 md/docx 冻结 (504810c, 不重生成)。

## Git
- HEAD: 60f5d4e + 本 commit（T1-T4 专项: 审计报告×2 / schema 沉淀 / eval 接线 / 台账）
- 三方对齐（GB10 push → GitHub → 本机 fetch+merge）

## 专项战绩（T1-T4, 2026-08-12 凌晨）
- T1 甲方体验审计: 15 步全过 / 0 console 错误 / 无演示前必修; 口头解释×4 + 可接受×3 → docs/experiments/2026-08-12_client_experience_audit.md
- T2 声明复测: 16/16 生产口径 PASS; 漂移×2 入账（默认路延迟当晚 T4① 修复 RESOLVED; OCR 冷/热口径列口头解释）; docs/23 冻结未改
- T3 Loop C 差分审计 = CONDITIONAL: FC-1 已修; FC-4 fail-open/FC-5 async 阻塞复评 HIGH 存量; FC-7/8/9 合规 → docs/experiments/2026-08-12_audit_loop_c_differential.md
- T4① schema 沉淀: +分红方式/可用份额 标准字段 + FC-1 碰撞修复 → 嘉合×8 87.5→100 / TraFax表3 81.8→100 / NCAMC 75→87.5 / nanhua 75→87.5; 基线 rebuild 门禁 15 pass/0 warn; 嘉合默认路 3.3-9s→63ms; 自学习写入器丢 applied/rejected bug 修复+区段恢复
- T4②: 数值忠实度 eval 接入 run_eval.sh [3/4] 计退出码; .env.example 补 M1_API_TOKEN

## 服务
- :5050 未重启（schema 热加载生效）; health 137 embeddings/provider=local/route=on
- :4096/:8004/:8005/:8100 up; :8007 down; Loop B 30min 周期不扰
- tmux: graph-loop-b(禁杀)/opencode-serve/coding-jinrong; audit-t3+t2eval 一次性会话已关闭

## 质量基线
- pytest 313 passed / 13 skipped; scenario1 门禁 15 pass/0 warn/0 fail（含 OCR 全量口径）
- 冻结节点 md5 未动（test_m1_service.py / frozen_hashes.txt / docs/m1_schema/）

## 日间追加战绩（Q1-Q4, 2026-08-12）
- Q1 资产摸排: Top3 = :8005 judge 分流(实测 no-think 4.4s) / vision MCP 接样本目录(真调 PASS) / status.sh; 详见 sweep 文档
- Q2 映射表别名资产: product_aliases.json + compare 三级解析链 (45 tests, 诚实 delta=0, 重启窗口生效); schema 差集 0 缺口
- Q3 docs_lint.py + sync_skills --check + AGENTS.md "neat 必跑 docs_lint"; 首跑 0 fail/0 warn
- Q4 docs/29 路线图菜单 (L1 status.sh / L2 任务卡 / L3 暂缓), 等拍板
- pytest 325 passed / 13 skipped (+12 alias 测试)

## 下一步（等用户）
1. docs/23 用户终读后亲发甲方 → 发后按序: ①B4 观察时钟(≥100 ask/≥3天) ②延迟 a+b(用户给重启窗口, 同时载入 Q2 别名链) ③docs/28 #2数值claim产品化→#1检索透明面板→#4 Docling 探针(独立 venv, Q1 web_search 情报已备)
2. Q1 Top3 + Q4 菜单拍板（:8005 judge 分流 / vision roots / status.sh / 任务卡模板）
3. walkthrough 反馈处置 + 任务二 B 一期排期（先 B 后 A 已批, 代码等发送后）
