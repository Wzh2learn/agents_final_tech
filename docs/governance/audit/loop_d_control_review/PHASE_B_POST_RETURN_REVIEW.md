# Phase B回执事后复核

更新：2026-10-26（Asia/Shanghai）｜`VALIDITY_CORRECTION_REQUIRED / STOP_IMPLEMENTATION_ACCEPTED`

## 模式与证据边界

采用 `inquiry-methods / fact-check` 和 `experiment-autopsy`。核对提交 `c7bcd5e9` 的训练/生成源码、冻结合同、raw、C报告及账本；本轮对144条主要比较输出独立抽取并核对集合匹配计数。另在GB10已安装PEFT上运行CPU合成反例。未重训、未加载Qwen、未发科研生成、judge或生产探针。源码哈希、实际CPU输出及范围见[机器收据](PHASE_B_POST_RETURN_REVIEW.json)。

此前C的288行复算正确；本次不声称重新执行其全部评分、聚类bootstrap或真实模型前向。原始报告、协议、raw、训练工件和旧账本均保持历史身份。

## 事实：需要更正的执行前提

| 发现 | 直接证据 | 结论边界 |
|---|---|---|
| ordinary父adapter未在训练中保持激活 | `b2/B2_TRAIN_RUN.py:704`加载父adapter，`:710`添加新child，`:721`只激活child；preflight的parent_load也写active_adapter=b2_child | R/E确有真实参数更新，但不是报告声称的有效ordinary-parent continuation |
| 哈希和schema属于输出合同负担 | `B2_TRAIN_RUN.py:323`要求candidate/target SHA；`B1_LOCAL_EDIT_APPLIER.py:233`和`:270`做精确验证 | 纯model.generate没有哈希工具；未来由工具计算完整性字段。E当前先败在keys/schema，不能声称SHA单独导致0合法patch |
| Correct只表示证据集合匹配 | `B2_D_FREEZE_DECISION.md`明确sole estimand，5条合格纠正中3条目标与参考反号 | 27/26/25/0不能标成答案语义正确数 |
| R并未满足严格输出合同 | 修复raw独立解析：R36/36为embedded JSON、strict为0；72条R/E全撞384上限 | 第一对象可解析不等于严格可交付；不能把R写成接口完全修好 |
| R-N小差异没有清洁识别 | C报告区间[-19.4pp,+13.9pp]，N为sampling/192，R为greedy/384加suffix | 支持当前配置未见增益，不支持R普遍无效或干净因果负结论 |

GB10 PEFT 0.21.2的已安装`PeftModel.set_adapter`源码明确一次激活一个adapter。CPU反例中父adapter产生`[[2,2]]`，切到零初始化child后产生与base相同的`[[0,0]]`，同时父权重哈希保持不变。反例只证明原验收条件不足，不认证真实Qwen已修复或生成嵌套adapter等价。

复现（CPU，非新模型实验）：

```bash
cd /home/testuser/wzh/projects/agents_final_tech
venv/bin/python docs/governance/audit/loop_d_control_review/phase_b_parent_activity_cpu_audit.py
```

## 已确认的结果与未确认的解释

主要开发比较的集合匹配计数仍为O27/36、N26/36、R25/36、E0/36；E四个目标未决与32个未完成分列。R/E受过训练、A/C实际运行、停止当前实现以及不消耗确认/第二seed预算均可接受。

但父计算路径、极少独立纠正、重复样本、217/256 no-op/未决、全prompt+target loss及生成合同同时存在差异。不能把“没有得到好方法”变成“局部编辑信息无效”或“反馈无法转化为能力”。也不能因为训练标签不得在部署时读取，就禁止训练阶段使用合法训练参考，进而冻结已知错误顺序并称其正确修复。

排除一个看似合理却未证实的解释：已安装TRL 1.14.1对文本训练存在自动追加EOS逻辑。源码没有手写EOS不足以证明缺EOS是根因。本轮没有把任何单一混淆项认定为已识别的唯一原因。

## 价值选择、风险与下一动作

接受当前候选停止，纠正ordinary continuation和方法负结果叙事；旧R/E不追加训练、提示或确认。负责人上一版指令只写原则，没有要求前向有效身份和可学习语义目标的可执行证据，也应承担设计修正。

唯一下一步是一次合并任务：修正当前知识状态，并从既有自然失败中筛最多两个可完整语义核验的问题，只保留一个真实决策残差。可查条件化证据适用性或可核验的证据获取；若精确缓存、metadata规则、固定查找或普通检索已解释全部，则停止新方法主张，继续Paper E和学位正文。

原预算尚余484次生成、2,660,694生成tokens、2次训练、3,680,052训练tokens及3次A/C派发；不能重置。本次至多48次/240,000tokens开发小探针，训练0次，资格失败则不调用。未得到完整语义参考或部署可见动作就退出；小样本正向也不升级为确认。

Paper E不并入这些新实验，不重复扩展两案例。投稿渠道/作者/公开等Owner事项集中办理；内稿和期刊派生准备可继续。学位按2027年10月送审，C2/C3尚未成立，不能用本次治理或工程失败补足创新点。

## Git与协作观察

检查时本机与origin main为c7bcd5e9，GB10实验worktree也为该提交且clean；GB10主工作树仍为caa18102且clean。应分别报告各checkout，不能以实验worktree同步代表所有主树同步。后续正常fast-forward可对齐主树，保留实验worktree快照。

协作已用13/16次；已知Codex输入累计约93.7M，但缓存、复用和费用不能由这一数字直接推断，Claude量仍未知。下一轮只在剩余3次中安排A准备、A小探针、C联合独立核验；D承担过程裁决和正常集成，不为同一非阻断表述反复派新审计会话。
