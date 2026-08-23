# Graph Engineering 路线图（Q4: 只出菜单, 等拍板）

> 状态: 活跃（L1 已补全 08-22 / L2 已落地 templates/ / L3 只列清单未实施） | 更新: 2026-08-22 | 取代/被取代: 无
> 复盘范围: 近两周 dispatch_log (197 条) / blocked_questions / 08-11 延迟事故 / 08-12 辅助线核验

## 一、人肉环节盘点（现状）

| 环节 | 现状 | 事故/代价实例 |
|---|---|---|
| 分发 | 手写: tmux send-keys / claude -p 长字符串现场拼 | 权限门卡死 (忘 --dangerously-skip-permissions, 08-12 T2 教训); 长 prompt 手拼易漏红线 |
| 验收 | 手跑: 每任务验收命令由分发者临场执行 | 延迟事故: route=on 名义开启, 实际 18s 超时全回落直连——验收标准里没有"agent 路延迟分布"一项, 靠用户辅助线人工量出 |
| 漂移发现 | 人发现: 用户/辅助线比对文档与实况 | 08-11 known_gap 陈旧台账 (三项已解决 gap 仍标挂起); 08-12 docs/23 声明复测发现默认路延迟漂移 |
| 核验 snippet | ad hoc: 三方 HEAD / pane grep / /proc environ 每次重写 | 辅助线核验每次手搓 ssh+base64 snippet, 无沉淀 (Q1 已把部分固化进 status.sh 提案) |
| 健康视图 | loop_d_monitor.sh 陈旧 (查 :5000 旧端口, 缺 :4096/:8100, 无三方对齐) | 无人用; 真实状态靠临时 curl |
| 回归 eval | 记得才跑 (run_eval.sh 无定期挂载) | 16/16 基线只在专项时跑, 平时无哨兵 |

## 二、分级菜单

### L1（0.5d）scripts/graph/status.sh 一页健康 ★★★ 推荐先做
把辅助线 ad hoc 核验固化为一条命令 (`ssh jinrong-dev "bash .../status.sh"`)：
- 三方对齐: GB10 HEAD + GitHub origin (git ls-remote) + 上次 push 时间（本机侧给一行自查命令）
- Loop B 上次 PASS 时间 (verify-report.json + watchdog log 尾行)
- 端口快照: :5050/:4096/:8004/:8005/:8100/:15432 (含禁杀 tmux 会话标注)
- 距上次 dispatch_log 条目时长 + 最后一条 tag
- 冻结节点 md5 复算 vs frozen_hashes.txt
- docs_lint + sync_skills --check 一键联动 (Q3 资产)
**工作量**: 0.5d | **风险**: 只读, 无 | **收益**: 核验从 10 分钟手搓 → 3 秒; loop_d_monitor.sh 退役 (git mv archive)

### L2（1d）任务卡 + 验收清单模板 ★★ 推荐高风险任务先用
`templates/task_card.md` (YAML frontmatter 机器可读):
```yaml
id: T-YYYYMMDD-n
loop: A|C
model: flash|max
risk: low|mid|high        # high = 重启/灰度/schema 写/冻结节点邻近
acceptance:               # 分发前写死, 验收时逐条执行
  - cmd: "curl .../api/health/full"
    expect: "embeddings=137"
rollback: "两行 sed 回滚命令 (如模型切换类)"
redlines: [冻结节点, API key, ...]
```
**工作量**: 1d (模板 + 2 个历史任务回填示范) | **风险**: 每任务 +5min 开销 | **收益**: 验收标准前置, 杜绝"route=on 名义开实际全回落"类事故; 为 L3 铺机器可读基础

### L3（远期）A→B→C 自动分发编排 ★ 暂缓, 列前提不实施
前提条件 (全部满足再议):
1. L1 status.sh 成为唯一健康事实源且稳定 2 周
2. 任务卡 YAML 化 (L2) 且 Loop B 验证项可从 acceptance 字段自动生成
3. Loop C dispatch 模板固化 (claude -p + 权限参数 + 报告路径约定, 本轮 T3 已跑顺)
4. 成本护栏: flash reasoning token 估算入任务卡预算字段
5. 回滚判据可执行化: 任务卡 rollback 字段可由编排器直接执行
6. 人在环保留: 高风险 (risk=high) 任务永远等人确认, 编排器只备料
**不实施理由**: 当前瓶颈仍是模型能力与甲方反馈节奏, 不是分发吞吐; 自动化编排在分发量 <5 次/天时 ROI 为负。

## 三、推荐执行顺序
1. **L1 status.sh**（发送后第一个窗口, 0.5d）
2. L2 模板先在下一个 risk=high 任务 (延迟 a+b 重启窗口) 试用
3. L3 暂缓实施, 每两周 neat 时重评前提条件

## 附录: A→B→C 自动分发前置清单（2026-08-22 T4, 只列不实施）

> 背景: §2 L3 暂缓; 本附录把每个前提落成"现状 → 差距"条目, 供重评使用。**只列不实施**, 不改任何分发默认行为。

| # | 前提项 | 现状（2026-08-22） | 落地差距 |
|---|---|---|---|
| 1 | 任务卡机可读化 | templates/task_card_template.md 已带 YAML frontmatter（08-22 T2）, 但无解析器; acceptance 命令人读人跑 | ① frontmatter schema 校验脚本（id/loop/model/risk/acceptance/rollback/redlines 字段）; ② 任务卡存放与命名约定; ③ acceptance cmds 必须一次性可执行（无交互/无 sudo）, expect 可机器判定（grep/regex/JSON 字段断言） |
| 2 | 验收项可自动执行 | templates/acceptance_checklist_template.md 三列表（声明→验证命令→实测值）, 人工执行 | 验收 runner: 读任务卡 acceptance → 逐条执行 → 输出 PASS/FAIL JSON; 范例已二（c9b2b07 B4 口径修复 / f8898c9 Phase 0 回滚） |
| 3 | 回滚点机可读 | 任务卡 rollback 字段为自由文本; B4/DSpark 窗口实践 = docker inspect 存档配对 + rollback_launch.sh | ① rollback 字段格式约定（一次性可执行命令）; ② 存档路径约定 logs/graph/inspect_<taskid>_{before,after}.json; ③ 回滚前置校验（存档存在性检查） |
| 4 | 失败升级路径 | 全人工: 失败 → 对话汇报 → 用户拍板 | 升级分级: L0 自动重试（幂等操作）/ L1 自动回滚（执行 rollback 字段 + 记台账）/ L2 停手 + dispatch_log + 等用户; 任务卡中止条件机可读; Loop B ALARM 已是机器信号（08-22 watchdog 设计内先例）, 可作升级触发源 |
| 5 | 健康事实源（L1 稳定） | status.sh 08-22 补全（端口 +8006/8007/8008、Loop B log 最近 PASS、B4 两列口径）, 输出为人读文本 | ① 稳定运行 2 周积累记录; ② 加 --json 输出模式供编排器消费; verify-report.json（Loop B）已是 JSON 可直接用 |
| 6 | Loop C dispatch 模板固化 | claude -p + 权限参数 + 报告路径约定已跑顺（08-12）, 但长字符串每次现场手拼 | dispatch 模板文件化（任务卡 → claude -p 命令生成器）, 与任务卡 id 关联 |
| 7 | 成本护栏 | 未实现 | 任务卡加 budget 字段（flash reasoning token 估算）; 当前 flash/max 选型靠人判断 |
| 8 | 人在环保留 | 设计原则, 无需实现 | risk=high 永远人确认, 编排器只备料——此项为约束不是待办 |

落地顺序建议（L3 重评时）: 1 schema 校验 → 2 验收 runner → 3 存档约定 → 5 --json → 6 dispatch 模板 → 4 升级路径 → 7 成本护栏。每步 flag 增量, 不改分发默认行为; 与 §2 L3 "不实施理由"（分发量 <5 次/天 ROI 为负）一并重评。


## 附录: Backlog 台账（2026-08-23 首版, TODO 梳理专项产出）

> 规则: **新发现/挂账条目即时登记入本表**, 不再散落。每行: 发现点 / 现状 / 阻塞 / 下一步 / 承接层（A 执行 / B 验证 / C 审计 / D 用户决策）。
> CLOSED 条目不入表（历史见 THREADS/dispatch）; 触发条件达成时重新入表。

### 一、用户决策类（D）

| # | 条目 | 发现点 | 现状 | 阻塞 | 下一步 | 承接层 |
|---|---|---|---|---|---|---|
| D1 | 任务2 M1/M2 页面改版设计稿拍板 (A 三栏工作台 / B 流水线画布) | THREADS 08-11 (docs/27) | 设计稿+草图就位, 未动代码, 挂账 12 天 | 等用户圈选 | 圈选后排执行窗 | D |
| D2 | 专利五项定夺（权利要求范围/发明人排序等） | THREADS 08-22 专利台账 | 三件套已发导师 08-22 晚 (三 hash 在案) | 等导师反馈 | 反馈到后按意见修订 | D |
| D3 | image/.env 旧 PNG 去留 (7 张 2026-02 Dify 原型截图) | THREADS 08-12 仓库精简 | 本机 gitignored 残留, 零引用待验 | 等用户圈选 | 圈选后执行 (删前验引用) | D |
| D4 | NLPCC 2026 workshop 窗口核实 | THREADS 08-19 批复⑥ | 主节点已定 NLPCC/CCIR 2027; workshop 待核实 | 用户人工核实中 (agent 尝试被 DNS/502/JS 挡) | 核实回话更新台账; 8 月底无回话默认按 NLPCC 2027 节奏 | D |
| D5 | admin token fail-open 收口 (M1_ADMIN_TOKEN/M1_API_TOKEN 未设) | THREADS 部署加固 + 08-05 启动告警 | fail-open 运行中 (m1.py:201/middleware.py:48) | 需 :5050 窗 + 决策 | 备忘录 D5 圈选后执行 | D |
| D6 | 超时 (a) 45→60-75s | THREADS N3 缓办 08-22 | L1 矩阵数据就位 (抬 60-75 容纳不了 xhigh p95) | 等 08-24 23:50 48h checkpoint 数据 | 按预写判据拍板 (段 C+D 完成率 <10% → 再议) | D (数据 A 出) |
| D7 | L2 sidecar 瘦身方案菜单批 | THREADS 08-22 L2 测量 | 测量定论 (prefill 主导), 菜单待批 | 等用户圈方案 | 圈选后 opencode.json 变更窗 | D |
| D8 | warm-up 候选 a (sidecar 重启预热消 37s 冷启) | THREADS 08-11 修复菜单 | 留候选, 冷路 45s 预付 | 等用户批 | 可随下次侧车重启附带 | D |
| D9 | schema 口径同步 (运行时副本 vs config 版 + frozen_hashes manifest 刷新) | THREADS 08-09 P1 | resolve_schema_path 已统一走 config | 需 Loop D 决策 | 决策后 A 刷 manifest | D |
| D10 | M4 减 step A/B 拍板 | 08-22 减 step 菜单 + 08-23 方案预备 | 方案就位 (侧车/prompt 层) | 等窗口后排 | 拍板后 A/B 执行 | D |

### 二、等窗/排期类（A 执行, 窗/触发由 D 给）

| # | 条目 | 发现点 | 现状 | 阻塞 | 下一步 | 承接层 |
|---|---|---|---|---|---|---|
| A1 | PSO 落点② / K3 注入批跑 二选一 | THREADS 08-23 夜核 | 前置 PASS (v1 + evidence card 齐) | 等 08-24 23:50 收口后错峰窗 | 预算门复查 + 执行 | A |
| A2 | K4 小模型矩阵 C3 (4B 级) / C4 | docs/33 §8 | C1/C2 NO-GO 完成 | 错峰排期 | 预算门先行, :8007 探针 | A |
| A3 | 每步输出 (adapter step 事件流开发) | THREADS N3 缓办 08-22 | 开发任务未动 | 等下个代码窗 | 兼作导师演示叙事素材 | A |
| A4 | Route S 对照臂 serving (SGLang+NVFP4+RadixArk) | blocked_questions 08-19 | 权重下载完成 | 需 :8006 停机窗 (缓, 与未来操作合并) | 给窗后起服补对照报告 | A+D |
| A5 | L3 DFlash2 :8007 探针 | THREADS 08-22 N2 | #52816 已合入上游 + 权重在位; 我们镜像 08-15 早于合入 | 等 timothystewart6 新 tag (08-29 checkpoint) | tag 到 → 探针 (L1 基线已满足前置) | A |
| A6 | drafter v2 / DSpark 再议 | drafter ledger 08-22 | 生产退出, 权重留盘 | 触发: drafter v2 发布或 medium 矩阵再议 | 盯梢命令自动 (ledger 现状) | A (自动) |
| A7 | vLLM 版本升级评估 (#46932/#49760/#48140) | 08-21 窗口批复 | 长期台账, 版本未动 | 无 | 择评估窗; 新 tag 与 L3 联动 | A+D |
| A8 | HTML 邮件提取步脚本入库 (.msg→HTML→表格) | THREADS 08-09 P1 | 匹配步已复活, 提取步仅存产物 | 无 | 与 4.1 一并入库 | A |
| A9 | evidence card UI 展示层 | 批复 08-19 ⑤ | 脚本随 v1 交付 | 演示冻结窗不碰前端 | 另行排期 | A |
| A10 | ZhikunCode 重建 (pip 直连 pypi 慢 → aliyun 源/上游 PR) | THREADS 08-03 | 低优先 | 无 | 顺手时做 | A |
| A11 | Qoder CLI Phase 2 连通性实测 | THREADS 07-29 | BLOCKED-auth | 等用户注册提供 PAT | PAT 到后实测 | D→A |

### 三、甲方侧（D 对外）

| # | 条目 | 发现点 | 现状 | 阻塞 | 下一步 | 承接层 |
|---|---|---|---|---|---|---|
| C1 | 跨期对比多期数据 | THREADS 甲方待确认 | 阻塞 (仅单期) | 等甲方提供 | 数据到 → 入回归基线 | D (甲方) |
| C2 | M2 正式业务指标 (label-to-source 映射 + 人工标注) | THREADS 甲方待确认 | 阻塞 | 等甲方批准 | 架构边界, 不越界 | D (甲方) |
| C3 | 部署加固 (systemd/Prometheus/token) | THREADS 甲方待确认 | 等甲方运维确认 | 甲方 | token 部分可先行 (见备忘录 D5) | D (甲方) |
| C4 | 场景 B 问答候选选择题 | THREADS 08-10 | 设计入库 (docs/26 §三) | 触发: 甲方 walkthrough 认可场景 A 面板 | 触发后排期 (直连路 ~2h) | D (触发) |
| C5 | dify 5 份甲方规则 docx 深挖 | THREADS 08-12 | 确定性挖掘已做 (delta=0, 3 synonyms) | 触发: 甲方提供估值表类样本 | 见备忘录 D2 | D (触发) |

### 四、观察/监控类（B 验证）

| # | 条目 | 发现点 | 现状 | 阻塞 | 下一步 | 承接层 |
|---|---|---|---|---|---|---|
| B1 | FK 菜单 a 修复后观察 | 08-23 窗口 | 三表持久化恢复 (0→9/44/118), FK 停涨 136 | 无 | 08-24 收口看积压; 异常才上菜单 b | B |
| B2 | PG 池修复后观察 (实例缓存 + GUC 10min) | 08-23 窗口 | 泄漏根治 (菜单 a), GUC 兜底 | 无 | 收口顺带 pg_stat_activity 抽样 | B |
| B3 | B4 48h 观察 (段起点 3429; 段 B 11:45-20:20 PG 污染降权) | 批复卡 08-22 | 进行中 | 无 | 08-24 晚 23:50 cron 按预写口径判定 | B |
| B4 | 常驻资产纳管规则执行 | kiosk 教训 08-22 | 规则入账 (runner 入库 + Loop B 断言) | 无 | 未来常驻资产逐个对照 | 治理 |
