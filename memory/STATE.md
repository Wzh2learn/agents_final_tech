# memory/STATE.md
更新: 2026-08-18 00:45（T1 演示准备 + T2 对账审计收口; **演示冻结窗生效中**）

## 模式
**演示冻结窗**（08-18 00:30 起至明日演示结束）: :5050/opencode/vLLM 配置不动,
代码变更演示后; Loop B 照常观察。明日白天导师演示（SSH 隧道+屏幕共享）。
终态 route=on。等: ① 演示 ② 甲方首轮反馈 ③ 导师反馈。

## Git
- HEAD: 16d1246 → +本收口 commit (hash 见 dispatch_log 收口行)
- 三方对齐: GB10 → GitHub → 本机; 冻结工件未动 (甲方 docx bc3785cb / 导师 docx 929a8c65)

## 本轮战绩（T1 演示准备 + T2 对账审计）
- T1: 体检全绿（health/快路 compare 旁路 62ms/隧道 e2e 477ms）; 《明日演示脚本》
  （三段切换 off→on→off, 翻转实测 24.1-24.4s, 逐步话术+预案）; 彩排全流程实跑
  （A1 2.1s / A5 4.1s / A6 3.6s / D1 4.1s / D2 3.6s; 建议面板 14 候选; 截图确认
  WaveFax OCR 表）; 名词速查卡 10 条。
- **agent 路规律定案**: 空闲 >~10min 首问易超 45s 门（47-51s 回落×3）, 连续问稳定
  ~31s（6 次完成 29-41s）→ **条件 GO**: 演示前 5min warm-up 2 发确认 + 两轮题型上场
  + 60s 兜底切 off; warm-up 第 2 发仍回落则 NO-GO 纯直连。
- T2: 进程普查 0 倒挂（8 进程 mtime-vs-start 全 OK, 含 11s 紧边界注）; 声明对账全 OK
  + 3 注（eval 基线早于 P0 修复待重跑 / 演练 6-8 口径决议=发8落8 / B4 快照一致）;
  新发现 4 项记账演示后处置（m1harness 死 pane / zhikuncode 休眠 / 拒答带来源 toggle /
  status.sh mtime 列菜单）。

## 服务
- :5050 UP (route=on, timeout=45, embeddings=137); :8004 A3B UP; :8006 27B UP (qwen3_xml+APC);
  :8008 proxy UP; :8005 DOWN; :8100 UP; :4096 sidecar UP; :15432 PG UP
- tmux: coding-jinrong / graph-loop-b / opencode-serve / vllserve / thinking-proxy
  （m1harness pane 进程已死, 演示后吸收）
- Loop B: 00:11 周期 8/8 PASS; 冻结窗内照常观察

## 质量基线
- pytest 336/13（Loop B 周期）; docs_lint 0/0; sync_skills 21/21; 冻结 5 件 PASS
- eval v2 08-16 23:23 口径: 16/16 / NF 0/9 / judge 5.0×4（**P0 修复前基线, 演示后重跑**）
- B4: asks=1111 (agent=101 含 A3B 时代 / fallback=936 / error=0); 修复后真实完成 6 条

## 下一步（演示后解锁）
1. 演示 → 反馈入账; 解冻后按积压队列: eval 重跑 / 拒答 toggle 评修 / m1harness pane 吸收 /
   status.sh mtime 列 / 缓办清单（任务二 B 一期 / 场景 B / _cleanup_backup / Qoder PAT）
2. 甲方首轮反馈 → M2 延迟菜单拍板（三轮题降轮次或抬超时）
3. 菜单存量: Docling NCAMC / OpenAI4S / docs/28 #2→#1→#4
