# 发票经验向 PDF/表格差异任务迁移：开发实验卡

2026-10-31；本卡先于本实验的模型请求，属于已经看过任务与参考结构的**开发实验**，不是盲选确认。目标是检查来自先前真实发票工作流的一条“先精确匹配完整标识”的经验，能否在新的文件比对工作流中被适当地使用；同时允许经验不提供增益或适用性不足。

## 来源与参考资格

目标为 SkillsBench v1.1 checkout `b63b7b2850226b6aa4fb5929a8c1ac7bc4d9a6af` 中的 `pdf-excel-diff`，与发票任务同 benchmark、不同任务，不是独立 benchmark；模型预训练曝光未知。任务要求从旧 PDF 和新 Excel 中识别删除与字段修改，数据生成器明确描述其为合成员工数据。任务源的顶层仓库为 Apache-2.0；它在 Dockerfile 中另行下载 [skillsbench-files](https://github.com/XuandongZhao/skillsbench-files) 数据仓库。数据仓库固定 HEAD `2982259afd39ec77df4c324bd29208f77986e9de`，没有发现单独 LICENSE，数据许可**未确认**：原文件仅保存在 GB10 研究证据目录，不加入 Git 或重新分发，不用来训练。

我们用数据仓库的原始 Excel 与当前 Excel **独立于 benchmark 的 expected JSON 重新计算**：原始 10,500 条、当前 10,485 条，15 删除、20 字段变化，与 expected 的 ID、字段、值全部相符；旧 PDF 经 `pdftotext` 提取 10,500 个唯一 ID，与原始 Excel ID 集合一致。详细 hash 和计数见 [资格结果](../../pdf_excel_reference_qualification_20261031.json)及[脚本](../../qualify_pdf_excel_reference.py)。这一核对只验证 PDF 的 ID 集合，尚未逐字段证明 PDF 等于原始 Excel；两个表格和 expected 仍来自同一公开数据制作链，不是人工或独立自然业务 gold。

## 三个条件和资源

1. `no_memory`：只提供任务说明、旧 PDF、新 Excel 和相同的本地工具。
2. `prior_experience`：在相同任务、输入与工具之外，增加先前发票真实错误和修复的简短经验：先核实完整名称/标识再决定是否模糊匹配，按当前任务判断适用性。当前任务的五位员工 ID 结构已在任务说明中，经验未必提供额外有用信息，也可能被忽略。
3. `task_skills`：提供该任务公开 PDF 与 XLSX skills。它含更多信息，仅作任务专属能力参照，不与其他条件作信息等量因果比较。

使用同一 OpenCode + GB10 本地 Qwen3.6-35B-A3B、独立启动的无外网 Docker、同一输入字节、Python/pypdf/openpyxl 环境和写权限。每组最多 **16 次被转发的模型 HTTP 请求、900,000 字节累计 POST 请求体、每步 8,192 输出 token、600 秒进程超时**；同时保留拒绝原因、服务失败、全部 raw、usage 和墙时。GET 请求也占接口计数，原始输出可能包括缓存 token。环境是适配执行，未声明官方 BenchFlow 和原 Dockerfile 完全等价。

原始 Excel、benchmark expected JSON、任务 verifier 和参考解都不能挂到 Agent；Agent 停止后，在单独无网 verifier 容器运行原测试，并由单独评分器与完整 expected 对照删除、变化键与值，报告漏检、误检、格式与无输出，不能将测试项数量当独立样本。任务原输出要求“按 ID 排序”；另查顺序、重复项和键值类型，避免合约漏洞。

## 判读

每组先做 1 条探索，全部为同一个合成任务实例，不计算跨任务显著性或方法收益；只观察交付、输出质量、经验是否实际被使用及总成本。task skill 信息量不同；有差异先检查工具调用、参考与上下文。不存在输出时如实保留并检查截断、依赖、代理预算，不以失败计准确率。若经验无用或有害，在后续不同任务族加入可迁移/不适用条件与强简单规则，而不是在本样本反复改提示。任何事后新增条件均另记，不改写本卡。
