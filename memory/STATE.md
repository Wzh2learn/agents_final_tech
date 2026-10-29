# Current State

> **2026-10-29 Paper E 最新修订**：[v4 内部审阅稿](../research/paper_e_agent_evidence_20261029/paper_e_review_revision_v4.md)、[修订核验](../research/paper_e_agent_evidence_20261029/V4_REVIEW_AND_CORRECTIONS.md)、[负责人自审](../research/paper_e_agent_evidence_20261029/RESEARCH_LEAD_SELF_REVIEW.md)。新增4次真实 OpenCode/Qwen 开发运行，8次模型 HTTP、31,054已记录事件tokens；采用一个已暴露迁移仓库的两个历史候选和两个事后选取的 SciFact 查询，静态字面合同与 Agent 均为2/2，未标注文档不能算负例。历史7/7测试本轮未重跑；这不是新独立验证、方法增益或投稿终稿。第二篇实验仍进行中，不提前写成完成。旧状态中若有 v3 为当前稿的说法，以本段 v4 为准。

> **2026-10-29 科研增量**：[Paper E 对标](../research/paper_e_deep_benchmark_20261029/PAPER_E_RESEARCH_BENCHMARK.md)将观测界限定为背景而非新定理；[隔离 Agent 探索](../research/paper_e_deep_benchmark_20261029/CONTAINER_AGENT_EXPLORATION_RETURN.md)六次物理尝试中后三次容器任务完成，已知事件总 tokens 29,329、前两次用量未知；两个合成病例仅展示粗略最终数值与读取轨迹的观测差异，不证明实际危害或一般性能。[第二篇 Agent 候选](../research/agent_frontier_portfolio_20261029/AGENT_FRONTIER_RESEARCH_PORTFOLIO.md)与 [SkillsBench 资格](../research/agent_frontier_portfolio_20261029/SKILLSBENCH_SOURCE_QUALIFICATION_AND_PLAN.md)均未建立方法效果，Partridge 为暴露的离线资格。

> **现役快照（2026-10-29，负责人复核）**：本段优先于下面保留的阶段历史。Paper E 的三案例 v3 是内部审阅稿，未投稿；六系统分析为事后探索，Holm 算术已独立重算，尚无独立数据确认或真实用户决策研究。最新材料见 [论文修订](../research/paper_e_manuscript_followup_20261028/V3_REVIEW_RETURN.md)、[实验](../research/paper_e_evidence_followup_20261028/RESULTS.md)、[投稿倒排](../research/paper_e_publication_route_20261028/PUBLICATION_PLAN_ZH.md)。第二篇仅为[相关工作筛选与候选](../research/paper_e_evidence_followup_20261028/SECOND_PAPER_RELATED_WORK_20261028.md)，不是已成立创新。会议可线下；IJCNN 与 EASE 不可按“先等 IJCNN 后再投 EASE”顺序衔接。2027 年 10 月送审，具体日和学校成果凭证待核。经用户确认，原阻挡合并的本机副本已保存在 `D:/Documents/Loop_D_assets/git_sync_backup_20261029`，带逐文件 SHA-256 清单；本机、GitHub、GB10 main 已接收论文集成分支。新研究与历史 worktree 状态须另核，不能以此次合并宣称所有工作树 clean。

以下为阶段历史，旧评分、路线与待办中如与本快照冲突，均不代表当前裁决。

> Updated: 2026-10-28（第二轮执行）| Scope: 三图源重导出与重渲染完成；D/T/M 卡已按复核更正；生成仍为 0
> 上一轮治理核验：`VERIFIED`；备份、三端对齐与工作区核验范围见治理报告，不替代本轮科研方法或投稿包验收。

## 当前任务

本轮（第四轮）完成精度与官方工具核验，并实测投稿可行性。

- 官方 `trec_eval 10.0-rc3` 已在 GB10 从源码编译并实际运行：18,690 个逐查询值（两个子集、5 系统、
  k=10/100）与自写实现一致，最大差 5.0e-05（官方四位小数打印的半个末位），1e-4 容差内 0 不一致。
- 精度修正：NFCorpus 并列序两种汇总为 0.30453945 / 0.30449093，差 0.0000485；全文不再写"严格为 0"。
  未校正=配对 bootstrap 区间，校正=Holm 调整的 sign-flip 置换 p 值，两者分列。
- IJCNN 2027 官方作者须知已核：6 页（至多 10 页，超页每页 $100）、双栏 10pt、双盲、远程预录须
  2027-04-12 前声明、无直播、AI 文本须致谢披露。
- 已生成匿名双栏投稿稿并实测渲染：**13 页**，超过免费上限 7 页、超过收费上限 3 页，
  **即付费也不能投 IJCNN**。要投它必须另写真正的 6 页精简稿，属内容重写，本轮未做。
- 主投改为 SN Computer Science（无页数上限）；IJCNN 仅在接受另写 6 页版时为备选；
  FLAIRS 需到场且页数同样超标。

C 只审过两案例快照 `08be0547`，此后全部无独立复审。模型生成仍 0/128、0/1,000,000 token。



BEIR评分与对照修正已由D在2e7cc0f8完成，负责人本地复核8项公式控制通过及保存的v1/v2指标差；并未重跑BEIR或官方二进制。下一阶段优先更正nDCG汇总差约0.000048525的四舍五入表述、尽可能进行官方评分器交叉验证、寻找更早的正式会议并完成实际会议稿与图1重设计；见[唯一指令](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。

负责人复核d79ba1a7后发现第三案例评分与官方合同不一致：nDCG将分级相关度二值化、MAP分母使用min(n_rel,k)；固定反例分别为1.0对官方公式约0.8597187、1.0对0.5。AB真阳性计数存在方向错误，官方排行榜/强基线/差异不可区分表述需重核。第三案例评分/对照已按后续回执修正、官方工具逐查询验证仍待做，前两案例不自动失效；D按[唯一指令](../docs/research/LOOP_D_RESEARCH_PROMPT.md)修正重算、审稿并继续投稿路线。

本轮（第三轮）新增第三案例并通过实测：以 BEIR 官方分发的 SciFact / NFCorpus 与官方指标定义，
审计"排行榜结论"而非模型。零模型生成（0/128 次、0/1,000,000 token）。

已证实：SciFact 10 对系统仅 3 对可分离（全部 BM25>TF-IDF），BM25 家族内部名次不可分离；
k=10 与 k=100 在两个子集上都改变排序；NFCorpus 36.5% 查询的 top-10 随并列序变化而总量只动
0.0002。审计把断言数从 15 降到 9/7，正确判"重复系统不可区分"、正确检出"退化系统更差"；
而只加 recall@100 的强简单基线会把 TF-IDF 排到第一，属误导性补充。

论文已扩为三案例（§3.6/§5.8，摘要/贡献/§1/§6/§7 同步），生产源升至 `paper_e_revision_v3.md`，
16 页重渲染；三图按类别 1202/601/601 dpi，图2/3 字号提到 7.5–9.7 pt，图1 仍 5.7 pt（结构限制）。
C 只审过两案例的 `08be0547`，此后全部无独立复审。

会议：未找到同时满足"更早+可投+正式论文集+远程+主题匹配"的选项。FLAIRS-40 更早但不支持远程，
IEEE VCC 2027 全虚拟但是通信领域，FG/VR 已排除。建议 IJCNN 2027 > FLAIRS-40（能到场）> SNCS。



Owner已要求增强Paper E的实证论证，并优先筛选更早、可远程展示的正式会议。现役指令：[LOOP_D_RESEARCH_PROMPT](../docs/research/LOOP_D_RESEARCH_PROMPT.md)。从公开评测独立验证与审计前后判断/纠错两方面推进，会议调研与稿件并行；结果尚未完成，Owner转发后执行。

已有两案例与正向观察：FinRank的已检查比较方向对tie规则稳定；针对三个阶段设计的检查点在216条受控变化中可区分阶段，但简单直接检查同样有效。新独立案例与真实决策收益尚未建立，不声称通用Agent方法成立。

D上一轮在4cc4290完成三图源重导出、14页重渲染和D/T/M卡更正；图内字号5.7–8.2pt仍需依据最终模板处理，C后修改未获新独立审阅。D/T/M五条仅开发，不是当前实验。主树123个未跟踪副本保留，集成worktree继续使用。

本Goal转发后授权限额内GB10本地评测，最多128物理生成尝试、100万输入+输出tokens（包含judge/失败/重试），训练、付费API、生产访问、A/C新增派发、外部投稿等不含在内。历史账本不重置，尚未转发和运行不得记为已授权/已用。

Phase A 复算确认：安全尾部适配后 copy 2/2、known edit 2/2；单位题没有可见 million/thousand 尺度，降为不可判定，唯一可修的引用题在 neutral/category/localization 下均 0/1。旧 generic adapter 的 `1)0→10` 语义污染反例已由 strict whole-JSON 和限定尾部规则阻止。详见 [Phase A 回执](../docs/governance/audit/loop_d_control_review/PHASE_A_RETURN.md)与[复算](../research/feedback_delivery_continuation_20261025_v1/PHASE_A_RECOMPUTE_V1.json)。

此前 P0/A/C 负结果继续保留开发身份。Phase B 的R/E是真实训练后的实现失败；ordinary续训、答案正确率和干净方法负结果未被建立，不是新来源确认或feedback-derived learning。Paper E 投稿包较成熟，渠道仍为条件建议，Owner尚未批准外部动作。送审为2027年10月，具体日未知。

| 用途 | 当前权威入口 |
|---|---|
| 当前方法实验 | [A回执](../research/word_scoring_new_family_20261027_v1/A_RETURN.md)、[C审阅](../research/word_scoring_new_family_20261027_v1/audits/C_JOINT_AUDIT.md)、[D收尾](../research/word_scoring_new_family_20261027_v1/D_CLOSEOUT_RETURN.md) |
| 修订算子诊断 | [REVISION_OPERATOR_RETURN](../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_DIAGNOSTIC_RETURN.md)、[CONTROL](../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_V2_CONTROL_RESCORED.json)、[MECHANISM](../research/feedback_delivery_continuation_20261025_v1/REVISION_OPERATOR_V3_MECHANISM.json) |
| Paper E 投稿路线 | [REVISION_NOTES_20261028](../research/word_scoring_new_family_20261027_v1/paper_e_word/D_REVISION_NOTES_20261028.md)、[SNCS_GUIDELINE_CHECK_20261028](../research/word_scoring_new_family_20261027_v1/paper_e_word/SNCS_GUIDELINE_CHECK_20261028.md)、[C_RESPONSE_20261028](../research/word_scoring_new_family_20261027_v1/paper_e_word/C_RESPONSE_AND_DISPOSITION_20261028.md)：会议优先；实验补强与更早会议调研尚待执行，图内字号与声明仍开放 |
| 当前科研基线与三张实验卡 | [RESEARCH_BASELINE_AND_REUSE_MAP](../research/research_baseline_governance_20261023/RESEARCH_BASELINE_AND_REUSE_MAP.md)；[GOVERNANCE_RETURN](../research/research_baseline_governance_20261023/GOVERNANCE_RETURN.md) |
| 唯一现役指令 | [LOOP_D_RESEARCH_PROMPT](../docs/research/LOOP_D_RESEARCH_PROMPT.md)：Owner转发后补强Paper E公开验证与审计前后对照，并筛选更早会议；A/C29/29不追加派发 |
| 事后有效性复核 | [POST_B_REVIEW](../docs/governance/audit/loop_d_control_review/PHASE_B_POST_RETURN_REVIEW.md)：主计数复算、有效父模型/合同与语义边界；本轮0科研生成/训练 |
| 最新科研回执 | [D_LOOP_RETURN_20261028](../research/word_scoring_new_family_20261027_v1/D_LOOP_RETURN_20261028.md)、[C_PAPER_E_V2_REVIEW](../research/word_scoring_new_family_20261027_v1/audits/C_PAPER_E_V2_REVIEW.md)、[DTM_DECISION_CARD](../research/word_scoring_new_family_20261027_v1/DTM_DECISION_CARD_20261028.md) |
| 新对话交接 | [D_CLOSEOUT_RETURN § 新对话交接](../research/word_scoring_new_family_20261027_v1/D_CLOSEOUT_RETURN.md)：最少必读、Git/工作区、预算与授权边界 |
| 本轮治理与 Git 实况 | [工作区治理报告](../docs/governance/2026-10-21_workspace_git_closeout.md) |
| 唯一科研导航 | [docs/research/README.md](../docs/research/README.md) |
| 当前方法账本 | [DIAGNOSTIC_SUMMARY](../research/word_scoring_new_family_20261027_v1/scoring_v3/results/DIAGNOSTIC_SUMMARY.json)：27次预留、24条raw、46,054 input+output、0训练；本轮新增0生成，仅对既有raw做分词分段测量([DTM_SEGMENT_SPLIT](../research/word_scoring_new_family_20261027_v1/validation/DTM_SEGMENT_SPLIT_20261028.json)) |
| 历史聚合记账 | [RESOURCE_LEDGER](../research/publication_thesis_goals_v1/RESOURCE_LEDGER.json)：历史阶段4,064 accounting attempts / 9,169,672 tokens，不含独立Phase B；B另记188物理生成、137,770—139,306生成tokens、2次训练/319,948训练tokens；340旧差额保留，不假称全局对账 |
| 历史 Portfolio 账本 | [COST_AND_CANDIDATES.json](../research/research_portfolio_v2/COST_AND_CANDIDATES.json)；历史独立账本不混算 |
| 未决事项 | [THREADS.md](THREADS.md) |

## 科学边界

- C1 / Paper E：`TEXT_AND_FIGURES_READY / DECLARATIONS_OPEN`。正文缺陷全部关闭并有确定性复现；三图已从源重导出，分辨率按图像类别达标、图内标题与脚注已移除。剩余只有声明占位与图内字号（5.7–8.2 pt，低于 8–12 pt 推荐值，需重排版面）。C 快照之后的全部修改均为 D 自验，未经新的独立复审。
- C2/C3新表族诊断：`SEVERE_BUDGET_CONFOUND / CARD_V2_CORRECTED`。旧24条分段支持严重输出预算混淆，**不分离**thinking 长度与合同长度；D4/T1/M0 是接口提取结果。参考字段为 `unit`（8/8 有值：percent 3、thousand 1、UNKNOWN 4），逐题核出 3 条标签冲突，可分析面板由 8 收缩到 5；预算重开为 27 物理请求 / 54,000 输入 / 13,824 输出 / 合计 67,824 token。typed UNKNOWN 冲突仍是静态缺陷，旧24条从未触发。D/T/M重跑未获本Goal授权。
- 以下 G2、G3 与旧第三研究点条目保留为历史边界和复用素材，不承担现役 C1/C2/C3 贡献身份。
- G2：`METHOD_INCREMENT_NOT_IDENTIFIED / STOP_CURRENT_MECHANISM`。v3 已绑定实际模块并拒绝审计反例；alias-aware static + repo/behavior 与 consumption + behavior 均 6/6。一个自然 Qwen 候选为等价正确实现，无新错误机制。
- G3：`SIMPLE_RULE_SUFFICIENT / COMPLEX_PLANNER_PAUSED`。六对象真实动作中多个 simple baseline 均 6/6；单次 wall-clock 不支持稳定成本排序。
- 第三研究点：`NARROW_TO_STAGE_SEPARATED_EVIDENCE_RELIABILITY`。scope 的 30 对 35 probe 节省已由 exact cache + miss revalidation 完全解释；scope 面板停止扩样。
- G2 状态到行动：`CONTINUE_RQ_U_DEVELOPMENT_ONLY / NO_METHOD_GAIN`。plain/decision fact 为 2/8 对 3/8、action 均 1/8；当前 action 分布是 `1/6/1` 对 `1/5/2`。现有 bundle 会丢新事实，不能据此证明正确状态无法迁移到行动。
- G3 增量补查：`KEEP_RQ_A_WITH_HEADROOM / NO_POLICY_CLAIM`。oracle 只证明目标定义下的覆盖/成本空间；depth-2 `5/43` 与同预算随机相容，不能称弱可学习信号；模型接口仍是 `UNEVALUATED_NO_VALID_DECISION`。
- C2反馈学习：`IMPLEMENTATION_STOPPED / ORDINARY_CONTINUATION_NOT_SATISFIED / METHOD_NOT_ESTABLISHED`。训练切换到新child而非保持父计算；E0合法patch、R25/36集合匹配与N26/36不构成干净方法比较，R36/36仅embedded解析。下一步见唯一指令，旧raw/报告保留。
- C3 可靠交付：`NEUTRAL_RETRY_STRONG_BASELINE / LOCALIZATION_REPAIR_STOPPED`。先前 V4/V5 error-pool 回放上 original 60/72、neutral retry 62/72、localization 59/72；定位修订修对 3 个、破坏 4 个。该面板 24/24 与旧 error pool 重合，不能作新 family 确认；透明门控与有界修复仅以 33-34 次弃答换取较低条件错误率。
- FinRank：`STOP_ON_CURRENT_PANEL`，不重开 H/K；当前负结果不否定经验复用的一般可能性。
- MA-CERD：资源 membership 基线不等于依赖边传播；selective escalation 未验证，完整动作集合 exact match 与动作可接受性须区分，见[更正](../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md)。
- Adaptive V3：当前 authored fixtures 上 greedy 已足够，two-step 无正向配对收益；RPC capability 边界不等于操作系统沙箱。
- CodeUpdateArena：修正执行器后开发集与新 families 均为有界负结果，不重复同一 prose-update 实验。
- VersiCode：结果只涉及语法与 API 名称，不证明行为正确或信息表示优劣。
- PyMigBench/外部迁移：NtripBrowser 与 Partridge 两个真实迁移均显示行为测试边界；Partridge 进一步暴露旧依赖回退和合法 alias 的不同错误。仍不证明 hybrid oracle 普遍充分，也不进入 Paper E 两案例主张。

## 运行与历史

本轮 Git 和离线治理不是生产运行检查；运行约束仍见 [CORE.md](CORE.md)。未核实的生产问题、外部发送和审批事项保留在 [THREADS.md](THREADS.md)，不随文档归档自动关闭。

以下为不含独立Phase B的历史阶段累计：4,064 个 accounting attempts、536 次 physical HTTP、316 次本地批量 generate、9,169,672 accounting tokens，其中 judge 113 次。总量已含训练token；本次事件复算少340，原聚合账不改、差额待核。累计 14 次 LoRA SFT、3,495,424 training tokens、3,117.78 GPU-seconds。本轮修订诊断新增 20 attempts、8,060 prompt tokens、952 actual non-padding completion tokens；一次 runner 故障发生在生成前，计 0 attempts。付费 API 和生产 Memory 写回仍为零。

原 THREADS 完整快照保留在 [memory/archive/THREADS_2026-10-21_pre_workspace_governance.md](archive/THREADS_2026-10-21_pre_workspace_governance.md)。2026-10-19 收口前状态见 [历史状态](../docs/archive/2026-10-19_memory_state_history.md)；更早快照仍为 `memory/archive/STATE_2026-09-22_pre_governance.md`。
