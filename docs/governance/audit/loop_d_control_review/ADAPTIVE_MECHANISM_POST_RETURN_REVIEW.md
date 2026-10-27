# Adaptive Mechanism 回执事后复核

日期：2026-10-27。Mode：inquiry-methods / fact-check。性质：负责人AI复核与下一步提案；不等于人工gold、新实验完成或新增资源授权。

## 边界与已接受结果

基线 `70e06ebe`。读取D回执、C固定快照审阅、question-only实现、评分器/控制、冻结协议、持久预算runner和Paper E源包。在GB10 Python3.12运行相关31项测试，全部通过；三组36行全字段回放与已提交JSONL完全相同。新复算见同目录 `ADAPTIVE_MECHANISM_POST_RETURN_REVIEW.json` 和 `adaptive_mechanism_post_return_audit.py`。

FACT：oracle 31 ACCEPT/5 REASONABLE_UNKNOWN，blank 12/19/5，question-only 31/5均可复现。question-only actor确实只从可见题面推断类型，不读取gold answer_type；评分阶段使用参考类型不构成actor泄漏。接受当前开发面板停止扩模型，不要求为用完预算再跑冻结8UID。

FACT：持久预算主账本仅初始化事件，未新增真实生成。7个故障控制有价值，但mock seam不是已验证的真实生成接入；未来调用仍须绑定唯一账本和真实token上界。Paper E正式构建仍为BUILD_BLOCKED，不把完整fallback等同正式可投稿件。

## 需要收窄的评分声明

1. **同值正确角色误拒。** 当前状态登记于[THREADS](../../../../memory/THREADS.md)的NEXT-C2-SUPERVISION，本段保留本轮复现证据。 两行均为100，问题只问wanted行。只引用正确行与只引用错误行均REJECT；引用两行反而ACCEPT。`_find_numeric_cells_report`汇集全部数值匹配，未解决角色歧义。原“numeric_equal_wrong_role”反例只测了误放，缺合法正确角色的配对正例。未来有可信角色参考则判正确角色；参考无法分辨则PENDING，不要求引用全部同值项。
2. **混合引用漏检。** 两操作数问题，第一项精确引用、第二项只给列引用，仍ACCEPT；合同却说宽泛列支持应PENDING。不能以“至少一个exact”替代每个必要操作数的支持。
3. **单数字span的数值字段未核。** 现有两个UID共5条已ACCEPT输出，仅将numeric_value改为-999999，仍5/5 ACCEPT。原因是gold `answer`为单元素list，适用性判断只解析标量。正确数字文本与矛盾数值字段同时出现不满足一致性合同。

这些是本轮可执行反例，不是新增自然失败率；不证明原31个答案都错，不改写历史31/5。它们要求把“scoring V2有效”改为“现有控制通过，仍有角色与数值字段边界”；新增版本补配对控制后再纯重评原raw与actor输出。不要把修评分器记成C2/C3方法创新。

## Paper E的实际解阻路线

FACT（2026-10-27官方核验）：SN Computer Science投稿指南接受Word、建议常规10pt Times Roman，要求正文方括号数字引用；使用LaTeX时推荐Springer Nature模板。现包为article+`elsarticle-harv.bst`，尚未验证最终引用样式，不能只因有24条key即认定格式合规。

官方载体：`https://link.springer.com/journal/42979/submission-guidelines`，Source Files / Text Formatting / References。该页可核验Word、公式编辑器及数字引文要求；本次未核得统一正文词数上限，不引入未经证实的字数门。投稿时需再核实时页面及目标article type。

FACT（本轮工具盘点）：本机已安装Pandoc3.2.1，路径`D:/pandocLatex2word/pandoc.exe`；Word程序存在。GB10 `/usr/bin/soffice --version`成功，版本24.2.7.2。未安装新依赖，未创建或渲染新稿；可行性工具存在不等于Word稿件已完成。

建议：D本机Pandoc转换、GB10 LibreOffice渲染、逐页视觉核验。以当前两案例完整正文生成并核对**可编辑Word稿**及渲染预览；数字引文、完整24条格式化文献、真实公式、图表、跨引用、声明逐项验收。无需把安装TeX作为投稿准备的唯一入口。Word不是自动合格，必须逐页视觉检查。已有旧DOCX不直接复用为最新版；若可用Word渲染也不可达，保留具体阻断并提出最小依赖方案，不再交“又一次BUILD_BLOCKED”冒充推进。

## 建议的下一步及退出条件

VALUE：先解Paper E可编辑稿/渲染和有限评分修复；再冻结question-only强基线，在未曝光自然表族上做一次机制诊断，区别同源新表族与真正跨数据源。旧12UID封存为开发回归，不继续按题面加分支。

INFERENCE：现有31/5说明强规则足以解释该暴露面板，不能结束跨表族的证据选择—归约研究。下一步只比较direct、普通typed execution、一个机制上明确的候选；同模型/同可见上下文/同计算器和预算。先测，再决定是否值得训练。若只有格式恢复、弃答或免费工具差异则不认方法增量。

提案为新增2次A/C协作（26已用保留，累计帽拟28），一次A实作与一次C固定快照审阅；D自行集成。原科学总帽不增加，旧未用36/240k子预算仅在Owner接受新计划后重定向，训练0。当前会话未派发、未生成、未安装依赖、未外部联系。

风险：再次为修评分而无限延期、把新表族冒充跨源确认、拿宽松评分或工具不等量造增量。退出：本次最多一个候选；无增量则停止该候选，给出实测机制边界与一张后续研究卡，不重开全景治理。首个可验动作是成对复现上列三个评分控制，并对照官方指南选择Word生产链。
