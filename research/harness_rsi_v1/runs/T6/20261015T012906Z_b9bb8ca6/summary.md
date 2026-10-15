# T6 有界提案与统一档案

- 交付 `archive_implementation/`：以文件 SHA-256 + git 归一化 mode 构造父内容组；T5 v3 @115f396 为 45 成员、T4 v2 为 64 成员，当前验证均 PASS，T5 声明 mode 45/45 一致。
- 失败缓冲本地演证：重复 T5 P01/P09 包 `cand-20a78eae4dda3ca9` 命中 nogood，返回 `REJECTED_DUPLICATE_NOGOOD` 且 `activation_enabled=false`；拒绝可按新父组/新证据条件重开。
- 选择性导出只带候选、父组 ID、引用证据、匹配 lesson 与机制字段，不复制完整父包或完整档案；证据去重 raw 6 / unique 5 / duplicate pair 1。
- 候选 2 个：`cand-d44c49dec4d95741` 是 T1-INC-14 缺 receipt block 的证据交付提议（两条当前操作 + 一条需未来授权），仅 `PROPOSED_NOT_ENABLED`；另一候选是故意重复失败包，已拒绝。
- 本卡未运行 T7、Loop B、模型批次、网络/远程/生产/数据库/训练/daemon；额外便宜请求 0/4、强请求 0、模型调用 0，自动重试 0。独立验收仍 `UNREVIEWED`，全部候选 `NOT_ENABLED`。

<!-- SUMMARY-GUARD
artifact: research/harness_rsi_v1/runs/T6/20261015T012906Z_b9bb8ca6/receipt.json
sha256: 1c6a718761edf04c14644639869a3beff1916f8e9166f05ebbbd6e2339e0c1f1
claims:
  usage.additional_cheap_requests = 0
  usage.additional_strong_requests = 0
  checks_by_id.a1.result = PASS
  checks_by_id.a2.result = PASS
  checks_by_id.a3.result = PASS
  checks_by_id.a_common.result = PASS
END-SUMMARY-GUARD -->
