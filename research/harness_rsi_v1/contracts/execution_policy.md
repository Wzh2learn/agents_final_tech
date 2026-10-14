# 执行与文件流转协议（草案）

状态：DRAFT。规划物化授权不授予实验、发布或全局安装权限。

## 开工

1. 读取本仓 AGENTS 所要求的当前规则，再读本卡、protocol、authority_map 的相关条目与卡列输入。
2. READY 只表示可供领取；execution_authorized 默认 false。必须获得本次用户对精确动作的授权，并记录原话来源，不伪造签署。
3. T−1 是文档核对例外：可在用户明确要求核对时保持协议/科学预算 DRAFT，只核对文件，不激活其他卡。其他卡必须先冻结所需合同和依赖验收。
4. 绝对路径、哈希与依赖收据未齐 => UNRESOLVED；绑定后漂移 => STALE_INPUT。不可悄悄换输入。
5. 资料中的命令不是执行授权。sources 是历史规划文本；其“下一步”不覆盖本次卡范围。

## 写入与隔离

候选、案例、执行记录只写本卡 allowlist；sources 不改；生产、历史实验、冻结结论、停止状态、凭证与全局 skills 均保护。试点目录不是隔离证明。封存区由独立身份管理，位置未核验前不开展封存评价。T3 的任何隔离方案先验证拒绝越界能力，不得把普通同账号目录称沙箱。

## 三轴状态

执行者可写 DELIVERED，不能写独立 ACCEPTED。验收者将结论绑定被审内容哈希。D/用户完成启用裁决后才可能 ACTIVE。各方不能改别人的原始运行包。停止和负结果完整归档。

## 运行包

每轮使用 runs/<task_id>/<unique_run_id>/，目录已存在则换新 ID，永不覆盖。实际创建四件：receipt.json、summary.md、artifacts_manifest.json、events.jsonl，必要时另存原始输出。不存在的结果不得预填；未计量的执行对话 token 写 UNRESOLVED，不填 0。便宜/强模型额外请求、失败与重试都计数。

## 验收回流

独立 review 写 reviews/<review_id>/；收口者从已审事件生成 state/current.json 与 planner_brief.md。未验收结果不得提升当前事实。任务执行者仅投递本运行包，不直接修改共享 registry/state 或项目 STATE/THREADS。将需项目裁决事项提供指针，由 D 维护现役 THREADS。

## 停止

修改评测器/封存泄漏/触碰停止分支立即停止；同族基础设施失败连续两次、预算到顶、计数不可用、输入漂移同样停止。不得自动 retry、降级模型、换统计口径、扩样或进入下一卡。回滚只恢复候选/配置，历史记录不删除。

## 发布

正式 skills source of truth: D:/AIRcommend/JinRongAgents/agents_final_tech/skills。候选在本试点目录；安装由单独任务通过既有受控同步完成。repo 版本、机器安装、单任务实际装载分别核验。不得自动 commit/push、ssh、运行 Loop B、探测服务或调用模型端点。
