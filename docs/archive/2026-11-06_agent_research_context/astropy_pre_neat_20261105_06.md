> 历史快照归位于 2026-11-06。原文件 `research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md` 的连续片段；旧任务、结果与预算保持当时口径，不能作为当前授权。现状见[第二阶段计划](../../../research/agent_frontier_portfolio_20261029/STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。

## 工具修复、反馈接入与 Astropy 批次（2026-11-05）

**工具前提已修复**：[离线工具探针](../../../scripts/graph/research_tool_runtime.py)在同一禁网镜像和一次性HOME下成对运行OpenCode搜索；缺rg时exit1且无匹配，只读挂载固定ARM64 rg后exit0、有真实源码匹配，零模型。原工具错误不归因于经验方法。探针总回执 SHA-256 `73791f1a61b9c82d88b5805f73126565a75aa61bb836ffd78f196632846b5519`，私有根 `ripgrep_runtime_probe_20261105/`；rg SHA-256 `968cabe8efed72fd8fd482cb76b6084fcb695fc5293af7fb62296b02f487fb69`。新Astropy所有臂统一使用该绑定；旧轨迹和工具环境不追溯修改。

**公开基线接入推进**：RethinkSkill的原生字段摘要诊断获得一个格式和提案协议合法的replace，但实际diff只删末尾换行，未获得实质修订，未部署旧Sphinx。见[接入与成本记录](../../../research/agent_frontier_portfolio_20261029/IJCNN_RELATED_WORK_REFRESH_20261030.md)。本阶段新模型调用1次、2,447报告tokens，历史源执行不重计；这解除了格式接入的一部分疑问，下一次真正方法比较仍须源训练/独立验证/目标分离，不能省去gate。

**新自然任务资格**：`astropy__astropy-14995` → `astropy__astropy-15082`，source base `b16c7d12ccbc7b2d20364b89fb44285bcbfede54`，target base `c5e2521db013d9641999be9c79d1d807741bc39a`。题面、实际原题复现和参考行为一致：source无mask操作数的bitwise掩码传播在base失败、gold修复；target无mask/无unit的collapse在base报AttributeError、gold返回正确数组并保持单位。source focus base/gold `0/1`、`1/1`，两者完整回归 `179/179`；target为`0/3`、`3/3`，两者完整回归`132/132`。源修复是目标基线祖先；目标正文直接给出源PR和机制，因此该信息对所有Agent可见，不能当成历史臂的独有信息。

[资格器](../../../research/agent_frontier_portfolio_20261029/qualify_swe_contextbench_astropy_20261105.py)回执 SHA-256 `e0ed1ac9cb580b36f65a9c90e4f99b418963e72554be92a031be955afa1fd71d`，私有根 `astropy_qualification_20261105/`；时序证据 SHA-256 `0e2ebe5f2054e9cb0bffd7cc0eb81c771807eacf25b7a6c06bcba77286e6581b`。使用隔离Python3.10/NumPy1.24.3，并仅将Astropy5.3.2 ARM wheel中缺失的17个原生扩展和生成的`_version.py`放入源树；不是固定commit的原生编译，关键Python逻辑保持固定源。覆盖清单SHA-256 `08e6caf6ff363d2e3175af60b017b1030f32bf08ed34949ddc909cbf6b9c6300`；源码BSD-3-Clause，任务数据按发布来源记录。

[Astropy runner](../../../research/agent_frontier_portfolio_20261029/run_swe_contextbench_astropy_20261105.py)复用现有harness、经验提取及自动记录，所有新尝试有独立attempt根，完整outer runner与组件hash在生成前固定。预检已验证实际Python/依赖与OpenCode搜索；原始nested tests恢复反例、资格脚本LF等价/真实差异反例、30并发请求仅24放行的零模型控制均保留在`astropy_agent_20261105/attempts/preflight*/`。先运行source无历史，使用真实源产物和最终反馈冻结历史、普通skill与透明结果卡，再运行target无历史和同预算经验对照；每臂24POST/900秒，seed7201、temperature0.2，模型与工具一致。新源历史额外保留最多10,000字符的真实最终代码diff及完整hash，避免仅依赖截断的edit输入；该字段同时提供给普通历史和skill生成。未通过参考测试、原题行为、异常退出和预算耗尽分开记录。

主研究问题继续沿用既有的“可运行指令、推断条件与环境副作用分离”，观察经验是否改变可执行行为，再决定采用来源约束编译、执行见证或适用性学习。先完成这些强基线；已有公开方法的字段结构、历史回放或简单规则能够解释结果时，以其为参照调整候选。训练与蒸馏仍是可选路线，监督需来自语义合格的真实结果，并计入形成和验证成本。

**实跑接续（固定代码提交 `d102487a`，批次ID保留20261105，执行跨至2026-11-06）**：source正常退出，14POST、154,712报告tokens（缓存90,492已含），原题四个输入例均得到正确数据与mask，focus`1/1`、完整回归`179/179`。raw中14个工具动作全部completed，glob和grep各1次，未见ripgrep执行错误；这证明新环境确实可用，不据此推算工具修复造成的准确率或速度收益。source completion SHA-256 `3080494ea572504fc62479554b54f5bcc84c29f55ba2aa6ad34bfe971955ffd2`。

源经验已在首次target调用前固定：历史14个实际工具动作、1个被裁输入和8个被裁输出，另保留真实源修复的502字符完整diff（SHA-256 `c7b7dd28c01a1e0ec7ad96bbe48fa799ef522405cec826103cd8ca7ffbe485f1`）。历史SHA-256 `99b379a42f335d5ceaa67f044a75168771faf49fb07cf488401925cb132b4b43`；结果卡 `15ee5089784b377d913358ad0f99c8c90f5cf2815d6803ad26b7b13b0ef0c155`。普通skill只用源历史生成，1POST、8,565tokens、正常stop，skill SHA-256 `d2c38570577d4355a7ec25ee0b8c22deae3cc0207de8db3ab5f90fe8bbd8c7bc`。目标输入freeze SHA-256 `bc185099415174ad0ad7bad1788b69c09ae4360a0e1fee70d3b29d7219e301a4`。

target无历史臂正常退出，15POST、246,557tokens（缓存201,704已含），原题数值和单位正确且不再抛异常，但把无mask结果改成全False数组，未保留参考规定的None，focus`0/3`、完整回归`132/132`；不能仅按“异常消失”算完整修复。回执SHA-256 `c22613b0599f3ea6cb8d1e60819d1de5e4ef4335167f6dcac3abe5660fe060ce`。

源历史臂正常退出，6POST、79,588tokens（缓存25,539已含），focus`0/3`、完整回归`132/132`，原题仍出现mask/unit AttributeError。read工具报告读到169/169行，但逐行原文比较并不完全相等，不能据行数称完整忠实读取；具体差异待raw核对。回执SHA-256 `50f9ce291db611baf95194cb7dbcbc81c387443aaaa1a5f0543e8477823e2570`。普通skill臂进行中，结果卡尚未执行；各格只运行一次，尚不据此归因记忆机制。

源实际评测、原资格base与gold均出现`numpy.ndarray size changed`警告；该警告与混合原生组件环境一并保留，不能把这套环境描述成无警告的原生构建。所有来源仍是已读取题面/参考的开发任务，当前没有跨来源方法确认。

## 与 Paper E 并行

用户已将 Paper E 的 ICINT 匿名审阅稿与导师讨论稿发送给老师，等待导师及作者团队反馈；收到意见后继续确认署名、AI 声明、论文集出版与学校认定。只有在 ICINT 拒稿或正式撤稿后才考虑 ICDAR 顺序投稿。2026-11-05 用户确认升级并恢复科研 Goal；不进行未授权的投稿、付款、公开或外部联系。
<!-- End of preserved historical segment. -->
