# 方法、公式与理论支撑素材 v1

> 状态：论文素材包，尚未并入统一稿 | 核验日期：2026-09-23
> 作用：为 Evaluate–Distill–Evolve 三阶段补足统一记号、可证明边界和可引用文献。本文不新增实验结果，也不把相邻理论的保证移植成本文保证。

配套 BibTeX：`paper/method_data_references_v1.bib`。规则 replay 方法图：`paper/figures/fig_rule_gate_replay_v1.svg`。

## 1. 最值得采用的理论主线

这篇小论文不宜包装成一个“万能自进化框架”。更稳的理论定位是：**过程证据驱动的数据选择 + 带拒绝的低成本动作预测 + 受独立验证约束的版本化规则更新**。

三个阶段分别对应三类成熟问题：

1. Stage E 是 process supervision / process-level evaluation：最终答案相同，不代表中间过程同样可靠；checkpoint 提供局部可验证证据。
2. Stage D 是 learning with selective prediction：学生不是替代最终验证器，而是在风险约束下决定哪些候选值得送入昂贵验证。
3. Stage R 是 constrained safe update：新规则只有同时满足源任务收益、既有任务回归约束和独立验证约束才进入版本化规则库。

这三类连接能支撑方法设计，但不能直接证明本文在未见分布上的泛化。统计保证仍取决于独立数据、固定阈值和实际样本量。

## 2. 统一问题设定

令长流程样本为 $x_i$，checkpoint 证据向量为

\[
\mathbf e_i=(e_{i1},\ldots,e_{iK}),\qquad
e_{ik}\in [0,1]\cup\{\bot\},
\]

其中 $\bot$ 表示缺失或不可判，不能自动填 0。教师产生规则动作

\[
y_i=(a_i,t_i),\qquad
a_i\in\{\texttt{map\_to},\texttt{hold},\texttt{skip}\},
\]

且 $t_i$ 只在 $a_i=\texttt{map\_to}$ 时有定义。学生 $\pi_\theta(y\mid x)$ 只提出候选或执行验证预筛；最终规则状态为 $R_t$，由确定性门和版本控制更新。

数据角色必须保持

\[
\mathcal D_{\mathrm{proposal}}
\perp \mathcal D_{\mathrm{gate}}
\perp \mathcal D_{\mathrm{sealed}}
\perp \mathcal D_{\mathrm{future}}
\]

的 UID/来源组隔离。这里的 $\perp$ 表示实验设计上的组不重叠，不宣称统计独立已自动成立。

## 3. Stage E：过程证据与过滤函数

### 3.1 分层 checkpoint 聚合

对树节点 $v$，叶节点从证据映射得到分数 $s_v$；内部节点按兄弟归一化权重聚合：

\[
S(v)=\sum_{c\in\mathrm{ch}(v)}
\frac{w_c}{\sum_{j\in\mathrm{ch}(v)}w_j}S(c).
\]

记样本的根节点分数为 $S_i=S(\mathrm{root}_i)$。缺失证据使用预先登记的 $m_v$，同时保留 degraded 标记；它不是“观测到失败”。hinge checkpoint 进入稳定性判定，但不把父节点直接归零。该公式对应现有 `scripts/eval_checkpoint_aggregate.py`，逐行证据见 `docs/experiments/2026-09-20_algorithm1_lines_vs_impl.md`。

### 3.2 可见性与过滤

对缺陷家族 $f$，定义 checkpoint $k$ 的经验可见率：

\[
\widehat V_{k,f}=
\frac{\sum_i \mathbb 1[F_i=f]\mathbb 1[D_{ik}=1]}
{\sum_i \mathbb 1[F_i=f]},
\]

其中 $D_{ik}=1$ 表示缺陷被该 checkpoint 显式检出。蒸馏过滤器写为

\[
z_i=\mathbb 1[\text{provenance}_i=1]
     \mathbb 1[\text{label-review}_i=1]
     \mathbb 1[\text{required hinges pass}]
     \mathbb 1[S_i\ge \kappa].
\]

$z_i=1$ 只表示样本满足预注册过滤合同，不表示标签天然正确；因此 provenance 与独立标签复核不能被 checkpoint 分数替代。

### 3.3 文献锚点

- Lightman et al., *Let's Verify Step by Step*, arXiv:2305.20050：区分 outcome supervision 与逐步 process supervision，并公开 PRM800K。它支持“中间步骤值得单独监督”，不证明本文 checkpoint 树更优。
- Hsieh et al., *Distilling Step-by-Step!*, arXiv:2305.02301：用 rationale 作为额外监督。本文当前只有动作事件而非完整 rationale，因此只作为相邻路线和术语边界，不得把动作蒸馏写成推理链蒸馏。
- Dataset Cartography（Swayamdipta et al., arXiv:2009.10795）与 Confident Learning（Northcutt et al., arXiv:1911.00068）说明训练动态或标签噪声建模可帮助发现困难/歧义/错标样本；二者是后续数据诊断候选，不是当前 checkpoint 过滤结果的理论证明。

## 4. Stage D：动作策略蒸馏与选择性预测

### 4.1 当前可实现的两头监督目标

对动作头和条件目标头，建议采用

\[
\mathcal L_{\mathrm{SFT}}(\theta)=
-\sum_{i:z_i=1}\log \pi_\theta(a_i\mid x_i)
-\lambda_t\sum_{i:z_i=1}\mathbb 1[a_i=\texttt{map\_to}]
\log \pi_\theta(t_i\mid x_i,a_i).
\]

该表达与现有 `map_to / hold / skip + target` 合同一致。类别不平衡应通过 macro-F1、逐类召回和按 UID 聚类区间处理，不能只用 accuracy。

经典温度蒸馏项

\[
\mathcal L_{\mathrm{KD}}=T^2\,
\mathrm{KL}\!\left(p_T^{(T)}(\cdot\mid x)\;\|\;p_\theta^{(T)}(\cdot\mid x)\right)
\]

该经典温度目标的文献锚点为 Hinton, Vinyals, and Dean（arXiv:1503.02531）。只有在教师 logits/概率的来源、温度和保存方式真实存在时才能加入。当前仓库只有动作事件和离散 confidence，**不能伪造软标签**，所以主实验仍应称 SFT 式动作策略蒸馏。

### 4.2 风险—覆盖而不是“准确率最高”

令选择函数 $g_\tau(x)\in\{0,1\}$ 表示候选是否进入完整验证：

\[
\mathrm{Coverage}(\tau)=\mathbb E[g_\tau(X)],\qquad
\mathrm{Risk}(\tau)=
\frac{\mathbb E[\ell(\hat Y,Y)g_\tau(X)]}
{\mathbb E[g_\tau(X)]}.
\]

上式只在 $\mathbb E[g_\tau(X)]>0$ 时定义。预筛器应求“风险不高于 $\alpha$ 时覆盖最大”，或报告完整 risk–coverage 曲线。always-skip 的覆盖为 0，其选择性风险未定义，必须单列为拒答退化基线而不能因“零错误”获胜。Geifman and El-Yaniv（arXiv:1705.08500）以及 SelectiveNet（arXiv:1901.09192）提供了 reject option / risk–coverage 的直接文献锚点。

Conformal Risk Control（Angelopoulos et al., arXiv:2208.02814）允许在交换性等条件下控制单调损失的期望风险，可作为**后续校准扩展**。当前样本量、交换性、阈值冻结和自适应查询条件尚未验证，因此正文最多写“受其启发”，不能声称已有 conformal guarantee。

### 4.3 偏好学习只作条件臂

若以后获得双向、独立且足量的偏好对 $(y_i^+,y_i^-)$，DPO 候选目标为

\[
-\log\sigma\!\left(\beta\left[
\log\frac{\pi_\theta(y_i^+\mid x_i)}{\pi_{\mathrm{ref}}(y_i^+\mid x_i)}-
\log\frac{\pi_\theta(y_i^-\mid x_i)}{\pi_{\mathrm{ref}}(y_i^-\mid x_i)}
\right]\right).
\]

公式来源为 Rafailov et al., arXiv:2305.18290。当前 60 对单向偏 `skip`，不满足主实验门；A3 保持条件臂。

## 5. Stage R：受约束规则更新与回滚

### 5.1 三个状态相关增量

对候选规则 $r_t$ 和当前规则状态 $R_{t-1}^{(a)}$，每个实验臂 $a$ 独立重算：

\[
\Delta_s^{(a)}(r_t)=H(\{x_t\},R_{t-1}^{(a)}\cup\{r_t\})-
H(\{x_t\},R_{t-1}^{(a)}),
\]

\[
\Delta_p^{(a)}(r_t)=H(\mathcal D_{\mathrm{proposal}}\setminus\{x_t\},R_{t-1}^{(a)}\cup\{r_t\})-
H(\mathcal D_{\mathrm{proposal}}\setminus\{x_t\},R_{t-1}^{(a)}),
\]

\[
\Delta_g^{(a)}(r_t)=H(\mathcal D_{\mathrm{gate}},R_{t-1}^{(a)}\cup\{r_t\})-
H(\mathcal D_{\mathrm{gate}},R_{t-1}^{(a)}).
\]

增强固定门为

\[
A_t=\mathbb 1[\Delta_s\ge\tau]
    \mathbb 1[\Delta_p\ge-\epsilon]
    \mathbb 1[\Delta_g\ge-\eta].
\]

这解释了为什么不能把原始臂日志里的 gain/collateral 搬给其他臂：接受历史改变了 $R_{t-1}^{(a)}$，三个增量随状态改变。

### 5.2 两个可证明但有限的性质

**命题 1（累计局部回归预算界）**。若第 $j$ 个被接受更新在其预注册比较池 $\mathcal P_j$ 上满足 $\Delta_p^{(j)}\ge-\epsilon$，且每次增量都在当时状态上重算，则接受 $m$ 次后

\[
\sum_{j=1}^{m}\Delta_p^{(j)}(r_j)\ge-m\epsilon.
\]

证明是对逐步下界求和。只有当所有 $\mathcal P_j$ 都是同一个固定回归池 $\mathcal D_{\mathrm{reg}}$ 时，才有伸缩推论

\[
H(\mathcal D_{\mathrm{reg}},R_m)-H(\mathcal D_{\mathrm{reg}},R_0)
=\sum_{j=1}^{m}\Delta_p^{(j)}(r_j)\ge-m\epsilon.
\]

当前 runner 的 collateral 池会按 source UID 做 leave-one-source-out，因此只能支持第一个累计局部界；若要在正文主张全局伸缩界，GB10 正式协议必须额外冻结同一个 $\mathcal D_{\mathrm{reg}}$。两个版本都只约束开发侧比较集，不推出 sealed test 泛化。

**命题 2（版本回滚不变量）**。令 $B\ge0$ 为预注册 rollback budget，$H_g^*(t)$ 为截至步骤 $t$ 保存过的最佳 gate-validation 快照分数。若每次接受后都检查，且一旦当前分数低于 $H_g^*(t)-B$ 就恢复最佳快照，则每个步骤结束时

\[
H(\mathcal D_g,R_t)\ge H_g^*(t)-B.
\]

证明按“未触发/触发回滚”两种情况直接成立。该不变量已由 `research/phase2_rule_gate_replay.py` 的合成状态分叉与 rollback 测试覆盖；它仍不约束 sealed test，也不等价于在线学习收敛。

SPIBB（Laroche et al., arXiv:1712.06924）在 batch RL 中研究相对基线的安全策略改进，可作为“高不确定时回退基线”的相邻理论。本文不是 MDP 策略学习，不能照搬其安全改进定理。

### 5.3 独立验证也会被用坏

反复观察 gate-validation 再改阈值、规则或 family，会使它逐渐变成开发集。Dwork et al., *Generalization in Adaptive Data Analysis and Holdout Reuse*（arXiv:1506.02629）明确指出自适应复用 holdout 会过拟合。本文最低实现要求是：

- 阈值、查询预算和 rollback budget 先冻结；
- 记录 gate 查询次数与适配历史；
- gate-validation 只决定接受/回滚，sealed test 只在系统冻结后读取一次；
- 超出查询预算时不再声称 gate-validation 是独立证据。

## 6. 统一目标与论文图表

不建议把质量、风险、成本强行压成一个未经校准的总分。主文报告 Pareto 面；仅为分析可定义

\[
J(\pi,R)=Q(\pi,R)-\lambda_h\,\mathrm{Harm}(\pi,R)
-\lambda_c\,\mathrm{Cost}(\pi,R),
\]

其中 $\lambda_h,\lambda_c$ 必须预注册并做敏感性分析，不能按结果挑权重。

- Table 1：A0–A3 的 action macro-F1、target exact、harm、coverage、最坏家族和成本。
- Table 2：七类门的 harmful accept、valid retention、gate coverage/accuracy、查询、回滚和成本代理。
- Figure 3：学生 risk–coverage / quality–cost Pareto。
- Figure 4：共享候选步上的 retained-valid、retained-harmful、rollback 和累计成本。

## 7. 写作时的主张分级

| 级别 | 可以写 | 不能写 |
|---|---|---|
| 已有事实 | checkpoint 聚合实现、历史可见性、已构造机制证据 | 训练后学生提升、完整闭环有效 |
| 仓内软件合同 | 五基线和七臂 replay 的输入/状态/输出约束已测试 | 合成 fixture 的数值是论文结果 |
| 理论推导 | 命题 1 的累计局部界与固定池条件推论、命题 2 的回滚不变量 | 动态池的全局伸缩界、sealed/future 泛化、统计显著性 |
| 文献支持 | 过程监督、选择性预测、安全回退、自适应 holdout 是相邻理论 | 这些文献已经证明本文方法成立 |

## 8. 已核验候选文献

以下元数据于 2026-09-23 通过 arXiv 官方 API 核验；venue 只在 arXiv comment 明示时作为备注，正式入稿前仍需二次核对。

| cite key | 题名 | 年 | 标识 | 用途 |
|---|---|---:|---|---|
| `geifman2017selective` | Selective Classification for Deep Neural Networks | 2017 | arXiv:1705.08500 | 风险—覆盖与拒绝 |
| `geifman2019selectivenet` | SelectiveNet: A Deep Neural Network with an Integrated Reject Option | 2019 | arXiv:1901.09192 | 学习式选择函数 |
| `angelopoulos2022crc` | Conformal Risk Control | 2022 | arXiv:2208.02814 | 有限样本风险控制候选 |
| `dwork2015adaptive` | Generalization in Adaptive Data Analysis and Holdout Reuse | 2015 | arXiv:1506.02629 | gate 反复查询风险 |
| `laroche2017spibb` | Safe Policy Improvement with Baseline Bootstrapping | 2017/2019 | arXiv:1712.06924 | 高不确定时回退基线的相邻理论 |
| `hinton2015distilling` | Distilling the Knowledge in a Neural Network | 2015 | arXiv:1503.02531 | 经典温度蒸馏目标 |
| `lightman2023verify` | Let's Verify Step by Step | 2023 | arXiv:2305.20050 | 过程监督 |
| `hsieh2023distilling` | Distilling Step-by-Step! | 2023 | arXiv:2305.02301 | rationale 蒸馏对照边界 |
| `rafailov2023dpo` | Direct Preference Optimization | 2023 | arXiv:2305.18290 | 条件 DPO 公式 |
| `swayamdipta2020cartography` | Dataset Cartography | 2020 | arXiv:2009.10795 | 数据难度/歧义诊断候选 |
| `northcutt2019confident` | Confident Learning | 2019/2021 | arXiv:1911.00068 | 标签错误审计候选 |
| `xia2024less` | LESS: Selecting Influential Data for Targeted Instruction Tuning | 2024 | arXiv:2402.04333 | 大论文的数据选择扩展 |

## 9. GB10 后续验证卡

1. 用正式数据重算七臂的每步状态增量，检查命题 1 的逐项恒等式和命题 2 的每步不变量；任一不成立即软件/口径错误。
2. 在 proposal/dev 上画 risk–coverage；阈值冻结后才读取 gate-validation，不用 sealed test 选阈值。
3. 记录 gate 查询预算；若发生策略/阈值改动，旧 gate 结果降为 adaptive development evidence。
4. A1/A2 只采用两头 SFT 主目标；教师 soft targets 不存在时不启用 KL，双向偏好不足时不启用 DPO。
5. 理论命题只做实现一致性与开发侧局部安全界说明；固定池伸缩推论只有在额外冻结同一 $\mathcal D_{\mathrm{reg}}$ 后才可启用，最终结论仍由 UID 聚类区间、最坏家族和 sealed test 决定。
