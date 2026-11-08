# 已训练8B基线：复用入口

> 2026-11-08 | 下一动作见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)。训练、部署和旧五臂完整过程已[归档](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md)；本页不新增实验或改写原结果。

<a id="trained-baselines"></a>
## 当前复用：同BF16父模型的 frozen / ordinary / recovery

O/R均已真实训练、保存重载、转为GGUF LoRA并实际推理，现成资产可直接比较新布局，不需要先增加训练。私有根`learning_comparison_v1/`在GB10证据目录，具体加载前重新核对实际文件与自有进程。

| 资产 | 相对私有根路径 | SHA256 |
| --- | --- | --- |
| 共同BF16父模型 | `gguf_conversion_v1/hf_parent_bf16_v1/Qwen3-8B-HF-BOUND-BF16.gguf` | `505618debb4e6ff112a8724f22853f09d4a6dd7ba0e32123d404fe9a4da8f5e3` |
| 普通训练 O | `gguf_conversion_v1/ordinary_v4/ordinary_v4.gguf` | `deaf4b1618cdc3664dab92d798c375f36ae2e9e6c87e787e9118277fa2bb805f` |
| 纠正训练 R | `gguf_conversion_v1/recovery_v4/recovery_v4.gguf` | `560a86bd66d11fd2186a9ddff0130b8c4bc37a1fb148623a6faea831cc4b34ba` |
| HF父权重绑定 | `HF8B_MODEL_BINDING_V1.json` | `b8d5af477c1f6be67981583a4a60df9561ea53872e0676535aa9745fce011dc1` |

两个约15MB的GGUF是适配器，不能单独充当完整模型。旧默认Q4未证实与HF LoRA坐标兼容，不能代替共同BF16 frozen。

<a id="实际训练表示复核2026-11-07"></a>
## 训练和旧成绩：可引用到哪里

同HF8B、seed17、q/v LoRA r8/alpha16/dropout0、lr2e-4、batch1，两臂各192更新；O为1,135,199序列/8,239监督tokens，R为1,135,273/8,378。实际135个唯一行中O为67行、R为68行，来自相同7组；只监督当前助手动作与EOS。可称同父模型/初始化/更新数，不能称完全等训练量。R来自失败前缀的教师接续，O从reset形成，比较的是配方整体，不是孤立反馈因果。

| 旧16题开发结果 | heat/cool/look主比较 | clean诊断 | 全部原生won |
| --- | ---: | ---: | ---: |
| Frozen F | 6/12 | 1/4 | 7/16 |
| Ordinary O | 6/12 | 1/4 | 7/16 |
| Recovery R | 7/12 | 3/4 | 10/16 |
| 普通历史all7 | 5/12 | 2/4 | 7/16 |
| 普通历史top1 | 4/12 | 2/4 | 6/16 |

R-F/O主比较差的描述区间包含0；普通历史all7与F/O成功数相同、实际token更低。旧R存在原生成功后继续请求的长尾，未来三臂统一原生终态停止；工程停止控制不能算学习贡献，旧费用不扣除。[五臂完整账和C复核](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#five-arm-results)给出全部费用、区间与旧27B参照。

## 新布局比较：尚未运行

旧7组训练来源与新train12的task UID、family、layout、layout_group、game hash交集均为0；仍共享look类型、同benchmark且属于已曝光开发材料，不是独立确认。旧训练没有clean样本，新clean应单列任务类型迁移诊断。

使用现役`ordinary_reset/student8b --runtime-profile <path> --runtime-profile-sha <sha>`，三臂统一reset提示、无经验、world/模型seed、解码、终态停止、历史窗口和预算。frozen也必须显式绑定BF16 profile，否则会落回默认Q4。每臂新自有进程、admission、O/R唯一LoRA且scale1；旧PID只作历史，不作当前归属证明。

旧HF驱动锁定16题/五臂，不能直接替换池执行；复用其有限生命周期和恢复原语。`ordinary_reset`读取`total_caps`，旧HF为128POST/1800秒/100动作/64M收发bytes，来源采集96/900是另一合同。先冻结任务清单、共同设置与实际恢复身份，再进入新批次，不再围绕已闭合heat_2追加接口分支。

## 历史记录按需读

<a id="learning-runtime-history"></a>
- [训练全过程与表示核查](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#已闭合同来源两臂真实训练)。
<a id="deployment-bindings"></a>
- [共同父模型、转换与部署](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#deployment-bindings)。
<a id="private-packets"></a>
- [闭合私有镜像](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#private-packets)。
<a id="terminal-retry-20261107"></a>
- [终态重试修复](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#terminal-retry-20261107)。
<a id="five-arm-results"></a>
- [旧五臂结果与成本](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#five-arm-results)。
<a id="code-source-controls"></a>
- [早期代码来源与接口](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#code-source-controls)。当前代码纠正查[现役代码记录](CODE_SOURCE_CORRECTIONS.md#current)。
<a id="sympy-intersection"></a>
- [SymPy集合语义公开复现](../../../docs/archive/2026-11-06_agent_research_context/alfworld_learning_through_20261108.md#sympy-intersection)：16988→16953只是开发候选，目标语义及完整回归未形成Agent方法比较，不为其另建runner。
