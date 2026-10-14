# T5 R 两个对象接口

- Run：`20261014T195445Z_60c8e213`；范围仅为运行时预检 recipe 与证据交付 recipe 的封闭接口、调用方校验和本地只读探针。
- 两个 recipe 各负责一个对象，只引用 3 个以 T4 v2 只读适配器为目标的登记操作；未登记操作、shell/命令文本、任意路径、类型/范围错误在目标执行前由调用方拒绝。
- 两轮真实调用方探针各 17/17 一致：2 个合法正例被接受，15 个负例被拒绝；坏摘要只在内存中派生并由 SHA-256 失配拒绝，失配 Markdown 不落盘。
- T4 baseline 只读取案级 `.cases[]`（16 例：detected 6 / missed 2 / not_applicable 2 / unverified 6），未读取 T4R-01 A1 所警示的派生汇总字段。
- 本包仅给 `CONTRACT_PASS`（范围：接口闭合、调用方拒绝、哈希绑定与本地探针一致性），不是科学 PASS、正式实验资格、`END_TO_END_PREFLIGHT_PASS` 或 `FORMAL_RUN_PASS`；独立验收仍为 `UNREVIEWED`，启用仍为 `NOT_ENABLED`。
- B0：模型/网络/远程/生产/数据库/训练/daemon/Loop B 调用为 0，自动重试为 0；执行对话 token 为 `UNRESOLVED`。G1、实际检查数、修复前后对照和未验证面以同目录 `receipt.json` 为准。
