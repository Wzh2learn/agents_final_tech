#!/usr/bin/env python3
"""S3④ Docling ARM64 探针 (2026-08-13, 结论型)。

独立 venv (~/wzh/venvs/docling_probe) 跑 docling 端到端, 对三个代表样本
输出 表数/耗时/首表预览, 与本项目 parser 基线对比。不碰生产 venv/服务。
用法: ~/wzh/venvs/docling_probe/bin/python scripts/probe_docling.py
产出: /tmp/docling_probe_report.json
"""
import glob
import json
import os
import time
import traceback

ATT = os.path.expanduser("~/wzh/m1_samples/scenario1/attachments")


def _first(pattern: str) -> str:
    hits = sorted(glob.glob(os.path.join(ATT, pattern)))
    return hits[0] if hits else os.path.join(ATT, pattern)


SAMPLES = {
    "TraFax_scan": _first("转发 来自：(TraFax Server)_att0_*.pdf"),
    "NCAMC_vertical": _first("转发 1L8023341752*_att0_*.pdf"),
    "Jiahe_electronic": _first("转发 嘉合基金客户对账单_att0_*.pdf"),
}
OUT = "/tmp/docling_probe_report.json"


def main() -> int:
    from docling.document_converter import DocumentConverter
    t0 = time.time()
    conv = DocumentConverter()
    print(f"[probe] converter ready in {time.time()-t0:.1f}s")
    report = {}
    for name, path in SAMPLES.items():
        entry = {"file": os.path.basename(path)}
        if not os.path.isfile(path):
            entry["error"] = "file not found"
            report[name] = entry
            continue
        try:
            t1 = time.time()
            res = conv.convert(path)
            doc = res.document
            tables = doc.tables
            entry["seconds"] = round(time.time() - t1, 1)
            entry["n_tables"] = len(tables)
            entry["pages"] = len(doc.pages) if hasattr(doc, "pages") else None
            previews = []
            for tb in tables[:3]:
                try:
                    df = tb.export_to_dataframe()
                    previews.append({
                        "shape": list(df.shape),
                        "head": df.head(3).astype(str).values.tolist(),
                    })
                except Exception as e:
                    previews.append({"error": str(e)[:120]})
            entry["table_previews"] = previews
        except Exception as e:
            entry["error"] = f"{type(e).__name__}: {str(e)[:200]}"
            entry["trace"] = traceback.format_exc()[-400:]
        report[name] = entry
        print(f"[probe] {name}: " + json.dumps(
            {k: v for k, v in entry.items() if k != "table_previews"},
            ensure_ascii=False))
    json.dump(report, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[report]", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
