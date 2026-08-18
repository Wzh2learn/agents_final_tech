# memory/STATE.md
更新: 2026-08-19 凌晨（六项批复执行收口: 评测协议 v1 交付 + 小模型矩阵首批 C1/C2）

## 模式
守护模式。本轮队列清空: v1（批复 ①⑤）交付完毕, 矩阵首批（批复 ②）C1/C2
执行完毕。等: ① 甲方首轮反馈（B4 时钟 08-12 启动, asks 已 ≥100, 天数累计中）
② 导师专利时间表对齐（PSO 批复 ③ 缓办前提）③ 用户 NLPCC 2026 workshop
窗口人工核实回话（批复 ⑥）。

## Git
- HEAD: 本收口 commit; 三方对齐 GB10=GitHub=本机
- 本轮提交链: 13d3f57(治理: 六批复入账) → 0f2b63f(v1 代码+测试) →
  4fc251c(GB10 直推: kiosk 计数+Loop B flip) → f8f0a07(判别力分级判据) →
  e350ba8(v1 报告+矩阵 runner) → +本收口(矩阵结果+INDEX+STATE)
- 冻结工件未动（甲方 docx bc3785cb / 导师 docx 929a8c65 / 冻结四文件 md5 复验一致）

## 本轮战绩（六项批复执行）
- 治理（③④⑥）: THREADS 两项 CLOSED; FORCE-Bench 直连核验入 related work
  (arXiv 2607.19409, README ~300 问 vs 摘要 251 差异如实, README 为准);
  "首个"主张降级"引入范式"; 投稿节点定 NLPCC 2027 / CCIR 2027 + arXiv 预印本
- v1（①⑤）: 冻版前后对照零漂移（20 叶/SR/STABLE 与 v0 逐项一致 + judge k=1
  跨日逐题一致）; 判别力 9/9 mutants PASS（标定洞察: rate 叶分级敏感、
  hit_rate 叶灾难态仅 -4.6 钝感 → PSO 输入）; judge --runs k A/B: k1=k3 全 5.0
  (64/64 std=0, 天花板效应如实, 机制验证成立, 生产维持 k=1); evidence cards
  16A; rubric 版本 v_k1 预注册; 报告 docs/experiments/2026-08-19_eval_protocol_v1.md
- 矩阵首批（②, 错峰 :8007）: C1 14B off 11/16·xhigh 14/16; C2 8B off 14/16·
  xhigh 15/16; 基线 A3B 16/16 守擂 → 双双 NO-GO 替换; 三洞察（档位效应实锤/
  8B>14B 异常待复测/q08 掩码姓名共性难题）; 报告 docs/experiments/
  2026-08-19_small_model_matrix_c1c2.md; :8007 探针用毕已停
- pytest 口径更正: GB10 全库 379 passed / 13 skipped（13 项 = 08-10 起 conftest
  显式策略, 非环境抖动; 08-18 "364/1" 口径异常, 以本轮为准）

## 服务
- :5050 UP (route=on, timeout=45, embeddings=137); :8004 A3B UP; :8006 27B UP;
  :8008 proxy UP; :8007 空闲（矩阵探针已停）; :8005 DOWN(退位); :8100 UP;
  :4096 sidecar UP; :15432 PG UP
- Loop B: 00:01/00:34 FAIL = STEP 4 脏文件检测（GB10 本地两文件, 随 4fc251c
  入账清除）, 非服务退化; 周期照常
- 本机: kiosk 已恢复播放（pid 158600 loop_demo + 150708 demo_controller;
  01:55-02:32 曾暂停为 judge A/B 测量纯净, 已入账）

## 质量基线
- eval: 确定性 16/16 + NF 0/9 fail + judge 四维 5.0（k=1 与 k=3 零差, 08-19 复验）
- pytest: 379 passed / 13 skipped（GB10, HEAD f8f0a07+; 口径见上）
- docs_lint: GB10 为准（本机 check[4] = CRLF 已知误报）; INDEX 覆盖 0 warn

## 下一步
1. 矩阵 C3 4B / C4 VL-8B + 14B 异常复测 + 候选答案 judge 四维 + NF --input
   参数化（下个错峰窗, 逐个 go/no-go 续行）
2. 甲方反馈到达 → B4 分布分析（08-19 00:39 起含 kiosk 夜间样本, 注意
   fallback 污染段 01:37-01:55 已如实入账）
3. PSO 等批复 ③ 前提（v1+evidence card 已交付, 剩导师专利时间表）
4. 台账 pending: NLPCC 2026 workshop 窗口用户人工核实
