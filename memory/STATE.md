# memory/STATE.md
更新: 2026-08-22 22:15（侧车修复判定更正: 验收全过 + 拍板 c 维持现状 + FK 竞争记账 + B4 修复后段分段）

## 模式
守护模式。等拍板: ① 甲方首轮反馈（B4 时钟 08-12 启动）② 专利件用户终审 + 亲发导师（三件已冻结收口）③ kiosk A1 方案窗口 ④ L1 矩阵窗口（08-23 晚, runbook 就位）
已关闭: 侧车楔死（修复 + 验收通过 08-22 15:11, 拍板 c）/ L1 基线口径（a）/ L3 路径（A）/ D3 作废 / cron 24h 已删 / content=null CLOSED
**48h 观察期（至 08-24 晚）**: 侧车修复后段完成率 <10% 或甲方要求更高 agent 完成率 → 抬超时(a)再议, 与减 step 数据一起拍

## Git
- HEAD: 本收口 commit; 三方对齐 GB10=GitHub=本机
- 本轮资产: 侧车判定更正+拍板 c 入账 / #LOOP-B-FLIP 行带走 / FK adapter 修复候选记账 / runbook L109 措辞修 / B4 修复后段标记

## 侧车修复终态（2026-08-22）
- 完整验收通过: 楔死解除（"exiting loop" 14:32:34 重现）; 验收① 15:11:59 达成——修复后 58 尝试 / 11 完成 = 19.0%（31.4-45.0s 全在预算内）, 与楔死前 45s era 基线 ~20% 吻合; Loop B overall 15:14 FAIL→PASS（#LOOP-B-FLIP）
- 判定更正: 14:53 "0 完成"判定 = 时点采样不足（15:11 数据坐实）
- **拍板 c 维持现状（不抬超时）**: ① 修复目标=恢复楔死前基线已达成, 无需动 :5050 ② 明晚 L1 需"生产配置未动"基线 ③ 不为外推花重启窗口 ④ 真正完成率提升走减 step（M4 34s→19s）+ L2 瘦身（27k→8-10k, 预热 2 overflow 为现成动机）
- (a) 抬超时保留后备: 48h 观察（至 08-24 晚）<10% 或甲方要求 → 再议
- FK 竞争（超时删 session vs 在途运行）: 08-11 以来已知结构性问题, adapter 修复候选, 不阻塞
- db 备份 ~/.local/share/opencode/backup_20260822/ 保留（恢复 SOP 在 dispatch #SIDECAR-DB-REBUILD）

## B4（分段）
- 回滚点段 128 尝试/0 完成（楔死 era, 修复前）; **侧车修复后段（08-22 14:37 起）: 58 尝试 / 11 完成 = 19.0%**（15:11 口径）
- 两列口径（尝试/完成）统一写全名, 回落率/完成率必须注明（#B4-NAMING）; 48h 观察以 b4_checkpoint.py 两列口径为准

## 服务
- :5050 UP（route=on, timeout=45, embeddings=137, 不重启）; :8004 A3B UP（M1 热路径锁定）; :8006 非 DSpark 生产 UP（GMEM 0.30, 观察期配置不动）; :8008 UP; :8007 空闲; :8005 DOWN（退位断言）; :15432 PG UP
- opencode 侧车 PID 1189803 UP（14:37:35 起, db 已重建）
- Loop B 30min 周期: overall **PASS**（15:14 翻转, 后续周期持续观察）
- kiosk 播放中（agent 路已恢复: 预算内完成 ~19%, 其余 46-50s 超时回落 = 基线预期内）

## 质量基线
- eval 08-22（经 :5050 生产端点）: M1 PASS / 确定性 16/16 / NF 0/9 / judge 四维 5.0
- pytest: 379 passed / 13 skipped（08-22 全量, logs/graph/pytest_latest.txt 全量工件）
- docs_lint: GB10 为准

## 专利三件（用户终审后亲发导师, 主线程不碰）
- md 737 行 hash F8A4B0…61F931635A6 / docx v2 hash 48FF2A…45DC01BC（入 git; 呈递说明已移出正文）/ 邮件草稿 hash 7E39CF…E84E109A6（INDEX 登记）; v1 7954BB… 留本地不入库

## 下一步
1. 08-23 晚窗口（另批）: **L1 thinking 档位裁定矩阵** medium/xhigh 两腿（runbook = docs/experiments/2026-08-22_l1_matrix_runbook.md; 腿直连 :8006, 侧车非硬前置; 还原第一项=生产配置未动验证）
2. 矩阵解读框架 = L2 定论（step 数主导）+ 08-22 三段核查（数据引用不重复复述）
3. 杠杆序（记账, 矩阵后实施）: 减 step（M4 组合 34s→19s −44%）+ 孤儿终结 > L2 context 瘦身 > thinking 档位（质量维度）
4. L3: 盯 timothystewart6 新 tag; **08-29 checkpoint** 无 tag → 路径 B 再评估报告
5. 48h 观察期（至 08-24 晚）: 修复后段完成率数据说话, 决定 (a) 是否再议
6. 缓办: 甲方反馈; kiosk A1 窗口; C4 VL-8B; K3 批跑; NLPCC 核实; adapter FK 修复（候选项）
