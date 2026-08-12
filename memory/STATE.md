# memory/STATE.md
更新: 2026-08-13 凌晨（发送后队列 S1+S2+S3 全部完成）

## 模式
守护模式。**docs/23 已发送甲方（08-12, 用户亲发）; B4 观察时钟运行中**（≥100 asks / ≥3 天）。发送后队列 S1-S3⑤ 全部完成; 缓至甲方首轮反馈: 任务二 B 一期 / 场景 B / _cleanup_backup 删除 / Qoder PAT。

## Git
- HEAD: 本 commit（S3 收口）; 本轮链: a12bc7c(S1/S2 入账) → bda88f4(S3①) → 6dd189b(S3②) → 61d2fd2(S3③) → ceec4ab(S3⑤) → f86a876(S3④) → 本 commit
- 三方对齐（GB10 push → GitHub → 本机 fetch+merge）

## 本轮战绩（08-12 夜 → 08-13 凌晨）
- S1: B4 JSONL 仪表 + status.sh 一页健康（Q4 L1 落地, loop_d_monitor 退役候选）
- S2: 延迟 a(warm-up 真实检索题)+b(/no_think 契约 C-1) + Q2 别名链 + 批 A + vision roots 一次载入; 六步验证全过; agent 路 warm 13.5s best（1/4 成功, 多检索题 >18s 回落, 根因入 A2 遗留）; 回滚演练 10s
- S3①: 数值核验产品化 (src/biz/number_grounding.py + 6 单测, NF 0/9 一致)
- S3②: dify docx 挖掘 + 3 补词（诚实 delta=0）
- S3③: 检索透明面板（top_k/score/route 可见）
- S3④: Docling 探针（CPU 可用, NCAMC 垂直更优, 离线候选）
- S3⑤: judge 分流交叉一致性 98.4%（:8005 可分流）

## 服务
- :5050 UP (route=on, provider=local, embeddings=137, tmux coding-jinrong:api5050)
- :4096 sidecar UP (16 skills + warm-up); :8004/:8005/:8100/:15432 UP; :8007 down
- Loop B 30min 周期不扰; tmux 禁杀 graph-loop-b/opencode-serve
- docling 独立 venv: ~/wzh/venvs/docling_probe (不碰生产)

## 质量基线
- pytest 336 passed / 13 skipped; docs_lint 五项 0 fail / 0 warn; 冻结节点 PASS
- eval 基线 (08-12 21:57): 确定性 16/16 / NF 0/9 / judge 4.94/5.0/5.0/5.0（:8004 复跑一致）
- agent 路延迟: 13.5s best / 成功率 1/4（a+b 后）; 直连 warm 2.7-3s; 回滚 10s

## 下一步（等用户/甲方）
1. 甲方首轮反馈 → 解锁: 任务二 B 一期 / 场景 B / 多期数据 / 字段规则表
2. B4 积累中（status.sh 可查）; eval 每天经生产端点跑一遍
3. A2 agent 路延迟方差根因（:8004 slot 争用疑似）— 台账遗留, 待排期
4. Docling NCAMC 增强路线 / :8005 judge 分流常态化 — 菜单项待拍板
