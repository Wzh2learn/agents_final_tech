# Loop D 接任执行后的负责人增量复核

状态：`REVIEWED_WITH_CORRECTIONS / PAPER_E_INTERNAL_WORK_CONTINUES`

日期：2026-10-28，Asia/Shanghai。复核固定起点：集成分支`c33c14bf85dda6defbe374ce8976192dc7a047a5`。本地离线范围；未连接GB10验证本轮运行，未派发A/C，未新增科研生成、训练、judge或外部动作。本文是证据与裁决；唯一执行指令仍为[LOOP_D_RESEARCH_PROMPT.md](../../../research/LOOP_D_RESEARCH_PROMPT.md)。

## 接受的实际进展

Paper E的修复有实质价值，不是只补汇报。负责人本地重放：

```powershell
py -3.11 -X utf8 research/word_scoring_new_family_20261027_v1/paper_e_word/build_revision_v2.py --check
py -3.11 -X utf8 research/word_scoring_new_family_20261027_v1/paper_e_word/verify_revision_v2.py
```

结果：源重建一致；结构/算术定点检查PASS，6步清单、4表、3图、24条引用及28项算术检查通过，声明仍有10个Owner占位。此检查不等于全文科学同行评审或负责人再次逐页目视验收。GB10 LibreOffice渲染、14页逐页检查及C耗时沿用D回执身份，不扩大为本次负责人重新实测。

C审`08be0547`并给出CONDITIONAL；D后续修订未经再次独立复审。这个边界保留。剩余图像与声明缺项仍不能写为最终投稿包已达标。

## 必须纠正的六点

1. **C额度耗尽不阻断D修图。** 原指令已经授权内部修订、现成工具渲染和D处理C意见后自验。SVG重导出、题注归位和重渲染均在此范围。D需核图像类别和最终尺寸，保留科学标注，更新派生hash链并检查新页面；不能以更改DPI元数据替代源重导出。没有新增C额度，不冒称新包获得独立C PASS。
2. **主工作树的路径冲突不是论文工作前置审批。** 123个未跟踪Word文件原位保留；现成干净集成worktree可以继续修稿。负责人本地核起点：集成分支c33c14bf，主工作树main f0c246df。当前不移动副本、不强制checkout，也不宣布所有main已一致。跨机状态由D在实际同步后记录。
3. **新实验卡读错单位字段。** 固定`exposure/PANEL_FREEZE.json`的raw Git blob SHA-256为`501e6feba30d823ba5f8e98295225a247f42e0ef27e0c577fd73e2ae13771dde`；Windows工作树换行转换后的字节SHA-256另为`96a5f5b1587e04853bfb48924348c1c7d89dbfe0d42809cae3f6b28a87f81b00`，两者不能混称。`unit_reference`不存在；8/8存在`unit`，分布percent=3、thousand=1、UNKNOWN=4。`diagnostic_rescore.py`也读取实际`unit`。因此撤回“单位全部未冻结”，但不把明确标签自动认证为正确。
4. **分段统计支持混淆诊断，不识别因果效应。** 复算既有24行分段JSON得到D/T/M推理均值432.875/460.375/453.125、答案均值51.25/44.625/58.875，推理未闭合2/3/3。独立分段重tokenize后与usage总量分别差-4/-1/0 token，必须披露边界与tokenizer口径。thinking与不同合同长度仍共变，不能仅凭D4/T1/M0宣布合同长度造成差异。`reasoning_tokens=None`缺的是细分；推理已在output总量内，不重复追加到历史账本。
5. **格式率持平不能触发“无机制增益”。** 现卡“合同可满足率差≤1 UID就停止M”错误。格式合格后才比较T/M的完整语义正确、修对/破坏、合理未知、风险覆盖与成本。8族开发样本不支持方法成立或“可发表负结果”的承诺。
6. **35请求预算不是完整硬帽。** 35=3 smoke+24主运行+8 D-long；输入预算却只取旧24条28,074的110%，未覆盖全部新prompt。每次允许重试1次也没有计入物理请求帽。35次无重试的输出算式16,512正确，但整个预算未闭合。D先离线重设计、枚举和记账，不直接开跑；D-only长预算不足以识别T/M输出负担。Owner不必代替D选schema、thinking开关或单位判据。

## 单位复核的精确范围

以下是冻结参考侧元数据，未进入新的模型输入，也未修改参考或评分：

| UID前缀 | answer_type | 实际unit |
|---|---|---|
| 57f38b17 | arithmetic | percent |
| 62bb8d90 | span | percent |
| 177fcc7a | span | UNKNOWN |
| b27a5513 | multi-span | thousand |
| f4acbb7e | multi-span | UNKNOWN |
| 90f9af10 | arithmetic | UNKNOWN |
| 49e5b466 | arithmetic | UNKNOWN |
| 24e5a96b | count | percent |

期限span与count的percent标签是待逐题复核的语义疑点，不是负责人已完成的新gold裁决。UNKNOWN也不能直接推论为不可回答；先核可见事实、量纲与尺度，再决定新版本的参考和PENDING规则。参考更正不能作为隐藏gold泄入actor的理由。

最小复算方式：读取上述固定JSON的`references`，分别统计`'unit' in row`、`'unit_reference' in row`与`Counter(row['unit'])`；不得用`get`不存在字段得到的全None推出来源缺失。

## 已执行与接下来执行分开

本次负责人实际执行：本地固定文件读取、上述源/定点检查、字段统计、既有分段均值复算，以及现役指令/状态的增量修订。未重新渲染图像、未生成新的DOCX/PDF、未改历史raw/参考/分数或原manifest、未派C、未验证GB10运行。

补充验收：字段正例与错误字段负例控制通过；变更文件链接按工作树/Git树核验通过；版本化secret scanner仅扫描本轮8份变更文档/技能源，结果clean，合成凭据形状正例正确返回1。没有读取`.env`。本地`git diff --check`通过。

全量`docs_lint`本次实际为FAIL，146 fail/0 warn：145项索引目标在稀疏工作树未展开，逐项在Git树中存在；另1项为稀疏checkout的skill source missing/安装比较。没有扩大checkout、改变lint或同步机器安装来消除这些报告，不能复述为本轮0 fail/0 warn。技能源契约补充已纳入本次变更，机器安装未同步，后续分发需依现役规则另行处理；此范围不阻断D修论文。

下一步交D：先完成三图和对应稿件重建、自验、manifest；再原地纠正离线实验卡。内部包可交作者后，作者/单位/声明、渠道确认与正式提交仍由Owner办理；不再把内部图像重导出列为Owner许可项。新科研模型预算保持未授权，A/C保持29/29。

长期仍以尽快发表Paper E、2027年10月学硕送审为目标。C2/C3尚未成立；不将格式修复或治理包装成创新点，也不凭受混淆的旧面板关闭整个研究问题。
