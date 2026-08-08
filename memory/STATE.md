# memory/STATE.md — 现状快照（唯一现状信源）

> 覆写: 2026-08-09 ~01:52 CST (沉淀专项 Phase 1-5 全部完成)

## 模式
队列完成，守护模式（等待用户下一步指令）。

## Git
- HEAD: 7fafeb7（本地 = GB10 = GitHub 三方对齐）
- 今夜关键 commit（按时序）:
  - c681fc8 = P3 skill 化收口: m2-rag-playbook 入武库 + opencode.json 去内联 + S4 机制验证 + 3.5 中性委派结论
  - 24770c4 = P4-4.5: compare/positions 模糊匹配回退 + products 噪声过滤（闭环 08-01 blocked question）
  - c863235 = P4-4.1: preprocess_msg.py 入库 + 8 单测
  - 6c2fd02 = P4-4.3/4.7: schema +8 账号字段（华泰 42.9→100%）+ 回归门控方向感知 + rg 15.1.0
  - 13a37b8 = P4-4.2/4.6: VLM 降采样实验 CLOSED + BM25 真实现与 A/B（决策不修）
  - 3882455 = P4 收尾: bm25 print 卫生修复, pytest 300 全绿
  - 7fafeb7 = P5: sidecar 重启脚本 + skill 漂移检查 + judge rubric 拒答豁免（四维 5.0 基线定稿）

## 服务
- :5050 FastAPI: overall=healthy, embeddings=137, provider=local (qwen3-embedding-0.6b CPU), M2_OPENCODE_ROUTE=on + OPENCODE_ASK_TIMEOUT=18
  - ⚠ 待下次经批准重启生效: compare 模糊匹配(24770c4) + M2_ENABLE_BM25 flag(13a37b8)
- :4096 OpenCode sidecar（tmux opencode-serve, PID 2519995, 01:50 经 scripts/restart_opencode_sidecar.sh 重启, 载入新配置+16 skills）
- :8004 Qwen3.6-35B / :8005 14B / :8100 responses2chat proxy
- :8007 VLM **未运行**（08-09 降采样实验后 kill；结论: 延迟达标但 TraFax 劣化, 维持 VERIFIED-CLOSED, 见 THREADS.md）
- docker: zhikuncode + pgvector_15432
- Loop A: deepseek-v4-flash-0731 via Token_Plan_Chat；Loop C: qwen3.8-max 全槽位（claude -p 需 --dangerously-skip-permissions）
- Loop B: PASS 01:37（30min 周期, graph-loop-b tmux 常驻）

## 质量基线（2026-08-09 定稿）
- pytest: 300 passed / 13 skipped / 0 failed
- M2 eval: 确定性 16/16 + AI judge 四维全 5.0（faithfulness/numeric/citation/refusal）
- scenario1 回归门禁: 15/15 PASS（华泰 100% / 嘉合 93.8% / TraFax [50,81.8,81.8] / WaveFax 85.7 / guojin HTML 90%）
- 门控脚本: scripts/m1_scenario1_regression.py（方向感知: 下降超差 FAIL, 提升 WARN）
- 冻结节点: test_m1_service.py / docs/m1_schema/ / frozen_hashes.txt 未触碰

## 本轮沉淀资产清单
- skills/m2-rag-playbook/（新）+ m1-gap-triage SOP 扩充; 注册 sync_skills.sh A/C 双端 + AGENTS.md 武库表
- scripts/: restart_opencode_sidecar.sh, graph/check_skill_sync.sh, preprocess_msg.py, m2_bm25_ab.py
- tests/: test_m2_compare_fuzzy.py, test_preprocess_msg.py
- schema: config/m1_table_schema.json +8 账号上下文标准字段
- 台账: THREADS.md 收入 4.2/4.6 结论 + 3.5 中性委派 CLOSED; blocked_questions 08-01 条目 RESOLVED

## 下一步（等用户拍板）
- :5050 重启窗口（载入 compare 模糊匹配 + BM25 flag 代码）
- docs/23 发送甲方（唯一人工阻塞项, B4 观察时钟随之启动）
