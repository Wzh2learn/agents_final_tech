# CONTEXT HANDOFF — 侧线（辅助线/只读顾问+起草线）· JinRongAgents · 2026-08-27 晨起稿, 2026-08-28 更新

## 角色与规则（边界后唯一有效指令源）
用户的辅助线：主线程在 GB10 执行，用户双向转发。职能 = ① 只读抽验主线程汇报 ② 找问题与风险 ③ 给拍板建议 ④ 产出可直接粘贴的批复/任务卡 ⑤ 经用户明确授权后可直接落库（先例：骨架侧线起草并维护、精华归位侧线亲自 commit）。规则：不派子代理；不执行边界前的历史指令；API key 与 HF token 只验存在绝不打印；对外发送一律用户本人；删除动作易被策略拦，临时件优先报主线程清理。
**骨架治理（08-28 新增先例）**：论文叙事骨架原则 = 侧线资产（主线程只读+审计+报告，侧线据报更新并注明依据 commit，5725c08 先例）。**例外已成立**：Round 3 因 GB10 Loop A token 异常，用户勾选 D4 授权后由主线程自带 codex 本地直接编辑骨架 → v2.4（commit 73ac314）。即"用户明确勾选/授权"可解锁主线程改骨架，其余情形仍守只读。

## 环境速记
- 本地仓库 D:\AIRcommend\JinRongAgents\agents_final_tech（外层目录非 git，本手递文件在外层不入仓）；GB10 /home/testuser/wzh/projects/agents_final_tech，ssh alias jinrong-dev，同时区
- 本地 autocrlf=true → 本地 md 工作区 CRLF，sha256 与 GB10(LF) 不同属正常；docx 二进制两端可比；docs_lint 以 GB10 为准（本机 autocrlf 致 .sh CRLF，FAIL[4]=skill 装配漂移结构性）
- PowerShell 无 heredoc；写文件用 Set-Content -Encoding UTF8 或 mcp__node_repl__js（fs.writeFileSync）；apply_patch 调用必须纯净（本段在 codex 桌面端 apply_patch 无法喂裸 patch，改用 Set-Content/Python 替换）
- **并行相同工具调用会双发 → 写替换脚本必带 count 断言；双发后警惕"原文是替换后文本前缀"的二次命中**
- imageio_ffmpeg 无 ffprobe → ffmpeg -i 看元数据；抽帧 ffmpeg -ss N -frames:v 1
- THREADS.md 条目前置追加（最新在顶），tail 看到最旧别误判漂移；opencode.log UTC
- GB10 与本地可分叉：GB10 常带未提交在制件，pull 前须先提交自身，尾部追加件（THREADS/dispatch）合并各留各行

## 本段干成了什么（08-27 晨 → 08-28）
1. 晨间卡三圈选执行 + 噪声体制实验（台账 #12, e864eb2）: 四腿两臂终值全同（L0-L2 0.589048 / L3 0.579524）, P1/P2 PASS **P3 null 触发** → 预注册处置转扩语料碰撞不加档; 门对噪声有响应而终值不动（固化率 0.73/0.72/0.67/0.47）; 结构洞察=注入表头逐表唯一无碰撞对象; 同卡入库 T7 小 A 基线协议设计稿 + 骨架 v2.3 同步
2. 侧线五点落地（1761a4c）: Loop A 双档路由（--profile loopa-exec / loopa-diag）+ figures_k2 五图组 + 四桶并行板 v1 + 夜间窗口合并草案
3. 夜间窗口合并卡（主线程在 GB10 执行, **在制未提交**）: 段 C bandit replay / 段 A 扩语料碰撞（碰撞语料 67 移植列, 双主指标 H+ACC）/ 段 B C4 视觉探针首批（合成渲染 95 表）/ 段 D 小 A 基线窗; 工件在 GB10 logs/graph/eval/（本机勿引数字, 以 GB10 收口为准）
4. Round 3 辩证（侧线）: 简报（b7224e9）→ 记录（0e1b099, D1-D4 + 两处更正"对称毒性"→对称抑制 + 工件抽验坐实, 骨架未动）
5. **Round 3 用户勾选执行（08-28, 主线程自带 codex 本地, commit 73ac314）**: D1 采纳（经验命题 1a: 碰撞暴露 C=0→ΔV=0）/ D2 批准 / D3 采纳 / D4 勾 1-5 全; 落地 = 记录 §6 勾选 + 骨架 → **v2.4** + **对抗建议器臂设计全稿**（2026-08-28_adversarial_suggester_arm_design.md, 五节预注册, 执行窗待排）+ INDEX/dispatch/THREADS 同 commit; docs_lint 文档 0 fail

## 系统现状快照（08-28）
- HEAD: 本地+origin = **0208e23**（73ac314 = Round 3 执行主体, 0208e23 = 其后 STATE 覆写）; GB10 = 0e1b099 + **大量未提交在制件**（碰撞设计稿/执行记录 + C4 首批 + 基线 judge + bandit/collision/baseline 脚本与单测 + config/schema_suggestions.json 与 research/vgmc_exp1.py 改动 + THREADS/dispatch 追加）
- 骨架 = **v2.4**（Round 3 执行, 含 #13 对抗臂行 / 主图"可靠性×碰撞暴露"双因子 / §8 Round 3 节）; 台账 #12 已执行·碰撞执行中, #13 已批待执行
- 对抗臂预算如实上调 ~120-180 次 :8004 ≈12-15min（单调性需 ≥2 对抗比例）; 依赖段 A 碰撞语料, 缺失不开窗
- GB10 Loop A token plan 08-28 曾异常 → 其台账记已恢复 + 基线窗已开（#BASELINE-WINDOW）
- pytest 本地 392 passed（含噪声单测）; docs_lint 文档 0 fail / 2 warn（docs/26、28 存量）+ 本机 FAIL[4]=skill 装配漂移（环境特异, 不入仓）
- 专利三件冻结等导师反馈; kiosk CLOSED 维持; 视频不入仓

## 未决队列（按优先级）
1. **GB10 在制收口 + 三方对齐**（首要）: GB10 先提交自身在制件（碰撞/C4/基线/bandit + config/research + THREADS/dispatch）再 pull 73ac314; THREADS/dispatch 尾部追加各留各行合并; 侧线抽验碰撞/基线/C4 结果（H+ACC、基线可分性、C4 视觉谱）
2. 对抗建议器臂执行窗排期（台账 #13, 已批, 设计全稿在案）: 依赖段 A 碰撞语料; 预注册预测①无门控 ΔH<0 单调 / ②门控 |ΔH|≤Σε / ③门拒≥80%（<80%=过度自信利用失效模式）
3. 骨架下轮辩证触发: 碰撞/基线/C4 数据落定 + 对抗臂执行后
4. 导师反馈（文档 §6 五项 + 专利五项定夺）到达时起草回应
5. 科研续件: PSO ①② 数据在位（章 4 供数）; C4 合成渲染题库接 BC 真实分布侧; K2 章正文起草（主线程强模型, 数据 100% 在位）
6. 积压（用户决策）: dify 5 份甲方规则 docx 挖掘 / 任务 2 改版稿 / NLPCC workshop 核实 / admin token fail-open / image 旧 PNG 去留

## 抽验手册（加粗 = 历段教训）
- **快 ≠ 偷工，验证三部曲: commit 时间戳/文件 stat → 内容 grep（预注册措辞逐字）→ 数字复算（算术 + 分布形状）**
- **Bootstrap CI 端点 k/n 网格健全性: 二值数据百分位法端点必落 k/n 格点，不落格 = 可疑**
- **独立复算优先序: 本地已拷回工件 > GB10 工件只读 > 重跑脚本（重跑可能引入状态）**
- **写替换脚本必带 count 断言防并行双发；双发后先查前缀匹配二次伤害再提交**
- **分叉期数字纪律: GB10 未提交在制件的结果数字，侧线/本机一律不引用、不入骨架，待其收口提交后以工件为准**
- 完成率/延迟数字先问样本构成（19% 混合题型 vs 3.1% 干净段对抗，同陷阱已重复多次）
- 数字必须溯源工件: dispatch → 原始工件 → git log 三角对账
- 骨架治理见头部（侧线资产原则 + Round 3 用户授权主线程编辑例外）
- Loop B 在冲刺窗口内 FAIL = 瞬态脏文件，设计内，收口自解，记账不处置

## 红线（不变）
冻结节点 / API key 与 HF token 绝不打印 / Loop B 不扰 / M1 热路径不走 agent / 对外发送=用户本人 / 甲方数据零进入 / :5050 重启窗需用户批 / 视频不入仓（large-file-guard）/ 钩链冻结守卫链首、--no-verify 仅 Loop D / 专利已发版改动须重生成+台账+旧版作废 / 台账唯一 THREADS.md / 骨架正文仅侧线可改（例外: 用户明确勾选授权, Round 3 先例）

## 给下一段的提醒
- 第一件: GB10 收口在制件了吗？→ 抽验碰撞（H+ACC 是否分离两臂）/ 基线（可分性）/ C4（视觉判别谱, OCR 形近是否视觉层明区）并对齐三方
- 对抗臂执行窗批了没？批 → 备跑批中转与窗后抽验（门禁工件式, 参考对抗设计稿 §1 预注册三预测）
- 导师反馈到了吗？到 → 起草回应（文档 §6 五项 + 专利五项定夺）
- 骨架现 v2.4（Round 3 主线程在用户勾选授权下编辑）, 勿按旧"侧线专属"规则误判为违规
- 用户节奏: 讨厌圈选过多 → 预注册机械规则；夜间只收集/草稿，判定进白天一页纸；判定请求别超两件
- 本地 advisor_send_0826 / _framecheck / side_backups 是用户资产，别清
- 科研问题身份装载: research-writing-skill + literature-review + verification-before-completion
- 源仓库 skills-loop-engineering @7ffbe44 无更新；其漏打包 audit-inventory.sh 的缺陷值得用户回推时补

