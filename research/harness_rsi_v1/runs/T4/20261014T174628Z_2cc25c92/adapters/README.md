# T4 只读适配器

所有适配器只路由已有离线入口；工具源码、作用域和判定语义均未修改。适配执行现场与结构化结果只写入本 run 的 `scratch/`。

| 适配器 | 目标工具 | 允许入口 | 副作用核实 | 级别与范围 | 未验证面 |
|---|---|---|---|---|---|
| `dispatch_precheck_adapter.sh` | `scripts/graph/dispatch_precheck.sh` | 原 CLI 参数原样传递 | 只读 watcher 字节与 JSON；调用 `bash -n`；不执行 watcher、不读取 cron、不写文件、不访问网络 | `COMPONENT_PASS`：仅限本 run fixture 的 watcher/tick/cron 输入合同；不是科学预检 | 不验证 cron 调度、运行环境或真实派发 |
| `summary_guard_check_adapter.sh` | `scripts/graph/hooks/summary_recompute_guard.py` | 仅 `check`；禁用 `--staged` | 只读 Markdown 与工作树工件；不改 git index；不写文件 | `COMPONENT_PASS`：仅限声明摘要与指定 JSON 工件的机械一致性 | 不判断测量对象是否科学有效、事件是否完整或线上可运行 |
| `frozen_hash_check_adapter.sh` | `scripts/graph/frozen_hashes.txt` 所定义的冻结清单核验形态 | `md5sum --check -- MANIFEST` | 只读 manifest 与目标字节；不写文件 | `COMPONENT_PASS`：仅限 MD5 manifest 对目标字节的匹配；T4 fixture 不改变仓库冻结清单 | 不区分原始/归一哈希域，不验证任意历史 manifest，不授权解冻 |
| `check_skill_sync_adapter.sh` | `scripts/graph/check_skill_sync.sh` | 原入口，无参数 | 只读 `skills/` 与 `sync_skills.sh`；不安装或同步 skill | `COMPONENT_PASS`：仅限仓库 skill 目录与分发清单的集合一致性 | 不验证 skill 内容、分发端安装状态或运行时装载 |

## 排除入口

| 工具 | 排除理由 |
|---|---|
| `scripts/graph/loop_b_verify.sh` | 硬禁止：现役验证 daemon，且会调用 pytest、生产 API、模型服务、数据库并写 tracked report |
| `scripts/graph/governance_drift_scan.py` | 默认模式登记 backlog；即使 `--cron` 不登记，仍重写 `logs/graph/governance_drift_latest.md`，越出 run |
| `scripts/graph/hooks/index-guard.precommit.sh` | 只检查 git index 的新增脚本；T4 不得 `git add` 或改变 index |
| `scripts/graph/hooks/large-file-guard.precommit.sh` | 只检查 staged 文件；T4 不得改变 index |
| `scripts/graph/formal_experiment_preflight.py` | 只读 stdout，但需要正式 FinQA/formal manifest；本 run 没有获准 manifest，且不得把 FinQA 专用资格泛化为通用资格 |
| `scripts/graph/generate_repository_receipt.py` | 写 receipt 与 `.sha256`，并绑定生产仓库测试、提交与历史无效运行证据；当前输入不在 T4 最小复盘范围 |

`formal_experiment_preflight.py`、`frozen_hashes.txt`、summary guard 与 dispatch precheck 的能力边界均不替代 PREFLIGHT 的 `END_TO_END_PREFLIGHT_PASS`。
