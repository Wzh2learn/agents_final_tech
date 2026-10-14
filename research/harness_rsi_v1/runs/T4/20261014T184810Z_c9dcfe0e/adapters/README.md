# T4 v2 只读适配器

所有适配器只路由既有离线入口；目标工具源码、判定语义和路由范围未修改。适配执行现场只写本 run 的 `scratch/tool_outputs/`，临时失配件只存在于命令执行期间。

| 适配器 | 目标工具 | 允许入口 | 副作用核实 | 级别与范围 | 未验证面 |
|---|---|---|---|---|---|
| `dispatch_precheck_adapter.sh` | `scripts/graph/dispatch_precheck.sh` | 原 CLI 参数原样传递 | 只读 watcher 字节与 JSON；调用 `bash -n`；不执行 watcher、不读取 cron、不写文件、不访问网络 | `COMPONENT_PASS`：仅限本 run fixture 的 watcher/tick 输入合同 | 不验证 cron、运行环境或真实派发 |
| `summary_guard_check_adapter.sh` | `scripts/graph/hooks/summary_recompute_guard.py` | `check`；禁用 `--staged` | 只读 Markdown 与工作树工件；不改 git index；不写文件 | `COMPONENT_PASS`：仅限声明摘要与指定工件的机械一致性 | 不判断科学有效性或线上可运行性 |
| `summary_guard_derive_check_adapter.sh` | `scripts/graph/hooks/summary_recompute_guard.py` 的既有 `check` | 从可提交基底 Markdown 在临时目录派生失配 Markdown，随后调用既有 `check`；预期 rc=1 | 派生脚本只读基底并写 `mktemp` 文件；`trap` 删除临时件；不改基底、git index 或仓库文件 | `COMPONENT_PASS`：仅证明守卫能抓住 claim 与存储工件失配 | 不判断失配来源、测量对象或科学有效性 |
| `frozen_hash_check_adapter.sh` | `scripts/graph/frozen_hashes.txt` 所定义的冻结清单核验形态 | `md5sum --check -- MANIFEST` | 只读 manifest 与目标字节；不写文件 | `COMPONENT_PASS`：仅限 MD5 manifest 对目标字节匹配 | 不区分双哈希域，不授权解冻 |
| `check_skill_sync_adapter.sh` | `scripts/graph/check_skill_sync.sh` | 原入口，无参数 | 只读 `skills/` 与分发清单；不安装或同步 skill | `COMPONENT_PASS`：仅限目录与分发清单集合一致性 | 不验证内容、安装状态或运行时装载 |

## v2 最小调整说明

summary 适配入口新增独立的 `summary_guard_derive_check_adapter.sh`，用于修复 v1 可提交性问题。它不替换、不包装也不放宽 `summary_recompute_guard.py`：派生 Markdown 在临时区形成，最终仍调用同一既有 `check` 入口；持久化基底件必须 rc=0，失配变体必须 rc=1。其余适配器的路由范围与 v1 相同。

## 排除入口

| 工具 | 排除理由 |
|---|---|
| `scripts/graph/loop_b_verify.sh` | 现役验证 daemon，会调用 pytest、API、模型、数据库并写 tracked report |
| `scripts/graph/governance_drift_scan.py` | 默认写报告/backlog；即使 `--cron` 也重写仓库日志，越出本 run |
| `scripts/graph/hooks/index-guard.precommit.sh` | 检查 staged index；T4 不得改变 index |
| `scripts/graph/hooks/large-file-guard.precommit.sh` | 检查 staged 文件；T4 不得改变 index |
| `scripts/graph/formal_experiment_preflight.py` | 需要正式 FinQA/formal manifest；不得把专用资格泛化 |
| `scripts/graph/generate_repository_receipt.py` | 写 receipt 与 sidecar，并绑定更广的生产测试/历史证据 |

所有上述能力均不替代 PREFLIGHT 的 `END_TO_END_PREFLIGHT_PASS`。
