# GB10 实验安全与资源门（开工前必过）

> 状态: 活跃 | 更新: 2026-09-24 | 取代/被取代: 不取代任何受保护路线文档
> 依据: 用户 2026-09-24 裁定 6 与补充自检 4（磁盘/内存/GPU/并发/artifact 体量/调用预算/进程回收/失败停止条件必须先定义；接近 OOM 或磁盘爆满即停，不得硬跑）
> 适用范围: GB10 上任何 Phase 1a / Phase 2 / smoke / 训练 / 模型端点调用。本机不做权威验收。
> 本件只定义门，不授权任何阶段；授权仍逐项由用户给出。

## 1 实测基线（2026-09-24 01:2x–02:0x CST，只读采集）

| 项 | 实测值 | 采集方式 |
|---|---|---|
| 磁盘 `/` | 3.6T 总 / 814G 已用 / 2.7T 可用 / 24% 已用 | `df -h /` |
| inode | 2% 已用 | `df -i /` |
| 内存 | total 124546 MB / used 93407 / free 19467 / available 31138 / buff-cache 13684 | `free -m` |
| swap | 16383 MB 总 / 8277 已用（50.5%） | `free -m` |
| GPU | NVIDIA GB10，utilization 0%，**FB Memory 全部 N/A** | `nvidia-smi -q` |
| 负载 | 0.41 / 0.36 / 0.43，20 核 | `/proc/loadavg`、`nproc` |
| 常驻大户 RSS | llama-server 8.6G、uvicorn worker 2.8G×2、python 2.6G、vLLM EngineCore 2.0G、vllm 0.8G、opencode 0.7G | `ps --sort=-rss` |
| 僵尸进程 | 1（`sd_espeak-ng-mb`，约 71 天，不占内存只占 PID） | `ps -eo stat` |

## 2 门槛与判定口径

| 指标 | 测量命令 | 开工门 | 停止门 | 本次实测 | 判定 |
|---|---|---|---|---|---|
| 磁盘可用 | `df -h /` | 可用 ≥20% 且 ≥50GB | <15% 或 <30GB | 76%、2.7TB | PASS |
| inode | `df -i /` | 已用 <80% | 已用 ≥90% | 2% | PASS |
| 内存 | `free -m` 的 **available** | available ≥20GB 或 ≥20% | used >85% 或 available <10GB | available 30.4GB（24.4%）、used 75.0% | PASS（见 §3.1） |
| GPU | 见 §3.2 | 重任务前 utilization <80% | >90% 立即停 | 0% | PASS（口径待确认） |
| 负载 | `/proc/loadavg` ÷ `nproc` | 1 分钟负载 <70% 核数 | >90% 核数 | 2.1% | PASS |
| 重任务并发 | 人工确认 | **同时只允许 1 个** | 发现第 2 个即停 | 0 | PASS |

## 3 两处不可直接测量项（必须先确认口径，不得当作已 PASS）

### 3.1 内存：`free` 与 `available` 给出相反结论

用户阈值写的是「free ≥20GB 或 20%」。实测 **严格 `free` = 19.0GB（15.6%），不达该字面门**；
而 **`available` = 30.4GB（24.4%），达标**；`used` = 75.0%，低于 85% 停止门。
本件采 **`available`** 作为生效指标，理由：它计入可回收的 page cache，是内核真正能交给新进程的量；
在常驻模型占满缓存的机器上，严格 `free` 会长期偏低从而永久锁死开工门。
**该口径选择需用户确认**；若用户坚持以严格 `free` 为准，则当前为不达标，任何重任务都不得开。

### 3.2 GPU：GB10 显存不可单独测量

`nvidia-smi -q` 的 FB Memory Usage 四项（Total/Reserved/Used/Free）与 BAR1 全为 **N/A**，
`Addressing Mode = ATS`。GB10 是 Grace-Blackwell 统一内存，GPU 与 CPU 共用同一 124.5GB 池，
不存在独立 VRAM 数字。因此「VRAM <80% 才开重任务、>90% 停止」**在本机无法按字面执行**。
替代口径（建议）：把 §2 的内存门当作唯一内存预算，GPU 侧只保留
`utilization.gpu` 的 <80% / >90% 两档；训练或大模型加载前额外要求 available ≥ 模型权重常驻量的 1.5 倍。
**该替代口径需用户确认**，确认前不得以「VRAM 检查通过」为由开重任务。

## 4 并发、体量与预算

1. **同一时间只跑一个重任务**。重任务 = 任何训练 / 模型加载 / Phase 2 正式 replay / 全量 pytest 之外的批量作业。Phase 2 replay 与训练**永不并行**。
2. **输出目录上限**：单次运行产物 ≤5GB、日志 ≤500MB；超限即停并清理，不追加。
3. **输出位置**：一律写隔离 worktree 内的独立输出目录或 `/tmp` 下带 run-id 的目录；**绝不写 production 工作区**，尤其 `logs/graph/dispatch_log.md`、`logs/graph/verify-report.json`、`config/schema_suggestions.json`。
4. **调用预算**：任何模型端点调用必须带窗口内硬计数上限、canary 首调、异常即停并记账。`:8006` 仍受 2026-08-31 五条件裁定约束（仅预注册窗口卡内、白天错峰、硬预算门、canary 异常即停、窗口外零触碰）。
5. **先 pilot 后放量**：任何新链路先用最小样本跑通并核产物，再扩大规模。
6. **每次运行必带** `timeout`、预算上限、停止条件、失败回收方案（产物路径 + 如何删除 + 如何确认进程已退出）。

## 5 进程回收与失败停止

1. 启动前记录基线进程集；结束后对比，**新增进程必须全部退出**，残留即人工回收并记账。
2. 僵尸进程只占 PID 不占内存，记录但不阻塞；其父进程若为常驻服务则不动。
3. **立即停止条件**（命中任一即停，不硬跑、不重试）：available <10GB；`used` >85%；磁盘可用 <15% 或 <30GB；GPU utilization >90%；负载 >90% 核数；出现第 2 个重任务；OOM killer 触发（`dmesg` 出现 oom）；产物或日志超上限。
4. 停止后必须记：触发指标、实测值、已产出的部分结果路径、是否已回收进程。

## 6 隔离纪律

1. 实验在**隔离 worktree**（`git worktree add --detach <path> <sha>`）内执行，production 工作区不被 checkout、不被 pull。
2. worktree 缺 gitignored 的 `data/`、`venv/` 时：`data/` 用 **复制**（`cp -a`）并逐文件核 sha256 与 production 一致，**不用软链**以免回写；`venv/` 用 production 解释器的**绝对路径**调用，不在 worktree 内新建。
3. production 脏件与来料路径**有交集时不 pull production**。2026-09-24 实测案例：`logs/graph/dispatch_log.md` 在 production 有 36 行未提交的 Loop B FLIP 追加记录，而它同时在来料 25 路径内 ⇒ 直接 pull 会被 git 拒绝或覆盖运行证据。

## 7 本件不授权的事

不授权 Phase 1a 解除 `DATA_NO_GO`、不授权 Phase 2 正式执行、不授权 4B/8B 训练、不授权任何模型端点调用窗口、不改变任何冻结判据或冻结 hash、不解除专利公开边界。
