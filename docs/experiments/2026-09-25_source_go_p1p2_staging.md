# SOURCE_GO 证据件：P1/P2 批准范围下载完成（2026-09-25，D-C 裁定执行）

> 状态: 证据件（Loop D）| 裁定: D-C（2026-09-25 最小范围）+ D-B（scope confirmation 四项）
> 暂存: GB10 `~/wzh/phase1a_staging_20260925/`（仓外；数据体永不入 Git）
> 传输: blobless sparse-checkout clone（`--filter=blob:none --no-checkout` + sparse 模式）经 ssh，
> 仅取批准 blob；raw.githubusercontent 大文件流在 GB10 与本机均被节流/重置（已中止并记录），
> 该传输偏差如实入账：字节范围仍严格等于批准清单（scope 检查见 §3）。

## 1 来源与引用

| 源 | official repo | ref | 许可（引用见 D-B 附件） |
|---|---|---|---|
| FinQA | https://github.com/czyssrs/FinQA | `0f16e2867befa6840783e58be38c9efb9229d742` | repo MIT（sha 92c0e67b…）；README 对数据许可沉默（D-B 裁定按组合许可+记录风险） |
| Valentine | https://github.com/delftdata/valentine | `5d5163f04da304985bd51a476ccf7653de3979c3` | repo Apache-2.0（sha f4960433…）；NYC 目录数据受 NYC Open Data 上游条款 govern |

## 2 逐文件字节与 sha256（批准清单内）

| 路径 | 字节 | sha256 |
|---|---|---|
| finqa/train.json | 78 216 616 | `49f237eb9779b569473b26b08048867d04635a7cc39ad6a7a5664c55bb428db6` |
| finqa/dev.json | 10 954 658 | `a847fb7e0d61a3125a1e2909852df6b89f1ee64d2c5ff1bf689e332214deee51` |
| valentine/LICENSE | 11 365 | `f4960433bd98568685898d782e724fc28b5481be2a4b57b6280bf6e8c262e99d`（与 09-24 取证逐字节同） |
| valentine/bench.py | 24 893 | `e038be5145b48432f524c04fc335e6b5ce9652fac2fa75714524a5d7eb7f6b92` |
| valentine/experiments/data/（10 个 NYC 目录，58 文件） | 见暂存 bytes_manifest.txt | 见暂存 sha256_manifest.txt |

FinQA 两文件字节数与 D-C 附件 API 实测**逐字节一致**；valentine 共 62 文件（LICENSE+bench+58 数据文件）、
恰 10 个 NYC 目录。retrieved_at = 2026-09-25T04:12:14Z。

## 3 范围与零甲方数据自证

- scope 检查：`find finqa valentine -type f` 全路径匹配批准模式，越界路径 **0**（命令输出空）。
- 零甲方/私有数据：暂存仅含上述公开仓库文件；未触碰 ~/wzh/m1_samples 与任何 production 数据目录。
- 数据体不入 Git：暂存位于仓外；本件只记哈希与字节，不记数据内容。
- 下载不改任何门：SOURCE_GO 的本件证据 = URL/ref/字节/哈希/许可引用/零甲方数据；LABEL_GO 起仍需
  独立复核链（R1/R2/裁决）跑完并过合同。

## 4 下一步（已排程序，未执行）

1. SPLIT 设计：以 FinQA 例 id 的报告级 lineage 为聚类单元，哈希分桶定四层（proposal/train、dev、
   gate-validation、sealed-test），future_replay 暂空（LONGITUDINAL_EVIDENCE_UNAVAILABLE）；宇宙有界化
   规则与样本量在实测计数后定稿并独立审计。
2. label review：R1=qwen3.8-max / R2=deepseek-v4-pro（模板互异），参考 = 已审计 FinQA schema 草案
   （D-A 选项 3）；裁决载体独立；输出过装配器→派生→合同→manifest 双跑→独立复核。
3. Valentine 只作 P2 action 来源，单独 provenance 与 split 命名空间，不与 P1 拼同分布主实验。
