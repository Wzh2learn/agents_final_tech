#!/usr/bin/env python3
"""Record the client demo video in segments (playwright recordVideo).

Segments:
  seg1  直连路快问快答 (record with M2_OPENCODE_ROUTE=off)
  seg2  agent 验证链路关键数字 + 对照 (route on)
  seg3  上传嘉合 PDF (route on)
  seg4  上传 WaveFax 传真 OCR 故事 (route on)
  seg5  复核面板 + 多轮追问 + 诚实拒答 (route on)

Output: docs/experiments/2026-08-09_demo_video/<segment>.webm
Concatenate + mp4 conversion is done by concat_demo_video.sh (ffmpeg).

Usage: python scripts/record_demo_video.py seg1 seg2 ...
"""
from __future__ import annotations

import os
import sys
import time

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5050"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "experiments", "2026-08-09_demo_video")
ATT = os.path.expanduser("~/wzh/m1_samples/scenario1/attachments")
JIAHE = os.path.join(
    ATT, "转发 嘉合基金客户对账单_att0_3R8006587045_客户对帐单_2026年04月01日.pdf")
WAVEFAX = os.path.join(
    ATT, "转发 来自：(WaveFax Fax Device)_att0_20260506_132650IU.pdf")

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


def banner(page, text, hold=2.5):
    page.evaluate(BANNER_JS, text)
    time.sleep(hold)


def ask(page, q, timeout=60):
    """Ask a question in the M2 panel; wait until the answer renders."""
    page.fill("#m2Question", q)
    time.sleep(0.5)
    page.click("#m2AskBtn")
    t0 = time.time()
    last_len, stable_since = -1, time.time()
    while time.time() - t0 < timeout:
        txt = page.evaluate(
            "() => (document.getElementById('m2ChatLog')||{}).innerText || ''")
        done = ("出处" in txt or "未找到" in txt or "根据" in txt)
        if len(txt) != last_len:
            last_len, stable_since = len(txt), time.time()
        elif done and time.time() - stable_since > 1.5:
            break
        time.sleep(0.5)
    time.sleep(1.5)
    return page.evaluate(
        "() => (document.getElementById('m2ChatLog')||{}).innerText || ''")


def upload(page, path, timeout=240):
    """Upload a file; wait until parse results render."""
    page.set_input_files("#fileInput", path)
    t0 = time.time()
    while time.time() - t0 < timeout:
        tc = page.evaluate(
            "() => (document.getElementById('tableCount')||{}).textContent || ''")
        badge = page.evaluate(
            "() => (document.getElementById('reviewBadge')||{}).textContent || ''")
        tc = tc.strip()
        badge = badge.strip()
        if tc not in ("", "-", "0 表") and badge not in ("", "-"):
            break
        time.sleep(1.0)
    time.sleep(2.5)


def new_context(p, browser):
    return browser.new_context(
        viewport={"width": 1440, "height": 900},
        record_video_dir=OUT,
        record_video_size={"width": 1440, "height": 900},
    )


def seg1(p, browser):
    """直连路快问快答 (route off)."""
    ctx = new_context(p, browser)
    page = ctx.new_page()
    page.goto(BASE + "/m1")
    page.wait_for_load_state("networkidle")
    banner(page, "段 A｜直连路快问快答（约 2 秒/轮，适合快速交互）", 4)
    banner(page, "首页三面板：解析结果 / 表头信息 / 复核校验", 3)
    ask(page, "复熙混合25号的资产总值是多少？", timeout=30)
    banner(page, "看点：约 2 秒出答，数字带来源标注", 3)
    ask(page, "嘉兴民安的总资产是多少？", timeout=30)
    banner(page, "看点：连续快问，均带出处（此答案稍后与验证链路对照）", 3.5)
    time.sleep(1.5)
    ctx.close()


def seg2(p, browser):
    """agent 验证链路 (route on)."""
    ctx = new_context(p, browser)
    page = ctx.new_page()
    page.goto(BASE + "/m1")
    page.wait_for_load_state("networkidle")
    banner(page, "段 B｜多 agent 验证链路（关键数字场景，答案经独立 agent 复核）", 4)
    banner(page, "提问：嘉兴民安的总资产是多少？——等待期间独立 agent 正在复核检索证据", 3)
    ask(page, "嘉兴民安的总资产是多少？", timeout=90)
    banner(page, "看点：答案带完整溯源；与直连路对照——数字一致，验证链路多一层独立复核", 5)
    time.sleep(1.5)
    ctx.close()


def seg3(p, browser):
    """上传嘉合 PDF."""
    ctx = new_context(p, browser)
    page = ctx.new_page()
    page.goto(BASE + "/m1")
    page.wait_for_load_state("networkidle")
    banner(page, "段 D｜上传嘉合客户对账单（电子件，毫秒级解析）", 3.5)
    upload(page, JIAHE, timeout=60)
    banner(page, "看点：字段命中率 93.8%，同版式 8 份表现一致", 4)
    page.evaluate("document.getElementById('reconcileSection') && "
                  "document.getElementById('reconcileSection').scrollIntoView()")
    time.sleep(2.5)
    ctx.close()


def seg4(p, browser):
    """上传 WaveFax 传真 (OCR)."""
    ctx = new_context(p, browser)
    page = ctx.new_page()
    page.goto(BASE + "/m1")
    page.wait_for_load_state("networkidle")
    banner(page, "段 E｜上传传真扫描件（无文本层，走视觉识别通道）", 3.5)
    banner(page, "看点：视觉模型看图识字，全本地推理，数据不出域；约需半分钟", 3.5)
    upload(page, WAVEFAX, timeout=300)
    banner(page, "看点：传真件还原出结构化表格，命中率 85.7%", 4)
    time.sleep(1.5)
    ctx.close()


def seg5(p, browser):
    """复核面板 + 多轮追问 + 诚实拒答."""
    ctx = new_context(p, browser)
    page = ctx.new_page()
    page.goto(BASE + "/m1")
    page.wait_for_load_state("networkidle")
    banner(page, "段 F｜复核面板：勾稽校验四项 + 未映射列清单", 3)
    upload(page, JIAHE, timeout=60)
    page.evaluate("document.getElementById('reconcileSection') && "
                  "document.getElementById('reconcileSection').scrollIntoView()")
    banner(page, "看点：数据不足时如实标注\"跳过\"，不给虚假的通过", 4)
    page.click("#m2NewChatBtn")
    time.sleep(1)
    banner(page, "段 G｜多轮追问（自动关联上文）", 3)
    ask(page, "嘉兴民安的总资产是多少？", timeout=90)
    ask(page, "其中证券市值占多少？", timeout=90)
    banner(page, "看点：追问\"其中…\"自动关联上一轮实体", 4)
    banner(page, "段 H｜诚实拒答：库中没有的数据，明确说未找到", 3)
    ask(page, "复熙混合25号的基金经理是谁？", timeout=90)
    banner(page, "看点：只回答有出处的数字，不编造", 4)
    banner(page, "演示结束｜快与准是菜单：直连 2 秒/轮，验证链路 15-20 秒/轮", 5)
    time.sleep(1.5)
    ctx.close()


SEGS = {"seg1": seg1, "seg2": seg2, "seg3": seg3, "seg4": seg4, "seg5": seg5}


def main():
    names = sys.argv[1:] or list(SEGS)
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name in names:
            if name not in SEGS:
                sys.exit(f"unknown segment: {name}")
            print(f"[record] {name} ...", flush=True)
            t0 = time.time()
            SEGS[name](p, browser)
            print(f"[record] {name} done in {time.time()-t0:.0f}s", flush=True)
        browser.close()
    print("[record] all segments done")


if __name__ == "__main__":
    main()
