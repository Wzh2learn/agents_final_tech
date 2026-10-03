# 投稿包完整性审计证据（2026-10-04）

> 状态：内部审计证据，不是投稿许可 | 审计入口：`research/audit_submission_package.py`
> 机器报告：`paper/submission_package_audit_v1.json`

## 1 判定

| 状态 | 值 |
|---|---|
| `mechanical_status` | `PASS` |
| `submission_status` | `PENDING_EXTERNAL_ITEMS` |
| `overall` | `NOT_READY_FOR_SUBMISSION` |
| checks | `10/10` |

审计刻意区分机械一致性与投稿准备度：机械检查全绿不代表 venue、作者、匿名、专利或 camera-ready 已完成。

## 2 检查面

- 主稿与匿名预览的 9 个必需章节；
- claim manifest 的全部 manuscript tokens 在两份文本中均存在；
- 主稿 References 15 条、投稿映射 15 条、BibTeX 15 条集合一致；
- 匿名预览禁词 0，redaction map source/output hash 与 tracked 文件一致；
- 投稿清单 hash 全部以 **GB10 checkout 字节**为准；
- D-B licence_record 的 accepted_by、accepted_at、四项 permitted_uses、三项 covered hashes 与排除用途；
- 可复现性声明引用 D-B 记录并保持外发边界。

## 3 未完成的外部项

1. venue 官方模板与 CFP 核验；
2. 作者、单位、匿名化；
3. 专利状态确认；
4. camera-ready PDF 视觉验收；
5. 146 列 Q3 三载体复核仍未运行。

这些项目保持 pending，不写成已完成或可投稿。
