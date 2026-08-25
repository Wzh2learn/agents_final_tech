#!/usr/bin/env python3
"""Demo v3 彩排闸 (S2): 全部分镜经 :5050 /m1 UI 真实走一遍。

成功判据: 每步拿到答案 (或预期拒答) 且未超时; agent 路问题记录完成/回落实况。
失败 = 修分镜或换题, 不赌录制运气。产出 rehearsal.json + /tmp/rehearse_done.txt。
红线: 零配置变更 (route=on 生产态), 全部使用测试题集。
"""
import json, os, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5050"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VD = os.path.join(ROOT, "docs", "experiments", "2026-08-25_demo_video_v3")

def last_assistant(page):
    return page.evaluate("""() => {
        const log = document.getElementById('m2ChatLog');
        if (!log) return '';
        const b = log.querySelectorAll('.m2-msg.assistant');
        return b.length ? (b[b.length-1].innerText || '') : '';
    }""")

def ask(page, q, timeout=90):
    """点击前后按 assistant 消息条数区分新答, 防多问题同页陈旧读。"""
    before = page.evaluate(
        "() => document.querySelectorAll('#m2ChatLog .m2-msg.assistant').length")
    page.fill("#m2Question", q)
    time.sleep(0.4)
    page.click("#m2AskBtn")
    t0 = time.time(); last = None; stable = time.time()
    while time.time() - t0 < timeout:
        txt = page.evaluate("""(before) => {
            const b = document.querySelectorAll('#m2ChatLog .m2-msg.assistant');
            return b.length > before ? (b[b.length-1].innerText || '') : null;
        }""", before)
        if txt:
            done = ("条来源" in txt) or ("未检索" in txt) or ("未找到" in txt) or ("无法提供" in txt)
            if done:
                if txt == last and time.time() - stable > 2.0:
                    return txt, time.time() - t0, False
                if txt != last:
                    last = txt; stable = time.time()
        time.sleep(0.5)
    return last_assistant(page), time.time() - t0, True

# (step, question|None, timeout)
STEPS = [
    ("home", None, 0),
    ("topk_ui", None, 0),
    ("q07_fast", "博时传统产品的基金代码是什么？", 45),
    ("q06_fast", "嘉兴民安的资金余额是多少？", 45),
    ("q01_agent", "复熙混合25号的资产总值是多少？", 75),
    ("refusal", "华夏成长混合基金的持仓明细有哪些？", 60),
    ("mt1", "嘉兴民安的总资产是多少？", 60),
    ("mt2_followup", "其中证券市值占多少？", 60),
]

def main():
    os.makedirs(VD, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()
        t0 = time.time()
        page.goto(BASE + "/m1", wait_until="networkidle", timeout=30000)
        ok_home = page.locator("#m2ChatLog").count() > 0
        results.append({"step": "home", "ok": ok_home, "elapsed": round(time.time() - t0, 1)})
        ok_topk = page.locator("#m2TopK").count() > 0
        results.append({"step": "topk_ui", "ok": ok_topk, "elapsed": 0})
        # warm-up: 预热冷态首请求 (不计结果), 彩排与录制口径一致
        wtxt, welapsed, wto = ask(page, "博时传统产品的基金名称是什么？", 60)
        print("warmup elapsed=%.1f timed_out=%s" % (welapsed, wto), flush=True)
        for name, q, timeout in STEPS:
            if q is None:
                continue
            txt, elapsed, timed_out = ask(page, q, timeout)
            ok = bool(txt) and not timed_out
            results.append({"step": name, "q": q, "elapsed": round(elapsed, 1),
                            "timed_out": timed_out, "ok": ok, "tail": (txt or "")[-180:]})
            print(json.dumps(results[-1], ensure_ascii=False), flush=True)
        browser.close()
    with open(os.path.join(VD, "rehearsal.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    all_ok = all(r["ok"] for r in results)
    print("REHEARSAL", "PASS" if all_ok else "REVIEW", flush=True)
    with open("/tmp/rehearse_done.txt", "w") as f:
        f.write("DONE")

if __name__ == "__main__":
    main()
