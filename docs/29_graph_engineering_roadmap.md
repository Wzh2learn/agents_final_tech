# Graph Engineering 路线图（Q4: 只出菜单, 等拍板）

> 状态: 活跃（菜单待拍板, 未实施） | 更新: 2026-08-12 | 取代/被取代: 无
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
