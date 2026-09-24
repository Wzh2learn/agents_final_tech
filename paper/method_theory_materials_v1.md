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

其中 $D_{ik}=1$ 表示缺陷被该 checkpoint 显式检出。先定义所有训练臂共享的资格门

\[
u_i=\mathbb 1[\text{proposal/train}_i=1]
     \mathbb 1[\text{provenance}_i=1]
     \mathbb 1[\text{label-review}_i=1]
     \mathbb 1[\text{licence}_i=1].
\]

在共同资格母池上，checkpoint 过滤器才写为

\[
z_i=\mathbb 1[\text{required hinges pass}]
     \mathbb 1[S_i\ge \kappa].
\]

$u_i=1$ 是 A1/A2 的共同输入资格，$z_i=1$ 只表示样本进一步满足预注册 checkpoint 过滤合同，不表示标签天然正确。A1 使用 $u_i=1$ 的母池，A2 使用其中 $u_i z_i=1$ 的子集；size/token/group-matched 对照也只能从同一 $u_i=1$ 母池构造。这样才能把来源/标签合法性与 checkpoint 的增量作用分开。

### 3.3 文献锚点

- Lightman et al., *Let's Verify Step by Step*, arXiv:2305.20050：区分 outcome supervision 与逐步 process supervision，并公开 PRM800K。它支持“中间步骤值得单独监督”，不证明本文 checkpoint 树更优。
- Hsieh et al., *Distilling Step-by-Step!*, arXiv:2305.02301：用 rationale 作为额外监督。本文当前只有动作事件而非完整 rationale，因此只作为相邻路线和术语边界，不得把动作蒸馏写成推理链蒸馏。
- Dataset Cartography（Swayamdipta et al., arXiv:2009.10795）与 Confident Learning（Northcutt et al., arXiv:1911.00068）说明训练动态或标签噪声建模可帮助发现困难/歧义/错标样本；二者是后续数据诊断候选，不是当前 checkpoint 过滤结果的理论证明。

### 3.4 过程错误定位与自动标签的边界

ProcessBench（Zheng et al., arXiv:2412.06559）把任务定义为定位数学推理中最早错误步骤或判定全程正确；Math-Shepherd（Wang et al., arXiv:2312.08935）探索不依赖人工逐步标注的过程监督。这两件说明“过程错误位置”可以成为独立监督目标，但不能直接当作本文金融表格流程的训练集：任务域、错误本体和标签生成机制都不同。它们适合支撑 Stage E 的问题重要性，以及作为“自动过程标签需独立核验”的反例边界。

## 4. Stage D：动作策略蒸馏与选择性预测

### 4.1 当前可实现的两头监督目标

对动作头和条件目标头，令 $w_i^{(1)}=u_i$、$w_i^{(2)}=u_i z_i$ 分别表示 A1 和 A2 的样本权重，建议采用

\[
\mathcal L_{\mathrm{SFT}}^{(b)}(\theta)=
-\frac{\sum_i w_i^{(b)}\log \pi_\theta(a_i\mid x_i)}
{\sum_i w_i^{(b)}}
-\lambda_t
\frac{\sum_i w_i^{(b)}\mathbb 1[a_i=\texttt{map\_to}]
\log \pi_\theta(t_i\mid x_i,a_i)}
{\sum_i w_i^{(b)}\mathbb 1[a_i=\texttt{map\_to}]}.
\]

两项分别按其有效样本数归一化；若一个 batch 中没有 `map_to`，目标头项定义为 0，而不是除以 0。$\lambda_t$ 是归一化后目标头相对动作头的权重，须在 proposal 内部 dev 上预注册并在 A1/A2 间保持一致；不得让 A2 因 `map_to` 占比变化而隐式改变损失尺度。该表达与现有 `map_to / hold / skip + target` 合同一致。类别不平衡应通过 macro-F1、逐类召回和按 UID 聚类区间处理，不能只用 accuracy。

经典温度蒸馏项

\[
\mathcal L_{\mathrm{KD}}=T^2\,
\mathrm{KL}\!\left(p_T^{(T)}(\cdot\mid x)\;\|\;p_\theta^{(T)}(\cdot\mid x)\right)
\]

该经典温度目标的文献锚点为 Hinton, Vinyals, and Dean（arXiv:1503.02531）。只有在教师 logits/概率的来源、温度和保存方式真实存在时才能加入。当前仓库只有动作事件和离散 confidence，**不能伪造软标签**，所以主实验仍应称 SFT 式动作策略蒸馏。

### 4.2 风险—覆盖而不是“准确率最高”

令 $v_\tau(x)\in\{0,1\}$ 表示学生是否把一个可执行候选送入冻结的完整验证器；$v_\tau(x)=0$ 只表示不提出/暂缓该候选，**不表示学生直接接受规则**。送检覆盖与送检前候选条件风险为

\[
\mathrm{VerificationCoverage}(\tau)=\mathbb E[v_\tau(X)],\qquad
\mathrm{Risk}_{\mathrm{student}}(\tau)=
\frac{\mathbb E[\ell_s(\hat Y_s,Y)v_\tau(X)]}
{\mathbb E[v_\tau(X)]}.
\]

上式只在 $\mathbb E[v_\tau(X)]>0$ 时定义。预筛器应求“候选风险不高于 $\rho_{\max}$ 时送检覆盖最大”，同时报告有效候选召回、漏失有效规则率和验证成本；所有 $v_\tau=1$ 的候选仍须经过确定性 gate。$\rho_{\max}$ 是送检前候选风险上限，不再与统计显著性水平共用 $\alpha$。always-skip 的送检覆盖为 0，其条件风险未定义，必须单列为退化基线而不能因“零错误”获胜。Geifman and El-Yaniv（arXiv:1705.08500）以及 SelectiveNet（arXiv:1901.09192）只提供选择函数的相邻文献锚点，不赋予绕过本文验证门的权限。

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

### 4.4 `hold`、拒答与送检必须分开

本文有两个容易混淆的决定：`hold` 是任务标签，表示当前证据下无法唯一决定规则动作；verification routing 是系统路由，表示学生是否提出候选并送交昂贵的完整验证。令 $c_v(x)$ 为实测验证成本、$\ell_v$ 为冻结验证器仍可能产生的损失、$\ell_{\mathrm{miss}}$ 为未送检而漏掉有效规则的损失，可写成本敏感风险

\[
\mathcal R_{\mathrm{route}}(\theta,\phi)=
\mathbb E\!\left[v_\phi(X)\{\ell_v(V(X),Y)+\lambda_c c_v(X)\}
+(1-v_\phi(X))\ell_{\mathrm{miss}}(X,Y)\right].
\]

这与 learning to defer（Mozannar and Sontag, arXiv:2006.01862）同属“模型与专家/验证器分工”的问题，但本文验证器是冻结的确定性 checkpoint/gate，而不是默认正确的人类专家；学生没有直接持久化规则的分支。`always-skip`、输出 `hold`、不提出候选和候选送检必须分列，否则零送检会伪装成零风险。

若学生输出置信 $q_\theta(x)$，先在 proposal 内部 dev 上做校准；Guo et al.（arXiv:1706.04599）支持 temperature scaling 作为候选基线，但校准改善不等于排序或风险保证。主判据仍是 UID 级候选风险—送检覆盖、有效候选召回、漏失有效规则率、最坏家族和 sealed test，而不是单独 ECE。

### 4.5 离线蒸馏与 on-policy 蒸馏的边界

GKD（Agarwal et al., arXiv:2306.13649）与 MiniLLM（Gu et al., arXiv:2306.08543）针对学生生成分布与固定教师样本之间的 exposure mismatch，使用学生自生成输出再获得教师反馈。它们是重要强基线，但不应偷偷混入当前 A1/A2：当前主实验是冻结离线动作数据上的同预算 SFT。若以后增加 on-policy 臂，必须单独登记教师调用预算、学生 rollout 来源、过滤器版本和 UID 层，且学生生成数据不得接触 gate/sealed/future。

数据选择方面，Influence Functions、Data Shapley、example forgetting、GraNd/EL2N 与 LESS 分别提供影响度、价值分摊、训练遗忘、早期梯度/误差和目标化 instruction selection 视角。它们适合做大论文的选择器对照；小论文优先保留可解释的 checkpoint filter，并用 size/token/group-matched A1/A2 证明收益不是单纯减量。没有正式训练动态前，不把这些方法写成已实现基线。

## 5. Stage R：受约束规则更新与回滚

### 5.1 三个状态相关增量

对任意数据子集 $\mathcal D$ 和规则状态 $R$，先定义实现一致的效用

\[
U(\mathcal D,R)=\frac{N_{\mathrm{correct}}(\mathcal D,R)-N_{\mathrm{harmful}}(\mathcal D,R)}{N_{\mathrm{total}}(\mathcal D)}.
\]

这里不再用 $H$，避免与历史稿的“字段命中率/field-hit rate”记号冲突。对候选规则 $r_t$ 和当前规则状态 $R_{t-1}^{(a)}$，每个实验臂 $a$ 独立重算：

\[
\Delta_s^{(a)}(r_t)=U(\mathcal G_t,R_{t-1}^{(a)}\cup\{r_t\})-
U(\mathcal G_t,R_{t-1}^{(a)}),
\]

\[
\Delta_p^{(a)}(r_t)=U(\mathcal D_{\mathrm{proposal}}\setminus\mathcal G_t,R_{t-1}^{(a)}\cup\{r_t\})-
U(\mathcal D_{\mathrm{proposal}}\setminus\mathcal G_t,R_{t-1}^{(a)}),
\]

\[
\Delta_g^{(a)}(r_t)=U(\mathcal D_{\mathrm{gate}},R_{t-1}^{(a)}\cup\{r_t\})-
U(\mathcal D_{\mathrm{gate}},R_{t-1}^{(a)}).
\]

$\mathcal G_t$ 是候选 $r_t$ 所属的完整 source-lineage UID 组，而不是单条事件 $\{x_t\}$。因此 collateral 比较必须排除该 UID 的 clean、mutant、轨迹和派生表全组；这与当前 runner 的 leave-one-source-UID-out 实现一致。

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
U(\mathcal D_{\mathrm{reg}},R_m)-U(\mathcal D_{\mathrm{reg}},R_0)
=\sum_{j=1}^{m}\Delta_p^{(j)}(r_j)\ge-m\epsilon.
\]

当前 runner 的 collateral 池会按 source UID 做 leave-one-source-out，因此只能支持第一个累计局部界；若要在正文主张全局伸缩界，GB10 正式协议必须额外冻结同一个 $\mathcal D_{\mathrm{reg}}$。两个版本都只约束开发侧比较集，不推出 sealed test 泛化。

**命题 2（版本回滚不变量）**。令 $B\ge0$ 为预注册 rollback budget，$U_g^*(t)$ 为截至步骤 $t$ 保存过的最佳 gate-validation 快照效用。若每次接受后都检查，且一旦当前效用低于 $U_g^*(t)-B$ 就恢复最佳快照，则每个步骤结束时

\[
U(\mathcal D_g,R_t)\ge U_g^*(t)-B.
\]

证明按“未触发/触发回滚”两种情况直接成立。该不变量已由 `research/phase2_rule_gate_replay.py` 的合成状态分叉与 rollback 测试覆盖；它仍不约束 sealed test，也不等价于在线学习收敛。

SPIBB（Laroche et al., arXiv:1712.06924）在 batch RL 中研究相对基线的安全策略改进，可作为“高不确定时回退基线”的相邻理论。本文不是 MDP 策略学习，不能照搬其安全改进定理。

### 5.3 独立验证也会被用坏

反复观察 gate-validation 再改阈值、规则或 family，会使它逐渐变成开发集。Dwork et al., *Generalization in Adaptive Data Analysis and Holdout Reuse*（arXiv:1506.02629）明确指出自适应复用 holdout 会过拟合。本文最低实现要求是：

- 阈值、查询预算和 rollback budget 先冻结；
- 记录 gate 查询次数与适配历史；
- gate-validation 只决定接受/回滚，sealed test 只在系统冻结后读取一次；
- 超出查询预算时不再声称 gate-validation 是独立证据。

### 5.4 与“自我改进/经验记忆”工作的最近邻差异

Reflexion（Shinn et al., arXiv:2303.11366）、Self-Refine（Madaan et al., arXiv:2303.17651）、ExpeL（Zhao et al., arXiv:2308.10144）和 Agent Workflow Memory（Wang et al., arXiv:2409.07429）分别展示语言反馈迭代、无额外训练自修正、跨任务经验抽取和可复用 workflow 记忆。它们支持“经验可以外化并复用”，但不替本文证明独立验证、回归预算或版本回滚。

更直接的最近邻来自 schema matching：Valentine（Koutras et al., arXiv:2010.07386）给出开放匹配基准与经典 matcher；Magneto（Liu et al., arXiv:2412.08194）已组合小模型候选检索和大模型重排；Matchmaker（Seedat and van der Schaar, arXiv:2410.24105）已提出自改进 LLM schema-matching program；Prompt-Matcher（Feng et al., arXiv:2408.14507）已研究预算内 correspondence verification 与不确定性更新。因此本文**不能**声称首次“小模型+大模型”“自改进 schema matching”或“验证后更新”。可守住的候选差异是：checkpoint 证据先过滤蒸馏数据，学生只做候选/预筛，规则写入由独立 gate-validation、sealed 防火墙和版本回滚共同约束。该差异仍须由 RQ2–RQ4 实验证明。

## 6. 统一目标与论文图表

不建议把质量、风险、成本强行压成一个未经校准的总分。主文报告 Pareto 面；仅为分析可定义

\[
J(\pi,R)=Q(\pi,R)-\lambda_h\,\mathrm{Harm}(\pi,R)
-\lambda_c\,\mathrm{Cost}(\pi,R),
\]

其中 $\lambda_h,\lambda_c$ 必须预注册并做敏感性分析，不能按结果挑权重。

- Table 1：A0–A3 的 action macro-F1、target exact、harm、coverage、最坏家族和成本。
- Table 2：七类门的 harmful accept、valid retention、gate coverage/accuracy、查询、回滚和成本代理。
- Figure 3：学生候选风险—送检覆盖 / quality–verification-cost Pareto。
- Figure 4：共享候选步上的 retained-valid、retained-harmful、rollback 和累计成本。

### 6.1 两种伤害分母必须分开

规则级描述量定义为

\[
\widehat h_{\mathrm{rule}}=
\frac{\#\{\text{accepted harmful rules}\}}
{\#\{\text{accepted rules}\}},
\]

它回答“已接受规则里有多少有害”，但候选规则共享 UID，不能直接套独立二项区间。UID 级安全量则先把同一 lineage UID 的所有候选合并：对 $n$ 个独立 source UID，令 $K$ 为至少出现一次 Q3 harmful accept 的 UID 数，定义 $\widehat h_{\mathrm{uid}}=K/n$。若 $K<n$，显著性水平记为 $\alpha_{\mathrm{sig}}$，其一侧 Clopper–Pearson 上界为

\[
U_{1-\alpha_{\mathrm{sig}}}=
\operatorname{Beta}^{-1}(1-\alpha_{\mathrm{sig}};K+1,n-K).
\]

当 $K=0$ 时仍有 $U_{1-\alpha_{\mathrm{sig}}}=1-\alpha_{\mathrm{sig}}^{1/n}>0$；所以“0 次伤害”只能与有效 UID 数和置信上界一起报告。主安全门使用 UID 级上界，规则级比例只作描述或使用另行预注册的 UID 聚类推断，二者不得共用一个 harmful accept rate 名称。

### 6.2 确认性推断合同

- A1/A2 使用同一 seed 列表和同一 lineage UID：点估计对 seed×UID 单元等权，区间采用“先成对重采样 seed，再在 seed 内成对重采样 UID”的两阶段 bootstrap；不得把所有事件或 token 平铺成 iid。
- 质量非劣使用 A2−A1 的单侧下置信界与 $-\delta_q$ 比较；安全非劣使用 A2−A1 的单侧上置信界与 $\delta_h$ 比较；retention 非劣同理与 $-\delta_r$ 比较。“不显著”不等于非劣。
- RQ2 的确认性族固定为质量非劣、安全非劣和风险约束下覆盖；RQ3 的确认性族固定为 UID-any-harm 与 valid-rule retention。各族内部使用 Holm，次指标和逐家族结果标 exploratory。
- 阈值只能在 proposal/train 的内部 dev 上按“满足 $\rho_{\max}$ 后覆盖最大”选择；并列时先选 action macro-F1 高者，再选更保守阈值。gate-validation 只接受/回滚，sealed test 只在模型、阈值、规则和分析代码冻结后揭封一次。
- $\delta_q,\delta_h,\delta_r,\rho_{\max},\alpha_{\mathrm{sig}}$、seed 列表、每角色×家族最低 UID 和 MDE 都必须在 Git 外冻结收据中由人批准；当前仍为 UNSET，不能由软件默认值冒充论文预注册值。

Clopper–Pearson（1934）和 Holm（1979）提供统计工具，不会自动解决重复查询 gate 的适应性偏差；候选集合、查询预算或阈值发生结果驱动变化时，必须更换独立 holdout 或把证据降级为 exploratory。

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

### 8.1 新增的直接方法与统计锚点

| cite key | 题名 | 年 | 标识 | 用途/边界 |
|---|---|---:|---|---|
| `mozannar2020defer` | Consistent Estimators for Learning to Defer to an Expert | 2020 | arXiv:2006.01862 | 送检/专家分工；不把验证器假设成完美 |
| `guo2017calibration` | On Calibration of Modern Neural Networks | 2017 | arXiv:1706.04599 | temperature scaling 候选；不替代 risk–coverage |
| `agarwal2023gkd` | On-Policy Distillation of Language Models | 2023 | arXiv:2306.13649 | 学生分布蒸馏强基线；当前离线主实验不混用 |
| `gu2023minillm` | MiniLLM: On-Policy Distillation of Large Language Models | 2023 | arXiv:2306.08543 | on-policy KD 近邻；须另开预算/数据合同 |
| `zheng2024processbench` | ProcessBench | 2024 | arXiv:2412.06559 | 过程错误定位；数学域不可直接移植 |
| `wang2023mathshepherd` | Math-Shepherd | 2023 | arXiv:2312.08935 | 自动过程标签；仍需独立正确性审计 |
| `koh2017influence` | Understanding Black-box Predictions via Influence Functions | 2017 | arXiv:1703.04730 | 训练样本影响度候选 |
| `ghorbani2019datashapley` | Data Shapley | 2019 | arXiv:1904.02868 | 数据价值候选，计算成本高 |
| `toneva2018forgetting` | An Empirical Study of Example Forgetting | 2018 | arXiv:1812.05159 | 训练动态数据诊断候选 |
| `paul2021datadiet` | Deep Learning on a Data Diet | 2021 | arXiv:2107.07075 | GraNd/EL2N 选择候选 |
| `clopper1934confidence` | The Use of Confidence or Fiducial Limits Illustrated in the Case of the Binomial | 1934 | DOI:10.1093/biomet/26.4.404 | 零伤害有限样本上界 |
| `holm1979simple` | A Simple Sequentially Rejective Multiple Test Procedure | 1979 | JSTOR stable:4615733 | 冻结确认性假设族校正；该 stable identifier 不是 DOI |

### 8.2 最近邻系统与数据工作

| cite key | 题名 | 年 | 标识 | 对本文的压力 |
|---|---|---:|---|---|
| `koutras2020valentine` | Valentine | 2020 | arXiv:2010.07386 | 已有开放 schema-matching 基准与经典 matcher |
| `liu2024magneto` | Magneto | 2024 | arXiv:2412.08194 | 已有 SLM 检索 + LLM 重排与合成训练数据 |
| `seedat2024matchmaker` | Matchmaker | 2024 | arXiv:2410.24105 | 已有自改进 LLM schema-matching program |
| `feng2024promptmatcher` | Prompt-Matcher | 2024 | arXiv:2408.14507 | 已有预算内 correspondence verification |
| `shinn2023reflexion` | Reflexion | 2023 | arXiv:2303.11366 | 语言反馈式迭代，不等于安全规则持久化 |
| `madaan2023selfrefine` | Self-Refine | 2023 | arXiv:2303.17651 | 无训练自修正，不等于独立 gate |
| `zhao2023expel` | ExpeL | 2023 | arXiv:2308.10144 | 跨任务经验抽取，不提供本文回归保证 |
| `wang2024awm` | Agent Workflow Memory | 2024 | arXiv:2409.07429 | workflow 记忆近邻，不提供 sealed 防火墙 |

### 8.3 新增数据候选论文

| cite key | 数据/论文 | 年 | 标识 | 当前角色 |
|---|---|---:|---|---|
| `chen2022convfinqa` | ConvFinQA | 2022 | arXiv:2210.03849 | FinQA 同源会话扩展，不作独立 test |
| `hulsebos2021gittables` | GitTables | 2021 | arXiv:2106.07258 | 自然表头 proposal/pretrain only |
| `hulsebos2019sherlock` | Sherlock | 2019 | arXiv:1905.10688 | 语义类型 baseline only |
| `chen2020hybridqa` | HybridQA | 2020 | arXiv:2004.07347 | 大论文跨域过程压力候选 |
| `chen2020ottqa` | OTT-QA | 2020 | arXiv:2010.10439 | 大论文检索重负载压力候选 |

## 9. GB10 后续验证卡

1. 用正式数据重算七臂的每步状态增量，检查命题 1 的逐项恒等式和命题 2 的每步不变量；任一不成立即软件/口径错误。
2. 在 proposal/dev 上画 risk–coverage；阈值冻结后才读取 gate-validation，不用 sealed test 选阈值。
3. 记录 gate 查询预算；若发生策略/阈值改动，旧 gate 结果降为 adaptive development evidence。
4. A1/A2 只采用两头 SFT 主目标；教师 soft targets 不存在时不启用 KL，双向偏好不足时不启用 DPO。
5. 理论命题只做实现一致性与开发侧局部安全界说明；固定池伸缩推论只有在额外冻结同一 $\mathcal D_{\mathrm{reg}}$ 后才可启用，最终结论仍由 UID 聚类区间、最坏家族和 sealed test 决定。

## 10. 三阶段形式化状态与开放问题清单（2026-09-24 加记）

本节只登记「已经形式化到什么程度」与「明确未形式化 / 未证明的部分」，不引入任何新数字、新命题或新判据；
每条均回指既有载体。开放问题与 `paper/teacher_review_finalization_v1.md` 的回填位、开题 §5.6 的门一一对应。

| 对象 | 已形式化内容 | 载体 | 未形式化 / 未证明部分 |
|---|---|---|---|
| 检查点森林与聚合 | 递归分数 S(n)、兄弟归一化权重、稳定性判据（≥90% 叶过阈 + hinge ≥7）、按树缺失分（parse 0 / qa 5） | 本文 §3.1、`config/eval_checkpoint_trees.json`、Algorithm 1 对位表 | 无（实现与论文逐行对位已存档） |
| 可见性三分类与剖面 | V_ckpt / V_proto、静默吸收、盲区 vs 无效变异体、家族剖面 | 大论文第 2 章 §2.9、`logs/graph/eval/t2_visibility_sensitivity.json` | 无 |
| matched-FPR 比较与仿射等价 | 校准阈值定义、比较协议；仿射等价是**单 varying leaf 实例化下的经验发现**（退化情形），不是定理 | 小论文 §5.2、`logs/graph/eval/d3_matched_fpr_stage_a.json` | 多叶响应下的一般性条件未证明 ⇒ 开放问题 OP-1 |
| fail-closed 合同语义 | 双结局机器合同、READY ≠ DATA_GO、哈希绑定与跨工件一致性（D11 校验） | `research/phase1a_data_contract.py`、`research/phase1a_learnability_baselines.py` | 无 |
| Stage D 风险边界 | 仅第一个累计局部界（本文命题载体）；无 conformal guarantee；不等价于在线学习收敛 | 本文 §4、§5.2 | 动作策略蒸馏下的学生风险上界未证明 ⇒ OP-2 |
| Stage R 门语义 | gain–collateral 双门 + 独立 gate-validation 作为判定规则；机制级证据 7/7 与 5/5 拒绝 | `research/phase2_rule_gate_replay.py` 合同、小论文 §5.5 | 无有害累积 / 收敛类定理 ⇒ OP-3；功效与强基线未闭合 ⇒ OP-4 |
| 纵向维度 | future replay 协议 schema（获取时间、来源约束、分层规则、不回流） | `paper/dataset_protocol_v1.md` | 获取与哈希绑定未完成 ⇒ OP-5（容忍 `LONGITUDINAL_EVIDENCE_UNAVAILABLE`） |

开放问题（与门 / 回填位对应）：

- **OP-1**：仿射等价在多输入响应叶下是否保持。前置：第二数据流 + 第二 scorer（对应 BF-3 / 复审恢复判据）。
- **OP-2**：动作策略蒸馏的学生风险上界。前置：SOURCE_GO→MODEL_GO 全过 + 独立验收（对应 BF-1）。
- **OP-3**：受控规则累积的无有害累积性质。前置：Phase 2 门 + 独立 gate-validation（对应 BF-2）。
- **OP-4**：H3a 类假设的功效闭合（250–500 有效 UID 目标）。前置：数据批准；达不到则降 exploratory，不改检验方法。
- **OP-5**：future replay 的获取与哈希绑定。前置：协议执行；缺失不阻塞机械预检。

纪律：任何开放问题在对应门通过之前**不得**在正文中以定理、已证性质或已得结果的形式出现；
回填时只允许新增小节或替换显式占位句，不得回改已验收段落的数字。
