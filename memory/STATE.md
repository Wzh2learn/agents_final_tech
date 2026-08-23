# memory/STATE.md
更新: 2026-08-24 00:20（08-23 夜收口: :5050 一窗全激活三件 + PG 根治 + TODO 梳理专项四资产; Loop C 差分审计两对象 PASS; HEAD 1fe4e41 三方对齐）

## 模式
守护模式。等拍板: ① 甲方首轮反馈（B4 时钟 08-12 启动）② 专利件导师五项定夺反馈（三件已发导师 08-22 晚）③ 超时 (a) 45→60-75s——等 08-24 23:50 cron 48h checkpoint 数据（判据预写: 段 C+D 完成率 <10% → 再议, ≥10% → 维持）④ 五项用户决策备忘录 D1-D5 圈选（docs/experiments/2026-08-23_user_decision_memos.md）⑤ M4 减 step A/B 拍板（方案就位, 窗口后排）
本轮已关闭: PG 池打满（GUC 持久化 + 实例缓存根治, Loop C 审计 PASS）/ FK 竞争（菜单 a 落地, 持久化恢复, 08-11+08-14 合并条目 CLOSED）/ M1_B4_LOG_PATH 激活（08-22 审计"代码滞后"条 CLOSED）/ backlog 台账建成（docs/29 附录, 新发现即时登记规则）
**48h 观察期（至 08-24 晚）**: 侧车修复后段完成率 <10% 或甲方要求更高 agent 完成率 → 抬超时 (a) 再议, 与减 step 数据一起拍; 口径注: kiosk 停摆后样本 = 纯金丝雀; 段 B（08-23 11:45-20:20）PG 打满污染, 判定剔除或降权（预写口径在 THREADS）

## Git
- HEAD: 1fe4e41（08-23 夜 TODO 梳理专项收口, 跨日 08-24）; 三方对齐 GB10=GitHub=本机
- 本轮双 commit: 07a7c16（:5050 一窗全激活三件）→ 1fe4e41（专项四资产 + 审计后续）
- 本轮资产: 窗口三件 + 重启 SOP scripts/restart_m1_harness.sh + 新测试 5 项 + 窗前存档 / backlog 台账 docs/29 附录（30 条四组）/ 五项决策备忘录 / Loop C 审计报告 / M4 A/B 方案

## :5050 代码窗一窗全激活（2026-08-23 23:22-23:35, 用户批准提前）
- 三件: ① FK 菜单 a（超时不删 session + completed 标志）② vector_store 实例缓存（engine-per-search 根治）③ M1_B4_LOG_PATH 随重启生效（生产默认路径, env override 仅测试隔离）
- 证据: 重启 6s 新 PID 2300096（23:27:09, env timeout=45 / route=on 未动）/ /api/health/full healthy / QA2+compare+canary 4/4 / pytest 384/13（+5 新测试）
- FK 验收双条件 PASS: db 三表 0/0/0 → 9/44/118 + FK 错误停涨于 136（持久化恢复成立）
- agent 路实值: 6 尝试全回落 47.6-70.5s（窗口样本不构成结论, 按 48h 口径续观察）
- B4 第五分段点 3682 @23:27; checkpoint 3429 冒烟 PASS（259 行）读路径连续; 超时 (a) 不预载; 回滚口径 = 原参数重起（SOP 在库）

## PG 事故与根治（2026-08-23）
- 事故: :15432 饱和 100/100, 生产检索间歇降级, Loop B 翻转 5 次; 窗口 restart + GUC idle_session_timeout=10min 持久化（T+30min idle=0 闭环）
- 根治: vector_store 实例缓存（菜单 a, 07a7c16）——根因 engine-per-search（缓存类非实例）; GUC 兜底; B4 污染段 11:45-20:20 判定降权
- Loop C 差分审计两对象 PASS（4 LOW + 13 INFO, 无 C/H/M）: 归因报告更正注入账（行号引用/调用点角色标注瑕疵, 结论不动摇）+ F17 测试断言补强 + 测试文件 sys.path 守卫（修单文件隔离缺陷）
- 残留: compose(pg16/m1_pgvector) vs 在跑容器(pg15/pgvector_15432) 漂移只记账不修

## B4（分段, 两列口径 尝试/完成 写全名）
- 侧车修复后段（08-22 14:38:33 起, 段起点 3429）: 累计 **263 尝试 / 49 完成**, 回落率 81.4%（00:09 checkpoint; 含段 B 污染降权, 明晚 23:50 cron 按预写口径判定）
- 窗口段标记: 第五分段点 3682 @23:27（:5050 重启）
- 窗口后手工复测 q06 正确（3508.55, 源 sample_jiaxing_minan 命中 0.7889; agent 超时回落直连答对, B4 行 route=direct fell_back=true）

## 侧车修复终态（2026-08-22, 未变）
- 完整验收通过（15:11:59, 修复后 58 尝试/11 完成 = 19.0% ≈ 楔死前基线）; 拍板 c 维持现状不抬超时; (a) 保留后备至 48h 观察
- db 备份 ~/.local/share/opencode/backup_20260822/ 保留（SOP 在 dispatch #SIDECAR-DB-REBUILD）; 启动器在库 scripts/sidecar_launch.sh

## 服务
- :5050 UP（新 PID 2300096, 08-23 23:27:09; route=on, timeout=45, embeddings=137）; :8004 A3B UP（M1 热路径锁定）; :8006 非 DSpark 生产 UP（GMEM 0.30, 观察期配置不动）; :8008 UP; :8007 空闲; :8005 DOWN（退位断言）; :15432 PG UP（GUC 10min）
- opencode 侧车 PID 1189803 UP（08-22 14:37:35 起）
- Loop B 30min 周期: 23:51 周期 FAIL = canary q06 随机抖动（判别见下）, 其余步全 PASS（pytest/拓扑/watchdog/dirty=0/git 对齐）; 下周期预期翻绿, 否则按 canary 检索抖动口径优先处置
- **canary 判别（00:12 定论）**: 非窗口回归——① canary FAIL 历史 102 次（已知噪声, 含今日 PG 饱和段连败）② 窗口验证 23:33 canary 4/4（含 q06）③ 手动复测 00:12 答对（命中 0.7889）④ 病灶 = agent 超时回落 + 直连路检索偶发弱命中, 与 81% 回落率同源（M4 减 step 才是根治）
- kiosk 正式关闭（08-22 选项 B, 详见 THREADS）

## 质量基线
- eval 08-22: M1 PASS / 确定性 16/16 / NF 0/9 / judge 5.0
- L1 矩阵 08-23: medium/xhigh 两腿 NO-GO, 准路默认维持 thinking=OFF（报告 2026-08-23_l1_thinking_matrix.md）
- pytest: **384 passed / 13 skipped**（08-24 收口全量, 含窗口新测试 5 项 + F17 断言补强 + sys.path 守卫; logs/graph/pytest_latest.txt）
- docs_lint: PASS（Loop B 23:51 周期 STEP7; GB10 为准, 本机 autocrlf 结构性 FAIL 不采信）

## 专利三件（已发导师 08-22 晚, 等导师五项定夺反馈; 主线程不碰）
- md 737 行 hash F8A4B0…61F931635A6 / docx v2 hash 48FF2A…45DC01BC（入 git; 呈递说明已移出正文）/ 邮件草稿 hash 7E39CF…E84E109A6（INDEX 登记）; v1 7954BB… 留本地不入库
