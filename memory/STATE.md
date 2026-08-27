# memory/STATE.md
更新: 2026-08-27 23:0x（晨间卡: 三圈选入账 + 骨架 v2.3 同步 5725c08 + 噪声体制实验执行 P3 null + T7 基线协议设计稿入库）

## 模式
守护模式。论文主线: **噪声体制实验（台账 #12）执行完毕 = P3 null**——四腿两臂终值全同（L0-L2: 0.589048 / L3: 0.579524）, 预注册处置 = 转扩语料碰撞（骨架候选①）, 不加档重试。三圈选结果（08-27 晨间, 用户拍板）: ① VGMC 实验 1 null result 确认入账（无新动作）② C4 探针窗缓（让路噪声实验 + 等侧线 BC 图; C4 合成题库 = BC 真实分布侧数据依赖, 先后序明确）③ 噪声窗批准并已执行（本卡完成）。

## 噪声体制实验（08-27 22:41-22:53, #VGMC-NOISE-WINDOW）
- 四腿 × 两臂: L1 temp0.8（seed 42/43）/ L2 prompt 退化 / L3 force 0.5; 建议器仅 :8004, 生产配置零写（sha 前后一致）
- P1 单调 PASS（D: −0.031/−0.031/−0.0214）/ P2 有界 PASS（二条款 vacuous）/ **P3 null 触发**（各档两臂 |差|=0）
- 门对噪声有响应而终值不动: 固化率 0.73/0.72/0.67/0.47, L3 门拒 26/58（L0 仅 4/53）; 结构性洞察 = 注入表头逐表唯一, 错误规则在 holdout 无碰撞对象 → 分离两臂须碰撞体制
- 工件: vgmc_noise_{L1s42,L1s43,L2,L3}_results.json + vgmc_noise_curve.json + 执行记录 docs/experiments/2026-08-27_noise_regime_experiment.md
- 噪声层代码: research/vgmc_exp1.py --noise 参数族（50 insertions, --noise none 回归原行为）+ 单测 5/5

## 基线备战（T7 设计稿入库）
- docs/experiments/2026-08-27_small_a_baseline_protocol_design.md: Mem0 式 / AWM 式 / few-shot × （记忆形态/读写接口/评测协议/预算）全预注册; ~131 次 :8004 调用 ≈12min 单窗可跑完; 执行窗口待批（让路序: 扩语料碰撞设计稿 → 基线窗口）

## 导师包终态（08-26 凌晨冲刺后）
- docs/31 v2 md+docx: judge 四维 08-26 重测实测入文（4.94/5.0/5.0/5.0, :8004 口径, 零 unusable）; 黑话零命中; 缩写首现展开; sha256 见 send_checklist
- demo_v3.mp4: 186.03s/1080p30/h264+aac; 五门全过; 三帧目视无乱码
- 呈递清单: docs/experiments/2026-08-25_send_checklist.md（hash 已同步终版）

## 规则裁定（一页纸 v3, 已按规则机械裁定, 零圈选）
- 0 过闸(261 尝试) / A: 3.1%<10% 不抬超时 CLOSED 走结构诊断 / B: steps p50=4 维持 T1 /
  C: FK 单件窗等批 / D: PSO 首批落盘+续跑 / E: 积压维持 / F: 今夜不开 :5050 窗
- 挂起: F-J3 孤儿治理提案(b→a→d→c) / 减 step 组合拳 / FK 窗口时机
- 侧线代圈 08-26 晚（用户授权）: F-J3 圈 b 先行 a 并入窗口队列 / 组合拳立主线本周冻结让路论文 / FK 缓办合并激活

## B4（两列口径 尝试/完成 全名）
- 池修复后段 3929: 261 尝试 / 8 完成 = 3.1%（canary 题型代表性注记维持）
- 段 3429: 761/62=8.1%（含池病污染, 不作数）

## 服务
- :5050 UP (route=on timeout=45) / :8004/:8006/:8008 UP / :8007 空闲 / PG UP (GUC+pre_ping)
- Loop B 30min 周期; kiosk 关闭; cron 空
- Loop B 20:54 起 FAIL（0 agent completions / 30 asks, ≥25 fallbacks）= canary agent 路完成率体制波动（已知症状, 翻转时点对 canary 完成, 只记账不处置）

## 质量基线
- pytest 见 pytest_latest.txt（收口全量, 392 passed 含噪声层单测 5）; docs_lint 0 fail / 2 warn（docs/26/28 预存）
- eval 08-26 01:0x: 16/16 / NF 0/9 / judge 4.94-5.0
