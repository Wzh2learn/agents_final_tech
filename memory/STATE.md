# memory/STATE.md — 当前快照（覆写式）

快照: 2026-08-04 22:00 | 写入: Loop D（夜间产出验收审计完成，回守护模式）

## Loop 状态

- Loop A: 待命（无驻留进程；tmux + codex exec 一次性派活，通道见 CORE.md）
- Loop B: graph-loop-b daemon 常驻 30min（本轮审计未扰动），最近 21:35 @6edf3d9 PASS
- Loop C: 按需 claude -p 派活（qwen3.8-max），降频 12h
- Loop D: 守护模式

## 验收审计结论（2026-08-04 夜间，evidence-based）

- Phase 0 skill 注册: PASS — sync_skills.sh 幂等 (2 次 exit=0 清单一致), codex 实报 A 侧 4 skill + jinrong-docs-sync, claude 实报 C 侧 7/7 PRESENT, 与 AGENTS.md 注册表逐项相符
- Phase 1 codebase_map: PASS — 抽 3 模块核对 (src/biz 4 service 齐全 / m1_statement_parser.py 1917 行与报告一致 / main.py+vlm_server_8007+responses2chat_proxy 存在)
- Phase 2 INDEX: 修复 — 无死引用; 漏登记 docs/README.md 与 datasets data-card 已补
- Phase 3 审查修复: PASS — fix#1 collection 校验 / fix#2 M1_API_BASE 统一 / fix#8 vlm 加固 复验通过; 被删 16 文件无存活引用
- Phase 4 skill diff: PASS — 仓库↔本机↔远端两侧内容一致
- Phase 5 memory: 修复 — CORE 端口表 6/6 实测 200 (8006/8007 确认 DOWN); DECISIONS 补 glm-5.2 验证+回滚条目; 本文件 git 基线修正
- 漂移校准: scenario1 三 gap 实为已解决 (9ea3754/b927efe), 此前误报挂起; THREADS 台账定基线并入 DECISIONS 案例
- 业务冒烟: PASS — 嘉合#0 parse-file 重跑 tables=2 hit[87.5,100] 与 final_results.json 一致; m2/ask 两问均带 sources; health/full embeddings=137 (T2 生效)
- 卫生: PASS — phase3_reports_tmp 已清理 (git clean), docker 仅 zhikuncode+pgvector, llama 进程仅 :8004/:8005

## 验证

- pytest: 227 passed / 13 skipped（2026-08-04 远端复跑全绿）
- git: 本机与 GB10 对齐（6edf3d9 → 本审计提交）
- 冻结节点未触碰；Loop B 持续 PASS

## 下一步

- 守护模式: Loop B 常驻；新任务按 CORE.md 分发通道派活
- 延后事项: docs/experiments/2026-08-03_code_review_dedup.md §4 清单（H1 引擎归位 / H2 knowledge 瘦身 / H5 tools 测试 / fail-closed 生产化 / git 历史脱敏待甲方确认）
- 未决线索: THREADS.md（VLM 恢复条件 / MCP x3 / OpenCode / 甲方待确认四项 + scenario1 遗留南华 65.7%）

## 阻塞项

- 无（甲方侧待确认项见 THREADS.md）
