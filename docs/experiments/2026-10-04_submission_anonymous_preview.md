# 匿名投稿源预览生成证据（2026-10-04）

> 状态：内部投稿准备证据，不是 camera-ready，不是外发件
> 生成环境：GB10；生成器 `research/build_submission_anonymous_preview.py`
> 源稿：`paper/teacher_review_draft_v1.md`

## 1 产物

| 工件 | sha256 | 说明 |
|---|---|---|
| `paper/submission_draft_arr_www_anonymous_v0.md` | `6af1dfc661f56cd29b63ecc727a4ee35e0df93adf42e887254ba017de1f1b30e` | 匿名投稿源预览 |
| `paper/submission_redaction_map_v1.json` | `30f1be4b82759ef151d148f71ddf146cbdda75d84bfca3b1c1d93ea5a2af03a6` | 内部脱敏审计图，不随稿外发 |
| 源稿 `paper/teacher_review_draft_v1.md` | `9d3e492694dda052a854c3cffac0b127ecda3aa383aa566abb75293fd7716f5c` | 未被生成器修改 |

## 2 机械脱敏

共 11 处有效替换、12 条 redaction 记录（含一个预期为 0 的配置替换分支）：

- 内部状态 header → anonymous preview header；
- 两个 figure 相对路径 → `figures/...`；
- checkpoint/semantic-judge 配置、source/injection artifact hash、matcher 实现、judge model/endpoint、sensitivity artifact、production wording →匿名描述。

禁词扫描结果为空：`logs/graph`、`docs/experiments`、`data/research`、`scripts/`、`127.0.0.1`、`Qwen3.6`、`GGUF`、`GB10`、`Loop D`、`patent-status`、作者/单位待填提示均未出现在预览正文。

## 3 完整性与确定性

- `claim_manifest_v1.json` 的全部 manuscript tokens 在预览中保留，缺失列表为空。
- 生成器双跑 stdout 与产物一致；源稿 sha256 不变。
- `tests/test_submission_anonymous_preview.py`：4 条生成器回归 + tracked preview 对账测试。
- `tests/test_paper_claim_acceptance.py` + `tests/test_document_governance.py`：17 passed。
- `research/validate_paper_claims.py`：PASS / 73 checks。
- `docs_lint`：`0 fail / 4 warn`，与既有基线同构。

## 4 发布边界

预览仍需 venue 官方模板、作者/单位、匿名规则和专利确认；redaction map 明确是内部审计件。专利未确认前不外发、不上传 arXiv、不公开代码。
