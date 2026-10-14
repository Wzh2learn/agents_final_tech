# Paper E AI 味审查与精修 v1（2026-10-14）

> 范围: 全文通读 + 典型 AI 文风标记扫描（"rather than" 密度、强调词、元话术收尾、词汇重复、否定堆叠、heading 风格）。
> 性质: **仅表达层精修**——不动数字、claim、证据哈希；流程同既有 presentation-fix（重建 + 双审计 + PDF 断言）。
> 触发: owner 2026-10-14「从 ai 味的角度看看我们文章哪些部分需要修改」。

## 1. 扫描发现（按类别）

1. **"rather than" 句式密度 23 处**（摘要一行 3 处、§5.6 一行 2 处、附录一行 3 处）——全文最典型的 AI 节律；处置：精修 7 处（优先堆叠与摘要），保留 16 处中属于 claim 边界精度必需的。
2. **强调词/元话术**: "This is precisely why…"、"Read together,…"、"These limits define the paper's claims."、"strongly defect-type dependent"（heading）→ 重写去 meta。
3. **词汇重复**: "instantiation" 3 处 → 保留 1、其余改 "here"/"construction"；"explicit(ly)" 11 处以 302 处中的术语义为主，保留（与 ablation 叙事绑定）。
4. **否定堆叠**: §5.2 长句（"not a newly calibrated…; deliberately narrow, in that… and is not offered as…"）→ 拆分；§5.6 "mismatch lies in … rather than in an undefined predicate" → "not of predicate definition"。
5. **重复词开段**: "This boundary case…"（与标题 "Boundary case" 连用）→ "This case…"。
6. **未发现**: em dash（0）、delve/leverage/underscore/showcase 等词（0）、"It is worth noting"（0）。

## 2. 已应用修改（14 处；逐条单次命中守卫；23→16 处 "rather than"）

1. 摘要: "describes this carrier construction rather than a detection ability, a measurement-object mismatch rather than protocol blindness." → "…describes this carrier construction: a measurement-object mismatch that does not evidence protocol blindness."
2. 摘要尾: "…hierarchical organization, rather than a detector ranking." → "…hierarchical organization; the audit is not a detector ranking."
3. §3.1: "This is precisely why additional localization value remains unestablished…" → "Additional localization value therefore remains unestablished…"
4. §4.1: "…perturbation carrier in this instantiation;…" → "…perturbation carrier here;…"
5. §5.1 标题: "Visibility is strongly defect-type dependent" → "Visibility depends on defect family"
6. §5.2: "…clean-only procedure rather than a general claim that…" → "…clean-only procedure, not a general claim that…"
7. §5.2: "…deliberately narrow, in that it explains… and is not offered as…" → "…deliberately narrow: it explains…, and it is not offered as…"
8. §5.2 尾: "single-varying-leaf instantiation" → "single-varying-leaf construction"
9. §5.6: "the mismatch lies in the measurement objects rather than in an undefined predicate." → "the mismatch is one of measurement objects, not of predicate definition."
10. §5.7: "This boundary case is not part of…" → "This case is not part of…"
11. §6.3: "Read together, the results support…" → "Together they support…"
12. §6.3 尾: "These limits define the paper's claims." → "The paper's claims hold within these limits."
13. §6.3: "…a boundary rather than a performance number." → "…a boundary, not a performance number."
14. 附录 A.2: "…label gate rather than to criterion (i)" → "…label gate, not to criterion (i)"

## 3. 保留（不动）与理由

- 精度必需的 "rather than"（如 "alternative interpretation rather than independent ground truth"——claim 边界用语，且与 §6.1 呼应）保留原样。
- "explicitly instrumented / explicit stage-aligned instrumentation" 术语族：与摘要—§5.5—图 3 的 ablation 叙事绑定，保留。
- "frozen"（45 处）、"boundary"（20 处）：领域核心术语，不动。
- 数字、公式、表、图注数字、引用格式：未触碰。

## 4. 验证

- 重建: md→tex→bundle→tectonic exit 0；9 页；PDF 289.04 KiB。
- `PRE_SUBMISSION_AUDIT = PASS`；`WIDE_EVIDENCE_CHECK = PASS`；`??`=0；禁用 token 全 0。
- PDF 断言: 旧句式 0 命中；新句式就位（1 处 PDF 提取断行伪影已单独核验，正文正确）。
- 记录: `PDF_LAYOUT_AUDIT_v1.md` 增补 Presentation fix (2026-10-14g)。

## 5. 边界

表达层修改，可逐条回退（git）；如 owner 对某条有偏好（例如保留某个 headline 句式），单独指出即可恢复。