# 本机、GB10 与主线治理

> 状态: 活跃 | 更新: 2026-10-21 | 取代/被取代: 当前工作区与 Git 治理收据；不取代科研原始回执
> 验收: `VERIFIED`。核验范围为工作区、Git、列明的离线测试与证据保护；最终三端提交见仓外 `final_ref_receipt.json`。

## 任务与边界

Owner 要求先分类、保全、合并和清场，再讨论后续科研与论文 Goal。本轮执行离线治理与 Git 同步，新增生成请求为零；未探测生产服务、数据库或模型端点，未重启服务，未安装新技能，未改写冻结科研结果或共享历史。GB10 一个既有技能的分发副本经备份后补齐五个缺项，详见下文。

当前入口为 [STATE](../../memory/STATE.md)、[THREADS](../../memory/THREADS.md)、[唯一科研导航](../research/README.md)与[代码资产地图](../architecture/codebase_map.md)。Paper E 唯一主稿为 [saner_rene_manuscript_v1.md](../../paper/saner_rene_manuscript_v1.md)。旧 THREADS 已原样归档，现役短表继续保留真实未决的运行、数据和外部投稿事项。

## 分支事实与合并依据

初始集成基线为 `dd275a64e806c67f1e5af14a76b10d0616ba2245`，分支 `research/portfolio-integration-v2`。先前“三端一致”指该分支，不代表 main 一致。

| 初始位置 | HEAD | 相对集成基线的独有 / 落后提交 | 裁决 |
|---|---|---:|---|
| 本机 main | `6fc48f35dc8c244a178933de6f3050a94d0dd3ce` | 0 / 17 | 保全脏工作区后向前合并 |
| GitHub main / GB10 main | `af89c30a8ec911402ddcba1299380c7820c325ef` | 0 / 12 | 同步合并后的主线 |
| 本机 test | `a92e170e7ced04be984e0f2360bca0f8ff49593d` | 0 / 471 | 无新提交，按工作区保全情况退役 |
| 本机临时验证现场 | `3003faad172233b7f3793602d3bc29350770c3e9` | 0 / 149 | 3,005 个删除状态是旧验证现场，不作为删除提交 |
| GB10 三个 accept 工作树 | 各自历史 HEAD，见机器清单 | 均为已包含的祖先 | VGMC 独有测试接回；忽略语料另行保全 |
| GB10 lc_research | `1f8070e21b79ac2d9cf6cdecec92f387f0ee584b` | 4 个独有提交 | 接收四份历史审计后归档 |
| GB10 loop_c | `815dda50efcbc9bff48348e14634c54002a96c70` | 5 个独有提交 | 接收报告纠错链；未完成控制器原型只作历史保全 |

没有发现分叉的现役科研执行结果；进一步核验旧工作树补出了两条 C 分支的九个历史独有提交，不能因首次只看现役 refs 就忽略。它们的有用内容经审查后合并，旧报告注明历史边界，存在确定状态迁移缺陷的 lead runner 不激活。两份 LC-GOV 原报告保持原路径，修复现役架构文档的缺链；旧 INDEX 的“活跃”原型链接不恢复为当前入口。

整合保留各历史父提交，GitHub main 使用非强制 push；不 rebase 公共分支，不伪造合并冲突。对旧 dirty main 先保存 staged/unstaged patch、index、working bytes、WIP Git 对象与 bundle，再经祖先校验同步索引及需更新文件；避免 hard reset、全量 clean 或丢弃本地独有内容。

最终当前提交由 `git rev-parse HEAD` 和仓外 `final_ref_receipt.json` 判定，本报告不嵌入包含自身的最终 commit hash。

最终本机与 GB10 各只保留一个 `main` 分支和一个主工作树，GitHub 只保留 `main`。共退役本机三个、GB10 五个旧工作树；本机两个、GB10 四个、GitHub 两个已合并分支引用已删除，历史对象另有 archive refs 和 bundle。GitHub 分支删除前重新读取 tip、核验祖先，并用显式 lease 原子删除；未强推 main。重复的本机 `origin-ssh` remote 已移除，保留 `origin` 与 `gb10`；GitHub fetch/push 统一使用可工作的 SSH。

## 文件分类与保全

| 位置 / 类别 | 初始数量 | 处理依据 |
|---|---:|---|
| 本机 tracked dirty entries | 92（24 staged，77 unstaged，存在重叠） | 69 个工作文件已与集成一致，20 个仅 EOL 不同，3 个现役入口是旧版本；全部先保全后对齐 |
| 本机 untracked 已集成内容 | 2,465 | 2,407 个字节一致、58 个仅 EOL 差异；归入可恢复副本后由规范树重建 |
| 本机同路径旧版本 | 3 | 旧成本表、探索日志和 Goal 回执，独立保留历史，不覆盖当前版本 |
| 本机 runtime | 3,575 | 独立虚拟环境整体迁出；不迁出产品 `venv` 或生产运行依赖 |
| 本机 score cache | 2，合计约 160 MB | 缓存单文件迁出，不搬走其旁边的结果 |
| 本机论文来源包 | 175，约 40 MB | 原包与解包内容保留在仓外；Git 保留来源、hash、许可证和报告 |
| 本机嵌套 FinRank | 独立 Git 仓库 | 独立 bundle 与工作内容核验后整体保全；不当作无意义目录删除 |
| 本机其余历史材料 | 旧实施单与 TeX `.blg` | 保留原路径与字节，不激活旧任务授权 |
| GB10 untracked | 2,351 | 1,594 个 exact、1 个 EOL、6 个旧版元数据、750 个独有执行中间件，分类保全 |
| GB10 独有执行中间件 | 750，1,037,213 bytes | 250 个 v2_oracle、500 个 v2_revalidation；保留可取回证据和哈希，不作为重复缓存丢弃 |
| GB10 持续写入报告 | 4 tracked | 保全并在原运行路径恢复为 ignored 文件；只取消 Git 跟踪 |
| GB10 VGMC 未提交改动 | 3 tracked + 1 helper | 接回主线，修复其对忽略语料的隐含依赖 |

GB10 六个异版文件均为旧描述、路径或成本元数据；指标不含独有增量。当前集成版本的更正优先，旧字节仍在备份。原 index 中两个未被任何现役 ref 引用的版本也已单独导出，不能仅凭工作树相同就丢弃 index。

四个取消跟踪的运行时文件是 `logs/graph/docs_lint_report.json`、`governance_drift_latest.md`、`loop_b_last_status`、`verify-report.json`。现有 ignore 已覆盖；代码按路径工作，不依赖 tracked 身份。各主机先保存各自副本再应用变更，保持运行路径；缺失时脚本采用 UNKNOWN/UNAVAILABLE 或重建。历史 `logs/graph/eval/`、`receipts/`、dispatch 日志与警告基线继续保留。

## 恢复位置与校验

本机保护根：`D:/AIRcommend/JinRongAgents/_protected_governance_20261021_v3`。
GB10 保护根：`/home/testuser/wzh/protected_governance_20261021_v3`。
更早的 `_protected_research_20261021_v1` 与远端 `protected_research_20261021_v1/external_sources/` 继续保留，绝非由新清场替代。

| 保护件 | 已核验内容 |
|---|---|
| 本机 `local_main_before` | 7,454 个归档 regular files 逐个重读 hash；含 1,140 个 ignored research 文件；patch、index、refs、bundle |
| 本机 `local_finrank_nested_before` | 独立来源 HEAD、bundle、唯一未跟踪 pyc 内容 |
| 本机 `index_blobs` | 24 个 staged blob 全部导出并校验；包含两个不可达的中间版本 |
| 本机 `local_temp_before` | 3,005 个缺失文件状态与 index；原 HEAD 可由 bundle 恢复 |
| GB10 `main_before` | 2,941 个 regular files 逐个 hash 核验；含 586 个 ignored research 文件；patch/index/bundle |
| GB10 `vgmc_before` | 四个原始未提交文件字节及工作状态 |
| GB10 `accept_ignored_data` | 旧 accept 工作树涉及的八个忽略语料文件，4,159,992 bytes；tar 重读 hash 核验，主工作树原件保留 |
| 两条 C 分支的原始材料 | 九个独有提交完成真实 merge；九个原始文件逐一与 Git blob 比较，报告及不激活的原型保留原字节 |
| GB10 `paper_deep_reading_before` | 补齐分发前的既有技能树，含文件 hash、mode 与空目录；没有丢弃本机定制内容 |
| GB10 `remaining_research_evidence` | 补充保护 13 个 `data/research` 文件与 34 个来源文件，共 47 个 / 33,398,389 bytes；包含三份旧重算收据，tar 重读 hash 核验，原件原地保留 |

恢复应在新目录读取 bundle 或 tar，先核验 manifest 再取所需文件；不要把旧 index 或全量补丁直接覆写当前 main。迁出 manifest 记录原路径与目标，具体未提交字节由 protected tar 和 WIP ref 保全。大备份不进 Git，且不读取或打包凭证文件；ignored runtime 本身不等于完整可复现的依赖环境。

机器摘要见 [audit/2026-10-21_workspace_git_closeout.json](audit/2026-10-21_workspace_git_closeout.json)。保护件是私人恢复资产，不自动构成论文公开 artifact。

干净指 Git 工作区与现役入口清晰，不表示删除所有 ignored 文件。本机产品环境、既有证据与来源 PDF 留在原位；研究树内 384 个非 pycache ignored 文件均在本机快照 manifest，size 一致。GB10 586 个原有研究证据/agent 状态也有快照。补充清单发现的 47 个旧科研/来源文件另做上述保护，仅排除一个本地 agent 节流状态。产品环境、其余 `.omc/`、运行日志和八月 demo 媒体原地保留，未冒称由本轮全量备份。runtime 可重建性不等于原始证据可替代性。

## 本轮实质修复

1. **记账完整性**：[账本核对](../../research/research_portfolio_v2/governance_20261021/LEDGER_RECONCILIATION.md)从 101 对原始请求/响应重算，补记 failed canary 的 84 和 failed scout 的 681 tokens。当前为 **101 attempts / 57,987 tokens**；原 events、冻结 runner、原结果和历史 747 / 313 账本保留。六个内存负例与三个隔离 CLI 负例均须失败。
2. **测试独立性**：VGMC 四个测试使用仓内 overlay 与合成语料，保留原语义断言，不依赖忽略的大表；特定端口前置阻断与全 socket 拒绝外层验证分别证明边界和零连接。
3. **技能检查准确性**：只读树比较仅允许双方为有效 UTF-8 且无 NUL 的普通文件有 CRLF/LF 差异。文本、空格、BOM、孤立 CR、二进制、symlink、缺项/多项仍失败。同步 staging 与激活仍是 byte-exact。本机原 33 项换行误报消除；GB10 检出的 `paper-deep-reading` 真实缺项经原树备份后，用既有 atomic `--sync-one` 补齐五个支持文件，随后 byte-exact diff 与 100 项 check 均通过。没有新装技能。
4. **跨平台字节合同**：当前冻结迁移实验包禁用 Git EOL 转换，避免 Windows checkout 改变 raw/hash；只给实际执行的 skill Bash 脚本固定 LF，不批量格式化 skills。
5. **架构与状态**：业务服务、业务 Agent、研发 Graph Loop、独立科研包及仓外存储分层说明；当前状态简短可读，历史原文仍可回溯。

## 验证与限制

| 核验 | 本机 | GB10 |
|---|---|---|
| 五组定点离线测试 | Python 3.11.9：43 passed / 3 skipped | Python 3.12.3：46 passed / 0 skipped |
| 连接边界 | 进程内 socket 尝试 0 | 进程内 socket 尝试 0 |
| docs lint | 0 fail / 0 warn | 0 fail / 0 warn |
| 已分发技能 check | 100 PASS | 100 PASS（一个真实缺项已修复） |
| 账本与冻结输入 | 101 对请求响应、57,987 tokens、216 hash；六个负例被拒绝 | 同项通过 |
| Git 工作区 / 活动分支 / 工作树 | clean / main / 1 | clean / main / 1 |

本机三项 skip 来自 Windows symlink 权限，GB10 已执行覆盖。测试各有一个已知 `asyncio_mode` 配置警告，原因是离线运行关闭插件自动加载；不表述为测试零警告。文档最终变更另行重跑 11 项文档治理测试。定点测试不是全仓测试；socket 拒绝仅证明这次被测 Python 进程没有连接尝试，不能证明所有子进程或生产环境隔离。

新增差异 secret scan 无未解释命中；公开来源目录名 `sk-415/harukabot` 的误报已按路径语境排除。原 THREADS 工作字节 hash、九个 C 分支原始文件及 216 个冻结输入均保持一致。冻结文档 33/34 未修改；本地缺少远端绝对路径的 schema 文件，不把跳过的本地检查包装成生产冻结验收。最后 refs、status 与检查收据保存在两端保护根。

技能元数据只读体检：现存 Python 3.12.11，115 scanned / 94 active，**0 errors / 141 既有 warnings**（74 completion-contract、67 frontmatter 排序）。skill-map 的 243 文件 / 119 名称 / 114 安装组是 source→harness 分发结构；58 unresolved-like tokens 含普通文本，不应当作 58 个确定缺失依赖。

## 为下一轮保留下来的科研资产

这些是后续讨论输入，不是新 Goal、运行预算或主张升级。

| 资产 | 可支持的问题 | 当前解释边界 |
|---|---|---|
| [NtripBrowser 真实行为探针](../../research/research_portfolio_v2/pymigbench_external_change_v1/ntripbrowser_qualification_v2/PROBE_REPORT.md) | 如何识别异常捕获/默认值掩盖未完成迁移 | 单案例可复现；不证明所有行为 oracle 都失败或 hybrid 普遍充分 |
| [PyMigBench 来源资格](../../research/research_portfolio_v2/EXTERNAL_CHANGE_SOURCE_INDEPENDENT_REVIEW.md)与环境材料 | 将任务意图、依赖版本、传递依赖与行为测量分开冻结 | 资格失败不是模型失败；code-only diff 不等于没有迁移意图 |
| CodeUpdateArena V2 的执行器修复与零新请求回放 | 怎样保证 nonce、Docker 与冻结候选代码的可比性 | V1 无效结果保留；修正后仍为有界负结果 |
| [Adaptive V3](../../research/adaptive_revalidation_v3/README.md)配对负结果 | 何时简单策略已足够，如何避免复杂方法的虚假收益 | authored fixtures，不外推真实世界最优策略 |
| [MA-CERD 更正](../../research/ma_cerd_independent_v1/CORRECTIONS_20261021.md) | 资源 membership、依赖传播、动作集合 exact match 与可接受性如何拆开 | 透明规则不是传播算法，selective escalation 未验证 |
| 本轮 765-token 结算遗漏与 replay guard | 失败输出如何保留可核验成本；如何区分传输成功与解析失败 | 只覆盖列明的 101 对保存记录，不构成独立网络全流量证明 |
| [C 层历史报告](../archive/2026-10-21_loop_c_reports/README.md)与[原型说明](../archive/2026-10-21_loop_c_lead_prototype/README.md) | 错误资产清单如何制造虚假审计发现，声明的 mode guard 如何与实现核对 | 历史纠错链；原型有确定状态迁移缺陷，未作为现役控制器启用 |

Paper E 保持两案例 `NARROW_AND_CONTINUE`；FinRank 当前面板、已停止的重复实验和数据/训练门禁继续有效。后续研究应由 owner 在治理核验后结合这些资产决定，不能由剩余预算自动触发。
