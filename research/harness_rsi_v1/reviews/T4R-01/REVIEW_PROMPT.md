# Loop C 独立评审任务 T4R-01：harness_rsi_v1 T4 v2 R适配器与基线（本卡唯一 1 次 Loop C 评审名额）

你是在 GB10 上运行的 Loop C（独立质量审计层）。只做独立评审；不修改仓库内任何文件（仓库与被审包均只读）、不 git 写、不联网、不调模型端点/生产/数据库、不进入 T5。输出只写 stdout（三块标记，见文末）。

## 背景
- R 线获 owner 授权（至 M1）；协议 FROZEN（`282f5213…`）；T1/T2/T3 已验收（T1I-03、T2R-01、T3R-01 均 ACCEPTED、blocking=0）。
- **T4 v1（`runs/T4/20261014T174628Z_2cc25c92`）不可提交**：其 `fixtures/summary/effect_mismatch.md` 是"故意失配"的仓库内收据夹具，被仓库 pre-commit 收据守卫（`scripts/graph/hooks/summary_recompute_guard.py`）硬拒绝（无夹具豁免机制；见 `tests/test_guard_sentinels.py` 头部 Decision 34：仓库内落盘夹具必须全部通过复算，失配变体须 runtime 派生）。v1 保留在两机磁盘作为前史，不进 git。
- **被审对象 = T4 v2**：`research/harness_rsi_v1/runs/T4/20261014T184810Z_c9dcfe0e/`（65 文件；已提交 `579a8ca`）。v1 锚点（v2.supersedes 中引用，应与磁盘实测一致）：manifest sha256 `8ef43aec8974ca4bf94931df14c138620ae02a9a9114c78138cf2c3f0dfb48af`、receipt sha256 `f270cab1177dc293ca0b94c21132e3dcdc70f2514e3e5cf4a71fc030e7691dbd`。
- v2 变更动机 = 守卫合规化 + 由此的全量再生成；声称画像与 v1 零差异（detected 6 / missed 2 / not_applicable 2 / unverified 6）；11 适用组合两轮回放一致；22 次适配器调用；零外部调用。

## 必读（只读）
`cards/T4.md`、`contracts/{protocol,authority_map,execution_policy,budget_profiles,schemas}.json`、`evaluation/reliability_spec.md`、`docs/governance/FORMAL_EXPERIMENT_PREFLIGHT_V1.md`（级别定义）；v2 run 全文（先读 receipt.json、summary.md、baseline.json、baseline_recipe.json、adapters/README.md，再读 adapters/、fixtures/、scratch/）；v1 run 在磁盘上可只读对照（未提交，勿依赖其存在性做断言以外的事）。

## 工具约束与已知环境事实（先读，避免撞墙）
- 命令白名单不含 git、mkdir、cp、mv、rm、chmod；git 命令会被拒——用双方法替代（字节派生 git blob SHA-1 + `.git/index` 解析）；被拒命令如实记录。
- 需要写 scratch 时：只用 `python3` 调用脚本，scratch/output 放仓库外（例：`/home/testuser/wzh/loop_runs/t4r01_recheck_a/`）；不得在被审 run 目录或仓库内创建/修改任何文件；如实披露全部仓库外路径。
- 运行 .sh 适配器可用 `python3 -c 'import subprocess; ...'` 包装（bash 本身不在白名单）。

## 必须独立复算（记录命令与退出码）
1. **计数与哈希**：v2 run 恰 65 文件；`artifacts_manifest` 64 条（自不含）逐条 SHA-256/字节实算一致；磁盘无遗漏、无多余。
2. **input_bindings 等**：卡片 6 输入 + PREFLIGHT + T1/T3/T2 依赖逐条双方法复算；`protocol_freeze_check` 与 FROZEN 值一致；依赖验收事实（T1I-03、T3R-01 的 decision/blocking）。
3. **守卫合规实弹测试（核心）**：
   a. 对 v2 包内**全部 9 个 `.md`** 逐个运行 `python3 scripts/graph/hooks/summary_recompute_guard.py check <path>`——**全部 rc=0**（7 个含收据块者复算通过，2 个无块者跳过）；与 g1 矩阵对照。
   b. **篡改正控制**：把 `fixtures/summary/effect_match.md` 与 `derive_case_mismatch.py` 复制到你自己的 scratch，运行派生脚本生成失配版，再对派生件运行守卫——**必须 rc≠0**（失配被检出）；核对派生 diff 恰为指导的 claim 翻转（request_count 4→3）。
   c. **g2 复核**：v2 包内不存在任何"失败收据块"的 `.md`；派生件仅瞬态存在于运行期（脚本把输出写到调用方指定路径；留证 = 输出日志 + 派生脚本）。
   d. **v1 根因复核**：对 v1 的 `fixtures/summary/effect_mismatch.md` 运行守卫——应 rc≠0（佐证 v1 阻断原因）；实测 v1 manifest/receipt 的 sha256，与 v2.supersedes 锚点一致。
4. **回放实跑**：用 v2 的 adapters（按其 README 用法；输出到你自己的 scratch）重跑全部 11 个适用组合 × 两遍 → 逐项与 `baseline.json` 记录的 exit code/判定对照；抽查 22 条证据路径存在性；至少精读 INC-12/INC-13 的 `*_summary_derive` 日志与 g1/g2/g3 三个日志，确认派生失配被守卫判 FAIL、且无持久化失配件。
5. **A1/A2/A3/A-common 逐条 + 级别标注**：A1（模型/环境/案例/评价器身份齐全：模型=NONE、环境、T1 案例三个文件的 blob id、工具含被排除项与理由、评价器=T2 绑定）；A2（同输入两轮判定一致；扫描 baseline.json 确认**不存在裸 PASS**，所有 PASS 带级别+范围）；A3（无旧实验输出、无网络、无现役 Loop B、适配器副作用审计结论）。
6. **对抗面**：适配器只读性（抽查一个适配器运行前后仓库工件哈希不变）；**不扩张旧检查器作用域**（适配器仅路由+结构化，无重实现——读适配器源码抽查）；被排除工具清单（loop_b_verify.sh 必须排除、formal_experiment_preflight.py 未运行且理由=无获准 FinManifest 且不泛化专用资格）成立；6 个 unverified + 2 个 not_applicable 的理由抽查 2–3 项是否精确、无可离线复盘却漏标的组合；两个合法对照无误拦；usage 零声明与 22 次适配器调用计数自洽；写入边界（mtime/porcelain 扫描）；6 条 repair 记录与证据一致（含 runner_errors/ 里 rc=127 的 setup 失败日志）。
7. **披露准确性**：supersedes 字段、TASK_PROMPT ↔ 实际任务文本、LOCAL/B0/工程范围限定措辞。

## 反证重点
- 守卫合规是否以"降级验证面"换得（删案例/放宽检查/丢证据）？对照 v1↔v2 差异表（G3）独立重算。
- 派生流程是否真的在运行期执行（而不是"抄一遍 v1 的失败输出"）？用你自己的派生重跑验证。
- baseline.json 的 detected/missed/not_applicable/unverified 标签与 22 条实跑证据是否一一对应、无粉饰。

## 输出（仅 stdout；三块标记；块间不要多余分隔符）
=== FILE: REVIEW.md ===
（Markdown：范围与方法；逐项结果（含命令/退出码证据）；实跑复算证据；BLOCKING/ADVISORY 发现（ADVISORY 附升级条件）；FACT/INFERENCE/UNVERIFIED 分离；对 T4 v2 的判定与理由）
=== FILE: review_receipt.json ===
（JSON：review_id="T4R-01"；task_id="T4"；reviewer/runtime；reviewed_artifact_sha256（v2 关键文件 ≥12 件：receipt/summary/baseline/baseline_recipe/artifacts_manifest/5 个适配器/derive 脚本/base 夹具等，含 sha256 与字节）；recomputed（计数/manifest/bindings/freeze/守卫矩阵/篡改正控制/回放对照/披露核对/写入边界）；checks；calls（review_session_calls=1；network/services/db/model=0；token UNRESOLVED；本地复跑命令计数如实）；refused_commands；reviewer_side_effects_disclosed；unverified；verdict）
=== FILE: ACCEPTANCE_PROPOSAL.json ===
（JSON：decision ∈ {ACCEPTED, REJECTED, PENDING_HUMAN_REVIEW}；blocking_items；advisory_items；scope；justification；dissent；next_steps）
=== END ===

重申：只写提案；registry/state 由收口者更新；不得进入 T5；不得修改任何已提交或被审包文件。
