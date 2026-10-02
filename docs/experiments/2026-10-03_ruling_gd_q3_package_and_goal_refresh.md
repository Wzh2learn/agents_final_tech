# 裁定落地与 Valentine 146 列 Q3 复核包（2026-10-03）

> 状态: 执行证据件（Loop D） | 裁定: G-A..G-E + V2-3 + docs_lint 基线 B
> 运行环境: GB10 唯一权威；本机仅 git / 文本编辑 / commit / push
> 模型调用: **0**。R1/R2 与裁决派发停在用户确认 Token Plan token 是否已轮换之前。

## 1. 裁定落地

| 项 | 落地口径 | 本批动作 |
|---|---|---|
| G-A | 不批 | Valentine 维持 `PILOT_ONLY proposal_train`，不承担 gate/sealed |
| G-B | 不批 | 维持 frozen hash-threshold bucketing；不为四层非空改规则 |
| G-C | 本批不批 | 不选源、不下载；扩到 ≥40 origin cluster 另开精确申报卡 |
| G-D | 批准 | canonical 参考 = 同一官方来源 `target_table.csv` 表头 |
| G-E | 接受 | 动作包维持 `DATA_NO_GO`；RQ2 = `NOT_IDENTIFIED`；146 列复核只作 exploratory |
| V2-3 | 关闭 | 步级重执行按预注册停止条件归档；不开 v3、不申报 FinQA 算子代码/文档 |

边界：G-D 不改变 gate/split/功效/训练门；exploratory 不得报为 Stage D 闭合或确认性证据。

## 2. docs_lint 基线 B

`logs/graph/docs_lint_warn_baseline.md` 由 1 条扩为 4 条，逐条注明「历史/受保护件，时效 warn 不代表内容错误；真实内容更新另批」。未回改正文、未消警、未改 `docs_lint.py`。

GB10 @ `31ba327` 实测：`rc=0 / 0 fail / 4 warn`。机器解析基线与 report 的“检查项 + 路径”集合：

```
BASE   = { [2] docs/32_模型升级与多agent再思考.md,
           [2] docs/33_导师指导吸收_科研三线升级.md,
           [2] docs/34_专利_小论文_大论文协同研究路线.md,
           [2] docs/m1_coldstart_candidates.md }
ACTUAL = 同一集合
SET_EQUAL=True COUNT=4/4
```

## 3. 146 列 Q3 复核包

### 3.1 输入与稳定身份

- 来源：GB10 `~/wzh/phase1a_staging_20260925/`，Valentine ref `5d5163f04da304985bd51a476ccf7653de3979c3`。
- `sha256_manifest.txt` sha256 = `c11d26f8fe58ea13b443bd4be8c7f946fa53778f84dc360f929060a7e46ba7dd`，64 项；source/target 逐文件 hash 全部与该 manifest fail-closed 对齐。
- 10 个 pair / 146 个源列 / 160 个目标表头。`sample_id` 由 dataset revision + lineage root + column index 稳定哈希；`uid` 复用 `research/phase1a_data_contract.lineage_uid`。
- canonical reference = 每个 pair 的 `target_table.csv` 表头；reference digest = `685197fdd1d2bcb32ca73a9fa0613af0314b088787657df2cafb3c26bf4fb83b`。

### 3.2 包结构与哈希

产物在 GB10 `/tmp/valentine_q3_20261003_jeDV/package_a/`，数据正文与逐样本材料不入 Git。共 18 文件：

- `samples.jsonl`：146 行稳定样本元数据；
- `canonical_reference.json`：G-D 批准的目标表头摘录；
- 3 块（50 / 50 / 46）× {R1 JSON、R1 prompt、R2 JSON、R2 prompt、裁决空模板}；
- `manifest.json`：输入读取面、载具可见性、文件 hash。

```
manifest.json          d91fd7d46a8c02c7ef4432d3fa1f38d8b5b42956746723d33244bd9dbcb94b5c
samples.jsonl          6843f4c500a90335f5b66f48e130565bb3887407aa1ad8971a99385e9ea28c6d
canonical_reference    241ca7ed1ef30c4531cd9d6c7dc03652c00142eb7a0d622c637489b57bede377
build.strace           b588bf9a966d07eb0bfa06dfa2760fa179d84fea081904b18bfa3cfc15c54258
```

### 3.3 可见性边界自证

- builder 的允许读取面只含 20 个 `source_table.csv` / `target_table.csv`；manifest 明记 `forbidden_files_read=[]`、`forbidden_open_count=0`。
- 10 个 `ground_truth.json` 均存在，仅通过 `Path.exists()` 计数；**从未 open / read**。
- `strace -f -e trace=openat,open` 的 `ground_truth.json` openat/open 命中 **0**。
- R1/R2 仅见 source header、canonical reference、LABEL_FIELDS 语义；裁决模板初始 action/target 全空，且不预置任何裁决。三载体均声明禁见 `ground_truth.json`、pipeline mapping、injection map、他载体判定。
- 双跑 `package_a` / `package_b`：`diff -qr` rc=0，全包逐字节一致。

## 4. 实跑偏差与修正（如实入账）

1. 首次合同测试 1 failed / 4 passed：fixture 把 CSV 列名写成 `source_src_*`，而断言要求每列 `src_*`。根因在测试数据生成器；只修 fixture 前缀，**未放宽断言、未改 builder**。
2. 首次真实包调用 `python research/valentine_q3_review_package.py` 因 `ModuleNotFoundError: research` 退出。根因是 direct-script 的 `sys.path[0]`；按仓内 finqa adapter / split_assign 既定模式把仓库根插回 import path，并新增“删除 `PYTHONPATH` 后 `--help` 仍 rc=0”的负例。
3. 修正后 GB10 @ `b1923fe`：`tests/test_valentine_q3_review_package.py` **6 passed / rc=0**；真实包双跑 rc=0。

## 5. Token Plan 配置交接（不含密钥值）

本件不读取 `~/.claude/settings.json` 的 `env` 值，也不写 token、prefix 或长度。只固化用户给出的路由口径：

- Loop C：GB10 Claude Code 默认 `qwen3.8-max`；
- Loop A：`~/.codex/config.toml` 的 `deepseek-v4.1-flash`；
- MIMO `mimo-v2.6-flash` / `mimo-v2.6-pro` 继续挂起，不重试、不换模型、不调试；
- `ANTHROPIC_AUTH_TOKEN` 由用户控制；任何读取操作必须过滤 `env`。本轮模型派发前须由用户确认该 token 已轮换；未确认不派发、不把旧值当新值、不自行重试。

## 6. Goal 推进重点（核心目标与安全边界不变）

1. 两份交付物按当前口径的完成核验已有证据链：claim 校验 73/73、双模型第 5 轮 ACCEPT、全链路独立审计、Office 视觉验收 PASS。
2. 唯一在途执行项 = G-D 下 146 列 Q3 三载体复核，严格标 exploratory。
3. 门链不再作为当前推进项；按 G-E 归档为用户裁定维持 `DATA_NO_GO` / RQ2 `NOT_IDENTIFIED`。

146 列复核完成后，须按目标完成标准逐项做完成审计；任一项不确定按未达成处理，不以部分落盘申报完成。

## 7. 红线自查

零模型调用、零业务端点、零下载；未读 token；数据体不入 Git；未改冻结判据 / hash / 数据合同；未覆盖 production 脏件；未重启 daemon / :5050；逐路径 add，无 `--amend`、无 `--no-verify`；专利未确认前不外发、不上 arXiv、不公开代码。

## 8 Exploratory result state（2026-10-03）

- 当前闭合的是**输入包与可见性边界**，不是 Q3 结果：R1/R2 尚未派发，独立裁决未发生。
- 尚不存在 `labels.jsonl`、review agreement、adjudication rate、action 分布、target exact agreement、learnability 指标或任何模型输出。
- 因此 exploratory 状态为 **NOT_RUN / UNFINISHED**；不得把 146 个输入样本数、160 个目标表头数或包哈希写成标注结果、可学性结果、Stage D 闭合、RQ2 确认或 `DATA_GO`。
