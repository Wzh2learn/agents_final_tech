# memory/STATE.md
更新: 2026-08-28（Round 3 辩证记录用户勾选执行, 主线程本地经 git 交付 = 73ac314; GB10 侧碰撞/基线/C4 在制未提交, 待其收口后对齐）

## 模式
守护模式。论文主线: **Round 3 辩证已收口**——用户按推荐勾选 D1 采纳 / D2 批准 / D3 采纳 / D4 勾 1-5 全, 并已执行: 骨架 → **v2.4**, 对抗建议器臂（台账 #13）设计全稿在案（执行窗口待排）。下一动作 = 对抗臂执行窗排期（依赖段 A 碰撞语料）+ GB10 在制实验收口对齐。

## Round 3 辩证执行（08-28, 主线程本地, commit 73ac314）
- 记录 = 2026-08-27_round3_dialectic_record.md §6 已勾选; 骨架 = 2026-08-26_thesis_narrative_skeleton.md → v2.4
- D1 采纳: 经验命题 1a（碰撞暴露 C=0 → 门控收益 ΔV=0）; I1 口径 = 臂间差只由"碰撞暴露 × 单次碰撞危害"驱动, 可靠性只移动两臂水平
- D2 批准: 对抗建议器臂设计全稿 = 2026-08-28_adversarial_suggester_arm_design.md（五节预注册; 预测①无门控 ΔH<0 单调 / ②门控 |ΔH|≤Σε / ③门拒≥80%, <80%=过度自信利用失效模式; 预算如实上调 ~120-180 次 :8004 ≈12-15min, 单调性需 ≥2 对抗比例）
- D3 采纳: 两次 null 叙事（良性体制=命题 1 空转; 噪声体制=剂量响应+碰撞瓶颈）
- D4 勾 1-5 全: 骨架五项落地（I1 口径 / selective prediction 必修注记 / #12 已执行·碰撞执行中 / #13 新增 / 主图升级"可靠性×碰撞暴露"双因子）, 项 6 条件条款保留; §8 增 Round 3 节 + "对称毒性"更正为对称抑制
- 执行方式注记: GB10 Loop A token plan 曾异常, 本轮由主线程自带 codex 本地执行经 git 交付; GB10 台账后记 08-28 20:0x Loop A 已恢复 + 基线窗已开（见 GB10 THREADS, 未提交）

## 对抗建议器臂（台账 #13, 已批, 执行窗待排）
- 设计稿在案; 依赖序 = 段 A 扩语料碰撞先行（缺失则不开窗）; 红线 = 建议器仅 :8004 / 生产配置零写 / 全合成

## GB10 在制（未提交, 本机与 GitHub 尚无, 待 GB10 收口后 pull 对齐）
- 段 A 扩语料碰撞: 设计稿 + 执行记录 + vgmc_collision_corpus.py + test_vgmc_collision_overlay.py（untracked, 结果以 GB10 logs/graph/eval/vgmc_collision_* 为准, 本机勿引数字）
- 小 A 基线窗（段 D, #BASELINE-WINDOW 起）: vgmc_baseline_judge.py + test_vgmc_baseline.py
- C4 视觉探针首批: 2026-08-28_c4_visual_probe_first_batch.md + render_c4_tables.py + c4_visual_probe.py
- config/schema_suggestions.json 与 research/vgmc_exp1.py 在 GB10 有未提交改动
- **对齐纪律**: 本机 73ac314 触过 THREADS.md/dispatch_log.md（尾部追加）, GB10 同名件亦有未提交追加 → GB10 先提交自身在制件再 pull, 尾部各留各行合并

## 噪声体制实验（08-27, 台账 #12 = P3 null, Round 3 前置背景）
- 四腿两臂终值全同（L0-L2 0.589048 / L3 0.579524）; P1/P2 PASS, P3 null 触发 → 转扩语料碰撞不加档
- 门对噪声有响应而终值不动（固化率 0.73/0.72/0.67/0.47）; 结构性洞察 = 注入表头逐表唯一无碰撞对象
- 工件 + 执行记录 = 2026-08-27_noise_regime_experiment.md; --noise 参数族 + 单测 5/5

## 导师包终态（08-26 凌晨冲刺后）
- docs/31 v2 md+docx: judge 四维 08-26 重测实测入文（4.94/5.0/5.0/5.0, :8004 口径, 零 unusable）; 黑话零命中; sha256 见 send_checklist
- demo_v3.mp4: 186.03s/1080p30/h264+aac; 五门全过; 呈递清单 = 2026-08-25_send_checklist.md

## 规则裁定（一页纸 v3, 已机械裁定, 零圈选）
- 0 过闸 / A: 3.1%<10% 不抬超时 CLOSED / B: steps p50=4 维持 T1 / C: FK 单件窗等批 / D: PSO 落盘+续跑 / E: 积压维持 / F: 不开 :5050 窗
- 挂起: F-J3 孤儿治理 / 减 step 组合拳 / FK 窗口时机; 侧线代圈 08-26 晚: F-J3 圈 b / 组合拳让路论文 / FK 合并激活

## B4（两列口径 尝试/完成 全名）
- 池修复后段 3929: 261/8=3.1%（canary 题型代表性注记维持）; 段 3429: 761/62=8.1%（含池病污染不作数）

## 服务（最近一次全量收口口径, GB10 在制期间或已变, 以实测为准）
- :5050 UP (route=on timeout=45) / :8004/:8006/:8008 UP / :8007 空闲 / PG UP (GUC+pre_ping); Loop B 30min 周期; kiosk 关闭
- Loop A token plan 08-28 曾异常 → GB10 台账记已恢复; Loop B 08-27 20:54 起 FAIL = canary agent 路完成率体制波动（已知症状, 只记账）

## 质量基线
- pytest 见 pytest_latest.txt（392 passed 含噪声层单测 5）; docs_lint 文档 0 fail / 2 warn（docs/26/28 预存）; 本机额外 FAIL[4]=skill 装配漂移（环境特异, 不入仓）
- eval 08-26 01:0x: 16/16 / NF 0/9 / judge 4.94-5.0
