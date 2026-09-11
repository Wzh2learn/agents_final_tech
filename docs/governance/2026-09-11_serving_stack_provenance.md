# GB10 serving 栈取证件（台账视图）— 2026-09-11

> 状态: 活跃（**取证件**, 决策 23=A 插队优先执行; 性质 = 只读证据存档, 不是配置管理件） | 更新: 2026-09-11 | 取代/被取代: 无
> 性质: GB10（`promaxgb10-0b48`）全部 serving 端点与容器的**启动配置取证存档**——**台账视图 + 权威源声明**（承 `docs/INDEX.md` 治理规则 5 与 09-10 夜治理打包批准的标准姿势）。**权威源声明**: 本件**不是**任何服务的权威状态源, 只是**某一时刻的只读快照**; 运行时实况的权威源 = **GB10 上的 `/proc`、`ss`、`systemctl`、`docker` 本身**, 本件只做转录与指针。任何一项若与本件不一致, **以现场实测为准**, 本件按更正注记处置、不回改。未决项与后续处置的权威源 = `memory/THREADS.md`; Backlog 权威源 = `docs/29_graph_engineering_roadmap.md` A 表。
> **取值时间与保质期（承「仓外环境面结论有保质期」规约, 见 THREADS `#LEGACY-NOTIFY-206-UPSTREAM-15A` 规约强化第 3 条）**: 本件全部数值取值于 **2026-09-11 22:5x – 23:0x CST**（`date` 实测 **2026-09-11 23:01:35 CST**）。**pid / 文件 hash / mtime / Up 时长 / ELAPSED / 监听集 会随重启与自更新漂移**, 引用本件任何数值**必须带取值时间**; 跨窗口引用前须现场复核。宿主事实: `hostname` = `promaxgb10-0b48`, `uname -a` = `Linux promaxgb10-0b48 6.17.0-1018-nvidia #18-Ubuntu SMP PREEMPT_DYNAMIC Tue May 5 21:28:33 UTC 2026 aarch64`, 本次开机 `uptime -s` = **2026-07-05 21:05:23**。
> 边界（红线自查用）: 本件全部内容 = **纯只读取证**。**端口只列举不连接**（承 R1 卡 P5 姿势）——用 `ss -ltnp` 读监听表, **未对 `:8004`/`:8006`/`:8007`/`:8008`/`:5050` 发起任何 TCP 连接、无 canary、无 judge、无模型调用、未起任何 run、未装任何观察器**。**未进容器、未 `docker exec`、未 `stop`/`restart`/`rm` 任何容器、未 `kill` 任何进程、未 `tmux send-keys`、未改任何配置文件**。所用命令全部为读操作: `/proc/<pid>/{cmdline,cwd,exe,environ}`、`ps`、`ss -ltnp`、`systemctl list-units`/`list-unit-files`（只查询）、`docker ps`/`docker inspect`/`docker image inspect`（只读）、`crontab -l`、`tmux ls`、`stat`、`sha256sum`、`llama-server --version`（**该二进制以 `--version` 单独调用, 不绑定端口、不起服务**, 承决策 22 批同一姿势）。
> 依据: 决策 23=A（用户 2026-09-11 裁定）/ `docs/governance/2026-09-07_execution_plane_boundary.md` 硬规则 3「收据必须可复现」/ `docs/29_graph_engineering_roadmap.md` A7 行（决策 27=C 界定两个评估对象）

---

## 一、为什么要有这一件（决策 23=A 的理由, 逐字落账）

承载 **D1 / D2 / D3 / 阶段 B 全部论文数字**的主 judge 端点 `:8004`, 其进程 **PPID = 1** 且 **systemd 无对应服务单元** ⇒ **无任何守护者**: 挂了不会自动重启, GB10 重启后不会自起。而它的**完整启动命令行只活在进程内存里**（`/proc/2642808/cmdline`）——**进程一死, 证据即永久消失**, 事后无法从任何配置文件复原「当时到底是用哪个二进制、哪个权重、哪个上下文长度、哪个 flash-attn 档位跑出的那批数字」。

按 `docs/governance/2026-09-07_execution_plane_boundary.md` 硬规则 3「收据必须可复现」, **serving 配置属实验事实的一部分**, 与收据里的数字同级。故本件在进程仍存活时把配置**转录落盘并入库**, 使其从「只活在内存」升级为「持久化可复现」。这是**取证**, 不是加固——**加守护者（systemd unit / tmux 常驻 / 健康检查重启）是另一件事, 本批不做、不提案落地**（见 §八 复原手册与 §九 未处置项）。

---

## 二、`:8004` — 主 judge 端点（llama.cpp / LM Studio 后端栈）

### 2.1 进程身份（`ps` + `/proc` 只读）

| 项 | 值（取值时间 2026-09-11 23:0x CST） |
|---|---|
| pid | **2642808** |
| **PPID** | **1**（⇒ 无父进程守护; 该事实本身即本件的核心结论, 见 §2.5） |
| `lstart` | **三 7月 29 23:11:59 2026** |
| `ELAPSED` | **43-23:46:16**（43 天 23 小时; 同期 `ps` 另一次采样为 43-23:47:56, 差值即两次采样间隔） |
| RSS | 8 561 264 KB（约 8.16 GiB） |
| 线程数 | 24 |
| `cwd` | `/home/testuser` |
| `exe` 软链目标 | `/home/testuser/.lmstudio/extensions/backends/llama.cpp-linux-arm64-nvidia-cuda13-2.16.0/llama-server` |
| 监听 | `127.0.0.1:8004`, backlog **512**, `users:(("llama-server",pid=2642808,fd=32))` ⇒ **仅回环, 不对外** |

### 2.2 启动命令行全文（`/proc/2642808/cmdline`, 逐字, 未截断）

**原始文件字节数 = 381 B**（`wc -c < /proc/2642808/cmdline`, 含 argv 之间的 NUL 分隔符; 展开为可读文本后为 **377 字符 + 1 个尾随空格**）。以下为 `tr '\0' ' '` 展开后的**全文**:

```text
/home/testuser/.lmstudio/extensions/backends/llama.cpp-linux-arm64-nvidia-cuda13-2.16.0/llama-server -m /home/testuser/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-GGUF/Qwen3.6-35B-A3B-Q4_K_M.gguf --mmproj /home/testuser/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-GGUF/mmproj-Qwen3.6-35B-A3B-BF16.gguf --host 127.0.0.1 --port 8004 -c 65536 -ngl 999 --flash-attn on
```

**可复现性关键参数逐项**（论文数字复算时必须一致的六个量）: 权重 = `Qwen3.6-35B-A3B-Q4_K_M.gguf` / 多模态投影 = `--mmproj mmproj-Qwen3.6-35B-A3B-BF16.gguf` / 绑定 = `--host 127.0.0.1 --port 8004` / **上下文长度 `-c 65536`** / **全部层 offload `-ngl 999`** / **`--flash-attn on`**。

### 2.3 二进制与模型文件（路径 + 字节数 + mtime + sha256）

| 件 | 路径 | 字节数 | mtime | sha256 |
|---|---|---|---|---|
| 二进制 | `/home/testuser/.lmstudio/extensions/backends/llama.cpp-linux-arm64-nvidia-cuda13-2.16.0/llama-server` | 2 037 000 | 2026-05-25 15:17:19 +0800 | `037e02419e78256ed4227af31fc0b2602ff04c670fb7ad4fa2429fafb03bd55d` |
| 主权重 | `/home/testuser/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-GGUF/Qwen3.6-35B-A3B-Q4_K_M.gguf` | **21 166 757 728**（约 19.7 GiB） | 2026-05-26 15:09:51 +0800 | **未算**——理由 = 单文件 **>10 GB**, 按开工卡硬约束只记 size + mtime, **避免磁盘 IO 影响在跑服务**, 不为取证把盘打满 |
| 多模态投影 | `/home/testuser/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-GGUF/mmproj-Qwen3.6-35B-A3B-BF16.gguf` | 902 822 016（约 861 MiB） | 2026-05-26 14:51:03 +0800 | `e5c205cec2fd28f66c3895e4040021ab994b860323c3db8531640305ff49b322`（<10 GB, 故已算; 以 `nice -n 19 ionice -c3` **空闲 IO 优先级**执行, 降低对在跑服务的影响） |

模型目录 `ls -la` 全清单 = **恰好上述两件**（无其他 gguf / 无 split 分片）, 目录本身 mtime 2026-05-26 15:11。

### 2.4 二进制版本（`--version`, 单独调用, 不绑端口不起服务）

```text
version: 1 (5306f4b)
built with GNU 11.4.0 for Linux aarch64
```

⇒ 与 `docs/29` A7 行 09-11 只读刷新所记 **`version: 1 (5306f4b)`** 一致（本批复取一次核对, 逐字相符）。目录名内嵌的上游标称版本 = **`llama.cpp-linux-arm64-nvidia-cuda13-2.16.0`**（LM Studio 后端包命名, CUDA 13, arm64）。

### 2.5 环境变量（**已过滤后落盘**; 敏感项一律 `<redacted>`）

`/proc/2642808/environ` 共 **22 个变量**。**安全硬门执行情况**: 任何名字含 `KEY` / `TOKEN` / `SECRET` / `PASSWORD` / `PASSWD` / `CREDENTIAL` / `AUTH` 的变量, **值一律以 `<redacted>` 替换**, 且**原始值未打印到终端、未写进任何文件、未进 commit**（承红线「API key 与 HF token 绝不打印」）。过滤以**机械规则**执行（`cut -d= -f1 | grep -iE '<敏感词>'` 取名单, 反向 `grep -vE '^[^=]*(<敏感词>)='` 取安全集）, 非人工挑选。

**被 redacted 的变量名清单（只给名, 绝不给值）= 2 项**:

1. `OPENAI_API_KEY`
2. `QODER_PERSONAL_ACCESS_TOKEN`

**保留的非敏感变量（20 项, 逐字）**:

```text
SHELL=/bin/bash
GTK_IM_MODULE=fcitx
XMODIFIERS=@im=fcitx
PWD=/home/testuser
LOGNAME=testuser
XDG_SESSION_TYPE=tty
HOME=/home/testuser
LANG=zh_CN.utf8
SSH_CONNECTION=10.29.57.38 7207 10.129.237.26 22
SDL_IM_MODULE=fcitx
XDG_SESSION_CLASS=user
USER=testuser
SHLVL=0
QT_IM_MODULE=fcitx
XDG_SESSION_ID=8021
XDG_RUNTIME_DIR=/run/user/1001
SSH_CLIENT=10.29.57.38 7207 22
PATH=/home/testuser/.npm-global/bin:/usr/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1001/bus
_=/usr/bin/nohup
```

**⇒ PPID = 1 的成因已由 environ 机械坐实（本件最有价值的一条推断）**: `_=/usr/bin/nohup` + `XDG_SESSION_TYPE=tty` + `XDG_SESSION_ID=8021` + `XDG_SESSION_CLASS=user` + `SSH_CLIENT=10.29.57.38 7207 22` + `SHLVL=0` 共同表明: 该进程是**由一次交互式 SSH 会话（源 10.29.57.38）里经 `nohup` 手工启动**的; 会话结束后 `nohup` 使其忽略 SIGHUP 而存活, 但**父 shell 已退出 ⇒ 被 init（PID 1）收养**。故 `PPID=1` **不是** systemd 托管的表现, 而是**孤儿化**的表现——**二者在 `ps` 里同样是 PPID=1, 但含义相反**, 这是本件必须逐字记录 environ 的理由。

### 2.6 **守护者缺失的明示结论**（决策 23=A 要求写清）

五路独立取证, **全部指向「无守护者」**:

| 检查 | 命令（只读） | 实测结果 |
|---|---|---|
| 系统级 systemd 运行单元 | `systemctl list-units --all --no-legend \| grep -icE 'llama\|lmstudio\|vllm'` | **0** |
| 系统级 systemd 单元文件 | `systemctl list-unit-files --no-legend \| grep -icE 'llama\|lmstudio\|vllm'` | **0** |
| 用户级 systemd | `systemctl --user list-units --all --no-legend \| grep -iE 'llama\|lmstudio\|vllm'` | **空** |
| cron | `crontab -l` | **只有 1 行** = `30 3 * * * cd /home/testuser/wzh/projects/agents_final_tech && venv/bin/python scripts/graph/governance_drift_scan.py --cron >> logs/graph/governance_cron.log 2>&1`（**与 serving 无关**） |
| tmux 常驻会话 | `tmux ls` | 5 个会话 = `coding-jinrong`（Jul 19）/ `graph-loop-b`（Aug 13）/ `opencode-serve`（Aug 6）/ `thinking-proxy`（Aug 17）/ `vllserve`（Aug 17）——**无任何 llama / lmstudio / 8004 会话**; 且 09-10 夜派发的 `loop-a-a4a5` 与 `loop-a-r1` 两个会话**已不在列表**（两代理已交付退出, 与 09-11 批所记一致） |
| 是否有 LM Studio 父进程 | `ps -eo pid,ppid,etime,args \| grep -iE 'lmstudio\|lms \|supervisor'` | **只命中 llama-server 自身一行**, 无 LM Studio 主程序、无 supervisor |
| 是否 docker 管理 | `docker ps` | 三容器均与 `:8004` 无关（见 §三/§五） |

**⇒ 结论（明示）**: `:8004` **无自动重启、无开机自启、无版本锁定、无健康检查**。它是一次手工 `nohup` 的产物, 已如此运行 **43 天**。

### 2.7 风险（照实记, 不淡化）

一旦该进程消失（OOM / GB10 重启 / 误 kill / 二进制被 LM Studio 自更新替换）, 则:

1. **论文线全部需 `:8004` 的窗口停摆** = R3 的 **A13**（设计稿主案约 120-180 次调用, 已裁定顺序 A3 → A13 → A12）、任何将来的 D 类实验（含**若 D4 被重启**——其预算门分支 **B1 已裁定为「仅 `:8004`」**）、以及 **T7 数字合流若需重算**的任何一项。
2. **复原需人工按 §2.2 的命令行逐字重建**, 且**六个关键参数中任一项记错即产出不可比的数字**（尤其 `-c 65536` 与 `--flash-attn on`）。本件存在的唯一目的就是让这一步**有据可抄**而非凭记忆。
3. **静默替换风险**: 二进制住在 `~/.lmstudio/extensions/backends/` 下, 属 **LM Studio 自管目录**——LM Studio 若自行更新后端, 会**新增另一个版本目录**（与本机 `~/.codex/config.toml` 的 cua_node 运行时轮换同型, 见 THREADS `#LEGACY-NOTIFY-206-UPSTREAM-15A`: 五代轮换、间隔 33 天 → 9 天 → 3 天 → 21.7 小时）。**已在跑的进程不会受影响（inode 已持有）, 但一旦重启就会起在另一个版本上**, 而版本号只在目录名与 `--version` 里, **无任何锁定机制**。本件已把「目录名 + `version: 1 (5306f4b)` + 二进制 sha256」三个量一并记下, 使事后可判定「是否还是同一个二进制」。

---

## 三、`:8006` — vLLM 探针容器（A7-a 的评估对象）

| 项 | 值 |
|---|---|
| 容器名 | `vllm-probe` |
| 镜像 | `dockerproxy.net/timothystewart6/vllm-gb10:v0.27.1-gb10.1` |
| 镜像 ID | `sha256:734134467dc5b567845fdfc1cbe5b16e9761e3b6a059b35dc8de6d8147ac997f` |
| 镜像 created | **2026-08-15T05:19:06Z** |
| 镜像 repoDigests | **同一 digest 三镜像源**: `sha256:e33b263954ae32bf467a17756b6d70ec2ce879f1f950b01fc28169c30afe62c8`（`docker.1ms.run` / `dockerproxy.net` / `hub.rat.dev` 三个前缀, digest 相同 ⇒ **tag 可锚定到 digest, A7-a 评估有稳定标识**） |
| 容器 started | **2026-08-21T15:41:38.036347742Z** |
| Up 时长 | **Up 2 weeks**（`docker ps`; 启动它的 shell 进程 `ELAPSED` 为 20-23:16:37） |
| 端口映射 | `8000/tcp → 0.0.0.0:8006` 与 `[::]:8006` ⇒ **对外可达**（与 `:8004` 仅回环不同） |
| **重启策略** | **`policy=no`**, 且启动命令带 **`--rm`** ⇒ **容器一旦退出即被删除**, 连「停了但还在」的现场都不保留 |
| 健康态 | 无 healthcheck（`docker inspect` 取 `.State.Health` 报 `map has no entry for key "Health"`） |

**启动链（三层, 逐字转录自 `ps`）**:

1. 外层 shell（pid **668563**, PPID **1**, `lstart` 五 8月 21 23:41:37 2026）:

```text
bash -c cd ~/wzh/projects/agents_final_tech && CHAT_TEMPLATE=/home/testuser/wzh/vllm_cache/qwen38_think_off_default.jinja nohup bash scripts/vllm_probe_serve.sh > /tmp/vllm_rollback_0821night.log 2>&1 & sleep 5; docker ps --format "{{.Names}} {{.Status}}" | head -3; tail -2 /tmp/vllm_rollback_0821night.log
```

2. `docker run`（pid **668565**, PPID 668563）——**全文**:

```text
docker run --rm --name vllm-probe --device nvidia.com/gpu=all --ipc host -p 8006:8000 -v /home/testuser/wzh/models/hf/Qwen3.8-27B-FP8:/models/model:ro -v /home/testuser/wzh/vllm_cache:/root/.cache/vllm -v /home/testuser/wzh/vllm_cache/qwen38_think_off_default.jinja:/models/chat_template_custom.jinja:ro dockerproxy.net/timothystewart6/vllm-gb10:v0.27.1-gb10.1 vllm serve /models/model --served-model-name qwen38-27b-fp8 --gpu-memory-utilization 0.30 --max-num-seqs 32 --max-model-len 32768 --enable-prefix-caching --reasoning-parser qwen3 --enable-auto-tool-choice --tool-call-parser qwen3_xml --limit-mm-per-prompt {"image":2} --chat-template /models/chat_template_custom.jinja --trust-remote-code
```

3. 容器内进程（pid **668610**, PPID 668587）= `/usr/bin/python3 /usr/local/bin/vllm serve …`（参数同上）, 其下 **`VLLM::EngineCore`**（pid 669070, PPID 668610）。

**挂载与配置面（A7-a 评估的输入清单）**: 权重 = 宿主 `/home/testuser/wzh/models/hf/Qwen3.8-27B-FP8` → `/models/model`（**`:ro` 只读**）; vLLM 编译缓存 = `/home/testuser/wzh/vllm_cache` → `/root/.cache/vllm`; **自定义 chat template** = `qwen38_think_off_default.jinja`（既经 `CHAT_TEMPLATE` 环境变量传入 `scripts/vllm_probe_serve.sh`, 又以 `:ro` 挂为 `/models/chat_template_custom.jinja` 并由 `--chat-template` 显式指定）。关键推理参数 = `--served-model-name qwen38-27b-fp8` / `--gpu-memory-utilization 0.30` / `--max-num-seqs 32` / `--max-model-len 32768` / `--enable-prefix-caching` / `--reasoning-parser qwen3` / `--enable-auto-tool-choice` / `--tool-call-parser qwen3_xml` / `--limit-mm-per-prompt {"image":2}` / `--trust-remote-code`。

**⇒ A7-a 的「vLLM 版本」是镜像属性而非宿主包属性**（决策 22 批已实测: 宿主 `which vllm` 无、项目 venv `pip show vllm` 空）, 故升级动作面 = **换 tag / 换 digest**, 而非 `pip install -U`。本件已给出可锚定的 **digest `e33b2639…`**, 使「换到哪个版本」可被精确表述与事后核验。**与 A5 的联动照 `docs/29` A7 行所记只记指针不动它**（换 tag 是全局动作: 约 800 commit 跨度 + 等价性三连 + GB10 启动 SOP 重标定）。

---

## 四、`:8008` 与 `:5050` — 项目自有 Python 服务

### 4.1 `:8008` thinking 注入代理

| 项 | 值 |
|---|---|
| pid / PPID | **1510547** / **1510545** |
| 命令 | `venv/bin/python scripts/thinking_inject_proxy.py --port 8008` |
| `cwd` | `/home/testuser/wzh/projects/agents_final_tech`（**仓库内**） |
| `lstart` / ELAPSED | 一 8月 17 23:20:06 2026 / **24-23:40:21** |
| 监听 | `127.0.0.1:8008`, backlog 2048, `fd=6` ⇒ 仅回环 |
| 父进程 1510545 | `bash -c cd ~/wzh/projects/agents_final_tech && venv/bin/python scripts/thinking_inject_proxy.py --port 8008 > /tmp/thinkproxy.log 2>&1`（PPID **3459917**）; 日志 = `/tmp/thinkproxy.log` |
| 守护形态 | tmux 会话 **`thinking-proxy`**（created Mon Aug 17 23:20:06 2026, 与 `lstart` 同刻）⇒ **有 tmux 承载但无自动重启**; 且 **`/tmp` 日志属临时目录**, 承硬规则 3「临时目录镜像视同不可复现」 |
| 红线 | **永久零触碰**（阶段 B 与本批口径一致: `:8008` 零触碰） |

### 4.2 `:5050` 项目主应用（uvicorn）

| 项 | 值 |
|---|---|
| pid / PPID | **3153034** / **1**（同样孤儿化） |
| 命令 | `./venv/bin/python ./venv/bin/uvicorn main:app --host 0.0.0.0 --port 5050 --workers 2` |
| `exe` | `/usr/bin/python3.12` |
| `cwd` | `/home/testuser/wzh/projects/agents_final_tech` |
| `lstart` / ELAPSED | 一 8月 24 23:50:29 2026 / **17-23:09:58** |
| worker 子进程 | **3153038**（`pipe_handle=9`）与 **3153039**（`pipe_handle=13`）, 均 PPID 3153034, 由 `multiprocessing.spawn` 派生 |
| 监听 | `0.0.0.0:5050`, backlog 2048（三 pid 共享 `fd=3`）⇒ **对外可达**; 另 worker **3153039** 单独监听 `0.0.0.0:5001`（`fd=35`, backlog 100） |
| 守护形态 | **无 systemd、无对应 tmux 会话、PPID=1** ⇒ 与 `:8004` 同型无守护 |

---

## 五、`:8090` zhikuncode 与 pgvector_15432（另两个容器）

| 项 | `zhikuncode` | `pgvector_15432` |
|---|---|---|
| 镜像 | `zhikuncode:latest`（**本地构建, 无 repoDigest**） | `dockerproxy.net/pgvector/pgvector:pg15` |
| 镜像 ID | `sha256:66f863ad6ee7ae66c0eaafef3daf90e780289f01bf048abfcdc772f0b4da0020` | `sha256:83e2d1dbdb76788b4f6e51df9f9535bca45320679011966dcdefab072cd2ad9e` |
| 镜像 created | 2026-08-03T22:39:37.859034148+08:00 | 2026-07-08T23:09:56.837822678Z |
| 容器 started | 2026-08-03T14:39:40.004354601Z | 2026-08-23T12:26:06.996919145Z |
| Up / 健康态 | **Up 5 weeks (healthy)** | Up 2 weeks（无 healthcheck） |
| **重启策略** | **`unless-stopped`**（⇒ 宿主重启会自起; 三容器中唯一有守护语义的之一） | **`unless-stopped`** |
| 端口 | `8080/tcp → 0.0.0.0:8090` 与 `[::]:8090` | `5432/tcp → **127.0.0.1**:15432`（仅回环） |

**⇒ A10 的事实输入（只记事实, 不替用户决定 A10 做不做; 承决策门纪律）**: `zhikuncode` 容器**当前在跑**——`Up 5 weeks (healthy)`, `:8090->8080`, 重启策略 `unless-stopped`, 镜像为**本地构建的 `zhikuncode:latest`（无上游 digest 可锚定）**。A10 条目为「ZhikunCode 重建（pip 直连 pypi 慢 → aliyun 源/上游 PR）`, `docs/29` 记「低优先 / 无阻塞 / 顺手时做」, **仍未裁定**——本件只登记「在跑」这一事实, 供将来裁定时对称阅读。

---

## 六、`:8007` — **当前无监听**

**实测**: `ss -ltnp` 全表（§七 转录）**无 `:8007` 任何条目**; 定向复核 `ss -ltn | grep -c ":8007"` = **0**。**端口只列举不连接**, 未做任何探测。

**后果（照 `docs/29` A7 行 09-11 只读刷新的结论, 本批复核仍成立）**:

- **A5**（L3 DFlash2 `:8007` 探针）**当前无服务可用**——其前置除「等 timothystewart6 新 tag」外, 还需**先把 `:8007` 起起来**, 该动作属执行面且需窗。
- **A12**（`:8007` 一窗用毕即停）**同理**; 已裁定 R3 顺序为 **A3 → A13 → A12**, 其中 A12 排最后, 故「起 `:8007`」应写成 **A12 拟卡的显式前置**（承 09-11 批已入账的同一结论）, 不得默认服务在位。

---

## 七、监听表全转录（`ss -ltnp`, 只列举不连接; 取值时间同上）

本件相关的行（逐字, 其余系统端口一并转录以备漂移对照）:

```text
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      128        127.0.0.1:44575      0.0.0.0:*    users:(("code-6a44c352bd",pid=1977449,fd=12))
LISTEN 0      4096       127.0.0.54:53        0.0.0.0:*
LISTEN 0      4096       127.0.0.1:33331      0.0.0.0:*    users:(("clash-verge",pid=3409020,fd=29))
LISTEN 0      70         127.0.0.1:33060      0.0.0.0:*
LISTEN 0      511        127.0.0.1:60301      0.0.0.0:*    users:(("code",pid=3409002,fd=36))
LISTEN 0      4096       127.0.0.1:15432      0.0.0.0:*
LISTEN 0      4096       127.0.0.1:11000      0.0.0.0:*
LISTEN 0      4096       127.0.0.1:7897       0.0.0.0:*
LISTEN 0      2048       127.0.0.1:8008       0.0.0.0:*    users:(("python",pid=1510547,fd=6))
LISTEN 0      2048         0.0.0.0:5050       0.0.0.0:*    users:(("python",pid=3153039,fd=3),("python",pid=3153038,fd=3),("python",pid=3153034,fd=3))
LISTEN 0      512        127.0.0.1:8004       0.0.0.0:*    users:(("llama-server",pid=2642808,fd=32))
LISTEN 0      100          0.0.0.0:5001       0.0.0.0:*    users:(("python",pid=3153039,fd=35))
LISTEN 0      5          127.0.0.1:8100       0.0.0.0:*    users:(("python",pid=1679516,fd=3))
LISTEN 0      128          0.0.0.0:5938       0.0.0.0:*
LISTEN 0      128        127.0.0.1:5939       0.0.0.0:*
LISTEN 0      4096         0.0.0.0:8090       0.0.0.0:*
LISTEN 0      4096         0.0.0.0:8006       0.0.0.0:*
LISTEN 0      512        127.0.0.1:4096       0.0.0.0:*    users:(("opencode",pid=3153507,fd=17))
LISTEN 0      151        127.0.0.1:3306       0.0.0.0:*
LISTEN 0      4096         0.0.0.0:22         0.0.0.0:*
LISTEN 0      4096       127.0.0.1:631        0.0.0.0:*
LISTEN 0      4096   127.0.0.53%lo:53         0.0.0.0:*
LISTEN 0      511        127.0.0.1:19800      0.0.0.0:*    users:(("code",pid=3407303,fd=76))
LISTEN 0      511        127.0.0.1:18791      0.0.0.0:*    users:(("node-MainThread",pid=4054315,fd=27))
LISTEN 0      511        127.0.0.1:18789      0.0.0.0:*    users:(("node-MainThread",pid=4054315,fd=25))
LISTEN 0      4096           [::1]:631        [::]:*
LISTEN 0      128              [::]:5938      [::]:*
LISTEN 0      4096           [::]:8090        [::]:*
LISTEN 0      4096           [::]:8006        [::]:*
```

**⇒ 监听集（本件相关五端口）= `:5050`（对外）/ `:8004`（仅回环）/ `:8006`（对外）/ `:8008`（仅回环）/ `:8090`（对外）; `:8007` 缺席。** 与决策 22 批 A7 刷新所记「监听集 = 5050 / 8004 / 8006 / 8008」**一致**, 本批另计入容器暴露的 `:8090` 与 worker 的 `:5001`。

---

## 八、复原手册（**本批不执行**; 仅在 `:8004` 进程消失后由人工按此重建）

> 性质: 以下为**证据的可操作性附录**, 目的是让 §2.2 的命令行可被无歧义地重放。**本批未执行其中任何一步, 也不构成「应当执行」的裁定**——是否给 `:8004` 加守护（systemd unit / 常驻 tmux / 健康检查）属**另一件事**, 需用户裁定, 见 §九。

1. **先确认是否真的不在**: `ss -ltnp | grep ':8004'`（只列举）与 `pgrep -a llama-server`。**若仍在跑, 不做任何事**。
2. **确认二进制与权重仍是本件所记的那两个**: 比对 §2.3 的 sha256（二进制 `037e0241…`）与字节数（主权重 21 166 757 728 / mmproj 902 822 016, mmproj sha `e5c205ce…`）。**若二进制目录名已变（LM Studio 自更新）⇒ 停下报用户**, 因为此时重放出的**不再是产出论文数字的那个栈**, 任何新跑的数字与既有收据**不可比**, 须重新定标（承 A5 联动同一逻辑）。
3. **逐字重放 §2.2 的命令行**, 六个关键参数（权重 / `--mmproj` / `--host 127.0.0.1` / `--port 8004` / `-c 65536` / `-ngl 999` / `--flash-attn on`）**一项都不得改动或省略**。
4. **重放后必须实证**: 端口在监听表内 + `--version` 仍为 `version: 1 (5306f4b)` + 首次真实调用的响应可与既有收据对齐（该步属执行面, 须在 GB10 窗内做）。
5. **记账**: 把「进程曾消失 + 复原时间 + 复原后是否与原件同 hash」写进 `memory/THREADS.md`。**若曾消失过, 则跨越该时点的任何数字对比都必须显式披露**——这是本件存在的根本理由。

---

## 九、本件未处置的项（**只登记, 不提案落地、不排窗**）

| 项 | 事实 | 处置状态 |
|---|---|---|
| `:8004` 加守护 | 无 systemd / 无 cron / 无 tmux / PPID=1 / 43 天 | **本批不做、不提案落地**; 属执行面改动且需用户裁定, 登记进 `memory/THREADS.md` 待议 |
| `:8006` 的 `--rm` + `policy=no` | 容器退出即删除, 现场不保留 | **只记事实**; 改动属执行面, 未裁定 |
| `:8007` 无监听 | A5 / A12 需先起服务 | **只记事实**; 起服务属执行面且需窗, A12 拟卡须写成显式前置 |
| A7 评估窗 | 决策 27=C 已界定两个子对象 A7-a / A7-b | **本批只界定范围, 不排窗、不评估、不升级、不动任何服务**（见 `docs/29` A7 行） |
| `zhikuncode`（A10） | 容器在跑, `Up 5 weeks (healthy)` | **只记事实**; A10 做不做**仍未裁定**, 主线程不替用户决定 |

---

## 十、引用规约（承「仓外环境面结论有保质期」）

1. 引用本件任何数值**必须带取值时间**（本件 = **2026-09-11 23:0x CST**）。
2. **size 相等不构成「未改动」的证据, 必须以 sha256 + mtime 为准**（同规约第 3 条; 该条由 `config.toml` 五代 hash 轮换中「两代 hash 同为 16 字符故 size 不变而内容已变」实测得出）。
3. 本件是**快照**不是**权威源**: 与本件不一致时以现场实测为准, 本件按更正注记追加, **不回改原文**（承决策 4=A「只追加不回改」纪律）。
4. 涉及 `:8004` 的任何将来窗口（A13 / A12 / 若 D4 被重启 / T7 重算）在**拟卡阶段即应引用本件 §2.2 与 §2.3**, 把「栈同一性」写成派发前置检查的一项——**否则一旦栈被静默替换, 产出的数字与既有六份收据不可比, 而这一点在事后无法补救**。
