# Astropy 真实任务对：开发批次回执

> 2026-11-06 | 固定执行代码 `d102487ac36b121b15b284f23e0b30cff66f8eda`。批次 ID 沿用 20261105，执行跨日。当前下一步见[短计划](../STAGE2_AGENT_RESEARCH_PLAN_20261102.md)，本记录不提供新增授权。

## 问题与冻结合同

源 `astropy__astropy-14995`（base `b16c7d12ccbc7b2d20364b89fb44285bcbfede54`）修复另一操作数无 mask 时的 bitwise 掩码传播；目标 `astropy__astropy-15082`（base `c5e2521db013d9641999be9c79d1d807741bc39a`）修复无 mask/unit 的 collapse。源修复是目标 base 的祖先；目标题面直接提及源 PR，因此这是所有臂共有信息。

[资格器](../qualify_swe_contextbench_astropy_20261105.py)先检查原题行为、base/gold、全部可执行回归：源 focus 0/1→1/1、回归均179/179；目标0/3→3/3、回归均132/132。资格 SHA-256 `e0ed1ac9cb580b36f65a9c90e4f99b418963e72554be92a031be955afa1fd71d`。

[运行器](../run_swe_contextbench_astropy_20261105.py)复用 OpenCode 1.18.3、本地 Qwen3.6-35B-A3B Q4_K_M、独立 attempt、自动证据/成本 sidecar。各臂 seed7201、temperature0.2、24次转发POST/900秒上限，均只读挂载固定 rg。目标测试/patch、未来 Git 历史不交给执行 Agent；评分副本恢复测试后独立执行原题及回归。

Python3.10 / NumPy1.24.3，原生组件来自 Astropy5.3.2 ARM wheel（17个扩展及生成的 `_version.py`），关键 Python 代码保持冻结源码。这是混合构建，不是固定 commit 的原生编译；base/gold 与实际 Agent 产物评测均有 `numpy.ndarray size changed` ABI 警告。覆盖清单 SHA-256 `08e6caf6ff363d2e3175af60b017b1030f32bf08ed34949ddc909cbf6b9c6300`。

## 实际结果

| 执行 | Agent exit / 状态 | 关键测试 / 回归 | 原题行为 | 转发POST / reported tokens（含cache） |
| --- | --- | --- | --- | --- |
| source / none | 0 / 正常退出 | 1/1、179/179 | 4组数据与mask均正确 | 14 /154,712（90,492） |
| target / none | 0 / 正常退出 | 0/3、132/132 | 两例数据与unit正确，无异常；mask应为None却为全False数组 | 15 /246,557（201,704） |
| target / source_history | 0 / 正常退出 | 0/3、132/132 | 两例仍分别抛mask/unit AttributeError | 6 /79,588（25,539） |
| target / generated_skill | 1 / 请求上限 | 3/3、132/132 | 两例数据[60,66,72,78]、mask None、unit Jy/None均正确 | 24 /351,534（237,893） |
| target / feedback_card | 未执行 | 未执行 | 已冻结卡片，尚无模型输出 | 0 |

普通 skill 单次产生合格目标产物，但执行未正常收口。无历史仅消除异常不算满足完整问题合同，历史臂回归通过也不代表修复目标。

## 经验形成与实际读取

源14个工具动作全部completed；glob/grep均真实工作，未见rg错误。源历史记录实际动作与最终反馈，动作输入有1条、输出有8条被裁剪；额外保留完整502字符源码diff，SHA-256 `c7b7dd28c01a1e0ec7ad96bbe48fa799ef522405cec826103cd8ca7ffbe485f1`。历史和skill生成都能访问该最终diff。

首次目标调用前固定的输入：

| 文件 | SHA-256 |
| --- | --- |
| source_history.md | `99b379a42f335d5ceaa67f044a75168771faf49fb07cf488401925cb132b4b43` |
| feedback_card.md | `15ee5089784b377d913358ad0f99c8c90f5cf2815d6803ad26b7b13b0ef0c155` |
| generated_skill.md | `d2c38570577d4355a7ec25ee0b8c22deae3cc0207de8db3ab5f90fe8bbd8c7bc` |
| target_input_freeze.json | `bc185099415174ad0ad7bad1788b69c09ae4360a0e1fee70d3b29d7219e301a4` |

普通 skill 仅从源经验生成，1 POST /8,565 tokens、正常stop。目标历史虽收到169个行号，第3行预期2501字符、实际2034，逐字读取不完整；skill32/32行逐字相同。结果与读取、执行预算使用量共同变化，不能把该次差异全部归因于经验表示机制。

## 成本与证据定位

本任务对已完成 source、三个目标臂及一次skill形成，合计**60次转发POST、840,956 reported tokens，缓存555,628已包含其中**；限额拒绝不算转发调用，其记录保留在代理raw。无新增训练/judge。RethinkSkill的1 POST /2,447 tokens及其他来源单独记账，不混入此小计。

GB10 私有证据根：
`/home/testuser/wzh/research_evidence/agent_learning_20261030/astropy_agent_20261105/attempts/pilot_astropy_20261105/`

每个执行前缀为 `source__none__seed7201` 或 `target__{none,source_history,generated_skill}__seed7201`；按需读取该前缀的 `.completed.json`、`.auto_record.json`、`.evidence_check.json`、harness原始输出及独立评分。源码资格记录在同级来源根 `astropy_qualification_20261105/`，源经验及生成账在本attempt的 `source_experience/`。

| completed 文件前缀 | SHA-256 |
| --- | --- |
| source__none__seed7201 | `3080494ea572504fc62479554b54f5bcc84c29f55ba2aa6ad34bfe971955ffd2` |
| target__none__seed7201 | `c22613b0599f3ea6cb8d1e60819d1de5e4ef4335167f6dcac3abe5660fe060ce` |
| target__source_history__seed7201 | `50f9ce291db611baf95194cb7dbcbc81c387443aaaa1a5f0543e8477823e2570` |
| target__generated_skill__seed7201 | `de066af651c17b6f097d32c0610f79bd7cc747735e0ed5961a57e5e3d25ff49e` |

4个episode各10项文件绑定通过；这是文件来源检查，不是独立统计/方法审阅。源码BSD-3-Clause，数据来源许可沿资格记录保留。

## 判断与下一步

当前有“普通skill可在该次变化任务中完成修复”的积极线索，但一个任务对和seed不足以确认方法。先完成冻结结果卡臂，再核对调用预算、历史读取和实际代码行为；有可辨识机制后安排重复与不同来源，加入公开近邻及强简单对照。原工具缺失已经修复，不能将旧工具失败算成经验方法效果。
