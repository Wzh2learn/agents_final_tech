# memory/STATE.md
更新: 2026-08-23 01:00（L1 thinking 档位裁定矩阵已执行: 两腿 NO-GO, 准路默认维持 thinking=OFF; 08-19 xhigh 起步正式作废; runner reasoning fallback 补丁; N2/N3/N4 已记账）

## 模式
守护模式。等拍板: ① 甲方首轮反馈（B4 时钟 08-12 启动）② 专利件导师五项定夺反馈（三件已发导师 08-22 晚）③ N3 agent 超时抬升（数据输入就位, 执行需 :5050 重启窗）
已关闭: 侧车楔死（修复 + 验收通过 08-22 15:11, 拍板 c）/ L1 基线口径（a）/ L3 路径（A）/ D3 作废 / cron 24h 已删 / content=null CLOSED / 专利三件已发导师（08-22 晚）/ **kiosk 正式关闭（选项 B 08-22: A1 方案/演示观感/建议计数观察全 CLOSED, 提案归档）**/ **L1 thinking 档位矩阵（NO-GO 08-23: thinking ON 无延迟收益, 准路默认维持 OFF）**
**48h 观察期（至 08-24 晚）**: 侧车修复后段完成率 <10% 或甲方要求更高 agent 完成率 → 抬超时(a)再议, 与减 step 数据一起拍; **口径注**: kiosk 停摆后本段新增样本 = 纯金丝雀（~8 行/时）, 48h 到点若样本不足需重议口径

## Git
- HEAD: 本收口 commit（08-22 夜间收尾轮元认知审计）; 三方对齐 GB10=GitHub=本机
- 本轮资产: 元认知快照（七项对账 + 漂移 D1-D4）/ 侧车启动器入库 scripts/sidecar_launch.sh / INDEX+THREADS 洁癖 / #NIGHT-AUDIT-T1~T5 记账 / 冻结件 md5 复验（甲方件 + 专利三件）

## 侧车修复终态（2026-08-22）
- 完整验收通过: 楔死解除（"exiting loop" 14:32:34 重现）; 验收① 15:11:59 达成——修复后 58 尝试 / 11 完成 = 19.0%（31.4-45.0s 全在预算内）, 与楔死前 45s era 基线 ~20% 吻合; Loop B overall 15:14 FAIL→PASS（#LOOP-B-FLIP）
- 判定更正: 14:53 "0 完成"判定 = 时点采样不足（15:11 数据坐实）
- **拍板 c 维持现状（不抬超时）**: ① 修复目标=恢复楔死前基线已达成, 无需动 :5050 ② 明晚 L1 需"生产配置未动"基线 ③ 不为外推花重启窗口 ④ 真正完成率提升走减 step（M4 34s→19s）+ L2 瘦身（27k→8-10k, 预热 2 overflow 为现成动机）
- (a) 抬超时保留后备: 48h 观察（至 08-24 晚）<10% 或甲方要求 → 再议
- FK 竞争（超时删 session vs 在途运行）: 08-11 以来已知结构性问题, adapter 修复候选, 不阻塞
- db 备份 ~/.local/share/opencode/backup_20260822/ 保留（恢复 SOP 在 dispatch #SIDECAR-DB-REBUILD）
- 启动器入库: scripts/sidecar_launch.sh（/tmp 版 08-22 夜间审计定型入库, 内容照搬）, db 恢复 SOP 引用改指仓库路径

## B4（分段）
- 回滚点段 128 尝试/0 完成（楔死 era, 修复前）; **侧车修复后段（08-22 14:38:33 起, 段起点行 3429）**: 15:11 口径 58 尝试/11 完成 = 19.0%; 22:19 b4_checkpoint.py 冒烟 **57 尝试 / 11 完成 = 19.3%**, 回落率 80.7%（超时回落 46）
- 两列口径（尝试/完成）统一写全名, 回落率/完成率必须注明（#B4-NAMING）; 48h 观察以 b4_checkpoint.py 两列口径为准

## 服务
- :5050 UP（route=on, timeout=45, embeddings=137, 不重启）; :8004 A3B UP（M1 热路径锁定）; :8006 非 DSpark 生产 UP（GMEM 0.30, 观察期配置不动）; :8008 UP; :8007 空闲; :8005 DOWN（退位断言）; :15432 PG UP
- opencode 侧车 PID 1189803 UP（14:37:35 起, db 已重建）
- Loop B 30min 周期: overall **PASS**（15:14 翻转, 最新周期 08-22 21:53 持续 PASS, schema_suggestions 豁免生效）
- **kiosk 正式关闭**（08-22 用户终判选项 B; 归因定论 = 窗前暂停未复活, 停点 = B4 行 3092 = DSpark 窗口 v2 切换点; 启动方式失考 = 仓库无 runner 未纳管资产; A1 方案/演示观感/建议计数观察全 CLOSED; 规则入账: 常驻演示资产必须 runner 入库 + Loop B 健康断言, 不允许无册运行）
- 已知漂移: :5050 运行代码滞后（HEAD 的 08-21 m2.py M1_B4_LOG_PATH 修复未激活, 待重启窗, 只记账不动）

## 质量基线
- eval 08-22（经 :5050 生产端点）: M1 PASS / 确定性 16/16 / NF 0/9 / judge 四维 5.0
- L1 矩阵 08-23（直连 :8006）: medium 13/16 + NF 1/9 + judge 4.67; xhigh 16/16 + NF 0/9 + judge 4.875; 两腿 NO-GO（报告 2026-08-23_l1_thinking_matrix.md）
- pytest: 379 passed / 13 skipped（08-22 全量, logs/graph/pytest_latest.txt 全量工件）
- docs_lint: PASS 0 fail / 9 warn（08-22 夜间复跑, GB10 为准）

## 专利三件（已发导师 08-22 晚, 等导师五项定夺反馈; 主线程不碰）
- md 737 行 hash F8A4B0…61F931635A6 / docx v2 hash 48FF2A…45DC01BC（入 git; 呈递说明已移出正文）/ 邮件草稿 hash 7E39CF…E84E109A6（INDEX 登记）; v1 7954BB… 留本地不入库

## 下一步
1. **L1 矩阵已裁定 NO-GO（08-22 夜窗执行）**: 准路默认维持 thinking=OFF; xhigh 记为用户可选"深度"档菜单项（citation/refusal 5.0 + 跨期诱导抗性, 代价单步 p50 ~58s）; 报告 docs/experiments/2026-08-23_l1_thinking_matrix.md
2. 延迟根治 = 减 step + L2 瘦身（第一梯队; L2 定论 step 数主导 + L1 矩阵坐实 thinking 无延迟收益）
3. 杠杆序（记账, 等窗口）: 减 step（M4 组合 34s→19s −44%）+ 孤儿终结 > L2 context 瘦身 > thinking 档位（质量维度, xhigh 深度档菜单项）
4. L3: 盯 timothystewart6 新 tag; **08-29 checkpoint** 无 tag → 路径 B 再评估报告
5. 48h 观察期（至 08-24 晚）: 修复后段完成率数据说话, 决定 (a) 是否再议
6. 缓办: 甲方反馈; **:5050 重启窗（激活 HEAD 代码, 含 M1_B4_LOG_PATH 修复）**; N3 agent 超时抬升拍板; C4 VL-8B; K3 批跑; NLPCC 核实; adapter FK 修复（候选项）
