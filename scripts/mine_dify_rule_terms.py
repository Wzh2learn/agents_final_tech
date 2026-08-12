#!/usr/bin/env python3
"""S3② dify 甲方规则 docx 术语挖掘 (Q2 同款确定性流程, 无 LLM)。

从 dify/*.docx (七月 Dify 原型遗留的 5 份甲方业务规则) 提取候选术语,
与 config/m1_table_schema.json 的 standard+synonyms 词表做确定性比对:
- covered: 已是 schema 词 (standard 或 synonym 精确命中)
- candidate: 与某 standard 存在双向子串关系 (len>=3) 且无碰撞 -> 可补词候选
- unknown: 无确定性映射, 仅报告 (等甲方字段规则表或人工判定)

用法: venv/bin/python scripts/mine_dify_rule_terms.py
产出: logs/graph/dify_rule_terms_report.json (不入 git)
"""
import glob
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

SCHEMA = os.path.join(REPO, "config", "m1_table_schema.json")
OUT = os.path.join(REPO, "logs", "graph", "dify_rule_terms_report.json")

STOPWORDS = {
    "字段", "说明", "提取内容", "规则", "规则名称", "最后更新", "来源位置",
    "用户问题", "规则逻辑", "数据来源", "业务示例", "唯一标识", "业务描述",
    "生效日期", "文档位置", "待补充", "系统", "触发", "流程", "场景", "配置",
    "查询", "监控", "执行", "判断", "处理", "生成", "检测", "触发方式",
    "定时任务", "前置依赖", "前置校验", "数据准备", "方式", "条件", "动作",
    "结果", "状态", "记录", "信息", "功能", "界面", "用户", "运维", "人员",
    "会计", "经办", "管理人", "托管", "外包", "券商", "经纪商",
    "典型的用户问法", "结构", "描述", "补充", "关键", "包含", "如下",
    "相同时", "不同", "一致", "不一致", "缺失", "完整", "自动", "手动",
}
CJK_TOKEN = re.compile(r"[\u4e00-\u9fa5][\u4e00-\u9fa5A-Za-z0-9（）()]{1,9}")
SPLIT = re.compile(r"[/、，,；;：:\s]+")


def schema_vocab() -> tuple[set, dict]:
    d = json.load(open(SCHEMA, encoding="utf-8"))
    standards: dict[str, list[str]] = {}
    all_words: set[str] = set()
    for t in d.get("tables", []):
        for f in t.get("fields", []):
            std = f.get("standard", "")
            if std:
                standards.setdefault(std, [])
                standards[std].extend(f.get("synonyms", []))
                all_words.add(std)
                all_words.update(f.get("synonyms", []))
    hm = d.get("header_meta_fields") or {}
    if isinstance(hm, dict):
        for std, syns in hm.items():
            standards.setdefault(std, [])
            if isinstance(syns, list):
                standards[std].extend(syns)
                all_words.update(syns)
            all_words.add(std)
    elif isinstance(hm, list):
        for f in hm:
            std = f.get("standard", "")
            if std:
                standards.setdefault(std, [])
                standards[std].extend(f.get("synonyms", []))
                all_words.add(std)
                all_words.update(f.get("synonyms", []))
    return all_words, standards


def extract_docx_terms(paths: list[str]) -> dict[str, int]:
    from docx import Document
    counts: dict[str, int] = {}
    for p in paths:
        doc = Document(p)
        texts = []
        for tb in doc.tables:
            for row in tb.rows:
                for c in row.cells:
                    texts.append(c.text)
        for para in doc.paragraphs:
            texts.append(para.text)
        for raw in texts:
            for chunk in SPLIT.split(raw):
                for m in CJK_TOKEN.finditer(chunk):
                    tok = m.group(0).strip("（）()")
                    if 2 <= len(tok) <= 10 and tok not in STOPWORDS:
                        counts[tok] = counts.get(tok, 0) + 1
    return counts


def main() -> int:
    all_words, standards = schema_vocab()
    docx = sorted(glob.glob(os.path.join(REPO, "dify", "*.docx")))
    if not docx:
        print("no dify/*.docx found")
        return 1
    terms = extract_docx_terms(docx)
    covered, candidates, unknown = [], [], []
    for tok, cnt in sorted(terms.items(), key=lambda x: -x[1]):
        if tok in all_words:
            covered.append({"term": tok, "n": cnt})
            continue
        hits = []
        for std in standards:
            if len(std) >= 3 and (std in tok or tok in std):
                hits.append(std)
        if hits:
            # 碰撞检查: 候选词若已是别处 synonym 则跳过 (FC-1 教训)
            owners = [s for s, syns in standards.items() if tok in syns]
            candidates.append({"term": tok, "n": cnt, "maps_to": hits,
                               "collision": owners})
        else:
            unknown.append({"term": tok, "n": cnt})
    report = {
        "docx": [os.path.basename(p) for p in docx],
        "schema_words": len(all_words),
        "covered": covered,
        "candidates": candidates,
        "unknown_top": unknown[:60],
        "unknown_total": len(unknown),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(report, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"schema 词表: {len(all_words)} | 提取术语: {len(terms)}")
    print(f"covered={len(covered)} candidates={len(candidates)} unknown={len(unknown)}")
    print("-- covered --")
    for c in covered:
        print(f"  {c['term']} x{c['n']}")
    print("-- candidates (确定性子串映射) --")
    for c in candidates:
        print(f"  {c['term']} x{c['n']} -> {c['maps_to']} collision={c['collision']}")
    print(f"-- unknown top20 (共{len(unknown)}) --")
    for u in unknown[:20]:
        print(f"  {u['term']} x{u['n']}")
    print("[report]", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
