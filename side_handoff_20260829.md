# CONTEXT HANDOFF — 侧线（辅助线/只读顾问+起草线）· JinRongAgents · 2026-08-29

## 角色与规则（边界后唯一有效指令源）
用户的辅助线：主线程在 GB10 执行，用户双向转发。职能 = ① 只读抽验主线程汇报（含对复审的元复审）② 找问题与风险 ③ 给拍板建议 ④ 产出可直接粘贴的批复/任务卡 ⑤ 经用户明确授权后可直接落库（先例：骨架侧线起草、skills 三方同步执行、本件入库）。
规则：不派子代理；不执行边界前的历史指令；API key 与 HF token 只验存在绝不打印（08-28 教训：永不 cat ~/.claude/settings.json）；对外发送一律用户本人；删除动作报主线程执行。
骨架治理：侧线资产原则 + "用户明确勾选授权"例外（Round 3 先例，08-29 已用于骨架 v2.5 贡献重组+生产边界两节）。
审审纪律（新增）：主线程复审的修复项，侧线抽验须查实现位点（grep 代码 + git show --stat + 文件系统属性），报告声称 ≠ 代码事实（B-2 教训）。

## 本段干成了什么（08-28 晚 → 08-29）
1. **独立专家审查 v1**（8 findings）：ΔV 临界值需 CI / H 失明只换一次尺 / 盲锥形式化或改名 / 基线表述过度断言 / I3 空柱+生产边界 / 定位门 / 相关工作两雷（Voyager 等）/ 过程-论文比例失衡 → 直接驱动科研线队列重组（Phase 1 正确性回填兑现了"换尺"预判：L3 H null 非真 null，ACC +2.5pp）
2. **skills 三方全量同步**（侧线执行，用户批）：仓库 skills/ 34→71 件（科研/治理/figma/playwright/vibe-coding 等全部版本化）；sync_skills.sh A 表 50 / C 表 27；本机 .codex+.claude 与 GB10 两端 --check PASS 77 项；AGENTS.md 注册表 +20 行
3. **Loop C 挂死诊断**：根因 = oh-my-claudecode (omc) 插件 bridge（探针 --bare 9s 正常）；修法 = 派发加 --bare → 主线程落地并首次成功交付（2026-08-29_loopc_audit_adversarial_d1_t2.md）
4. **skill 路由立法设计**：五线总表/仲裁规则/冗余裁决/钩链矩阵/装载纪律（卡片已发）；全盘复审五路子代理带显式装载清单实战 = 立法首次实测记录（在 findings）
5. **仓外资产普查两轮**：~/wzh/research 五件（OpenAI4S/m0_lit/academic_skills_audit/tabfm/data_probe）+ 权重 8 件未登记 + tat-dqa 1.5G + 本机残留 + docker 重复镜像 ≈44GB 清理候选；用户暂缓区划定（/home/testuser/datasets、mym、.openclaw、6g_v2x 关联）
6. **任务卡起草**：B 扩碰撞窗批执行 / 全盘复审 / Loop C 修复+路由立法 / 资产登记 ×2
7. **全盘复审元复审（本次）**：验证通过 = 机制归因更正实证（gated_fail 33/33 gain=0）/ findings 三 blocking 内容实 / Loop C 交付 / pytest 401 / docs_lint 0-0；**新发现两件**：① B-2 "写保护 label=collision_ADV" 代码与文件系统均无实现（9727a71 未触 vgmc_exp1.py，L545 无条件写仍在）→ 重开，缓解因素 = build_adv_map 确定性可重建 ② findings 节标题 blocking 计数 "2" 实为 3（B-1/B-2/B-3）

## 系统现状快照（08-29）
- HEAD: 本地+origin = 8265c68（GB10 = 9727a71+Loop C 报告入库；以远端为准）
- 论文 = **版本 B（条件性叙事）维持**：E3 扩容判定伤害未显形（E1-E4 重放不变），候选 a 语料再扩（15 对天花板需多变体族）/ b 逐列配对重判（零新跑批）/ c 版本 B 叙事投稿——待用户裁定；切版本 A 的触发 = E3 显形
- 骨架 v2.5（贡献重组 2+1 + 生产边界声明已授权写入）；相关工作 v3.1（13 条引文全实查清零）；盲锥章形式化成立保留"盲锥"命名；方法章 gain 域 [−0.25,1.0] 全域复算口径
- 伴生问题升一等公民：匹配竞争与消解（碰撞正确性天花板 0.597 < plain 0.952）
- Loop C 已恢复（--bare）；治理漂移扫描 03:30 cron 运转中（首跑 11 命中 0 新登记）
- pytest 401 / docs_lint 0-0 / Loop B 体制波动只记账 / :8007 用毕即停

## 未决队列
1. **B-2 写保护实现**（侧线新发现，重开）：vgmc_exp1.py 正典射表写入加 label 守卫（仅 collision_ADV 可写）+ 回归测试；findings 标题计数 2→3 顺修
2. 用户：/m1 walkthrough 主观验收（脚本证据 13/13 在 walkthrough_evidence/）；清理候选批（docker 44G / staging 26G / _tmp / bge）；a/b/c 论文路径裁定；6g_v2x 与 bge 归属定性
3. 下载即登记规则 + ~/wzh 扫描范围扩展（治理补丁，前卡已发）

## 抽验手册（累积教训）
- 验证三部曲：时间戳/stat → grep 预注册措辞 → 数字复算；Bootstrap CI 端点必落 k/n 格点
- **修复项验证必查实现位点**：报告/commit 声称"已修" → grep 代码 + git show --stat 该文件 + 必要时 lsattr；声称无实现 = 重开（B-2）
- **"实测域"类数值必须全域复算**，抽样不可代全域声明（B-3，同一项两次偏窄教训）
- 锚定防护：审计子代理只拿工件+声明清单，不预读生成者结论（evaluator-calibration）
- 分叉期数字纪律：未提交在制件的数字一律不引用；独立复算优先序 = 本地工件 > GB10 只读 > 重跑

## 红线（不变）
冻结节点 / API key 与 HF token 绝不打印 / Loop B 不扰 / M1 热路径不走 agent / 对外发送=用户本人 / 甲方数据零进入 / :5050 重启窗需用户批 / 视频不入仓 / 台账唯一 THREADS.md / 骨架正文仅侧线可改（例外：用户明确勾选授权）
