# 自然错误与取证成本回执事后复核

日期：2026-10-26，Asia/Shanghai。模式：inquiry-methods / fact-check → portfolio-triage。
边界：冻结提交0af5f5444feff8190ca9bf87cadab98e5f3ebe13；读取D/A/C交付与现役指令；GB10只读复算、两个人工审计反例和词边界敏感性检查。非新模型实验、非人工gold、非方法确认。

## 1. 裁决

接受已执行的六次协作、原门下暂停模型、507行算术/hash及旧R/E停止。把当前科学裁决收窄为：

`EXECUTION_ACCEPTED_OFFLINE_PROXY_NO_GO_RETAINED_SEMANTIC_CLOSURE_NOT_ESTABLISHED`

P1所选错误有规则解释；统一可部署actor与全24题无破坏回归未在交付物定位。P2有限策略未过原代理/字符预算门；真实答案—风险—成本仍未测，当前分类器不能认证完整语义充分性。旧门和旧raw保留，不改阈值洗成正结果。

## 2. FACT：本次实际复算

来源TAT-QA dev SHA256：8da095a819af6db3c14877c6df2d4d29960e41d1a63dd1fa853507bd2a616af5。
最终507行canonical SHA256：93ce50e26d51359c5e8dca9cca9381607b50f762c93ff3cce3da164d830f340e。

| 策略 | 既有代理计数 | 既有可见字符合计 |
|---|---:|---:|
| table_only | 197 | 223,082 |
| top-3 | 452 | 619,687 |
| top-1-neighbor | 414 | 547,954 |
| top-5 | 486 | 773,767 |
| transparent stop/expand | 481 | 784,932 |
| all | 506 | 927,751 |

逐行重加与原结果一致；来源启发式分类table197、paragraph44、both265、unresolved1也复现。这验证实现一致性，不证明其语义构念有效。

## 3. 主要缺口与影响

### F1 / NEEDS_NARROWING：P1解释不等于已部署修复

[a_closeout/P1_SEMANTIC_LEDGER_FINAL.json](../../../../research/natural_error_evidence_cost_20261026_v1/a_closeout/P1_SEMANTIC_LEDGER_FINAL.json:54)给出六条文字规则；:562后重放表仅有5个选定错误项，4个模型错误/1个参考方向冲突。GB10本轮目录交付的.py/.sh只有两份P2脚本，未定位包含该policy标识的统一P1执行器或其全24题回归。外部/inline执行仍UNVERIFIED，不据此断言不存在。

4个错误的可见语义解释有价值，但尚不能推出19条原对无破坏、全部自然问题残差为0、P1问题永久关闭。还须区分numeric-correct与完整单位/方向/引用正确。当前实现/监督停止不受影响，不重开旧R/E。

### F2 / CONFIRMED_CONSTRUCT_GAP：来源分类器不是完整语义参考

[P2脚本](../../../../research/natural_error_evidence_cost_20261026_v1/a_closeout/P2_RECOVERY_RECOMPUTE_FINAL.py:170)的text_contains为规范化子串包含。:350—359抽gold答案/derivation字面量，:429—457以这些字面量的出现位置推来源；:745—750直接由分类/标注段落恢复产生potential。

本次在GB10原脚本实际复现两个人工反例：
- 问revenue=5；表只有年份2015和employees=100；段落给revenue5。子串5命中2015，被判table。
- 问revenue=5；表里employees=5、revenue未报告；段落给revenue5。相同字面量、不同角色，仍被判table。

这些是审计fixture，不算两条新自然发现。在真实197个table判定中，另有5个UID至少一个数字字面量仅以数值子串匹配、缺少独立数字token；只是敏感性标记，需按语义裁决，不能直接减去5或宣称真实错误率。

因此506条是自动参考状态，未成为506条独立完整语义裁决；potential也未证明是真实答案上界/下界。C已独立复现实现，但其18项matcher自测不会验证来源分类器语义。R7/R8仍只影响未来新评分路径，非当前no-go算术根因。

### F3 / INFERENCE：代理硬门过早替代了诊断问题

原-2pp和75%/50%门是在代理/字符量上的冻结取舍，按它停止当前候选属于合规执行。它不构成相同真实答案/风险下总成本无空间的证据。全上下文可能便宜且足够，也可能读出受干扰；必须在同一actor上测，不能由段落ID恢复直接代替。

本次负责人也修正自己的设计责任：上一版虽区分字符与答案，仍允许代理门把首次实际读出实验提前挡住。保留旧门结果；下一阶段新问题是代理与真实答案/实际成本的校准，未知收益即可进入有界诊断，不先要求证明收益。

### F4 / VALUE与成本边界

六次派发已花在准备/修复/审计/收口，没有完成原计划中的模型腿。D报告A累计输入46,580,135、输出241,232、reasoning-output86,945；本次未从所有raw独立重算这些usage。缓存/Claude/现金费用未知，不能由累计输入推收费，也不能用零科研生成概括全部成本。

下一轮协作精简为A实作+C一次固定快照联合审阅，保持原故障储备；不另起多轮“修文—复审”。科学问题的证据强度优先于工件PASS数量。

## 4. 推荐、条件与停止

优先交真正的Paper E期刊派生稿；并行补P1统一执行链/全24开发回归，进行一次最多48次生成、训练0的真实答案/成本诊断。仅拟新增2次A/C，累计帽22→24；原生成/训练帽不增加。此为待Owner接受提案，未派发。

小面板参考/actor必须合法、可执行；不能把启发式改名为语义oracle。冻结后按同actor/top-3/top-5/all比较，完整答案、合理未知、错误交付、实际非padding tokens/调用/耗时并报。不是2pp非劣确认，不保证正向结果。若连8—12题参考链都无法建立，记录具体阻断，不追加审计轮；Paper E稿件仍交付。

长期C1测量、C2充分证据语义使用、C3固定能力下取证/交付保持候选结构，后两项尚未成立。2027年10月送审，具体日未知；先在2026年11月确立一个可检验方法问题，不从四个错误或单次代理前沿外推整个年度研究计划。

首个行动：D读取本附注并确认科学边界，在唯一prompt内接续A一次实作任务。本文不授权A/C或外部动作。

## 5. 官方渠道核验与局限

2026-10-26读取Springer官方SN Computer Science作者指南与出版路线页：
- https://link.springer.com/journal/42979/submission-guidelines
- https://link.springer.com/journal/42979/how-to-publish-with-us

官方支持订阅路线无APC、150—250词Purpose/Methods/Results/Conclusion结构摘要、可编辑源文件及相关LLM使用披露。仅据此支持可逆派生稿准备，不证明录取率、发表周期、学校认可或总费用为零。渠道/作者/公开及正式提交仍待Owner；不新增ICAART实时日期/费用声明。

## 6. 本次验证边界

复算和反例脚本见同目录natural_cost_post_return_audit.py，机器收据见同名JSON。首次审计调用传错serialize_table参数类型，在读取自然数据时退出；改为原函数要求的table对象后重跑成功，首次失败未产生科研样本或更改原结果。

本次科研生成/训练/judge/生产探针/A-C派发/外部投稿均0。现役文档、唯一prompt和导航同步；原D/A/C/raw/冻结评分与Paper E正文不改。本轮本地/远端定点检查、Git状态在Documents/Loop_D_科研管理/checks收尾记录。原全量pytest已知缺FinQA fixture失败保留，本次不声称全仓全绿。
