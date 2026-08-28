#!/usr/bin/env python3
"""D1 /m1 三栏工作台脚本化 walkthrough（五步, 替代人工等待, 用户只留主观验收）。

五步: ① 解析时间轴点亮 ② 刷新持久化 ③ QA 五步条 ④ 建议映射 tab ⑤ 快路三问回归
产出: logs/graph/eval/walkthrough_evidence/{step*.png, walkthrough_results.json}
红线: 零配置变更; 全部合成样本题; QA 只读检索（解析入库沿彩排先例）。
"""
import json, os, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5050"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "logs", "graph", "eval", "walkthrough_evidence")

def ask(page, q, timeout=60):
    before = page.evaluate(
        "() => document.querySelectorAll('#m2ChatLog .m2-msg.assistant').length")
    page.fill("#m2Question", q)
    time.sleep(0.3)
    page.click("#m2AskBtn")
    t0 = time.time()
    while time.time() - t0 < timeout:
        txt = page.evaluate("""(before) => {
            const b = document.querySelectorAll('#m2ChatLog .m2-msg.assistant');
            return b.length > before ? (b[b.length-1].innerText || '') : null;
        }""", before)
        if txt and (("条来源" in txt) or ("未检索" in txt) or ("未找到" in txt)
                    or ("无法提供" in txt) or ("⚠" in txt)):
            return txt, time.time() - t0
        time.sleep(0.5)
    return None, time.time() - t0

def main():
    os.makedirs(EV, exist_ok=True)
    results = []
    def rec(step, name, ok, detail=""):
        results.append({"step": step, "assert": name, "pass": bool(ok), "detail": str(detail)[:200]})
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        page = b.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE + "/m1", wait_until="networkidle", timeout=30000)

        # ① 解析时间轴点亮
        page.evaluate("() => localStorage.removeItem('m1v2_tasks')")
        page.reload(wait_until="networkidle")
        page.click("#sampleBtn")
        t0 = time.time()
        ok_steps = False
        while time.time() - t0 < 90:
            n = page.locator("#parseSteps .step-card.done").count()
            if n >= 6:
                ok_steps = True
                break
            time.sleep(0.5)
        rec(1, "六步卡全点亮", ok_steps, f"done={page.locator('#parseSteps .step-card.done').count()}/6, {(time.time()-t0):.1f}s")
        badge = page.locator("#execBadge").inner_text()
        rec(1, "任务徽章完成态", "完成" in badge or "待处理" in badge, badge)
        rec(1, "表格产物渲染", page.locator("#tableCount").inner_text() not in ("-", ""), page.locator("#tableCount").inner_text())
        rec(1, "任务卡入左栏", page.locator("#taskListParse .task-card").count() >= 1, page.locator("#taskListParse .task-card").count())
        page.screenshot(path=os.path.join(EV, "step1_parse_timeline.png"))
        task_title = page.locator("#taskTitle").inner_text()

        # ② 刷新持久化
        page.reload(wait_until="networkidle")
        time.sleep(0.6)
        n_task = page.locator("#taskListParse .task-card").count()
        rec(2, "刷新后任务卡仍在", n_task >= 1, f"n={n_task}")
        if n_task >= 1:
            page.locator("#taskListParse .task-card").first.click()
            time.sleep(0.8)
            rec(2, "点击任务恢复产物", page.locator("#tableCount").inner_text() not in ("-", ""), page.locator("#tableCount").inner_text())
        page.screenshot(path=os.path.join(EV, "step2_refresh_persist.png"))

        # ③ QA 五步条
        page.fill("#m2Question", "嘉兴民安的总资产是多少？")
        page.click("#m2AskBtn")
        saw_steps = False
        t0 = time.time()
        while time.time() - t0 < 8:
            if page.locator("#m2ChatLog .qa-steps").count() > 0:
                saw_steps = True
                break
            time.sleep(0.15)
        page.screenshot(path=os.path.join(EV, "step3_qa_steps_bar.png"))
        ans, dt = ask(page, "嘉合基金的对账单一共入库了几份？", timeout=60) if False else (None, 0)
        # 第一问的答案等待
        t0 = time.time()
        txt = None
        while time.time() - t0 < 60:
            txt = page.evaluate("""() => {
                const b = document.querySelectorAll('#m2ChatLog .m2-msg.assistant');
                return b.length ? (b[b.length-1].innerText || '') : null;
            }""")
            if txt and (("条来源" in txt) or ("未检索" in txt) or ("未找到" in txt) or ("⚠" in txt)):
                break
            time.sleep(0.5)
        rec(3, "QA 五步条出现", saw_steps, "")
        rec(3, "QA 答案落地", bool(txt), (txt or "")[:80])

        # ④ 建议映射 tab
        page.click("#suggBtn")
        time.sleep(1.0)
        visible = page.evaluate("() => !document.getElementById('panel-sugg').hidden")
        rec(4, "sugg tab 激活可见", visible, "")
        n_sugg = page.locator("#suggList > div").count()
        empty = page.evaluate("() => !document.getElementById('suggEmpty').hidden")
        rec(4, "建议列表或空态", n_sugg > 0 or empty, f"rows={n_sugg}, empty={empty}")
        page.screenshot(path=os.path.join(EV, "step4_sugg_tab.png"))

        # ⑤ 快路三问回归
        for i, q in enumerate(["博时传统产品的基金代码是什么？",
                               "嘉兴民安的资金余额是多少？",
                               "复熙混合25号的客户全称是什么？"], start=1):
            ans, dt = ask(page, q, timeout=60)
            rec(5, f"快路问题 {i} 有答", bool(ans), f"{dt:.1f}s " + (ans or "")[:60])
        page.screenshot(path=os.path.join(EV, "step5_fast_regression.png"))
        b.close()

    out = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "base": BASE,
           "n_asserts": len(results),
           "n_pass": sum(1 for r in results if r["pass"]),
           "results": results}
    with open(os.path.join(EV, "walkthrough_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({"n_pass": out["n_pass"], "n": out["n_asserts"],
                      "fails": [r for r in results if not r["pass"]]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
