# memory/STATE.md
更新: 2026-08-10（自主巡检轮 + Loop C differential 审计 + 修复批 A/B）

## 模式
守护模式。等用户: ① 批 :5050 重启窗口（载入审计修复批 A 端点加固，与 walkthrough 合并）② 亲自走场景 A walkthrough ③ 审看修正后 docx + 视频 → 发甲方 → B4 时钟启动。

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
- :5050 PID 3290556（00:2x 重启）: 建议映射端点+精确解析开关已载入；**审计批 A 加固未载入（需重启）**；health/embeddings=137/provider=local/route=on 已验证
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
