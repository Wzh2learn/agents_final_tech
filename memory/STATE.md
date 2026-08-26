# memory/STATE.md
更新: 2026-08-27 01:xx（夜间科研: 骨架 v2.2 落地——噪声体制设计稿/小 B 盲锥骨架/bandit+ρ 设计稿/T4 审计 7 数字全一致）

## 模式
守护模式。论文主线: 骨架 v2.2 落地完成（设计稿四件 + 审计在案, 零新实验执行）。晨间队列: ① VGMC 实验 1 判定过目（两臂退化未现形 + 网格标定, 只记不拍等圈选）② C4 探针窗口批否（2026-08-26_c4_visual_prep.md）③ **噪声体制实验窗口卡草稿批否**（2026-08-27_noise_regime_exp_design.md §7, 台账 #12 = 小 A 决定性实验）④ 4/42 vs 4/53 口径裁定报侧线（evidence_t4_audit.md §2, 骨架正文侧线资产主线程未动）。

## 导师包终态（08-26 凌晨冲刺后）
- docs/31 v2 md+docx: judge 四维 08-26 重测实测入文（4.94/5.0/5.0/5.0, :8004 口径, 零 unusable）; 黑话零命中; 缩写首现展开; sha256 见 send_checklist
- demo_v3.mp4: 186.03s/1080p30/h264+aac; 五门全过（含音画同步 11/11 章 delta<=0.61s, 速度闸 8x→16x+裁剪兜底修复 ch07/ch08）; 三帧目视无乱码
- 呈递清单: docs/experiments/2026-08-25_send_checklist.md（hash 已同步终版）

## 规则裁定（一页纸 v3, 已按规则机械裁定, 零圈选）
- 0 过闸(261 尝试) / A: 3.1%<10% 不抬超时 CLOSED 走结构诊断 / B: steps p50=4 维持 T1 /
  C: FK 单件窗等批 / D: PSO 首批落盘+续跑 / E: 积压维持 / F: 今夜不开 :5050 窗
- 挂起: F-J3 孤儿治理提案(b→a→d→c) / 减 step 组合拳 / FK 窗口时机

## 今夜修复
- F-J1 judge None 安全化 (25 行+3 单测) / F-J2 run_eval 隔离闸 (:8006 排空才打分, 实测闸正确触发)
- judge 重跑走 :8004 结构隔离（F-J2 协议回落）; eval 16/16 + NF 0/9 + judge 4.94-5.0
- PSO 落点②: bank19/7 mutant/B=8 全保持/最小全保持 B=4

## B4（两列口径 尝试/完成 全名）
- 池修复后段 3929: 261 尝试 / 8 完成 = 3.1%（canary 题型代表性注记维持）
- 段 3429: 761/62=8.1%（含池病污染, 不作数）

## 服务
- :5050 UP (route=on timeout=45) / :8004/:8006/:8008 UP / :8007 空闲 / PG UP (GUC+pre_ping)
- Loop B 30min 周期; kiosk 关闭; cron 空

## 质量基线
- pytest 见 pytest_latest.txt（收口全量）; docs_lint 0 fail / 2 warn（docs/26/28 预存）
- eval 08-26 01:0x: 16/16 / NF 0/9 / judge 4.94-5.0
