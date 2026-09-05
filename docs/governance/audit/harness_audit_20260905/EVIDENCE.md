# 审计证据账本

更新：2026-09-05，checkpoint 7（E01–E13为恢复的初审记录；后续E14–E18及检查点更正优先）。除特别注明，路径相对 `D:/AIRcommend/JinRongAgents/agents_final_tech/`；基线 HEAD 为 `9cdd141c418d8c91d63715f701ec591e7ede8f4c`。行号为当前工作副本的真实文本行号。

证据身份：A=主线程直接读取核对；B=独立分工审计读取回报；H=仓库存留历史记录，非本轮动态重演。A/B 都是静态核查，不代表执行测试通过。

## E01 D3 定标数据流（A+B）

- 卡：`docs/experiments/2026-09-01_d3_matched_specificity_card.md:114`，S1只用clean controls定标，禁止扰动样本。
- 实现：`research/paper_d3_matched_fpr_stage_a.py:830-878`，fpr_calibration_table接收clean和harmful两个集合；844取harmful支持集，847加入1e-12候选，851-853依该批TPR择优。
- 交叉拟合：同文件895-901，用其他fold的clean与当前评估fold的ev_flat/ev_lay共同定标。
- 自证：1383固定`S1_calibration_only_clean=True`；存盘JSON39及1405也为true。
- 引入提交：`51cbed9e`，主线程git blame已核对。
- 限定：923-927以同一确定性值相减构造clean零分；当前两臂正仿射，不能从契约失败直接推出协议差0错误。
- S5的max TPR措辞解释实现动机，但卡面声明覆盖E2，没有取消S1。

## E02 指标误抄（A+B）

- `memory/STATE.md:120`：conditional/end-to-end「均1.0」。git blame归于`51cbed9e`。
- `docs/experiments/2026-09-01_d3_matched_fpr_stage_a.md:167-173`：匹配工作点检出90，conditional1.0，end-to-end0.810811。
- JSON：`logs/graph/eval/d3_matched_fpr_stage_a.json:1238-1247`；字段 `payload.a4_matched_fpr.localization_S3.at_matched_theta`。
- 主线程直接解析：n_detected=90、n_correct_location=90、p_correct_given_detected=1.0、end_to_end_p=0.810811。分母111。
- 这是现状摘要错误；原始报告和字段在这一点一致。
- `side_handoff_20260829.md:27`：6例[3×C1+4×C2]；STATE140-145、THREADS648为7 E→H+1 H→E，净分母+6。handoff为审计前已修改的工作副本，不能据此归因到HEAD。

## E03 LF 哈希守卫（B）

- `scripts/graph/hooks/summary_recompute_guard.py:25-30、175-176`。
- 纯LF时计算字典无lf键，raw-only收据无sha256_lf键，缺失值相等可令lf_ok为true。
- 精确触发：纯LF + raw期望失配 + LF期望缺失。数值claim仍可能失败。
- 引入`78e3048d`。
- D3报告234-253是raw-only收据格式例子；该工件git index=LF、working tree=CRLF。因此未证实本机当前误放行。
- 同工具181-190对照JSON已存字段，不独立重算研究指标或扫描报告正文。

## E04 Loop B 双判决（B）

- `scripts/graph/loop_b_verify.sh:403` Shell整体条件漏pgpool_violations；413传给Python。
- `scripts/graph/write_report.py:33`含PG池条件。
- 416-417日志与519状态翻转继续用Shell结果；521为普通日志，无对应失败退出码。
- `scripts/graph/status.sh:36`从日志提取最近PASS，非同run强绑定。
- 引入`1196ee9b`：扩展Python判据未同步Shell。
- 当前`logs/graph/verify-report.json:4`为2026-09-04 22:14的全项PASS，不是PG-only分叉的实际遥测。

## E05 抽验不可能失败（B）

- `research/paper_d3_spotcheck_recompute.py:94`：`rho is None or ... or True`。
- 查找键遗漏真实的`spearman_rho_rank_identical`。
- `logs/graph/eval/d3_spotcheck_recompute.json:87-91`实际rho_found=null、pass=true，仍计入12/12。
- 85-89仅检查已存值，不重算bootstrap；工件82-83部分detail为null。
- 130行脚本结束，不把检查失败变成非零退出码。
- 引入`be26e016`。
- **排除夸大**：W2的常量True是明确标supplementary的观察，宜移出PASS分母；D2的`if False else True`变量row_ok未使用，不能说它直接制造PASS；D3主脚本1248的同函数自比属于同源定位建模声明，严重度低于独立抽验的实际假通过。

## E06 冻结清单删除（B）

- `scripts/graph/hooks/pre-commit:8-9`，diff-filter=ACMR排除删除，空变更集提前成功。
- `scripts/graph/loop_b_verify.sh:113、123`，清单打不开不增加violations，测试文件数足够仍输出零。
- hook引入`cf5df3df`。
- 只证明源码路径；没有核对本地实际安装hook或远端运行版本，没有执行删除复现。

## E07 查看副作用（B）

- `scripts/graph/status.sh:4`称只读；111调用默认docs_lint。
- `scripts/docs_lint.py:235-251`创建目录并覆盖带当前时间的`logs/graph/docs_lint_report.json`。
- 调用引入`cab17b95`。
- status53使用普通sqlite3.connect，缺库可能创建空库；只读可改URI mode=ro。
- 本次没有运行status/docs_lint。

## E08 文档与记忆结构（B）

- `AGENTS.md:412-429`：STATE覆写快照、THREADS未决、日志另存；423宣称启动约2KB。
- 实测文件字节：STATE42042、THREADS173363，总计215405，未含CORE。是字节，不是token。
- STATE5-6仍等D2/下一步Phase B；105-151已经后续收口。
- handoff15称THREADS最新在顶；实际顶5-14为08-01/08-03，最新在653-667。
- INDEX220归档标题；252-272最新研究条目无新标题接在其下。
- docs34的8/58/92仍将PSO作主贡献，到121-127尾注才撤销。
- docs17标活跃，197-226旧待评估/待部署与316-334已运行状态并存，历史标识不完整。
- AGENTS421与INDEX316规定THREADS唯一未决；docs29的79-80又规定新挂账进其表。
- docs29 A13:115仍待08-29窗，STATE12已执行。
- INDEX261的D2待圈选与266已销账并存；259的D1待autopsy与260已有决策并存，272重复登记。

## E09 令牌与恢复成本（A+B，数字为H）

- D2定稿卡73-84：首跑629428 tokens零工件；后改两段独立交付，要求按键段读。
- DR4卡73-84：首跑1281246 tokens，工件已生成、报告/收据/提交未完成；限制只读已有工件、收口重派。
- THREADS646/659有同类自报；docs29的49/71把预算列作前置/未实现护栏。
- 没有核对供应商账单或原始usage，所以只能写“卡面/台账记录”。token大不自动等于浪费；没有总工时，不能计算治理占比。

## E10 预注册与论文边界（A）

- D3卡130冻结28调用，134防泄漏，138问题模板/schema由Loop A定义；146澄清DR4唯一H→E例不在judge调用清单，以确定性证据呈现，零追加调用。
- 最近相关提交0f132b8、9cdd141。未连接远端确认实际执行。
- D1设计15-18把可见/吸收行为纳入分类，DR4卡46-51改为独立实例级oracle；DR4脚本965-976先生成并冻结oracle输出，再比较旧分类。
- **限定**：主函数此前已经装载D1/T2对象，不能说整个进程从未读过任何旧字段；可确认oracle函数输入不含检测结果、输出先冻结后比较。
- Claim Set v2:83已记录D3仿射恒等适用域；paper/draft_v0_s1_s2_s6.md:89-102已同步阈值摆放解释。不能说论文完全没吸收新结论。
- D4没有单独定稿卡实证；已读T3前身卡/设计及Claim Set v2:91重设计注记，仍应按拟卡阶段报告。

## E11 Skill 清单、引用与遥测（B）

- 71顶层源；A50、C27，77安装项、71独立名称；AGENTS与sync数组逐项一致。
- rg非忽略枚举：92个SKILL.md、1100个文件，含科学包嵌套技能；不是92顶层安装项。
- `AGENTS.md:311`及旧skill第6行声明弃用；`scripts/graph/loop_a_exec_constraints.md:118`仍用旧verification-before-completion作为触发入口。
- routes.example.json24/29/39目标research-driven-design、organize-logs、exp-lifecycle缺源。8目标仅2属C清单；skill_router96默认routes.json本机不存在。只是示例，不证明现场路由故障。
- figma-implement-design/SKILL.md18的figma-create-design-system-rules是真缺源引用；其余8个静态缺链候选为示例占位，不列故障。
- skill_router126只输出建议，没有实际调用/结果/耗时事件，无法算利用率。
- sync_skills29-30先删后拷，49-60有内容一致性检查；可改暂存校验后交换。未运行同步。

## E12 研究脚本输入与库存（B）

- research/pso/pso_question_set_search.py55/65从共享eval目录glob读NF/judge，62-63/75-76解析错误跳过；174起CLI只有disc/out，213-219元数据没有完整题库输入hash。
- 相同命令/seed的输入可能随目录变化；未重跑证明历史结果受影响。
- scripts中126个py/sh/ps1：根90、archive15、graph13、hooks7、scripts/research1。逐文件SHA256无完全重复，不代表不存在代码片段克隆。
- research有39个py（根37+pso2），paper一个md；代码/稿件已有目录隔离，但研究仍依赖共享eval目录。

## E13 值得保留的实证（H）

- logs/graph/dispatch_log.md706记录冻结测试修改被拦rc=1、新测试可提交；707记录Loop B对5050死锁期报警；933记录PG阈值演练与周期。
- THREADS653把恒等式结果转为主张适用域；663-665区分点估计与bootstrap均值、结构字段与散文误抄。
- docs17:3-5、docs29:65-69保留同窗交互假设与声明→验证→实测值结构。
- 上述是留存历史记录，不是本轮独立重演，不能换算保护成功率。

## 未升级为主 finding 的线索

- status45称禁杀graph-loop-b，但graph_orchestrator153-155的stop_all会杀该session；实际授权边界和运行路径未全查。
- 派发示例40-42内层codex|tee没有显式传递pipeline失败；当前实际使用与事故关系未证明。
- tmux前缀误命中、PowerShell/SSH多层引号家族仍需定位当前统一启动器与反例覆盖。
- 截断误报和0.810689/0.8286误引在旧prompt/台账有记录；已确认docs29 A18:118承认收据外裸数字未核验，但未逐一重演历史数字来源。

## 收口前必做

1. 独立反方审阅本报告，重点检查影响夸大与源码/运行态混淆。
2. 恢复后核对HEAD、已有工作副本修改列表，再决定哪些行号需要更新。
3. 对剩余家族能静态闭合则补证据；不能闭合则标“未证实”，不以合理建议冒充已存在机制。
4. 最终报告明确成本为估计，动态复现未做、运行态未核查，建议未执行。

## checkpoint 2：交接文件核验（2026-09-05，A）

- 已检查 RESUME.md、AUDIT_REPORT.md、EVIDENCE.md 存在，Markdown 互链目标均存在，文本无 U+FFFD，文件尾有换行。
- 已检查状态措辞：综合报告反方审阅仍未完成；测试/动态复现未执行；三个分工审计已经返回。没有把分工取证写成终审。
- 只读复核本地 HEAD 仍为9cdd141c418d8c91d63715f701ec591e7ede8f4c；工作区仍为两份handoff修改、PROMPT.md及IMPLEMENTATION_PLAN.md未跟踪。
- HANDOFF_PROMPT.md 保存完整续审请求。没有新取证改变F01–F10，也没有实施修复。

## checkpoint 3：续审启动（2026-09-05）

- 已依次恢复 HANDOFF_PROMPT、RESUME、AUDIT_REPORT、EVIDENCE；HEAD 仍为 9cdd141c418d8c91d63715f701ec591e7ede8f4c，四项既有工作区变化列表一致。
- 已按 review-codebase 启动独立反方审阅，输出 CRITIQUE.md；主线程补查本地钩链及 tmux/PowerShell/SSH 失败家族。
- 尚待：反方裁定整合、现行防线取证、最终文档核验。没有运行仓库脚本或实施修复。

## E14 本地安装钩链（checkpoint 4，A）

- 只读 git config --show-origin --get-all core.hooksPath 无配置值；git rev-parse --git-path hooks 指向 .git/hooks。
- `.git/hooks/pre-commit:1-13` 与 `scripts/graph/hooks/install_hooks.sh:8-20` 按文本行规范化换行后逐行相同；本地入口 SHA256=52085D01EB63AC231C465DAE51D0EB03AD70DB2360370CD67A70887C68F688A8。不是把入口与单一冻结子hook误比。
- 入口7行先调用冻结守卫，8-11行 glob 调用 *.precommit.sh，13行汇总返回；因此 F02/F05 对应源已被本地入口引用。入口自身未纳入Git，不能归因某提交或证明实际commit时已经执行。
- 摘要包装器 `summary-recompute-guard.precommit.sh:14-16` 无Python时警告放行；19-23行只枚举ACM的Markdown，并读工作树文件；24-29行无收据只警告。此保护不是任意提交内容的全量强制验证。
- 未执行hook、未改文件权限，未确认GB10安装/运行态。

## E15 tmux / PowerShell-SSH 现行防线（checkpoint 4，A+H）

- `memory/THREADS.md:623`（ca7a4f93）和 `docs/experiments/2026-09-01_d2_autopsy_decision_record.md:10,21`（5d93f813）记录前缀坑后更换唯一观察器名 d2r2，00:20 SESSION_ENDED、attempts=16、自清。属历史记录。
- 当前仓库 `scripts/graph/graph_orchestrator.sh:25,77,154-155` 仍使用普通名称目标；`:40-42` 是打印派发示例，非统一执行器；`loop_d_monitor.sh:39` 同样用普通名称。不能从一次更名推出家族级精确目标约束。
- `memory/THREADS.md:629`（e5c82d34）记录 PowerShell 展开内嵌 heredoc 的 $()，处置为本地写文件+scp，并记录 bash -n SYNTAX_OK；它是历史语法检查声明，不是本轮验证。
- 在 scripts 的 .sh/.ps1 清单和tmux/ssh调用搜索中，未定位承载上述两类约束的统一实验派发/观察器实现；dev_remote_demo.ps1 是端口隧道，不是实验派发器。此结论限定本次检索范围，不断言远端不存在。
- 本地以下三件均不存在：logs/graph/eval/loop_a_d2_done.json、loop_a_d2_r2_done.json、loop_a_d3_done.json。台账所指 /tmp/d2r2_watcher.sh 与 /tmp/d3_watcher.sh 是远端临时路径，未访问。故无法独立核对完成信号或脚本内容。
- tests/*.py 的 tmux/watcher/summary guard/frozen/Loop B 关键字检索只命中 test_b4_instrumentation.py:57 的排除词，未定位这些家族的负例套件；不等于证明所有仓外/历史测试不存在。
- 结论：两家族已有处置纪律和历史恢复声明，当前通用防线与反例覆盖未证实。建议固定脚本+显式参数/输入摘要、精确会话身份、独立退出工件；中文/引号/换行/前缀碰撞为未来验收，尚未执行。

## E16 截断误报与证据身份（checkpoint 4，A+H）

- `memory/THREADS.md:655` 明确撤销“164行、缺§8③④和§9”的截断声明，记录登记版完整与逐条核对。本次未重演原工具显示截断，不复述敏感沉淀全文。
- AGENTS.md:449-452 的 UTF-8 字符安全截断规则针对编码损坏；不能当作“把显示截断误认源文件缺失”的机械防线。
- 数字漂移、令牌耗尽、CRLF/sha、工件散文分别继续采用 E02/E03/E05/E09 的已完成证据，不重复扫描。


## E17 补齐归属提交与引文更正（A）

- F07：AGENTS421 单一事项源来自 0b5f33b3；423 约2KB来自 69d97445；docs/29:79-80 第二挂账入口来自 1fe4e413。是所引行的 blame 归属，不把后来全部文档增长归因这些提交。
- F09：PSO输入glob与静默跳过 research/pso/pso_question_set_search.py:55-65 来自 0271b498；查看副作用继续采用 E07 cab17b95。
- F10：旧触发引用 loop_a_exec_constraints.md:118 来自 e86ff07b；先删再拷在 sync_skills.sh:29-30（78ec44a6），原报告写28行不精确，现更正。检查模式在49-60行，逐项目录内容比较在43-44行。
- E15普通tmux目标 graph_orchestrator.sh:154-155 来自 91026389。E16撤销记录 THREADS655 来自 0f132b86；字符安全截断规则在AGENTS449-452，初录450-453更正，归属3147bed4。
- 当前本地钩链四个包装器为 cjk-byte-check、index-guard、large-file-guard、summary-recompute-guard；没有执行其中任何一个。

## checkpoint 5：反方首批限定（2026-09-05，待完整裁定）

CRITIQUE.md 检查点A已落盘。F01/F02/F03/F05核心静态路径获独立确认；需将F02触发扩展到纯LF时raw哈希缺失也可命中缺失计算值；F05双层均漏只适用于清单删除/不可读等条件，普通冻结条目删除在清单完好时仍被Loop B捕获。F04及F06–F10完整裁定尚待回报，不能在此时宣称终审完成。

下一步：整合完整反方结果、复核修订点、完成报告与恢复入口核验。

## checkpoint 6：首轮反方整合（2026-09-05）

F01–F10逐项独立裁定已完成，无整项误报删除；主报告v0.2已整合影响范围、替代方案、成本和严重度分歧，详见CRITIQUE.md与报告更正节。补充F04 detail-only模式、F01零clean阈值边界；F10首项成本/严重度保留审慎限定。待完成仅第二轮定向复核（含摘要包装器工作树/暂存对象边界）、最终文档核验；遥测/远端/动态复现是未证实或范围外，不因收口而变成已验证。

## E18 独立反方补证（B；详细结果见 CRITIQUE.md）

- F01–F10均保留，限定及成本更正已合入主报告。F10反方建议整体P3，综合按review-codebase保留较高的P2/P3并拆分：分发非原子P2、引用/示例P3，无事故升级。
- F02除LF哈希缺失，还有raw缺失分支（Python84-104、175-176）；包装器19-23以staged名称选取但Python154/164/172/182读工作树，部分暂存或暂存后编辑可造成检查对象与提交blob不一致。仅静态证明，无动态复现、无现成绕过事件证据。Python缺失/WARN为显式降级。
- F04的44-76、78-89、114-122有detail-only/存值/存在性检查，不能按标题认定统计独立复算；19-29真实哈希重算、103-105真实合并计数检查应保留，不把12项一概否定。
- F05普通条目删除在manifest完好时由Loop B98-101捕捉；双层缺口需manifest失效等条件。F01清零分布取θ=0会使score≥θ的经验FPR=1，候选边界必须预冻结，经验预算不等于总体保证。
- F03引用定位修正为Shell404-406、Python33-35；F10删除复制29-30，E17留更正。首轮确认不代表动态验收通过。



## checkpoint 7：终审裁定与最终限定（2026-09-05）

- 两轮独立反方完成，原文见CRITIQUE.md；F01–F10均保留，无整项误报关闭。主报告v1.0已整合所有建议，不等于仓库问题已修复。
- 对checkpoint5/6及E18的F05短句作最终限定：hook已证实漏检删除；Loop B在清单不可读/无条目等条件可能报零，但普通清单暂存编辑仍受hook硬编码保护。因此“任意清单失效必然穿透双层”不成立。清单删除路径在其他守卫条件满足时是本次指出的双层缺口。
- F02显式降级细分：Python缺失，--warn-missing对缺工件，符合包装器条件的报告缺收据时警告。工作树与暂存对象不一致及缺失哈希比较仍是成立的源码缺口。
- 已完成剩余可读证据核查；远端运行态、遥测百分比、动态反例均未证实/未执行，无任何源码修复或实验。
- 下一步：本次最终审计文档与Git状态核验；此后仅在新证据/明确新授权下继续。

最终核验结果：本地HEAD仍为9cdd141c418d8c91d63715f701ec591e7ede8f4c；工作区仍为两份handoff修改及PROMPT/IMPLEMENTATION_PLAN未跟踪。五份审计文档读取/互链/乱码/换行检查通过，主报告10条finding及最终限定存在，状态检查零错误。这里只验证审计交付物，不代表被审计守卫或实验测试通过。本次授权内工作已完成；后续修复需另有授权。
