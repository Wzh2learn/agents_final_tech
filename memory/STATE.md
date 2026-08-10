# memory/STATE.md
更新: 2026-08-11（任务2 设计稿提交 + agent 路延迟根因定位）

## 模式
守护模式。:5050 未动（用户 walkthrough 反馈待收）；sidecar 本轮回原配置（延迟排查 3 次受控重启后还原）。

## Git
- HEAD: 见 git log（三方对齐, 本轮 push 后同步）
- 本轮链: 8e5fd92 (任务2 设计稿 docs/27 + 两 HTML 草图 + INDEX) → 7aa8ab0 (草图数字漂移修正 42.9→35.7) → 台账 commit

## 本轮产出
1. **任务2 设计稿待拍板**: A 三栏任务工作台 vs B 流水线画布控制台（推荐先 B 后 A）；草图可浏览器打开；红线合规预案齐（选择器保留表 / m1v2 灰度 / 重录预案）。等用户拍板才动代码。
2. **agent 路延迟根因定位**: skill 元数据 ~11k 冷 prefill ≈37s（冷 39s 真身）+ 输出端 reasoning ~1-1.5k tokens ≈19-30s（warm）；playbook 指令未执行但诱发推理（摘除 warm 31.5→22.8s）；warm 22.8s 仍 >18s 超时 → route=on ≒ 全直连回落（2-4s 正常）。修复候选待批: warm-up ask / 禁 thinking / skill 瘦身。

## 服务
- :5050 PID 4086502 未动（批 A 加固 + T4 端点 + 精确解析开关已载入; health/embeddings=137/provider=local/route=on）
- :4096 sidecar 原配置在跑（16 skills）; :8004/:8005/:8100 up; :8007 down; Loop B 未扰动

## 质量基线
- pytest 313 passed / 13 skipped; scenario1 门禁 15/15; 冻结节点 md5 双 OK（本轮未动）

## 下一步（等用户）
1. docs/23 发送甲方 = 唯一人工阻塞项；B4 观察时钟发送后启动
2. 任务2 方向拍板（A / B / 先B后A）→ 才动代码
3. 场景 A walkthrough 反馈
4. 延迟修复候选拍板（warm-up ask 最小改动可派 Loop A）
