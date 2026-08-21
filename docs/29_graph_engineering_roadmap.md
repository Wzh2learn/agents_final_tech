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
