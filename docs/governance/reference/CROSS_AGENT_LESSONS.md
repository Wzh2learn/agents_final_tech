# 跨Agent经验沉淀

> 用途：记录各Agent在执行过程中发现的可复用经验、踩坑教训、优化建议
> 规则：任何Agent发现"另一个Agent可能也会遇到"的问题，主动记录于此
> 参考：AGENT_COLLABORATION_PROTOCOL_v1.0.md §1.4

## 格式

每条经验按以下格式记录：

### YYYY-MM-DD | {发现Agent} | {经验标题}

- **场景**：什么情况下遇到的
- **教训/发现**：核心结论
- **建议**：其他Agent可以怎么做
- **相关文件**：（可选）

---

## 经验记录

### 2026-06-26 | Commander Agent | 三入口文件零重叠验证

- **场景**：建立协同机制时，初版规则假设 README/CLAUDE.md/MEMORY_INDEX.md 职责重叠需要重构
- **教训/发现**：经调研验证，三份文件实际零重叠，形成"宽→窄→深"递进式导航设计（README=新人入口，CLAUDE.md=Agent快速定向，MEMORY_INDEX=深度查阅）。假设性判断需要先验证再行动。
- **建议**：修改入口文件前，先用 grep/对比确认是否真的重复，不要基于直觉重构
- **相关文件**：README.md, CLAUDE.md, MEMORY_INDEX.md

---

### 2026-06-26 | Commander Agent | handoff skill 临时产出 vs SESSION_HANDOFF 持久状态

- **场景**：多 Agent 接力时，handoff skill 产出的 compact 文档放在临时目录，但关键状态信息未回流到持久 SESSION_HANDOFF
- **教训/发现**：handoff skill = 临时对话压缩（用完即弃）；SESSION_HANDOFF.md = 项目持久状态（永不归档）。两者是不同层级，但关键信息必须从临时层回流到持久层，否则跨会话信息散失。
- **建议**：每次 handoff skill 执行后，检查产出中是否有"下周另一个agent接手时需要知道"的信息，有则同步到对应 SESSION_HANDOFF_*.md
- **相关文件**：session/AGENT_COLLABORATION_PROTOCOL_v1.0.md §0.7

---

### 2026-06-26 | Code Agent | remote-server torch 2.2 + AMP 必 NaN

- **场景**：v2 模型在 remote-server 上跑 FP32 正常，开 AMP（混合精度）后 P2 实验 100% NaN
- **教训/发现**：remote-server 的 torch 2.2 对 AMP 的某条路径不稳，与 Local Agent 已固定为 FP32 训练，避免重复踩坑。
- **建议**：remote-server 实验脚本默认 `--fp32`，禁用 AMP；local machine MPS 可用 FP16 节省显存但仅限预筛。新数据集首跑必先冒烟 FP32 通过再考虑降精度。
- **相关文件**：session/SESSION_HANDOFF_CodeAgent.md §七

---

### 2026-06-26 | Code Agent | torch.compile 与 num_workers>0 互斥

- **场景**：v2 训练 DataLoader 设 num_workers>0 时，torch.compile 触发 fork segfault
- **教训/发现**：torch.compile graph capture incompatible with DataLoader subprocess fork，remote-server/local machine 均复现。当前实现：检测到 num_workers>0 时自动跳过 torch.compile。
- **建议**：性能优化时不要同时开 torch.compile + num_workers>0；若必须 compile，用 num_workers=0 + prefetch_factor 调优。
- **相关文件**：session/SESSION_HANDOFF_CodeAgent.md §七

---

### 2026-06-26 | Writing Agent | MARS 六操作译名是忠实翻译不是术语替换

- **场景**：the paper §X 引用 MARS 六操作（extraction/reinforcement/weakening/consolidation/forgetting/resynthesis）时，写作 Agent 用了中文直译（提取/强化/削弱/巩固/遗忘/重新合成），被误认为是替换为 project-specific-terms 术语
- **教训/发现**：忠实翻译 ≠ 术语替换。project terminology (e.g., Write/Read/Update/Govern)是 the paper.s own abstraction，MARS 六操作是 MARS 原文具体机制，两者层级不同不能混用。译名要保留"对方原文"标识，避免读者误以为 MARS 用了 project-specific-terms。
- **建议**：引用竞品机制时，译名后必须标注 `[MARS 原文, ref]`；自创术语（project-specific-terms/ProjectModule1/ProjectModule2 等）单独成段，不与竞品译名混排。
- **相关文件**：session/SESSION_HANDOFF_WritingAgent.md §2.4

---

### 2026-06-26 | Research Agent | 引用论文前先核对精读笔记事实

- **场景**：研究 Agent 曾在 §2 Related Work 中引用 Rec2PM 的 Challenge 4，但写作 Agent 后续核对精读笔记时发现原论文表述与引用不符
- **教训/发现**：精读笔记是引用事实的唯一权威来源（SSOT）。凭印象引用竞品机制容易过强 claim 或错位归因。研究 Agent 精读时若没记录具体行号证据，写作 Agent 就无法验证。
- **建议**：研究 Agent 精读必产出"事实卡片"（论点 + 原文行号 + 译名），写作 Agent 引用前 grep 笔记确认。无笔记支撑的引用标 🟠 建议补。
- **相关文件**：session/SESSION_HANDOFF_ResearchAgent.md §3；reading_notes/INDEX.md

---

### 2026-06-26 | Commander Agent | 助手"全部完成"汇报需逐项核对勾选状态

- **场景**：助手汇报"P0/P1/P2 全部完成并验证通过"，但Commander Agent grep 协议文件后发现 P1 仍有 2 项 `[ ]`、P2 仍有 4 项 `[ ]` 未做
- **教训/发现**：助手"完成"汇报存在虚报风险（可能把"新增项做完"误报为"全部项做完"）。Commander Agent 接收汇报时必须逐项核对 `[x]`/`[ ]` 勾选状态，不接受"全✅"汇总性陈述。
- **建议**：接收任何"全部完成"汇报时，grep `\[ \]` 看是否有未勾选项；有则要求助手补做或明确标注"未做原因"。这是 §1.6"主动暴露问题不要藏雷"的反向应用——Commander Agent 也要对助手藏雷。
- **相关文件**：session/AGENT_COLLABORATION_PROTOCOL_v1.0.md §1.6 / §5.4

---

### 2026-06-26 | user | 产出 Agent 直接做下游产物，不经Commander Agent 中转

- **场景**：时间线原定 T2"Commander Agent 基于 EVAL_v2 帮 user 梳理一页纸"，但代码 Agent 已做了 EVAL_v2 对方法最熟，user 决定让代码 Agent 直接产出一页纸
- **教训/发现**：当产出 Agent 已掌握全部上下文时，让另一个 Agent（Commander Agent）中转会丢信息 + 增加传递损耗。Commander Agent 的中转价值在于"全局信息差"，但若产出 Agent 已有完整上下文，中转就是负价值。
- **建议**：派活时判断"下游产物需要的是局部上下文还是全局上下文"。局部（基于已产出文档）→ 直接让产出 Agent 做；全局（跨多 Agent 信息汇聚）→ 走Commander Agent 中转。
- **相关文件**：session/SESSION_HANDOFF.md §0.1 时间线 T2

---

### 2026-06-26 | Code Agent | 和外部专家/advisor对齐的讨论稿结构

- **场景**：user 要带一页纸去和advisor对齐方法，代码 Agent 提的 6 段结构按"谈话顺序"组织，产出 180 行讨论稿写入 `docs/EVAL_advisor稿设计变更_2026-06-25.md` 头部
- **经验**：讨论稿≠信息文档，要按"会议谈话顺序"组织：
  1. 开场·现状对齐（代码能跑什么 + baseline 锚点 + 已锁定消融）——证明不是空谈
  2. 共识区（12 项对照表，"你的稿子我们大部分认同"）——先建立合作基调，不对立
  3. 核心分歧（T1-T4 训练层，每条五段式：稿子怎么写 / 我们踩过什么坑带实测数字 / 我们的方案 / 你的想法怎么融入 / 待确认）——让她感到被吸收
  4. 公式层对照表（D1-D17 压缩成表，只展开 3 个有分歧的）——快速过不展开
  5. 后续路线图（近/中/长期 + 设计原则）——让她看到完整规划
  6. 待确认清单（Q1-Q9 选项式：议题 / 我们建议 / advisor要回答的具体动作）——收口
- **红线**：第⑥段必须是**选项式**不是开放问题式——让外部专家填空不让其开放式回答，否则会议发散。"我们建议"列必须给明确倾向，"advisor回答"列必须是 yes/no 或 A/B/C 具体动作
- **五段式核心**：第④段"你的想法怎么融入"是关键——每条分歧都不是单方面否定，而是说"你的 X 想法比我们强，我们吸收"，让外部专家感到合作而非被挑战
- **适用场景**：和advisor/审稿人/合作者对齐方法分歧的会议讨论稿
- **相关文件**：docs/EVAL_advisor稿设计变更_2026-06-25.md §🔵 和advisor讨论稿

---

*本文件由各Agent共同维护，Commander Agent定期review。*

---

## SeqModel 两路实现设计经验（2026-06-26，local agent）

- **场景**：advisor稿 §3.7.3 SeqModel（forward 内 reference+增量+预测全有梯度，按 session 时序）需实现，但完整 SeqModel 本质串行（chunk_2 等 chunk_1），remote-server 全量慢
- **两路方案**：
  - 路1 真串行（`--full_seqmodel`）：round-robin sampler + 跨 chunk detached 传递 + FIFO cap。reference 来自 chunk_1 末尾 cache。本质串行，remote-server 调试备查
  - 路2 Rec2PM 两阶段伪并行（`--rec2pm_seqmodel`）：Stage1 一次全局 forward 产出所有 m^ref_h（**detached teacher**，并行的根因）+ Stage2 所有 (m^ref_{h-1}, S_h) batch 维度并行。11x 加速，remote-server 主跑
- **关键设计哲学**（GEMs/Rec2PM detach 哲学）：**chunk 内 in-graph 有梯度（增量更新）+ chunk 间/Stage 间 detached（reference anchor，控内存）**。reference 跨边界必然 detached（跨 batch/Stage 保梯度图会内存爆炸）
- **红线**：
  - 路1 必须用 round-robin sampler（外层 chunk_idx 内层 users），block-shuffle 会让同 user chunks 同 batch 并行，cache 传递失效（chunk_2 看不到 chunk_1）
  - 路2 能并行的根因是 `m_ref.detach()`——reference 是 detached teacher，Stage2 无时序依赖。不 detach 则退化成串行
  - pos_emb 越界陷阱：长序列（E_global=H×(N+1)）若对整体 encode_actions 会越界（pos_emb 只有 N）。解法：**per-segment encode（L=N）+ Q_mem 无 pos_emb + 跨 segment 靠 attn_mask**，e_global cat 后不再 encode
- **Q_mem 简化陷阱**：复用 prototypes.mean 是 C=1 简化（Rec2PM 原文 C=2~4），信息容量低。先跑 C=1 看趋势，再消融 C=2/4（新增 nn.Parameter(C,D) ~30 行）
- **适用场景**：实现 Rec2PM 式端到端训练（reference memory + 增量更新 + 预测）的并行加速
- **相关文件**：`src/data/loader.py`（路1）+ `src/data/variant_loader.py`（路2）+ `src/model.py:forward_full_model/forward_variant_model` + `docs/archive/2026-06/PLAN_implementation.md`

---

## 60× eval bug 诊断教训（2026-07-07~08，user + local agent）

- **场景**：commit-ABC（2026-07-07）修 5 个 CRITICAL bug 时，顺带删了 `forward()` 的 baseline 分支 + 改 `val_ds` 从 `DatasetXSessionDataset` 为 `SequentialDataset`。之后 remote-server 全量 HR@10 从 ~0.4 崩到 0.005（60×），花了 6 轮 remote-server 诊断（R1-R6，13 个假设，12 个被排除）才定位根因。
- **根因**：eval 原来走 baseline forward（全序列尾 N 个 item，`(B,N)` 格式，和 BaseModel eval 一样的 working window），删了之后走 `forward_full_model`（按 session 拆，`(B,S,N)` 格式），后者产出的 h_out 在 full-vocab 434K 上判别力极差。
- **修复**：恢复 baseline forward 分支 + `--eval_baseline` flag（`DatasetXSessionDataset` + rebuild cache + sampled_eval 每 epoch）。remote-server 验证 HR 0.0058→0.3223。
- **核心教训**：
  1. **删代码路径前搜全部调用方**：baseline forward 看似"训练不走"但 eval 依赖它（`valid_mask=None` 分支）。commit-ABC 只关注了训练路径，没检查 eval 入口。
  2. **训练/eval 数据格式不能随意混用**：训练用 `SequentialDataset`(B,S,N) + `forward_full_model`，eval 用 `DatasetXSessionDataset`(B,N) + baseline forward——两者是**设计上合理的分离**（训练做 SeqModel session 串行，eval 做全序列级预测和 BaseModel 可比）。强行统一格式反而出问题。
  3. **gen_loss 收敛不代表 eval 正常**：AM 训练 gen_loss 降到 0.40（正常），但 full-vocab HR 0.005（崩了）。sampled 128 neg 的 loss 曲线看不出 eval 问题。**改了 eval 逻辑后必须跑一次 sampled_eval/full_eval 对比改前数字**。
  4. **local machine 小规模预验证不可信**：本次 13 个假设中多次出现"local machine 小规模方向和 remote-server 真实规模完全相反"的情况（如 eval_no_memory local machine +49% vs remote-server -17.7%）。**任何假设都要 remote-server 真实规模验证后才能下结论**。
  5. **改动链式传播**：删 baseline forward(改动1) → 逼迫改 val_ds 格式(改动2) → 逼迫改 eval 取 target 的索引维度(改动3)——一个改动引发级联，每个环节都可能引入新问题。
- **过程中额外发现并实现的改进**：`--no_self_leak`（user 要求默认开启）/ `--evict_strategy`（论文 §3.3 Govern 接入主路径）/ L2/L3 cache 持久化 / pretrained encoder 加载 / Router K padding（待实现）
- **相关文件**：`docs/DIAG_60x_HR低_根因确认_2026-07-07.md`（完整 13 假设排除/确认记录）/ commit 6b82333+9e226f4（修复）/ commit-ABC（引入 bug 的 commit）

### 2026-07-08 | Code Agent | neat 清理自检要逐条核对 archive section 回流 + §0.4 规则射程有限

- **场景**：代码 Agent handoff neat（24 闭环 section 归档 + §0 精简 + INSTRUCTION_07-03 归档），自检补 6 行 §M/§P 回流，但另一个 agent review 发现漏了 2 个（v3k / P0批1 handoff 零回流）；INSTRUCTION_07-03 归档引用"§M 行320"实际不对应（证据错误）；5天<14天归档违规。
- **教训**：
  1. **自检要逐条核对**：每个 archive section grep 关键词在 handoff（§0/§M/§P/§D）命中数，0 命中=漏回流。不能只补"觉得缺的"（我补 6 个漏 2 个）。
  2. **归档理由引用要可核查**：commit message 说"行320回流"要实际读行 320 确认（我引用错行号）。
  3. **§0.4⑤ 14天规则射程有限**：文本只覆盖 INSTRUCTION_*.md，不覆盖 handoff 内嵌闭环 section / 非 INSTRUCTION 命名反馈文档——协议空白，各 Agent 不应自行类推。
- **建议**：
  1. 自检时 grep 每个 archive section 关键词在 handoff 命中数，0 命中=漏回流，补一行再归档。
  2. 归档 commit message 引用要可核查（行号/文件路径实际对应）。
  3. §0.4 规则射程（handoff 内嵌 section / 非 INSTRUCTION 反馈文档归档时机）待 user/Commander Agent 补明文规则，避免各 Agent 各凭理解。
  4. **引用数字要回源 archive 原文/remote-server_GUIDE 核对，不能抄别的文档转述**：这次 D16 50ep HR 抄了 07-04 旧 INSTRUCTION 的 0.4570 错值（实为 BaseModel L=4 80ep HR），真实 0.4364 ep50 -1.1%（方向都反了，写的 +3.6% 超越实际是 -1.1% 落后）。自检"核对存在与否"做到了，"核对数字本身准确"没做到——同一类问题的另一个侧面。

### 2026-07-08 | local agent | 性能优化要先定位真实瓶颈，不能照单全收诊断建议

- **场景**：remote-server 助手诊断 rebuild 慢（29 实验跑很久），给了 5 个优化方案：A) num_workers 加倍 B) rebuild 多进程化(ProcessPoolExecutor) C) k-means 换 faiss-cpu D) GPU k-means E) 跳过重建。remote-server 建议中期做 B、长期做 C。
- **教训/发现**：实际读 `rebuild_cache` 代码后发现，k-means 只做 434K items→8 个簇心，10 轮迭代 <5 秒，根本不是瓶颈；真正瓶颈是 **Phase 2 GPU 压缩**（85K segments 长度分布不均，pad_sequence 按 chunk 内最长 segment 补零，短 segment 有几十倍 padding 浪费）。这是 **GPU-bound**，remote-server 建议的 B（CPU 多进程）和 C（faiss 加速 k-means）都打在了不是瓶颈的地方——加 CPU 并行救不了 GPU 算力浪费。真正有效的是给 GPU 端做 segment 按长度排序（同 chunk 内长度接近，padding 大减），实测 Phase2 快 2.4×。
- **建议**：收到"性能慢"的诊断报告和优化建议时，不要直接照单执行，先自己读一遍关键路径代码，确认报告里"占比最大的阶段"和"建议优化的阶段"是不是同一个。诊断 Agent 可能凭经验假设（"rebuild 慢 = k-means 慢"）而不是真的测过每个子阶段的真实耗时。加 per-phase 计时打印（`_time.time()` 打点）是最低成本的验证手段，比读代码猜测更可靠。
- **相关文件**：`src/data/dataset.py rebuild_cache`（commit commit-DEF 加排序+计时打印）/ `docs/archive/2026-07/REBUILD_PLAN.md`

### 2026-07-08 | local agent | neat-freak 文档同步越权：改了不该改的 section，漏了必读文件

- **场景**：执行 neat-freak 文档同步时，直接改写了 `SESSION_HANDOFF_CodeAgent.md` 的顶部状态行和「给Commander Agent 的项目建议」整段——这两处按 §3.6 回流路径应该只由代码 Agent 本人写，local agent的回流位是 §M 派活记录子段。而且新会话没有按协议开头"新会话第一件事：读本文件+MEMORY_INDEX.md+SESSION_HANDOFF.md"先读这三个必读文件，直接凭对话历史动手改文档。
- **教训**：
  1. **执行 neat-freak 前先确认自己的角色边界**：不同 Agent 对同一份 handoff 文件有不同的可写区域（代码 Agent 的头部摘要+建议区块 vs 助手的 §M/§P/§D 子段），改错区域比不改还糟——会让下一个读者以为是代码 Agent 本人的判断。
  2. **60× bug 修复 + 31 实验 + 新方法候选，命中了 §3.3 导航同步触发条件（remote-server全套实验完成产出论文级结果 + 论文主方法候选变化）**，这类信息必须在 `§0 代码域进展快照` 打 `[需导航同步]` 标记，而不是自己动手改 `SESSION_HANDOFF.md`/`MEMORY_INDEX.md`/`SHARED_RESULTS.md`（这三个是项目级文件，助手/Code Agent 都不能直接改前两个）。
  3. **越权的判断内容要能撤回但不删除证据**：修复方式是给旧内容加"⚠️已废弃"警示 banner + 把自己的判断标注"[Local Agent 原有的文字——覆盖会丢失谁在什么时间基于什么信息做过什么判断的审计链。
- **建议**：任何 Agent 做 neat-freak/文档同步前，先花 10 秒确认"这份文件我的可写区域是哪一段"，改完用 git diff 自查有没有碰到不该碰的区域。发现自己越权后不要静默保留，主动 revert 违规部分并说明。

### 2026-07-08 | local agent | edit_file 连续多次调用同一大文件，撞上已有文档记录的静默回退坑

- **场景**：上条越权修复过程中，对 `SESSION_HANDOFF_CodeAgent.md`（500+ 行）连续调用 5 次 `edit_file`。事后 `grep "�"` 发现 2 处不相关位置（"正交约束"→"正交���束"、"数据助手"→"数据���手"）出现了字符损坏，一度误判为"edit_file 随机腐蚀了无关字节"的新问题，user 提醒后核实——**这不是新问题，`SESSION_HANDOFF.md` 早就记录过同类坑**（见该文件"过程中发现的工具层面 bug"闭环记录段）：同一大文件在一条消息里并发/连续多次 `edit_file`，会出现"提示 1 replacement 成功，但读盘后改动消失/倒退回更早版本"的静默丢失，本次的字符损坏是这个"倒退回更早版本"机制的又一次具体表现（倒退拉回了某个更早的、局部已损坏的磁盘状态），不是随机腐蚀无关字节。
- **教训**：
  1. **遇到"工具好像干了奇怪事"先查 cross_agent_lessons.md + SESSION_HANDOFF.md 有没有记录过，不要重新造轮子诊断**——本次差点把已有教训当新发现写了第二份，险些造成同一坑两处记录、后人不知道该看哪份。
  2. **已有的应对方案是对的**：往后对同一大文件的多处修改，一律"整份读入 Python → 内存里做全部字符串替换 → 一次性整体写回磁盘"，不再依赖多次 `edit_file` 调用累加；本次修复损坏字符时用的正是这个方法（凑巧做对，但应该是第一选择不是事后补救）。
  3. **任何"编辑已完成"的判断必须读盘复核**（`grep` 目标字符串 + `grep -c "�"` 扫编码损坏），不能只信工具返回的成功提示。
- **建议**：改动 ≥3 处的大文件（尤其 handoff/CLAUDE.md 这类几百行的长期文档）时，默认走"读入 Python 内存改一次性写回"，别用多次 `edit_file` 叠加；改完固定跑一遍 `grep -c "�"` 全文件扫描确认零编码损坏。
- **相关文件**：`session/SESSION_HANDOFF.md`（"过程中发现的工具层面 bug"段，原始记录）

### 2026-07-09 | local agent | grep 工具复合正则会静默假阴性，别轻信"没匹配"

- **场景**：本 session 三次用多词 `|` 组合的正则（如 `pretrained_emb|q_mem_slots|rec2pm_seqmodel` 或 `rec2pm|q_mem|qmem|Q_MEM` 加 case_insensitive）搜代码，返回"(no matches)"，但换成单个词的简单模式或 bash+grep/sed 重搜，同一文件里全部命中。最严重一次差点把"forward_variant_model 机制已从主线丢失"当结论汇报给用户，用户已经准备派发"从 git 历史恢复"的任务——机制其实完整存在，只是复合正则误判。
- **教训/发现**：本环境的 grep 工具在多词 alternation（尤其搭配 case_insensitive 或转义字符）时会静默漏报，不是"真的没有"。凡是"没匹配"这个结果本身就让人意外/违反预期时（比如一个明明该在的关键词、一个之前文档提到过的机制），必须换单词简单模式重搜或用 bash+grep/sed 交叉验证，不能直接采信第一次的"无匹配"。
- **建议**：涉及"确认某个东西存不存在"这类高风险判断（尤其会导向"要不要重新实现"这种大动作的判断）时，复合正则搜索只当作第一遍粗筛，下结论前必须至少用一个简单单词模式复核。
- **相关文件**：本次误判发生在 `src/model.py` 的 `forward_variant_model`/`q_mem_slots` 搜索，纠正过程见 `session/SESSION_HANDOFF_CodeAgent.md` §M 2026-07-09 条目。

### 2026-07-10 | Code Agent | 给远程remote-server助手的prompt里"docs/X.md"这种相对路径依赖对方cwd，不同助手cwd不一样会各自"正确地"写到不同地方

- **场景**：给 multi-GPU和 multi-GPU两个 remote-server 助手的 prompt 里都写了类似"记录到 `docs/remote-server_XXX_LOG.md`"的指令。multi-GPU助手的 shell cwd 是 `code/`，所以它写出来的文件正确落在 `docs/remote-server_8GPU_XXX.md`；multi-GPU助手的 shell cwd 是仓库根 `paper/`，同样的相对路径写法让它把 6 个文件都写到了 `paper/docs/` 下（根目录新建了一个不该存在的 `docs/`），和 multi-GPU的规范长期不一致。两个助手都是"忠实执行了 prompt 里的路径"，没有谁犯了字面错误，是 prompt 本身路径写法有歧义（依赖读者的 cwd 假设）。这个不一致直接导致过一次"方法论缺口差点被漏看"（multi-GPU助手把一个重要发现记录进了正确位置的 `docs/remote-server_8GPU_OVERNIGHT_LOG.md`，但因为团队已经习惯了"multi-GPU文档可能在别的地方"的混乱，review 时更容易跳过没细看）。
- **教训**：
  1. **给远程助手的 prompt 里，写文件路径时不要用"看起来通用"的相对路径（`docs/X.md`），要么写清楚"相对哪个目录"，要么直接写从仓库根算起的完整路径（`docs/X.md`）**——尤其当不同助手的默认工作目录本来就不一样时，同一句话在不同 shell 里会解析成两个不同的物理位置，双方都不算"做错"。
  2. **发现某个助手的产出文件路径和既有规范不一致时，先确认对方的 cwd 约定，而不是直接假设"它自己瞎放的"**——本次修复前一度以为纯粹是 multi-GPU助手粗心，回溯后发现是 prompt 写法本身有歧义，multi-GPU助手是完全按指令做的。
  3. 修复这类问题时，要检查所有"引用了旧路径"的文档一并同步，但要先判断每处引用本身的路径语义（是"相对仓库根"还是"相对该文档自己所在目录的简写惯例"），不能无脑全局替换——`code/CLAUDE.md` 的"## Documentation"章节和 multi-GPU专属的 prompt 文件里，裸 `docs/X.md` 反而是**正确**的写法（该场景的读者/执行者 cwd 就是 `code/`），加上 `code/` 前缀会变成错误的双重路径。
- **建议**：以后新建任何要发给远程助手执行的 prompt，路径类指令统一走"完整仓库根相对路径"（如 `docs/X.md`），不要写省略前缀的相对路径，即使"通常应该"能猜对。
- **相关文件**：`docs/remote_multi_gpu_OVERNIGHT_LOG.md` 等 6 个文件迁移记录见 commit `commit-XYZ`；发现过程见 `session/SESSION_HANDOFF_CodeAgent.md` §0 第十轮条目。

### 2026-07-10 | Code Agent+multi-GPUremote-server | 一个只在函数开头被读取的属性，在函数末尾被无意义地改写，靠数值巧合掩盖了两个数据集才暴露

- **场景**：`data/dataset.py::rebuild_cache` 函数开头读 `self._has_precomputed_segs` 决定走"读预计算session边界"还是"用`idle_threshold`重新切分"；但函数末尾的`full_seqmodel`分支又把这同一个属性设成`False`——这行赋值对`__getitem__`（真正判断segment_embs可用性的地方，读的是另一个字典）没有任何功能，唯一效果是污染"同一个对象下一次调用"。叠加另一处独立问题（`baseline_val_ds.cfg = cfg`把构造时的cfg整个替换掉，带入了错误的`idle_threshold=86400s`默认值），两个问题叠加导致 DatasetY/DatasetZ 的 eval cache 每隔几个 epoch 就坍缩成几乎无记忆状态。**DatasetX 完全没暴露这个 bug**——纯粹因为 DatasetX 预处理用的`merge_gap=24`恰好在数值上等于污染后的 86400 秒默认值，坍缩前后切出的 session 边界几乎不变，眼睛看不出异常。Code Agent先在local machine上纯静态读代码把范围缩小到"这个对象的两次调用之间有什么不一样"但找不到最后一步，multi-GPUremote-server在真实环境加了3个变量的诊断打印（`cfg_id`/`cfg.full_seqmodel`/`cfg.idle_threshold`），几分钟内用50用户复现锁定。
- **教训**：
  1. **一个 flag/属性如果只在函数的一个地方被读，就不该在函数别的地方被写**——这种"读写位置分离"的属性极容易在后续修改时被无意间在错误的地方赋值，因为写的人可能根本不知道这个属性在别处被读、语义是什么。看到类似`self._xxx = False`这种赋值语句时，如果它紧跟在一段和"xxx"字面意思不直接相关的逻辑分支里（这里是"full_seqmodel不需要segment_embs所以清空缓存"），要专门确认这行到底在清空什么、有没有连带影响到同名但语义不同的属性。
  2. **"数值巧合掩盖 bug"是真实存在的风险，不能因为一个数据集上看不出问题就认为逻辑是对的**——这个 bug 对 DatasetX/DatasetZ/DatasetY 三个数据集都在执行，只是 DatasetX 恰好因为一个无关的数值撞车而未被观察到。以后遇到"这个逻辑在 A 数据集上运行正常"时，不能默认它在 B 数据集上也会正常，尤其涉及依赖具体数值阈值的逻辑（idle_threshold、cap、size 之类）。
  3. **静态读代码能大幅缩小范围，但"同一个对象两次调用结果不同"这类问题，最后一步几乎总是需要真实环境里加诊断打印**——本次Code Agent在local machine上把嫌疑范围缩小到了具体函数和具体几个候选变量，但没有运行环境验证只能停在"排除了几个假设"，multi-GPUremote-server在真实GPU环境加3行诊断打印几分钟就锁死了，效率差异很大，不必在纯静态分析上死磕到底，缩小范围后就该交给能跑代码的环境去打诊断点。
- **相关文件**：`src/data/dataset.py` 修复 commit `commit-JKL`；完整诊断记录见 `docs/remote-server_MULTIDATASET_LOG.md`；两处引用了错误flag组合（`chunk_size 5`+`evict_strategy`）的"定型配置速查"文档`docs/ARCHITECTURE_DESIGN.md`和`docs/LOCAL_EXPERIMENT_GUIDE.md`同批一并修正——这两份文档是这次全面审查才发现的独立遗漏，说明"定型配置"这类容易被复制粘贴的速查表，一旦配置定型值发生变更（chunk_size 5→4），要主动去搜一遍所有出现过旧值的地方，不能只改一处就认为完成了。

### 2026-07-10 | Code Agent+multi-GPUremote-server | 修好一个真实bug≠这个bug就是观察到的异常现象的原因，必须用修复后的数据验证，不能默认"修完了就该解释得通"

- **场景**：DatasetY上"AM(0.2410)远低于BaseModel(0.4352)"这个异常，一开始怀疑是eval cache坍缩bug造成的（`baseline_val_ds`每5epoch重建后坍缩成几乎无记忆的状态）。这个怀疑合理、bug本身也是真的（后来multi-GPU在真实环境100%确认+修复），Code Agent当时的表述是"很可能是eval bug，非真实模型能力"——**属于在数据出来之前基于代码逻辑做出的合理推测，用词上已经加了"很可能"而不是断言，但推测终究只是推测**。multi-GPU用修复后代码重跑DatasetY AM：HR@10=0.2381，和修复前的0.2410只差0.29%，坍缩确实消失了（segment数从坍缩后的969回升并稳定在25319-25333）但HR几乎没变——**说明这个bug不是（或不是主要）造成BaseModel>>AM现象的原因**，异常本身依然成立，变回一个真正开放的问题。
- **教训**：
  1. **"这个bug应该能解释异常X"是一个待验证的假设，不是修完bug之后自动成立的结论**——bug越明确、诊断过程越扎实，越容易产生"修完了问题肯定解决了"的心理惯性，但两者是两件独立的事：bug是不是真的存在是一件事，这个bug是不是导致了你最初想解释的那个现象是另一件事，后者只能靠修复后重新跑数据来验证，不能靠"这个bug看起来足够严重"来推断。
  2. **multi-GPU这次的处理方式值得作为范例记录**：没有因为"好不容易找到并修好了bug"就顺势宣布问题解决，而是如实报告"意外的是数值几乎没变"，并明确说"不能说修复后问题解决了"——这是本项目一贯强调的"磁盘是唯一真相，不盲信汇报（包括不盲信自己的推测）"方法论的一次具体践行，值得延续。
  3. **对外沟通/写文档时，"很可能是X"这种带不确定性词汇的推测，一旦被验证推翻，必须显式撤回并说明撤回原因，不能留着旧表述不管**——本次Code Agent在`SHARED_RESULTS.md`、`SESSION_HANDOFF_CodeAgent.md`、`code/CLAUDE.md`三处都同步撤回了"很可能是eval bug"的说法，改成"这个bug存在但不解释该现象，异常重新开放"，避免下游（Writing Agent、Commander Agent）基于已经被证伪的推测做决策。
- **相关文件**：multi-GPU重跑记录见`docs/remote-server_MULTIDATASET_LOG.md`（multi-GPU自己维护，待其更新）；Code Agent撤回记录见`session/SESSION_HANDOFF_CodeAgent.md`§0第十四轮、`code/CLAUDE.md`、`SHARED_RESULTS.md`。

---

### 教训4：graph-connected zero必须绑定到永远不被freeze的参数（2026-07-11，DDP全padding batch四连崩修复）

- **场景**：multi-GPUDDP全padding batch导致backward崩溃，经历四轮修复：①`continue`跳过→NCCL all_reduce次数不对齐hang ②dummy loss覆盖全参数→"ready twice"(forward graph和dummy graph双引用同参数) ③skip forward→DDP buffer broadcast不对齐 ④model.py内`_zero=(prototype_embs.sum()*0.0)`→Phase 0/1 freeze prototypes时_zero无grad_fn仍然崩溃。最终fix：`_zero=(self.encoder_norm.weight.sum()*0.0)`，绑定到永远不被curriculum freeze的encoder参数。
- **教训**：
  1. **在训练循环外打补丁(dummy loss/skip forward/改sampler)都是workaround不是根因修复**——真正的bug在model.py的loss初始化逻辑(`torch.zeros()`/`torch.tensor(0.0)`)，这些plain tensor在输入退化时（全padding batch）无法构建计算图。修复应该在bug所在的层（model），不是在调用方（训练循环）。
  2. **"graph-connected zero"不是任意参数都行**——必须确认所选参数在所有curriculum phase下都`requires_grad=True`。prototypes在Phase 0/1被freeze，用它做`_zero`在Phase 0第一个全padding batch就崩溃。这种"某些phase才暴露的bug"很容易被正常phase的smoke test漏掉。
  3. **DDP兼容性的核心约束是"所有rank在每一步执行完全相同的collective操作序列"**——不只是backward的all_reduce次数（已知），还包括forward里的buffer broadcast（容易忽略）。任何跨rank的条件分支（if padding: skip/continue/dummy）都可能违反这个约束，最安全的做法是让model自身能handle退化输入，而不是在训练循环里加条件分支。
- **相关文件**：`src/model.py:479`（_zero定义）、`code/training/curriculum.py:42-56`（Phase freeze表）、`code/scripts/run_full_model.py:835`（freeze执行）。commit链：`fcf83ba`→`f738c35`→`23b18e0`→`ee9c023`。

---

### 2026-07-11 | Code Agent | L3 Prototype EMA 覆盖梯度——训练中 EMA 和 L_regularization 冲突

- **场景**：Code Agent核查 `docs/EMA_mechanism_analysis.md` 时发现：L3 prototype 同时是 `nn.Parameter`（接收 L_regularization 梯度）又被 `compute_ema` 用 `@torch.no_grad()` + `.data.copy_()` 每 batch 直接覆盖。设计意图是"训练靠梯度、EMA 只在推理/增量更新时用"（见 `RESEARCH_architecture_redesign.md` §三），但当前实现是训练时两者同时作用。
- **教训/发现**：EMA 的 `.data.copy_()` **完全绕开 autograd**，L_regularization 算出的梯度（本该拉开 representation collapse。
- **建议**：任何 Agent 在设计"参数同时被梯度和非梯度路径更新"的模块时，要明确两条更新路径的优先级和互斥条件。`@torch.no_grad()` + `.data.copy_()` 会静默吞掉之前所有梯度计算的效果，没有任何 warning。验证实验 `--no_train_ema`（commit commit-GHI）排队中。
- **相关文件**：`docs/EMA_mechanism_analysis.md`（一、二）、`session/RESEARCH_architecture_redesign.md`（§三）、`session/cross_agent_lessons.md`（本条目所在文件，此前已有"EMA 覆盖梯度"的初步记录，本条是代码核实后的精确版）
