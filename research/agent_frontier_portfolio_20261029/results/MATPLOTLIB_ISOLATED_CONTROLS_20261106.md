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

## 输入形成与冻结

经验构造代码`b14a66efc39dc145603e092a205651cb173d9382`；未改source候选、raw或completed。普通历史含36个真实工具动作（6项输入、16项输出按既有规则截取）及完整1543字符实际diff，无遗漏路径。结果卡和历史都原样保留source问题probe，而非只保留通过数。普通skill真实形成1POST：16,720输入＋873输出＝17,593tokens、25.598秒，正常stop；未人工润色。

| 冻结输入 | 字节 / 行 | SHA-256 |
| --- | --- | --- |
| 普通源历史 | 40,685 /405 | `e938ce8a8491ef61b0a288d9d4cbca5cf31caded5a3f62e07fb96221fec69a82` |
| 透明结果卡 | 2,464 /39 | `5d378a3bcfe9e89c648bb40614d9558a0b24bc0727e46ef03e8c1263e15405ad` |
| 普通生成skill | 3,343 /26 | `39de8e7bcca11549d0a20e336288124e28e24c80514d7110a6e2b198a7e5869a` |

`metadata.json` SHA `37391e162e8757771ef6f14edf2bea8ff48068c96bcd55bb53b71677e19991c4`，形成账本 SHA `76bf7fb691fe9e5c52975a7bdd3750283052bf659ab9fc25c426a0cad116f3f3`；`target_input_freeze.json` SHA `25aa75391f7966c2216c0169345f80d520ef0adc56908701a9e8659eae465a2a`在首个target POST之前创建。四臂均绑定同一冻结输入、源episode、target源码/题面、投影和采样配置；每臂另有6MB请求体总限额。三经验臂均一次read逐行完整读取，没有索引覆盖却内容截断的现象。这里的“普通历史”仍是有声明截取的36动作摘要，不等于完整原始轨迹。

## 目标结果与成本

| 目标输入 | 关键测试 | 冻结回归 | POST | reported tokens（含缓存） | 未缓存输入 / 输出 | 自动计时秒 |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 无历史 | 1/1 | 150/150 | 18 | 289,977 | 21,054 /4,659 | 119.57 |
| 透明结果卡 | 1/1 | **149/150** | 45 | 874,724 | 26,072 /12,917 | 283.49 |
| 普通源历史 | 1/1 | 150/150 | 16 | 455,172 | 33,180 /3,343 | 124.60 |
| 普通生成skill | 1/1 | 150/150 | 14 | 345,310 | 26,649 /3,700 | 126.12 |

四臂Agent均exit0、未达请求帽。原题PDF/PNG均无异常并通过预设文件头/画布/像素检查；这些不是完整视觉金标。**结果卡不算完整成功**：它覆盖`PathPatch3D.get_path`返回未投影的`_original_path`，虽然目标报错消失，却使既有`test_arc_pathpatch[png]`图形回归失败（RMS约5.118）；probe包围框也异常增大。该包围框只是诊断线索，没有事后新增评分标准。其他三臂的预设原题观测与参考数值一致。

判断：本次普通skill少于无历史4POST，但未缓存输入输出合计由25,713增至30,349，reported tokens也更高，耗时未观察到改善；不能用请求数一项认证净成本收益。普通历史同样未改善完成率。结果卡这次引入回归值得继续归因，但一个seed不能归因为这种经验形式的一般效应。完整历史更强、普通skill更强或无历史更强，均需要按任务和总成本检验，不能预先指定。

**2026-11-10 原始轨迹尸检。** 结果卡臂将`get_path()`无条件改为返回原始二维路径，自己编写测试要求它返回原始路径；测试中矩形顶点数先误写4，再根据实际输出改为5。其后自建6项通过，原题也通过，但独立冻结回归中的`test_arc_pathpatch[png]`失败（RMS约5.118，149/150通过）：绘图后仍返回原始路径，与投影后的绘图行为冲突。轨迹未见该Agent运行这项回归；结果卡仅含来源事实与修改路径，没有写上述修复规则，因此不能断定是来源经验导致误修。无历史、普通历史和skill臂在同一目标独立评分均通过。这给出可研究的真实断点：自编测试可能把未确认的假设当成要求，即使绿灯也不足以证明未破坏既有行为；[ExecCritic](https://arxiv.org/html/2609.09133v1)已研究类似测试—修复耦合，不能把这条观察本身当新方法。

**后续同现场反馈对照（生成前冻结）**：只对上述已曝光失败工件做一次两臂开发性续修：两臂均拿到相同旧源码、原题、自编测试、实际回归失败信息及相同OpenCode工具、模型与预算；比较普通反馈和要求整理同一事实的约束清单。Qwen3.6-35B-A3B、seed7201、65536/16384上下文/输出，每臂最多16 POST/900秒，顺序普通→清单；恢复冻结测试分别报告原题、已暴露回归和其余回归。此题不是盲确认，一次格式对照也不是经验学习方法或新机制。私有`feedback_repair_pair_20261110_v1/PLAN.json` SHA `8b2b40d6bbe42aaf6c9997b9f74aeed13dd2f982bb3424cacf812e13b44f1824`，驱动SHA `6f7c8588f59e312f7bcecb1d82e138de635ec0c3baf610c0721a10c46d32591c`；准备阶段逐项核对共同输入、两臂唯一提示差及脚本可编译，未消耗模型。

**两臂结果与一个额外核验**：普通反馈臂7 POST后一次请求超时，退出1、无编辑；原题1/1，回归149/150，最后请求usage未知。清单臂12 POST正常退出，先实际重现既有绘图回归失败，随后将`get_path`改为有投影路径时使用投影路径、否则使用原路径；原题1/1、回归150/150，原题PDF/PNG探针通过。这是实际OpenCode＋本地模型续修成功，不是人工补丁。普通臂6次完整报告156,963 tokens（含缓存110,479）＋1次未知；清单臂352,671 tokens（含缓存287,263），无训练。原始SUMMARY SHA `7d0677f8b0f04b28dc790ecc6be2e4ca812f34a62aec13bb9ad5488fee2b3f74`，两臂receipt SHA分别`7d9aecb4654042cdbe1b02bf22382cbb13cb1701b7461112bfd29ea156c86b6f` / `b7f38d23d73fe855b1c64cfcce9308c06483004fcd66bad36cb12751b608b4a8`。普通臂超时、两臂顺序和缓存不同，不能据此把成功归因于清单。为排除简单反馈本身足够这一关键解释，追加至多一次相同普通反馈、相同资源/seed的复跑；不改提示，不再追加同题变体。该回归已用于反馈，评分通过不是独立确认。

**普通反馈复跑结果**：预备时核对生成脚本仅替换attempt路径，初始代码、普通反馈及模型参数不变；运行顺序和缓存状态仍不同。私有`freeform_recheck/PLAN.json` SHA `a06a1adb6106976ff7e10183e811b68b7fd791ab5435cdad19fc10f1ba765ec6`。真实Agent 15 POST、正常退出，自主复现绘图回归后将`get_path`改为`getattr(self, '_path2d', self._original_path)`，原题1/1、回归150/150及PDF/PNG探针通过。474,716 tokens含缓存403,847，未缓存输入66,543、输出4,326，146.73秒；receipt SHA `83b7afb7a2e96c4c48ce2c0d4943eb8274f444ed743b2f9efc734dff6326b3b2`，result SHA `49656d1c92660cd9647fd78f06527a4248108f2d2400214e3735c8f4ef8df9d1`。两次成功说明同一现场中**普通真实反馈也足够达到原冻结评分**，清单尚无已证明的总体增益。连同首次超时，两臂＋复跑共34 POST、984,350已知tokens＋1次未知usage，缓存801,589为已知token子集；训练0。停止该题提示变体，扩其他来源。

**后验旧状态探针，零模型。** 用原版代码实际创建并绘制`PathPatch3D`，此时有`_path2d`而无`_original_path`，原版`get_path`可用；将对象序列化后在两个独立新进程分别加载两份真实Agent修复。普通反馈生成的`getattr`写法先求默认值，因缺少`_original_path`抛`AttributeError`；清单臂的条件分支返回已有投影路径。两个候选除该方法外源码逐字相同；原始工件hash前后不变。私有`old_version_pickle_subprocess_v1/RESULT.json` SHA `5139e813ba77fea83865533c6e43dd8c8cc6bccb6d344d236a066ca25419dede`，驱动SHA `3d5a5ecfb24186c53bcd0cd9ddbeca2b853cbe6eadf23c8a1bbf72c5f4697338`。这是事后挑选的一种旧对象状态，不证明Matplotlib承诺跨版本pickle兼容，也不能证明清单普遍优于普通反馈；它表明原150项通过不足以覆盖此状态，为后续经验适用边界和保持历史行为提供可复验开发素材。

target合计93POST/1,965,183tokens，含缓存1,833,609、未缓存输入106,955、输出24,619。连同新source及skill形成，本批**124POST/2,789,460tokens**，含缓存2,594,932、未缓存输入161,465、输出33,063；0训练、0额外judge、0付费科学API。已有自然历史的增量使用成本与为研究专门采集source的全成本应分别比较；source若是原工作流中的必做任务，属于共同工作量，不能只向某一臂重复收费。运行次序/缓存/共享机器影响时间，单次几秒差不作稳定速度结论。

## 复核与接续

| target completed | SHA-256 |
| --- | --- |
| none | `11ef85cf8f3fa89df4a8e68af9ffe893daeb939ee6c2050ba751648aa78caca5` |
| feedback_card | `3e193b8b887b0ee0ccba093ac4d0e28e8d801c2e09edfff6b56137319935b2d8` |
| source_history | `745ca7dc7415f361b6c97b66d8b805d9c71dd4b8d5e52021447e952a677be13c` |
| generated_skill | `4d3428376e59d869ac6d0b60653dcbf34ab4f44f413a8c0fed671d89d7a21f2a` |

私有`target_batch.completed.json` SHA `b91bcd5f1e261d754aaf46565084ea4e67881f995537c0e877d58092009d35b0`；各case保留原始响应、采样记录、候选、恢复冻结测试后的评分和自动账本。一次有界独立AI只读复核核对了共同配置/冻结输入、渲染检查边界、149/150回归及成本求和，相符；不是人工视觉金标。

122项raw/回执/输入/评分日志另存审阅包，本机`D:/Documents/Loop_D_assets/agent_learning_20261106/matplotlib_isolated_controls_20261106.tar.gz`与GB10私有`evidence_packets_20261106/matplotlib_isolated_controls/`同一包；680,295bytes，SHA `0d88f64e6585429f604fa63195c22e4c4b071a1251591d6d4a39ebf2d5d2b2e9`。本机逐成员复核122项hash相符；不含完整源码checkout、权重或可独立运行的环境，原始大现场继续留GB10，包不入Git。

本批是一个已曝光开发目标、四种输入条件，151个测试不是151个独立任务。没有新训练方法或泛化确认。下一检查点：复用已验证的Astropy隔离投影，从新source重做同配置对照，检验旧历史复用成本信号是否保留；如果无历史也稳定完成，则换更有挑战的自然任务或小模型，不在此简单面板上堆训练。

接续：上述Astropy复验已完成，[结果及下一动作](ASTROPY_ISOLATED_CONTROLS_20261106.md)单独收录，旧检查点不作为现役待办。
