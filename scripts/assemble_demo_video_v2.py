#!/usr/bin/env python3
"""Assemble demo_v2.mp4 from cards + recorded segments (speedup + concat)."""
import os, subprocess, sys
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VD = os.path.join(ROOT, "docs", "experiments", "2026-08-15_demo_video_v2")
SEGS = os.path.join(VD, "segs")
CARDS = os.path.join(VD, "cards")
WORK = os.path.join(VD, "work")
FF = imageio_ffmpeg.get_ffmpeg_exe()

# (kind, path, seconds_or_speed)
MANIFEST = [
    ("card", "card_open.png", 4),
    ("seg", "seg_open.webm", 1),
    ("seg", "seg_qa_direct.webm", 1),
    ("seg", "seg_transparency.webm", 1),
    ("seg", "seg_jiahe.webm", 1),
    ("seg", "seg_suggestions_a.webm", 4, 30),  # trim: 截掉纯等待尾部
    ("seg", "seg_suggestions_b.webm", 1),
    ("seg", "seg_review_mt_ref.webm", 1),
    ("seg", "seg_ocr_a.webm", 8),
    ("seg", "seg_ocr_b.webm", 1),
    ("seg", "seg_agent_a.webm", 4),
    ("seg", "seg_agent_b.webm", 1),
    ("card", "card_end.png", 8),
]

def run(args):
    r = subprocess.run([FF] + args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ffmpeg failed: {r.stderr[-800:]}")
    return r

def main():
    os.makedirs(WORK, exist_ok=True)
    parts = []
    for i, item in enumerate(MANIFEST):
        kind, name, val = item[0], item[1], item[2]
        trim = item[3] if len(item) > 3 else None
        out = os.path.join(WORK, f"part{i:02d}.mp4")
        if kind == "card":
            run(["-y", "-loop", "1", "-i", os.path.join(CARDS, name), "-t", str(val),
                 "-vf", "scale=1440:900,fps=30", "-c:v", "libx264", "-pix_fmt", "yuv420p", out])
        else:
            vf = f"setpts=PTS/{val},scale=1440:900,fps=30" if val > 1 else "scale=1440:900,fps=30"
            args = ["-y", "-i", os.path.join(SEGS, name), "-vf", vf,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p"]
            if trim:
                args += ["-t", str(trim)]
            args.append(out)
            run(args)
        parts.append(out)
        print(f"[part] {i:02d} {kind} {name}")
    lst = os.path.join(WORK, "concat.txt")
    with open(lst, "w") as f:
        for pth in parts:
            f.write(f"file '{pth}'\n")
    final = os.path.join(VD, "demo_v2.mp4")
    run(["-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", final])
    r = subprocess.run([FF, "-i", final], capture_output=True, text=True)
    dur = [l for l in r.stderr.splitlines() if "Duration" in l]
    print("[done]", final, "|", dur[0].strip() if dur else "?")

if __name__ == "__main__":
    main()