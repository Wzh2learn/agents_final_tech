---
name: code-pathology
version: 1.0.0
description: |
  代码全路径病理检查：沿数据流从输入到输出逐层审查，找确定性 Bug 和高价值优化方向。
  核心理念：不做泛泛 review，而是沿着一条具体的训练路径（如主特征路径 full-model + enhanced 分支），
  从数据加载到 eval 输出，逐层追踪张量形状、梯度流向、时序语义、DDP 安全性，
  用"代码事实"而非"可能有问题"来定性每个发现。
  触发词：代码病理、全路径review、code review、代码审查、code pathology、
  全链路检查、查一遍代码、review这条路、bug hunt、代码体检。
  示例：对主特征路径做一次全路径review、帮我查一遍路1的代码有没有bug、
  review一下MODEL的训练路径、代码体检。
metadata:
  author: anonymous
  category: code-quality
  tags: [bug-hunt, optimization, gradient, DDP]
allowed-tools: [Read, Glob, Grep, Agent, Bash, Write, Edit]
---

# 代码病理检查 — Code Pathology

> **设计哲学**：实验跑出来的数字只有代码正确时才有意义。一个隐藏的 `.detach()`、一个错误的时序、
> 一个 DDP 不同步，都能让你在错误的基线上做三周消融。
> 本 skill 诞生于一次主特征路径的全路径review——那次发现了3个确定性Bug（EMA覆盖梯度/绕过freeze/eval旧cache）
> +4个高价值优化（Compressor用encoder输出/Router真实ts/EMA只用新episode），直接改变了large-scale rerun strategy。

## 什么时候用这个 Skill

- 一条训练路径的实验要run at large scale之前（**最高ROI时机**）
- 实验结果异常（震荡、不收敛、指标矛盾）需要排查代码原因
- 新功能实现后的系统性验证（不是看单个文件，是看整条链路）
- 合并多个feature后检查交互副作用

## 不适用于

- 纯风格/命名review（用linter）
- 单文件局部bug（直接debug）
- 架构设计讨论（用research-driven-design skill）

---

## 核心流程：9 维病理检查

### 前置：确定检查路径

**不做全代码review，锁定一条具体路径**。格式化为：

```
检查路径: [PathA / 路1 / 路2 / rebuild / ...]
CLI 配置: [--full-model --enhanced ...]
入口文件: [scripts/run_<path>.py]
核心文件: [model.py forward_<path> → memory/*.py → decoder/ → data/]
```

**为什么锁定路径**：不同路径共享大量代码但分支逻辑不同，review全代码会漏掉路径特定的bug。
那次的 EMA 覆盖梯度 bug 就藏在 `enhanced` 分支里，全局review不走这个分支就看不到。

### 维度 1: 数据输入（Data Input）

**检查目标**：数据加载→特征构造→batch组装，确保模型看到的输入是你以为的输入。

```
检查清单:
 □ Dataset.__getitem__ 返回的字段和 collate_fn 预期是否一致
 □ padding/truncation 逻辑：截取索引是否同步（ek/ev/et同长度？）
 □ cache 读写：写入时的形状 vs 读出时 collate_fn 预分配的形状
 □ mask 构造：valid_mask/attention_mask 是否正确反映 padding 位置
 □ 时间戳/action_type 等辅助特征是否真的传到了模型（不是全0占位）
 □ 数据类型：float32 vs float16 vs int64，特别是索引类的张量
```

**典型Bug模式**：
| 模式 | 症状 | 案例 |
|------|------|------|
| 截取不同步 | collate_fn shape mismatch crash | D3 et截取用cap后长度判断，et=68 vs ek=64 |
| cache写入脏数据 | 训练中期crash或指标突变 | episode_timestamps全0（注释TODO但没实现） |
| 辅助特征死通道 | 对应模块无效但不crash | action_type_emb存在但某路径没传 |

**检查方法**：
```python
# 在 __getitem__ 和 collate_fn 之间加 assert
assert ek.shape[0] == et.shape[0], f"ek={ek.shape[0]} vs et={et.shape[0]}"
# 或者直接读代码追踪：写入点的shape → 读取点的shape → collate_fn的预分配shape
```

### 维度 2: 模型结构（Model Architecture）

**检查目标**：forward path上每个模块的输入输出维度、激活函数、norm层是否符合设计。

```
检查清单:
 □ 各模块的输入来源：是raw embedding还是encoder输出？（空间一致性）
 □ Norm类型一致性：encoder用LayerNorm、decoder用RMSNorm是有意还是遗留？
 □ 残差连接：是否每层都有？skip connection的维度是否匹配？
 □ 初始化：新增模块（Gate/Router MLP）的初始化是否合理？
 □ __init__ vs forward 一致性：__init__构造了但forward没用的模块（死权重）
 □ 条件分支：if cfg.X 的分支是否都有对应的else/default行为
```

**典型Bug模式**：
| 模式 | 症状 | 案例 |
|------|------|------|
| 空间不一致 | 辅助loss改善但主指标不动 | D1: Compressor压缩raw embedding，Decoder用encoder输出，L2/L1不同空间 |
| 死模块 | 参数占显存但无梯度 | __init__构造write_gate但某路径forward不调用 |
| 分支遗漏 | 某配置组合crash | model_enhanced=True但forward里没处理这个flag |

### 维度 3: 三层记忆（3-Layer Memory）

**检查目标**：L1 working / L2 episodic / L3 prototypes 的生命周期、更新时机、交互方式。

```
检查清单:
 □ L1(working): H_working来源正确？encoder输出 vs raw embedding？
 □ L2(episodic): cache的写入时机（forward中 vs step后）和读取时机是否有竞态？
 □ L2 cap/truncation: 超过容量时的截取策略（FIFO/-k_cap/govern）是否正确？
 □ L3(prototype): 更新方式（EMA/k-means）的时序——是在梯度更新前还是后？
 □ L2↔L3交互: EMA的输入是全部episode还是只有新episode？稀释问题？
 □ per_user vs global: prototype是共享还是per-user？路径是否正确分发？
 □ eval时的memory状态: 是训练末的状态还是重建的状态？
```

**典型Bug模式**：
| 模式 | 症状 | 案例 |
|------|------|------|
| EMA时序错误 | proto梯度失效 | Bug1: forward算EMA(旧proto)→step梯度更新→copy_(旧EMA)覆盖梯度 |
| EMA稀释 | proto更新缓慢 | D4: m_e_values含64个旧cache+4个新episode，mean被旧episode稀释 |
| eval用旧cache | 指标偏低 | Bug3: val_ds cache在epoch1 rebuild后不再更新 |
| proto漂移 | norm持续增长 | proto norm 从 ~1 单调涨到近 10（EMA累积无normalize） |

**关键时序图**（每条路径都要画出来）：
```
forward开始 → [读L2 cache] → [encoder] → [Compressor压缩→新episode]
  → [Router retrieves from L2] → [Decoder fuses L1+L2+L3] → [算loss]
  → backward → optimizer.step() → [EMA更新L3] → [写回L2 cache]
                                    ↑ 必须在step后（用梯度更新后的proto）
```

### 维度 4: 四个操作（Core Operations (e.g., Write/Read/Update/Govern)）

**检查目标**：Write/Read/Update/Govern 四个操作的实现是否与论文设计一致。

```
检查清单:
 □ Write(Compressor+Gate):
   - Compressor的输入是encoder输出还是raw？（应该是encoder输出）
   - Gate的梯度路径：STE是否正确（y_hard - y_soft.detach() + y_soft）？
   - Gate=0时的行为：是skip还是写全0？（写全0会稀释mean）
   - L_binary是否在正确的位置累积？

 □ Read(Router):
   - Router query来源：H_working末位 vs 记忆查询向量 vs 其他？
   - Router key/value：来自cache还是in-graph M_e？
   - 4维scoring（relevance/recency/importance/semantic）每维的输入是否正确？
   - 时间戳：cache中的episode timestamp是真实的还是全0？
   - top-K选择：Gumbel-TopK vs 普通topk？训练/eval行为一致？

 □ Update(EMA):
   - in-place vs non-inplace：DDP下必须non-inplace（compute_ema而非ema_update）
   - EMA时机：必须在optimizer.step()之后（用梯度更新后的proto）
   - EMA输入：只用新episode还是全部M_e？（应该只用新的，避免稀释）
   - normalize：EMA后是否normalize防止norm漂移？
   - DDP broadcast：EMA后是否rank0广播？

 □ Govern(Evict):
   - 淘汰策略：FIFO vs retention score vs MLP？
   - 淘汰时机：cache写入时还是读取时？
   - 截取索引：ek/ev/et是否同步截取？（同一个keep_idx）
```

**典型Bug模式**：
| 模式 | 症状 | 案例 |
|------|------|------|
| EMA绕过freeze | warmup阶段proto漂移 | Bug2: Phase0/1 freeze proto但EMA copy_不检查phase |
| Router输入全0 | recency维度无区分 | D3: cache episode timestamp=0，Router对旧episode无法区分新旧 |
| DDP proto不同步 | 指标震荡 | ema_update inplace改proto.data无broadcast → 多rank漂移 |
| Gate写全0 | M_e被稀释 | D6: gate=0时key_s*=0写入全0行，mean(dim=1)被稀释 |

### 维度 5: Loss 构成（Loss Composition）

**检查目标**：每个loss的计算、权重、梯度路径、detach边界。

```
检查清单:
 □ L_gen: 主loss，梯度流向哪些模块？是否覆盖了Compressor/Gate？
 □ L_con: 压缩质量loss，teacher是什么？detach了哪些？
 □ L_ortho: 正交约束，输入是当前proto还是EMA后proto？
 □ L_gate/L_binary: 稀疏性约束，是否和主loss方向冲突？
 □ L_router: Router loss，detach了query/key/proto哪些？
 □ 权重balance: 各loss量级是否在同一数量级？梯度是否被某个loss淹没？
 □ detach原则: L_con只更新Compressor+Proto？L_router只更新Router？检查每个detach点
 □ loss累积: 多session/多chunk的loss是sum还是mean？是否有重复累积？
```

**检查方法**：
```
对每个loss画梯度路径图：
L_gen → Decoder → [L3 proto, L2 retrieved, L1 H_working] → Encoder → item_emb
L_con → Compressor → Prototype（detach Encoder、detach item_emb）
L_ortho → Prototype（直接）
```

### 维度 6: 训练路径和方式（Training Pipeline）

**检查目标**：训练循环的控制流、数据流、状态管理。

```
检查清单:
 □ DDP forward分发: 是走model()还是raw_model.forward_*()？
   （必须走model()让DDP wrapper注册all_reduce hook）
 □ optimizer.step()和其他状态更新的时序:
   1. forward → 2. backward → 3. step() → 4. EMA更新 → 5. cache写回
   （顺序不能乱，EMA必须在step后）
 □ Curriculum phase切换: 哪些参数在哪个phase freeze/unfreeze？
   freeze的参数是否有其他路径绕过（如EMA copy_）？
 □ cache rebuild时机: 哪些epoch做？eval前是否rebuild？
 □ 梯度累积: 如果有gradient accumulation，loss是否正确除以accumulation steps？
 □ 混合精度: autocast范围是否正确？哪些操作必须在fp32？
 □ 随机种子: DDP下各rank的数据是否不同？sampler是否正确分片？
```

**典型Bug模式**：
| 模式 | 症状 | 案例 |
|------|------|------|
| 绕过DDP wrapper | 多卡梯度不同步/震荡 | raw_model.forward_<path>()绕过model()的DDP hook |
| 时序颠倒 | 梯度被覆盖 | Bug1: EMA(旧proto)在step前算好→step后copy_覆盖梯度更新 |
| phase守卫缺失 | freeze失效 | Bug2: curriculum freeze proto但EMA copy_不检查phase |
| eval cache过时 | 指标偏低 | Bug3: val_ds cache epoch1后不再rebuild |

### 维度 7: 参数配置（Parameter Config）

**检查目标**：config默认值、CLI参数传递、feature flag生效。

```
检查清单:
 □ 新feature的默认值: 必须是off/False，不破坏已有baseline
 □ CLI参数→config→模型: 传递链是否完整？有没有中间断裂？
 □ 参数耦合: 改了A是否需要同步改B？（参见research-driven-design Step 4.5）
 □ 硬编码: 是否有应该读config但硬编码的值？（如compute_ema_softmax里的tau=0.1）
 □ 条件组合: flag A + flag B 同时开启是否有未测试的交互？
 □ 类型安全: bool flag是否用store_true？数值参数是否有合理range？
```

### 维度 8: 评估方式（Evaluation）

**检查目标**：eval pipeline的正确性和公平性。

```
检查清单:
 □ eval时的model状态: model.eval()是否调用？dropout/batchnorm行为？
 □ eval时的memory状态: 用训练末cache还是重建cache？
 □ top-K计算: 是全量item还是采样？负样本是否一致？
 □ 指标计算: HR@K/NDCG@K/MRR的实现是否正确？
 □ best model选择: 是best epoch还是last epoch？best基于哪个指标？
 □ sampled vs full eval: sampled eval的采样比例是否足够？
   是否有只在full eval才暴露的问题？
 □ DDP eval: 各rank是否eval相同数据？结果是否正确聚合？
```

**典型Bug模式**：
| 模式 | 症状 | 案例 |
|------|------|------|
| 取末epoch而非best | 震荡路径被低估 | 末epoch谷值 vs 中段峰值差一截（末值显著偏低） |
| eval用旧cache | 指标偏低 | Bug3: val_ds在epoch1 rebuild后冻结 |
| sampled eval误导 | sampled和full方向不一致 | HR@10 sampled中为0（设计问题非bug） |

### 维度 9: 训练速度（Training Speed）

**检查目标**：性能瓶颈、显存使用、可扩展性。

```
检查清单:
 □ 数据加载: num_workers/prefetch_factor是否合理？IO瓶颈？
 □ 计算瓶颈: 哪个模块最慢？是否有不必要的同步操作？
 □ 显存: 中间变量是否及时释放？detach是否减少了计算图？
 □ cache操作: numpy↔tensor转换是否频繁？能否常驻GPU？
 □ 通信: DDP all_reduce + broadcast 的开销？是否有不必要的同步？
 □ 可优化点: 哪些操作可以batch化？哪些循环可以向量化？
```

---

## 发现分级标准

每个发现按影响分级：

| 级别 | 标准 | 行动 |
|------|------|------|
| **🔴 确定性Bug** | 代码行为与设计意图不一致，有明确的代码事实证据 | 必须修，修完才能run at scale |
| **🟡 高价值优化** | 代码正确但次优，改了大概率提升效果 | 建议修，feature-flag off不破坏baseline |
| **🟢 观察点** | 可能有问题但无法确定，或影响小 | 记录，running at scale观察 |
| **⚪ 设计建议** | 不影响正确性，改善可维护性/扩展性 | 可选，does not block large-scale run |

**分级关键原则**：
- 🔴 必须有**代码事实**（行号+逻辑推导），不能是"可能有问题"
- 🟡 必须有**预期收益的逻辑推导**，不能是"改了试试"
- 不确定的发现降级为🟢，不要为了显得thorough把🟢升级为🟡

---

## 输出模板

```markdown
## 代码病理报告：[路径名]

**检查路径**: [CLI配置]
**涉及文件**: [文件列表]
**检查日期**: [日期]

### 发现汇总

| # | 级别 | 维度 | 标题 | 文件:行号 |
|---|------|------|------|-----------|
| 1 | 🔴 | 三层记忆 | EMA覆盖梯度更新 | model.py:<行> + run_<path>.py:<行> |
| 2 | 🟡 | 四个操作 | Compressor用raw embedding而非encoder输出 | model.py:858 |
| ... | ... | ... | ... | ... |

### 详细发现

#### 🔴 Bug 1: [标题]
- **位置**: `file.py:行号`
- **代码事实**: [引用具体代码，说明实际行为]
- **设计意图**: [应该是什么行为]
- **影响**: [对实验结果的具体影响]
- **修法**: [具体怎么改，几行代码]
- **验证**: [怎么确认修好了]

#### 🟡 优化 1: [标题]
- **位置**: `file.py:行号`
- **现状**: [当前代码怎么做的]
- **问题**: [为什么次优]
- **改进**: [怎么改]
- **预期收益**: [为什么改了会更好的逻辑推导]

### 时序图
[关键操作的时序，标注哪些地方有问题]

### 梯度路径图
[各loss的梯度流向，标注detach点和断裂点]

### 修复优先级
1. [先修什么] — 原因
2. [再修什么] — 原因
3. [可选修什么] — 原因

### Post-fix monitoring notes
[修完后running at scale需要watch的点]
```

---

## 实战案例：一次主路径全路径Review

这是本skill诞生的触发场景，完整展示了检查过程和发现：

**检查路径**: `--full-model --enhanced`（主特征路径）
**涉及文件**: model.py / memory/update.py / data/<dataset>.py / scripts/run_<path>.py / training/curriculum.py

**发现**:
| # | 级别 | 维度 | 标题 |
|---|------|------|------|
| Bug1 | 🔴 | 三层记忆×训练路径 | EMA覆盖梯度更新（proto梯度失效——主指标是在梯度失效下跑出来的） |
| Bug2 | 🔴 | 四个操作×训练路径 | EMA绕过curriculum freeze（Phase0/1 proto漂移） |
| Bug3 | 🔴 | 评估方式 | eval用epoch1 cache（指标偏低） |
| D1 | 🟡 | 模型结构×四个操作 | Compressor压缩raw embedding而非encoder输出（L2/L1空间不一致） |
| D3 | 🟡 | 数据输入×四个操作 | Router cache episode timestamp全0（recency维度失效） |
| D4 | 🟡 | 三层记忆 | EMA输入含64旧+4新episode（旧episode稀释） |
| D3-et | 🔴 | 数据输入 | et截取和ek/ev不同步（大规模跑到中段 crash） |

**关键教训**:
1. Bug1是上一次 review 时的疏漏——只看了DDP安全（non-inplace），没看梯度时序语义
2. 多个发现跨越两个维度（如Bug1=三层记忆×训练路径），单维度review会漏
3. 🔴级发现必须有代码行号+时序推导，不能是"可能有问题"

---

## 检查策略

### 选择检查深度

| 场景 | 推荐深度 | 预计耗时 |
|------|---------|---------|
| pre-launch full checkup | 9维全查 | 30-60min |
| 新feature集成后 | 重点查维度2-6 | 15-30min |
| 实验异常排查 | 按症状定位1-2个维度 | 10-20min |
| 修复后回归验证 | 只查修改涉及的维度 | 5-10min |

### 检查顺序建议

**推荐顺序**（按发现bug概率排序）：
1. **维度6 训练路径** — DDP/时序/phase问题最容易被忽略且影响最大
2. **维度3 三层记忆** — 状态管理复杂，bug藏得深
3. **维度4 四个操作** — each core operation的边界条件
4. **维度1 数据输入** — shape/截取/cache同步
5. **维度5 Loss构成** — detach/梯度路径
6. **维度2 模型结构** — 空间一致性
7. **维度8 评估方式** — eval正确性
8. **维度7 参数配置** — flag/默认值
9. **维度9 训练速度** — 性能优化（最后看）

### 检查心法

1. **追数据流，不追代码结构**：不是按文件读，而是按张量从输入到输出的流向读
2. **画时序图**：forward→backward→step→EMA→cache写回，任何乱序都是bug
3. **问"这行代码的输入从哪来"**：顺藤摸瓜往上追，直到数据源头
4. **问"这行代码的输出去了哪"**：顺藤摸瓜往下追，直到loss/eval
5. **DDP思维**：每行代码都问"每个rank执行这行后状态一致吗？"
6. **代码事实 > 推测**：引用具体行号和代码片段，不要说"可能"
7. **不要grep一半就下结论**：一个函数可能在 run_<path>.py 调用而不在model.py出现

---

## 与其他 Skill 的关系

- **experiment-autopsy**: 分析实验结果，找到"为什么指标异常"。code-pathology从代码侧找根因——两者互补
- **research-driven-design**: 设计新训练策略。code-pathology verifies implementation matches design — design→implement→pathology→deploy
- **neat-freak**: 文档同步。pathology发现的bug/优化需要更新到docs
