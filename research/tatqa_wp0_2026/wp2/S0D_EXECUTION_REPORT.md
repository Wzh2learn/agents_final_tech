# S0D 严格性证据补档执行报告

> task: `tatqa-wp2-f5d-20261014` | date: 2026-10-14 | loop: A
> overall: `PASS`
> boundary: 严格性矩阵补建与记录闭环；零模型、endpoint、judge、网络、数据库和服务调用

## 1. 状态

| 项目 | 状态 | 结果 |
|---|---|---|
| 严格性矩阵重建 | `PASS` | 16/16 例完成 pre/post 评分 |
| 严格性统计门 | `PASS` | 5 条变更全部为 `wrong_period` → `wrong` |
| correct-class 安全性 | `PASS` | correct-class flip = 0 |
| 重跑确定性 | `PASS` | 两次完整收据 + 一次对落盘收据复跑均 byte-identical |
| 原断言处置 | `PASS` | 24-case 原句明确撤回；原未落盘 scratch 检查明确撤回 |
| 文档 lint | `PASS` | `0 fail / 14 warn`，未新增 warning |
| 指定授权卡 | `PASS` | `loop_a_prompt_f5.md` 已核验，SHA-256 `0b7f126b…290a4` |
| 指定 Loop C round-3 文件 | `PASS` | `WP2_F5F10_LOOP_C_AUDIT_v1.md` §2.2 已核验，SHA-256 `bfe367cb…b420b` |

overall 为 `PASS`：新矩阵、owner 授权卡与 Loop C round-3 分支差分证明均已在最终验收门上实际读取并哈希核验。

## 2. 实际矩阵结果

- case construction：`periods order × delta_source correctness × delta_target correctness × unit correctness`。
- 总数：`N = 2 × 2 × 2 × 2 = 16`；未预设 24。
- equivalent-form branch space：8；direct-form controls：8。
- changed：5；unchanged：11。
- transition types：`wrong_period->wrong = 5`；其他类型 0。
- correct-class flip：0。
- direct-form controls：0 条变更。

pre 为临时重建的 pre-F-10 `checker_v2.py`，仅删除唯一 F-10 branch C 块；post 为现行 `checker_v2.py`。临时 pre 文件在加载后立即删除；生产 `checker_v2.py` 未修改。

## 3. 新增文件与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `research/tatqa_wp0_2026/wp1/build_s0c_strictness_matrix.py` | `9bf5af883a52c8d73a7abd6df80b49729d1c6549de2dc49857553d505b440aa8` |
| `research/tatqa_wp0_2026/wp1/S0C_STRICTNESS_MATRIX_RECEIPT.json` | `b88c7e1cce159d8f567265d5f5a53ab650758884fee89b5418f42ec8222f115b` |
| `docs/research/F10_STRICTNESS_MATRIX_ADDENDUM_v1.md` | `112f04865707070661847af08b28b30acba413f02a922203ce33fc3682d7e1e6` |

本报告不嵌入自身 SHA-256，避免自引用；最终哈希在本轮文件外登记。

关键既有输入保持不变：

| 输入 | SHA-256 |
|---|---|
| `research/tatqa_wp0_2026/wp1/checker_v2.py` | `aeedf62b7d44a1422ee631783c3daa47be8a3e7e8811462a23ad3c520ce4d048` |
| `research/tatqa_wp0_2026/wp1/checker.py` | `c919845b051a7cfbebfdc782ba4c9dcbd99cac8b950b46f8bd908fcdc2cb12f1` |
| `research/tatqa_wp0_2026/wp2/F5_EXECUTION_REPORT.md` | `c26f422246016bf2817f092fc7e56aa92e57d4b31a93a53c54c03bda8eb78c5f` |

交叉引用也已哈希核验：

| 引用 | SHA-256 |
|---|---|
| `research/tatqa_wp0_2026/wp2/loop_a_prompt_f5.md` | `0b7f126b1938f3d5e1beb9d9b4efc34df09fe89f963c42f8598b97fd97d290a4` |
| `docs/research/WP2_F5F10_LOOP_C_AUDIT_v1.md` | `bfe367cb8be7b362f855c1f4a2c0dc0f0ea6fb317394a80e95a4c694cd2b420b` |

## 4. 命令与结果

1. 构建第一轮：

   `PYTHONHASHSEED=0 python3 research/tatqa_wp0_2026/wp1/build_s0c_strictness_matrix.py --output /tmp/.../run1.json`

   输出：`cases=16 changed=5 correct_flips=0 PASS`。

2. 构建第二轮并比较：

   `PYTHONHASHSEED=0 python3 research/tatqa_wp0_2026/wp1/build_s0c_strictness_matrix.py --output /tmp/.../run2.json`

   `cmp -s /tmp/.../run1.json /tmp/.../run2.json`

   结果：byte-identical；两文件 SHA-256 均为 `b88c7e1c...f115b`。

3. 对已落盘收据 fresh rerun：

   `PYTHONHASHSEED=0 python3 research/tatqa_wp0_2026/wp1/build_s0c_strictness_matrix.py --output /tmp/.../rerun.json`

   `cmp -s research/tatqa_wp0_2026/wp1/S0C_STRICTNESS_MATRIX_RECEIPT.json /tmp/.../rerun.json`

   结果：byte-identical。

4. 文档 lint：

   `python3 scripts/docs_lint.py --json /tmp/s0d_docs_lint_report_v2.json`

   结果：`PASS (0 fail / 14 warn)`；14 条均为既有 warning。

5. 仓内引用核查：

   `nl -ba <path>`、`sha256sum <path>`、`rg -n '^### 2.2' <path>`

   结果：owner 授权卡已读取；Loop C round-3 §2.2 已读取。二者证明本轮没有扩大原 F-10 授权，且独立确认严格性界仅为 `wrong_period` → `wrong`、无 correct-class 翻转。

## 5. 原断言与引用处置

- 已撤回 `F5_EXECUTION_REPORT.md` L23 的 "24-case / five changed classifications" 原句作为未落盘 scratch 断言。
- 新矩阵得到的是 `16 cases / 5 changes / 0 correct flips`；5 的数量不能追溯性地证明原 scratch 的 24-case 产物存在。
- 新收据和补档均标注：`post-hoc reconstruction；原未落盘 scratch 检查已撤回`。
- Loop C round-3 §2.2 提供静态分支差分证明，与新矩阵的逐例实跑结果一致。
- 未覆写 `F5_EXECUTION_REPORT.md` 或任何既有收据。

## 6. 遗留点

1. S7 建议仍待 C3 备档：`prepare_item` / `recompute_gold` 增加 `late != early` fail-closed 断言；runner 携带 pre-fix 实跑路径。
2. 未执行 S4+、item freeze、pilot、actor selection、训练或任何模型相关动作。
3. 未 git add、commit、push；工作区原有其他修改保持未动。

## 7. 调用计数

| 类型 | 计数 |
|---|---:|
| model calls | 0 |
| endpoint calls | 0 |
| judge calls | 0 |
| network calls | 0 |
| database calls | 0 |
| service restarts/probes | 0 |
