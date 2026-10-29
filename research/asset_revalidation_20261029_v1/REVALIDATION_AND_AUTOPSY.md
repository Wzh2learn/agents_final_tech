# 研究资产复核与尸检

日期：2026-10-29，Asia/Shanghai。基于 [事前范围](PLAN.md) 在 GB10 复算既有输入和产物；无新模型生成、训练、judge、生产探针或外部联系。本报告是对保存结果的事后复核，不是新来源确认，也不是独立人类评审。

## 1. Paper E：冻结结果可复算，但“更多干净样本”不能修复构造性缺口

执行仓库原有 negative-result recomputation，唯一脚本改动是将输出位置重定向到独立临时目录，不覆盖冻结结果。11 个 summary 检查与旧回执一致：118 次受控注入、96 次可见；OCR-like 0/13；固定比例约 0.375、最大偏差 8.75e-8；两个 clean support 都为 0；全向量/直接叶各 1.000，非直接叶 top-1 0.333、平局 0.667。旧输入 hash 和三项 stage 产物 hash 均匹配。机器摘要见 [paper_e_summary.json](paper_e_summary.json)。

更有解释力的是：原 [matched-FPR 分析](../stage_e_method_revision_20261009/matched_fpr_reanalysis.json)记录，2,382 条干净记录的差值为零是同一未修改记录重复计算造成的，因而增加同定义的干净记录本身不能识别唯一正阈值。未来可比较另行定义且事先冻结的 null/pseudo-mutation 或不同噪声测量，但要与现有口径分开，不事后声称原协议已得到独立验证。

本次复核加强的是数据绑定和解释，不提高跨来源泛化强度；单模型语义判断与合成注入边界仍在。75/95 与 20/95 所用各协议操作点的完整映射仍需核查，不能把一个叶级阈值不加区分地赋给所有协议。

## 2. 迁移验证：行为盲点可信，方法优势尚未识别

GB10 使用仓库 venv 重跑 v3 的五个定点测试：5 passed；这验证构造反例、别名、缓存未知等实现合同，不等于重跑六个真实仓库对象。六对象的历史完整原始结果 SHA-256 与既有绑定一致；逐行确认 parent、gold、source fallback、alias、构造 counterexample 和一次模型候选的身份不同。

其中 parent 与 source-fallback 的仓库测试均为 PASS，静态和消费合同判 INVALID；gold 与 alias 均为 VALID。历史汇总的 repository-tests-only 为 4/6，而 alias-aware static 加测试与消费干预加行为合同均为 6/6。前者说明当前测试面可能漏掉特定目标合同，后者说明此面板没有证明复杂干预优于强简单基线。6 个对象不是 6 个独立自然项目；参考合同和 upstream 迁移目的仍是应用条件。

## 3. Agent：从抽样断言扩展到完整保存轨迹

对四次相同任务的已保存 report，使用同一公开任务的现有 oracle 计算完整 2,000 个请求的逐项 idx、prompt_tokens、hit_tokens。脚本 [revalidate_agent_artifacts.py](revalidate_agent_artifacts.py)、结果及输入哈希见 [agent_whole_trace.json](agent_whole_trace.json)。这是在看过结果后追加的同源 oracle 对照，未重新调用模型，不能当成独立数据或因果比较。

| 已保存运行 | 进程退出 / 原 verifier | 全部 2,000 行 hit_tokens 不匹配 | 全部 2,000 行 prompt_tokens 不匹配 | 限定 |
| --- | --- | ---: | ---: | --- |
| no skill | 1 / 1 | 156 | 2,000 | 最后请求超时，用量未知 |
| forced skill | 0 / 0 | 0 | 0 | 一次运行 |
| optional docs、8 POST 上限 | 1 / 1 | 95 | 0 | 后续请求被限 |
| optional docs、12 POST 上限 | 1 / 0 | 0 | 0 | 进程退出 1；拒绝的具体原因未知 |

四组 trace/config 哈希一致；两个全匹配 report 的哈希也一致，但生成程序或推理过程不因此被证明一致。原 verifier 的逐请求断言只抽查 5 个索引并检查聚合/自一致，本次补看了所有已保存行；oracle 本身未接受本轮独立正确性验证。2,000 行同属于一次 episode，不能用于计算跨任务成功率或扩大样本量。

**候选可检验问题**：Agent 交付应否同时报告产物正确、执行是否完成、预算是否受限及未完成请求成本？下一步需在多个不同公开任务上冻结同一合同、比较强基线，并区分异常后恢复与模型质量；既有单次结果不能证明 skills 有因果优势。

## 4. MA-CERD：相同样本上，完整集合匹配与可选动作合法性会给不同答案

独立脚本 [revalidate_ma_cerd.py](revalidate_ma_cerd.py)将保存的 250 个预测按唯一 contract_id 与 Gold 逐项连接；原数据和结果 hash 及计数见 [ma_cerd_revalidation.json](ma_cerd_revalidation.json)。金标准允许集合为 defer+execute+repair 138 条、defer+repair 112 条。

| 输出 | 完整集合精确匹配 | 非空输出是 Gold 子集 | 输出仅为 defer |
| --- | ---: | ---: | ---: |
| 已保存模型集合 | 3/250 | 245/250 | 241/250 |
| 后加简单基线：始终输出 defer | 0/250 | 250/250 | 250/250 |

两种评价回答不同问题：完整集合匹配评价**枚举**，子集合法性评价**候选是否在允许集合内**；始终 defer 在本面板合法，不意味着任务完成、风险低或对用户有用。模型输入包含 simulator relation、样本已曝光，不能用来宣称部署性能。后续若研究可执行决策，须重新定义交付/弃答/副作用/成本和独立参考。

## 5. 工作树归档与剩余现场

- 本机集成 worktree 的 30 个未跟踪文件全部复制到 D:/Documents/Loop_D_assets/neat_20261029/integration_untracked，逐文件 SHA-256 验证并写 manifest，随后只移除工作树里的这些副本；该 worktree 的 Git status 现为 clean。归档包含旧渲染、脚本与结果，不自动变成论文最新版本。
- GB10 C 审阅 worktree 的三个未跟踪文件复制到 /home/testuser/wzh/backups/asset_revalidation_20261029/c_review_untracked，逐项 cmp 和 SHA-256 校验后移除工作树副本；该 worktree 的普通 Git status 现为 clean。其隐藏/忽略的 .omc 运行与记忆文件未触碰，因此不删除 worktree。
- 其余 GB10 历史 worktree 含不同数量的忽略文件，内容和所有权尚未逐项核清；不将 commit 已合并等同于忽略文件可删除。GB10 当前 Loop B 测试日志由其他工作生成，保留。

## 6. 可信度与下一步

1. **近期 Paper E**：优先使用可哈希复算的单叶缩放与 clean-support 解释；核实各操作点后考虑加入更直观的数学示例，保持现有三案例主线。
2. **第二篇 Agent**：已有实验揭示了产物验证和进程完成的分离，但新意需对标现有 benchmark；优先多任务、同信息和总成本的评测合同，观察失败后可否用可靠证据恢复，先进行自然来源资格。
3. **学位材料**：将迁移反例和 MA-CERD 合同错位用作方法论、评价设计或错误分析；未独立验证的启发不作为已成立创新点。

未触碰生产、私钥或共享服务配置。模型/训练账本本轮新增均为 0；旧账本与未知用量原样保留。
