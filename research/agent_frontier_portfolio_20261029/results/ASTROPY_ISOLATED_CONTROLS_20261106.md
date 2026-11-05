# Astropy：隔离依赖后的经验复验

> 2026-11-06 | 内部开发复验；目标和参考已在此前开发中见过。原始数据、运行资格与旧比较见[原对照](ASTROPY_PROFILE_CONTROLS_20261106.md)。本页在新source首次生成前创建，原地维护本批结果。

## 执行合同

source为Astropy14995、target为15082，沿用冻结源码/题面/测试、Python3.10/NumPy1.24.3及原生wheel overlay。actor仅挂载已验证的`actor_dependencies_v2`，manifest SHA `32fd788dae461e4eca1f792c9f9e569c70bac9ee7d0befb3335848f98efe1aed`；项目wheel Python源码不进入actor可读面。旧source、skill和目标输出保留，不作为新经验输入。

独立attempt为Astropy自己的`isolated_dependencies_20261106`。source seed7201，target四臂seed7202；temperature0.2，context65536/output16384，每episode48POST/1500秒、请求体总额6MB。先真实执行source，再从实际轨迹、完整补丁与独立反馈生成经验及一次普通skill，冻结输入后按无历史→实际补丁＋源结果→长行安全普通历史→普通skill顺序串行比较。相同数据值的重新排版不作为新方法；记录其与原历史的无损映射。

原始源输入在派生profile前零模型冻结，无需先运行任何target。派生profile须标明在本attempt目标运行前构造，不能沿用旧组“目标出结果后的post-hoc”时间口径。输入与编译账本、source completed/raw绑定；各臂独立工作区。

target分别报告关键测试3项、完整回归132项、原题data/mask/unit实际结果、Agent退出与预算事件；测试通过不替代原题探针。成本分列POST、缓存、未缓存输入/输出及用时，source和技能形成单独记录；共同必做source与专门采集经验的成本分别解释。单任务各一次用于开发，不把测试条数当任务数，不由旧新差异推断依赖隔离的单变量因果效应。

## 源执行与经验形成

新source在`b23836be`代码下完成：Agent exit0，15POST/461,994tokens（含缓存377,887），未缓存输入78,030、输出6,077，自动计时178.309秒。冻结关键测试1/1、回归179/179；原题四种mask组合中，要求检验的data和mask均匹配。source completed SHA `7e0f7b02ca3e204eef2036b664c4ba62928d9a8e1cb8131144a9d2e6c5cded80`，raw SHA `440ffdc0501c5f5e368a033aca40500e44f418280f38dea83ae7e63f29eb8df1`。

源经验14个真实工具动作（4项输入/9项输出按既有600/800字符规则截取），完整实际diff1942字符、无遗漏路径。普通skill已真实生成1POST/8,900tokens（8,184输入、716输出、16.396秒），正常stop，未人工修改。源历史SHA `7a27d44a6b4148ccf01b51a29adbadb94a6ff366628add6fc58498db585e71c8`，skill SHA `08ea1f857034a337ff74077bc27e9699f36d27a917470711c49eadc29a4754f2`。源普通历史是有声明截取的轨迹摘要；无损排版保持其全部对象值，不把它改称完整原始对话。

随后在零模型下冻结原输入，再派生实际补丁卡和长行安全格式。1942字符diff在JSON中成为2040字符单行；`c134bd43`中的格式适配将其原样多行呈现，短diff保留旧格式，解码后全部对象值相等。派生时间为本attempt目标运行前。普通skill与生成输入/输出hash绑定；手工改文件再刷新输入freeze会被拒绝。相关回归检查远端24 passed，本机22 passed/2 Windows符号链接skip。

## 四臂目标结果

四臂均完成，Agent exit0、关键检查3/3、回归132/132。原题输出的data为`[60,66,72,78]`，实际mask为`None`，两种输入下单位分别为Jy/None。原始探针的`mask_matches: null`表示该比较没有计算，不能当作通过；本轮另核实际mask字段与题面要求相符。

| 目标输入 | POST | 报告tokens（含缓存） | 缓存输入 | 未缓存输入 | 输出 | 自动计时秒 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 无历史 | 19 | 491,274 | 407,516 | 75,711 | 8,047 | 212.056 |
| 源实际补丁＋结果 | 20 | 514,604 | 430,744 | 75,707 | 8,153 | 212.641 |
| 普通历史摘要 | 10 | 268,655 | 227,391 | 38,236 | 3,028 | 93.656 |
| 普通skill | 19 | 553,232 | 473,580 | 70,994 | 8,658 | 222.838 |

三种经验均实际完整读取：补丁卡72/72行、历史296/296行、skill27/27行；没有长行或未读输入混淆。目标共68POST/1,827,765tokens；含source与skill形成共84POST/2,298,659tokens，其中缓存1,917,118、未缓存输入346,862、输出34,679。训练、额外judge及付费科研API均为0；D/子Agent平台用量另账，不包含在该科研模型账本中。

在**已经拥有源经验**的条件下，普通历史的目标未缓存输入输出为41,264tokens，无历史为83,758；本次用时也较短。保留这一正向开发信号。普通skill未超过历史，无历史本身亦能完成；仅一个目标、一次seed、固定执行顺序，不据此宣称稳定因果收益。若source是为收集经验而额外执行，其成本必须计入；本表不能直接证明端到端净节省。

与[Matplotlib隔离批次](MATPLOTLIB_ISOLATED_CONTROLS_20261106.md)对照，载体效用随任务变化：该批无历史的本次token/用时更低，结果卡产生回归。两批的`feedback_card`不是同一干预：本批包含完整源补丁，Matplotlib只含结果摘要/路径，不合并估计一个“卡片方法”效果。两点不足以训练或认证选择器；下一步验证较小模型及新的自然任务对，寻找实际能力和迁移差异，而非继续只在35B已掌握任务上扩大计数。

## 冻结与复核定位

私有根：`/home/testuser/wzh/research_evidence/agent_learning_20261030/astropy_agent_20261105/attempts/isolated_dependencies_20261106/`。目标运行代码`c134bd43`；批次脚本`target_controls.py`与started/completed一并保留。固定profile只证明在**本attempt**目标之前形成，不证明全局未见或独立时间戳预注册。

| 工件 | SHA-256 |
| --- | --- |
| 原source输入freeze | `85c644d157981892de543d4cf59480aea3f084526b2315e0251a5cf04caa404f` |
| 派生profile manifest | `d53442df85e7dd631d5ae4a9525e44db2307e8ad564064b2d44180541e7f4a36` |
| 目标输入freeze | `232ed0a339687360b96e7b520c0256900e4822dc3f20a73edf4418a9edba3cc2` |
| 派生普通历史 | `890f36d6bcaf4d1735d16d612c7ebad17028f626d523459c3b37c6fd6b4a3661` |
| 补丁＋结果卡 | `a9ea63f6c9b8d46c9011b1979a4d7c3f1e72cead15e7ef9d2cedc38958e667d1` |
| 四臂汇总 | `9cd4a747ed0c76a877312ae6e04c6a52b94a7f8fd85aee2f9f17e4f0a7412f30` |
| none completed | `ed0d56058453c667e023ee17854c07d73a71dd1739f2e4c56129f2a03a97943b` |
| patch/result completed | `c9f679d5284c964476f6b46eb70e1d884477ceb4b54f8729853ca6907a471ad7` |
| history completed | `4dcd75b180f0ccc73980795e68e6359379a2d56cbbeda5412fc13bccea8009c2` |
| skill completed | `85ac91034babc88c6594db64b85f249524fd67397825b100b26179354f02cab0` |

独立只读子Agent核对四臂completed、成本、原题实际mask及输入freeze，未运行新模型、未修改raw；这是AI证据复核，不是人工gold。当前环境仍使用声明的ARM原生wheel overlay，NumPy ABI warning在base/gold/Agent均保留；不等于原提交环境的完整二进制复现。

125项raw/回执/输入/评分日志另存双机审阅包：本机`D:/Documents/Loop_D_assets/agent_learning_20261106/astropy_isolated_controls_20261106.tar.gz`，GB10私有`evidence_packets_20261106/astropy_isolated_controls_review/`；357,982bytes，SHA `32ddb0917f78d271f1d9d94102e5b94ab816d6cf74ad131fb5fad8c8310a72e2`。本机逐成员hash复核125项相符，四个completed均与批次绑定相符。不含完整checkout/依赖/权重，非独立复现包，不入Git。首次打包草稿误含candidate树，私有保留并标为已被精简包替代；未改科学raw。
