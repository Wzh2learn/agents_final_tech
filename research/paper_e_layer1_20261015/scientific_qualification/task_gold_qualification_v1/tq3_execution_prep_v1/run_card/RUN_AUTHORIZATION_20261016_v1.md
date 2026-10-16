# TQ-3 一次性开发性实验授权 — G1–G5 已裁决

日期：2026-10-16，Asia/Shanghai。

状态：AUTHORIZED_FOR_IMPLEMENTATION_AND_ONE_DEVELOPMENTAL_RUN。

授权来源：owner 在总规划师对话中明确要求“你来去填写吧，让他开启实验”。本文件由总规划师 AI 按该委托选择参数、记录授权范围；不是人工评审签名，不代表科学资格通过。

本文件对 RUN_CARD_v1.md 中 G1–G5、PREPARED_AWAITING_AUTHORIZATION、仅准备/零模型调用限制提供本次专项覆盖。其余科学边界继续有效。原运行卡、prompt_templates.md、52 文件材料 MANIFEST 和旧结果保持不变。此次仅开放 TQ-3 开发性运行，不开放后续独立面板、确认性 Layer-2、训练或论文 claim 修改。

## G1 — 固定模型、端点、版本和解码

- actor、B、C 全部使用同一个 GB10 现役本地模型，不自动换模型或端点。
- 主机：SSH alias `jinrong-dev`，GB10；工作目录 `/home/testuser/wzh/projects/agents_final_tech`。
- OpenAI-compatible base URL：`http://127.0.0.1:8004/v1`（在 GB10 上访问）。
- model ID：`Qwen3.6-35B-A3B-Q4_K_M.gguf`。
- 模型路径：`/home/testuser/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-GGUF/Qwen3.6-35B-A3B-Q4_K_M.gguf`。
- 模型大小：21166757728 bytes。
- 模型 SHA-256：`4ac6a06bce551257267f49ad2226f8671a22519ccc1a4dde9d5b433d1f2a410d`。
- 服务程序：`/home/testuser/.lmstudio/extensions/backends/llama.cpp-linux-arm64-nvidia-cuda13-2.16.0/llama-server`。
- 服务程序 SHA-256：`037e02419e78256ed4227af31fc0b2602ff04c670fb7ad4fa2429fafb03bd55d`。
- 本次实测 `/v1/models` 返回上述 model ID、owned_by=llamacpp；`/props` 返回上述 model_path、total_slots=4、n_ctx=65536。以上是本轮只读实测，不是根据旧状态推断。
- 固定请求参数：`temperature=0`，`top_p=1`，`seed=20261016`，`max_tokens=2048`，`stream=false`，`response_format={"type":"json_object"}`，`chat_template_kwargs={"enable_thinking":false}`。三组均相同；未指定的服务端默认项写入运行环境快照。seed 不意味着 GPU 计算绝对确定。
- 执行前重新核对两个文件 hash、model ID 和 model_path，保存最小服务元数据和 chat template 的 hash；不读取凭证文件或转储全部进程环境/命令行。身份不一致则停止，不自行换 pin。
- 第一个正式 actor 请求同时承担 API 参数兼容性检查，计入 40 次总预算；没有额外生成式 canary。若格式或关闭 thinking 参数被明确拒绝，保存原始 HTTP 结果并停机，不静默删参数后重跑。

## G2 — 硬预算

- 计划：12 actor + 12 B + 12 C = 36 个生成请求；A 是零模型调用的确定性简单规则基线。
- 全局最多 40 个生成请求尝试，包括失败、超时、兼容性请求和所有重试；每次发起网络请求之前持久化计数。
- 只允许基础设施错误重试，三组总计最多 4 次；内容错误、JSON 不合法、答案错误、输出截断均不得重试。HTTP 4xx 参数错误不属于可重试基础设施故障。
- 每个请求串行执行，并发=1；单请求超时=120 秒。不修改服务已有 slots/并发配置。
- 总 token 上限=400000，包含 prompt、completion、任何 reasoning token 与重试消耗。每请求 prompt 上限=8192，生成上限=2048。
- 请求前原子预留 10240 token；完成后仅用可信 usage 向下结算。超时、usage 缺失或无法判明 reasoning 是否已计入时保留完整预留。预留将超过总上限则不发请求。
- 构造完整消息后核验 prompt token 上限。允许使用同一服务的非生成 tokenize/apply-template 接口，每个拟生成请求最多各一次；计入独立 HTTP 操作账本，不冒充生成次数。必须包含 chat template 开销。无法可靠计数时，只可使用经离线核验的保守上界，否则停止；禁止截断题目/段落来挤进预算。
- 新增付费 API 费用上限=USD 0。仅使用现有本地服务；不购买算力，不访问外部模型，不安装新依赖，不加载/下载新权重。本地 token、时长照实记录，不把边际 API 费用为零说成算力成本为零。

## G3 — 时间与执行者

- 有效期：2026-10-16 本文件签发后至 2026-10-17 20:00，Asia/Shanghai。
- 允许启动时段：上述日期 09:00–18:30；从首个生成请求起至多 90 分钟，且必须在 20:00 前停止。一次运行，不能通过新建 run_id 重置窗口或预算。
- 该时间限制只约束生成实验窗口；实现和离线测试可先进行。材料和实现具备条件后直接开跑，不再为已填写的 G1–G5 询问 owner。
- operator：Loop D 负责落地、执行和交付；可以按既有分工委派 Loop A 实现与执行、Loop C 做一次范围内的离线独立复核。委派不新增模型实验预算，也不得接入新计费服务。
- 有效期内若未启动、超过窗口、服务身份变化、生产负载冲突或需重启服务，则保存具体阻塞，不自动延期/重启。
- 人员身份按真实 AI/harness 记录，owner 不被登记为已做标注或已签验收的人员。

## G4 — runner 实现及读写授权

- 授权实现本次专用轻量 runner、预算计数器、隔离加载、原始响应保存、结果汇总和必要定点测试；优先 Python 标准库与已有环境，不建设通用平台。
- 新代码放在 `tq3_execution_prep_v1/execution_v1/`；所有新运行材料放在 `tq3_execution_prep_v1/runs/<run_id>/`。不得覆盖现有 tools、输入、参考、评分文件、旧检查报告或旧 MANIFEST。
- 允许离线导入既有 tq3_scoring_entry.py。先完成预算上限、隔离、崩溃续跑、异常输出和真实评分入口的定点测试；不得触发默认 Loop B 的生产/API canary 或全库联网测试。
- 新 runner 自带实现版本/哈希、测试记录、最终请求参数、渲染后的 prompt 哈希和本授权文件哈希。已有材料 MANIFEST 的 52 个 pin 在运行前后各核对一次；新文件另建 execution/run manifest。
- 模型输入从模板白名单字段构造，不传文件路径、variant、original/perturbed 标记、注入元数据或答案键。task_id 使用同题统一 ID；配对状态仅留在调度器和结果侧。不把整个输入 JSON 原样追加进 prompt。
- actor 可见 question/table/paragraphs；B 可见同一输入与 actor 完整输出；C 仅可见同一输入与 actor 的最终 answer。评分参考与模型请求构造分离。
- A 仅依赖公开输入及 actor 输出；不得读取参考答案/隐藏题型来决定是否接受。若 numeric 类型无法从公开题意用冻结规则确定，记录 NOT_APPLICABLE，不借参考侧信息补判。
- 不更改 v1 prompt 文字，不做逐题调参或语义修复。输出仅允许确定性 JSON 解码；保存完整响应（含错误和 reasoning 字段，如有），不调用模型修 JSON。actor 无有效 answer 时 B/C 标记 BLOCKED_NO_VALID_ACTOR，并跳过对应请求；不拿参考答案填空。
- 固定调度：actor 按 Q02/Q03/Q04/Q05/Q10/Q12，各 original 后 perturbed；完成 actor 阶段后再进行 B/C，每份输出的顺序交替 B→C、C→B。所有请求独立上下文，不把上一题输出带入下一题。
- 禁止重启或修改现役模型服务、:5050、数据库、全局路由、技能库或其他研究面板。不得挪用 WP-2/TAT-DQA 的运行授权或停止状态。

## G5 — 环境与产物

- 正式运行环境：GB10 当前仓库，现有 Python 3.12 环境。执行前核对版本；若现有环境不能满足要求则报告，不安装或切换公共运行环境。
- endpoint 为本地现役无新增凭证服务。禁止读取 ~/.claude/settings.json、~/.codex/auth.json、.env 或任何凭证值；若服务意外要求认证，停止，不寻找其他密钥。
- GB10 输出根：`/home/testuser/wzh/projects/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/tq3_execution_prep_v1/runs/<run_id>/`。
- 本地镜像输出根：`D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/tq3_execution_prep_v1/runs/<run_id>/`。
- 允许 SSH/SCP 传送本次授权、runner、必要公开材料与运行结果；私有来源、凭证、模型权重不传送。保留两端已有工作区脏文件。同步成功后记录实际校验；不能把本地存在称为三端同步。
- 不将生成数据集、原始运行输出或日志提交 Git；代码、授权和摘要可由 Loop D 按仓库既有规则做范围明确的提交。结果保留在两端本地并用 manifest 定位，不要求为了“三方 git 对齐”把原始数据推到 origin。

## 解释修订与交付

- 原模板的 C 在同一次请求中看到了候选答案。因此 C 是“同模型、独立上下文、不提供 actor 证据链的核验”，不是答案盲态独立解题，也不是独立模型。此次保留模板作开发性试验；禁止把 C 当作已经验证的路径独立机制。
- B/C 差异同时包含证据链暴露和指令差异；本轮不单独归因于路径独立性。A 是简单规则基线，不代表已经接入原生产 checker。
- 主要参考匹配率以 12 个预定输入为分母；另列有效输出条件下的匹配率和有效输出覆盖率，不能将两个分母混用。单位和格式按已固定评分器解释，不因 prompt 的示例临时更改评分规则。
- 报告 A/B/C 在参考 MATCH/NO_MATCH/INVALID/BLOCKED 各层的 accept/alarm/abstain/invalid/skipped 数；无相应样本时比率写 NOT_ESTIMABLE，不填 0。
- 配对单位=题目/表，共 6 组，不是 12 个独立样本。旧面板、AI 诊断、官方参考均不因此获得独立人工 gold 资格。
- system_outcome 必须从真实运行得到；scientific_gold_validity 仍为 NOT_ESTABLISHED。无差异、无错误、格式失败或部分运行都是合法结局，不为好看结果补跑。
- 交付 runs/<run_id>/RECEIPT.json、MODEL_PIN.json、请求账本、原始响应、A/B/C 决策、逐题评分、RESULTS.json、SUMMARY.md 和可复核 manifest；入口汇报写 execution_v1/TQ3_RUN_RETURN.md，列出所有失败和偏差。
- 连续两次连接失败、出现模型身份漂移、预算达到上限、输入 pin 漂移/参考泄漏或窗口结束时停止。崩溃后仅可在同一窗口、同一 run_id 和原计数账本下继续尚未执行项；任何已发请求不重置或删除。
- 完成后只做一次聚焦结果复核，说明实际研究信号及下一步是否值得；不启动新面板，不修订冻结稿，不公开投稿。

## 本授权签发时的实际操作记录

- 总规划师进行了 GB10 两次非生成 HTTP 读取：GET /v1/models、GET /props；模型文件和服务程序只读 SHA-256 计算。
- 最初一次 SSH Python 引号错误在发出 HTTP 请求前失败，随后使用 stdin 脚本完成上述读取。
- 模型生成调用=0；实验尚未启动。本文件解除本次 G1–G5 的 owner 决策缺项，执行前技术断言由 Loop D 完成，不伪造它们已经通过。
