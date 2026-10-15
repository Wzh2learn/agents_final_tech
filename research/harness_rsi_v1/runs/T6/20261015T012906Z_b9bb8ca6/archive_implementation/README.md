# T6 共用谱系与失败缓冲机制

本目录是本 run 内的本地确定性机制，仅使用 Python 3.12 标准库与只读本地 Git 对象。它不修改 T4、T5、共享 registry、`meta/lessons.jsonl`、`meta/nogoods.jsonl`、生产服务、数据库或模型端点。

## 谱系与唯一 ID

- 父版本不是任务名推断，而是“成员清单 + 每个文件 SHA-256 + git 归一化 mode”的内容哈希组。
- T5 v3 canonical id：`T5-v3:20261014T233742Z_cb132ce7@115f396af`，内容组 45 个成员；T4 v2 canonical id：`T4-v2:20261014T184810Z_c9dcfe0e`，内容组 64 个成员。
- candidate/evaluation id 分别由各自的 canonical identity JSON 计算，不含时间、路径或运行序号。
- T5 声明 mode 先逐项与交付工作树比对；内容组再使用 git 语义 mode，避免 T5R-04 ADVISORY-2 的 umask 表示耦合。

验证命令（均应在仓库根运行）：

```bash
python3 -B research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/archive_implementation/archive.py validate-parents
python3 -B research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/archive_implementation/archive.py evaluate research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/candidate_packages/cand-d44c49dec4d95741/candidate.json
python3 -B research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/archive_implementation/archive.py evaluate research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/candidate_packages/cand-20a78eae4dda3ca9/candidate.json
python3 -B research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/archive_implementation/archive.py export-context research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/candidate_packages/cand-d44c49dec4d95741/candidate.json
python3 -B research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/archive_implementation/archive.py count-evidence research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/candidate_packages
```

## 失败缓冲

- `fixtures/lessons.jsonl` 保存经验、适用父组与重开条件；本卡只读本地投影，不写共享 lessons 存放点。
- `fixtures/nogoods.jsonl` 保存被拒签名、拒绝原因、版本适用条件与 reopen conditions。“拒绝 ≠ 永远无效”：签名相同时拒绝且 `activation_enabled=false`；父组、失败证据或目标语义发生实质变化后才允许重提。
- 重复已证失败包 `cand-20a78eae4dda3ca9` 命中 `NOG-T6-DUP-001`，返回 `REJECTED_DUPLICATE_NOGOOD`。

## 选择性上下文与去重

- `export-context` 仅投影 candidate、父组 ID、被引用证据、匹配 lesson 与最小机制字段；不复制完整父包、完整共享档案或未引用证据。
- `count-evidence` 同时报告原始候选引用数、全局唯一证据数与跨候选重复对；唯一证据在全局总数中只计一次。本批为 raw 6 / unique 5 / duplicate pair 1。

## 未验证面

- 本机制只在当前本地 Git 工作树与两个已验收父包上演证；未验证跨机器、换 umask 的复制链、真实 Loop D 调用、封存集、T7 配对评价或 promotion。
- C/S 机制可复用仅是接口层陈述；本卡没有 C/S 模型批次、额外便宜请求、强请求、网络、远程、生产、数据库、训练或 daemon 调用。
- 候选第三条若标记“需未来授权”，当前词汇无法执行；T6 未改共享件，也不把提案解释为可启用实现。
