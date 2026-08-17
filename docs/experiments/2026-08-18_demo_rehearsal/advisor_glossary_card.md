# 导师演示名词速查卡（内部, 现场答问用）

用法: 老师问到哪个抽哪个。每条 = 一句白话 + 一句技术底。

1. **双链路架构**
   白话: 同一个问题两条路——快路 2 秒给答案, 准路半分钟但多一个独立复核员。
   技术底: M2_OPENCODE_ROUTE 开关; 直连 = FastAPI 内 RAG(:8004 A3B), 验证链路 = opencode sidecar m2-qa agent(:8006 27B), 超时 45s 自动回落直连。
2. **vLLM**
   白话: 模型的"发动机托管厂", 让 27B 模型在咱这台小机器上跑得动、能排队。
   技术底: vLLM 0.27 GB10 构建, FP8 量化, PagedAttention 管 KV, docker 容器 :8006, GMEM=0.30 内存预算。
3. **prefill-decode 与带宽墙**
   白话: 模型答题分"读题"和"写答"两步; 这台机器内存带宽是天花板, 写答速度被它卡死。
   技术底: GB10 273GB/s 统一内存带宽 → 27B dense FP8 单流解码 ~10-15 tok/s; prefill 吃算力, decode 吃带宽。
4. **APC（前缀缓存）**
   白话: 同样的"开场白"只读一遍, 后面复用, 不然每轮都重读全文。
   技术底: vLLM Automatic Prefix Caching; 本构建默认关（prefix_cache_queries=0 实测）, --enable-prefix-caching 后 warm ask 47s→31s, 命中率 ~78%。
5. **思考控制**
   白话: 让模型"别想太多直接答", 省时间; 想过头反而又慢又没用。
   技术底: chat_template_kwargs enable_thinking=false（服务器模板默认 + :8008 注入代理兜底）; reasoning_effort 探针显示 dense 27B 开思考全档加延迟且非单调。
6. **qwen3_xml 工具解析**
   白话: 模型"使工具"时说的是 XML 方言, 得配对应翻译器, 不然工具调用被当废话。
   技术底: Qwen3.8 工具调用输出 XML 标签; vLLM --tool-call-parser qwen3_xml（hermes 不识别 → tool_calls=null）。
7. **OCR-VLM**
   白话: 扫描件/传真靠视觉模型"看图识字", 不用联网, 数据不出屋。
   技术底: :8004 A3B + mmproj 视觉转写表格; 坐标重建 + 引擎超时梯度 + 预算政策（M1_OCR_BUDGET_SECONDS）; 全本地推理。
8. **embedding 与溯源**
   白话: 把每段文字变成"坐标", 提问时找坐标最近的段落; 答案必须挂出处, 没出处不显示。
   技术底: qwen3-embedding-0.6b 本地 CPU; pgvector 137 chunks; sources = sample_id/table/field, FORMAT_HINT 机器解析契约。
9. **schema 自学习**
   白话: 新表里不认识的列名, 系统先猜一个映射做成选择题给人确认, 确认后变规则, 下次自动认识。
   技术底: LLM 兜底映射 → schema_suggestions.json（置信度/理由/去重）→ 勾选经 schema API 应用 + 热加载 → scenario1 回归门禁报 delta; 华泰紫金 35.7%→100% 即此闭环。
10. **多 Loop 互核治理**
    白话: 干活的、查岗的、审计的是三拨"人", 互相盯着, 谁报错都有记录。
    技术底: Loop A 执行(Codex) / Loop B 纯 bash 9 步验证(30min 周期, 拓扑断言+agent 看门狗, 翻转才出声) / Loop C 审计(Claude) / Loop D 指挥; dispatch_log + THREADS 单一台账。

备用弹药: 嘉合同版式 100% / 最难样本 35.7%→100%（纯确定性规则）/ 问答 16/16 带溯源 / 电子件毫秒级 / 扫描件 OCR 16-71s 全本地。
