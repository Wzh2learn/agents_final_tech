# Django：8B真实执行与经验迁移开发

> 2026-11-06 | 本页在首次模型执行前创建，原地维护本批合同与结果。前置[资格](DJANGO_AGGREGATION_PAIR_QUALIFICATION_20261106.md)已经跑通原题base/gold；它不是Agent成绩。Paper E不在本批修改。

## 问题与比较

在同一8B执行器、相同工具和预算下，从真实源任务形成的历史、实际补丁/反馈和普通skill，能否改善后续同类但发生版本变化的目标任务？先运行无历史source12589，再比较target34176的无历史、源历史、补丁/结果卡、普通skill。记录问题完成、回归、原题结果与总成本；若无历史已完成，比较实际成本和破坏，不能把更少POST自动视作更低成本。

source seed7201、target seed7202，temperature0.2，每episode48POST/1200秒/6MB累计请求体；8B context32768/output8192，单slot、禁止context shift、沿模型模板的thinking配置。普通skill由本批实际source形成，其模型、输入和额外调用单独记录；不得复用公开旧轨迹或以前已曝光source。失败source也可提供经验，但须如实绑定失败状态，不虚构已修复。独立新attempt保留raw、候选、评分、截断和拒绝，不自动覆盖/重跑。

此对及参考已暴露给研究者，属于开发；两任务不是两个独立来源。本轮不据一个目标认证普适学习方法或跨来源泛化。新方法仍需与最强普通载体、简单规则和公开近邻比较，适用的留出与重复按[现役计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)继续。

## 冻结环境与可读面

私有根`/home/testuser/wzh/research_evidence/agent_learning_20261030/django_aggregation_agent_20261106/`。

| 输入 | SHA-256 / 配置 |
| --- | --- |
| source依赖投影v1 manifest | `387f9d8f11bb154c3b5cb77fd94dd5bb7cd898bf7e6383dabad43052a6ad4483`，Python3.8；完整评测暴露缺依赖，未用于模型执行 |
| source依赖投影v2 manifest | `f76dc69ba650e61c49a81611392dabf15b65c5d67b7c8fc0ae03bac10c10c16c`，保留旧投影，加入原环境已有typing_extensions/pytz |
| target依赖投影manifest | `196a1cfb4cb2d98fddb66ac56bed81ee90868b8e608fc15055b0e051f8a33efc`，Python3.10 |
| 模型profile | `acce24743e43c205b605b8bceddd4f5eb756d93fdba5f58e28bc32ba772ab6d0`，独立loopback18104 |
| 8B GGUF | `d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785` |
| PG socket manifest | `5a47eae155b38533536563543deb2b2e12e938ba95be81509894b60f97ad35c5` |

actor使用冻结base源码、无Django安装包/原site-packages的独立runtime及依赖投影；不挂未来Git、参考补丁、隐藏测试或外部研究目录。模型通过受限UDS代理，仅转发本批18104。source PostgreSQL仅使用新建专属容器的Unix socket，actor和DB均`--network none`，无TCP监听/宿主映射，不连接业务DB。无密码的local trust只在该独占socket范围内使用，不是通用安全认证。目标用SQLite，不承接源数据库状态。

Python、Django源码导入和source跨容器socket查询在零模型预检中实际通过，`actor_environment_preflight.json`保留stdout/hash。PG版本本批已用SQL实测15.17，是原题11的适配。只读挂载socket仍可连接；源码与依赖均与固定manifest核对。评测在actor退出后独立副本恢复冻结测试；原题probe仅改连接环境、不改SQL与期望，并消除源actor残留数据库状态。

## 工程诊断与成本

两次PG初始启动因镜像初始化脚本固定使用标准socket目录而失败；退出码、日志和两个失败回执保留。绑定标准`/var/run/postgresql`后第三次启动成功，未发生模型调用。该新环境仅有1次模型health GET，0生成；先前小模型资格7POST/44,800tokens归[独立资格批次](QWEN4B_TOOL_QUALIFICATION_20261106.md)，不算本批方法结果。

更完整的gold预检发现，顶层`import django`通过不能保证测试路径可运行：source的asgiref需要`typing_extensions.ParamSpec`，隔离后原环境的隐式依赖消失。v1失败记录保留，v2仅从原Python3.8环境补typing_extensions与Django3.1所需pytz，不恢复整个site-packages；新投影仍排除Django安装源码。target完整路径另核。准备阶段问题不计作Agent任务失败。

当前检查点：实现和验证新runner，提交固定代码后运行真实source；随后冻结源经验再执行目标比较。运行期间不改已启动harness及其绑定组件，不把预检或候选生成当方法成立。

## 运行器资格（首次生成前）

[新runner](../run_django_aggregation_agent_20261106.py)与[合同测试](../../../tests/test_django_aggregation_runner.py)已核对。远端8项定点测试通过（含Python3.8投影）；无历史source/target已接入自动记录、完整外层/组件快照和退出后独立评测。经验冻结与skill形成接口尚未实现，非none条件明确拒绝，不能把预定四臂写成已执行。

完整合成gold控制：source关键1/1、可映射回归65/65与新PG评测库原题均通过，target关键6/6、回归166/166与SQLite原题均通过。`preflight_django_runner_20261106_v2/receipt.json` SHA `878d825dac2758bc74ce079cac759daa005643435081cf473ed2f6ae43cf4a36`。随后base控制保持原题/关键失败、回归通过，实际合成请求验证18104模型及7201/7202种子转发；v3 receipt SHA `7c710cf5530ea7a5c27651c83885f4f448156e977725cd9ae8e861ba0005fb01`。这两批均0科研生成，非模型成功样本。
