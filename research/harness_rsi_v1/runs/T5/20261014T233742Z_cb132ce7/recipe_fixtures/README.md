# T5 调用方边界夹具与无前置重放

本目录只服务于两个真实调用方契约：Loop D 对一个 run 包发起 `T5-R-RUNTIME-PREFLIGHT-V1`，以及交付方对一个 receipt/manifest 证据包发起 `T5-R-EVIDENCE-DELIVERY-V1`。契约来源取自 T4 `baseline_recipe.json` 的真实 adapter argv、T3 runner 的有界 CLI/fail-closed 纪律、T2 evaluator 的字段/路径/哈希规则；`probe_definitions.json` 保存来源与 blob id。

## 无前置重放入口

前置条件：**无**。交付树只读；不得先运行任何 prepare 脚本，不得改写、补时间戳、恢复 mode 或生成 run 内文件。唯一入口从仓库根执行：

```bash
python3 research/harness_rsi_v1/runs/T5/20261014T233742Z_cb132ce7/scratch/verify_replay.py \
  --run-root /home/testuser/wzh/projects/agents_final_tech/research/harness_rsi_v1/runs/T5/20261014T233742Z_cb132ce7 \
  --work-root /tmp/t5-v3-replay
```

脚本在 `work-root`（必须位于交付树之外）对交付态运行两遍完整矩阵，再复制整棵交付树到外部 fresh-delivery 目录运行两遍；它复算 manifest、比较四轮归一化结果，并以 SHA-256/bytes/mode/mtime_ns 比较重放前后完整 run 文件集。任何 run 内新增或修改都会使重放失败。

运行时带界 tick 只在外部临时目录生成：P01 使用交付夹具 `max_tick_age_minutes=0`（该工具对 0 不施加上限，且不接受未来时间），P09 每次生成新的 `runtime/tick_valid.json` 并使用 60 分钟界。交付夹具 `dispatch/tick_valid.json` 永不改写。

`external_summary_pin.txt` 与 `valid_delivery_call_independent_pin.json` 是异源文件；运行时由探针读取前者并注入后者缺失的 pin。这只证明夹具层的文件来源分离，不证明真实部署中 pin 由生产者之外的主体控制。

`caller_validator.py` 内嵌 interfaces/operations SHA-256 pin，任何 registry 替换在调用校验和目标执行前以 `FC_INPUT_IDENTITY_MISMATCH` 拒绝；每个登记目标还在执行前按 `target.git_blob_id` 复算字节身份。声明范围是 against the delivered, identity-verified registry。

摘要校验裁决身份绑定，不裁决摘要内容充分性、质量、完整性或科学解释；该范围已在 `recipe_interfaces.json` 的 `caller_contract.scope_boundary` 显式声明。

所有路径参数均为封闭枚举；runtime 路径只能在显式外部 `--runtime-root` 下解析。调用方拒绝绝对路径、`..`、symlink 逃逸、未登记值和类型漂移。操作不含 shell 字符串、自由文本命令、解释器参数、环境变量或任意 argv 入口。
