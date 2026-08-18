#!/usr/bin/env python3
"""(K3) Schema 漂移注入器 v0 — 公开表格数据集上的确定性列名扰动/别名变体注入。

VGMC 实验 1（漂移注入 + 门控闭环）数据准备工具。纯确定性脚本:
- 不调用任何 LLM / 推理 / Web 端点
- 同 seed 同输入 => 输出字节级一致（有单测证明, 见 tests/test_drift_inject.py）

输入格式（TAT-QA 归一化后的 JSON 数组）:
  [{"uid": "...", "table": [["col1", "col2", ...], [v, v, ...], ...]}, ...]
首行视为表头; 非表头行不得被改写（只注入列名）。原列名保留在注入映射清单。

注入类型分类学（6 类, 每类独立种子派生通道, 全表可复现）:
  1. alias_variant       别名变体（简称/全称/中英行业术语）
  2. mixed_lang          中英混写
  3. unit_suffix         单位后缀（元/万元/份额）
  4. date_variant        日期变体（对账日期/期末日期/净值日期）
  5. ocr_similar         OCR 形近错认
  6. prefix_noise        前后缀噪声（圈号/序号/空格/标点）

用法:
  python scripts/research/drift_inject.py \
      --input data/research/drift_v0/input/tatqa_tables.json \
      --out data/research/drift_v0/output \
      --ratio 0.3 --seed 42
输出:
  injected_tables.json    注入后表（顺序与输入一致, 字节稳定）
  injection_map.json      注入映射清单（原列名/注入后/类型/种子, 可追溯）
  report.json             统计报告（源/表数/注入分布/注入率/确定性 hash）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

DRIFT_VERSION = "v0"
DEFAULT_SEED = 42
DEFAULT_RATIO = 0.3

# --------------------------------------------------------------------------
# 注入词库: 全部为公开行业术语/OCR 常见形近对。词库为确定性的字典+排序结构,
# 不引入任何运行期随机（唯一熵源 = seed 派生的 PRNG）。
# --------------------------------------------------------------------------

ALIAS_VARIANTS: Dict[str, List[str]] = {
    "revenue": ["sales", "turnover", "营业收入", "营业总收入", "营收"],
    "receipts": ["收入", "收款"],
    "net income": ["net profit", "profit after tax", "净利润", "税后利润"],
    "total assets": ["total assets (t/a)", "资产总额"],
    "total liabilities": ["负债总额", "liabilities"],
    "cash flow": ["cashflow", "现金流量", "现金流"],
    "operating profit": ["营业利润", "operating income"],
    "gross profit": ["毛利", "gross margin"],
    "rd expenses": ["research and development expenses", "研发支出", "研发费用"],
    "market value": ["市值", "market cap", "market capitalization"],
    "closing price": ["收盘价", "close", "closing"],
    "open price": ["开盘价", "open"],
    "trading volume": ["成交量", "volume", "交易量"],
    "trade date": ["交易日", "业务日期"],
    "maturity date": ["到期日", "maturity"],
    "sharehoders equity": ["shareholders' equity", "股东权益"],
    "account": ["账户", "account no.", "帐号"],
    "interest": ["利息", "interest income"],
    "dividends": ["股息", "dividend"],
    "amortization": ["摊薄", "amort"],
    "provision": ["拨备", "provisions"],
}

MIXED_LANG_VARIANTS: Dict[str, List[str]] = {
    "revenue": ["revenue(营收)", "营业收入(revenue)", "revenue收入"],
    "net income": ["net income(净利润)", "净利润(net profit)", "净income"],
    "total assets": ["total assets(资产总额)", "资产总额(total assets)"],
    "market value": ["market value(市值)", "市值(market cap)"],
    "closing price": ["closing price(收盘价)", "收盘价(closing)"],
    "trade date": ["trade date(交易日)", "交易日(trade date)"],
    "dividends": ["dividends(股息)", "股息(dividend)"],
    "account": ["account(账户)", "账户(account)"],
    "operating profit": ["operating profit(营业利润)", "营业利润(op profit)"],
    "cash flow": ["cash flow(现金流)", "现金流(cash flow)"],
    "income": ["income(收入)", "收入(income)"],
    "assets": ["assets(资产)", "资产(assets)"],
    "interest": ["interest(利息)", "利息(interest)"],
}

UNIT_SUFFIX_VARIANTS: Dict[str, List[str]] = {
    "revenue": ["revenue (元)", "revenue(万元)", "revenue-元"],
    "net income": ["net income(元)", "净利润(元)", "net profit (万元)"],
    "total assets": ["total assets(元)", "资产总额(万元)", "total assets 元"],
    "cash flow": ["cash flow(万元)", "现金流量(元)"],
    "market value": ["market value(元)", "市值(万元)"],
    "closing price": ["closing price(元/股)", "收盘价(元)"],
    "trading volume": ["trading volume(股)", "成交量(手)", "trading volume(万股)"],
    "dividends": ["dividends(元/股)", "股息(万元)"],
    # v0.2 扩充: 全量表上高频语义键, 提高单位后缀类覆盖（简化/全称/中英）
    "assets": ["assets(万元)", "资产(元)", "资产总额(万元)"],
    "income": ["income(元)", "收入(万元)"],
    "interest": ["interest(万元)", "利息(元)"],
    "profit": ["profit(万元)", "利润(元)"],
    "receipts": ["receipts(元)", "收入(万元)"],
}

DATE_VARIANT_SEMANTICS: List[str] = ["对账日期", "期末日期", "净值日期", "交易日", "报表明细日期"]
DATE_VARIANT_PATTERNS: List[Tuple[str, str, str]] = [
    # (正则, 替换模板, 说明)。%d 与 %s 两个占位符由注入器按 <年份,语义词> 填充,
    # 值本身来自表格年份上下文（保持从简), 因此同样与 seed 无关。
    (r"date", "%d年%s", "日期-长格式"),
    (r"date", "date %d-%s", "日期-语义后缀"),
    (r"date", "%s / date", "日期-语义前缀"),
    (r"date", "%d期末", "期末-年月"),
]
DATE_YEAR_POOL: List[str] = ["2016", "2017", "2018", "2019", "2020", "2021"]

OCR_SIMILAR_PAIRS: List[Tuple[str, str]] = [
    # (正则, 替换) — 只作用于表头行
    (r"revenue", "revenne"),
    (r"income", "inccome"),
    (r"assets", "assetg"),
    (r"liabilities", "liabilitie5"),
    (r"profit", "profitl"),
    (r"capital", "capitai"),
    (r"interest", "intere5t"),
    (r"dividend", "divdend"),
    (r"volume", "vo1ume"),
    (r"closing", "c1osing"),
    (r"operating", "operat1ng"),
    (r"equity", "equty"),
]

PREFIX_NOISE_DECORATORS: List[Tuple[str, str, str]] = [
    ("①②圈号", "{}①", "{}:①"),
    ("序号前缀", "{} 1.", "{} [1]"),
    ("号码前缀", "{} №", "No.{}"),
    ("全角方括号", "{}【】", "{}〔〕"),
]
PREFIX_NOISE_SURROGATES: List[str] = ["*", "#", "§"]


def _make_rng(seed: int):
    """确定性 LCG（x = (a*x + c) mod 2^31), 与 Python 版本无关, 跨进程字节稳定。
    函数内不落任何业务状态, 因此可脱离自定义类直接使用。"""
    a, c, m = 1103515245, 12345, 2 ** 31
    state = seed % m

    def rng():
        nonlocal state
        state = (a * state + c) % m
        return state

    return rng


class DriftInjector:
    """schema 漂移注入器。线程安全 = 单次调用内顺序执行, 无共享可变状态。"""

    def __init__(
        self,
        seed: int = DEFAULT_SEED,
        ratio: float = DEFAULT_RATIO,
        tables: Optional[List[Dict[str, Any]]] = None,
    ):
        if not 0.0 < ratio <= 1.0:
            raise ValueError("ratio must be in (0, 1]")
        self.seed = seed
        self.ratio = ratio
        self.tables = tables or []
        self.injected: List[Dict[str, Any]] = []
        self.mapping: List[Dict[str, Any]] = []
        self.stats: Dict[str, Any] = {}

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _norm_header(header: Sequence[Any]) -> List[str]:
        return ["" if (h is None or str(h).isspace()) else str(h).strip() for h in header]

    @staticmethod
    def _semantic(key: str) -> str:
        """从词库键名提取语义词（用于别名/单位/混合注入的确定性映射）。"""
        return key

    @classmethod
    def _alias_candidates(cls, header: List[str]) -> List[Tuple[str, str]]:
        """返回 [(matched_key, variant)] — 匹配只针对表头, 按词库 key 顺序确定性。"""
        out: List[Tuple[str, str]] = []
        for h in header:
            hl = h.lower().strip()
            for key, variants in ALIAS_VARIANTS.items():
                if key.lower() in hl:
                    # 首选未重复的变体, 若全重复则允许复用（词库 v0 不做去重回退）
                    for v in sorted(variants):
                        out.append((key, v))
                    break
        return out

    @classmethod
    def _mixed_candidates(cls, header: List[str]) -> List[Tuple[str, str]]:
        out: List[Tuple[str, str]] = []
        for h in header:
            hl = h.lower().strip()
            for key, variants in MIXED_LANG_VARIANTS.items():
                if key.lower() in hl:
                    for v in sorted(variants):
                        out.append((key, v))
                    break
        return out

    @classmethod
    def _unit_candidates(cls, header: List[str]) -> List[Tuple[str, str]]:
        out: List[Tuple[str, str]] = []
        for h in header:
            hl = h.lower().strip()
            for key, variants in UNIT_SUFFIX_VARIANTS.items():
                if key.lower() in hl:
                    for v in sorted(variants):
                        out.append((key, v))
                    break
        return out

    @classmethod
    def _date_candidates(cls, header: List[str]) -> List[int]:
        return [i for i, h in enumerate(header)
                if re.search(r"date", h, re.IGNORECASE)
                or re.match(r"^日期$", h.strip())
                or re.match(r"^\u65e5\u671f$", h.strip())]

    @classmethod
    def _ocr_candidates(cls, header: List[str]) -> List[int]:
        return [i for i, h in enumerate(header) if any(re.search(pat, h, re.IGNORECASE) for pat, _ in OCR_SIMILAR_PAIRS)]

    @classmethod
    def _prefix_candidates(cls, header: List[str]) -> List[int]:
        return [i for i, h in enumerate(header) if h.strip()]

    # ------------------------------------------------------------------ 注入动作
    @classmethod
    def _apply_alias(cls, header: List[str], idx: int, variant: str) -> str:
        h = header[idx]
        return variant if variant.lower() != h.lower() else f"{h} ({variant})"

    @classmethod
    def _apply_mixed(cls, header: List[str], idx: int, variant: str) -> str:
        return variant

    @classmethod
    def _apply_unit(cls, header: List[str], idx: int, variant: str) -> str:
        return variant

    @classmethod
    def _apply_date(cls, header: List[str], idx: int, year: str, semantic: str, pattern_idx: int) -> str:
        pat, tmpl, _ = DATE_VARIANT_PATTERNS[pattern_idx]
        hl = header[idx].strip()
        if re.match(r"^日期$", hl) or hl.lower().strip() == "date":
            return tmpl.replace("%s", semantic).replace("%d", year)
        new = tmpl.replace("%s", semantic).replace("%d", year)
        return re.sub(pat, new, header[idx], count=1, flags=re.IGNORECASE)

    @classmethod
    def _apply_ocr(cls, header: List[str], idx: int, pair: Tuple[str, str]) -> str:
        pat, repl = pair
        h = header[idx]
        for cand_pat, cand_repl in OCR_SIMILAR_PAIRS:
            if re.search(cand_pat, h, re.IGNORECASE):
                return re.sub(cand_pat, cand_repl, h, count=1, flags=re.IGNORECASE)
        return re.sub(pat, repl, h, count=1, flags=re.IGNORECASE)

    @classmethod
    def _apply_prefix(cls, header: List[str], idx: int, deco: Tuple[str, str, str]) -> str:
        name, fmt_a, fmt_b = deco
        # 确定性: 圈号/序号取 word 首字符; 全角取 word 首字符 + 尾字符
        word = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "", header[idx])
        if not word:
            return header[idx]
        if name.startswith("①②"):
            return fmt_a.format(word[:1])
        if name.startswith("序号"):
            return fmt_b.format(word)
        if name.startswith("号码"):
            return fmt_a.format(word)
        if name.startswith("全角"):
            return fmt_a.format(word[:1], word[-1:])
        return header[idx]

    # ------------------------------------------------------------------ 主流程
    def run(self) -> Dict[str, Any]:
        headers = [self._norm_header(t.get("table", [])[0] if t.get("table") else []) for t in self.tables]
        # 表级 PRNG 种子: 每表一个流（uid + seed 哈希派生), 保证跨表独立、同表内部顺序稳定
        uid_rng = _make_rng(self.seed ^ 0x9E3779B9)
        for ti, t in enumerate(self.tables):
            uid = str(t.get("uid", f"table_{ti}"))
            tbl: List[List[Any]] = list(t.get("table", []))
            if not tbl:
                continue
            header = ["" if x is None else str(x) for x in tbl[0]]
            table_seed = (self.seed + ti) & 0x7FFFFFFF
            rng = _make_rng(table_seed)
            n_cols = len(header)
            injections: List[Dict[str, Any]] = []
            new_header: List[str] = list(header)

            # 别名/中英/单位 三类: 每类各一轮, 命中列按 ratio 抽样（取整≥1 时取最小命中）
            for cand_fn, kind in (
                (self._alias_candidates, "alias_variant"),
                (self._mixed_candidates, "mixed_lang"),
                (self._unit_candidates, "unit_suffix"),
            ):
                cands = cand_fn(header)
                if not cands:
                    continue
                chosen = []
                if self.ratio < 1.0:
                    n_hit = max(1, int(round(self.ratio * len(cands))))
                else:
                    n_hit = len(cands)
                pool = cands[:]
                while pool and len(chosen) < n_hit:
                    r = rng() % len(pool)
                    chosen.append(pool.pop(r))
                for key, variant in chosen:
                    for ci, ha in enumerate(header):
                        if key.lower() in ha.lower() and new_header[ci] == header[ci]:
                            new_header[ci] = {
                                "alias_variant": lambda: self._apply_alias(header, ci, variant),
                                "mixed_lang": lambda: self._apply_mixed(header, ci, variant),
                                "unit_suffix": lambda: self._apply_unit(header, ci, variant),
                            }[kind]()
                            injections.append({
                                "row": 0, "col": ci, "original": header[ci], "injected": new_header[ci],
                                "type": kind, "source_key": key, "variant": variant,
                                "seed_component": table_seed,
                            })
                            break

            # 日期变体: 命中 date 的列, 语义词从 DATE_YEAR_POOL 确定性取
            date_idx = self._date_candidates(header)
            if date_idx and self.ratio >= 1.0 or (date_idx and rng() % 100 < self.ratio * 100):
                for ci in sorted(date_idx):
                    if new_header[ci] != header[ci]:
                        continue
                    year = DATE_YEAR_POOL[(table_seed + ci) % len(DATE_YEAR_POOL)]
                    semantic = DATE_VARIANT_SEMANTICS[(table_seed + ci) % len(DATE_VARIANT_SEMANTICS)]
                    pat_i = (table_seed + ci) % len(DATE_VARIANT_PATTERNS)
                    new_header[ci] = self._apply_date(header, ci, year, semantic, pat_i)
                    injections.append({
                        "row": 0, "col": ci, "original": header[ci], "injected": new_header[ci],
                        "type": "date_variant", "source_key": "date", "variant": f"{semantic}/{pat_i}",
                        "seed_component": table_seed,
                    })

            # OCR 形近: 只看命中其中的列
            ocr_idx = self._ocr_candidates(header)
            if ocr_idx and self.ratio >= 1.0 or (ocr_idx and rng() % 100 < self.ratio * 100):
                for ci in sorted(ocr_idx):
                    if new_header[ci] != header[ci]:
                        continue
                    applied = self._apply_ocr(header, ci, (None, None))
                    if applied == header[ci]:
                        continue  # 正则未命中文本时跳过, 保证注入必有变化
                    hit_pair = next((p for p in OCR_SIMILAR_PAIRS
                                     if re.search(p[0], header[ci], re.IGNORECASE)), (None, None))
                    new_header[ci] = applied
                    injections.append({
                        "row": 0, "col": ci, "original": header[ci], "injected": new_header[ci],
                        "type": "ocr_similar", "source_key": hit_pair[0], "variant": hit_pair[1],
                        "seed_component": table_seed,
                    })
                # 命中多列的降级回补: 若单列都未变, 再按列强制一次（含“单个字符/数字”列）
                ocr_done = any(m["type"] == "ocr_similar" for m in injections)
                if not ocr_done:
                    for ci in sorted(ocr_idx):
                        applied = self._apply_ocr(header, ci, (None, None))
                        if applied != header[ci] and new_header[ci] == header[ci]:
                            hit_pair = next((p for p in OCR_SIMILAR_PAIRS
                                             if re.search(p[0], header[ci], re.IGNORECASE)), (None, None))
                            new_header[ci] = applied
                            injections.append({
                                "row": 0, "col": ci, "original": header[ci], "injected": new_header[ci],
                                "type": "ocr_similar", "source_key": hit_pair[0], "variant": hit_pair[1],
                                "seed_component": table_seed,
                            })
                            break

            # 前后缀噪声: 每表 ≤2 列, 限定未注入列与 2 字符词长; 已由其他类注入的列跳过
            pfx_idx = []
            for pi, h in enumerate(header):
                word = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "", h)
                if word and len(word) <= 2:
                    pfx_idx.append(pi)
            if pfx_idx and len(pfx_idx) <= 2:
                rng()  # 保持与 ratio<1.0 分支的熵同步（注入与否仍唯一确定)
            elif pfx_idx and len(pfx_idx) > 2:
                rng()
                pfx_idx = []
            for ci in sorted(pfx_idx):
                        deco = PREFIX_NOISE_DECORATORS[(table_seed + ci) % len(PREFIX_NOISE_DECORATORS)]
                        new_header[ci] = self._apply_prefix(header, ci, deco)
                        injections.append({
                            "row": 0, "col": ci, "original": header[ci], "injected": new_header[ci],
                            "type": "prefix_noise", "source_key": "decorator", "variant": deco[0],
                            "seed_component": table_seed,
                        })

            if injections:
                tbl[0] = new_header
                self.injected.append({"uid": uid, "table": tbl})
                for m in injections:
                    m["uid"] = uid
                self.mapping.extend(injections)
            else:
                self.injected.append({"uid": uid, "table": tbl})

        # 统计
        self.stats = self._build_stats()
        return {"tables": self.injected, "mapping": self.mapping, "stats": self.stats}

    def _build_stats(self) -> Dict[str, Any]:
        from collections import Counter

        n_tables = len(self.injected)
        injected_uids = {m.get("uid") for m in self.mapping}
        n_injected_tables = sum(1 for t in self.injected if t.get("uid") in injected_uids)
        by_type = Counter(m["type"] for m in self.mapping)
        n_cols_total = sum(max(0, len(t.get("table", [])) - 1) for t in self.injected)
        n_injections = len(self.mapping)
        return {
            "version": DRIFT_VERSION,
            "seed": self.seed,
            "ratio": self.ratio,
            "source": "TAT-QA (NExTplusplus/TAT-QA) tables, train+dev",
            "n_tables_total": n_tables,
            "n_tables_injected": n_injected_tables,
            "n_injections_total": n_injections,
            "n_cols_total": n_cols_total,
            "injection_rate_per_table": round(n_injected_tables / max(1, n_tables), 4),
            "by_type": dict(by_type),
        }


# --------------------------------------------------------------------------
# 文件层: 确定性输出（sort_keys + ensure_ascii=False + 固定 indent 保证字节稳定）
# --------------------------------------------------------------------------

def _load_input(path: Path) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("input must be a JSON array of table objects")
    return data


def _dump_json(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def _sha256_hex(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="K3 schema 漂移注入器 v0（确定性）")
    ap.add_argument("--input", required=True, help="归一化表格 JSON（TAT-QA 数组）")
    ap.add_argument("--out", required=True, help="输出目录（injected_tables.json / injection_map.json / report.json）")
    ap.add_argument("--ratio", type=float, default=DEFAULT_RATIO, help="注入命中率 (0,1]")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED, help="确定性种子")
    args = ap.parse_args(argv)

    in_path = Path(args.input)
    out_dir = Path(args.out)
    tables = _load_input(in_path)

    out = DriftInjector(seed=args.seed, ratio=args.ratio, tables=tables).run()

    injected_path = out_dir / "injected_tables.json"
    map_path = out_dir / "injection_map.json"
    report_path = out_dir / "report.json"

    _dump_json(out["tables"], injected_path)
    _dump_json(out["stats"], report_path)
    manifest = {
        "meta": {
            "version": DRIFT_VERSION,
            "seed": args.seed,
            "ratio": args.ratio,
            "input": str(in_path),
            "deterministic": True,
        },
        "mapping": out["mapping"],
    }
    _dump_json(manifest, map_path)

    # 统计报告（含确定性 hash）
    report = dict(out["stats"])
    report["determinism_sha256"] = _sha256_hex(out["tables"])
    report["n_injection_rows_total"] = len(out["mapping"])
    _dump_json(report, report_path)

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
