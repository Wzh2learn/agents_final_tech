# SymPy：成功经验能否迁移到后续变化任务

> 2026-11-06 | 开发比较；现役计划见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。本页是本对实验记录，不是新prompt或新Goal。原始源运行及计量修正见[Django批次的当日接续](DJANGO_AGGREGATION_AGENT_20261106.md#current-27b-handoff)。

## 问题与事前比较

Qwen27B已经实际修复源任务14774。现在检验：这些真实执行与反馈形成的历史、结果卡或普通skill，能否帮助8B完成后续19235任务？比较无历史、普通历史、结果卡和模型生成skill，所有目标从相同base开始，seed7202、temperature0.2、32K上下文、8192输出上限、48POST/1200秒/6MB，使用同一8B服务/隔离依赖。先固定三种经验再开始任何目标臂。

这是表示与经验利用的开发对照，信息量并不等同，不能直接解释为纯格式因果效果。普通skill与历史本身都不是新方法；后续候选还须超过最强简单策略和公开近邻。source题面直接提示修法，target引用前序PR；D已知参考，不能称跨来源、预训练隔离或独立确认。

## 已核实资产

- 数据资格：`sympy_latex_qualification_20261106/FINAL_QUALIFICATION.json` SHA `941e2cc1f44ddb77059d6feb6a51669b7e5cab39cb8456a832231b998ba974e7`。source base `8fc63c2d71752389a44367b8ef4aba8a91af6a45`，target base `226b942f0748819d5d2d723b91591fed4975961c`，时序祖先已核。
- 真实源：私有`agent_learning_20261030/sympy_latex_agent_20261106/attempts/teacher27_source_v1`；completed SHA `9d3d0e74502346202ab76bf4bef859eeb2bc8a06940ddf80a8038555e5e72a7e`。17POST、148,213 provider tokens；17响应用量完整。原题probe、focus1/1和114回归均通过。只改原有`printing/latex.py`与其测试，测试基础设施未改。
- 源历史33,614bytes，SHA `2acccd038177a67d4a7d23153cbf92699c804895ab95d5e3c54b3fb3cfb654b2`；结果卡9,171bytes，SHA `d6c0617f4e66ed3e72ee4d8f77e3b4782dba35c3b7b0a240ff0a3231831bbb53`。两者绑定实际source task、完整实际diff与独立结果；历史另含带status/error的截取动作。模型skill尚待生成。
- 独立目标控制：`transfer_controls_20261106_v1` receipt SHA `456fea9e02d3217ec6d0b0ec5a5da2fb938c70a586171f57781e4364248f33f4`；base原题/focus失败，gold通过，两者142回归通过。原144项中的`test_issue_13559`与`test_issue_8470`均为两臂共同的Python3.8 AST问题，按原资格排除，不改口为144全过。
- actor只读指定任务、baseline、无SymPy wheel的依赖投影及选定经验；隐藏测试、参考patch与evaluator不进入actor。目标评测在独立副本恢复原有嵌套tests和配置，再应用隐藏测试；原题语义probe另核。

执行器：[源](../run_sympy_latex_agent_20261106.py)、[经验与目标](../run_sympy_latex_transfer_20261106.py)。私有经验目录`.../sympy_latex_agent_20261106/source_experience_v1`，目标目录`.../transfer_attempts/<attempt-id>`；以各自manifest、raw、请求/响应及回执为准，不覆盖旧输出。

## 判定与成本

主要结果要求原题语义、focus和142项适用回归同时通过；agent正常退出或自称完成不替代验收。未运行、语法/接口失败、未读取经验分别记录。观察实际经验读取，不把读取直接当作语义使用。

成本保留按模型区分的请求、provider tokens、缓存及实际用时；provider和公开步骤的同一用量不相加。目标边际成本与完整冷启动成本分列：冷启动经验臂计入17次源采集，skill额外计其形成请求；已有源经验情形只比较各载体新增形成与目标成本。来源共享物理账本只记一次。Django与源采集曾共享GPU，不用这部分wall time主张延迟优势；目标臂串行，若出现成本信号，再重复顺序/seed验证。

## 后续分支

- 某种经验有成功率增量：先复核具体行为与普通历史/卡的作用，再做内容消融、重复和另一项目，不能以单任务认证方法。
- 全部成功、只有成本差：核对缓存、读取与形成成本后复验；普通历史若已解释收益，保留其为强基线。
- 全部失败：区分小模型能力、任务参考、工具接口与经验适用性，必要时用较强模型作诊断，不外推经验学习无效。

当前只有合格源与目标资格，目标实验尚未执行；全局方法贡献仍未成立。
