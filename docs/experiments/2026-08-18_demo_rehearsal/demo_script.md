# 明日导师演示脚本（2026-08-19 白天）

更新: 2026-08-18 夜（T1 演示准备产出；彩排耗时表见 rehearsal_results.md）

## 0. 演示形态
- 通道: 本机 `powershell -NoProfile -File scripts/dev_remote_demo.ps1` → 浏览器
  http://localhost:5050/m1 → 屏幕共享给导师（SSH 本地转发, 无公网暴露）。
- 叙事主线: **快与准是菜单, 不是取舍**。直连路 ~2s/轮适合快速交互; 验证链路
  ~30-40s/轮, 答案经独立 agent 复核、溯源遵从度更高, 适合关键数字场景。
- 双链路执行方式: 演示分三段切换 M2_OPENCODE_ROUTE（off→on→off）, 每次切换
  = :5050 重启（实测 23-31s, 用话术填充）。切换命令见 §5。

## 1. 演示前检查清单（T-30min）
1. GB10 侧: `bash scripts/graph/status.sh` — 三方 HEAD / Loop B 最近 PASS / 端口快照。
2. `curl -s http://127.0.0.1:5050/api/health/full` → overall healthy, embeddings=137, provider=local。
3. 本机跑 dev_remote_demo.ps1 → 自动开 localhost:5050/m1（5050 被占自动切 15050, 看控制台）。
4. 确认起始 route 状态 = off（快路段需要）: `tr "\0" "\n" < /proc/$(pgrep -f "uvicorn.*5050" | head -1)/environ | grep M2_OPENCODE_ROUTE`。
5. 浏览器窗口置前台, 开屏幕共享。

## 2. 正片步骤（点击动作 / 看点话术 / 实测耗时）

### Phase A — route=off 快路段
| # | 动作 | 看点话术 | 预计耗时 |
|---|------|----------|----------|
| A1 | 打开 /m1, 点 `Sample` 按钮 (#sampleBtn) | "一屏三面板: 解析结果 / 表头信息 / 复核校验, 解析→映射→校验不跳页" | ~5-8s |
| A2 | 滚动到勾稽区 (#reconcileSection) 再回顶 | "勾稽校验如实标注, 未映射列透明可见" | 5s |
| A3 | 上传 WaveFax 传真 PDF (#fileInput, 文件: scenario1/attachments/转发 来自：(WaveFax Fax Device)_att0_20260506_132650IU.pdf) | 等待期讲: "扫描件走视觉模型看图识字, 全本地推理, 数据不出域; 这份传真一轮识别后有错认, 规则沉淀后命中率升到 100%" | 16-71s（OCR 实测区间） |
| A4 | 点建议映射按钮 (#suggBtn) 打开选择题面板 | "系统把不确定的字段映射做成选择题: 原列名/建议标准字段/置信度/理由, 甲方勾选即生效, 拒绝即不用; 最难样本华泰紫金 35.7%→100% 就是这个闭环复现的" | 面板 2s; 故事 60s |
| A5 | 快问 1: 复熙混合25号的资产总值是多少？ (#m2Question + #m2AskBtn) | "秒级出答, 数字带出处" | ~2s |
| A6 | 快问 2: 嘉兴民安的总资产是多少？ | "连续快问均秒级; 无出处的数字不显示" | ~2s |

### Phase B — 切换（话术填充 ~23-31s）
- 动作: 执行 §5 切换命令 route off→on, 等 health 恢复。
- 话术: "现在我切到验证链路——每个答案由一个独立 agent 复核检索证据后才给出,
  代价是每轮多等半分钟, 适合关键数字。切换本身 23 秒, 也是系统能力: 链路可秒级降级。"

### Phase C — route=on 验证链路段
| # | 动作 | 看点话术 | 预计耗时 |
|---|------|----------|----------|
| C1 | 关键数字题: 嘉兴民安的资金余额是多少？ | 等待期讲: "独立 agent 正在复核检索证据——它有自己的检索工具, 答案必须带出处; 快与准是菜单, 您按场景选" | 30-40s（彩排实测填这里） |
| C2 | 展开来源 (.m2-sources-toggle) | "样本/表名/字段/原文片段逐条可验" | 2s |
| C3 | 透明面板: 切 top_k (#m2TopK 3/5/8/10), 指 meta 行 | "检索条数用户可控; 每问标注走哪条路/检索几条/花了多久——系统不藏东西" | 5s（不再发新问, 看历史 meta） |

### Phase D — 切回 route=off（再次 §5, ~23-31s）→ 收尾快问
| # | 动作 | 看点话术 | 预计耗时 |
|---|------|----------|----------|
| D1 | 追问: 其中证券市值占多少？ | "多轮上下文自动关联上一轮实体, 不用重说主语" | ~2s |
| D2 | 拒答题: 星辰私募1号的资产总值是多少？ | "库里没有的数据明确说未找到, 不编造——这是给甲方的信任基础" | ~2s |
| D3 | 收尾 | "嘉合同版式 100% / 最难样本 35.7%→100% / 问答 16/16 带溯源; 下一步: 前端改版 + 验证链路延迟治理 + 跨期对比" | 60s |

## 3. 预案（演示中异常处置）
| 症状 | 处置 | 口径 |
|------|------|------|
| C1 agent 路 >60s 未出答或报错 | 立即 §5 切回 route=off, 后续全走直连, 口头讲"验证链路今天状态不佳, 菜单能力以录像/截图为准" | 双链路降级为纯直连, 不恋战 |
| 页面 502 / 打不开 | 本机 `ssh jinrong-dev "bash scripts/graph/status.sh"` 查 GB10 :5050 存活; 挂了就在 api5050 pane 重启 | 最多 30s 恢复 |
| 隧道断开 | 重跑 dev_remote_demo.ps1（自带残留清理） | 10s |
| 上传解析 >2min | 口头讲 OCR 预算政策, 刷新页面改演示嘉合电子件（毫秒级） | 不冷场 |
| 演示中 Loop B 报警 | 与演示无关, 演示后处理 | 不中断 |

## 4. GO/NO-GO 判定（今晚彩排产出）
- 判据: 彩排 agent 路关键数字题样本。≥2 次完成且均 ≤45s → **GO 双链路**;
  任一回落后无第二次成功, 或延迟 >60s → **NO-GO: 全程 route=off 纯直连**,
  验证链路口头讲 + 用 docs/31 截图/视频 v2 佐证。
- 判定结果填 rehearsal_results.md, 演示前不再改配置（冻结窗）。

## 5. route 切换命令（api5050 pane）
```bash
# Ctrl-C 停当前进程后:
cd /home/testuser/wzh/projects/agents_final_tech && \
PYTHONPATH=$PWD/src M2_OPENCODE_ROUTE=<on|off> OPENCODE_ASK_TIMEOUT=45 \
./venv/bin/python ./venv/bin/uvicorn main:app --host 0.0.0.0 --port 5050 --workers 2
# 验证: health 200 + /proc/<pid>/environ 的 M2_OPENCODE_ROUTE 值
```

## 6. 演示后
- route 恢复 on（生产态）+ health 验证 + B4 日志标注演示流量。
- 冻结窗解除, 积压的代码变更/审计修复按队列恢复。
