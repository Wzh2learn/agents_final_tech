# tmux 会话大盘点（2026-08-06 02:00, Loop D 夜间专项 T4）

方法: tmux ls 全量枚举 + 每 pane capture-pane -S -300 抓上下文 + ps/ss 交叉核对承载服务。
禁杀清单: graph-loop-b（红线）、opencode-serve（A0 sidecar）、承载 :8004/:8005（LM Studio 进程, 非 tmux）/ :8100 代理（nohup, 非 tmux）/ :5050 的 pane。

## 盘点结果

| 会话:窗口 | 用途 | 最后活动 | 判定 | 理由 |
|---|---|---|---|---|
| coding-jinrong:0 codex-idle | 交互式 codex CLI（停在空 prompt, 模型显示 gpt-5.6-terra medium） | 夜间无活动 | 保留+待审 | 交互式工具会话, 可能承载用户上下文; 启动告警暴露 skill 文件缺失（见吸收项 1） |
| coding-jinrong:1 tat-dqa | TAT-DQA 数据集下载/校验实验（已完结, 剩 shell 提示符） | 实验结束输出 | 吸收+关闭 | 工作已完结且结论已落盘（docs/datasets/tat-dqa-joint-v1-*）; 窗口仅剩空闲 shell, kill-window |
| coding-jinrong:2 m1harness | :5050 uvicorn（workers=2）运行窗 | 持续 | 保留 | 承载生产服务（禁杀清单） |
| graph-loop-b | Loop B 纯 bash 验证循环（1800s 周期） | 01:36 轮次 | 保留 | 红线, 信任锚点 |
| graph-loop-d | 旧 Loop D 主线程终端（7/30 创建） | pane 全空 | 关闭 | 空 shell, Loop D 已迁移桌面端; kill-session |
| opencode-serve | opencode serve sidecar :4096（A0） | 持续 | 保留 | A2 灰度依赖（禁杀清单） |

处置统计: 6 个 pane → 保留 4 / 吸收 1 / 关闭 2（tat-dqa 窗口 + graph-loop-d 会话）。

## 吸收到的最有价值信息（top 3）

1. **Skill 分发漂移（已修复）**: GB10 ~/.codex/skills/ 中 verification-before-completion 与 subagent-driven-development 目录存在但 SKILL.md 缺失（codex 启动告警捕获）——AGENTS.md 注册表声称已分发, 实际不可用。重跑 sync_skills.sh（幂等）修复, 四个 A 配属 skill SKILL.md 全部 OK。教训: sync 后应校验目的端 SKILL.md 存在, 不能只信源端检查。
2. **tat-dqa 数据集阻塞点**: tatdqa_docs_train.zip 被 Google Drive 消毒代理断连, 下载/校验工具链已完成（6 tests passing, manifest+datacard 就绪）, 待网络恢复后按 pane 记录的 download/validate 命令重试。
3. **opencode serve 未设口令**: 启动告警 OPENCODE_SERVER_PASSWORD 未设置; 仅监听 127.0.0.1, 当前阶段可接受, 列入安全台账（B 阶段/生产化前需设口令或保持 loopback 绑定）。

## 附注

- Loop B 01:36 轮次 overall=FAIL: API anchors 全 000——当时 :5050 正处于 T2 死锁僵尸窗口期, 属准确报警而非系统退化; 冻结 hash 校验本身 OK。其 "tests/ was modified" 警告仍是旧口径（全 tests/）, 与 T3 hook 收窄后口径不一致, Loop B 脚本为红线不改, 仅记录。
- :8004/:8005 模型服务为 LM Studio 子进程（ppid=1）, 不在 tmux 中; :8100 代理为 ssh nohup 进程。均不受本次清理影响。
