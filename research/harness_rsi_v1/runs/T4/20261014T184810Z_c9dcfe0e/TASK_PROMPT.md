# Loop A 任务：T4 v2 返工 —— 夹具可提交性修复 + 全套包件再生成

本任务是 T4 v1 run `20261014T174628Z_2cc25c92` 的返工版本。T4 任务卡与科学范围不变；唯一返工动机是 v1 包内持久化了故意失配的 Markdown 收据夹具，导致仓库 pre-commit 的 `summary_recompute_guard.py` 硬阻断。

## v2 硬要求

1. 不在本 run 内任何 `.md` 中持久化故意失配的 SUMMARY-GUARD 收据块。
2. 失配场景改为运行期派生：仓库内基底 Markdown 必须通过守卫；派生脚本在临时区把匹配 claim 改为不匹配 claim；守卫 FAIL 输出、派生件 sha256 和命令证据保留在本 run 的日志中；派生 Markdown 本体在命令结束前删除。
3. 所有持久化 SUMMARY-GUARD 的 `artifact:` 必须引用本 v2 run 内路径。
4. 对 11 个适用 (工具, 案例) 组合执行两轮回放，重建 `scratch/tool_outputs/`、`baseline.json` 与 `baseline_recipe.json`。
5. 全量重建 `adapters/`、`fixtures/`、`receipt.json`、`summary.md`、`artifacts_manifest.json`、`events.jsonl` 与本任务书；新增 `supersedes` 字段，记录 v1 run_id、返工原因和保留方式。
6. 案例→检查映射语义、适配器旧工具路由范围、结论口径和未验证面处置不得改变。若画像与 v1 不同，如实记录并分析。

## 预算与边界

- profile=B0：模型、网络、远程、生产、数据库、训练、daemon、Loop B 调用均为 0；自动重试为 0。
- 仅写 `research/harness_rsi_v1/runs/T4/20261014T184810Z_c9dcfe0e/`；不覆盖 v1，不做 git commit/push，不改其他文件。
- 执行对话 token 不可计量，保留为 `UNRESOLVED`。
- 不得以删除案例、放宽检查或丢证据的方式过守卫。

## 完成前自检

保留 v1 的 A1、A2、A3、A-common、两轮一致性、哈希重算、写入边界和 B0 计数，并新增：

- G1：对本 run 内每个 `.md` 逐个执行守卫 `check`，全部 rc=0，记录完整矩阵。
- G2：全包扫描无任何含失配收据块的 `.md`；失配件仅在运行期临时派生或完全不留本体。
- G3：给出 v1↔v2 结果差异表；零差异或逐项解释。

本包只表示工程能力画像，不是科学实验、正式基线或独立验收。
