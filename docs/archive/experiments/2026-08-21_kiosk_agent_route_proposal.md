# kiosk agent 尝试关闭 — 最小实现路径方案（决策 A，待确认不动手）

状态: 待批 | 更新: 2026-08-21 22:55 | 类型: 方案评估（用户圈 A: 先评估出方案等确认）
背景: 两列口径冒烟坐实切换点后 186 次 agent 尝试全超时回落（100%）——kiosk QA 每条 46-50s 演示观感差; 准路恢复前关闭 kiosk 的 agent 尝试。红线: 不改 M2_OPENCODE_ROUTE 全局值。

## 1 现状链路（实测核查）

kiosk = demo_controller.py（Playwright 驱动真实 /m1 UI）+ loop_demo.py（脚本编排）; QA 由浏览器内 m1.js fetch /api/m2/ask 发出（m1.js:477-480, payload 仅 question/top_k/session_id）; 服务端 route_enabled() 逐请求读 M2_OPENCODE_ROUTE env（opencode_adapter.py:40-42, 进程级, 无法外部免重启变更）。

## 2 推荐方案 A1：per-request route 参数（服务端+前端+kiosk 三点）

1. **服务端**（src/web/routers/m2.py, ~6 行）：M2AskRequest 加可选字段 route: auto|direct|agent（默认 auto）; 端点判定改为 全局开关 on 且 route≠direct 且非 compare 意图 才走 agent; route=agent 而全局 off 时优雅按 auto 处理。**向后兼容**：字段可选、默认 auto=现行为, eval/浏览器/kiosk 零漂移; M2_OPENCODE_ROUTE 不动。
2. **前端**（src/web/static/m1.js, ~10 行）：QA 面板 top_k 旁加小选择器"链路: 系统默认/直连/验证链路", 值入 ask payload。StaticFiles 挂载（main.py:157）, **改 m1.js 免重启**。附带收益：快与准菜单从口头叙事落成可见 UI 控件——演示叙事"由甲方按场景选"有了落点。
3. **kiosk**（_rehearsal_files/, 本地进程）：demo_controller 加 op route 或 loop_demo QA 段前 select_option 置"直连"; kiosk 本地重启即生效, 无红线上触碰。
4. **生效前提：一次 :5050 重启窗口**（m2.py 变更所需）——向用户申请, 未批不动。
5. 准路恢复后（B4 两列口径出现稳定完成数）：kiosk 选择器回"系统默认", 验证链路样本重新积累。

## 3 备选与否决记录

- A2 kiosk 专用 flag（header 识别）：kiosk 走浏览器 UI, 注入 header 仍须改 m1.js——改动面与 A1 相同却无 UI 菜单收益, 不推荐;
- 零重启替代全部否决：① M2_OPENCODE_ROUTE 全局值禁改 ② env 进程级无法免重启变更 ③ Playwright page.route() 改请求体无服务端字段承接, 无意义。

## 4 边界与联动

- B4 两列口径天然兼容（只计实际发生的尝试）; kiosk 转直连后 agent 尝试数下降属预期, 判定分母随之变化, 报告已按 attempted/completed 输出;
- eval 套件不带 route 字段 → auto → 行为不变;
- UI 选择器成为演示资产 → 任务二改版"选择器同步"红线清单需纳入（台账已记）;
- 实施估时 ~30min 代码 + pytest 子集 + 冒烟, 唯一阻塞 = 重启窗口。