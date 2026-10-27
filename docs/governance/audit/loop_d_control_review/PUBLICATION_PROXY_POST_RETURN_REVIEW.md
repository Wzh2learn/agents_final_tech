# Publication/Proxy 阶段负责人复核

日期：2026-10-27（Asia/Shanghai）。对象：`f88499af6586dab1a06500ffbd918dc43ee38934`。

## 方法、边界与结论

采用 inquiry-methods 的最小实验与分阶段裁决、experiment-autopsy 和 verify-before-done。问题是：新执行是否改变研究判断，以及哪些失败来自评价、模型或工程？本次在 GB10 Python 3.12.3 上从第一批原始回答独立重放36个主结果，未复制第二批的评分字段；0新增模型生成、训练、judge、生产探测和A/C派发。没有运行全仓pytest。历史raw、评分器、稿件、manifest及D/A/C回执均不改写。

**裁决：接受真实执行和P1补证；P2旧评分可复现，但不能作为完整语义准确率或检索增益。先修评价与持久记账，再决定一个机制实验。Paper E正文已完整，正式构建与Owner事项仍未完成。**

机器收据：[PUBLICATION_PROXY_POST_RETURN_REVIEW.json](PUBLICATION_PROXY_POST_RETURN_REVIEW.json)；复现：[publication_proxy_post_return_audit.py](publication_proxy_post_return_audit.py)，在仓库根用Python 3.12执行，可用`--output /tmp/review.json`保存。合成反例只验证评分器，不是新模型实验或人工gold。

## 接受的进展（FACT）

- P1公共actor和全24题已交付，之前的执行缺口关闭。现有报告区分numeric 23/24、semantic 13/24、unit 14/24，以及4修复/0原numeric正确项破坏/1方向冲突。这是曝光开发面板上的简单基线，不是新来源方法确认。
- P2实际调用了本地**base Qwen3-4B**，不是前期ordinary SFT adapter；跨阶段准确率不能直接归因于任务或方法。12个UID来自11个table families，是分层选择的开发样本。
- 第一批40条与第二批40条的科学字段一致，但40个wall-time均不同；物理80次调用及全部tokens应计账。第一批36主调用+4冻结重试可独立重评分，原2/3/3 ACCEPT和strict 11/11/10均复现。
- Paper E有完整15页fallback和24条引用，较原单页/摘录交付有实质改善；仍为两案例，后续探索不并入首投稿。

## 改变研究解释的评分缺陷（FACT）

| 复现对象 | 实际观察 | 影响 |
|---|---|---|
| 净销售额UID `fcb5e3fa-...` | top-3为`["$1,289,962"]`，top-5/all为`"1,289,962"`，numeric_value均1289962、单位均thousands；旧span路径前者REJECT后者ACCEPT | 唯一新增ACCEPT不能解释为补查恢复了新事实；至少存在表示/评分混杂 |
| 6个arithmetic/count参考 | reference.program全部是字符串；expected_refs只遍历dict/list，均得空集。填入正确参考数字时全部只能PENDING | 这6类参考在现役路径上无法获得数字ACCEPT；不能据此否定推理或取证 |
| components UID `a75bb0b1-...` | 回答含正确的beginning/additions，也额外含结果项end-of-period，三臂仍ACCEPT | all-gold-spans覆盖没有排除错误额外项目，不等于完整集合正确 |
| Canada参考的合成反例 | `96,168`配`unit=million`和不存在的`P999`仍ACCEPT | scorer未绑定独立unit字段，也未验证引用确实存在并支持答案；尚非完整语义oracle |
| payroll UID `5e67e832-...` | 六条raw均含正确155/113，但numeric_value为数组，严格合同拒绝；还含需核验的TABLE:C3 | 不能把全部解析失败视作不知道事实；也不能修好JSON就追认完整语义正确 |
| audit-services的all臂 | raw包含错误类别及`VISIBLE:P7`导致格式失败 | 同一输出可以同时有语义与合同错误，不能仅选一个解释抹掉另一个 |

精确token差为top-5减top-3 **917**（9780−8863），不是911；all减top-5为1604。这些是每个UID最终尝试的输入token差，完整端到端成本还包含重试；80次物理总量为66,414 input + 5,218 output。历史0.75“error_delivery_risk”混入解析失败及评分器拒绝，不能直接命名为实际错误交付率。

原9个共享REJECT是旧合同下的行集合，不是9个独立、已确认的推理失败。已见两条候选机制：平均数题给出了正确两操作数但未归约；季度计数题给出了正确三季度却没有输出计数。它们支持优先检查**选择→类型化归约→答案合同**的信息损失，尚不证明新方法，也不能通过把参考程序交给executor制造收益。另有错行/时期/单位等真实残差待逐项核验。

## 资源事故与执行链（FACT / INFERENCE）

当前runner虽然增加了同路径已有完整ledger时跳过生成，但预算计数仍是进程内；raw在整批生成结束后才写，评分又覆写同一文件。移动失败现场或换输出目录即可失去全局累计约束。**推断：根因治理需要共享持久attempt预留、每次调用立即落盘、纯rescore命令与生成模式分离，而不是再提醒一次不要重复跑。**未在本轮修改历史runner或用真实模型测试故障恢复。

按原Phase B总帽保守扣除：672−188−80=**404**次生成；2,800,000−139,306−71,632=**2,589,062** generation tokens（按输入加输出保守占用）；训练仍余2次/3,680,052 tokens。本次没有释放这些余额，也未补授权32次超帽。A/C为24/24，新增派发需明确的新提案。旧340-token差额不变。

## Paper E构建复核（FACT）

本次实际调用内置`compile_latex_document`，显式选`paper_e_sncs.tex`，返回`compile-failed`：Windows restricted-token sandbox无法执行编译helper。未修改TeX或绕过该限制。此为可验证的工具不可用，不是缺少Owner科研许可；正式环境构建可继续由D处理，不能把技术问题归为Owner身份决定。

GB10渲染并人工视查fallback第1、8、15页：正文确实存在，引用末页仍出现BibTeX key、`author:`字段及未渲染的`\\url`。所以fallback仅供内容审阅，不是正式排版包。精确TeX、参考文献样式、公式/图表、完整页面视觉验收和对应PDF hash仍是技术交付门。编译成功不等于已投稿；Owner仍决定身份、许可和外部动作。

## 顺序建议与退出条件（VALUE / UNVERIFIED）

1. Paper E优先完成正常TeX构建及实质可读性，维持SNCS条件路线，不因方法实验推迟，不重复调研渠道清单。
2. 新版本评分契约同时覆盖正例与反例，逐层分报strict格式、答案内容、单位/方向、引用支持、实际交付；PENDING不能等同WRONG。从第一批raw零模型重评全部12UID三臂，原分数保留。
3. 以当前已曝光输出定位信息损失；先建立无gold的透明类型化计算/读出强基线，再选一个尚未被解释的自然机制。仅当接口和计账已合格，才按更新指令提案做一次有界模型诊断；无需预先证明正向收益。
4. 2027年10月送审不变。C1成熟、C2/C3待定；11月形成一个可持续任务/机制，1月评估是否重组贡献，不能用新一轮治理或同一错误修复拆出两个创新。

最大风险是反复修评分、再把修正后的开发分数当方法收益。退出：若修正与强简单基线已经解释残差，就关闭该面板的方法候选，保留测量材料；新任务必须对应具体未覆盖条件。首个可独立验证动作是重放本审计及评分器正反例，不是再跑40次生成。

## 本次完成门

GB10 Python 3.12.3实际重建原始上下文/提示hash并重评分36项，全部匹配历史计数；P1、future matcher、raw chain定点unittest合计16项通过。它们证明现有测试能通过，不证明本次新增反例已被旧评分器正确处理。文档lint在本机为0 fail / 0 warn；变更13文件的凭证形状扫描经已知合成正例校验后无命中。全仓pytest未重跑，生产和外部动作未执行。新增执行提案未派发，后续状态以唯一prompt和Owner实际接受为准。
