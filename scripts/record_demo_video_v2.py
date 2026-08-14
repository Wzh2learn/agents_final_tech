#!/usr/bin/env python3
"""Demo video v2: re-record per advisor-review V1-V7.

Segments recorded as webm (playwright recordVideo); assembly (cards/speedup/concat)
in assemble_demo_video_v2.py. Route handling is orchestrated by the operator:
phase A segs need M2_OPENCODE_ROUTE=off; seg_agent needs =on.
"""
import os, sys, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5050"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "experiments", "2026-08-15_demo_video_v2", "segs")
ATT = os.path.expanduser("~/wzh/m1_samples/scenario1/attachments")
JIAHE = os.path.join(ATT, "转发 嘉合基金客户对账单_att0_3R8006587045_客户对帐单_2026年04月01日.pdf")
WAVEFAX = os.path.join(ATT, "转发 来自：(WaveFax Fax Device)_att0_20260506_132650IU.pdf")
GUOJIN = os.path.join(ATT, "转发 2026年4月国金基金开放式基金对账单_body.txt")

BANNER_JS = """(t) => {
  let b = document.getElementById('__demo_banner');
  if (!b) {
    b = document.createElement('div');
    b.id = '__demo_banner';
    b.style.cssText = 'position:fixed;left:0;bottom:0;width:100%;' +
      'background:rgba(17,24,39,0.94);color:#fff;padding:10px 20px;' +
      'font:600 15px/1.6 system-ui;z-index:99999;border-top:3px solid #2563eb;' +
      'box-sizing:border-box';
    document.body.appendChild(b);
  }
  b.textContent = t;
}"""

def banner(page, text, hold=3.0):
    page.evaluate(BANNER_JS, text)
    time.sleep(hold)

def last_assistant(page):
    return page.evaluate("""() => {
        const log = document.getElementById('m2ChatLog');
        if (!log) return '';
        const b = log.querySelectorAll('.m2-msg.assistant');
        return b.length ? (b[b.length-1].innerText || '') : '';
    }""")

def ask(page, q, timeout=90):
    page.fill("#m2Question", q)
    time.sleep(0.4)
    page.click("#m2AskBtn")
    t0 = time.time(); last = None; stable = time.time()
    while time.time() - t0 < timeout:
        txt = last_assistant(page)
        done = ("条来源" in txt) or ("未检索" in txt) or ("未找到" in txt) or ("无法提供" in txt)
        if done:
            if txt == last and time.time() - stable > 1.5:
                return txt
            if txt != last:
                last = txt; stable = time.time()
        else:
            last = None
        time.sleep(0.5)
    return last_assistant(page)

def upload(page, path, timeout=300):
    page.set_input_files("#fileInput", path)
    t0 = time.time()
    while time.time() - t0 < timeout:
        tc = page.evaluate("() => (document.getElementById('tableCount')||{}).textContent || ''").strip()
        badge = page.evaluate("() => (document.getElementById('reviewBadge')||{}).textContent || ''").strip()
        if tc not in ("", "-", "0 表") and badge not in ("", "-"):
            break
        time.sleep(1.0)
    time.sleep(2.0)

def new_context(p, browser):
    return browser.new_context(
        viewport={"width": 1440, "height": 900},
        record_video_dir=OUT,
        record_video_size={"width": 1440, "height": 900},
    )

def seg_open(p, browser):
    ctx = new_context(p, browser); page = ctx.new_page()
    page.goto(BASE + "/m1"); page.wait_for_load_state("networkidle")
    banner(page, "段 1｜Sample 一键解析：三面板信息架构（解析结果/表头信息/复核校验）", 4)
    page.click("#sampleBtn")
    t0 = time.time()
    while time.time() - t0 < 60:
        tc = page.evaluate("() => (document.getElementById('tableCount')||{}).textContent || ''").strip()
        if tc not in ("", "-", "0 表"): break
        time.sleep(1.0)
    time.sleep(2.0)
    banner(page, "一屏闭环：解析 → 映射 → 校验，减少页面跳转", 4)
    page.evaluate("document.getElementById('reconcileSection') && document.getElementById('reconcileSection').scrollIntoView()")
    time.sleep(2.5)
    page.evaluate("window.scrollTo(0,0)"); time.sleep(1.5)
    ctx.close()

def seg_qa_direct(p, browser):
    ctx = new_context(p, browser); page = ctx.new_page()
    page.goto(BASE + "/m1"); page.wait_for_load_state("networkidle")
    banner(page, "段 2｜直连路快问快答（约 2 秒/轮，适合快速交互）", 4)
    ask(page, "复熙混合25号的资产总值是多少？")
    page.evaluate("""() => {
        const log = document.getElementById('m2ChatLog');
        const b = log.querySelectorAll('.m2-msg.assistant');
        const t = b[b.length-1] && b[b.length-1].querySelector('.m2-sources-toggle');
        if (t) t.click();
    }""")
    time.sleep(1.0)
    banner(page, "数字带溯源：样本 / 表名 / score / 原文片段，无出处的数字不显示", 4.5)
    ask(page, "嘉兴民安的总资产是多少？")
    banner(page, "连续快问均秒级出答、带出处", 3.5)
    ctx.close()

def seg_transparency(p, browser):
    ctx = new_context(p, browser); page = ctx.new_page()
    page.goto(BASE + "/m1"); page.wait_for_load_state("networkidle")
    banner(page, "段 3｜检索透明面板：top_k / 路由 / 耗时，全部对用户可见", 4)
    ask(page, "复熙混合25号的单位净值是多少？")
    page.select_option("#m2TopK", "5"); time.sleep(1.0)
    banner(page, "top_k 可调（3/5/8/10）：用户自己控制检索条数", 4)
    ask(page, "嘉兴民安的总资产是多少？")
    page.select_option("#m2TopK", "8"); time.sleep(1.0)
    banner(page, "meta 行逐问标注：走哪条路、检索几条、花了多久——系统不藏东西", 4.5)
    ctx.close()

def seg_jiahe(p, browser):
    ctx = new_context(p, browser); page = ctx.new_page()
    page.goto(BASE + "/m1"); page.wait_for_load_state("networkidle")
    banner(page, "段 4｜上传嘉合客户对账单（电子件，毫秒级解析）", 4)
    upload(page, JIAHE, timeout=60)
    banner(page, "嘉合同版式 8 份：一轮 93.8% → 规则沉淀后 100%", 5)
    ctx.close()

def seg_suggestions_a(p, browser):
    ctx = new_context(p, browser); page = ctx.new_page()
    page.goto(BASE + "/m1"); page.wait_for_load_state("networkidle")
    banner(page, "段 5｜建议映射选择题面板：上传国金对账单，系统生成映射建议（等待段 4 倍速）", 4)
    upload(page, GUOJIN, timeout=180)
    ctx.close()

def seg_suggestions_b(p, browser):
    ctx = new_context(p, browser); page = ctx.new_page()
    page.goto(BASE + "/m1"); page.wait_for_load_state("networkidle")
    page.click("#suggBtn"); time.sleep(1.5)
    banner(page, "原列名 / 建议标准字段 / 置信度 / 理由，可勾选应用或拒绝", 5)
    page.evaluate("""() => {
        const cb = document.querySelector('#suggModal input[type=checkbox]');
        if (cb) cb.click();
    }""")
    time.sleep(1.5)
    banner(page, "应用后自动跑全量回归门禁，命中率下降自动回滚（最难样本 35.7%→100% 即此闭环）", 5.5)
    page.click("#suggCloseBtn"); time.sleep(1.0)
    ctx.close()

def seg_review_multiturn_refusal(p, browser):
    ctx = new_context(p, browser); page = ctx.new_page()
    page.goto(BASE + "/m1"); page.wait_for_load_state("networkidle")
    page.click("#sampleBtn"); time.sleep(3.0)
    banner(page, "段 6｜复核面板 + 多轮追问 + 诚实拒答", 4)
    page.evaluate("document.getElementById('reconcileSection') && document.getElementById('reconcileSection').scrollIntoView()")
    banner(page, "勾稽校验如实标注；未映射列清单透明可见", 4)
    ask(page, "嘉兴民安的总资产是多少？")
    ask(page, "其中证券市值占多少？")
    banner(page, "追问\"其中…\"自动关联上一轮实体", 4)
    ask(page, "星辰私募1号的资产总值是多少？")
    banner(page, "库中没有的数据明确说\"未找到\"，不编造", 4.5)
    ctx.close()

def seg_ocr_a(p, browser):
    ctx = new_context(p, browser); page = ctx.new_page()
    page.goto(BASE + "/m1"); page.wait_for_load_state("networkidle")
    banner(page, "段 7｜传真扫描件：视觉模型看图识字，全本地推理（等待段 8 倍速）", 4)
    upload(page, WAVEFAX, timeout=300)
    ctx.close()

def seg_ocr_b(p, browser):
    ctx = new_context(p, browser); page = ctx.new_page()
    page.goto(BASE + "/m1"); page.wait_for_load_state("networkidle")
    banner(page, "重跑传真识别以展示结果面板", 3)
    upload(page, WAVEFAX, timeout=300)
    banner(page, "WaveFax：规则沉淀后 100%（TraFax 同类 50→81.8）", 5)
    time.sleep(1.5)
    ctx.close()

def seg_agent_a(p, browser):
    ctx = new_context(p, browser); page = ctx.new_page()
    page.goto(BASE + "/m1"); page.wait_for_load_state("networkidle")
    banner(page, "段 8｜验证链路：独立 agent 正在复核检索证据——快与准是菜单（等待段 4 倍速）", 4)
    ask(page, "嘉兴民安的总资产是多少？", timeout=120)
    ctx.close()

def seg_agent_b(p, browser):
    ctx = new_context(p, browser); page = ctx.new_page()
    page.goto(BASE + "/m1"); page.wait_for_load_state("networkidle")
    banner(page, "同一问题：展示验证链路答案与溯源", 3)
    ask(page, "嘉兴民安的总资产是多少？", timeout=120)
    banner(page, "验证链路 12-20 秒/轮，适合关键数字场景；与直连路数字一致、多一层独立复核", 5.5)
    ctx.close()

SEGS = {
    "open": seg_open, "qa_direct": seg_qa_direct, "transparency": seg_transparency,
    "jiahe": seg_jiahe, "suggestions_a": seg_suggestions_a, "suggestions_b": seg_suggestions_b,
    "review_mt_ref": seg_review_multiturn_refusal, "ocr_a": seg_ocr_a, "ocr_b": seg_ocr_b,
    "agent_a": seg_agent_a, "agent_b": seg_agent_b,
}

def make_cards(p, browser):
    out = os.path.join(ROOT, "docs", "experiments", "2026-08-15_demo_video_v2", "cards")
    os.makedirs(out, exist_ok=True)
    cards = {
        "card_open": ("基于 AI 的金融对账单智能解析与问答系统",
                      ["多格式解析（含扫描件） · 智能字段映射 · 勾稽校验",
                       "带溯源、可多轮、会诚实拒答的 RAG 问答",
                       "全部推理本地化，数据不出域"]),
        "card_end": ("快与准是菜单，不是取舍",
                     ["嘉合客户对账单 100%（一轮 93.8% → 沉淀后）",
                      "最难样本 35.7% → 100%（纯确定性规则）",
                      "RAG 问答 16/16 带溯源",
                      "下一步：前端改版 · 验证链路延迟治理 · 跨期对比"]),
    }
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    for name, (title, lines) in cards.items():
        html = "<html><body style='margin:0;background:#0f172a;display:flex;align-items:center;justify-content:center;height:900px;font-family:system-ui,\"Microsoft YaHei\",sans-serif;'>"
        html += "<div style='text-align:center;color:#fff;max-width:1100px;'>"
        html += f"<div style='font-size:44px;font-weight:700;line-height:1.4;'>{title}</div>"
        html += "<div style='margin-top:36px;'>"
        for ln in lines:
            html += f"<div style='font-size:24px;color:#cbd5e1;line-height:2.1;'>{ln}</div>"
        html += "</div></div></body></html>"
        page.goto("data:text/html;charset=utf-8," + __import__("urllib.parse", fromlist=["quote"]).quote(html))
        page.wait_for_timeout(300)
        page.screenshot(path=os.path.join(out, name + ".png"))
        print("[card]", name)
    ctx.close()

def main():
    names = sys.argv[1:] or ["cards"] + list(SEGS)
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name in names:
            t0 = time.time()
            if name == "cards":
                make_cards(p, browser)
            elif name in SEGS:
                print(f"[record] {name} ...", flush=True)
                SEGS[name](p, browser)
                print(f"[record] {name} done in {time.time()-t0:.0f}s", flush=True)
            else:
                sys.exit(f"unknown segment: {name}")
        browser.close()
    print("[record] done")

if __name__ == "__main__":
    main()