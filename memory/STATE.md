# memory/STATE.md
更新: 2026-08-18 晚（科研探索队列 K1-K6 收口; 导师演示已于 08-18 白天完成并获三层指导）

## 模式
导师演示已完成（docs/33 = 演示后指导吸收）。冻结窗实质解除（K 队列全程
以"不跑生产推理/不动运行时"约束执行完毕）; kiosk 展示循环仍在本机播放
（隧道+控制器+loop 三会话, 演示用）。等: ① 甲方首轮反馈 ② 导师后续意见
③ 用户对 docs/33 §8 倒排计划中"待拍板"项的批准。

## Git
- HEAD: 本收口 commit（其前为 884221e）; 三方对齐 GB10=GitHub=本机
- K 队列提交链: 807e810(docs/33) → 48255f7(K1) → 9befc93(K2) → 49a4ec2(K3)
  → 0250624(K4) → 884221e(K5) → +本收口(K6)
- 冻结工件未动（甲方 docx bc3785cb / 导师 docx 929a8c65）;
  config/schema_suggestions.json 的 modified = kiosk 自学习新数据, 待下轮 apply 窗口

## 本轮战绩（科研探索队列 K1-K6, graph loop 全程: D 发卡 → A(flash) 执行 → D 验收）
- K1 ✅ 48255f7: hbkeyan 两篇精读 — GTA-2 检查点树 SOP(Steps 0-6+Algorithm 1)
  + 本项目解析/QA 四层映射 + Judge 技巧 T1-T14 逐条适用性(防漂移: k=3-5 均值化优先)
- K2 ✅ 9befc93: 评测协议 v0 — 树定义 20 叶 + Algorithm 1 聚合脚本 + 首份分层
  报告(Root 10.0/10.0, 口径对照 16/16/judge/NF 零漂移) + 20 测试
- K3 ✅ 49a4ec2: 漂移注入器 v0 — TAT-QA 2479 表 6 类注入/95 样本表/确定性 sha256
  契约, 独立 venv; VGMC 实验 1 输入就位; pytest 全库 364 passed/1 skipped
- K4 ✅ 0250624: 小模型矩阵设计 — 6 候选(5 磁盘零下载)全过内存预算门,
  K2 协议固定题库 + Score/Cost Pareto; 执行待批准窗口
- K5 ✅ 884221e: PSO 落点一页方案 — 权重分配+最小判别题集, 三要素齐全,
  专利权利要求逐条对应; 只出方案
- K6 ✅: docs/33 §8 带日期倒排计划 + INDEX 登记 7 行 + docs_lint 0 warn
- 治理沉淀: GB10 codex exec 需 --dangerously-bypass-approvals-and-sandbox
  (bwrap 失败) + apply_patch 不可用需 heredoc + 大 PDF 预提取分块读 (任务卡模板化)

## 服务
- :5050 UP (route=on, timeout=45, embeddings=137); :8004 A3B UP; :8006 27B UP;
  :8008 proxy UP; :8005 DOWN(退位); :8100 UP; :4096 sidecar UP; :15432 PG UP
- Loop B: 照常周期观察（K 队列未扰）
- 本机: 演示隧道+demo 控制器+kiosk loop 播放中（本地未提交, 演示资产）

## 质量基线
- pytest 364 passed / 1 skipped（K3 后全库口径; 含 K2 20 测试 + K3 8 测试）
- docs_lint: GB10 为准（本机 check[4] = CRLF 已知误报）; INDEX 覆盖 0 warn
- eval v2 08-16 口径仍为最新（演示日未重跑; P0 修复后重跑列下一步第 1 项）

## 下一步（docs/33 §8 倒排, 待拍板项标注）
1. 08-19~20 评测协议 v1: 缺陷样本判别力 + judge --runs k A/B（K1 T2/T3/T10 并行; 需解冻确认）
2. 08-20~22 VGMC 实验 1: 95 注入表门控闭环（论文 A 主图; :8006 错峰）
3. 拟 08-21~24 小模型矩阵执行（**待用户批准窗口**; K4 设计已就绪）
4. PSO 实现 08-23 后（待拍板; 依赖 1/2 判别力数据）
5. eval 重跑（P0 修复后口径）— 演示后积压第 1 项
6. 用户侧 pending: 甲方会谈排期 / NLPCC-CCIR 截稿日浏览器查询 / 矩阵窗口批准
