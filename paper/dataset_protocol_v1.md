# 小论文数据集选择与分层协议 v1

> 状态：数据准备权威素材，尚未批准下载/构建 | 核验日期：2026-09-23
> 边界：本轮只做公开来源核验、选择和合同设计；未下载新数据、未读取 GB10 私有语料、未生成或上传数据正文。TAT-DQA 冻结线不重开。
> 可机读来源快照：`docs/datasets/paper-public-source-registry-v1.json`。其中 commit 是 2026-09-23 的核验锚，不是下载许可或永久最新版声明。

## 1. 结论先行

近期小论文的数据路线建议是：

1. **TAT-QA 保留为 Stage E 历史主域和 proposal 素材，但既有 train+dev 混合池全部标 `HISTORICAL_ONLY`**；先在 GB10 用公开 UID 回溯已消费范围，不能把旧池重新命名为独立验证集。
2. **不存在一个公开数据集能同时覆盖三阶段**。FinQA 是 P0 过程来源：同属金融表格/文本并带 gold reasoning program，适合 Stage E 的 checkpoint/过程监督；这些 program 不是 `map_to / hold / skip` 标签，未经 adapter 与 Q3 复核不能直接训练动作头。
3. **Valentine 的 NYC schema-matching benchmark 是 P0 动作来源**：它提供真实表对、gold column correspondences 和 COMA/Cupid/Similarity Flooding 等强简单基线，直接贴近 Stage D/R 的 `map_to`。但 gold match 只直接支持正向映射；`skip/hold` 仍需 Q3，且 NYC 上游许可和 LLM 扰动 provenance 必须先审。
4. **MultiHiertt 作为 P1 条件外部过程来源**：多层级、多表、长文本和细粒度 supporting facts/program 与长流程评估更贴近，但正式获取前必须确认数据包许可范围与 private-test 使用方式。ConvFinQA 直接由 FinQA 问题分解/组合而来，二者默认视为同一 independence cluster，不能冒充独立测试。
5. HiTab 只作跨域层级表扩展；GitTables/Sherlock 只作自然表头、语义类型或预训练候选池；HybridQA/OTT-QA 只作大范围外部压力。PubTables-1M 解决视觉表格结构，不解决语义规则动作，体量又大，本小论文不下载。
6. **不新造另一个漂移注入器**。仓库已有 `scripts/research/drift_inject.py`，后续应做 split-preserving v1 适配，而不是改动已产生历史结果的 v0。合成数据只进入训练/机制压力测试，不能冒充真实独立评测。

## 2. 两个正交维度：质量等级不等于实验 split

“黄金级、训练级、评测级”若只做一条层级，会产生同一批 gold 被反复调参又拿来终评的问题。这里冻结为两维：

### 2.1 标签质量等级

| 等级 | 定义 | 允许用途 |
|---|---|---|
| Q0 来源级 | 官方原始数据、公开 ID、许可、版本与 hash 可核；尚无本文动作标签 | 资产盘点、待标注 |
| Q1 合成/弱标级 | 确定性变换或教师建议，标签来自变换程序/自动规则；保留 source pointer 和 generator hash | 非主实验软件/训练链 smoke、候选生成与机制压力测试；不得进入 Phase 1a 接收包或 A1/A2 主训练 |
| Q2 单审级 | 一名人工复核 action/target/来源，冲突未必已裁决 | pilot、错误分析；不作最终 gold |
| Q3 黄金级 | 两名独立复核者 + 第三方裁决或一致结论；许可、来源、标签、去重均通过 | 训练金标子集、gate、sealed；具体用途仍由 split 决定 |

Q3 是标签质量，不是“测试集”。Q3 样本一旦分到 proposal/train，就不能再移到 sealed test。

### 2.2 实验角色层

| 层 | 可做 | 禁止 |
|---|---|---|
| proposal/train | SFT/DPO、内部 UID-dev、简单基线开发、候选生成 | 充当最终泛化证据 |
| gate-validation | 冻结门后的接受/回滚、有限次数校准 | 训练学生、反复调阈值、冒充 sealed |
| sealed test | 系统/阈值/规则版本冻结后一次只读终评 | early stopping、选模型、更新规则 |
| future replay | 冻结后新增独立 UID/时间批次的前瞻只读评测；尚未到来时允许空层 + 哈希绑定获取协议 | 回流本轮结论；揭封后继续称未见数据；把空层伪造成长期证据 |

每个样本必须能由 label ledger 的 `quality_grade` 与 manifest 的 role layer 联合解析其“质量 × 用途”，不在 ledger 中重复一套 `role_layer` 字段。通用素材的最低口径为：训练链 smoke = Q1 以上 + proposal/train；黄金级 = Q3；Phase 1a 接收/可学性与 A1/A2 主训练 = Q3 + proposal/train；评测级 = Q3 + gate/sealed/future 中一个明确角色。

## 3. 已核验公开数据候选

### 3.1 选择矩阵

| 数据集 | 官方事实与标识 | 许可核验 | 对本文的价值 | 裁定 |
|---|---|---|---|---|
| TAT-QA | 16,552 问题、2,757 个金融表格+文本上下文；arXiv:2105.07624；官方仓库 `NExTplusplus/TAT-QA` | 官方 README 明示数据 CC BY 4.0；仓库 API 为 MIT（代码） | 已有 95 表/118 注入 Stage E 资产；适合金融表头漂移和历史可比 | **核心但历史污染需审计**；旧 train+dev 池不作独立 gate/sealed |
| FinQA | 金融报告 QA，带 gold reasoning programs；arXiv:2109.00122；官方仓库 `czyssrs/FinQA` | GitHub API 标 MIT；数据条款未在本次 README 片段单独区分，获取时复核 | 补过程级监督、数值链和新鲜金融来源；program 不等于规则动作标签 | **P0 过程来源**；优先做许可/版本/UID preflight |
| ConvFinQA | 把一个或两个 FinQA 问题分解为多轮会话，保留 original program 与来源标记；arXiv:2210.03849 | GitHub API 标 MIT；数据适用范围获取时复核 | 可测长程上下文和过程状态，但继承 FinQA 来源 | **P1 关联扩展**；与 FinQA 同 cluster，不作独立 test |
| MultiHiertt | 多层级、多表、长文本，带 program 与 supporting facts；arXiv:2206.01347；ACL 2022 官方引用 | GitHub API 标 MIT，数据由官方 Drive 分发；数据包范围需下载前再核 | 更强长流程和跨表推理；适合 dataset-held-out 外部验证 | **P1 条件来源**；许可与 private-test 路径清楚后接入 |
| HiTab | 当前 README 写 10,672 samples/3,597 tables；arXiv v3 摘要写 10,686，存在版本差异；arXiv:2108.06712 | README 明示 Computational Use of Data Agreement v1.0 | 跨域层级表、header hierarchy 和公式标注 | **P2 条件扩展**；先冻结版本并过许可门 |
| PubTables-1M | 575,305 页、947,642 张完整标注表；arXiv:2110.00061；官方 Microsoft Table Transformer 仓库 | 代码仓 MIT；数据在 Microsoft Research Open Data，数据条款须单独确认 | OCR/结构识别、header bounding boxes；不直接提供本文动作/目标语义 | **本小论文不下载**；留大论文视觉补盲 |
| Valentine NYC | schema matching 工具与实验套件；当前仓含 10 个 NYC Open Data 表对、`ground_truth.json` 与 LLM 扰动轨迹；arXiv:2010.07386 | Apache-2.0 覆盖仓库；NYC 上游数据与派生扰动范围仍须单独核 | 与 `map_to` 动作及 exact/fuzzy/COMA/Cupid/Similarity Flooding 基线最贴近 | **P0 动作 pilot 来源**；正向 gold 可用，`skip/hold` 不自动补 |
| GitTables | GitHub CSV 大规模关系表语料，带语法/语义标注；arXiv:2106.07258 | 仓库 API 标 CC0-1.0；逐表来源与再利用边界仍需审计 | 自然表头覆盖和语义类型预训练；无天然 pairwise match gold | **P2 proposal/pretrain only**；不作 sealed gold |
| Sherlock/VizNet | 686,765 列、78 个语义类型；arXiv:1905.10688 | 代码仓 MIT；VizNet 上游范围另核 | 强语义类型基线，可帮助候选召回 | **P2 baseline only**；类型标签不等于字段映射 |
| HybridQA / OTT-QA | Wikipedia 表格+文本多跳 QA；arXiv:2004.07347 / 2010.10439 | 两代码仓 GitHub API 标 MIT；数据范围另核 | 可作跨域检索/长流程压力，不直接给规则动作 | **P3 大论文候选**；不占小论文主路径 |
| TAT-DQA | 已有 `joint-v1` 数据卡，CC BY 4.0，仓外约 1.5 GiB | 仓内数据卡已核 | 文档视觉 QA 和大论文跨数据流 | **保持冻结**；本批不重开 D4、不下载、不重建表层 |

### 3.2 来源核验记录

- 论文元数据通过 arXiv 官方 API 于 2026-09-23 查询。
- TAT-QA、FinQA、ConvFinQA、MultiHiertt、HiTab、Table Transformer、Valentine、GitTables、Sherlock、HybridQA 和 OTT-QA 的官方 GitHub README/API 或 `git ls-remote` 于同日只读核验；精确 head 见可机读来源快照。
- HiTab 当前 README 与 arXiv v3 的样本数不一致，说明版本会漂移；未来数据卡必须写 commit/release hash，不能只写数据集名称。
- ConvFinQA README 明示其简单/复杂会话由一个或两个原 FinQA 问题分解而来；FinQA 与 ConvFinQA 在完成 report/question UID 去重前不得跨 train/gate/sealed 角色。
- Valentine 当前仓的 NYC benchmark 含 10 对真实来源表、gold correspondences 和基于 LLM 的 schema/value perturbations。它与动作任务高度贴合，但不是天然三分类金标：未匹配列不能自动等同 `skip`，近似候选不能自动等同 `hold`。
- GitHub 仓库 license 可能只覆盖代码，不能自动推定所有第三方文档内容；每次实际获取仍须保存数据页条款和时间戳。

## 4. 小论文最小数据组合

### 4.1 推荐组合 A（最现实的双来源最小闭环）

| 角色 | 来源 | 构造 |
|---|---|---|
| 历史机制复现 | 现有 TAT-QA 95 表/118 注入 | 仅复算历史，不改 split、不升级证据 |
| Stage E 新过程来源 | FinQA train/dev | 用 gold program/supporting evidence 设计 checkpoint adapter；不直接转成动作标签 |
| Stage D/R 动作 pilot | Valentine NYC 10 个表对 | ground-truth correspondence 只生成 `map_to` 候选；负例/歧义例经 Q3 才生成 `skip/hold`；先作 proposal/dev，不直接作 sealed |
| proposal/train | 经 UID 暴露审计后的 TAT-QA official train + 获批的 FinQA/Valentine 独立组 | Q1 只作非主实验 smoke/候选池；Phase 1a 与 A1/A2 仅用 Q3 人工金标子集；同表 clean/mutant 不跨角色层 |
| gate-validation | 使用未参与历史开发、完成 Q3 且达到最低 UID/家族门的独立来源组 | 当前 Valentine NYC 10 个表对只登记为 `PILOT_ONLY` proposal/dev 候选，不同时承担 gate；后续新增且按完整 origin cluster 隔离的独立批次才可申请 gate 角色 |
| sealed test | 从未用于规则/阈值/写作判断的独立 dataset/document UID | 全部 Q3 或官方 gold 可验证映射；一次只读；不得把 ConvFinQA 当 FinQA 的独立来源 |
| external transfer | MultiHiertt 的独立文档族 | 只作过程外部效度；不参与主阈值选择 |

如果无法从旧 TAT-QA 池复原 UID 暴露，TAT-QA train/dev 全部降为 historical/proposal，不能再承担 gate。FinQA 的过程样本与 Valentine 的匹配样本**不能按行拼成一个假装同分布的数据集**；二者分别回答 checkpoint 外部效度与动作策略可学性。RQ2 的 A1/A2 只能使用同一母池中同时具有“checkpoint evidence + Q3 teacher action/target + Q3 outcome/correctness”的样本；缺少这座同样本桥时，两路结果只算互补预研，RQ2 标 `NOT_IDENTIFIED`。跨数据集构造差异要单列，不能把 domain shift 误写成方法效应。

### 4.2 最低 action 构成

- `map_to`：候选目标正确且来源可追溯。
- `skip`：候选目标明确错误或不存在合法目标；不能只生成明显乱码负例。
- `hold`：在当前可见信息下至少两个目标合理，或证据不足；需要人工复核，不能由 confidence=`medium` 自动产生。
- Valentine 的 `ground_truth.json` 只可机械生成正向 `map_to` Q1 标签；未出现在 ground truth 的列对只是候选负例，完成 Q3 前不能直接标 `skip`，更不能自动生成 `hold`。
- 冲突族：同一表面别名在不同文档上下文指向不同 canonical，专门检验 collateral 与 gate-validation。
- 未见族：至少按 perturbation family 或 dataset family 留一类，不在训练/阈值选择中出现。

训练集可以含可追溯的合成正例与反事实负例；gate/sealed 的主结果必须把“程序生成且人工确认”和“自然出现且人工确认”分层报告。若后一类不足，只能声称 controlled perturbation benchmark 上成立。

## 5. split-preserving 合成方案

现有 `scripts/research/drift_inject.py` 的 v0 输出记录为 TAT-QA train+dev，且历史结果已依赖它。不要原位修改 v0。后续 v1 适配应遵循：

1. **先 split 后变换**：输入必须带 `dataset_id/source_split/document_id/table_id`；组键为 document/table UID。
2. **一母多变不跨层**：clean、所有 mutant、教师轨迹和规则事件继承同一 `role_layer`。
3. **正例与反事实分开**：确定性变换得到 `map_to` Q1；错目标对只标 `synthetic_counterfactual`，不得作为自然错误统计。
4. **hold 不自动臆造**：由双人复核的歧义案例产生。
5. **八类压力族**：v0 六类 alias/mixed-language/unit/date/OCR/prefix，加 collision 和 no-valid-target；family 定义在生成前冻结。
6. **字节复现**：固定 source hash、generator commit、seed、规则词典 hash；双跑逐字一致。
7. **产物位置**：数据正文、逐样本输出、下载包和人工批注均在 GB10 Git 外；Git 只放 data card、public-ID manifest、schema 和聚合收据。

只有通过 Phase 1 数据合同后才实现/运行 v1 数据构建器。当前直接合成更多样本只会放大未经裁决的标签和 split 问题，价值低于先补 provenance 与 Q3 gold。

## 6. Phase 1 canonical schema 与唯一派生链

唯一权威链路是：**人工标注源 → package label ledger → learnability view**。人工工具可以有自己的 UI/导出格式，但进入 Phase 1 时必须先无损归一为下面两类 v2 记录；learnability view 只能从已验收 ledger 与已绑定 source/schema/confidence 工件派生，不能再成为第四套标签权威。

### 6.1 Manifest lineage row

每个 split 引用严格包含：

```json
{
  "sample_id": "stable sample hash",
  "uid": "sha256(canonical dataset_id/revision/lineage_root_id)",
  "dataset_id": "source namespace",
  "dataset_revision": "immutable release/commit/hash",
  "source_split": "official source split",
  "independence_cluster": "source-namespace:stable shared-origin group id",
  "lineage_root_id": "stable report/document/table root",
  "transformation_parent_id": null
}
```

`uid` 不是自由文本；由规范化的 `dataset_id + dataset_revision + lineage_root_id` 计算。同一母表的 clean、mutant、轨迹和派生表继承 lineage root。`independence_cluster` 是**具体共享来源组**，粒度应为 report/document/table family，例如 `finqa_financial_reports:<shared-report-id>`，不是把整个 FinQA 或 Valentine 数据集写成一个簇。来源注册表中的 `independence_cluster_namespace` 只提供前缀；FinQA/ConvFinQA 等若追溯到同一报告，必须生成同一个完整 cluster。验收允许一个完整 cluster 位于 proposal/train 的内部 train/dev，但禁止它跨 proposal、gate、sealed、future 角色层；UID 与 lineage root 仍不得跨任意 partition，不能靠改 UID 或 dataset 名隐藏泄漏。

### 6.2 Canonical Q3 label ledger

Phase 1 label ledger 的每行严格包含：

```json
{
  "sample_id": "must match one manifest row",
  "uid": "must match the computed lineage uid",
  "col": 0,
  "gold_action": "map_to|hold|skip",
  "gold_target": "required only for map_to",
  "quality_grade": "Q3",
  "reviewers": [
    {"reviewer_id": "pseudonymous-a", "action": "map_to", "target": "Revenue"},
    {"reviewer_id": "pseudonymous-b", "action": "map_to", "target": "Revenue"}
  ],
  "adjudication": null
}
```

角色层只存在于 manifest，不在 label ledger 重复维护。分歧时 `adjudication` 必须含不同 adjudicator 的 action/target；一致时为 `null`。验收同时报告 action 原始一致率、action Cohen's kappa（类别失衡时附原始一致率）、`map_to` 条件下 target exact agreement、冲突率和裁决率。任何一项缺失都不能标 Q3。reviewer 不能从模型 confidence 或 gate 结果反推标签。

### 6.3 Learnability view（非权威派生视图）

仅 proposal/train 的已验收 Q3 ledger 可派生最小视图：复制 `sample_id/uid/gold_action/gold_target/quality_grade`，再从已绑定 source/schema/confidence 工件加入 `observed_header/canonical_fields/candidate_target/confidence/family`。Runner 必须逐条回查 ledger，拒绝标签不一致、Q1/Q2、gate/sealed/future 样本及 `gain/collateral/accepted/split/partition` 字段。

## 7. 模型与对比配置

不另开模型选型路线，沿用已冻结方向：

| 组 | 配置 | 作用 |
|---|---|---|
| 非学习基线 | always-skip、exact matcher、lexical/fuzzy、confidence-only | 回答是否根本不需要学生 |
| 简单学习基线 | 当前 CPU softmax classifier；后续可加冻结特征的 logistic regression | 回答便宜特征是否足够 |
| A0 | Qwen3-8B 同任务 zero-shot | 主学生训练前基线 |
| A1 | Qwen3-8B unfiltered SFT | 普通动作 SFT |
| A2 | 同底座、同预算的 checkpoint-filtered SFT | 评估过滤的增量价值 |
| A3 | A2 + DPO | 仅双向偏好门通过后运行 |
| smoke | Qwen3-4B LoRA/QLoRA 极少步 | 只验训练链，不作参数量消融 |
| teacher | 当前获批教师的精确 model/revision/template | 数据来源与质量上界；不可更换后仍称同实验 |

GB10 运行前必须冻结：权重来源与许可、revision/hash、tokenizer/chat template、context 长度、量化与精度、LoRA 参数、optimizer/learning rate/scheduler、effective batch、epoch/step、seed、early stopping、解码、最大输出、硬件和软件版本。A1/A2 同时报告 natural-volume 与 size/token/group-matched 两种口径；主臂至少 3 seeds，单 seed 只算 pilot。

## 8. 数据与模型判门顺序

1. `SOURCE_GO`：官方 URL、许可范围、版本、hash、容量和不含甲方数据确认。
2. `LABEL_GO`：Q3 双审/裁决、action 分布、target 合法性、冲突解释通过。
3. `SPLIT_GO`：group UID 零交叉，历史曝光清单完成，gate/sealed/future 角色固定。
4. `POWER_GO`：按 UID/家族估计有效样本量和最小可检测效应；不足即 `PILOT_ONLY`。
5. `BASELINE_GO`：简单基线仍有稳定残余，才申请 4B smoke/8B 训练。
6. `MODEL_GO`：权重许可、显存、环境、训练预算、输出目录和回滚方式确认。

任一门失败不通过复制样本、改 split、换阈值或查看 sealed test 来补救。

## 9. GB10 恢复后的执行清单

1. 只读盘点现有 TAT-QA/TAT-DQA/模型资产及 hash；TAT-DQA 只核状态，不运行 D4。
2. 用旧注入 map/checkpoint 反查已曝光 TAT-QA UID，形成 `historical_exposure_manifest`。
3. 分别做 FinQA（过程来源）与 Valentine NYC（动作来源）的 metadata-only preflight：核官方仓库 commit、数据许可适用范围、split/ground-truth 文件名、字节数/hash；未获批准不下载数据正文。
4. 对 FinQA/ConvFinQA 做 report/question UID 关系审计，对 Valentine 做 NYC 上游许可、LLM 扰动 provenance 与 gold 语义审计；不得用代码仓许可证替代数据许可。
5. 用户确认具体来源后，在 Git 外下载并生成 public-ID-only manifest；先跑许可/容量/hash 验收。
6. 抽取表头与 source pointers，按组先分层，再运行 split-preserving v1 合成；双跑 hash 一致。
7. 建立 Q3 标注包并完成双审/裁决；再由 Phase 1 合同判门。
8. Phase 1 接收后，Phase 1a 与 Phase 2 各自申请授权；Phase 2 不依赖 `LEARNABILITY_SIGNAL`。只有 Phase 1a 表明简单基线有残余、Phase 2 可复现且用户批准，才进入 4B smoke 与 8B A0–A2。

GB10 恢复后的第一步仍是 metadata-only 核验，不拉数据正文：

```bash
python3 -m json.tool docs/datasets/paper-public-source-registry-v1.json >/dev/null
jq -r '.sources[] | [.dataset_id, .official_repo, .checked_default_head] | @tsv' \
  docs/datasets/paper-public-source-registry-v1.json |
while IFS=$'\t' read -r dataset_id source_repo checked_head; do
  live_head=$(git ls-remote "${source_repo}.git" HEAD | awk '{print $1}')
  printf '%s\tchecked=%s\tlive=%s\n' "$dataset_id" "$checked_head" "$live_head"
done
```

任一 `live` 为空或与 `checked` 不同，只表示注册表需要人工重核，不能自动跟随最新版，更不能据此下载。只有用户批准具体 source/revision 后，才在 Git 外建立下载目录、记录条款快照/字节数/SHA-256，并把聚合收据交给 Phase 1 合同；原始文件不得加入 Git。

## 10. 当前不做的事

- 不把 TAT-QA 旧 train+dev 池洗成新 gate/test。
- 不下载 PubTables-1M；TAT-DQA 继续冻结，不重开 D4；不读取公开 test 来挑方案。
- 不把 repository license 自动当成所有原始报告的再分发许可。
- 不把程序知道变换真值等同于“真实世界黄金标签”。
- 不提交数据正文、权重、私有逐样本输出或带原始文本的人工标注。

## 11. 官方入口

- TAT-QA：<https://github.com/NExTplusplus/TAT-QA>；论文 arXiv:2105.07624。
- FinQA：<https://github.com/czyssrs/FinQA>；论文 arXiv:2109.00122。
- ConvFinQA：<https://github.com/czyssrs/ConvFinQA>；论文 arXiv:2210.03849。
- MultiHiertt：<https://github.com/psunlpgroup/MultiHiertt>；论文 arXiv:2206.01347；ACL Anthology `2022.acl-long.454`。
- HiTab：<https://github.com/microsoft/HiTab>；论文 arXiv:2108.06712。
- PubTables-1M：<https://github.com/microsoft/table-transformer>；论文 arXiv:2110.00061。
- Valentine：<https://github.com/delftdata/valentine>；论文 arXiv:2010.07386。
- GitTables：<https://github.com/madelonhulsebos/gittables>；论文 arXiv:2106.07258。
- Sherlock：<https://github.com/mitmedialab/sherlock-project>；论文 arXiv:1905.10688。
- HybridQA：<https://github.com/wenhuchen/HybridQA>；论文 arXiv:2004.07347。
- OTT-QA：<https://github.com/wenhuchen/OTT-QA>；论文 arXiv:2010.10439。
