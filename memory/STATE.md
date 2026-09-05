# memory/STATE.md
更新: 2026-08-31 夜（:8006 有条件放宽裁定入账 + 侧线移交五件 + 蓝图 v2 对齐 + P0-1 相关工作 v4 + P0-2 D1 设计稿/卡（Loop A 执行）+ P1 两件草案; 前序: 2026-08-30 Phase A（外部专家评审采纳: J1-J7 圈选入账 + C2 措辞覆盖 + 序列重冻结 Phase A-D（T3/T5 暂停, T3→D4/T5→P2）+ 六件尸检 + Paper Claim Set v2 冻结 + PSO 出贡献（专利 crosswalk 核对在案）; 前序: 2026-08-30 白天（W2 收口绿态: 三方对齐 60887e6 + 主线程抽验 26/26 + 完整版一页纸待圈选 J1-J6 + 圈选 ①a②a③F-1 入账落稿 + summary-recompute-guard 机械化上线; 前序: 论文补强执行会话 II: T3 裁定=a（TAT-DQA joint-v1 仅限 T3 解冻, validation split only, 完成即恢复冻结）+ T5 裁定=批错位治理（C4 案 b 单列裁剪, :8007 一窗用毕即停）+ 执行体系更正在案（实验执行一律 Loop A@GB10, 主线程拟卡抽验记账）+ T1/T2/T6 预注册设计稿三件在案（待执行路径复述确认后开卡）; 前序: 2026-08-29 23:2x（论文补强执行会话: 主线 = 会议小论文证据补强（蓝图 Phase 1-3, T 卡制）, 路线评审输入 1.txt（sha256 6E24362C…D72145E）吸收进 docs/34+蓝图+计划三件, 原始件存档 experiments/2026-08-29_paper_route_review_input.md; 前序: 03:2x 元复审修复两件 + HANDOFF 快照; 前序: 全盘复审收口: 3 blocking 修复审过 + Loop C 首份交付 + S1-S5 通过项; 前序: B 扩碰撞窗收口 + 骨架 v2.5 + 伴生问题入账; 前序: 科研线队列收口 + 注册表↔分发漂移修复（侧线 7a65bea 副作用, 30 件登记对齐）+ 前序: 前序收口在案: 段 C bandit replay / 段 A 扩语料碰撞（P3 未触发）/ K2 章草稿 v0 / 段 B C4 探针首批 / 段 D 基线窗（三基线不可分）+ 侧线 Round 3 记账三行随收口带走）

## 模式
**当前裁定（2026-08-31, 资源与序列）**: ① :8006 有条件可用（五条件, CORE 在案; 唯一有效放宽; J7 不自动开）② 今晚零端点任务: P0-1 相关工作 v4（四簇重排, 六线索实查落 BibTeX, BiomniBench 禁用）+ P0-2 D1 突变体有效性审计（设计稿预注册 → Loop A 零端点执行, 三分类 118 注入 + 9 突变体, M7 归不可观测原样保留）+ P1-1 统计预案草稿 + P1-2 D2 卡草案 ③ 蓝图四点同步（L8/L24/L35 更正 + L10 核过, 同 commit）④ 白天窗口序列（明日起）: D2 跨匹配器（:8004 主; :8006 按条件）→ D3 matched-specificity（零端点校准先行 + judge 白天窗）→ D4 = 原 T3（TAT-DQA 解冻条款照旧）; 每段停一次 autopsy; T5 降 P2 ⑤ 今晚零窗口零端点零对外。⑥ 夜间收口: P0-1/P0-2/P1-1/P1-2 四件全完成——D1 执行绿态（三分类 85/7/26, MO/MU 8/1, M7=MU 原样保留; 预注册 P1-P6 全 true; 门 G1-G7 全过, G6 闸修 1 次纪律内; 抽验 7/7; 工件 d1_mutant_validity_audit.json; Loop A commits 285a93d/4384e90）; D1 autopsy 完成（DR-1..5 用户批准）; D2 零端点窗已派发（GB10 22:22; 零端点窗不限时段裁定在案）→ 等 SESSION_ENDED → 工件入账 → D2 autopsy 停一次再续; 方向性结果（盲区消失/τ<0.8）立即上报不等排期。
**当前裁定（2026-08-30 Phase A, 外部专家评审采纳）**: ① 圈选 J1-J7 入账（J1-J6=a; J7 端点鲁棒性窗条件开放; 详见 THREADS #RULING-J1-J7-EXPERT-REVIEW）② C2 表述覆盖为更保守句（判据冻结不变; 落稿 paper/draft_v0_s1_s2_s6.md）③ 序列重冻结: T3/T5 派发暂停 → Phase A（已完成: 六件尸检 + Claim Set v2 冻结, 见 2026-08-30_phase_a_autopsy_and_claim_set_v2.md）→ Phase B 文献重定位（四簇六线索实查, BiomniBench 未证实前禁用）→ Phase C 新判据预注册（含 118 注入表级聚类统计, 不得按 iid 引 CI）→ Phase D（D1 突变体审计 → D2 跨匹配器 → D3 同 FPR → D4=原 T3, 解冻条款不变）; 每段停一次尸检; T5 降 P2 ④ PSO 从贡献删除, 方法一句带过; docs/34 更正注记入账（专利终态件只读零改动）⑤ 记账更正销账: "余量 78 不足 16×4" = 算术错误（64≤78）。下一步 = Phase B（主线程, 零端点）。
**当前裁定（2026-08-30 白天, W2 收口）**: ① W2 收口绿态: GB10 ahead 3 提交已推（在制件 91a2042 + INDEX 合并 e0fb601）, 三方 = 60887e6; 主线程抽验 26/26 复算过（research/paper_w2_spotcheck_recompute.py → logs/graph/eval/w2_spotcheck_recompute.json）+ GB10 27 件输入/脚本 sha 零漂移; 派发证据 = tmux loop-a-w2 + Loop A commits 5e2498d/f1bf00b/36ab25f ② 用户圈选入账（判据冻结）: ①a 分层提供定位与诊断不主张检出优越（冻结降级措辞）/ ②a 谱排序稳定+极差量化机制入正文 / ③ T6 分支 a 入效度威胁节 / F-1 fixture=「内部校准臂」正文只引公开底座; 落点 paper/draft_v0_s1_s2_s6.md（S1/S2/效度威胁占位节）③ Hook Escalation 第 3 次触发 → 机械强制上线: scripts/graph/hooks/summary-recompute-guard.precommit.sh + summary_recompute_guard.py（收据块 gen/check, sha raw+LF 双口径, 数值容差 5e-5; AGENTS.md 机械强制层 #5）④ 完整版一页纸（2026-08-30_decision_sheet_full_w2.md）待圈选 J1-J6（F_W2_4 量化地板 / F_W2_1 M7 / C3 降级 / 预算轴饱和 / E1.5 变体 2 / F-SC-1 加编两列缺失）; **圈选前 T3/T5 零派发**。
**当前裁定（2026-08-30 00:1x, 论文补强执行会话 II）**: ① T3 = 裁定 a（TAT-DQA joint-v1 仅限 T3 解冻: 只在已冻结 validation split 构造注入, test split 零触碰, 不重开旧实验循环, T3 完成即恢复冻结）, 先拟卡再执行 ② T5 = 批错位治理（C4 菜单 b 案单列裁剪, 预注册 33%→≤5%, 门 <10%; 治理零端点; 复跑视觉判别一次 :8007 窗用毕即停）, 先拟卡再执行 ③ 执行体系更正: 实验执行（T1-T6）一律 Loop A@GB10（tmux 直启, 双档 profile）, 本地 = 拟卡/写文档/抽验/记账; 主线程直跑仅 Loop A 异常时且显式记账; 计划文档 T1/T2/T6 执行者字样已更正（同 commit）④ T1/T2/T6 预注册设计稿三件在案（2026-08-30_t1/t2/t6_*_design.md）; 开卡前置 = 用户确认执行路径复述。
**当前裁定（2026-08-29 23:2x, 论文补强执行会话）**: 主线 = 会议小论文证据补强执行（蓝图 Phase 1-3, T1-T8 任务卡, 见 docs/superpowers/plans/2026-08-29-long-horizon-evaluation-paper.md）; 零端点卡先行（T1 E1.1-E1.4 / T2 E2.1-E2.3 / T6）; T3 第二数据流 / T5 视觉 = 阻塞, 未获用户裁定前不启动; 路线评审输入（D:\Desktop\1.txt, sha256 6E24362C…D72145E）吸收进 docs/34 + 蓝图 + 计划三件, 原始件存档 docs/experiments/2026-08-29_paper_route_review_input.md; 审阅日 b/c 产出（列级敏感性 + 版本 B 内部稿）保留为素材输入, 版本 B 稿结构被蓝图取代。
**当前裁定（2026-08-29 审阅日）**: 论文 **b+c 并行、a 暂缓**（b 仅列级探索性敏感性分析，不覆盖冻结表级 E3；c 仅内部投稿稿准备，禁止对外，待用户终审）；清理仅限 `_tmp` / bundles / side staging / `side_audit_inbound_0822` 四类可恢复处置；/m1 保留 13/13 功能证据，但“快路体验通过”未签，须先核对约 50s 延迟与命名；Docker/bge/DAIR/暂缓区继续冻结。不启动研究跑批。本行取代下列 03:2x 历史收口摘要中的“待裁/待验收”状态。
**本轮执行结果（12:15）**: b 已完成 40 列探索性重判（零端点），c 已形成内部投稿草稿；四类获批清理件均经落点/完整性验证后移入日期化隔离区（可恢复、未删除）；/m1 三问确认均为 45s 验证链等待后回落直连，故证据改称“回落问答”，真实提速与是否改 UI 命名仍待用户裁定。
守护模式（静待用户审阅: a/b/c 裁定 / 清理候选批 / walkthrough 验收; 不启动新队列）。**08-29 元复审修复两件**: ① B-2 写保护补实现（元复审实查发现首轮守卫未落码: 报告声称≠代码事实 → 重开; 实现位点 vgmc_exp1.py:246/:551 + 回归测试 3/3, findings B-2 状态已改"已修复（二次）"）② findings blocking 计数 2→3 顺修; 教训入账（抽验手册同步: 修复验证必查实现位点 / 实测域全域复算不可抽样）; HANDOFF.md 08-29 冻结快照节入库。**08-29 全盘复审收口（五路锚定防护自审, 边界 ea993d8）**: 3 blocking 全修复审过——① 对抗臂机制归因更正（拦截在 gain 维非 ε 维, 三处措辞已正, P3 PASS 判定不动）② 射表覆写溯源断裂修复（确定性重建+写保护+快照留档+判定重放不变）③ gain 实测域二次更正 [−0.25,1.0]; Loop C --bare 修复后首次成功交付（对抗臂/D1/T2 三对象审计, 数字链三层全对齐）; sync_skills --check 77 件两端一致; 详见 2026-08-29_full_review_findings.md。**08-29 凌晨 B 扩碰撞窗收口**: E1/E2 PASS（伤害首触 H −0.0057 / 门控零伤害 / 门拒 5/5）, **E3 未触发（ΔV(ACC)=0.05 但 CI 含 0, 15 碰撞表功效不足）→ 版本 B→A 不切换, 版本 B 维持（判据冻结不溯及）**; 骨架 v2.5 授权写入（贡献重组 2+1 + 生产边界声明）; 伴生问题（匹配竞争天花板）升一等公民入账方法章/盲锥章/骨架; 相关工作待复核清零; A15 奖励再设计稿待窗。下一步候选（另行裁定）: a 语料再扩突破 15 对天花板 / b 逐列配对重判现有数据（零新跑批）/ c 版本 B 叙事投稿。**08-29 凌晨科研线队列收口（findings 双向变现）**: Phase 1 三件（逐体制正确性回填: L3 H null 非真 null + acc_meas 同一语料底座内跨臂恒定实锤（08-29 审计措辞更正） / ΔV 配对 bootstrap CI 固化进 judge / oracle headroom: 碰撞正确性天花板 0.597 列竞争伴生问题）+ 相关工作 v2（Voyager/MemGPT/mutation score 三增量）+ 写作四件（盲锥章盲集族形式化五定义 / 方法章变量对位+命题 1 收紧 / 贡献重组 2+1+生产边界声明 / 定位双版本当前=版本 B）+ paper-review-check 自审（2 blocking 全修: 定义 5 口径不一致 / gain 域编造）。**08-29 凌晨并行层收口**: ① 脚本化 walkthrough 13/13 全过（证据在案, 用户只留主观验收）② 论文线三件（相关工作草稿+盲锥章 v1+小 A 方法章, 零端点）③ B 扩碰撞设计稿入库（危害梯度 ρ 机制, 窗待排）④ 治理制度化生效（漂移扫描首跑 10 命中登记 + 收口清单 + 03:30 cron + Loop C 扩围）⑤ Loop C 审计首派挂起重派（运转状态待察）。前序: **对抗建议器臂窗已执行**（08-28 23:37-23:53, #13）——**P3 PASS 门拒对抗建议 100%**（机制: gain 维拦截, 与 C0/C1 同型; ε 维未激活——08-29 审计更正）; ① 字面失败（ΔH 正向, 伤害未显形 = fix↔meas 表头共享不足）; 三臂终值与 C0/C1 逐位同值（可靠性轴只移水平再证）; T2 对抗臂坐标已回填（主图右端补上）。**判定件 B 序不变**: 带本次危害梯度发现出扩容设计稿（定向提高 fix↔meas 共享度）, 只出设计不执行。D1 /m1 三栏待用户五步 walkthrough 验收（口径 3 = localStorage 已拍）。晨间一页纸判定项（收集与判定分离, 夜间只记）:
① 段 A 碰撞体制: P3 null 未触发——两臂分离（H |差| 0.0057 临界 + ACC 门控 2 倍级, n=25 弱）→ 是否扩大碰撞语料确认分离待拍
② 段 D 基线: fewshot/mem0/awm 全部与 no-gate 不可分（ΔH 逐位 0）→ 预注册结论"替代记忆机制无增量, VGRM 显式规则库充分"入账
③ C4 首批: OCR 形近视觉判别 61.5% = 匹配层盲锥锥尖的跨层互补; 错位噪声 33% 治理为后续批次前置
④ K2/小 B 章草稿 v0 路径待用户过目（侧线机械对账清单在案, b7224e9）
⑤ Round 3 已收口执行（用户勾选, 73ac314）: D1 采纳（经验命题 1a: C=0→ΔV=0; 臂间差=碰撞暴露×单次碰撞危害）/ D2 批准（对抗建议器臂设计全稿在案 2026-08-28_adversarial_suggester_arm_design.md, 预算主案 ~120-180 次 :8004, 执行窗待排, 依赖序=段 A 碰撞语料已就位）/ D3 采纳（两次 null 叙事）/ D4 勾 1-5 全（骨架 → v2.4, 项 6 条件条款保留）; 两处更正入账（对称毒性→对称抑制 / L0 行=跨运行比较含抖动）
⑥ **判定件已拍（08-29）: A 先 B 后**——A = 对抗建议器臂窗 **08-29 晚开窗**（#13, 三预测照稿, 主案 ~120-180 次 :8004 ≈15min, 降级案双臂 1.0）; B = 扩碰撞复跑带 A 危害梯度再定扩容设计（同窗顺延或后晚）; 理由 = 同底座剂量响应链可比性（A 解锁 A15/DPO 前置）
⑦ /m1 验收: 用户五步 walkthrough 自走（时间轴/刷新持久化/QA 五步条/建议映射 tab/快路回归）, 与 A 窗汇报一并看 08-29 晚; 口径 3 = 接受 localStorage（服务端持久化 = 触发项 D13）
⑧ 审阅日最终复验（12:37）: walkthrough 13/13 功能断言通过；QA 五步条完成耗时 48.7s，三条原称“快路”的回落问答分别 48.6/50.6/49.7s（服务端四问均为 `route=direct, fell_back=true`），故仅保留功能通过，不签“快路体验通过”；验收证据先如实改名，真实提速菜单待裁

## W1 零端点合并窗结果（2026-08-30, T1/T2/T6, Loop A）

- 三段全 PASS（卡 TASK-20260830-01）: T1 E1.1-E1.4 / T2 E2.1-E2.3 / T6 E5.1-E5.2, 复现门 G1-G4 全过。工件 `logs/graph/eval/{t1_eval_baseline_comparison,t2_visibility_sensitivity,t6_matching_competition}.json` + 收口汇报 `logs/graph/eval/w1_window_report.md`; commit cca4144 / 1333cae+670dc44 / 0d337b9 / fix 7eaef88 / 汇报 86d4d55。
- 门限实测: G1 臂 A 逐 mutant root_scores 最大误差 0.0、臂 B 75/95 表级与注入级零失配; G2 PSO 均值分离度 1.4326（冻结 1.432574, 误差 2.6e-05）/ 最差 M7 0.0926; G3 S 档 75/95 + by_type 六类计数误差 0; G4 贪心臂 75/95 + oracle plain 0.952381 / overlay 0.597015（误差 0.0）。
- 结论向（喂 T7 写作）: T1 分层协议在检出维度无优势（臂 A 3/9 vs E1.2 4/9; 臂 B 表级 0.2105 vs 0.7895）而定位率 1.0 vs 0.0 → 设计稿 §1 预注册降级表述评估已触发（本窗只产证据）; T2 ocr_similar 五 γ 点全盲成立、γ 字面极差判据在 0.7/0.9 不成立、S′ 档 8/13 未达（构造偏差, 机制零反例: 距离 2 的 8/8 全可见, 距离 1 的 5/5 全吸收）; T6 落分支 a（贪心 95/95 已全局最优 + 22/22 吸收无更高分竞争列）→ C1 可见性谱不需"匹配器次优性"注记, 效度威胁改写为打分层污染。
- 红线自查五条全 PASS: 甲方数据零进入 / 零端点（socket 护栏 + 固定清单扫描 + 卡 P5 grep 零命中）/ 冻结件零改动（五件 md5 复核 OK, 开窗基线→收口 diff 仅本卡路径）/ 逐路径 add 无 amend / T3-T5 与 :8006 零触碰。
- 治理教训（汇报 §6.6）: 脚本 `self_source_scan()` 原以 `research/` 目录 glob 枚举扫描集且该字段入 payload 摘要 → 下一个 `paper_t*.py` 落盘即令本窗工件不可复现（实跑已见 T1/T2 摘要漂移）。修法 = 钉死 `SCAN_MANIFEST`（7eaef88）+ 探针实验回归。后续零端点窗照抄该模板并保留"收口 = 重跑比摘要"这道门; T3/T5 派卡时写入脚本模板。

## W2 :8004 合并窗结果（2026-08-30, E1.5/E1.6/T4, Loop A）

- 三段全 PASS（卡 TASK-20260830-04）: E1.5 Full-Judge 120/120 单元零失败未 BLOCKED / E1.6 三 seed 臂 B / T4 五组对照+minimax+预算梯度。单工件 `logs/graph/eval/t4_pso_fair_comparison.json`（payload_sha256 cb00e8af…1a870, gates 全 PASS, 双跑一致）+ 汇报 `logs/graph/eval/w2_window_report.md`。
- 红线实测: `:8004` 调用 **122/200**（账本悲观占用, 重跑缓存命中不增计数）; 端点观测按作用域分层: 原始实跑 `ports=[8004]`（逐字输出入耐久件 `w2_endpoint_evidence_excerpt.txt` + 跨作用域并集 `union_all_scoped_ports=[8004]`）, 缓存复算 `ports=[]` 属正常（不建连接）; :8006/:8008/:5050 零触碰且经**零调用护栏自证**（正向可记录 / 受保护端口 syscall 前拦截 / 对端零收包 / 预算不变）; 甲方标识终工件全 JSON 零命中; 冻结五件 md5 OK（未触发 REQUEST_UNFREEZE）; 逐路径 add 无 amend。
- C2/C3 裁定: **C2「≥3 seeds CI 可算」PASS**（三 seed CI 非退化 + 合并 CI [0.727,0.8227]; E1.2_flat 0.7895/0.7835/0.7556 全落预测带）。**C3 PARTIAL → 降级条款已触发**: PSO 优于 equal/expert/random30 三组, 但与 greedy 坐标上升**完全同值 1.432574 且贵 114.2× 评估次数**（67 vs 7650）; 另 PSO 最差 mutant 0.0926 < expert 0.2083（均值增益以最差维退化）→ 论文须按「自动搜索省专家调参」而非「判别力上限」陈述 C3。冻结复现门 abs_err=0.0 且权重逐维全等。
- Full-Judge vs 确定性映射（E1.5, 判分均值 1.3053 vs 映射 1.2526, 检出集两口径同 3/9）三机制入账: F_W2_1 M7 判分分离度**恰为 0**（NF 工件 9 条中 8 条 number_claims=0, 注入只落在聚合 n_fail → item 层不可观测 = 突变体保真度问题, 非裁判能力）; F_W2_2 裁判对空证据给 0 而确定性给中性 missing_score=5（M8 敏感度翻倍, 政策差异）; F_W2_3 硬闸门 `overall_status_binary` 被裁判部分分软化（M1 1.8523 vs 2.6428, M9 反向）。一致性 max|Δ|=0.5 **恰在边界**且恰等于 0-10 整数叶分的分辨率下限（F_W2_4）→ 该判据在此量纲无区分力。
- 预算梯度: keep_rate 在 25/50/75/100%（B=5/10/14/19）恒 1.0 **饱和**, 「单调不降」平凡成立但不可用作结论; 适应度序列非单调（B=10 0.0368 反劣于 B=5 0.0316）。Pareto 双轴去重后仅 2 点, expert/equal 被 minimax 解支配。
- 明日一页纸判定项（五项, 详见汇报 §7）: 叶分量纲是否改连续 / M7 是否重设计为在有数值主张条目注入 / C3 降级条款是否采纳并补 greedy 为标配对照组 / 题集预算轴是否换判据 / E1.5 是否追加「裁判评原始答案」第二形态（需另批预算, 本窗余量 78 次不足 16×4）。
- Loop A 纪律注记: 本窗执行期间 Loop B 因 4 个在制未跟踪脚本判 `git_alignment=FAIL`（dirty 6>白名单 5）, 其余 8 项检查全 PASS; 入库后 dirty 归零待下周期翻回。`logs/graph/dispatch_log.md` 的 daemon FLIP 行不并入本工作 commit。

## D1 零端点审计窗结果（2026-08-31, TASK-20260831-01, Loop A）

- 全门 PASS: G1-G7 + 预注册 P1-P6 逐条成立, **零改判零 BLOCKED**, exit 0。工件 `logs/graph/eval/d1_mutant_validity_audit.json`（payload_sha256 d7d0e0e0a3…7f28b3, 跨两次实跑逐字节稳定）+ 报告 `docs/experiments/2026-08-31_d1_audit_report.md`（SUMMARY-GUARD 收据 27 claim, check 过）; commit 285a93d。
- 三分类底表（喂 D2/D3/D4）: 118 注入 = **H 85 / E 7 / HI 26**（95 表）, 逐类锚点检出 36/12/19/**0**/13/5 与 T2 冻结同值; E 集合与 T2 `e2_2` 集合差 ∅（alias 4 + prefix 3 + mixed_lang 0）且 7 条全 γ 网格不可见; ocr_similar 13/13 ∈ HI（tier 1 编辑距离容差静默接回, 映射目标 100% 不变）; HI 机制分层 = 吸收静默 15 + 阈值稀释 11（两口径并行入账: 严格吸收 22 = E 7 + HI 15, 锚点未检出 33 = E 7 + HI 26）。
- 突变体 MO/MU = **8/1**: 唯一 MU = `M7_nf_fail_3`（4 处原子变化全落 `n_fail` 聚合 + `results[*].pass` 派生标签; 承载字段 number_claims/ungrounded 9 item 零移动 → 判分分离度 0.0000 vs 映射 0.2083）。**M7 原样保留零替代（J2）**, 未重设计、未改判其既有结论。
- 方法学注记（供后续零端点窗沿用）: G6 硬门从「逐行字面量」改为 **AST 级 import/call 检索**（任务卡 P4 证伪口径 = 不导入任何 http 客户端）, 字面量降为披露层——原逐行门把生产匹配器 `m1_statement_parser.py` 的合法 OCR/VLM helper（19 处）与脚本自身中文注释「不调 :8004」误判为违规。作用域分层沿用 T2 `SCAN_MANIFEST` 先例; 「只调用纯文本匹配 API」不靠嘴说 = socket 封死 + 主动试连三探针全拦 + `MATCHER_APIS_CALLED` hasattr 断言 + 检索器正/负控（造假违规样例必命中, 不放水）。
- 红线自查: 零端点（ports=[] / model_calls=0 / 预算 0）✓; 冻结与活工件前后 sha256 全等, 突变体副本落 `/tmp/d1_mutant_scratch` ✓; 甲方标识终工件与报告零命中（证据只用 `row_NN`/`item_NN` 位置别名, uid 为 UUID）✓; 判据冻结不溯及 ✓; 逐路径 add 无 `-A`/无 amend ✓。
- 质量基线: pytest **402 passed / 13 skipped**; docs_lint PASS(0/0); summary-guard check exit 0; governance_drift_scan 15 命中全为前序存量（新登记 0, 无本卡路径）。
- 归主线程（收集与判定分离）: C1「注入有效性」基础层的论文含义判定待 autopsy; D1 底表已冻结可作 D2（跨匹配器）/D3（matched-specificity）输入。

## D2 阶段 A 跨匹配器窗结果（2026-08-31, TASK-20260831-D2, Loop A, 零端点）

- 门态: **G0/G3/G4/G5/G6 PASS + G1 FAIL** → `all_pass=false`, 脚本 exit 1（= 卡设计语义「任一门失败上报, 不静默处置」, 非管线故障）。工件 `logs/graph/eval/d2_cross_matcher_det.json`（payload_sha256 caf1e3bd…0c9558, 跨两次实跑逐字节稳定）+ 报告 `docs/experiments/2026-08-31_d2_cross_matcher_phase_a.md`（SUMMARY-GUARD 收据 49 claim, check 过）。
- **方向性结果已触发（τ<0.8）**: 按 `#D2-DIRECTIONAL-TRIGGER` 记账后立即上报, 不等 autopsy 排期。P-1 两半句拆开看 = ocr_similar 全盲存续 **成立**（四件皆 0/13, 任意 γ 可见数恒 0）; 谱排序 τ≥0.8 **不成立**（归一化列 τ_min=0.733333 @ γ=0.3, 独立复算同值）→ R3 降级条款按预注册自动生效入报告, 零改判零阈值回调。
- 四件谱（打分×分配两轴分解; 唯一变动 = date_variant 锚点 0.7059→0.4118, 其余五类四件逐字不动）: greedy_prod 85/7/26 τ1.0 / greedy_norm **80/7/31 τ0.733** / hung_prod 85/7/26 τ1.0 / hung_norm 80/7/31 τ0.733（补充列, 不入预注册判定）。G0 复现门 = 生产件 118 注入 × 6 字段零失配 → 跨件分母可信。
- **轴归因**: 分配轴（贪心→Hungarian）零翻转 τ=1.0 → 谱对分配算法不敏感; 打分轴（绝对 ed≤1 → 相对 ed/max_len≤0.20）5 翻转 → 谱对打分口径敏感。τ 失败由打分轴**单轴**驱动。
- **翻转毒性（关键, 交 autopsy 判读）**: 5/5 为良性正确吸收（漂移表头映射到**正确** canonical 字段 + keyset 不变）, 且 5/5 只因类型不在冻结 `EQUIV_TYPES` 内未计入 E → **谱形改变幅度由 E/HI 类型闸门驱动, 非新增危害驱动**（`visibility_gained_HI_to_H=0`, 无一例转可见）。R3 降级表述第一半句「盲区位置匹配器相关」本窗证据**不支持**（全盲集合四件恒等 = {ocr_similar}）, 第二半句支持。
- DR-3 迁移矩阵: 33 吸收注入（E7+HI26）× 3 预注册列 = 99 格无缺格（含补充列 132 格）, 矩阵内**零翻转** = D1 盲区跨匹配器单调保持。P-3 等价 7 条四件零翻转。HI 机制构成随件变化: 生产 silent15/dilution11 → 归一化 **silent21**/dilution10（供 D3 救援先验）。
- 方法学注记（自证护栏缺陷, 本窗实修）: 初版把**护栏自证试连**的端口记进 `ports_touched` → 自证反噬误判 G4 FAIL（[8004]）。修法 = 语义分离: `ports_touched` 只记实际建立的出站连接（socket 封死 → 恒空）, 被拦试连单列 `socket_attempts_blocked_disclosure` 逐事件披露 + 退出时护栏完整性复核 + 自证来源外尝试必须为零 → **判据强度净增非放宽**（与 W2 36ab25f「ports_touched 声明≠存储」同族病灶）。教训二: 现场取证一次性脚本 `!='H'==False` 链式比较恒假吃掉统计（同坑第 2 次, 是否上机械强制归治理线）。
- 阶段 B（bge-m3 嵌入件）**已同会话续跑交付**（见下节「D2 阶段 B」; 本条原记「本跑未产出」为阶段 A 收口时点事实, 现由阶段 B 补完, 判据零改动）。阶段 A = 本窗绿态下限已达成。
- 红线自查: 零端点（ports=[] / model_calls=0 / 全程未用 :8006 / J7 窗未开）✓; 判据冻结零改动 ✓; D1 底表 + drift 三件 + T2 + T6 前后 sha 全等, 冻结节点零改动 ✓; 甲方标识终工件与报告零命中（逐注入只落 uid+列号）✓; 逐路径 add 无 `-A` 无 amend ✓。
- 质量基线: pytest **402 passed / 13 skipped**（零回归）; docs_lint **PASS 0/0**; summary-guard check exit 0; governance_drift_scan 15 hits / **registered 0**（新两文件零漂移命中）。
- 归主线程（收集与判定分离）: ① τ 失配的论文落笔（R3 两半句一支持一不支持, 如何改写）待 D2 autopsy; ② 「E/HI 类型闸门驱动谱形改变」是否上升为对 D1 三分类定义的方法学主张（涉冻结设计稿 §2）; ③ 阶段 B 已产出（独立工件 + 独立报告）→ D2 两阶段齐, 本窗可收口。

## D2 阶段 B 跨匹配器窗结果（2026-08-31, TASK-20260831-D2, Loop A, 零端点）

- 嵌入两件事（bge-m3 余弦打分 × 贪心/Hungarian 分配）一次跑通: **全门 PASS**（G0/G1/G3/G4/G5/G6, `all_pass=true`, exit 0）。工件 `logs/graph/eval/d2_cross_matcher_embed.json`（独立件, payload_sha256 `299ab1c7acfc…1f950`, **双跑 payload 逐字节等**（原始差异仅 `.meta.generated`）+ 报告 `docs/experiments/2026-08-31_d2_cross_matcher_phase_b.md`（SUMMARY-GUARD 收据 92 claim, check 过）; 阶段 A 报告以**文末附节**衔接（既有正文零改动）。
- **P-2 按预注册不判过判**: 工件 `prereg_predicates.P2_embedding_verdict = none`, `no_pass_fail_adjudicated = true`; 本窗只产证据。
- **打分基替换的谱塌降**: H/E/HI = 生产 85/7/26 → greedy_embedding **23/57/38** → hungarian_embedding **19/66/33**; 锚点谱仅 date_variant 保持（0.7059→0.3529, γ≥0.3 名列第 1）, mixed_lang 0.95→**0.05**（跨语种字段名被嵌入"读懂"）, prefix_noise 0.8125→0, unit_suffix 1.0→0.4/0。τ_min vs 生产 = **0.276026 / −0.298142**（γ≥0.5 两嵌入件名次趋同 τ 0.771517/0.833333）。
- **全盲存续 + 盲区集合扩张**: `ocr_similar` 13/13 在**六件事 / 两种打分基**下任意 γ 恒 0 可见（未被照亮）→ R3 第二半句获第二打分基支持; 全盲集合 = `{ocr_similar}` → `{+prefix_noise}` → `{+unit_suffix}`（单调扩张, 非平移）→ 第一半句须区分「盲区消失（否）」与「盲区范围随打分基移动（是）」两种读法。**方向性触发第二次入账, 按 `#D2-DIRECTIONAL-TRIGGER` 立即上报**。
- **迁移矩阵（33 × 3 列 = 99 格零缺格）**: 翻转 生产 0 / 嵌入两列各 **8**, 全部 `HI(threshold_dilution) → E`（7 alias_variant + 1 mixed_lang, 8/8 keyset 全等）, **0 例转为可见** ⇒ D1 盲区锚点下仍全盲, 翻转是"良性化改标"非新增危害; 严格吸收 22/33 → 30/33; HI 机制构成 silent 15/dilution 11 → 嵌入件 silent 31/dilution 7 与 silent 29/dilution 4（供 D3 救援先验）。P-3 等价 7 条同口径观察零翻转。
- **定标诚实入账（阈值先于打分冻结, 事后未回调）**: 阈值 = 生产 schema 286 个 `(standard, synonym)` 正控余弦 p05 = **0.5439**; 负控（286 跨字段对）p75 0.5568 > 阈值, margin p05(正)−p95(负) = **−0.13278** ⇒ 正负控重叠, 弱门控; 正控含 74/286（25.9%）`standard == synonym` 同串对（cos=1.0）抬高分布 —— 两条都入报告 §3, 不用调阈值救它。
- **零端点自证（本窗新增作用域 = 本地模型装载）**: `ports_touched=[]`、`model_service_calls=0` 与 `local_inference_batches=16 / local_encoded_texts=496` **分列**; 护栏**先于** `sentence_transformers` 导入与装载安装, 被拦事件 3 条 = 自证三探针全部 ⇒ **导入-装载-编码路径零出站尝试**; `device=cpu` 显式（不占 :8004 生产显存）, 离线 env 三件套 + `local_files_only`; :8006 零触碰 / J7 未开。
- 只读与红线: 阶段 A 工件**零覆写**（`phase_a_sha_unchanged=true`）, D1 底表 + drift 两件 + T2 + 阶段 A 件前后 sha 全等, 冻结节点零改动; 甲方标识零命中（uid+列号）; 逐路径 add / 无 `-A` / 无 amend / 不改写阶段 A commit。
- 质量基线: pytest **402 passed / 13 skipped**（零回归）; docs_lint **PASS 0/0**; summary-guard check exit 0（两件收据均复核）; governance_drift_scan 结果见收口汇报。
- 归主线程（收集与判定分离）: ① 是否把嵌入族纳入 R3 匹配器集（P-2 探索性 ⇒ 纳入即改判据口径, 属主张层）; ② 弱阈值（负控重叠 + 同串对）是打分基性质还是短表头域性质 → D3 若引嵌入臂需先定标尺; ③ D2 两阶段齐, autopsy 后排 D3。
## 研究窗口结果（08-27 夜-08-28, 窗口合并卡）
- 段 C bandit v0 replay: 42 金标 × 六格, TS 4 决策点全 R=1; **六格 direct 全 1.0 同分（可靠体制无分辨空间; json direct_best 为字典序 tie-break 不读作信号）**; 零端点; 工件 bandit_gate_v0_eval.json
- 段 A 扩语料碰撞（#VGMC-COLLISION-WINDOW 23:38-23:51）: 移植列 67/37 表; C0 可靠/C1 碰撞+force; P1 PASS（弱, D 同值）/ P2 PASS（vacuous）/ **P3 未触发**（H |差| 0.0057 两体制同值 + ACC C0 0.28 vs 0.12）; H 对噪声逐位不变, ACC 为敏感量; ε 维首次实质激活
- 段 B C4 探针（#C4-VISUAL-PROBE-WINDOW）: 95 表 PIL 渲染题库（1.8MB 入库）+ Qwen3-VL-8B :8007 用毕即停; 视觉判别谱: ocr_similar 61.5%（5 严格+3 包含）/ date 23.5% / 余类 ≤12.5%; 错位 39/118
- 段 D 基线窗（#BASELINE-WINDOW 19:58-20:20, Loop A 异常期主线程直跑后恢复）: 三基线 ΔH 逐位 0, 记忆正常累积（29/32 条）而终值不动; 效度注记（H=覆盖度, 单 seed）
- K2 章: 2026-08-27_blind_cone_chapter_draft_v0.md（92 行, 数字全溯源, judge 零引用, §5.3.3 口径注记携带）

## 导师包终态（08-26 凌晨冲刺后）
- docs/31 v2 md+docx: judge 四维 08-26 重测实测入文（4.94/5.0/5.0/5.0, :8004 口径, 零 unusable）; 黑话零命中; sha256 见 send_checklist
- demo_v3.mp4: 186.03s/1080p30/h264+aac; 五门全过; 呈递清单 2026-08-25_send_checklist.md

## 规则裁定（一页纸 v3 + Round 3 增量）
- 0 过闸(261 尝试) / A: 3.1%<10% 不抬超时 CLOSED 走结构诊断 / B: steps p50=4 维持 T1 /
  C: FK 单件窗等批 / D: PSO 首批落盘+续跑 / E: 积压维持 / F: 当夜不开 :5050 窗
- 挂起: F-J3 孤儿治理提案 / 减 step 组合拳 / FK 窗口时机; Round 3 更正: D2 已勾选=对抗臂设计在案（执行窗待排, 明晨判定件 A）/ D4 已执行（73ac314, 骨架 v2.4）
- 侧线代圈 08-26 晚（用户授权）: F-J3 圈 b 先行 / 组合拳立主线本周冻结让路论文 / FK 缓办合并激活

## B4（两列口径 尝试/完成 全名）
- 池修复后段 3929: 261/8=3.1%（canary 题型代表性注记维持）; 段 3429: 761/62=8.1%（含池病污染不作数）

## 服务（08-29 审阅日守护态；运行态以实测为准）
- :5050 UP (route=on timeout=45) / :8004/:8006/:8008 UP / :8007 DOWN（C4 探针用毕即停确认）/ PG UP (GUC+pre_ping); kiosk 关闭
- Loop A 已恢复（用户 08-28 通报, 前条 token plan 异常作废）; Loop C 已恢复（派发必须 `claude --bare`）; Loop B 30min 周期，agent watchdog 完成率体制波动为已知症状，只记账不处置

## 质量基线
- HEAD 收口验证: pytest **402 passed / 13 skipped**; docs_lint **0 fail / 0 warn**
- Loop B 最新波动周期仅 agent_watchdog FAIL，其余冻结节点/pytest/API anchors/QA canary/git alignment/docs_lint/model topology/PG pool checks PASS；维持“波动只记账”口径
- eval 08-26 01:0x: 16/16 / NF 0/9 / judge 4.94-5.0

## D2 收口（09-01, autopsy 停一次）
- 窗口: TASK-20260831-D2, Loop A（GB10）, 零端点。首跑令牌耗尽改期 #1 → R2 两阶段: 阶段 A 确定性三件（7b49fb3）+ 阶段 B bge-m3 嵌入（f0b3a89）; 观察器 00:20 SESSION_ENDED 自删; 三方对齐 11df397（GB10 分叉已合）。
- τ 裁定 b: 门失败属实（归一化族 τ_min=0.7333<0.8, 平均名次+tau-b 口径）; 0.8286 撤销销账（教训台账第 4 次, 守卫缺口登记 docs/29 A18）。
- R3 降级条款适用（09-01 用户裁定 + Claim Set v2 适用注记）: 半句 A 不入论文（确定性族盲集恒 [ocr_similar] 交集=并集）; 半句 B 成立; 打分轴敏感性入边界条件。阶段 B 补充: 盲集单调扩张 {ocr}→{ocr,prefix}→{ocr,prefix,unit}（盲区消失=否/范围移动=是）, ocr 13/13 全盲跨打分基存续; 适用域圈选待 §5-①。
- 抽验: 阶段 B 12/12 全 PASS（research/paper_d2_phase_b_spotcheck_recompute.py → logs/graph/eval/d2_phase_b_spotcheck_recompute.json）; 阶段 A 4/5 唯一 FAIL=τ 口径分歧, 裁定 b 后自洽。
- 判定请求 ×2: ① R3 半句 A 适用域/盲集扩张表述（推荐 a）; ② D3 嵌入臂弱门控定标先行与否（推荐 a）。
- 红线: 零端点 / :8006 零触碰 / J7 未开 / 冻结件 sha 全等 / 判据冻结不溯及 / 甲方标识零命中 / 零对外。

## D3 阶段 A matched-FPR 窗结果（2026-09-02, TASK-20260901-D3, Loop A, 零端点）

- 窗口: 卡 + 加编 S-1..S-8（专家第 2 轮落地）, 阶段 A 零端点重派交付。全门 **PASS**（`gates.all_pass=true`, G-1/G-2 + E-1..E-4 + S-1..S-8 + R1 全 true, G-3 N/A=阶段 A 不开端点窗; 脚本 `research/paper_d3_matched_fpr_stage_a.py` 单跑 33.6s）。工件 `logs/graph/eval/d3_matched_fpr_stage_a.json`（payload_sha256 `61e6c6dd…`, 文件 sha `3318ac17…`）+ 报告 `docs/experiments/2026-09-01_d3_matched_fpr_stage_a.md`（九节 + SUMMARY-GUARD 收据 15 claim, check 过）。
- **卡 §4 pivot 触发（无可定标空间, 按预注册分支如实报不硬造阈值）**: 对比型分数在 **2382** 张可用 clean 表上恒 0（枚举 n_clean 2384, 2 张缺 canonical; 自导出 canonical ⇒ h_orig≡1）⇒ 两协议 `FPR(θ)=0 ∀θ>0`。两条绝对通道亦不可定标: **Ch-1** 生产 schema 覆盖率在 2476 表上恒 0（英文 TAT-DQA 表头 vs 中文对账单 schema, 域不相交, AUC 0.5 无信号）/ **Ch-2** 自身撞车率非退化但 **AUC 0.248411 < 0.5 = 反判别**。改报「零误报观测 0/2382 + 精确二项 CI [0, 0.001547] + 检出率原始比较 + 效度注记」; Ch-1/Ch-2 入工件 `prereg.fp_channel_taxonomy` 明确标 **observations, no new criterion**。
- **主结论: matched-FPR 检出差 = 0 是恒等式不是"没测出差异"**。剪枝后 `parse` 树只剩一个随输入变化的叶 ⇒ root(h)=6.25+3.75h, 层位降幅 ≡ (3/8)·扁平 drop10（严格正仿射像, 同一条 ROC）。证据: Spearman ρ=1.0 / 斜率偏离 ≤9e-08（1e-6 量化抖动）/ 2000 次**逐 replicate 重定标**表簇 bootstrap 非零 replicate **0/2000**, 差 CI **[0,0]**。⇒ **W2 的 0.7895 vs 0.2105 差 = 阈值摆放（ΔH≥0.2 vs ≥0.5333）, 非协议判别力**。
- **A1 = E-1 三态之 (b) → 嵌入臂降为敏感性分析**（`embedding_citation_decision` 由结果常量映射, 非事后解释）。本地 bge-m3 重编码**逐位复现** D2-B 存盘正负控分布（自检门）后剔除 74 条 `standard==synonym`（cos≡1.0）同串对: p05 **反而恶化** 0.5439→0.5323, margin −0.13278→**−0.14433**（同串对污染假设**证伪且方向相反**）; 上移 p10/p15 收回 −0.106396/−0.081916 且过负控 p75, 但 margin 始终 ≤0 ⇒ 判 (b)。弱门控成因 = 短表头域正负控真实重叠, 非自配对。
- **A3 救援 11/11 全确定性救援**（θ 再定标 5 例, 最小正降幅 drop10=1.428571 + 表级聚合 8 例, 重叠 2, 未救 0）; S-6 出身措辞照加编。嵌入臂 D2-B 的 8 例 HI→E **是标签损失非救援**（marginal_dH≡0, 把有害改判为无害）, 与 A1 判 (b) 自洽。
- **S-2/S-3/S-4/S-7 全项落实**: 分母 H∪HI=**111**（E=7 excluded）, 三行分列 = observable **90/0.810811**（CI [0.725461,0.878907]）/ invisible **21**（15 严格吸收 + 6 零稀释）; 工作点 θ*=**1.428571**（注入级）/ 1.666667（表级, 88 张含害表 TPR 0.886364）; **α=0.05 与 0.10 选出同一 θ***（预算从不咬合 ⇒ S-5 自动切换规则实测无需触发）; 定位双指标 conditional 与 end-to-end 同报且 **均 1.0**, mean_blamed_cols=1.0 ⇒ 零误归属, **定位轴在本通道不携带判别信息**; 成本轴 model calls 两臂恒 0, 规则评估 `map_headers` 7549 / 层位额外 `aggregate` 4764, latency 按 S-4 降次要未报; S-7 primary protocol×type = `degenerate_identically_zero`, 三组预设对比 c1 OCR 0/13 vs 非 OCR 90/98、c2 吸收 0/15 vs 稀释 5/11、c3 等价 0/7（validity audit 通过: 已知等价在 θ* 下零误判）。5 折表簇交叉拟合各折 θ 各异（1.6667/1.6667/1.4286/2.0/1.6667）= 定标确为逐折重做, 各折协议差仍全 0。
- [09-06 更正注记 | harness 审计 F06+F01 受理, 只增不改, 不溯及]: 上行「定位双指标 conditional 与 end-to-end 同报且**均 1.0**」系摘要误抄——正确口径 = conditional P(correct|detected) = **1.0** / end-to-end P(detected∧localized|harmful) = **0.810811**（= 90/111, 因检出即全对故数值同 TPR）; 绑定工件字段 `payload.a4_matched_fpr.localization_S3.at_matched_theta`（阶段 A 报告 :167-173 与 JSON 一致, 误抄源 51cbed9e 之摘要层）。另（F01）: 上行 θ*=1.428571 之定标实现违反 clean-only 契约（`S1_calibration_only_clean=True` 自证失真: 阈值候选来自 harmful 分数谱 :844 / 按同批 TPR 择优 :851-853 / 评估折 harmful 入定标 :895-901 / 自证硬编码 :1383）; **协议差=0 结论不受影响**（仿射恒等对任意阈值成立, 独立结构支撑）; 凡引 θ*/绝对 TPR 处以阶段 A 报告 09-06 头部注记为定标契约更正指针; 定标契约版本化修复 = A5 卡（阶段 B 收口后排, 新旧版本分列）。
- **G-1 全绿含最强一项**: `frozen_counts_reproduced_from_recomputed_scores` —— 本窗独立重算分数复现 W2 seed42 **85/13/75/20** 逐数全等; D1 三分类 85/7/26 + HI 机制 15/11、D2 阶段 A 零翻转 + 稀释 11、D2-B 稀释 7/4 + 定标三数全复现。
- 两处实现缺陷（本窗自查修复, 报告 §7 记账; 修复前后 G-1 均 true ⇒ 判据零影响）: ① 列归因用叶位置而非输入位置; ② TPR 比对用四舍五入值致 fold 2 落到 1e-12 哨兵显示 θ=0（改 raw 口径后正常）。
- 红线自查: 阶段 A **零端点**（`ports_touched=[]` / `model_calls=0` / AST 作用域检索零 http 客户端; 本地 bge-m3 CPU 推理按 D2-B 先例作自证口径分列, 护栏先于模型装载）; 冻结件只读（含 D1/D2-A/D2-B/W2 工件 sha 前后全等）; 新预注册不动旧判据（R1-R4/D1-D2/W2 零改动）; 甲方标识零命中; 逐路径 add / 无 `-A` / 无 amend / J7 不开 / TAT-DQA 零触碰 / 零对外。
- 归主线程（收集与判定分离）: ① 阶段 B judge 重打分 28 调用清单待白天端点窗派发; ② 层位树第二变化叶（`parse.reconcile` 型, 可零端点分离两协议）需 Loop D 批准, 本窗未动冻结树; ③ **对 Claim Set v2 的影响必须上报**: 08-30 裁定 ①a「分层提供定位与诊断不主张检出优越」在本语料需限定 —— 匹配-FPR 下**检出与定位两轴均无差异**（单变化叶 ⇒ 仿射恒等）, "分层提供定位"在此通道亦无额外信息。详见 `memory/THREADS.md`。

## DR-4 D1 现行分类逐实例复核收口（2026-09-04, TASK-20260901-DR4, Loop A 改期 #1, 零端点）

- 窗口: 首跑（09-02 00:2x）分析段完成、报告段令牌耗尽（1,281,246）→ 本次**收口重派**范围严格限定
  （只读工件 + 确定性复跑 + 报告 + 收据 + 记账 + 提交）。四门全 PASS（`gates.all_pass=true`）+
  五预注册全 holds; 工件 `logs/graph/eval/dr4_d1_reclassification_review.json`
  （payload_sha256 `47adbe66…`, 文件 sha `7806b77b…`, 441,072 B）+ 脚本
  `research/paper_dr4_d1_reclassification_review.py` + 报告
  `docs/experiments/2026-09-04_dr4_d1_reclassification_review_report.md`（SUMMARY-GUARD 收据 53 claim, check 过）。
- **确定性复跑（本次唯一执行动作, 镜像法）**: 脚本 sha 快照含任务卡, 卡片 09-04 加编后原地重跑会改写冻结工件
  ⇒ 在 `/tmp/dr4_verify.*` 镜像布放加编前卡片（`790f67f` 版本, sha `85155fc7…`）双跑: 两次输出 `cmp` 逐字节相同,
  sha256 = 首跑工件 `7806b77b…`, exit 0, client hits `[]`; 仓库内工件与五件输入 sha 收口前后全等。
- **复核结果**: 118/118 逐实例 Step 1 oracle（C1 算子资格 ∧ C2 规范真值映射不变 ∧ C3 下游语义不变）
  = **oracle E 1 / H 117**; 现行分类复现 H85/E7/HI26 且逐条 118/118 与 D1 存储一致、E 集与 T2 冻结 7 uid 集合相等（G1 PASS）。
  交叉表 oracle|现行 = `E|H 1` / `H|E 7` / `H|H 84` / `H|HI 26`, **`E|E` 格为空**。
- **diff = 8 例（稳定 110）**: 7 例 E→H（`50e78448#2`/`5e60c056#0`/`b5aae4e9#0` 前缀噪声删除单位原子 `US$`/`£` ⇒ 首失 C1;
  `54c494f7#2`/`e9730ea3#2` amort 丢 ACCUMULATED、`73a817fc#1` dividend 丢 PAID、`e67f7bf2#4` cashflow 丢 FREE+PRE_SPECTRUM ⇒ 首失 C2）
  + 1 例 H→E（`3789d7da#1` `Revenues→sales`, 三条全过）。**HI→E = 0 例**（卡 §3 步骤 3 问句答零）;
  diff 8 例 C3 全部通过 ⇒ 复判机制集中在字段集内容变化（单位符号/限定语丢失）, 非表头歧义。
- **对下游**: D3 有害分母敏感性 111（现行）→ 117（oracle）, delta **+6**, `retroactive=false`（不溯及, D3 冻结产物不重算,
  下一轮 FPR/召回分母须显式声明口径）; 口径敏感性 = 严格 E 1 vs 宽松（限定语移出 C2）E 15, 逐实例一致 104/118（宽松仅披露不入分母）。
- 独立性自证: 阶段 1 冻结（`oracle_rows_sha256=4b3025ef…`）先于读任何 class/检测字段;
  禁读字段产物内零命中 + 生产匹配器未载入（`forbidden_*=[]`）。红线: 零端点（ports=[]/model_calls=0/试连 3 项全拦）/
  D1+T2 工件与报告只读 / 不溯及 / 判据冻结零改动 / 甲方标识零命中 / D3 工件域零写入 / 逐路径 add 无 `-A` 无 amend。
- 归主线程（收集与判定分离）: **「等价注入」作为鲁棒性正例的证据基础在本语料近乎不存在**（现行 7 条 E 全失守,
  oracle 仅认可纯同义别名 1 例）⇒ D1「E 集」口径、任何以 E 集为分子的表述、D4 等价类定义需 Loop D 判定;
  本窗只出更正记录不改写既有主张（见 `memory/THREADS.md` #DR4-CLOSEOUT）。
