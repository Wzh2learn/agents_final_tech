"""C4 合成渲染题库（段 B, 设计稿 2026-08-26_c4_visual_prep.md §3 合成路）。

95 注入表 → PIL 网格 PNG（确定性, 零下载, 零新依赖, 全合成甲方零进入）。
产出: logs/graph/eval/c4_rendered/{uid}.png + manifest json。
"""
import importlib.util
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "logs" / "graph" / "eval" / "c4_rendered"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MAX_ROWS = 5


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> int:
    vg = load_module("vgmc_exp1", REPO / "research" / "vgmc_exp1.py")
    corpus = vg.load_corpus()
    OUT.mkdir(parents=True, exist_ok=True)
    f, fb = ImageFont.truetype(FONT, 16), ImageFont.truetype(FONT_B, 16)
    manifest = {}
    for uid in sorted(corpus):
        rec = corpus[uid]
        rows = [rec["inj_header"]] + [
            [str(c) if c is not None else "" for c in r] for r in rec["rows"][1:MAX_ROWS + 1]]
        ncol, nrow = len(rows[0]), len(rows)
        widths = []
        for c in range(ncol):
            w = max(len(str(rows[r][c])) if c < len(rows[r]) else 0 for r in range(nrow))
            widths.append(min(max(w, 4) * 9 + 12, 220))
        H = sum(30 for _ in range(nrow)) + 8
        W = sum(widths) + 8
        img = Image.new("RGB", (W, H), "white")
        d = ImageDraw.Draw(img)
        x = 4
        for c in range(ncol):
            for r in range(nrow):
                txt = str(rows[r][c]) if c < len(rows[r]) else ""
                if len(txt) * 9 > widths[c] - 8:
                    txt = txt[: (widths[c] - 14) // 9] + "…"
                d.rectangle([x, 4 + r * 30, x + widths[c], 4 + (r + 1) * 30],
                            fill="#e8e8e8" if r == 0 else "white", outline="black")
                d.text((x + 6, 4 + r * 30 + 6), txt, font=fb if r == 0 else f, fill="black")
            x += widths[c]
        img.save(OUT / f"{uid}.png")
        manifest[uid] = {"ncols": ncol, "nrows_shown": nrow, "size": [W, H]}
    mpath = OUT / "manifest.json"
    mpath.write_text(json.dumps({"n_tables": len(manifest), "tables": manifest},
                                ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"n_tables": len(manifest), "out": str(OUT)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
