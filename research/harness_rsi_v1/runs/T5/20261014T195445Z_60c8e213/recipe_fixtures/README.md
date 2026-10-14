# T5 调用方边界探针来源与使用

本目录只服务于两个真实调用方契约：Loop D 对一个 run 包发起 `T5-R-RUNTIME-PREFLIGHT-V1`，以及交付方对一个 receipt/manifest 证据包发起 `T5-R-EVIDENCE-DELIVERY-V1`。契约来源不是实现者想象：前者取自 T4 `baseline_recipe.json` 的真实 adapter argv、T3 runner 的有界 CLI/fail-closed 纪律；后者取自 T2 evaluator 的输入字段、路径 allowlist、哈希绑定与 fail-closed 规则。`probe_definitions.json` 记录这些来源及 blob id。

探针由独立调用方 `caller_validator.py` 在 `run_probes.py` 中逐例执行。合法调用才会按注册表执行只读操作；未登记操作、shell 注入、任意路径、类型/范围错误、漏字段、错哈希、单字段总体 PASS 和伪造摘要都在目标执行前被调用方拒绝。

坏摘要对照只在进程内派生：`probe_definitions.json` 的 mutation 会改变内存中的 `summary_text`，随后比较其 SHA-256。仓库内不落盘任何失配 `.md`。另一个负向守卫对照调用 T4 的既有派生适配器，在临时目录生成失配 Markdown、由原守卫返回 rc=1，并立即删除；适配器包装退出码与目标守卫退出码分别记录，避免复用 T4R-01 A2 的同名字段歧义。

所有路径参数均为封闭枚举；调用方只解析当前 run root 下的相对路径，拒绝绝对路径、`..`、symlink 逃逸、未登记值和类型漂移。任何操作都没有 shell 字符串、自由文本命令、解释器参数、环境变量或任意 argv 入口。
