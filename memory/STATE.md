# memory/STATE.md — 现状快照（唯一现状信源）

> 覆写: 2026-08-09 ~02:10 CST (:5050 经批准重启 + 四步验证全过)

## 模式
守护模式（等用户发送 docs/23；发送后启动 B4 观察时钟: ≥100 次 ask / ≥3 天灰度统计）。

## Git
- HEAD: f1b1f24（本地 = GB10 = GitHub 三方对齐）
- 昨夜沉淀专项 commit 链: c681fc8→24770c4→c863235→6c2fd02→13a37b8→3882455→7fafeb7→f1b1f24

## 服务
- :5050 FastAPI（**2026-08-09 02:0x 经批准重启**, PID 3224449, uvicorn --workers 2）:
  - 已载入: compare 模糊匹配 (24770c4) + M2_ENABLE_BM25 flag (13a37b8, 默认关) + PG 超时加固 (c5a8ecf)
  - 验证: health/full overall=healthy, embeddings=137, provider=local (qwen3-embedding-0.6b CPU)
  - 冒烟: parse 嘉合#0 87.5%/1.5s; QA 2/2 (OCR meta-query sources=3 + 复熙资产总值掩码保留); compare/positions("嘉兴民安") → 2 持仓 ✓; products 列表去噪 7→4 ✓
  - M2_OPENCODE_ROUTE=on + OPENCODE_ASK_TIMEOUT=18（灰度继续; 演示前可 23s 回滚）
- :4096 OpenCode sidecar（tmux opencode-serve, PID 2519995, 载入新配置 + 16 skills, 经 scripts/restart_opencode_sidecar.sh 管理）
- :8004 Qwen3.6-35B / :8005 14B / :8100 responses2chat proxy
- :8007 VLM 未运行（VERIFIED-CLOSED, 重启方法见 THREADS.md）
- docker: zhikuncode + pgvector_15432
- Loop A: deepseek-v4-flash-0731 via Token_Plan_Chat；Loop C: qwen3.8-max 全槽位
- Loop B: 30min 周期常驻（graph-loop-b tmux）

## 质量基线（2026-08-09 定稿）
- pytest: 300 passed / 13 skipped / 0 failed
- M2 eval: 确定性 16/16 + AI judge 四维全 5.0
- scenario1 回归门禁: 15/15 PASS（华泰 100% / 嘉合 93.8% / TraFax [50,81.8,81.8] / WaveFax 85.7 / guojin HTML 90%）
- 冻结节点: test_m1_service.py / docs/m1_schema/ / frozen_hashes.txt 未触碰

## 下一步（等用户）
- 用户审阅并发送 docs/23 → B4 观察时钟启动（≥100 次 ask / ≥3 天, 届时积累灰度统计）
- 无新队列前不开新战线
