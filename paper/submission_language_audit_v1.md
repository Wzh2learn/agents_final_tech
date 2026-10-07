# 小论文投稿前语言与术语审计 v1

> 状态：内部静态审计，不替代 venue 格式审查 | 更新：2026-10-04
> 对象：`paper/teacher_review_draft_v1.md` 与 `paper/submission_draft_arr_www_anonymous_v0.md`
> 依据：`paper-polish-and-audit` 检查单；零模型、零外部调用

## 1 术语一致性

| 术语 | 统一口径 | 结果 |
|---|---|---|
| checkpoint-level visibility | 协议是否在中间检查点观测到缺陷 | 一致 |
| protocol-level detection | 聚合分数/映射文本是否越过检测阈值 | 一致 |
| silent absorption | 检查点证据保持而缺陷未被观测到的第三类结果 | 一致 |
| matched-FPR / affinely equivalent | 匹配假阳率后的退化等价观察 | 一致 |
| single-varying-leaf | `[0,0]` 支持集的构造条件 | 一致 |

未发现同义词漂移；Related Work 四簇与主稿方法/结果术语一致。

## 2 强主张与 AI 风格扫描

- `state-of-the-art`、`delve into`、`it is important to note that`、`in conclusion` 命中 0。
- `superior`、`significant`、`robust` 等命中项均位于“not claim / does not establish / not a general”等否定、边界或测量语境，不构成无依据强主张。
- 主稿不使用训练完成、Stage D 闭合、DATA_GO 等结果性措辞；Q3 输入包与未完成项显式保留为边界。

## 3 版本同步

- 主稿、匿名预览、DOCX、claim manifest、acceptance report 由投稿包审计统一检查。
- 匿名预览保留全部 claim tokens；内部路径、hash、模型/端点身份按 redaction map 脱敏。
- 结论段与 Abstract 均强调“decomposition, not better detection sensitivity”，未出现主张漂移。

## 4 结果

未发现 blocking language issue；本次不改主稿。剩余工作属于 venue 官方格式、作者/匿名、专利和 camera-ready 外部项。

## 5. 2026-10-07 narrative revision audit

- Title and abstract now foreground `Visibility Is Not Detection`; the abstract uses the same claim tokens and measured values as the body.
- Introduction contributions now follow the order: three-way distinction, hierarchical evidence instrument, controlled protocol audit.
- Section 5.2 leads with the threshold-artifact interpretation; Section 6 separates scientific limitations from deferred independent evidence.
- No new strong-claim language was introduced. Future dataflow/scorer/localization work is explicitly deferred and does not change current claim status.
