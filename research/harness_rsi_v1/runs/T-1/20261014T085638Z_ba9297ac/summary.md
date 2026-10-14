# T-1 规划物化复核 v2（修正重跑）
- task: T-1 | run_id: 20261014T085638Z_ba9297ac | supersedes: 20261014T072826Z_6f19a394 | 时间(UTC): 2026-10-14T08:56:38Z
- 结论: v1 的实质结论可复用；按 T1R-01 评审完成修正重跑。检查 **22 项 = 15 PASS + 4 INFO + 3 FAIL**。
- 修正: F2 已修（candidates/.gitkeep，manifest 53/52 已同步）；F3/F4/F5 已修（本包计数 13 项权威、16/2 口径见下、U04 分类口径一致、矩阵 outputs 约定已注明）；F6 已补（C17 写入边界、C18 R/C/S+人工门）。
- F1 复核（三域口径）: 13/13 pin = 本地工作树原始字节（可复现）；13/13 repo blob 双边一致（**无内容漂移**）；6/13 GB10 工作树原始字节与 pin 不同 = EOL/检出表示差异。=> 记 RUN-R05，T0 重钉 canonical(blob) 域；不记 STALE_INPUT。
- 评审仲裁: 接受 F2–F6；F1 接受"口径/标注"内核，**不接受**"回填/自相循环"与".gitattributes 普适权威"两点（证据见 C11 三域表）；详见 receipt.adjudication。
- 证据: 包内 64 文件逐件哈希在册；两轮原文与 provenance 一致；状态授权全关；依赖无环；预算 BR 4/3、BC 66/8、BS 106/4、SHADOW 6/2、META 12/2 一致；INDEX 1 入口；GB10 HEAD=d6f456704b53bd954278962cc28aadf56b9cd935、仅 logs 脏。
- 未验证面: 未触碰模型端点/服务/数据库；Loop C 内部 token 用量 UNRESOLVED；两条 Claude Code 注入防护命令仍需等价写法（见 C19）。
- 下一步: 交 GB10 Loop C 对 v2 复审（reviews/T1R-02）；通过后由收口者据已审事件更新 registry/state；T0 仍待授权动作。
