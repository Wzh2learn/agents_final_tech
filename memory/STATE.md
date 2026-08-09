# memory/STATE.md
更新: 2026-08-10（:5050 重启载入 T4 端点, 六步验证全过）

## 模式
守护模式（等用户亲自走场景 A walkthrough; 之后: 用户发送 docs/23 → B4 观察时钟启动; 场景 B 排期等 walkthrough 反馈）。

## Git
- HEAD: 16a3572（本地 = GB10 = GitHub 三方对齐）
- 本轮 commit 链: fc08f13 (T1+T2) → 218122f (T3 视频) → 7b27d50 (T4 场景A) → 02b768e (hygiene) → f970642 (T5 对账+ledger) → 16a3572 (精确解析开关)

## 服务
- :5050 FastAPI（PID 3290556, uvicorn --workers 2, **2026-08-10 经批准重启**）:
  - 已载入: 建议映射三端点 (/api/m1/schema-suggestions GET/apply/reject, 实测 200 + 21 pending) + 精确解析开关 (?llm_fallback=0) + 此前全部加固
  - 验证: health overall=healthy, embeddings=137, provider=local; parse 嘉合#0 93.8% 基线一致; QA route=opencode 18s 带引用; M2_OPENCODE_ROUTE=on 未动（回滚 23s 已实测）
- :4096 OpenCode sidecar / :8004 35B / :8005 14B / :8100 proxy
- :8007 VLM 未运行（VERIFIED-CLOSED）
- docker: zhikunCode + pgvector_15432; Loop B 常驻未扰动

## 质量基线
- pytest: 310 passed / 13 skipped / 0 failed
- M2 eval: 确定性 16/16 + judge 四维 5.0; scenario1 门禁 15/15 PASS
- 冻结节点未触碰

## 场景 A walkthrough 备忘（给用户）
- 样本: sample_20260506_233222LU.pdf（精确模式当前 75/75/42.9%, 未映射列与面板 21 条候选对应）
- 路径: GB10 ~/wzh/m1_samples/sample_20260506_233222LU.pdf（需 scp 到本机上传）
- 门禁反馈: 成功=绿提示(应用条数+新增同义词数), 失败=红提示(409 detail 含 rolled back)

## 下一步（等用户）
1. 用户走场景 A walkthrough → 反馈后定场景 B 排期
2. 用户审看 demo.mp4 + docx → 发送甲方 → B4 时钟启动
3. 无新队列前不开新战线
