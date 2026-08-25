# memory/STATE.md
更新: 2026-08-26 00:15（夜间冲刺收口: demo_v3 视频 + docs/31 v2 + talk track v2 + judge 归因 + E1-E6 已完成）

## 模式
守护模式。**08-26 上午 = 用户亲发导师包**（三件: 文档 md/docx + demo_v3.mp4; 发送清单 = docs/experiments/2026-08-25_send_checklist.md, 含建议发送一句话）。主线程零对外。
判定一页纸 v2 仍待圈选（规则 0/A/B/C/D/E 已评估: 超时(a) CLOSED / T1 维持 / FK 单件窗等批 / PSO blocked 根因坐实）。
其余等拍板: 甲方首轮反馈 / 专利导师五项定夺 / FK 水位线单件窗 / M4 减 step（与 context 瘦身组合, 含孤儿轨迹治理 F-J3）。

## 夜间冲刺成果（08-25 23:10 - 08-26 00:15）
- demo_v3.mp4: 3:22, 1080p, Yunyang 配音 11 段; 质量门过（流齐全 / 4 帧非空 / 音量 -27.7dB）; 视频不入 git（v2 先例）
- docs/31 v2（md+docx, docx 黑话扫描零命中, judge 四维未引用）
- talk track v2（选题变更证据: route=on 下普通题全走深度通道, 快路段=持仓对比 11ms）
- judge 超时归因定论: NF agent 路 + 孤儿轨迹自饱和 :8006 → 16×90s; 菜单校准 F-J1/F-J2/F-J3（F-J3=孤儿治理=M4-a, 与准路洼地同根因）
- B4 视频窗口 23:19-23:51 登记（干净段统计剔除）

## Git
- HEAD: 冲刺收口 commit; 三方对齐（本机 pull --ff-only）
- 本轮资产: 31 v2 md+docx+builder / talk track v2 / judge triage / send_checklist / v3 脚本四件（record/tts/cards/assemble）/ steps.md / INDEX+THREADS+dispatch 入账

## B4（分段, 两列口径 尝试/完成 写全名）
- 池修复后段注册窗 3929→3988 = 59/2 = 3.4%（规则评估口径）; 滚动累计见 checkpoint
- 视频窗口 23:19-23:51 剔除（dispatch #VIDEO-V3-WINDOW-START/END）

## 服务
- :5050 UP（PID 3153034, route=on timeout=45 未动）; :8004/:8006/:8008 UP; :8007 空闲; :15432 PG UP
- Loop B 30min 周期运行; kiosk 关闭; crontab 空

## 质量基线
- eval: 确定性 16/16 + NF 0/9（W3）; judge 腿作废待重跑（协议加隔离闸, 见 triage）
- 视频质量门: 3:22/1080p30/aac/4 帧非空/配音在位
