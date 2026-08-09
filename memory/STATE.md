# memory/STATE.md
更新: 2026-08-10（文档刷新+双链路+视频+选择题专项收口）

## 模式
守护模式（等用户: ① 发送 docs/23 → B4 观察时钟启动; ② 批准 :5050 重启窗口以激活建议映射端点并亲自走场景 A）。

## Git
- HEAD: 见 git log（本地 = GB10 = GitHub 三方对齐, 本轮 push 后同步）
- 本轮 commit 链: fc08f13 (T1+T2 文档刷新+双链路叙事) → 218122f (T3 演示视频) → 7b27d50 (T4 选择题场景A) → 02b768e (hygiene conftest) → T5/ledger commit
- 前置链: 34f673a (:5050 重启四步验证 PASS)

## 服务
- :5050 FastAPI（PID 3224449, uvicorn --workers 2, 2026-08-09 02:0x 重启后未再重启）:
  - **运行的是旧代码**: T4 新增的 /api/m1/schema-suggestions 三端点未载入, 需批准重启窗口
  - 已载入: compare 模糊匹配 + BM25 flag(默认关) + PG 超时加固 + 本地 embedding (qwen3-embedding-0.6b CPU)
  - M2_OPENCODE_ROUTE=on（灰度继续; 回滚演练实测 23s）
- :4096 OpenCode sidecar（tmux opencode-serve）
- :8004 Qwen3.6-35B / :8005 14B / :8100 responses2chat proxy
- :8007 VLM 未运行（VERIFIED-CLOSED）
- docker: zhikuncode + pgvector_15432
- Loop B: 30min 周期常驻（graph-loop-b, 未扰动）

## 质量基线
- pytest: **310 passed / 13 skipped / 0 failed**（+10 新建议端点测试; legacy e2e_browser 显式跳过）
- M2 eval: 确定性 16/16 + AI judge 四维全 5.0（2026-08-08 基线）
- scenario1 回归门禁: 15/15 PASS（华泰 100% / 嘉合 93.8% / TraFax [50,81.8,81.8] / WaveFax 85.7 / guojin HTML 90% / nanhua 65.7%）
- 冻结节点未触碰: test_m1_service.py / docs/m1_schema/ / frozen_hashes.txt

## 本轮交付物
- docs/23 二轮改进表 + 双链路菜单叙事 + docx 发送版（scripts/build_doc23_docx.py 重生成）
- docs/experiments/2026-08-09_demo_script.md（8 段演示脚本）
- docs/experiments/2026-08-09_demo_video/demo.mp4（5:10, 不入 git, scp 取回）+ 9 截图 + steps.md
- docs/26_选择题体验设计.md（场景 A/B 设计 + 能力暴露度 12 项 + T5 对账表附录）
- /m1 建议映射面板（场景 A 最小闭环, 待 :5050 重启激活）

## 下一步（等用户）
1. **:5050 重启窗口** → 载入建议映射端点 → 用户亲自走场景 A（上传新样本 → 徽章 → 勾选应用 → 重解析看 delta）
2. 用户审阅发送 docs/23（+ demo.mp4）→ B4 观察时钟启动（≥100 次 ask / ≥3 天）
3. 场景 B 实现排期: 场景 A 被认可后启动（直连路 ~2h）
4. 无新队列前不开新战线
