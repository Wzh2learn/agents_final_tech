# memory/STATE.md
更新: 2026-08-10（自主巡检轮 + Loop C differential 审计 + 修复批 A/B）

## 模式
守护模式（walkthrough 就绪）。:5050 已重启载入批 A 加固并验证全过；等用户开浏览器走场景 A walkthrough。

## Git
- HEAD: 见 git log（三方对齐，本轮 push 后同步）
- 本轮 commit 链: 395f85b (审计修复批A: F1/F2/F3/F4/F5/F10/F11 +3 tests) → 7173dce (审计修复批B: F18/F19 数字校正 + docx 重生成) → 台账 commit
- 前置: e715dc5 (schema_suggestions 结构规范化)

## 重要更正（对外数字）
- 华泰紫金一轮命中率 **35.7%**（非 42.9%，后者系 LU 样本数字张冠李戴）→ 二轮 100%
- 国金 HTML 一轮 **70%**（非 80%）→ 二轮 90%
- TraFax 逐表 [50/81.8/63.6]→[50/81.8/81.8]，样本均值 65.1→71.2
- 结构化产出 31 表（现行基线；一轮 30）
- docs/23 + docx 已按工件校正重生成（发送以此版为准）

## 服务
- :5050 PID 4086502（2026-08-11 00:07 重启）: 建议映射端点 + 精确解析开关 + 审计批 A 加固全部载入; health/embeddings=137/provider=local/route=on 验证 PASS
- ⚠ agent 路延迟退化 39-55s（口径 15-20s）, 18s 超时优雅回落直连正常工作; 排查项见 THREADS; 演示以直连路为主
- :4096/:8004/:8005/:8100 up; :8007 down (VERIFIED-CLOSED); docker zhikunCode+pgvector; Loop B 未扰动

## 质量基线
- pytest: 313 passed / 13 skipped / 0 failed（+3 审计守卫测试）
- scenario1 门禁: 15/15 PASS（quick 12 pass/3 skip OCR）
- Loop C differential: CONDITIONAL → 修复批 A/B 已落，待重启后转 ACCEPTED 复核
- 冻结节点 md5 双 OK

## 下一步（等用户）
1. :5050 重启窗口（批 A 加固生效）→ 用户走场景 A walkthrough（样本已在 D:\EdgeDownload\sample_20260506_233222LU.pdf）
2. 用户审看修正版 docx + jinrong_demo.mp4（均在本地）→ 发甲方 → B4 时钟启动
3. 场景 B 排期等 walkthrough 反馈；无新队列不开新战线
