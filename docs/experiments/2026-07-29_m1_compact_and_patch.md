# M1 Parser 紧凑摘要 + C 待审补丁回写

日期: 2026-07-29
执行: Codex CLI（Qoder CLI 认证通过、:8004 Qwen3-14B 在线）
范围: `scripts/m1_statement_parser.py`（`--compact-summary` 旁路）+ `~/wzh/m1_samples/m1_table_schema.json`（C 补丁回写）
约束: 样本/schema 在项目外不进 Git；报告已脱敏；未改 `src/biz/m1_service.py`；未碰 TAT-DQA。

---

## 1. 紧凑摘要（`--compact-summary`）

### 实现

`build_compact_summary()` 已就绪（前序会话实现），本轮验证通过。每样本输出：

```json
{
  "sample_id": "sample_fuxi_hunhe25_20231101.txt",
  "n_tables": 2,
  "reconcile": {
    "market_value": "PASS",
    "currency": "PASS",
    "date": "PASS",
    "silent_mismatch": "PASS"
  },
  "n_unmapped": 1,
  "unmapped_cols": ["证券市值"]
}
```

### 体积

| 输出 | 体积 | 备注 |
|------|------|------|
| `--json` 全量 | **216,276 B** (~211 KB) | 6 样本，超出 16K context |
| `--compact-summary` | **1,356 B** (~1.3 KB) | 6 样本，远小于 16K tokens |
| 压缩比 | **0.63%** | 全量的 1/159 |

紧凑摘要包含全部 4 项勾稽结论（market_value / currency / date / silent_mismatch）+ unmapped 列名，
足以支撑 evidence-verifier 独立复核，无需读全量 JSON。

---

## 2. C 待审补丁回写 schema

### 来源

`docs/experiments/2026-07-29_m1_header_mapping_llm.md` 第 4 节：15 条通过勾稽安全门的
LLM 建议（13 个新标准字段，含 15 个源列映射）。

### 回写内容

| 归属表 | 新增标准字段 | synonyms | Δ unmapped |
|--------|-------------|----------|-----------|
| 证券持仓明细 | 交易日期 | 交易日期, 发生日期 | 2 |
| 证券持仓明细 | 代理费用 | 代理费 | 1 |
| 证券持仓明细 | 印花税 | 印花税 | 2 |
| 证券持仓明细 | 在途数量 | 在途数量 | 1 |
| 证券持仓明细 | 基金净值 | 基金净值 | 1 |
| 证券持仓明细 | 最新单价 | 市值价 | 1 |
| 证券持仓明细 | 成交数量 | 成交股数 | 1 |
| 证券持仓明细 | 手续费 | 手续费 | 2 |
| 证券持仓明细 | 清算费用 | 清算费 | 1 |
| 证券持仓明细 | 累计净值 | 累计净值 | 1 |
| 证券持仓明细 | 资产账号 | 资产账号 | 1 |
| 资金资产汇总 | 币种 | 币种 | 1 |
| 资金资产汇总 | 资产账户 | 资产账户 | 1 |

### 状态

本轮检查发现 **13 个字段已全部存在于 schema**（前序会话已回写），无需重复操作。
备份已创建: `m1_table_schema.json.bak_pre_c_patch`。

### Unmapped 对比

| 阶段 | unmapped 总计 | 来源 |
|------|-------------|------|
| C 补丁前（基线） | **39** | C 报告 §0 |
| C 补丁后（当前） | **23** | 本轮 parser 验证 |
| 降幅 | **-16 (-41%)** | 与 C 报告 §6 一致 |

剩余 23 个 unmapped 分布：
- `sample_jiaxing_minan_20231031.pdf`: 22 个（嘉兴样本多子表，多为仅表头 rows=0 的流水/申赎/配号表）
- `sample_fuxi_hunhe25_20231101.txt`: 1 个（证券市值——目标标准字段已被更优近义词占用）

进一步降低需扩展 schema 覆盖嘉兴样本的交易规费、过户费、财汇局征费等港股特有列，
属后续运营人审范畴。

---

## 3. 双跳验证（coordinator → m1-extraction → evidence-verifier）

### 结果: **BLOCKED**

| 检查项 | 状态 |
|--------|------|
| OpenCode 二进制 | ✅ `~/.opencode/bin/opencode` 可用 |
| agent 配置 | ✅ m1-extraction / evidence-verifier 已注册（subagent） |
| 非交互执行 | ❌ `opencode run` 模式下 `bash: "ask"` 权限被 auto-reject |
| 双跳完成 | ❌ 未执行 |

### 根因

1. `opencode.json` 中 `"bash": "ask"` — 非交互 `run` 模式无用户审批，所有 bash 调用被自动拒绝。
2. `m1-extraction` 是 subagent（`mode: "subagent"`），`opencode run --agent m1-extraction`
   回退到 default agent，无法直接以 subagent 身份运行。
3. 与 AGENTS.md 记录一致：**"Multi-agent automatic delegation is NOT verified end-to-end."**

### 解锁路径

- 方案 A: 将 `opencode.json` 的 `"bash": "ask"` 改为 `"bash": "allow"`（需评审安全风险）。
- 方案 B: 交互模式下人工审批 bash 权限，手动触发双跳。
- 方案 C: 绕过 OpenCode，用 Qoder CLI 串行模拟双跳（parser 产出 → 紧凑摘要 → 独立复核 prompt）。

紧凑摘要（1.3 KB）已就绪，evidence-verifier 的 16K context 瓶颈已消除；
双跳阻塞点从「数据体积」转移到「OpenCode 权限配置」。

---

## 4. 对甲方 M1 主线的贡献

- **紧凑摘要旁路**: 1.3 KB vs 211 KB（1/159），解锁 evidence-verifier 在 16K context 下的
  独立复核能力，为双跳多 agent 验证扫清数据层障碍。
- **C 补丁已生效**: unmapped 39 → 23（-41%），嘉兴样本持仓明细表命中率显著提升
  （p0_table_3: 100%, p0_table_4: 80%→90%+），减少运营人工补映射工作量。
- **闭环验证**: 紧凑摘要包含全部 4 项勾稽结论 + unmapped 列名，evidence-verifier 可据此
  做 PASS/FAIL 独立判定，无需理解全量解析细节。
- **下一步**: 解锁 OpenCode 权限（或 Qoder 串行模拟）后完成双跳端到端验证；
  嘉兴样本剩余 22 个 unmapped 需运营人审扩 schema。

---

*报告已脱敏。schema 与样本在项目外 `~/wzh/m1_samples/`，不进 Git。*
*未改 `src/biz/m1_service.py`；未碰 TAT-DQA / test split；未下载模型；未 push。*
