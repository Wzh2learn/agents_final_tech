# Matplotlib 自然任务对：运行资格

> 2026-11-06 | 资格与source开发记录。脚本：[资格器](../qualify_swe_contextbench_matplotlib_20261106.py)。区分零模型控制、旧暴露source与新的隔离比较，不将资格成绩当Agent效果。

## 固定来源与原题

**Agent输入隔离修正**：后续独立复核发现完整wheel site-packages经`/deps`可读，target的`/deps/mpl_toolkits/mplot3d/art3d.py`含未来gold修复。正常导入旧源码不等于参考不可读；目标模型尚未启动，因此先修隔离。旧source/普通skill/冻结输入保留为暴露环境的开发产物，不进入新的洁净比较。base/gold资格数字不变；新source须使用只含必要依赖且不含wheel项目源码的可读面重新执行和形成经验。

- source `matplotlib__matplotlib-23562`，base `29a86636a9c45ab5ac4d80ac76eaee497f460dce`：3D collection在首次投影前读取颜色触发AttributeError。
- target `matplotlib__matplotlib-27361`，base `5b5154ded5ee9c546e640b01f1a75ac041fd2fed`：3D patch在tight-layout保存时尚未建立二维路径；与source同属投影初始化，但对象、路径和测试不同。
- 官方GitHub compare留证：源PR合并`1fd71a5d23c0856f8005b9f82828d4b7c11b4734`是target base祖先，ahead5088/behind0。不是使用公开旧轨迹作为未经核实的历史。

## base / 参考修复控制

| 控制 | base | 参考修复 | 不改变的回归范围 |
| --- | --- | --- | --- |
| source关键测试 | 0/2 | 2/2 | 两臂均136/136 |
| source原题 | 首次取色`_facecolors2d` AttributeError | finite RGBA (2500,4)，draw前后形状稳定 | 原题独立于测试分数 |
| target关键测试 | 0/1 | 1/1 | 两臂均150/150 |
| target原题 | tight PDF/300dpi PNG均`_path2d` AttributeError | PDF7073 bytes、PNG249299 bytes；包围框内目标facecolor像素38026 | 验证格式、可见绘制与包围框，不只看是否生成文件 |

数据原始节点存在10项参数名被空格截断、7项缺失类名。仅对完整pytest collection中的唯一前缀/后缀匹配恢复，映射、missing及ambiguous逐项写日志；两臂均完整选择136/150条，未删除测试。

## 环境与边界

隔离Python3.10 / NumPy1.24.3，Agg替代原用户的QtAgg；检查的是同类投影及渲染行为，未声称复现GUI后端。源码来自固定commit；source使用3.6.3、target使用3.9.4 ARM wheel的原生扩展及缺失生成版号，各10文件有hash。wheel未覆盖Python行为源码，仍属混合环境，非固定commit原生构建。

两个归档各8项仅包含同目录目标的相对SVG软链，已按归档目标逐字节实体化并保留映射/hash；供未来Agent的源码不能再把这些文件当链接风险。首套source 3.5.3 native wheel的FT2Font ABI失败保留在v1现场，不覆盖为成功。

源码Matplotlib自有BSD兼容许可，任务数据卡MIT；各依赖原许可证继续适用。目标参考/test patch只供独立评分容器，不进入Agent工作区。题面和参考已在开发筛选中读取，本任务对不属于盲确认。

## 证据定位

GB10私有根：`/home/testuser/wzh/research_evidence/agent_learning_20261030/matplotlib_qualification_20261106_v2/`。

- receipt SHA-256 `b23f6980004b249b60902a6f68f82a561170a7d41209b8eecc4239609d1b9a25`。
- 原执行脚本SHA-256 `b7910caf78f36ca35828a71874c8a76b46fd6d808444cde7c8f9fa3c1ec68ece`；Git传输可有CRLF/LF差异，内容比较须声明换行口径。
- chronology SHA-256 `4560f9cd943c12d93539f4d44f5d7607c9fc45220d69c75c4ca3f9eda09b10f8`。
- `source/`、`target/`下各base/gold的原题、focus、regression日志及overlay、materialized_links清单可独立复核。第一套失败在相邻`matplotlib_qualification_20261106/`保留。

一次限定范围的独立只读核对已复算回执、映射、原题结果及归档实体化文件，未见阻断；它是AI代码/文件核对，不是人工专业金标。此次新增模型、训练、judge、生产调用均0。下一步复用已修复的离线搜索、真实源执行、冻结经验与自动账本，先完成自然source，再开展同配置target强基线。


## Agent 执行入口与预检

[运行器](../run_swe_contextbench_matplotlib_20261106.py)复用现有core/Requests派生、自动记录和固定rg，无全局模块参数替换。默认context65536/output16384、48转发POST/1500秒，seed/限额显式配置；source/target各使用对应冻结依赖。实际Agent完成后，评分副本恢复冻结测试、ancestor conftest与pytest配置，再独立跑原题和全部映射测试。

零模型预检根：`matplotlib_agent_20261106/attempts/preflight3/`。当前原始runner SHA-256 `d0015ddf171a10644eea59ff24af52b553458e90a2ce3b4ce44bb4679d67e9f7`；source/target均通过隔离绘图、rg、源archive/overlay/完整节点及资格hash核验。`preflight2/post_cap_probe/receipt.json`记录50个并发虚拟POST仅放行48；`preflight1/evaluator_gold_probe/preflight_receipt.json`记录合成参考候选的测试篡改被还原，独立问题1/1、回归150/150且原候选保留。重复预检拒绝并保留旧hash。合成seed7244仅用来验证源经验构造，不计为Agent样本。

独立只读源码核对确认当前文件与preflight3哈希一致、source工作区不包含gold/隐藏补丁/未来Git，未发现默认source命令的确定性阻断；实际行为仍待实跑。实际source使用独立attempt `pilot_matplotlib_20261106`、seed7201，在Astropy四臂完成后串行执行，未争用模型。


## 实际source与保留原件的重评

代码快照`502c095f`下的source实际执行已结束：Agent exit0，34转发POST /921,757 reported tokens（含缓存875,411）；未缓存输入38,176、输出8,170，自动计时202.17秒。原completed SHA-256 `154c53615751e26f4ce7ff9d6da13fcefb4afd4e1bae9487acc9bcdcb2d309bd`、raw SHA `b5cd61f9228bb26ac2f0a7f00138ed7dfe33bd4fe481d8b31e6a5fe0986cd2dc`。

原评分因公开绘图测试生成的`result_images`预期图片软链接而返回`UNRESOLVED_SYMLINK`，不是已评出的失败。现仅排除原clean_base不存在、且根目录自身不是软链接的生成图片项，记录99个PNG/55个预期图片链接；其他源码或异常链接继续拒绝。缓存清单SHA `12fef49546507d465fb92f90427ec34b8e862d5fa0da82b233e522b51df95a14`。真实源码变更仍为art3d.py与测试文件，完整diff1497字符；未把图片当成代码改动或经验指令。

零模型、独立评分副本重评结果：冻结关键测试**2/2**、完整回归**136/136**，原题调用不再抛异常。原candidate逐文件/链接manifest、raw和completed前后不变，原状态不重写；新revision在`pilot_matplotlib_20261106/source__none__seed7201/post_run_recheck_generated_images_v1/receipt.json`，SHA `869ed49561c2c902b6e226e98ace4528b3ab352dd01c2024e70fb77d8209d740`。

**附加属性范围校准**：候选首次get_facecolors返回形状[1,4]，draw后为[2500,4]；参考修复前后稳定。原问题只给出异常，未明确要求首次长度及前后稳定；collection API也允许单颜色。因此这是一项有动机的补充观察，不能单凭它宣布整个source修复非法。源经验并列记录公开窄合同通过、实测形状变化和更广泛语义未确定，不把“测试通过”扩展成所有映射行为都已验证。

源经验已零模型构造，39个真实工具动作，6项输入/16项输出按既有600/800字符规则截取，并另保留完整实际diff。`source_experience/metadata.json` SHA `961feaee7f22cdcc82c9c6dce1c5a120368659aeb11200c68e186aae149d6b5e`；history `28c0fdfaa8e04fdb7fe54e866e9f9a3bedb0afae1977f4f310fcb58b27c2e886`；结果卡 `8dc3961f28a369b47407860aecbba0d01cead66cb49f82eb22d009d66d3eeff8`。元数据明确绑定原status、重评hash和附加性质范围，target冻结前再次复核。构造命令已执行，不能覆盖重建；普通skill随后已编译，目标输入已冻结，见下。

4项定向artifact/revision测试已在GB10通过；本机因无Windows软链接权限有2项平台跳过，其他保护不弱化。此修订没有新增模型调用，不改测试节点或参考。


普通skill形成使用已提交`502c095f`入口和既有抽取器，真实1次本地POST、17,918输入＋860输出＝18,778tokens，缓存0，25.245秒正常stop。skill SHA `33210f513ef16d4873ddb8c7f2cab8b88211130bce98c070c397331f211de698`；保留原请求与响应，未人为润色或纠正。它包含对源初始化路径的概括及列映射更新等未决条件；源测试实际只检查RGBA与不抛异常，不能把模型建议的所有检查当作已执行事实。

target尚未调用模型。源history42,672bytes/430行/最长1581字符、结果卡2397bytes、skill3314bytes；实际读取仍需在目标执行时核对。`source_experience/target_input_freeze.json` SHA `65942eda7a2d45b56960e9ecb53b94226074fc2f3af0b26f55cbfc99292b33b6`，绑定原source、修订评价、source metadata、形成账本及三个输入文件。该项目累计形成阶段35POST/940,535tokens，source与skill形成分项记账。下一检查点是在相同target版本和资源下跑无历史、普通历史、普通skill及透明反馈对照，再决定是否增加实际补丁摘要/跨seed；新额外输入须另行冻结，不改已冻结三文件。

## 隔离批次执行合同（在首次新生成前写入）

隔离投影已完成零模型验证：私有`matplotlib_actor_dependencies_20261106_v2`，7168文件，manifest SHA `e63a69c6c719bdcc56aa8d08b7ba7635de6bafe90f826b51b7eda79cdad0f75b`。runtime不含site-packages，source/target各自的deps排除matplotlib/mpl_toolkits项目源码；三Python别名均3.10.19，Agg与rg通过。先前两个gold读取入口不存在，同权限image/可读挂载扫描只见固定`/root/lib/mpl_toolkits/mplot3d/art3d.py`，AST核对相应目标方法不含gold lazy projection。扫描排除虚拟/proc、/sys、/dev，以及实测不可读的apt私有缓存目录；这是具体路径核验，不是任意编码副本或预训练隔离证明。

`matplotlib_agent_20261106/attempts/actor_isolation_v6/preflight_source.json` SHA `fe6009943beaf594938e138ac8734cc6406c30872f85e817527d2c4da6162be5`，target回执 SHA `99a5e8c948014affb8c2c70737d07f715a39b0afff4e1604c73b4838bb98920a`。v1已重放两个任务的base/gold原题与focus，v2逐文件仅增加同字节python3入口；旧投影、失败扫描和原stderr保留。运行器前后验证新固定hash，经验构造/skill形成/target均拒绝未绑定该投影的旧source。

新attempt为`isolated_dependencies_20261106`，source和target都用seed7201、temperature0.2、context65536/output16384，每个执行episode上限48转发POST/1500秒。固定原题、版本、native overlay、rg和现有隐藏评分，新增actor依赖投影须通过同权限可读面与解释器检查。先在新投影执行真实source，再由该次raw/实际补丁/独立结果形成普通历史和反馈卡，生成一次普通skill并冻结输入；不复用旧暴露source的任何经验文本。

target按无历史→透明结果卡→普通源历史→普通skill串行运行，每臂独立工作区、相同资源。记录关键测试1项、完整回归150项及原题PDF/PNG实际渲染语义；分列Agent退出、预算截断、异常和未评，读取经验以raw为准。比较请求、未缓存输入/输出、缓存、用时，source/skill形成单独计费并说明摊销，不只挑选有利成本代理。若skill胜出，仍需实际补丁＋结果等强简单对照和重复，才能进入方法主张。

这是一对已在开发中见过参考的自然任务，不冒充盲确认或预训练隔离；测试条数不当独立任务数。此合同绑定下一批次，旧35POST及原回执原位保留，隔离修正不重写旧账。
