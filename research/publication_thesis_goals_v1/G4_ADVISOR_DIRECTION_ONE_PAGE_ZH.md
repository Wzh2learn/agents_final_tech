# 学硕论文方向讨论稿（一页）

日期：2026-10-22
暂定主题：**智能体任务评测的有效性与证据驱动验证方法研究**

## 当前三项材料

1. **测量有效性审计（成熟）**
   Paper E 以两个受限案例区分可见性、检测、合同相对危害、分值敏感性、决策稳定性和复现差距。ICAART 11 页投稿包、全精度统计、私有 artifact 与目标包审计已经就绪。建议作为第三章和当前独立小论文，主张保持“受限两案例审计”，不扩展为普适理论。

2. **变化任务完成验证（候选，当前停止扩展）**
   新版 verifier 已绑定实际模块、manifest 和环境，使用同输入的合法目标结果配对干预；旧“调用但丢弃 result”反例已能拒绝。六对象比较中，alias-aware static + 原仓库测试、static + 独立行为合同、consumption + 行为均为 `6/6`。因此消费判据虽修复，但没有超过简单强基线的独立增量；自然 Qwen 候选也是等价正确实现。当前建议保留为失败/边界材料，不再扩迁移或模型样本。

3. **证据失效、复用与状态传播（第三贡献候选）**
   同一候选和依赖保持不变、只把输入从真实 fixture 切换到短字节范围时，全局复用和 dependency-only invalidation 都产生 `2/5` 误迁移。新的策略探针进一步把证据粒度写成合同：只有 `per_input` 旧证据才能 exact-input `REUSE`，同 regime 新输入走 `PARTIAL_CHECK`，条件改变走 `FULL_CHECK`，缺 fingerprint 走 `DEFER`。在 5 个候选 × 4 个开发场景的 20 个 transition 上，scope policy 与 always-full 都是 15 CORRECT、5 ABSTAIN，但 probe 数为 30 对 35。20 个 transition 不是 20 个自然 family；该机制仍不是论文贡献或学习策略，下一步需要第二个自然模块和真实修复/结果收益。

   STALE 公开数据的开放探针补充了“找到旧证据后，如何把新状态传播到当前回答”的机制线索。确定性 retrieval 中，query-only recall 为 `0`，lexical top-k 平均 recall 为 `0.347`，oracle relevant top-k 为 `1.0`；后者只是开发上界，不是可部署检索。固定 Qwen3.6 提示下，主 4 UID 的 `dim1` 查询在 oracle raw sessions 下，one-shot 只有 `1/4` 检出 stale；显式给出隐藏的 `M_old/M_new` 后为 `4/4`，再加 `explanation` 仍为 `4/4`。由 raw sessions 先抽取 state card 再回答的 two-stage 为 `3/4`。冻结的同 STALE 发行版新 UID 确认集含 T1/T2 各 4 个，one-shot 为 `0/8`，two-stage 为 `4/8`，两类均为 `2/4`，配对差为 `+0.50`；共 24 calls、49,513 accounting tokens、0 retry。这里的 state card 不是 gold，答案极性是 lexical proxy；新 UID 仍是 STALE 内部确认，不是外部确认。当前只支持“状态表示与状态抽取是候选机制”，不能写成完整方法贡献。

## 建议的贡献结构

- 第一项：评测测量对象和合同敏感性审计；
- 第二项：迁移任务的证据充分性边界，不强行保留方法创新；
- 第三项：条件变化后的证据失效、复用与状态传播，重点是证据粒度、`REUSE/PARTIAL_CHECK/FULL_CHECK/DEFER` 动作合同，以及 raw-session 到 state card 的状态抽取是否改善 stale-state 处理。

这三项共享“什么证据足以支持结论”的问题，但分别涉及测量、任务完成和证据时效，不应合并成一个通用 Agent 框架。

## 请导师确认

1. 是否接受 Paper E 以受限两案例作为正式独立论文边界。
2. G2 在 simple strong baseline 已 6/6 后，是否同意停止当前消费方法扩展，把结果写成验证边界。
3. 第三项是否按透明证据复用合同和状态表示候选继续；下一门应要求第二个自然模块、真实修复/结果收益，以及非 oracle retrieval 下的冻结比较。state card、lexical polarity 和 STALE 内新 UID 均不足以单独成立方法贡献。
4. 按 2027 年 3-4 月送审倒排，是否优先保证 Paper E 投稿、第三章定稿和第三贡献资格判断，而不再扩大实验面。

## 六个月顺序

1. 10 月：Owner 完成 Paper E 投稿决策；冻结 G2 停止结论。
2. 11 月：寻找一个正交证据失效案例，并在非 oracle retrieval 下复核状态抽取；若 simple rule 或 one-shot 已足够，停止第三方法候选。
3. 12 月至 2027 年 2 月：把三项材料整理为中文正文、图表、引用和限制。
4. 3 月：导师审阅、作者/展示/成果认定材料收口。

当前未完成项包括 Owner 外部动作、第三贡献的正交自然案例、非 oracle retrieval 下的状态抽取验证和论文正文整合；不应以增加调用或表格数量替代这些判断。
