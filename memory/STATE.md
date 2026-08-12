# memory/STATE.md
更新: 2026-08-12 夜间（治理体检 5 项收口）

## 模式
守护模式。等用户"已发送"信号; 信号前不开新战线、不对外发送。docs/23 docx md5 bc3785cb4237dcda316120251fab8472 冻结等终审 (12 页)。

## Git
- HEAD: 895e9ac + 本 commit（治理体检 5 项）
- 三方对齐（GB10 push → GitHub → 本机 fetch+merge）

## 治理体检（2026-08-12 夜, 5 项）
- ① AGENTS.md 配属注册表补 jinrong-docs-sync A/C 两行（原 A+C 合并行拆分为两行, 与分发列表逐一对账）
- ② docs_lint.py 新增检查 [5]: AGENTS.md 注册表 ↔ sync_skills.sh A/C_SKILLS 双向 diff（注册未分发/分发未注册 → FAIL）; 首跑 PASS 0 fail/0 warn; AGENTS.md 治理规则同步四项→五项
- ③ DECISIONS.md 08-03 三条目加 SUPERSEDED 注（VLM GGUF 不可得 → 08-08 VERIFIED-CLOSED 取代; 模型路由 Loop A 部分 → 08-06 flash 分工取代, Loop C qwen3.8-max 仍有效; 记录不修部分 → OCR meta-query 08-05 已修/.msg htmlBody c863235, product_name 仍有效）
- ④ run_eval.sh 全量刷新基线: M1 门禁 PASS(12 pass/3 skip quick) / M2 确定性 16/16 / NF 0/9 fail / judge fait=4.94 nume=5.0 cita=5.0 refu=5.0
- ⑤ 本 STATE 覆写 + dispatch_log 五行

## 服务
- :5050 未重启; health 137 embeddings/provider=local/route=on
- :4096/:8004/:8005/:8100 up; :8007 down; Loop B 30min 周期不扰
- tmux: graph-loop-b(禁杀)/opencode-serve/coding-jinrong

## 质量基线
- pytest 325 passed / 13 skipped
- eval 基线 (2026-08-12 21:57): M1 门禁 PASS / 确定性 16/16 / NF 9 条 0 未落地 / judge 4.94/5.0/5.0/5.0
- docs_lint 五项 0 fail / 0 warn
- 冻结节点未动（test_m1_service.py / frozen_hashes.txt / docs/m1_schema/ / docs/23 bc3785cb）

## 下一步（等用户）
1. docs/23 用户终读后亲发甲方 → 发后按序: ①B4 观察时钟(≥100 ask/≥3天) ②延迟 a+b(用户给重启窗口, 同时载入 Q2 别名链) ③docs/28 #2数值claim产品化→#1检索透明面板→#4 Docling 探针(独立 venv)
2. Q1 Top3 + Q4 菜单拍板（:8005 judge 分流 / vision roots / status.sh / 任务卡模板）
3. walkthrough 反馈处置 + 任务二 B 一期排期（先 B 后 A 已批, 代码等发送后）
