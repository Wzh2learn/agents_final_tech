# memory/STATE.md — 当前快照（覆写式）
快照: 2026-08-05 晚 | 写入: Loop D（embedding 切本地第一步 + A0 sidecar + 决策固化）

## 本轮产出
- ① embedding 切本地（用户拍板，不恢复 SILICONFLOW key）：
  - .env 加 LOCAL_EMBEDDING_MODEL_PATH=~/wzh/models/hf/qwen3-embedding-0.6b + DEVICE=cpu（同模型 drop-in，存量 764 向量零迁移；对齐实测 top-1 全对 0.564/0.587）
  - **MCP 链已生效**：knowledge_search vector=3 命中（复熙/嘉兴/OCR 三查询，正确来源 + product_name metadata）；BEFORE 复现 = ValueError 未找到 SILICONFLOW_API_KEY（与 e2e 文档降级记录一致）
  - 机制说明：utils/config_loader.py 的 load_dotenv() 使 .env 变量对 MCP stdio 进程即时生效；:5050 需重启载入（第二步，等用户批窗口）
  - QA 脚本层 14/15 前后不变：唯一失败 OCR meta-query 是内容碰撞（email_caitong.html 含"交易对账单"字样），与 embedding 层无关
- ② A0 sidecar PASS：opencode serve :4096 起于 tmux opencode-serve；GET /app + /session OK；POST /session + /message 完整往返 OK（gb10 qwen3.6-35b-a3b，15.5s，finish=stop）。注意：存量会话已 100 个，A1 需做会话清理
- 决策固化（memory/DECISIONS.md 四条 + docs/25 §3/§4 修订）：A 保底+B 目标；M1 热路径永不走 agent；LoRA 三条件门槛；B4 对等验收清单 16 项（功能/延迟/并发/回滚）已列 docs/25 §4.2 待用户过目
- P2: skills/m1-gap-triage/SKILL.md 草稿完成（未注册未 sync），等用户审阅

## 系统状态
- git: 本机与 GB10 对齐（本轮 docs/memory/skills 变更待 commit）
- 服务: :8004 up; :5050 up 未动（重启等用户批窗口）; :4096 opencode-serve up（新）; docker zhikuncode+pgvector; tmux coding-jinrong/graph-loop-b/graph-loop-d/opencode-serve
- pytest: 227 passed / 13 skipped（上轮基线，本轮未动代码）
- 红线: 冻结节点/API key/72B 未触碰; Loop B 未扰动

## 下一步（闸门顺序）
1. 用户审阅 m1-gap-triage skill 草稿 + B4 清单 → 注册/修订
2. A1 FastAPI 薄适配层（可继续）；A2 灰度开关等 embedding 第二步落地后开
3. :5050 重启窗口（用户确认后执行；重启后 /api/health/full + parse 冒烟 + 2 条 QA）
4. 遗留台账唯一入口: memory/THREADS.md