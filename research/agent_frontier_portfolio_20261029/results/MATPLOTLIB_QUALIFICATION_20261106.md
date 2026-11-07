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

<a id="new-source-pair"></a>

## 新任务对25332→25352与真实来源采集（2026-11-08）

本节属于新pair，前文23562/27361的旧结果不合并。资产根为GB10私有`/home/testuser/wzh/research_evidence/agent_learning_20261030/code_source_expansion_v1/MATPLOTLIB_PAIR_QUALIFICATION_V1`；准确源码包位于同级`SECOND_WAVE_ARCHIVES_V1`。以下缓存与V1–V3过程从Git `5b6c77e5` 的ALFWORLD_CORRECTION_DATA同题段逐字迁入，规范LF原段SHA `8c5ffb3430b4c4604e61fd4d0464aecb984b1b29dd822522f58073edcd40f942`；它是V4前快照，现态见后续。

**Matplotlib新任务对源码缓存（11月8日，资格前快照）。** 25332/25352的准确base分别66ba515e/3742e7e，两个官方commit archive共75,362,388bytes已双端核hash；当时只读取目标instance/repo/base列，未读取目标参考补丁正文。私有`SECOND_WAVE_ARCHIVES_V1/FETCH_RECEIPT_V1.json` SHA `76f948d5c6385c5c0c6850ef1de0c35e2dad482c835ae2caa64c0ec0ce6bf3ca`，2次公开GET，当时尚未解压或执行。可复用旧Python3.10依赖投影（manifest SHA `e63a69c6c719bdcc56aa8d08b7ba7635de6bafe90f826b51b7eda79cdad0f75b`），缓存时尚未证明适配新base；须先做新pair的base/gold原题与完整回归资格，再开放actor。这是已有项目的新任务对，不算全新未曝光项目确认。

**新pair原生资格进展（11月8日）。** source25332已两次复现F2P1 fail→pass，181PTP两侧全过。target25352是同组件维护重构；25个公开label缺类路径，经AST唯一映射后61节点齐全，base为1失败/57通过/3跳过，3项pandas可选回归因投影未含pandas而skip，gold未跑，pair仍不合格，不释放actor。原警告错误、缺类路径与V1/V2/V3保留，未把skip当pass。累计7个CPU容器/34.342秒，模型/网络/安装0，30tests/63subtests通过；D核全部7份原生日志及owned CID已移除。`MATPLOTLIB_PAIR_QUALIFICATION_V1/RUN_V3/receipt.json` SHA `d75a7f499f20385c2e2cc15a121447ba6798de0b60731e186dd5156afd6d8fce`，D核验SHA `c27d8441b8cc5ea395dd69a7f690d6e39fe0775fc2e8d4358db006c77af49964`。仓库兼容缓存扫描超时，未据此宣称缓存不存在；下一步只解决明确的pandas参考缺口，不改方法结论。 78成员私有包已双端核验，SHA `9d0f84fc64b2f7a4b3d8a9685a6d76b07d4d50605aece588ae6d60443b39920e`；资格临时树保留用于冻结路径复核，源码已集成main。

### V4：缓存补齐后的完整资格

只复用milvus缓存pandas2.3.3，与原NumPy1.24.3/Python3.10及dateutil2.8.2相容；补缺失pytz2026.1.post1，source补tzdata2025.3，target保留2026.6。旧投影/原字节及native overlay不变，无网络或安装。新投影`PANDAS_PROJECTION_V1/manifest.json` SHA `4bc597b975481716b893eee86a2b87417bc1732b19b9e26f9766c320de3a7b8e`；9,881绑定与2,684复制记录保留。source/target的项目源码仍被依赖投影屏蔽。

| 新pair控制 | F2P | PTP | 实际退出 |
| --- | --- | --- | --- |
| source base | 1失败 | 181通过 | 1 |
| source gold | 1通过 | 181通过 | 0 |
| target base | 1失败 | 60通过 | 1 |
| target gold | 1通过 | 60通过 | 0 |

四组无skip/missing/error，D已独立核日志marker/hash。V4状态QUALIFIED，实际新增4容器/16.853秒，含V1–V3共11容器/51.195秒，均已关闭；0模型。V4合同SHA `6723d734d33fad028a2324092ec01f84b1b7361abd71b7a6b046b51cfb38d2ce`，receipt SHA `490dc51749892229d689312f56ef178f3bb0078c45f24b870addc3b85dd53cfe`，交付SHA `19152ff96ca1023780b385b14513a33888196b7b2040d55cf7008de1bf03f412`。资格只证明任务可执行与参考有效，target仍是维护后续任务。

### 一次真实source采集与停止

复用`run_contextbench_source.py`的Bash-v2、relay、计量与隔离容器，只增Python3.10/source依赖槽/本地项目lib与原生评分支持；旧Django/SymPy准入不变。先有两条失败控制，新增后联合97tests/65subtests通过。实际CPU prepare 4.767秒、0模型；四文件固定快照SHA `d56cfa009b8107937325a57dad971d471128d5be8cd0bfb185e67b58ad41718c`，C限定启动审阅无确定性阻断，SHA `7d928a80d8a3f9ab4b7b105e19d266479c54786ec22c3a238753fd27f5a7cde5`，未把测试或prepare当实际修复。

私有`SOURCE_COLLECTION_V1/attempt_v1`只采source25332，现有27B FP8、thinkingFalse、ctx32768/output8192、seed17/temp0.2；独立上限48POST/1200秒/64MiB，无训练、无目标调用、无服务重启。manifest SHA `af119afd6a670a94905ac21391634935f1da8ef941d26a0af576e7674d084b06`；启动SHA `f3ca235a21e342f6abf0eefd16739cab39884f1699633ac8f74ba83cf4189a4d`，原owner1473717/start1082424090已退出。

真实结果为GENERATION_FAULT、source_success=false：48个bash动作全为读取/搜索，末30次相同grep返回exit1/空输出；无编辑、无模型自行测试，diff0字节。最终F2P0/1、PTP181/181，原始weakref pickle故障保留；第49个本地attempt被帽拒绝，没有超发。全部48次实际body是Bash-v2且完整保留题面，47个后继工具反馈均逐字透传。未发现实际接口阻断，不能把无编辑尝试当作写入路径验证；也不据一个source否定学习。A尸检SHA `4460754835fe3622337e76ba1294b7db77b6e715e1ec38be31bfe06bb00f20bf`。

新增48POST、input410,882/output3,075/total413,957tokens；48请求cache均未知，noncached不填0或等同全部输入。D核全部48实际request/provider body hash、usage、1/181原生日志及三个owned容器已移除、锁空闲，SHA `12dc9cd013153b7f9c0250c34bbe877ed15874910f7c97f9d1a23c8c637682a4`；原receipt SHA `e0202b46997c32ef0c357498b29b181e7721a33b56cf5b301c1d66f7f8de8c9a`。这与旧两source各48POST分开：三道source形成共144POST/1,525,504tokens，接口canary2POST/5,494tokens、ALF与研发Agent另账，不是项目总账。

### 可复用的reference-assisted来源证据

停止无引导source重试，不先训练。复用已经真实执行且1/181全过的V4 source参考应用，形成`SOURCE_COLLECTION_V1/REFERENCE_ASSISTED_SOURCE_V1/SOURCE_EVIDENCE.json`，3,123bytes、SHA `1dae2bf35ea1c72a124a3ea236e1c00dd62e1ad1db734e11629ec74a3fe4c413`；manifest SHA `02e8448f7150df7ba27f6c38ef61e94495d8b7827f3a7f16dd36a26d83757f20`。它含source原题、source参考补丁、实际base/gold结果及本次自然失败事实，无target gold/未来题号；复用已有执行，0新增模型/容器/训练，形成费不隐藏或重计。

这是明确标注的训练来源参考辅助证据，不是Qwen成功轨迹或反馈学出的skill。后续先准备无经验、仅source文件位置提示、完整已验证source证据的同设置强基线对照；若再试紧凑卡/学习方法，必须给信息匹配的完整参考证据基线，不能只击败未修复的失败历史便归因于表示或学习。该来源证据冻结时尚未运行目标、未释放训练；后续目标对照见下文。

完整321成员私有闭合包已双端逐项核验：10,171,046bytes、SHA `aab5c78e9af3ae8cc57c14b7540fef321cabcfb54e66cd84f4c5765738893a93`；manifest SHA `ae847c1ab7f47885db48c818b55bd9d08967886f807837987e01ebd22b67e476`，本机check SHA `3161936a14936170262efd1191731401d59e88dc5393570da52b84524a6fb90f`。包只含控制/原始调用/精确源码与source证据，不含完整scratch或依赖包；v1误收staged第三方文件，v2已排除并保留修正说明。实际18个运行Python组件快照SHA `56871ba5a0beaf5f8f22dce464aeba62234fa733c760f139c65d2200ab196aac`；源码与测试两文件发布到Git时CRLF→LF，已核AST相同，原执行字节仍在快照，未改历史绑定（规范化记录SHA `b86c78ab20abb4b441312cbd538fe9e4ca7992c4cb50e78fcc22207dea3449a5`）。

代码集成后，已确认无在途source进程、4项自有WIP与main仅规范化换行差异，且18运行源码/两份测试已归档；随后正常移除已完成的资格临时worktree，保留原7历史树。不是删除raw、依赖或父模型。清理回执SHA `6f0518db52d41ee3cc10443249b4446c120369001638a8ea82e6d253cab00826`含原路径恢复配方；旧严格组件复核须用对应源码快照，不能拿当前main冒充历史字节。

### 新pair目标三臂：已闭合

目标25352独立准入，复用Bash-v2、relay、锁和评分，仅显式target依赖槽；source默认准入不变。GB10固定字节127tests/65subtests通过，3份真实输入CPU prepare/verify不含模型或容器。C仅检查固定源码/差异/隔离/预算，回执SHA `25c4d5915d36a5669dbd638efbde67250ccd5c7e6c39d7af1c547af638df0a49`，不当效果证据。源码已集成main `4ea46e4d`，不新建worktree。

私有`TARGET_BASELINES_V1/PROTOCOL_V1.json` SHA `66c54d60539f422718cefcddfa1fbc3b76f0963e00a949bd99d13af24e82e097`冻结none/source_file_locator/full_verified_source_evidence，后者只给上述source证据，不给target gold。三臂同clean base、27B FP8、seed17/temp0.2、thinkingFalse、ctx32768/output8192，每臂48POST/1200秒/64MiB，串行且不自动重试，无训练。正式prepare14.858秒，SHA `ad7cf0efe651f36e8ffdd06e8f2e7308e68332efe03b3a7cd2e5e10eb9eb3846`；D复核19组件和同设置SHA `59b4c49f04975310200d1eb34d698ab07dadbb410dee46d1481d44ceea046aa2`。

已释放单pair开发比较，不是方法/确认：完整经验若未超过文件位置，不归因于经验学习；无经验已全过则不在该题造增益。必须F2P1/1及PTP60/60全过，skip/error/missing非成功。发布SHA `a70a03370901fa2ac69726e7ea2de68b964c862692c4807100c288a05b32a3bf`；`LAUNCH_V1.json` SHA `114346059b9f3fa6ba4fc08ac05d233631078fecc421d3558679fd661ff61ae4`记录owner PID1525386/start1082873070，启动时已实测存活，终态见下文。旧source48POST及全部形成费保留。

**真实闭合结果。** 2026-11-08三臂均在48个实际POST后停滞；第49次本地attempt由relay按HARD_CAP拒绝，保留GENERATION_FAULT，不把这个403说成上游凭据失败。原失败题是公开维护要求对应的Grouper内部mapping控制；不是下游答案准确率。

| 臂 | 实际POST / bash动作 | F2P / PTP | 源码改动 | input / output / total tokens |
| --- | --- | --- | --- | --- |
| 无经验 | 48 / 48 | 0/1 / 60/60 | 0 | 452,291 / 3,571 / 455,862 |
| source文件位置 | 48 / 48 | 0/1 / 60/60 | 0 | 446,804 / 3,750 / 450,554 |
| 完整已验证source证据 | 48 / 52 | 0/1 / 60/60 | 0 | 498,552 / 3,903 / 502,455 |

合计144实际POST、147本地attempt、148个bash动作、1,408,871tokens（input1,397,647/output11,224）。三臂各自只有15/11/16个不同命令，最多重复34/38/37次；命令均为grep/sed/ls读取搜索，未编辑或自行测试，candidate.diff均0字节。144份provider原始SSE均tool_calls结束、无length，144份cache细分全部缺失，cached/noncached不补0。这里是同一任务三种输入，不是3个独立任务。旧source形成费另账，不重计。

D全量核对144份实际body/响应/usage、所有原生评分和19运行组件的Git blob字节；9个自有容器已实测不存在、owner已终止、模型锁可取得。原生每臂1个失败与60个通过，日志marker/hash/完整覆盖一致。D闭合SHA `586cbb92218e7e5b7e59f00b9aed24511cab47ffa6df93c683ce72718122af82`；裁决SHA `8bfc23c42a2d6c586aea328f5ddddf048311de0902149b012955025fc99d3939`。C仍仅为启动前审阅，本轮结果由D核验。

实测wire输入被OpenCodeCLI加外引号、转义内部双引号并保留原CRLF；全部请求精确匹配该变换，source内容未丢失。核对器最初误按未包装/换行规范化后的字符串比较，原读器已留底，修正只影响核验、未改raw或重跑模型。未证明该包装导致停滞，不据此宣布反馈学习无效。

**决策：停止该pair当前actor下的经验表示变体和训练。** 完整source证据也未打破搜索循环，没有经验增益证据。后验重复动作诊断显示：若在相同command+output连续3次后结束已有轨迹，无经验/文件位置后面分别还有31/35次请求、333,033/365,190tokens；这只是保存轨迹的费用诊断，未实现恢复、未声称真实节省，full臂含多动作/请求，不套用一对一计算。下一动作转向[新增训练来源](ALFWORLD_ADDITIONAL_SOURCES.md)，不复活旧7来源R配方。

547成员私有闭合包已镜像本机并逐项核验：4,202,258bytes，SHA `3a6213c33f8982a15a5c5129c6be8bb79c49507312d4b8c5aebb1e9be05f421e`；manifest SHA `00fc1916e190a30fcf6fdb0217cac9b563983b71c062a33999b9c04c5c81f568`，本机check SHA `bc360b2e641d51bb7854bd3d96e367a2501618175ba8ab625590506fd92e26f5`。包不含完整scratch/第三方依赖/权重，19组件按Git `4ea46e4d`逐blob可重建；无需新worktree。
