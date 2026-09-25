# Loop A sandbox scoping 设计（D-D 授权：仅范围设计，2026-09-25）

> 状态: 设计件（Loop D）| 授权边界：仅范围设计；不启动生产端口、不重启服务；本件不派发任何会话
> CLI 事实（GB10 codex exec --help 实测）：--sandbox 取值 read-only / workspace-write /
> danger-full-access；另有 --dangerously-bypass-approvals-and-sandbox（历史 Loop A 派发曾用）。

## 1 卡类与沙箱矩阵

| 卡类 | 沙箱 | 写权限 | 台账/ledger 触碰 | 产出落地方式 |
|---|---|---|---|---|
| R 类（清点/审计/取证，只读分析） | read-only | 无 | 禁止 | 会话 stdout 返回报告文本，Loop D 落盘并 commit |
| W 类（必须写 owned paths 的实施卡） | workspace-write | 仅专属 worktree 内 | 禁止（ledger 一律 Loop D 落） | 卡内 commit 前 git status 必须仅含 owned paths |
| 任何类 | danger-full-access / bypass 旗标 | — | — | **禁用**；历史 bypass 派发不再复用 |

## 2 范围规则

1. R 类卡把 owned paths 收窄为「无」：卡面只声明可读范围与产出格式；memory/STATE.md、
   memory/THREADS.md、docs/INDEX.md 等治理件从 Loop A owned paths 移除，杜绝 ledger 并发写。
2. W 类卡必须在独立 worktree（gb10/<card>-<date> 分支）执行；production worktree 对 Loop A 只读。
3. 网络面不靠沙箱模式保证：沿用卡红线 + 运行期观测（observed ports 记录、必要时 strace 复核）；
   生产端口 :5050/:8004/:8006/:8007/:8008/:4096/:15432 一律禁止连接。
4. 模型路由：Loop A = deepseek-v4.1-flash（Token_Plan_Chat，已跑通）；Loop C = qwen3.8-max（D-E）。
5. 每卡派发前由 Loop D 记录：卡类、沙箱模式、worktree、owned paths、预算上限、监控 pid/log 路径；
   派发后核对 git status 与 observed ports，偏差即停报。
6. 失败语义：沙箱拒绝所需操作 = 卡范围设计缺陷，停报 Loop D 重新定类，不得现场提权。

## 3 与既有卡的对齐

- LC-GOV-002 已由 Loop D 以零模型 R 类方式完成（reports/LC-GOV-002.md），本设计将其模式固化。
- LC-PHASE1A / LC-PHASE2 / LC-DATA-SUPPLEMENT / LC-A2-EXPAND 解锁后按 W 类执行（独立 worktree），
  其数据门前置不变；本设计不改变任何门顺序或判据。
