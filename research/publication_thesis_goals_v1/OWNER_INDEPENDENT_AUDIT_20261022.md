# Loop D 四项 Goals 独立审计

审计日期：2026-10-22（Asia/Shanghai）
审计对象：agents_final_tech，提交 2ebdcc3e2d8f3f94e8045b3ad63f47d56bd52570。
性质：Owner 独立复核；不修改被审代码、论文、冻结结果或历史账本。

## 结论

本轮完成了有价值的第一轮可审阅交付，但没有完成四项长期 Goals；部分“已就绪”判断还需实质修正。

不能用“一小时、零新模型请求”判断工作无效：Paper E 的统计重分析和改稿确有进展。原任务又允许首轮零请求重分析和机制控制测试，并以“当前阶段成果可审阅”为交付边界，容易被执行者理解为一次短检查点。该边界应澄清，不能把全部问题归为没有执行。

但以下问题已经得到代码与实测证据支持：
1. Paper E 的最终 ICAART 包尚未满足其自称的格式与验收状态。
2. G2 的“目标结果实际消费”判据存在已复现假接受；当前十例也没有显示超越增强行为测试的增量。
3. G3 是手工状态表和预设动作成本上的决策模拟，尚无真实任务成本收益；对照还有不一致。
4. G4 漏掉原任务明确要求的五份现役架构与权限文档衔接。

## 验收矩阵

| Goal | 本轮真实完成 | 审计后状态 |
|---|---|---|
| G1 Paper E | 统计修复、内容修订、模板迁移、作者审阅包 | 科学修订稿可审阅；投稿包还需修格式、补最终包验收及私有 artifact 准备 |
| G2 正确性验证 | 一个旧真实迁移的三份旧模型响应 + 七个合成控制 + verifier 原型 | 机制原型需修正；尚无独立新真实迁移验证、尚无相对增强行为的增量证据 |
| G3 证据获取决策 | 11 个预设状态上的策略模拟 | 开发设计材料；尚未证明真实成本—风险 headroom |
| G4 大论文 | 中文审计章节和导师一页稿 | 两份正文材料有价值；原五份现役文件未衔接，后两项贡献仍候选 |

## 审计方法与新鲜验证

- 核对原 Goals、任务卡、提交 diff、源码、保存的行级 JSON、论文源文件和投稿清单。
- 三个独立子任务分别审查 Paper E、G2/G3 方法与代码、Goal/素材/架构衔接。
- 本机和 GB10 的 HEAD、origin/main 都是上述提交，检查时工作树 clean。
- GB10 重新执行本轮 11 项测试：11 passed。禁用了无关 pytest 插件，产生一条 asyncio_mode 配置警告；此项不是测试失败。
- GB10 重新执行预提交审计：PASS，但它打印 pages=10，实际审阅 PDF 为 12 页，证实脚本检查的是旧包。
- 独立复得 Paper E 保存数据的 UID 聚类区间。
- GB10 内存执行 G2 对抗性反例，未覆盖原结果文件、未新增模型请求。
- 校验实际 12 页 PDF hash，并渲染查看第 1、12 页。仓库文件未被本审计修改。

## G1：统计修复成立，投稿包不能判“只剩 Owner”

### 已证实的实质进展

282 条 table-run、219 次 flat 检出，来自 119 个 UID。UID 出现次数为 73×3 + 17×2 + 29×1。
20,000 次 cluster bootstrap 独立复得区间 [0.711744, 0.836364]。
UID 等权估计 0.7535014，区间 [0.683473, 0.820728]。
FinQA 两份 raw 都是 89 行、30 个 report clusters。MD、TeX 和中文章已同步。
这些是真实改进，不应因零新模型调用而抹掉。

### 必须修复

1. **字号与行距**：官方随包 Example 要求表格、参考文献 9pt；当前四张表使用 scriptsize，style 定义为 7pt，参考文献另加 linespread{0.8}。恢复官方设置后重新排版；如果超页，应压缩冗余内容。不能用缩字后的 12 页证明合规。
   - paper/icaart_2027_submission_v1/template/Example.tex:156、281
   - paper/icaart_2027_submission_v1/SCITEPRESS.sty:131
   - paper/icaart_2027_submission_v1/manuscript.tex:53、91、156、192、242
   另需规范表 caption、无编号 Acknowledgments。
2. **最终包验收作用域**：scripts/pre_submission_audit.py:28、36、47 读取旧 overleaf_bundle 的 TeX/PDF；artifact 检查只查旧计划与文件存在。现有 PASS 不能证明实际 ICAART 包的格式、匿名或研究 artifact 可复现。
3. **artifact 尚为计划**：私下组装匿名候选压缩包、许可证核对、清洁环境复现仍可自主完成；公开发布才需要 Owner 最终授权。DOI 是否必要应按投稿要求判断，不能人为升级成一切工作的前置门。
4. **清单与披露**：PACKAGE_MANIFEST.json 的 ../../paper 路径按文件位置解析不存在；真实主稿 hash 匹配。AI 披露应准确区分写作辅助、实验模型输出、分析脚本及人工真值，避免“AI created no experimental evidence”的绝对措辞。

无需为了完成这一轮 G1 额外增加第三案例。优先完成可实际提交的稿件和私有材料。

## G2：消费判定有已复现的核心漏洞

g2_contract_verifier.py:107–111 把下面条件当作“结果被消费”：
目标函数调用次数大于零，而且 UTF-8 与 Latin-1 两个固定输入均输出预期文本。
它没有干预同一输入的目标返回值，也没有追踪返回值是否影响后续计算。

GB10 内存反例：

~~~python
import cchardet

def _decode_data(data):
    cchardet.detect(data)  # 故意丢弃返回值
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("latin-1")
~~~

该实现没有消费 detector 返回值。现有 verifier 实际输出：
- target_calls = 2
- target_result_consumed = true
- extended_behavior_pass = true
- runtime_consumption = true
- hybrid = true

因此，“10/10 支持实际消费验证有效”的主张必须降级为“在既有十个开发控制上通过；判据存在对抗性假接受”。

另一项关键发现：保存的十例中，extended_behavior_pass 已经与 VALID/INVALID 参考逐一一致，也是 10/10；summary 却未列这一基线。因此当前结果没有证明消费判定比增强行为测试提供增量。

其他限制：
- 三个自然候选均来自同一 NtripBrowser commit，未新增独立真实任务。
- 预注入 cchardet 全局变量、只提取单函数，可能掩盖模块缺失 import，或误拒绝外部 helper 等合理形式。
- 已知控制与判据由同一开发过程构造，适合调试，不是独立资格验证。

下一步应先补反例和强基线，再检验同输入返回值干预、动态依赖/污点追踪等是否真正识别消费。对允许等价实现及异常回退的合同要事前明确，不能把“输出必须随任意 stub 改变”也当作通用真值。随后在 GB10 建立第二个可重建真实迁移，以独立参考裁决 VALID/INVALID/UNKNOWN。

## G3：模拟算术尚不等于真实 headroom

g3_decision_probe.py:31–35 的成本为手设 1/1/3/4。
Case.outcomes 与风险布尔值也由代码直接填写；:266–268 所谓 run 只读取该表，不执行 verifier、测试或环境探针。
所以 62 对 99 可以作为设计模拟，不能解释为实测时间、调用、token 或真实成本节省。

当前还有三项对照问题：
1. G3 将 alias/wrapper 的 simple_contract 手填为 False，而 G2 对相应形式的实际静态检查已经通过。两次“静态误拒”缺少一致的真实执行支持。
2. full_revalidation 在 preflight 已失败时仍计全部动作，造成可避免的基线成本虚高。应比较有合理短路的全量流程。
3. 风险标记缺少可复现提取器及取证成本；是否在实际动作前可得尚未证明。

0.8182 = 9/11，另两例是环境失败和预设未决状态的 defer。“11/11 correct”包含正确拒答，不代表十一项迁移成功。
错误放行指标还应覆盖环境无效/未决对象；加入 always-defer、增强行为固定策略等合理对照。

下一步应接入真实动作接口与执行日志，测量动作和风险取证成本。简单 greedy 或固定顺序足够时，应接受其结论，不以构造复杂策略为目标。

## G4：正文完成一部分，现役架构未衔接

原任务 docs/research/LOOP_D_PUBLICATION_AND_THESIS_GOALS_20261021.md:193 明确要求处理五份现役文件；从规划提交到本轮最终提交，这五份均无 diff：

- docs/research/THESIS_RESEARCH_ARCHITECTURE_v3.md：仍为旧“经验学习与持续适应”、DESIGN_ONLY_NOT_AUTHORIZED。
- docs/research/THESIS_EXECUTION_BLUEPRINT_v1.md：仍为 WP-0 只读、300 次待批旧范围。
- docs/research/THESIS_RESEARCH_GOVERNANCE_BASELINE_v1.md：仍写当前不允许实现/pilot。
- paper/research_asset_map_v2.md：当前索引仍保留旧投稿与四 RQ 路线。
- paper/thesis_manuscript_scaffold_v1.md：仍是评估引导蒸馏与自进化旧骨架。

应保留历史证据，同时更新现役状态或明确历史身份。否则后续 agent 容易再次被已经过时的权限说明阻塞。

素材复用表也应区分“实际读入/重新分析”与“拟复用”：G1 与 G2 有真实读取；G3 没有接入 Adaptive V3 runner，其他多项旧资产本轮主要只是列名。

## 继续执行与权限边界

本轮对 G2/G3 的账本记 host=local，新生成的控制/模拟数字尚未发现 GB10 原始执行收据。按既有执行面规则，正式新科研观测应在 GB10 留存；同步文件不等于执行 provenance。本次反例与测试已在 GB10 复核，但不会追溯修补旧账本。

“至少八个未见真实 families”可以是采样计划，不能被当作原任务规定的认证门槛，也不能阻塞先做下一个真实任务。原 Goal 要求按机制、效应、精度与任务可得性调整规模。

只有作者身份、实际投稿/付款、展示承诺、公开发布与必要学校认定需要 Owner。稿件修复、私有 artifact 复现、方法修正、真实开发任务与成本实测均可在现有授权内继续。未发现文档明确写“所有科研必须等待 Owner”，因此不能把它描述为已经证实的权限阻断。

建议后续顺序：
1. 先修 Paper E 字号、最终包验收与私有复现材料，保持两案例范围，尽快形成真正可提交版本。
2. 修 G2 判据、补增强行为基线和对抗控制；新增独立真实迁移，不先凑数量。
3. 将 G3 从手写模拟接到真实执行，补强基线，决定是否确有成本—风险空间。
4. 同步五份现役文件，把已经成立的测量审计与仍未成立的候选方法分清。

不以增加模型调用作为工作量目标；需要新候选、跨任务验证或模型比较时，自主调用即可。研究价值由新增可检验事实和解释力决定。

补充：SWE Refactor Bench（arXiv:2608.23564，2026-08-24）已明确区分迁移完整性与行为正确性，原 Goal 和本轮材料都已提及。不能把“行为加结构”本身算作新颖性，也不能仅凭它的摘要断言实际消费验证完全被覆盖。G2 仍需读全文后界定最小方法增量。

本报告没有执行新的模型推理、judge、训练、正式投稿或公开发布；被审 Git 工作树保持 clean。
