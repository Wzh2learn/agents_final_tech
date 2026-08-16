# memory/STATE.md
更新: 2026-08-16 深夜（模型升级后半场 S1-S5 收口 + 甲方演示就绪）

## 模式
守护模式。**路线 A 双模型已落地**（S4, 配置层 only, 零重启, :5050 代码零改动）; 路线 B 35B-A3B 受阻上游（权重未发布）, routeb-watch 每 10min 自动探测、发布即自动下载。docs/23 已发送甲方（08-12）; 导师包已发送（08-16, 用户亲发）。等: ① 用户 :5050 重启窗口（超时预算重议 = agent 路真实承载的唯一解锁项）② 甲方首轮反馈 ③ 导师反馈。缓至甲方反馈: 任务二 B 一期 / 场景 B / _cleanup_backup 删除 / Qoder PAT。夜间不自行开新战线。

## Git
- HEAD: ca85316 → +本收口 commit（治理规则: STATE 覆写绑定收口 commit; hash 见最终汇报）
- 三方对齐: GB10 = GitHub = 本机 = ca85316（08-16 23:30 核验; 本机自 4f8dd17 ff merge）
- 冻结工件未动: 甲方版 docx bc3785cb / 导师版 docx 929a8c65（六次冻结）/ 冻结节点三件

## 本轮战绩（模型升级后半场 S1-S5, 22:00 后全量执行）
- S1 沉淀六项: vLLM 启动 SOP（FM1-FM5 + 通道台账 + 内存算术）/ DECISIONS 思考控制契约（reasoning_effort low·medium·xhigh 唯一旋钮; high 非法; thinking_budget≡xhigh）/ NF+benchmark 脚本 endpoint 参数化 / Loop B 误报模式备案
- S2 梳理: docs/32 数字与工件核对零漂移; §2.4 补官方 pairing 依据 + 拍板记录 + B 门槛
- S3 路线 B: **受阻入账** — 35B-A3B 权重双通道未发布（HF resolve 404 ×6 镜像源 / ModelScope Qwen org 仅 27B 系）; routeb-watch（tmux）每 10min 探测、发布即自动下载; 探针预案就绪（:8007 + SOP 复用）
- S4 路线 A 落地（ca85316）: opencode gb10v provider → thinking_inject_proxy(:8008) → :8006 27B; m2-qa + evidence-verifier 切 27B; judge → :8006（显式 enable_thinking=false, 与基线 4.94/5.0 对等）; M1 热路径（m1-extraction/tabular-*）留 :8004 A3B（红线）; :5050 零代码改动零重启
- FM5 沉淀: vLLM 0.27 reasoning-parser 键控请求级显式 enable_thinking（服务端模板不能替代; jinja 渲染逐字节一致反证）→ scripts/thinking_inject_proxy.py + SOP FM5 + CHAT_TEMPLATE 挂载
- 六步验证全 ✓: health/full（137/local/healthy）/ parse 15ms 确定性 / QA 2 条（OCR meta-query + 掩码值保留, 经回落直连）/ compare 嘉兴民安 2 持仓 / route=on+18s / agent 接线 modelID=qwen38-27b-fp8 坐实
- 如实口径: agent 路 27B 实测 29.6s/72.1s/>120s 一次（thinking off, dense 多轮累积）, 慢于 A3B 39-55s → 18s 预算继续全回落, 用户可见行为与切换前一致（零回归）
- eval 基线 v2 定稿: 确定性 16/16 + NF 0/9 + judge 5.0×4 @:8006; M1 门禁 PASS
- 甲方演示 UI（纯前端零重启）: M2 问题清单 chips ×11（含拒答题）+ 字段规则只读总览 modal（674 行映射表溯源）; playwright 截图验证过
- B4: asks≥513; 双模型切换点标记 08-16 ~23:35, 统计前后分段

## 服务
- :5050 UP（route=on, OPENCODE_ASK_TIMEOUT=18 模块级, provider=local, embeddings=137; tmux coding-jinrong）
- :8004 A3B UP 快路+视觉（旧栈 GGUF 保留 → 08-17 18:00 回滚窗口）; :8005 14B UP; :8100 代理 UP; :15432 PG UP
- :8006 vLLM 27B UP（tmux vllserve; agent 验证链/judge/深度问答）
- :8008 thinking-inject proxy UP（tmux thinking-proxy）; :4096 sidecar UP（tmux opencode-serve）
- :8007 down（路线 B 探针预留）; routeb-watch tmux 运行中
- Loop B: 22:41 FAIL→PASS（head=4f8dd17）; 禁杀清单 + vllserve/thinking-proxy/routeb-watch
- known risk: PG idle 连接泄漏 ~1/h（Loop B 周期跑遗留, 清理 one-liner 在 THREADS）

## 质量基线
- pytest 336 passed / 13 skipped（08-16 深夜收口复跑, 101.9s）; docs_lint 0/0; sync_skills --check 21/21; 冻结节点 PASS
- eval v2（双模型口径）: 确定性 16/16 / NF 0/9 / judge 5.0×4 @:8006
- B4: 回滚 10-23s 实测; route=on 当前 100% 于 18s 内回落直连（用户可见 ≈ 直连行为 + 18s 开销）
- 演示资产就绪: demo_v2.mp4（docs/experiments/2026-08-15_demo_video_v2/）+ 甲方版 docx bc3785cb

## 下一步（等用户/甲方/导师）
1. **用户重启窗口拍板**: OPENCODE_ASK_TIMEOUT 重议（agent 路才能真实承载）; 临时甲方演示第一动作 = M2_OPENCODE_ROUTE=off（回滚 23s 实测, 直连 2-5s/题）
2. 甲方首轮反馈 → 解锁缓办清单 + A2 延迟修复优先级
3. 导师反馈 → docs/31/视频微调或科研线推进（NLPCC/CCIR 截稿日仍 pending 人工查）
4. routeb-watch: 权重发布 → 自动下载 → S3 三问探针（:8007）→ 用户二次拍板
5. 菜单待拍板（存量）: Docling NCAMC / OpenAI4S 科研线接入 / docs/28 #2→#1→#4
6. apply 候选等窗口: 累计净值建议 + 产品份额①建议（走 SOP: 回归门禁 + delta）
