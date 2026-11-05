# Astropy：隔离依赖后的经验复验

> 2026-11-06 | 内部开发复验；目标和参考已在此前开发中见过。原始数据、运行资格与旧比较见[原对照](ASTROPY_PROFILE_CONTROLS_20261106.md)。本页在新source首次生成前创建，原地维护本批结果。

## 执行合同

source为Astropy14995、target为15082，沿用冻结源码/题面/测试、Python3.10/NumPy1.24.3及原生wheel overlay。actor仅挂载已验证的`actor_dependencies_v2`，manifest SHA `32fd788dae461e4eca1f792c9f9e569c70bac9ee7d0befb3335848f98efe1aed`；项目wheel Python源码不进入actor可读面。旧source、skill和目标输出保留，不作为新经验输入。

独立attempt为Astropy自己的`isolated_dependencies_20261106`。source seed7201，target四臂seed7202；temperature0.2，context65536/output16384，每episode48POST/1500秒、请求体总额6MB。先真实执行source，再从实际轨迹、完整补丁与独立反馈生成经验及一次普通skill，冻结输入后按无历史→实际补丁＋源结果→长行安全普通历史→普通skill顺序串行比较。相同数据值的重新排版不作为新方法；记录其与原历史的无损映射。

原始源输入在派生profile前零模型冻结，无需先运行任何target。派生profile须标明在本attempt目标运行前构造，不能沿用旧组“目标出结果后的post-hoc”时间口径。输入与编译账本、source completed/raw绑定；各臂独立工作区。

target分别报告关键测试3项、完整回归132项、原题data/mask/unit实际结果、Agent退出与预算事件；测试通过不替代原题探针。成本分列POST、缓存、未缓存输入/输出及用时，source和技能形成单独记录；共同必做source与专门采集经验的成本分别解释。单任务各一次用于开发，不把测试条数当任务数，不由旧新差异推断依赖隔离的单变量因果效应。

## 当前检查点

新source在`b23836be`代码下完成：Agent exit0，15POST/461,994tokens（含缓存377,887），未缓存输入78,030、输出6,077，自动计时178.309秒。冻结关键测试1/1、回归179/179；原题四种mask组合中，要求检验的data和mask均匹配。source completed SHA `7e0f7b02ca3e204eef2036b664c4ba62928d9a8e1cb8131144a9d2e6c5cded80`，raw SHA `440ffdc0501c5f5e368a033aca40500e44f418280f38dea83ae7e63f29eb8df1`。

源经验14个真实工具动作（4项输入/9项输出按既有600/800字符规则截取），完整实际diff1942字符、无遗漏路径。普通skill已真实生成1POST/8,900tokens（8,184输入、716输出、16.396秒），正常stop，未人工修改。源历史SHA `7a27d44a6b4148ccf01b51a29adbadb94a6ff366628add6fc58498db585e71c8`，skill SHA `08ea1f857034a337ff74077bc27e9699f36d27a917470711c49eadc29a4754f2`。源普通历史是有声明截取的轨迹摘要；无损排版保持其全部对象值，不把它改称完整原始对话。

下一步先零模型冻结原输入，再派生实际补丁卡和长行安全格式。1942字符diff在JSON中成为2040字符单行，需要原样多行呈现，避免工具截断；短diff保留旧格式。派生时间标签必须为本attempt目标运行前。新普通skill与生成输入/输出hash绑定，手工改文件再刷新输入freeze不能继续冒充原生成。完成这些检查后直接运行target四臂。
