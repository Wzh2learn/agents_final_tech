# 段 D 完成率塌方 × q06 空检索归因报告（2026-08-24 夜, 红旗 1+2 合并归因）

> 状态: 归因完成, 修复菜单待批 | 更新: 2026-08-24 | 取代/被取代: 无
> 触发: 红旗 1 段 D 完成率 1.8%（基线 15-19%）/ 红旗 2 q06 直连空检索抖一天（03:13/21:05/21:38/22:12）
> 结论: **两红旗同根**——08-23 两项修复（实例缓存长驻池 × GUC idle_session_timeout=10min）的化学反应, 被 smart_retrieve 异常吞没放大为静默错误答案

## 1 根因链（实证闭环）

1. 08-23 窗口: `idle_session_timeout=10min` GUC（池饱和兜底）+ vector_store 实例缓存（engine-per-search 根治）同窗生效
2. 实例缓存使 SQLAlchemy engine/池长驻; canary/eval 流量是脉冲式（30min 周期）, 池连接在周期间隔内 idle >10min → **PG 服务端杀连接, 客户端池不自知**
3. 下次检出死连接: `get_vector_store` 建引擎无 `pool_pre_ping` / `pool_recycle`（src/tools/vector_store.py, PGVector 仅传 connection 字符串）→ 首查抛 `psycopg.errors.IdleSessionTimeout`
4. **异常被吞**: `smart_retrieve` L322-330 `except Exception: logger.warning(...)`（WARNING 级非 ERROR 级 → 查错误日志查不到）
5. `vector_count==0` → `_local_fallback_docs`: 非相似度兜底（DocumentManager 取 15 条候选）→ **把无关 chunk 当检索结果返回**（实测 top score 0.0027）
6. 直连路（每周期首查, 池最冷）→ q06 canary 答错/空 → Loop B 翻转（翻转时点=canary 完成时点, 症状对上）
7. MCP 进程同病（独立池同代码路径, m1_service.log 49 条同类错误）→ agent 首查吃兜底垃圾证据 → 多绕 step → 完成率进一步压低

**证据**:
- app.log `Vector retrieve failed ... IdleSessionTimeout` **216 条**, 时间戳与 canary 周期起点逐一对上（17:43:14/18:15:03/18:48:33/19:22:05/20:29:43/21:02:26/21:05:04/21:35:57/22:09:28...）; m1_service.log 49 条
- **双窗复现（22:32, 只读, 经 :5050 生产端点）**: ASK1 冷池（距上次用 21min）→ "检索资料中未找到相关数据" + 博时传统 score 0.0027 兜底源 + 新增 WARNING 22:33:41; ASK2 暖池（3s 后）→ **3508.55 元** 命中 sample_jiaxing_minan score 0.7889, 无新 WARNING
- 反证排除: PG 池干净（无饱和）/ 集合键正确 / 嵌入确定性（暖池同问 0.7889 复现）

## 2 段 D 塌方分解（红旗 1）

三因子叠加, 非硬故障:

| 因子 | 证据 | 量级 |
|---|---|---|
| ① 流量构成: 今日=纯 canary（每日 eval 未跑, kiosk 已关）, 4 题中 3 题结构性超预算 | 今日 4 条完成全为 adv_ocr_meta（16:34/20:28 db 坐实, 00:21/02:03 特征同）; 早期段含 eval 16 题混合（单跳题 3 步可完成） | 完成率天花板 ≈ 1/4 题型 |
| ② step×时长错配: q06 类轨迹 6 步 152s（24s 首 prefill + 2 查 + 2 次冗余 get_source）≫ 45s 预算 | db 轨迹 dump: 22:08 q06 会话最终答对 3508.55 但耗时 152s; OCR 完成轨迹 3-4 步 ~30s | 结构性, 与 08-22 同（L2 p50=3 步未变） |
| ③ 红旗 2 乘数: 每周期首查必败 → agent 吃垃圾证据绕路 / 直连兜底答错 | 22:09 q06 agent 首查返回嘉合文档（兜底）, 二查（新连接）命中 minan; 完成仅发生在池暖时窗 | 把"偶可完成"压成"几乎不完成" |

**回答卡内问题**: 不是"step 增"（step 结构与基线期一致）, 是"检索命中降"但**仅限每周期首查**（死连接）, 叠加流量构成变化。次生发现: 超时不 abort——被弃 run 继续跑 4-26min（16:02 会话 msg=55/26min, 22:10 会话 20msg/10min）占 :8006 slot, 独立记账（与 FK 竞争同源的结构性问题）。

## 3 修复菜单（报用户拍板, 未批不动）

| # | 方案 | 改动 | 窗口 | 预期 |
|---|---|---|---|---|
| F1 | **pre_ping+recycle（根治）**: get_vector_store 自建 `create_engine(conn, pool_pre_ping=True, pool_recycle=300)` 传入 PGVector | vector_store.py ~10 行 | :5050 重启窗 + 侧车重启（MCP 重生） | 死连接检出即重建, 首查不再败; recycle 300<600 先于 GUC 回收 |
| F2 | **防御层**: smart_retrieve 区分"检索真空"与"检索异常"——连接类错误 dispose+重试一次, 再败记 ERROR 级并显式标注兜底（不把兜底冒充检索结果） | rag_service.py ~20 行 | 同 F1 窗 | 同类故障从"静默错答"变"响亮失败", 兜底答案带标记 |
| F3 | GUC 策略: 维持 10min 兜底（泄漏保险仍有价值）与 F1 并存; 不降不撤 | 0 | 无 | 双保险 |
| F4 | 僵尸 run（超时 abort）: 单独卡, 与 FK 竞争结构问题合并评估, 本轮不实施 | 大 | 另议 | 释放 :8006 slot, 降周期间干扰 |

推荐: F1+F2 同窗, F3 不动。修复后需**干净段**（含 eval 流量）重攒数据, 超时 (a) 判定用干净段拍。

## 4 对 checkpoint 判定的含义

段 D 数据被池 bug 污染（每周期首查必败）→ "<10% → (a) 再议"的触发**不能归因于超时太短**, 23:50 cron 数据照收, 判定挂起正确; 修复 F1/F2 后的干净段才是拍超时 (a) 的合法输入。

## 5 顺带记账

- 每日 eval 08-24 未执行（最后一次全 16 题 = 08-23 L1 矩阵腿）→ 恢复节奏待排（修复窗后）
- :5050 ERROR 清单（app.log, 全量 32 条, 口径差异: 用户侧 56 条未复现, 或为不同过滤/日志）: PGDATABASE_URL 未设 22 条（7-16~8-03 历史, 已治）/ 数据库连接 20s 失败 6 条（8-14 历史）/ 其余 4 条散发历史; **今日零 ERROR——今日故障全在 WARNING 级（216 条）, 是红旗 2 "无错误日志"的原因**
- FK 08:14 新增 1 条 = cleanup 水位闸 51>50 偶删在途（见 dispatch #HYG-FK-LEDGER, 下个代码窗修）
