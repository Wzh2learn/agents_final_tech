# T4 v2 工程能力基线

- Run: `20261014T184810Z_c9dcfe0e`；supersedes v1 `20261014T174628Z_2cc25c92`。
- v1 阻断已修复：仓库内 9 个 `.md` 全部通过守卫（G1）；失配 Markdown 不再持久化，仅在临时目录派生并由既有守卫判 FAIL（G2）。
- 16 例映射不变；11 个适用组合两轮回放一致；画像仍为 detected 6 / missed 2 / not_applicable 2 / unverified 6（G3 零结果差异）。
- 适配器调用 22 次；模型/网络/远程/生产/数据库/训练/daemon/Loop B 调用均为 0；自动重试 0。
- 本包是工程能力画像，不是科学实验或正式基线；6 个案例仍为未验证面，执行对话 token 为 `UNRESOLVED`，独立验收仍 `UNREVIEWED`。
