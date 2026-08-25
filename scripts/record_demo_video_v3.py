#!/usr/bin/env python3
"""Demo video v3: 十段结构 (2026-08-15 steps.md) + 现行口径。

录制: route=on 生产态, 零配置变更; 每段独立 context, playwright recordVideo webm。
用法: ./venv/bin/python scripts/record_demo_video_v3.py [seg|all]
段: home fast transparency jiahe sugg_a sugg_b review_mt_refusal ocr agent
"""
import os, sys, time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5050"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "experiments", "2026-08-25_demo_video_v3", "segs")
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
      'font:600 16px/1.6 system-ui;z-index:99999;border-top:3px solid #2563eb;' +
      'box-sizing:border-box';
    document.body.appendChild(b);
  }
  b.textContent = t;
}"""

def banner(page, text, hold=4.0):
    page.evaluate(BANNER_JS, text)
    time.sleep(hold)

def ensure_ask_ready(page, timeout=120):
    """等待 Ask 按钮可用 (前一请求在途时按钮 disabled)。"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if page.evaluate("() => { const b = document.getElementById('m2AskBtn'); return b && !b.disabled; }"):
            return True
        time.sleep(1.0)
    return False

def ask(page, q, timeout=90):
    ensure_ask_ready(page)
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
    return (last or ""), time.time() - t0, True

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

def new_context(p, browser, seg):
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080},
                              record_video_dir=OUT,
                              record_video_size={"width": 1920, "height": 1080})
    return ctx

def open_m1(ctx):
    page = ctx.new_page()
    page.goto(BASE + "/m1")
    page.wait_for_load_state("networkidle", timeout=30000)
    return page

def seg_home(p, browser):
    ctx = new_context(p, browser, "home"); page = open_m1(ctx)
    banner(page, "一键解析样本：三面板信息架构（解析结果 / 表头映射 / 复核校验）", 4.5)
    page.click("#sampleBtn")
    t0 = time.time()
    while time.time() - t0 < 60:
        tc = page.evaluate("() => (document.getElementById('tableCount')||{}).textContent || ''").strip()
        if tc not in ("", "-", "0 表"):
            break
        time.sleep(1.0)
    time.sleep(2.0)
    banner(page, "解析 → 映射 → 校验，一屏闭环；任何数字可回溯到原始表格行", 5)
    page.evaluate("document.getElementById('reconcileSection') && document.getElementById('reconcileSection').scrollIntoView()")
    time.sleep(2.5)
    page.evaluate("window.scrollTo(0,0)"); time.sleep(1.5)
    ctx.close()

def seg_fast(p, browser):
    ctx = new_context(p, browser, "fast"); page = open_m1(ctx)
    banner(page, "快速通道：持仓对比这类结构化查询，毫秒级返回", 4.5)
    t0 = time.time()
    while time.time() - t0 < 20:
        n = page.evaluate("() => document.getElementById('cmpProduct').options.length")
        if n and n > 0:
            break
        time.sleep(0.5)
    page.evaluate("""() => {
        const sel = document.getElementById('cmpProduct');
        const opt = Array.from(sel.options).find(o => o.value.includes('嘉兴民安'));
        if (opt) sel.value = opt.value;
        sel.dispatchEvent(new Event('change'));
    }""")
    time.sleep(1.0)
    page.click("#cmpPosBtn")
    time.sleep(2.5)
    banner(page, "持仓数 / 证券名称 / 市值 / 占比——结果带出处，无出处的数字不显示", 5.5)
    ctx.close()

def seg_transparency(p, browser):
    ctx = new_context(p, browser, "transparency"); page = open_m1(ctx)
    banner(page, "检索透明：检索条数可调，路由与耗时逐问标注", 4)
    page.select_option("#m2TopK", "5"); time.sleep(1.0)
    ask(page, "复熙混合25号的单位净值是多少？", timeout=75)
    banner(page, "meta 行如实标注：走哪条路、检索几条、花了多久", 4.5)
    ctx.close()

def seg_jiahe(p, browser):
    ctx = new_context(p, browser, "jiahe"); page = open_m1(ctx)
    banner(page, "电子件解析：毫秒级完成", 3.5)
    upload(page, JIAHE, timeout=60)
    banner(page, "嘉合同版式 8 份：一轮 93.8% → 规则沉淀后复测 100%", 5.5)
    ctx.close()

def seg_sugg_a(p, browser):
    ctx = new_context(p, browser, "sugg_a"); page = open_m1(ctx)
    banner(page, "建议映射：上传对账单，系统生成映射建议（等待段后期加速）", 4)
    upload(page, GUOJIN, timeout=180)
    ctx.close()

def seg_sugg_b(p, browser):
    ctx = new_context(p, browser, "sugg_b"); page = open_m1(ctx)
    page.click("#suggBtn"); time.sleep(2.0)
    banner(page, "原列名 / 建议标准字段 / 置信度 / 理由，可勾选应用或拒绝", 5.5)
    page.evaluate("""() => {
        const cb = document.querySelector('#suggModal input[type=checkbox]');
        if (cb) cb.click();
    }""")
    time.sleep(1.5)
    banner(page, "应用前过回归门禁——最难样本 35.7%→100% 即此闭环", 5.5)
    page.click("#suggCloseBtn"); time.sleep(1.0)
    ctx.close()

def seg_review_mt_refusal(p, browser):
    ctx = new_context(p, browser, "review_mt_refusal"); page = open_m1(ctx)
    page.click("#sampleBtn"); time.sleep(3.0)
    banner(page, "复核面板：勾稽校验如实标注，未映射列清单透明可见", 4.5)
    page.evaluate("document.getElementById('reconcileSection') && document.getElementById('reconcileSection').scrollIntoView()")
    time.sleep(1.5)
    ask(page, "嘉兴民安的总资产是多少？", timeout=75)
    ask(page, "其中证券市值占多少？", timeout=75)
    banner(page, "追问\"其中…\"自动关联上一轮实体", 4)
    ask(page, "星辰私募1号的资产总值是多少？", timeout=75)
    banner(page, "库中没有的数据明确说\"未找到\"，不编造", 4.5)
    ctx.close()

def seg_ocr(p, browser):
    ctx = new_context(p, browser, "ocr"); page = open_m1(ctx)
    banner(page, "传真扫描件：本地视觉模型看图识字，全程不出域（等待段加速）", 4.5)
    page.set_input_files("#fileInput", WAVEFAX)
    time.sleep(2)
    banner(page, "视觉模型逐页识别中——推理全程本地, 不出域", 70)
    time.sleep(3)
    ctx.close()

def seg_agent(p, browser):
    ctx = new_context(p, browser, "agent"); page = open_m1(ctx)
    banner(page, "深度验证通道：独立验证代理逐条核对检索证据", 4.5)
    txt, elapsed, timed_out = ask(page, "复熙混合25号的资产总值是多少？", timeout=80)
    note = "实测 %.0f 秒完成" % elapsed if not timed_out else "超预算，已安全回落并记录原因"
    banner(page, "本问" + note + "；偶发超时会安全回落到快速通道，原因可查", 6)
    print("AGENT_SEG elapsed=%.1f timed_out=%s" % (elapsed, timed_out), flush=True)
    ctx.close()

SEGS = {
    "home": seg_home, "fast": seg_fast, "transparency": seg_transparency,
    "jiahe": seg_jiahe, "sugg_a": seg_sugg_a, "sugg_b": seg_sugg_b,
    "review_mt_refusal": seg_review_mt_refusal, "ocr": seg_ocr, "agent": seg_agent,
}

def main():
    os.makedirs(OUT, exist_ok=True)
    names = list(SEGS) if len(sys.argv) < 2 or sys.argv[1] == "all" else sys.argv[1:]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name in names:
            t0 = time.time()
            SEGS[name](p, browser)
            print("[seg] %s done %.1fs" % (name, time.time() - t0), flush=True)
        browser.close()
    print("RECORD DONE", flush=True)

if __name__ == "__main__":
    main()
