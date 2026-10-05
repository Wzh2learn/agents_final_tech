# Goal

以长流程智能测评专利为技术底座，完成“会议小论文—研究生毕业论文”协同路线沉淀，并把会议稿证据缺口转化为可审计的 Graph Loop 计划。

# Done when

- 会议小论文唯一主线锁定为“长流程分层评测 + 缺陷可见性诊断 + PSO 评测协议优化”，VGRM 只作反馈闭环案例。
- 大论文锁定三个核心创新点：判别力感知分层评测、缺陷可见性/静默吸收理论、评测驱动的 VGRM 门控规则自学习；跨层补盲仅作条件性第四点。
- 新增正式活文档、AAAI 风格主张—证据—缺口蓝图、Graph Loop 分阶段计划。
- INDEX、STATE、THREADS、dispatch 同步；docs_lint 与冻结 diff 检查通过。
- 不修改专利终态正文、冻结节点、生产服务或甲方数据。

# Never touch

- `docs/experiments/2026-08-21_patent_full_revised.md` 及专利发送三件只读。
- `tests/test_m1_service.py`、`scripts/graph/frozen_hashes.txt`、`docs/m1_schema/` 及冻结清单全部路径。
- `:5050`、页面后端、生产配置、API key、HF token、甲方数据。
- 未确认专利正式申请日前，不上传 arXiv、不公开论文/代码、不对外投稿或发送。

# Stop if

- 需要把尚未执行、推定或探索性结果写成既成事实。
- 专利权利要求与论文主张无法建立事实一致的来源映射。
- 文档检查转为失败或出现冻结节点改动。
