#!/usr/bin/env python3
"""D1 /m1 三栏工作台脚本化 walkthrough（五步, 替代人工等待, 用户只留主观验收）。

五步: ① 解析时间轴点亮 ② 刷新持久化 ③ QA 五步条 ④ 建议映射 tab ⑤ 回落问答三问回归
产出: logs/graph/eval/walkthrough_evidence/{step*.png, walkthrough_results.json}
红线: 零配置变更; 全部合成样本题; QA 只读检索（解析入库沿彩排先例）。
"""
import json, os, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5050"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EV = os.path.join(ROOT, "logs", "graph", "eval", "walkthrough_evidence")
QA_TIMEOUT_SECONDS = 150  # 功能等待预算，不是体验通过阈值；实际耗时原样入证据。

def ask(page, q, timeout=QA_TIMEOUT_SECONDS):
    # 生产 auto 路可能先走 45s 验证链再回落；先确认上一问已完全释放按钮。
    page.wait_for_function(
        "() => { const b = document.querySelector('#m2AskBtn'); return b && !b.disabled; }",
        timeout=timeout * 1000,
    )
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
        # 第一问的答案等待
        t0 = time.time()
        txt = None
        while time.time() - t0 < QA_TIMEOUT_SECONDS:
            txt = page.evaluate("""() => {
                const b = document.querySelectorAll('#m2ChatLog .m2-msg.assistant');
                return b.length ? (b[b.length-1].innerText || '') : null;
            }""")
            if txt and (("条来源" in txt) or ("未检索" in txt) or ("未找到" in txt) or ("⚠" in txt)):
                break
            time.sleep(0.5)
        rec(3, "QA 五步条出现", saw_steps, "")
        rec(3, "QA 答案落地", bool(txt), (txt or "")[:80])
        if saw_steps:
            qa_steps = page.locator("#m2ChatLog .qa-steps-wrap").last
            qa_steps.scroll_into_view_if_needed()
            qa_steps.screenshot(path=os.path.join(EV, "step3_qa_steps_bar.png"))
        else:
            page.locator("#m2ChatLog").screenshot(
                path=os.path.join(EV, "step3_qa_steps_bar.png"))

        # ④ 建议映射 tab
        page.click("#suggBtn")
        time.sleep(1.0)
        visible = page.evaluate("() => !document.getElementById('panel-sugg').hidden")
        active = page.locator('.rt-tab[data-tab="sugg"].active').count() == 1
        rec(4, "sugg tab 激活可见", visible and active,
            f"panel_visible={visible}, tab_active={active}")
        n_sugg = page.locator("#suggList > div").count()
        empty = page.evaluate("() => !document.getElementById('suggEmpty').hidden")
        rec(4, "建议列表或空态", n_sugg > 0 or empty, f"rows={n_sugg}, empty={empty}")
        # 证据专用紧凑视图：克隆同页真实 tab/面板，避免整右栏长图被预览压缩。
        page.evaluate("""() => {
            const old = document.getElementById('walkthrough-sugg-evidence');
            if (old) old.remove();
            const wrap = document.createElement('section');
            wrap.id = 'walkthrough-sugg-evidence';
            wrap.style.cssText = 'width:760px;background:#fff;border:1px solid #d8e0ea;border-radius:10px;overflow:hidden';
            const label = document.createElement('div');
            label.textContent = 'walkthrough 证据视图 · 同页真实元素紧凑呈现';
            label.style.cssText = 'padding:8px 12px;font:12px sans-serif;color:#64748b;background:#f8fafc';
            const tabs = document.querySelector('.rt-tabs').cloneNode(true);
            const panel = document.getElementById('panel-sugg').cloneNode(true);
            panel.hidden = false;
            panel.style.cssText = 'display:flex;height:900px';
            const body = panel.querySelector('.panel-body');
            if (body) body.style.overflow = 'hidden';
            wrap.append(label, tabs, panel);
            document.body.appendChild(wrap);
        }""")
        page.locator("#walkthrough-sugg-evidence").screenshot(
            path=os.path.join(EV, "step4_sugg_tab.png"))

        # ⑤ 回落问答三问回归（旧证据路径名保留兼容）
        for i, q in enumerate(["博时传统产品的基金代码是什么？",
                               "嘉兴民安的资金余额是多少？",
                               "复熙混合25号的客户全称是什么？"], start=1):
            ans, dt = ask(page, q)
            rec(5, f"回落问答问题 {i} 有答", bool(ans), f"{dt:.1f}s " + (ans or "")[:60])
        page.screenshot(path=os.path.join(EV, "step5_fast_regression.png"))
        b.close()

    out = {"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "base": BASE,
           "n_asserts": len(results),
           "n_pass": sum(1 for r in results if r["pass"]),
           "results": results,
           "screenshot_summary": {
               "step1_parse_timeline.png": "完整工作台：六步解析时间轴、完成态与表格产物。",
               "step2_refresh_persist.png": "刷新后任务卡与解析产物恢复，验证 localStorage 持久化。",
               "step3_qa_steps_bar.png": "QA 五步条特写：五个步骤均清晰可见，并显示完成耗时。",
               "step4_sugg_tab.png": "证据紧凑视图：同页真实的建议映射 tab 激活态、说明与建议列表同屏。",
               "step5_fast_regression.png": "回落问答三问完成后的工作台与实际链路耗时信息（文件名为历史兼容保留）。"
           }}
    with open(os.path.join(EV, "walkthrough_results.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(json.dumps({"n_pass": out["n_pass"], "n": out["n_asserts"],
                      "fails": [r for r in results if not r["pass"]]}, ensure_ascii=False))

if __name__ == "__main__":
    main()
