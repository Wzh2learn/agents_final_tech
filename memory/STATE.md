# memory/STATE.md
更新: 2026-08-13 凌晨（科研线与守备强化队列 R1/R2/R3 完成）

## 模式
守护模式。**docs/23 已发送甲方（08-12, 用户亲发）; B4 观察时钟运行中**（≥100 asks / ≥3 天）。发送后队列 S1-S3⑤ 全部完成; 夜间科研线队列 R1/R2/R3 全部完成; 缓至甲方首轮反馈: 任务二 B 一期 / 场景 B / _cleanup_backup 删除 / Qoder PAT。

## Git
- HEAD: 本 commit（R3 收口: 学术 skill 安装 + docs/30 + 台账）; 前序 e508a5c (R1 Loop B 强化)
- 三方对齐（GB10 push → GitHub → 本机 fetch+merge）

## 本轮战绩（08-13 凌晨 R1/R2/R3）
- R1: Loop B 强化（QA 金丝雀 4 题 + git 对齐 + docs_lint + FAIL 翻转 dispatch, flag 增量默认不变, 破坏验收过）; 旧 daemon 停摆事故 → 重建
- R2①: zhikuncode 探针 = 维持云配置（:8100 /responses-only 与 Chat Completions 不兼容）
- R2②: OpenAI4S 最小科研循环验证通过（独立 venv/目录, 未接生产, 可作 docs/30 执行器）
- R3: codex-claude-academic-skills 审计安装（3 skill A 配属, sync --check 21/21）+ docs/30 VGMC 规划入库登记

## 服务
- :5050 UP (route=on, provider=local, embeddings=137, tmux coding-jinrong:api5050)
- :4096 sidecar UP (16 skills + warm-up); :8004/:8005/:8100/:15432 UP; :8007 down
- Loop B 30min 周期运行（强化版: canary/git/lint/flip）; tmux 禁杀 graph-loop-b/opencode-serve
- 科研隔离资产: ~/wzh/venvs/openai4s_probe + ~/wzh/research/{openai4s_probe,openai4s_data_probe,academic_skills_audit}; docling venv ~/wzh/venvs/docling_probe（均不碰生产）

## 质量基线
- pytest 336 passed / 13 skipped; docs_lint 五项 0 fail / 0 warn; sync_skills --check 21/21; 冻结节点 PASS
- eval 基线 (08-12 21:57): 确定性 16/16 / NF 0/9 / judge 4.94/5.0/5.0/5.0
- agent 路延迟: 13.5s best / 成功率 1/4（a+b 后）; 直连 warm 2.7-3s; 回滚 10s

## 下一步（等用户/甲方）
1. 甲方首轮反馈 → 解锁: 任务二 B 一期 / 场景 B / 多期数据 / 字段规则表
2. B4 积累中（status.sh 可查）; eval 每天经生产端点跑一遍
3. 科研线 M0 文献调研（docs/30 文末任务卡, 只读 2h）— 待用户排期
4. A2 agent 路延迟方差根因（:8004 slot 争用疑似）— 台账遗留, 待排期
5. Docling NCAMC 增强 / :8005 judge 分流常态化 / OpenAI4S 接入科研线 — 菜单项待拍板
