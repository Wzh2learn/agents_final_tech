#!/usr/bin/env python3
"""docs/23 发送版截图重拍 (2026-08-12): 按现 UI 重走关键屏, 含建议映射选择题面板。
产出 docs/experiments/2026-08-12_docs23_screenshots/*.png + shots_meta.json。
用法: venv/bin/python scripts/docs23_screenshots.py
"""
import json, os, time
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5050"
OUT = "docs/experiments/2026-08-12_docs23_screenshots"
JIAHE = os.path.expanduser("~/wzh/m1_samples/scenario1/attachments/转发 嘉合基金客户对账单_att0_3R8006587045_客户对帐单_2026年04月01日.pdf")
META = []


def shot(pg, name, full=True):
    pg.screenshot(path=f"{OUT}/{name}.png", full_page=full)
    META.append(name)
    print(f"[shot] {name}")


def wait_answer(pg, timeout_ms=90000):
    pg.wait_for_function(
        "(() => { const l = document.querySelector('#m2ChatLog');"
        " return l.innerText.length > 0 && !l.querySelector('.m2-empty-hint'); })()",
        timeout=timeout_ms)
    prev = -1
    for _ in range(40):
        cur = pg.eval_on_selector("#m2ChatLog", "e => e.innerText.length")
        if cur == prev and cur > 0:
            break
        prev = cur
        pg.wait_for_timeout(700)


def run():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1600, "height": 1000},
                            permissions=["clipboard-read", "clipboard-write"])
        pg = ctx.new_page()
        pg.goto(BASE + "/m1", timeout=30000)
        pg.wait_for_load_state("networkidle")

        shot(pg, "01_home")

        pg.click("#sampleBtn")
        pg.wait_for_function("document.querySelector('#tableCount').textContent !== '-'", timeout=30000)
        shot(pg, "02_sample")

        pg.set_input_files("#fileInput", JIAHE)
        pg.wait_for_function("document.querySelector('#tableCount').textContent !== '-'", timeout=60000)
        pg.wait_for_timeout(800)
        shot(pg, "03_upload_jiahe")
        body_txt = pg.eval_on_selector("body", "e => e.innerText")
        hit = next((l for l in body_txt.splitlines() if "命中率" in l), "")
        print("[info] jiahe hit line:", hit[:60])

        # 复核面板: 滚到 review 区
        pg.eval_on_selector("#reviewBadge", "e => e.scrollIntoView({block:'center'})")
        pg.wait_for_timeout(400)
        shot(pg, "04_reconcile", full=False)

        pg.click("#suggBtn")
        pg.wait_for_selector("#suggModal:not([hidden])", timeout=5000)
        n = pg.eval_on_selector("#suggList", "e => e.children.length")
        print("[info] suggestions pending:", n)
        shot(pg, "05_suggestions", full=False)
        pg.click("#suggCloseBtn")

        pg.click("#schemaBtn")
        pg.wait_for_selector("#schemaModal:not([hidden])", timeout=5000)
        pg.eval_on_selector("#schemaTableList li", "e => e.click()")
        pg.wait_for_timeout(500)
        shot(pg, "06_schema_rules", full=False)
        pg.click("#schemaCloseBtn")

        # QA: 干净会话
        pg.click("#m2NewChatBtn")
        pg.wait_for_timeout(400)

        def ask(q):
            pg.fill("#m2Question", q)
            pg.click("#m2AskBtn")
            wait_answer(pg)

        ask("复熙混合25号的资产总值是多少？")
        shot(pg, "07_qa_with_sources", full=False)

        ask("那它的证券市值呢？")
        shot(pg, "08_qa_followup", full=False)

        ask("星辰私募1号的资产总值是多少？")
        shot(pg, "09_qa_no_fabrication", full=False)

        # 持仓对比(简称)
        pg.wait_for_function("document.querySelector('#cmpProduct').options.length > 1", timeout=10000)
        opts = pg.eval_on_selector_all("#cmpProduct option",
                                       "els => els.map((e,i) => [i, e.textContent])")
        idx = next((i for i, t in opts if "嘉兴民安" in (t or "")), 1)
        pg.select_option("#cmpProduct", index=idx)
        pg.click("#cmpPosBtn")
        pg.wait_for_timeout(1500)
        txt = (pg.text_content("#cmpResult") or "")[:80]
        print("[info] compare head:", txt)
        pg.eval_on_selector("#cmpResult", "e => e.scrollIntoView({block:'center'})")
        pg.wait_for_timeout(300)
        shot(pg, "10_compare_positions", full=False)

        b.close()
    json.dump({"shots": META, "date": time.strftime("%Y-%m-%d %H:%M")},
              open(f"{OUT}/shots_meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[done] {len(META)} shots -> {OUT}")


if __name__ == "__main__":
    run()
