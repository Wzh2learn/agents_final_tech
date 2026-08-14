# memory/STATE.md
更新: 2026-08-16（发送后 neat 微轮）

## 模式
守护模式。**docs/23 已发送甲方（08-12）；导师包已发送（08-16，用户亲发）**；等甲方首轮反馈 + 导师反馈。B4 观察窗: asks=513（08-16 实测），≥100 ask / ≥3 天双维度达标（时钟 08-12 起），统计结论随甲方反馈行动。缓至甲方首轮反馈: 任务二 B 一期 / 场景 B / _cleanup_backup 删除 / Qoder PAT。

## Git
- HEAD: 29d1678（发送前微修轮）; 链: 299f77d(终审闭环) → 404a50d(受众分离) → e253abc/cbb9a08(视频 v2) → 29d1678
- 三方对齐（GB10 push → GitHub → 本机 fetch+merge）08-16 验证
- 导师版 docx 冻结: 929a8c65fbdea1bd672f5d8d5ea1fd16（六次冻结; bd3daed4/ab2fed43 作废）; 甲方版 docx 仍冻结 bc3785cb

## 本轮战绩（08-14→08-16 导师包闭环）
- 发送前终审: Loop C 三轮（初审 R2 FAIL 4 图-注不符 → 重拍 5 图 → 复验残差 2 → 三验达标）+ 受众分离轮（builder --audience 开关; 内部痕迹 11 处移除/6 类保留）
- 视频 v2: 3:48, V1-V7 全消解; route off/on 双段录完即恢复 on 并验证
- 文档定稿: D1-D4 + 微修 E1/E2; pytest 口径 334 passed/15 skipped（无 PG 环境; PG 依赖 2 项随环境翻转）
- 自学习台账: 累计净值建议 count 3, 不 apply（等窗口走 SOP）

## 服务
- :5050 UP (route=on, provider=local, embeddings=137, tmux coding-jinrong)
- :4096 sidecar UP; :8004/:8005/:8100/:15432 UP; :8007 down
- Loop B 强化版 30min 周期; tmux 禁杀 graph-loop-b/opencode-serve

## 质量基线
- pytest 334/15（08-15 无 PG 环境口径）; docs_lint 0/0（08-16 复跑）; sync_skills --check 21/21; 冻结节点 PASS
- eval 基线 (08-12): 确定性 16/16 / judge 4.94/5.0/5.0/5.0
- B4: asks=513; agent 路 warm best 13.5s; 回滚 10-23s 实测

## 下一步（等用户/甲方/导师）
1. 甲方首轮反馈 → 解锁: 任务二 B 一期 / 场景 B / 多期数据 / 字段规则表; A2 延迟修复优先级随反馈定
2. 导师反馈 → docs/31/视频微调或科研线推进（VGMC M1 前置 = NLPCC/CCIR 截稿日 pending 人工查）
3. 菜单待拍板: Docling NCAMC 增强 / :8005 judge 分流常态化 / OpenAI4S 接入科研线 / docs/28 #2→#1→#4
4. 累计净值建议 apply 候选等窗口（走 SOP）
