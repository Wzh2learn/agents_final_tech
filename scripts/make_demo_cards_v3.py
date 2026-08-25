#!/usr/bin/env python3
"""Demo v3 标题卡生成 (S5 前置): 1920x1080 PNG, Noto Sans CJK。"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "experiments", "2026-08-25_demo_video_v3", "cards")
W, H = 1920, 1080
BG = (17, 24, 39)
ACCENT = (37, 99, 235)
WHITE = (245, 247, 250)
GREY = (156, 163, 175)

def font(size, bold=False):
    path = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    if not os.path.exists(path):
        import glob
        cands = glob.glob("/usr/share/fonts/opentype/noto/NotoSansCJK-*.ttc")
        path = cands[0]
    return ImageFont.truetype(path, size)

def center(d, text, y, fnt, fill):
    bbox = d.textbbox((0, 0), text, font=fnt)
    d.text(((W - (bbox[2] - bbox[0])) / 2, y), text, font=fnt, fill=fill)

def card(name, title, subtitle=None, bullets=None):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 6, W, H], fill=ACCENT)
    y = 250 if bullets else 380
    center(d, title, y, font(72, True), WHITE)
    y += 120
    if subtitle:
        center(d, subtitle, y, font(40), GREY)
        y += 90
    for b in bullets or []:
        center(d, b, y, font(40), WHITE)
        y += 72
    img.save(os.path.join(OUT, name))
    print("card", name)

def main():
    os.makedirs(OUT, exist_ok=True)
    card("card_open.png", "金融对账单智能解析与问答系统",
         "最新进展演示 · 2026-08-25", ["解析 · 校验 · 问答"])
    card("card_selfheal.png", "自愈与可观测",
         None,
         ["连接使用前预检 · 闲置自动回收", "异常回落原因显式暴露", "九项哨兵巡检全天候运行"])
    card("card_metrics.png", "当前指标",
         None,
         ["标准测试集 16 / 16 通过 · 数值忠实度零幻觉",
          "快速通道秒级作答",
          "对抗性测试完成率约 19%，完成均在 31-45 秒预算内",
          "判别力测试床就位 · 专利申请文件已递交"])
    card("card_end.png", "下一步",
         None,
         ["精简作答步骤 · 瘦身上下文，提升深度通道完成率", "前端工作台改版迭代", "谢谢观看"])

if __name__ == "__main__":
    main()
