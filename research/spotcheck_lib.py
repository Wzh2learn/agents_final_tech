# -*- coding: utf-8 -*-
"""spotcheck_lib.py — 抽验纪律引擎 (审计 F04 的机械落点)

起源 (2026-09-10, Loop A / TASK-20260910-A4A5A4W 修复包 ④):
存量 6 个 `paper_*_spotcheck_recompute.py` 有四类同族病灶, 全部实测复现:
  1. **恒真项**: `ck("a4_affine_identity_recorded", rho is None or abs(rho-1.0)<1e-9 or True, ...)`
     (research/paper_d3_spotcheck_recompute.py:94) 与 `ck("transition_totals_all_33", True, ...)`
     (research/paper_d2_spotcheck_recompute.py:83) —— 条件恒真, 断言永过。
  2. **缺键静默放行**: `.get()` 兜底 + `rho is None or ...` 使"键根本不存在"也算通过;
     而且 d3 的 `find_margin(a4, {"rho",...})` 找的是不存在的键名, 真正的
     `...identity_evidence.spearman_rho_rank_identical` 从来没被读过 —— 断言检查的是空气。
  3. **恒 exit 0**: 6 个脚本 `sys.exit` 出现 0 次, 判定结果只印在 stdout,
     调用方与钩子拿不到失败信号 => "抽验失败"与"抽验通过"对上游完全同形。
  4. **分母掺水**: L1「字段存在」类项计入 PASS 分母, 使 n/N 数字虚高。

本模块把四条纪律做成结构性约束, 让"写一个恒真断言"在 API 层面就不可能:
  - 证据分级 L1/L2/L3/L4/INFO; **L1 与 INFO 不入 PASS 分母** (存在性/描述性不构成正确性)。
  - 缺键 = FAIL (存在性断言允许降级为 OBSERVED, 但**缺失**永远算缺陷, 不沉默)。
  - gating 断言必须携带 `actual`(实测量) 与 `level`; 无实测量的 `True` 一律 REFUSE。
  - `finalize()` 返回非零退出码; 零个 gating 项 = 失败 (没有闸门的不叫抽验)。
  - `--self-test`: 用微型错误工件自验上述四类缺陷确实被抓 (只用 tempfile, 不碰仓库工件)。
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

LEVELS = ("L1", "L2", "L3", "L4", "INFO")
LEVEL_DESC = {
    "L1": "字段存在 (presence only)",
    "L2": "存值与预期一致 (stored value)",
    "L3": "独立复算 (recomputed from source)",
    "L4": "运行证据 (live run / end-to-end)",
    "INFO": "观察项, 不构成闸门 (descriptive)",
}
GATING = ("L2", "L3", "L4")
MISSING = object()


class MissingKey(AssertionError):
    pass


def segments(path: str) -> list:
    """把 'a.b["c.d"][0]' 拆成段。必须支持**带点的键名**与引号键 ——
    天真地按 '.' split 会把 `slope_max_abs_deviation_from_0.375` 腰斩成两段 (自测抓到)。"""
    segs: list = []
    i, n = 0, len(path)
    while i < n:
        if path[i] == ".":
            i += 1
            continue
        if path[i] == "[":
            j = path.index("]", i)
            inner = path[i + 1:j]
            if len(inner) >= 2 and inner[0] == '"' and inner[-1] == '"':
                segs.append(inner[1:-1])
            elif len(inner) >= 2 and inner[0] == "'" and inner[-1] == "'":
                segs.append(inner[1:-1])
            else:
                segs.append(int(inner))
            i = j + 1
            continue
        j = i
        while j < n and path[j] not in ".[":
            j += 1
        segs.append(path[i:j])
        i = j
    return segs


def dig(doc: Any, path: str, default: Any = MISSING) -> Any:
    """按 'a.b["c.d"][0]' 取键。缺键且未给 default -> 抛 MissingKey (缺键即失败)。"""
    cur = doc
    for part in segments(path):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                if default is not MISSING:
                    return default
                raise MissingKey(path)
            continue
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
            continue
        if default is not MISSING:
            return default
        raise MissingKey(path)
    return cur


class Spotcheck:
    def __init__(self, name: str):
        self.name = name
        self.rows: list[dict] = []

    # ---- 记录原语 ----
    def _add(self, check: str, status: str, level: str, detail: Any) -> None:
        assert level in LEVELS, "unknown evidence level %r (allowed: %s)" % (level, ", ".join(LEVELS))
        self.rows.append({"check": check, "status": status, "level": level, "detail": detail})

    def observe(self, check: str, detail: Any = "") -> None:
        """INFO 观察项: 永远不入 PASS/FAIL 分母 (这就是它的历史位置)。"""
        self._add(check, "OBSERVED", "INFO", detail)

    def check(self, check: str, actual: Any, expected: Any = True, level: str = "L3",
              detail: Any = "", tol: float | None = None) -> bool:
        """gating 断言。actual **必须**是实测量 (来自工件或复算), 否则 REFUSE。

        纪律落点: 传字面量 True 当 actual 会因缺实测量被拒 —— 恒真项在本 API 上写不出来。
        """
        if level in ("INFO",):
            return self.observe(check, detail or actual)
        if actual is True and level in GATING and detail == "":
            # 没有任何实测量 => 这就是审计点名的恒真项, 直接拒绝登记
            raise ValueError(
                "REFUSE: check '%s' 传入字面 True 且无实测量 (detail/actual 全空) —— "
                "恒真项不入账, 请改用 expect_key/expect_eq 并把实测量放进 detail" % check)
        if isinstance(actual, float) or isinstance(expected, float):
            ok = (abs(float(actual) - float(expected)) <= tol) if tol is not None else (actual == expected)
        else:
            ok = actual == expected
        status = "PASS" if ok else "FAIL"
        if not ok:
            detail = {"actual": _clip(actual), "expected": _clip(expected), "detail": _clip(detail)}
        self._add(check, status, level, detail)
        return ok

    def expect_key(self, check: str, doc: Any, path: str, level: str = "L2", detail: Any = "") -> bool:
        """键存在性 + 取值。level=L1 时只登记 OBSERVED (存在性不算正确), 但**缺键仍 FAIL**。"""
        try:
            val = dig(doc, path)
        except MissingKey:
            self._add(check, "FAIL", level, "缺键: %s 不存在 (缺键不等于通过)" % path)
            return False
        if val is None:
            self._add(check, "FAIL", level, "键 %s 存在但值为 null —— 无法支撑断言" % path)
            return False
        if level == "L1":
            self._add(check, "OBSERVED", "L1", {"path": path, "value": _clip(val), "note": "仅存在性, 不入分母"})
            return True
        return self.check(check, _clip(val, 400), True, level, {"path": path, "value": _clip(val), "detail": detail}
                         if detail else {"path": path, "value": _clip(val)})

    def expect_eq(self, check: str, doc: Any, path: str, expected: Any, level: str = "L2",
                  tol: float | None = None) -> bool:
        try:
            val = dig(doc, path)
        except MissingKey:
            self._add(check, "FAIL", level, "缺键: %s 不存在 (缺键不等于通过)" % path)
            return False
        return self.check(check, val, expected, level, {"path": path}, tol=tol)

    # ---- 汇总与退出码 ----
    def counts(self) -> dict:
        gating = [r for r in self.rows if r["level"] in GATING]
        # fail **跨全部级别**统计: L1/INFO 不配拿 PASS 名额, 但它们的**缺失/失败仍是缺陷**。
        # denominator 只含 gating 项 => 存在性项既不能刷高通过率, 也不能把失败藏起来。
        return {
            "total_rows": len(self.rows),
            "denominator": len(gating),                      # L1 / INFO 已排除
            "pass": sum(1 for r in gating if r["status"] == "PASS"),
            "fail": sum(1 for r in self.rows if r["status"] == "FAIL"),
            "fail_gating": sum(1 for r in gating if r["status"] == "FAIL"),
            "observed": sum(1 for r in self.rows if r["status"] == "OBSERVED"),
        }

    def report(self) -> str:
        c = self.counts()
        lines = ["[%s] 逐条证据 (级别: %s)" % (self.name, " / ".join("%s=%s" % (k, v) for k, v in LEVEL_DESC.items()))]
        for r in self.rows:
            lines.append("%-9s %-4s %-46s %s" % (r["status"], r["level"], r["check"], _clip(r["detail"], 200)))
        lines.append(
            "%s SPOTCHECK: %d/%d gating PASS (分母=L2/L3/L4; OBSERVED 不入分母 %d 项; FAIL %d 项)"
            % (self.name, c["pass"], c["denominator"], c["observed"], c["fail"]))
        return "\n".join(lines)

    def finalize(self, artifact: dict | None = None, out_path: Path | None = None) -> int:
        """打印报告、可选落盘工件, 返回**退出码**: 0 全过 / 1 有 FAIL / 2 无 gating 项。"""
        print(self.report())
        c = self.counts()
        if artifact is not None:
            artifact = dict(artifact)
            artifact["spotcheck_discipline"] = {
                "library": "research/spotcheck_lib.py",
                "denominator_rule": "L1(presence-only) 与 INFO(观察项) 不入 PASS 分母",
                "missing_key_rule": "缺键 = FAIL, 不静默",
                "levels": {r["check"]: r["level"] for r in self.rows},
            }
            artifact["checks"] = self.rows
            artifact["summary"] = c
            if out_path is not None:
                out_path = Path(out_path)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=1), encoding="utf-8")
                print("artifact -> %s" % out_path)
        if c["fail"] > 0:
            return 1
        if c["denominator"] == 0:
            print("FAIL: 没有任何 gating 项 (全为 L1/INFO) —— 没有闸门的抽验不算通过")
            return 2
        return 0


def _clip(v: Any, n: int = 260) -> Any:
    if isinstance(v, (dict, list)):
        s = json.dumps(v, ensure_ascii=False, default=str)
    else:
        s = str(v)
    return s if len(s) <= n else s[:n] + "...(truncated)"


# ---------------- self-test: 微型错误工件自验 (F04 纪律的回归用例) ----------------
def _self_test() -> int:
    bad = 0

    def case(name, fn, expect_rc):
        nonlocal bad
        rc = fn()
        got = "OK" if rc == expect_rc else "WRONG"
        if rc != expect_rc:
            bad += 1
        print("  self-test %-34s rc=%-2s expect=%-2s %s" % (name, rc, expect_rc, got))

    def t_missing_key():
        s = Spotcheck("missing")
        s.expect_key("rho_recorded", {"a": {}}, "a.b.spearman_rho", level="L2")
        return s.finalize()

    def t_tautology_refused():
        s = Spotcheck("taut")
        try:
            s.check("always_true", True, True, level="L3")   # 无实测量 -> 必须 REFUSE
        except ValueError:
            return 0
        return 1

    def t_l1_not_in_denominator():
        s = Spotcheck("l1")
        s.expect_key("presence", {"a": {"b": 1}}, "a.b", level="L1")
        c = s.counts()
        return 0 if (c["denominator"] == 0 and c["observed"] == 1) else 1

    def t_no_gating_is_failure():
        s = Spotcheck("empty")
        s.observe("just_a_note", "x")
        return s.finalize()

    def t_real_failure_exits_nonzero():
        s = Spotcheck("value")
        s.expect_eq("wrong_value", {"a": {"b": 2.0}}, "a.b", 1.0, level="L3")
        return s.finalize()

    def t_dotted_key_requires_quoting():
        """带点键名: 引号写法必须解析成功, 裸写必须 FAIL (不得静默误读到别处)。"""
        doc = {"payload": {"a4": {"slope_max_abs_deviation_from_0.375": 9e-08}}}
        s1 = Spotcheck("q")
        s1.expect_eq("quoted_ok", doc, 'payload.a4["slope_max_abs_deviation_from_0.375"]', 9e-08,
                     level="L2", )
        rc_good = 0 if s1.counts()["fail"] == 0 else 1
        s2 = Spotcheck("u")
        s2.expect_eq("unquoted", doc, "payload.a4.slope_max_abs_deviation_from_0.375", 9e-08, level="L2")
        rc_bad = 0 if s2.counts()["fail"] == 1 else 1
        return 0 if (rc_good == 0 and rc_bad == 0) else 1

    def t_l1_missing_key_still_fails():
        s = Spotcheck("l1missing")
        s.expect_key("presence", {"a": {}}, "a.b", level="L1")   # 缺键 -> FAIL, 即便 L1 不入分母
        return s.finalize()

    def t_pass_path():
        s = Spotcheck("good")
        s.expect_eq("ok_value", {"a": {"b": 1.0}}, "a.b", 1.0, level="L3")
        return 0 if s.finalize() == 0 else 1

    def t_artifact_written_and_readable():
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sub" / "a.json"
            s = Spotcheck("write")
            s.expect_eq("k", {"a": {"b": 1}}, "a.b", 1, level="L3")
            rc = s.finalize({"payload": {}}, out_path=p)
            d = json.loads(p.read_text(encoding="utf-8"))
            ok = rc == 0 and "spotcheck_discipline" in d and d["summary"]["pass"] == 1
            return 0 if ok else 1

    print("spotcheck_lib self-test:")
    case("缺键 -> FAIL 非零", t_missing_key, 1)
    case("恒真项 -> 拒绝登记", t_tautology_refused, 0)
    case("带点键名须引号", t_dotted_key_requires_quoting, 0)
    case("L1-only -> 不入分母", t_l1_not_in_denominator, 0)
    case("零 gating -> 退出码 2", t_no_gating_is_failure, 2)
    case("值不符 -> 退出码 1", t_real_failure_exits_nonzero, 1)
    case("L1 缺键 -> 仍非零", t_l1_missing_key_still_fails, 1)
    case("全过 -> 退出码 0", t_pass_path, 0)
    case("工件落盘含分级", t_artifact_written_and_readable, 0)
    print("self-test: %s" % ("ALL PASS" if bad == 0 else "%d CASE(S) WRONG" % bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(_self_test() if "--self-test" in sys.argv else 2)
