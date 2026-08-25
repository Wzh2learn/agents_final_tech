
## GATE run 2026-08-25 00:16:01 (rearm #0)
recent_sessions_12min=5
IDLE NOT REACHED (recent=5) -> re-armed at 23 00 25 08

## GATE run 2026-08-25 00:28:02 (rearm #1)
recent_sessions_12min=0
pg_stat_pre_gate=1|0 | warn_T0=219 fallback_T0=0
gate_answer_head: {"answer":"嘉兴民安的资金余额为 3,508.55 元。\n出处: 样本=sample_jiaxing_minan_20231031.pdf, 表=p0_table_2","sources":[{"sample_id":"sample_jiaxing_minan_20231031.pdf","table_name":"p0_table_2","score":0.7889,"text":"样本: sample_jiaxing_minan_20231031.pdf\n表: p0_table_2 (资金资产汇总)\n字段: 资产账户=8802****, 资金余额=3508.55, 资金可用=3508.55, 资产市
warn_gate=219 fallback_gate=0 recovered_total=0 | pg_stat_post=6|5
GATE_OK=1
VERDICT: GATE_PASS 2026-08-25 00:28:51
## GATE END 2026-08-25 00:28:51

## GATE run 2026-08-25 00:35:01 (rearm #0)
recent_sessions_12min=5
IDLE NOT REACHED (recent=5) -> re-armed at 42 00 25 08

## Loop B 周期状态 + canary 复跑 2026-08-25 00:40:01
--- 最近 4 周期 ---
[2026-08-24 22:45:42] REPORT: overall=PASS -> /home/testuser/wzh/projects/agents_final_tech/logs/graph/verify-report.json
[2026-08-24 23:19:12] REPORT: overall=FAIL -> /home/testuser/wzh/projects/agents_final_tech/logs/graph/verify-report.json
[2026-08-24 23:44:20] REPORT: overall=PASS -> /home/testuser/wzh/projects/agents_final_tech/logs/graph/verify-report.json
[2026-08-25 00:17:52] REPORT: overall=PASS -> /home/testuser/wzh/projects/agents_final_tech/logs/graph/verify-report.json
--- 最近 canary 行 ---
[2026-08-24 23:40:49] STEP 5: QA canary sentinel (adv_ocr_meta,adv_refusal,q06_minan_cash_balance,adv_cross_doc)...
[2026-08-24 23:44:16]   OK: canary all pass | [m2-eval] PASS: 4/4 题全过 [report] /home/testuser/wzh/projects/agents_final_tech/logs/graph/eval/m2_canary_report.json 
[2026-08-25 00:14:20] STEP 5: QA canary sentinel (adv_ocr_meta,adv_refusal,q06_minan_cash_balance,adv_cross_doc)...
[2026-08-25 00:17:48]   OK: canary all pass | [m2-eval] PASS: 4/4 题全过 [report] /home/testuser/wzh/projects/agents_final_tech/logs/graph/eval/m2_canary_report.json 
--- pg_stat ---
1|0
warn_total=219 recovered_total=0
--- canary 复跑 ---
canary_rerun_exit=0
[m2-eval] PASS: 4/4 题全过
[report] logs/graph/eval/m2_canary_report_0040.json
--- W2 归因: 23:54 分段点后 IdleSessionTimeout / warn 分类 ---
IdleSessionTimeout=53 | Vector_retrieve_failed=219 | fallback_expose=0 | dispose_retry_recovered=0
(口径: GUC 回收闲连接 + pre_ping 静默恢复 = 预期; 用户可见检索失败 = 异常入台账)
{"message": "Vector retrieve failed on m1_parsed_statements: 创建向量存储失败: Failed to create vector extension: (psycopg.OperationalError) connection failed: connection to server at \"127.0.0.1\", port 15432 failed: FATAL:  sorry, too many clients already\n(Background on this error at: https://sqlalche.me/e/20/e3q8)", "timestamp": "2026-08-14 07:32:21,794", "level": "WARNING", "logger": "biz.rag_service", "log_id": "", "run_id": "", "space_id": "", "project_id": "", "method": "", "x_tt_env": "", "lineno": 330, "funcName": "smart_retrieve", "taskName": "starlette.middleware.base.BaseHTTPMiddleware.__call__.<locals>.call_next.<locals>.coro"}
{"message": "Vector retrieve failed on m1_parsed_statements: 创建向量存储失败: Failed to create vector extension: (psycopg.OperationalError) connection failed: connection to server at \"127.0.0.1\", port 15432 failed: FATAL:  sorry, too many clients already\n(Background on this error at: https://sqlalche.me/e/20/e3q8)", "timestamp": "2026-08-14 08:04:16,367", "level": "WARNING", "logger": "biz.rag_service", "log_id": "", "run_id": "", "space_id": "", "project_id": "", "method": "", "x_tt_env": "", "lineno": 330, "funcName": "smart_retrieve", "taskName": "starlette.middleware.base.BaseHTTPMiddleware.__call__.<locals>.call_next.<locals>.coro"}
{"message": "Vector retrieve failed on m1_parsed_statements: 创建向量存储失败: Failed to create vector extension: (psycopg.OperationalError) connection failed: connection to server at \"127.0.0.1\", port 15432 failed: FATAL:  sorry, too many clients already\n(Background on this error at: https://sqlalche.me/e/20/e3q8)", "timestamp": "2026-08-14 08:31:08,914", "level": "WARNING", "logger": "biz.rag_service", "log_id": "", "run_id": "", "space_id": "", "project_id": "", "method": "", "x_tt_env": "", "lineno": 330, "funcName": "smart_retrieve", "taskName": "starlette.middleware.base.BaseHTTPMiddleware.__call__.<locals>.call_next.<locals>.coro"}
--- pg_stat 普查 (全连接) ---
6227|idle||ROLLBACK|00:00:07.15124
6228|idle||ROLLBACK|00:00:06.950275
6232|idle||ROLLBACK|00:00:02.383833
6233|idle||ROLLBACK|00:00:02.135633
6225|idle||UPDATE chat_sessions SET last_active = N|00:00:00.334437
6246|active|psql|select pid, state, application_name, lef|-00:00:00.000003
## END 2026-08-25 00:43:22

## W2 归因更正 (00:50, 主线程复核)
00:40 cron 的 awk 时间过滤对 JSON 行失效 ($1$2 非时间戳, 比较恒真), 上面 53/219 为全文总数非分段数。
按 JSON timestamp 字段重算 23:54 分段点后:
post-23:54 真实计数: IdleSessionTimeout=0 (last=None) | Vector_retrieve_failed=0 (last=None) | fallback_expose=0 | dispose_recovered=0
(口径不变: pre_ping 静默恢复=预期; 用户可见失败=异常。若两项为 0 = 修复后病灶零复发)…(00:28 gate 脚本 head -c 400 截断 UTF-8 半字符, 08-25 E1b 修复, 原句读=资产市[值])
