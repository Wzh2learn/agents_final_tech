# Matplotlib：隔离依赖后的真实经验对照

> 2026-11-06 | 当前开发批次。事前执行合同及运行资格见[资格记录](MATPLOTLIB_QUALIFICATION_20261106.md#隔离批次执行合同在首次新生成前写入)。旧暴露环境source与成本保留，不进入本批输入。

## 问题与配置

检验从真实source修复形成的普通历史、反馈卡或普通skill，能否改善不同后续问题的完成或总成本。source为23562，target为27361；题面、版本、评分和时序沿资格记录。source执行代码`ad1b4ed566da59b19b195868b3e58626d25941d2`；actor可读runtime/deps固定manifest `e63a69c6c719bdcc56aa8d08b7ba7635de6bafe90f826b51b7eda79cdad0f75b`，不含wheel项目Python源码。

Qwen3.6-35B-A3B Q4_K_M，seed7201、temperature0.2、context65536/output16384；每episode48转发POST/1500秒，串行执行。比较无历史→透明结果卡→普通源历史→普通skill；输入形成后、target首次调用前冻结。开发团队已见参考，不作为盲确认或预训练隔离。暂未证明任何新方法增量。

## 真实source结果

独立attempt `isolated_dependencies_20261106`：Agent exit0，冻结关键测试2/2、完整回归136/136，原题get_facecolors不再抛异常。补充probe返回颜色数组[1,4]、`finite_rgba_and_shape_stable=false`；这不是原题明确约定的全部语义标准，不能仅凭附加形状检查宣布整个修复非法。经验同时保留窄合同结果与完整probe观测，避免把测试通过编译成所有性质都已验证。

source真实30POST/806,684 reported tokens，含缓存761,323；未缓存输入37,790、输出7,571，自动计时202.546秒。0训练、0judge。旧source的35POST/940,535tokens仍在旧账，不混入本批成功数；比较专门采集经验的总成本时，不能略去本批source形成成本。

私有根：`/home/testuser/wzh/research_evidence/agent_learning_20261030/matplotlib_agent_20261106/attempts/isolated_dependencies_20261106/`。

| source证据 | SHA-256 |
| --- | --- |
| completed | `6ba56215cb514d838f727694c892a2e1d944bc14e37e7b485c551aad3545c957` |
| raw | `9b73a33ba1319e32ee08cd893f75da8905445ef231cdf6e24b51cab595e21b9a` |
| started | `3e963d6fb6c4629b0a2ad4c378c40ca2042481723c76a6f413648e1b44315bb0` |
| harness | `4183dbafd6964175fdd4e5cc3b865bf579aba921b331c00ef6cb1e8cf082c458` |

## 下个检查点

从该次真实执行形成经验和普通skill，核对probe、实际diff和来源绑定，再冻结target输入并执行四臂。target尚未开始。一次任务的成本或测试优势只用于开发判断，后续仍需强简单对照、重复和其他来源。
