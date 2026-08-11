#!/usr/bin/env python3
"""T1 甲方视角体验审计: playwright 以第一次见系统的甲方身份走 :5050/m1 全表面。
只发现不修复。产出 JSON + 截图到 docs/experiments/2026-08-12_client_experience_audit/。
用法: venv/bin/python scripts/t1_client_experience_audit.py
"""
import json, os, time, traceback
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5050"
OUT = "docs/experiments/2026-08-12_client_experience_audit"
JIAHE = os.path.expanduser("~/wzh/m1_samples/scenario1/attachments/转发 嘉合基金客户对账单_att0_3R8006587045_客户对帐单_2026年04月01日.pdf")
FUXI_TXT = os.path.expanduser("~/wzh/m1_samples/sample_fuxi_hunhe25_20231101.txt")

RESULTS = []
CONSOLE_ERRS = []


STEPS = []


def step(name):
    def deco(fn):
        def wrap(ctx):
            t0 = time.time()
            try:
                note = fn(ctx) or ""
                RESULTS.append({"step": name, "ok": True, "ms": int((time.time()-t0)*1000), "note": note})
            except Exception as e:
                RESULTS.append({"step": name, "ok": False, "ms": int((time.time()-t0)*1000),
                                "note": f"FAIL: {type(e).__name__}: {e}"})
                traceback.print_exc()
        STEPS.append(wrap)
        return wrap
    return deco


def run():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(accept_downloads=True, permissions=["clipboard-read", "clipboard-write"])
        pg = ctx.new_page()
        pg.on("console", lambda m: CONSOLE_ERRS.append(m.text) if m.type in ("error",) else None)
        pg.on("pageerror", lambda e: CONSOLE_ERRS.append(f"pageerror: {e}"))

        pg.goto(BASE + "/m1", timeout=30000)
        pg.wait_for_load_state("networkidle")

        @step("01 首屏空态")
        def s01(c):
            hint = pg.eval_on_selector("#m2ChatLog", "e => e.innerText.slice(0,80)")
            tc = pg.text_content("#tableCount")
            pg.screenshot(path=f"{OUT}/01_empty.png", full_page=True)
            return f"tableCount={tc!r} m2hint={hint!r}"

        @step("02 Sample 解析")
        def s02(c):
            pg.click("#sampleBtn")
            pg.wait_for_function("document.querySelector('#tableCount').textContent !== '-'", timeout=30000)
            pg.screenshot(path=f"{OUT}/02_sample.png", full_page=True)
            return f"tables={pg.text_content('#tableCount')} review={pg.text_content('#reviewBadge')}"

        @step("03 上传 PDF(嘉合)")
        def s03(c):
            pg.set_input_files("#fileInput", JIAHE)
            pg.wait_for_function("document.querySelector('#tableCount').textContent !== '-'", timeout=60000)
            return f"tables={pg.text_content('#tableCount')} review={pg.text_content('#reviewBadge')}"

        @step("04 上传 TXT(复熙)")
        def s04(c):
            pg.set_input_files("#fileInput", FUXI_TXT)
            pg.wait_for_function("document.querySelector('#tableCount').textContent !== '-'", timeout=60000)
            return f"tables={pg.text_content('#tableCount')}"

        @step("05 精确解析开关")
        def s05(c):
            pg.check("#preciseParseChk")
            pg.click("#sampleBtn")
            pg.wait_for_function("document.querySelector('#tableCount').textContent !== '-'", timeout=30000)
            notice = pg.text_content("#notice") or ""
            pg.uncheck("#preciseParseChk")
            return f"notice={notice[:60]!r}"

        @step("06 建议映射面板")
        def s06(c):
            pg.click("#suggBtn")
            pg.wait_for_selector("#suggModal:not([hidden])", timeout=5000)
            n = pg.eval_on_selector("#suggList", "e => e.children.length")
            pg.screenshot(path=f"{OUT}/06_sugg.png")
            pg.click("#suggCloseBtn")
            return f"pending_items={n}"

        @step("07 规则配置模态")
        def s07(c):
            pg.click("#schemaBtn")
            pg.wait_for_selector("#schemaModal:not([hidden])", timeout=5000)
            pg.eval_on_selector("#schemaTableList li", "e => e.click()")
            pg.wait_for_timeout(500)
            rows = pg.eval_on_selector("#schemaFieldsBody", "e => e.children.length")
            pg.screenshot(path=f"{OUT}/07_schema.png")
            pg.click("#schemaCloseBtn")
            return f"field_rows={rows}"

        @step("08 Copy/Download M2")
        def s08(c):
            pg.click("#copyBtn")
            pg.wait_for_timeout(400)
            clip = pg.evaluate("navigator.clipboard.readText().catch(e => 'CLIP_ERR')")
            with pg.expect_download(timeout=10000) as d:
                pg.click("#downloadBtn")
            dn = d.value.suggested_filename
            return f"clip_len={len(clip or '')} download={dn}"

        qs = [("09 QA 基础", "复熙混合25号的资产总值是多少？"),
              ("10 QA 追问", "那它的证券市值呢？"),
              ("11 QA 简称", "嘉兴民安的总资产是多少？"),
              ("12 QA 无数据", "星辰私募1号的资产总值是多少？"),
              ("13 QA OCR溯源", "哪个样本通过OCR解析了交易对账单？")]

        def ask(q):
            pg.fill("#m2Question", q)
            pg.click("#m2AskBtn")
            pg.wait_for_function(
                "(() => { const l = document.querySelector('#m2ChatLog'); const b = l.querySelectorAll('.m2-bubble, .m2-a, div'); return l.innerText.length > 0 && !l.querySelector('.m2-empty-hint'); })()",
                timeout=90000)
            # 等最后一条回答稳定
            prev = -1
            for _ in range(30):
                cur = pg.eval_on_selector("#m2ChatLog", "e => e.innerText.length")
                if cur == prev and cur > 0:
                    break
                prev = cur
                pg.wait_for_timeout(700)
            return pg.eval_on_selector("#m2ChatLog", "e => e.innerText.slice(-220)")

        for name, q in qs:
            @step(name)
            def sq(c, q=q):
                tail = ask(q)
                pg.screenshot(path=f"{OUT}/{name.split()[0]}_qa.png", full_page=False)
                return f"tail={tail[:150]!r}"

        @step("14 持仓对比")
        def s14(c):
            pg.wait_for_function("document.querySelector('#cmpProduct').options.length > 1", timeout=10000)
            pg.select_option("#cmpProduct", index=1)
            pg.click("#cmpPosBtn")
            pg.wait_for_timeout(1500)
            txt = pg.text_content("#cmpResult") or ""
            pg.screenshot(path=f"{OUT}/14_compare.png")
            return f"result_len={len(txt)} head={txt[:80]!r}"

        @step("15 New Chat")
        def s15(c):
            pg.click("#m2NewChatBtn")
            pg.wait_for_timeout(500)
            hint = pg.eval_on_selector("#m2ChatLog", "e => e.innerText.slice(0,60)")
            return f"after_reset={hint!r}"

        for w in STEPS:
            w(None)
        b.close()

    json.dump({"results": RESULTS, "console_errors": CONSOLE_ERRS},
              open(f"{OUT}/audit_raw.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"n_steps": len(RESULTS), "fails": [r['step'] for r in RESULTS if not r['ok']],
                      "console_errors": len(CONSOLE_ERRS)}, ensure_ascii=False))


if __name__ == "__main__":
    run()
