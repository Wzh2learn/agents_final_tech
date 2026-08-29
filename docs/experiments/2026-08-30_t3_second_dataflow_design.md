# T3 第二数据流验证设计稿（Phase 2 E2.4, 零端点, 解冻范围限定）

> 状态: 预注册（执行前） | 创建: 2026-08-30 | 任务卡: docs/superpowers/plans/2026-08-29-long-horizon-evaluation-paper.md T3
> 解冻裁定（2026-08-30, 用户事项一）: 解冻 TAT-DQA joint-v1, 范围仅限 T3 一项——只在已冻结的 validation split 上构造注入, 不碰 test split, 不重开任何旧 TAT-DQA 实验循环; T3 完成后冻结线恢复冻结
> 红线: 甲方数据零进入; 零端点; 专利终态件只读; tat_dqa 相关既有文件（tests/test_tat_dqa_*.py / scripts/*tat_dqa*）零改动, 新脚本只读使用数据

## 1 对应主张与判据（蓝图 §1 原样引用, 判据冻结）

对应主张 C1: 「仅看最终答案无法区分"缺陷被检出"与"被中间层静默吸收"」。

- 成功标准（预注册）: 「OCR 形近全盲与类型不均匀在 γ∈{0.3,0.5,0.7,0.9} 网格内成立、经等价变异校正后存续、第二数据流方向一致」
- 失败后降级表述（预注册）: 「第二数据流不复现: 主张收窄为"金融表头匹配层观察到结构性盲区"，不推广到任意长流程管线」

本卡承担成功标准中"第二数据流方向一致"一维（γ 网格与等价变异校正由 T2 承担）。

## 2 输入工件与数据边界

| 工件/数据 | 角色 | 边界 |
|---|---|---|
| docs/datasets/tat-dqa-joint-v1-manifest.json + checks.json（仓库内冻结契约） | split 定义: 官方 dev→validation（20 文档/100 问题）, test-gold→test | 只读 |
| /home/testuser/wzh/datasets/tat-dqa/raw/tatdqa_dataset_dev.json（GB10 仓外） | validation 源数据（表块抽取输入） | 只读 |
| tatdqa_dataset_test_gold.json / test.json | test split | **零读取零触碰**（脚本运行时断言不打开） |
| scripts/research/drift_inject.py | 6 类注入器（确定性, 复用） | 只读导入 |
| scripts/m1_statement_parser.py map_headers | 被测匹配层（与 95 表臂同一冻结匹配器） | 只读导入 |
| logs/graph/eval/checkpoint_discrimination_tables_v2.json | 第一数据流基线（对照锚） | 只读 |

## 3 操作化定义

1. 表头抽取: 从 validation split 20 文档的 dev json 表块中确定性抽取表头行（新脚本, 规则 = 首非空行为表头; 列数 <2 或全空表头剔除并计数）; 产出 tatdqa_validation_tables.json（uid + table）。
2. 注入构造: 复用 drift_inject.py（seed=20260830, ratio=0.3, 与 v0 同参数族）, 注入器词库原样（英文金融词库与 TAT-DQA 英文底座天然适配）; 产出注入表 + 注入映射（同 drift_v0 工件格式）。
3. 判别协议: 与 95 表臂同流（k2_table_discrimination_v2 逻辑复用或同构实现）: original 重建 + 自含 canonical schema + 双臂 map_headers + drop10≥2.0 表级判据 + 注入级吸收判据; 零端点。
4. 指标: 按类型可见率 + 表级判别率 + 吸收谱; 与第一数据流（95 表臂）并列报告。

## 4 预注册预测与判据

1. 复现门 G1: 95 表臂对照重算不变（引用冻结工件, 不重跑）。
2. 主判据（成功标准"方向一致"的操作化）: 第二数据流上"类型间判别率不均匀"复现 ⟺ 六类（实际命中类型）可见率极差 ≥ 0.5 且 ocr_similar 类可见率为六类最低。
3. 辅助预测（不承诺, 如实报告）: ocr_similar 在英文文档表头上仍高吸收（编辑距离≤1 兜底机制与语言无关）; 若注入器某类型在 TAT-DQA 表头零命中, 该类型记"未覆盖", 不冒充 0。
4. 泄漏防线: 脚本运行时断言未打开 test-gold/test 文件 + 产物中零 test split document_id（对照 manifest 的 split 标签）。
5. 降级触发: 主判据不过 → 按 §1 降级表述执行（写作卡切换措辞）, 本卡只产证据。

## 5 工件命名与复算

- 执行脚本: research/paper_t3_second_dataflow.py（新脚本; tat_dqa 既有文件零改动）
- 输出工件: logs/graph/eval/t3_second_dataflow_validation.json（表头抽取统计 + 注入映射摘要 + 按类型可见率 + 泄漏断言记录 + payload sha256）; 中间语料 tatdqa_validation_tables.json 落 data/research/t3_validation/（GB10 仓外, 路径写入工件）
- 执行者: Loop A（GB10）; 主线程拟卡与抽验
- 完成后: 冻结线恢复冻结（THREADS 销账 + STATE 更新, 主线程执行）

## 6 红线自查（设计期）

- 解冻范围: 仅 validation split, test split 零触碰（运行时断言） ✓
- 不重开旧 TAT-DQA 实验循环: 只跑注入判别协议, 不跑旧检索/QA 循环 ✓
- 零端点: 纯规则 ✓
- tat_dqa 冻结文件零改动: 新脚本只读数据不动代码 ✓
