# 协调者操作约定

本目录根文件与 coordinator/ 仅供协调者及后续科学评审；不要把整个目录交给盲态标注者。当前没有任何人类标注或签名。

## 发放前

1. 阅读 README.md、DECISION_AND_PROTOCOL.md、PREPARATION_RECEIPT.json、VALIDATION_REPORT.json。材料检查通过仅表示可以组织标注，不表示 task gold 成立。
2. 登记 coordinator/annotator_roster.json 的两位真实独立标注者和第三位仲裁/科学评审。姓名可用研究代号，但须能由 owner 对应到实际人员；不得填写模型名作为人类。
3. 若人员不足或无法满足独立性，状态保持 AWAITING_HUMAN_ANNOTATION，向 owner 索取实际参与者，不发动 agent 模拟。已有旧标签暴露必须记录，必要时换无暴露参与者。
4. 只向 R1 发 exports/R1_stage1，向 R2 发 exports/R2_stage1。发送给人的具体渠道与收件人需 owner 指定；本包不自动发送消息。

## 收件与阶段封存

允许参与者在 CSV 或 JSON 中二选一填写。每人的每阶段仅选定一份正式文件；保留原始文件字节。协调者复制到 submissions/R1/stage1 或 submissions/R2/stage1，禁止覆盖既有文件，后续更正追加版本。

记录：实际人类代号、阶段、原文件路径、真实接收时间、实际 SHA256、case ID 集合、缺项/盲态声明、采用 CSV 还是 JSON。写入 coordinator/seal_log.json。示例格式和空数组不是封存证明；只能在收到真实文件后记录。

两人的 stage1 各含 12 个唯一 case ID，并且完成字段检查或明确标记不可答/不确定后，才分别发对应 stage2 目录。记录真正的 stage2 release 时间和获准收件人；系统当前没有自动强制权限，靠协调者逐阶段发放，不得声称目录分离等于已实施访问控制。

随后收 stage2；同样原件保留、不覆盖。Stage1 与 Stage2 合计 48 行阶段记录，表示 12 题 × 2 人 × 2 阶段；不是 48 个独立案例。

## 格式与内容检查

- 12 个 case ID 完整且无重复；R1/R2 对应不同实际人。
- 人工身份、真实时间、分钟数、先前暴露填写；时间与接收顺序无矛盾，分钟数不得为负。
- 每个 Stage1 填 answerability；ANSWERABLE 必须有答案、依据及相应单位/时期说明；其他状态必须说明原因。
- 每个 Stage2 填 reference_status、task_effect、perturbed_answerability、change_relevance。reference_status 不是 CONFIRMED 时不得给 PRESERVED/ALTERED。
- confirmed reference 必须有人工核验答案与证据；PRESERVED/ALTERED 必须有 effect_reason、扰动证据；不能只复制官方答案。
- cells 格式 rNcM，多项用分号；按表格实际边界核验。段落须能映射到包内 order/uid。坐标有效不代表语义正确。
- 数值、单位、scale、时期、对象、推导与容差均须有依据；允许显式 NOT_APPLICABLE，不用空白冒充不适用。
- 未完成不算 U；没有实际系统输出，禁止生成系统正确率/漏检率/误报率。

## 分歧与资格报告

使用 annotations/adjudication_template.csv 汇总 R1/R2 差异；不要覆盖原标注。比较 task_effect 之外，还要比较参考答案、单位、时期、证据、可答性。两人标签相同但依据冲突也须列出。

R3 针对具体证据裁决；无法解决时最终 UNDETERMINED，并保存双方理由。不能靠多数投票或第三个模型自动建立 gold。科学评审仍需检查一致案例的证据，避免两人共同误解。

收到完整人类记录后，另存 annotations/TASK_GOLD_QUALIFICATION_v2.json 和 QUALIFICATION_REVIEW.md；保留 v1 空模板。报告真实计数、分层 U/分歧/耗时、输入变化与任务相关性、原始参考问题、多表头干扰和规则修订建议。资格签名由真实评审提供，不由 agent 补写。

12 个诊断案例不估计总体率；不做显著性检验来声称泛化。若只出现 PRESERVED，应报告缺少有害任务案例，不能为了得到 ALTERED 换题补数。若需要修改任务定义，保留本轮结果为探索，另提设计，不在当前标签上回填新规则。

## Git、数据与远端

raw/、packets/、exports/、coordinator/、annotations/、submissions/ 是本地忽略目录。普通 git push 不会交付这些数据；不得声称三端数据同步。确需向另一台机器交付，先按 owner 指定渠道只传必需包，核对 PACKAGE_MANIFEST.json 中真实哈希，不公开原始或派生数据，不用 git add -f 绕过忽略规则。

本轮仅创建本地材料；未提交、未推送、未写入 GB10。旧 v4、原解释文件、论文与停止状态保持原样。后续 Layer-2、实际模型调用与稿件改动均需另行裁决。
