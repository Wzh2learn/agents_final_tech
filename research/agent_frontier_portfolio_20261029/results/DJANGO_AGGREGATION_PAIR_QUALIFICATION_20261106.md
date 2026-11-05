# Django 聚合问题对：数据、时序与环境资格

> 2026-11-06 | `READY_FOR_BOUNDED_DEVELOPMENT_PG15_SQLITE`。隔离 PostgreSQL 15 与 SQLite 的原题和 base/gold 控制已执行；PostgreSQL 11 原版本未验证。D 已读取参考和测试补丁，后续 Agent 必须隔离；本轮无模型、训练或业务数据库访问。

## 关联与时间

固定数据为 SWE-ContextBench Lite，revision `12c65bd15e2559bc808065565e941ee7bbbd008f`；数据清单 SHA-256 `bfa76e90221cc82e2c33d24588ff3060756c57679d687f68b29e9e662d68b10c`，三个 parquet 文件均与清单哈希一致。`SWEContextBench_Relationship.parquet` 中恰有一条指定关联：

| 角色 | instance ID | 基线 commit | 原始关联 |
| --- | --- | --- | --- |
| 来源 | `django__django-12589` | `895f28f9cbed817c00ab68770433170d83132d90` | [PR 12589](https://github.com/django/django/pull/12589)、[ticket 31377](https://code.djangoproject.com/ticket/31377) |
| 目标 | `django__django-34176` | `016bead6a23989adec5c7ee6948db7ce2fc5e89b` | [PR 16321](https://github.com/django/django/pull/16321)、[ticket 34176](https://code.djangoproject.com/ticket/34176) |

来源 PR 的 GitHub 元数据给出合并时间 `2020-03-25T08:49:43Z` 和合并 commit `10866a10fe9f0ad3ffdf6f93823aaf4716e6f27c`。[GitHub compare](https://github.com/django/django/compare/10866a10fe9f0ad3ffdf6f93823aaf4716e6f27c...016bead6a23989adec5c7ee6948db7ce2fc5e89b) 的 API 返回 `ahead=3282, behind=0`，支持该合并 commit 是目标基线祖先。非仅据创建日期判断；相关字段记录在 GB10 私有目录的 `public_metadata_receipt.json`。私有浅克隆仅保存三个 commit 对象，不具完整父链，**不能用于本地 `merge-base` 独立证明祖先关系**；`git_object_receipt.json` 留存获取结果。

来源题面已公开给出多表、`OuterRef`、子查询和聚合产生的模糊 `status`，并列举两个 Django 版本的 SQL 差异和 PostgreSQL 11；这些都是任务本有信息，不应包装成 Agent 从经验中额外发现的内容。目标题面自带 `Book`/`Publisher`/`Author` 关联示例、SQLite 与 PostgreSQL 错误、前序 ticket `#34123` 和 bisect commit `b7b28c7c189615543218e81319473888bc46d831`；后续各目标臂应等量保留这些自然提示。源题面称 Django 3.0.4，冻结源码版本为 3.1 alpha；目标冻结源码为 4.2 alpha。下述零模型环境已验证，后续 actor 的实际运行合同仍需单独验证。

## 暴露与经验边界

本地仓库 `research/`、`docs/`、`memory/` 对两个 instance ID、PR URL 和两个完整基线 commit 的精确检索无命中；GB10 `agent_learning_20261030` 下按 `raw.jsonl`、`metadata.json`、`target_input_freeze.json`、`*.started.json`、`*.completed.json`、`*.receipt.json`、`*.harness.py` 清点 354 个文件、未跳过大文件，检索 ID、PR/issue URL、两个基线和源合并 commit 均无命中。这个范围不覆盖所有历史目录、别名、缩写或预训练，**不能称未曝光或预训练隔离**。

公开基准的来源轨迹 `cases/SWEContextBench Lite Past Experience/7c3b3d04.jsonl` 存在时间泄漏：第 108 行是 `git log --oneline --all --grep="group.by" -i | head -20` 的工具结果，出现未来目标标识 `#34176`。该轨迹不得直接用作目标的隔离来源经验；如继续，应在冻结来源基线中生成自己的真实来源轨迹，移除 `.git` 并避免可访问目标参考、隐藏测试及完整历史。源轨迹文件 SHA-256 `89811925835380d922c0106f836439e7cb0064fc988d3086f91e2fba0c22ae2e`。这是明确字面泄漏，而并非对全部潜在语义泄漏的穷尽审计。

## 原题与冻结测试：零模型控制

GB10 为 ARM64。源码分别来自两个冻结 commit 的官方 codeload 归档，均在独立副本上先应用基准测试补丁，仅 gold 臂再应用参考补丁。D 已见参考，后续 actor 不得挂载参考、测试补丁或 `.git`；本对目前尚未执行 actor。原题探针是依据问题文本重建的小型数据模型和数据，运行于单独的评测容器，不代表真实用户生产环境。

| 对象和环境 | 冻结 base | gold 修复 | 回归范围 |
| --- | --- | --- | --- |
| 来源原题：私有 PostgreSQL 15.17 | `ProgrammingError: column reference "status" is ambiguous` | 返回 `status=7, total_count=1` | 原题探针；未跑 PostgreSQL 全量回归 |
| 来源冻结问题测试：SQLite | `0/1`，字段 `rating` 歧义 | `1/1` | 两臂各 `65/65` 可映射条目通过；另 1 条原始回归记录为说明文字，未映射 |
| 目标原题：SQLite | `OperationalError: ambiguous column name: name` | 返回 ISBN、出版社、联系人和作者数的预期结果 | 原题探针 |
| 目标冻结问题测试：SQLite | `0/6`，其中 5 errors、1 failure | `6/6` | 两臂各 `166/166` 通过 |

来源 PostgreSQL 探针沿用题面 A/B/AB/C、`OuterRef`、`Subquery`、`Q` 和 `Count` 结构，显式检查结果值；目标 SQLite 探针包含题面的出版者、联系人与作者数量。探针退出码为 0 仅表示探针脚本完成，base 的异常和 gold 的结果应读日志中的结构化字段，不能据脚本退出码判断问题是否修复。

来源 66 条 `PASS_TO_PASS` 原始记录中，唯一未映射的是 `Subquery annotations are excluded from the GROUP BY if they are`：它是说明文字而不是完整可执行测试标识，其余 65 条均已映射并执行。归档各省略 4 条文档主题符号链接，路径记录在 SQLite receipt；不据此声称全部源码逐字节物化。

官方 Docker Hub `postgres:11` manifest 请求超时；**可用性和 ARM64 digest 未确认，不能声称无 ARM 镜像**。本轮用已存在的 ARM64 `postgres:15-alpine` 镜像 `sha256:98e8adef37c633b03ac294e9fa80b939a7be708f4a29323571254d869a959008`，属于跨版本适配而非 PostgreSQL 11 原环境复现。镜像元数据 `PG_VERSION=15.17` 保存在 `pg15_image_metadata.json`；未执行服务端 `SELECT version()`，不能把镜像元数据写成 SQL 实测。来源 base/gold 的实际 SQL 和结果分别在 `pg15_source_base.log` 和 `pg15_source_gold.log`，哈希绑定见下。Python 3.8 来源评测使用从 PyPI 获取的 `psycopg2-binary==2.9.9` ARM64 wheel，SHA-256 `34eccd14566f8fe14b2b95bb13b11572f7c7d5c36da61caf414d23b91fcc5d94`；目标使用 Python 3.10/SQLite。回归均在 SQLite 下完成，不能宣称 PostgreSQL 回归已通过。

PostgreSQL 容器与 internal network 均使用 `research-django-aggregation-20261106` 前缀，未映射宿主端口、未使用现有卷；临时密码只存在于新建私有目录，试验后已删除。容器与网络删除均返回 0；未连接、停止或修改既有 pgvector 等服务。来源源码 3.1 alpha 与题述 3.0.4、目标源码 4.2 alpha 的版本差异仍需在任何实验结果中如实披露。

下一步可进入**有界开发资格**：冻结新 actor 依赖投影与每个实际执行环境，先以原题和上述测试复核无历史执行，再构建来源经验。若来源 actor 需要 PostgreSQL，下一次应新建带任务前缀的私有 internal network 和临时 PostgreSQL 服务、独立数据库及随机临时凭据，**不发布宿主端口、不使用既有服务或卷**；actor 与数据库经该私有网络连接，模型代理沿用隔离的现有通道，结束后只清理本次拥有的资源。网络隔离与连接实际行为需在新 actor 启动前验证；本次服务已清理，不能假定仍在运行。不得挂载完整已修复 Django 安装目录、隐藏测试、参考补丁或 `.git`。来源那条非测试文字保持未映射，不冒充 `66/66`；不要把 SQLite 的 65 项回归外推到 PostgreSQL。

## 许可与保存

固定数据清单记录数据集卡声明 MIT；数据集分发及各任务/问题文本的实际复用范围仍需按来源核验。[Django 官方仓库](https://github.com/django/django)的 GitHub license API 标识 `BSD-3-Clause`，两个冻结 commit 的 `LICENSE` 文件均存在；第三方依赖与独立发布的基准轨迹许可仍待核验，不能据数据集卡推定全部素材可再分发。

私有证据目录：`/home/testuser/wzh/research_evidence/agent_learning_20261030/django_aggregation_qualification_20261106/`。`sqlite_receipt.json` SHA-256 `46f67e61c87e2e3d118189fbce9ce45a9cbf105eb8440ff2eee6d43d67dd16cc`；`pg15_issue_receipt.json` SHA-256 `da0b11ed21fece2b388aa0c357a577b38e298d442348b8b3314442cee4cd7bf9`。私有目录保留独立探针、目标原题 receipt、节点映射、测试日志和参考补丁；这些只供评测端与审计人员使用。该对为已曝光给研究者的开发候选，不代表方法效果或独立确认。

负责人另行核对两份receipt、8份SQLite测试日志及2份PG原题日志的hash与结果；一处报告SHA误抄在提交前修正，原receipt未修改。35项审阅工件已双机归位：本机`D:/Documents/Loop_D_assets/agent_learning_20261106/django_aggregation_qualification_20261106.tar.gz`，GB10私有`evidence_packets_20261106/django_aggregation_qualification/`；20,768bytes，SHA `1810ea00db639444d2ce033b196bcafaba1cd206972c359c4944756c522457a1`。包不含源码树、wheel、运行环境、Git对象或密码，不入Git，也不挂载给后续actor。

| 私有工件 | SHA-256 |
| --- | --- |
| `source.tar.gz` | `4f797ff5816928ba3437f213c48dee36b4d1620d07826a9c411c2664d9a00812` |
| `target.tar.gz` | `e1b3703c2e3543d595bac9d124bbda6c29101628ac7ac7a2bdac514f13887582` |
| `qualify_sqlite.py` | `060c7111128d667686a0383bc3d43a504d3ce6f3df9563edad05ab333db7d390` |
| `qualify_pg15_issue.py` | `7e8c810a1f06f2fda047f6ae63f6a357733291a76926d1bd570ae277c798a161` |
| `issue_probe/source_issue_probe.py` | `bad04113610b05e9946274a967aeb2b6fb7487ac45dfd96e7683c8d3284d209d` |
| `issue_probe/target_issue_probe.py` | `01725a6a639f6e818aac7aca7fc33ef51ac250013a96df674a09f5b72b7984ea` |
| `sqlite_target_issue_receipt.json` | `db6240023d54db0e86742b449dfd39fbce30fe0a3d47f552219c2a1a3883b266` |
| `pg15_source_base.log` | `c42fb5339712d5c3762854ba60285c74a01dcb373673b3ff1d6d03a67cd8059d` |
| `pg15_source_gold.log` | `537aca32f3b454bc3da4db6540d0362e525969e471f2d1f3ae5d9df767be0c8f` |
