#!/usr/bin/env python3
"""Assemble demo_v3.mp4: chapters = (video sources with speed factors) + per-chapter 配音。

速度自适应: 每章视频时长向音频时长靠拢 (setpts 加速, 上限 16x; 仍超长则裁至目标; 视频短于音频则 tpad 冻帧补齐)。
输出: 1920x1080 30fps h264+aac。
"""
import json, os, subprocess, sys
import imageio_ffmpeg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VD = os.path.join(ROOT, "docs", "experiments", "2026-08-25_demo_video_v3")
SEGS = os.path.join(VD, "segs")
CARDS = os.path.join(VD, "cards")
AUDIO = os.path.join(VD, "audio")
WORK = os.path.join(VD, "work")
FF = imageio_ffmpeg.get_ffmpeg_exe()

# chapter: (name, audio, [(kind, file, speed)])
CHAPTERS = [
    ("ch01_open", "seg01_open.mp3", [("card", "card_open.png", 1)]),
    ("ch02_home", "seg02_home.mp3", [("seg", "seg_home.webm", 1)]),
    ("ch03_fast", "seg03_fast.mp3", [("seg", "seg_fast.webm", 1)]),
    ("ch04_trans", "seg04_trans.mp3", [("seg", "seg_transparency.webm", 1)]),
    ("ch05_jiahe", "seg05_jiahe.mp3", [("seg", "seg_jiahe.webm", 1)]),
    ("ch06_sugg", "seg06_sugg.mp3", [("seg", "seg_sugg_a.mp4", 4), ("seg", "seg_sugg_b.webm", 1)]),
    ("ch07_review", "seg07_review.mp3", [("seg", "seg_review_mt_refusal.webm", 1)]),
    ("ch08_ocr", "seg08_ocr.mp3", [("seg", "seg_ocr.webm", 1)]),
    ("ch09_agent", "seg09_agent.mp3", [("seg", "seg_agent.webm", 1)]),
    ("ch10_selfheal", "seg10_selfheal.mp3", [("card", "card_selfheal.png", 1)]),
    ("ch11_end", "seg11_end.mp3", [("card", "card_metrics.png", 1), ("card", "card_end.png", 1)]),
]

def run(args):
    r = subprocess.run([FF] + args, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffmpeg failed: %s\n%s" % (args[:6], r.stderr[-900:]))
    return r

def probe_dur(path):
    r = subprocess.run([FF, "-i", path], capture_output=True, text=True)
    for line in r.stderr.splitlines():
        if "Duration" in line:
            t = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = t.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 0.0

def main():
    os.makedirs(WORK, exist_ok=True)
    parts = []
    for name, audio, vids in CHAPTERS:
        apath = os.path.join(AUDIO, audio)
        adur = probe_dur(apath)
        if adur <= 0:
            sys.exit("bad audio: " + apath)
        target = adur + 0.6
        # 1) 每个视频源按预选速度归一化成中间片段 (无声)
        subs = []
        for j, (kind, f, speed) in enumerate(vids):
            src = os.path.join(CARDS if kind == "card" else SEGS, f)
            out = os.path.join(WORK, "%s_v%d.mp4" % (name, j))
            if kind == "card":
                # 卡片时长按章内均分 (最后一张吃余数)
                share = target / len(vids)
                run(["-y", "-loop", "1", "-i", src, "-t", "%.2f" % share,
                     "-vf", "scale=1920:1080,fps=30", "-preset", "ultrafast", "-crf", "20", "-c:v", "libx264", "-pix_fmt", "yuv420p", out])
            else:
                vf = "setpts=PTS/%g,scale=1920:1080,fps=30" % speed if speed > 1 else "scale=1920:1080,fps=30"
                run(["-y", "-i", src, "-vf", vf, "-preset", "ultrafast", "-crf", "20", "-c:v", "libx264", "-pix_fmt", "yuv420p", out])
            subs.append(out)
        # 2) 拼接本章视频
        vcat = os.path.join(WORK, name + "_vcat.mp4")
        if len(subs) == 1:
            os.replace(subs[0], vcat)
        else:
            lst = os.path.join(WORK, name + ".txt")
            with open(lst, "w") as fh:
                for s2 in subs:
                    fh.write("file '%s'\n" % s2)
            run(["-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", vcat])
        vdur = probe_dur(vcat)
        # 3) 速度自适应: 视频长 → 再加速 (≤8x); 视频短 → 冻帧补齐
        fit = os.path.join(WORK, name + "_fit.mp4")
        if vdur > target + 0.8:
            factor = min(vdur / target, 16.0)
            run(["-y", "-i", vcat, "-vf", "setpts=PTS/%g,fps=30" % factor,
                 "-preset", "ultrafast", "-crf", "20", "-c:v", "libx264", "-pix_fmt", "yuv420p", fit])
            # 兜底: 加速后仍超目标 (如源段极长) → 裁至目标, 保证音画同步门
            fdur = probe_dur(fit)
            if fdur > target + 0.8:
                run(["-y", "-i", fit, "-t", "%.2f" % target, "-c:v", "libx264",
                     "-preset", "ultrafast", "-crf", "20", "-pix_fmt", "yuv420p", fit + ".trim.mp4"])
                os.replace(fit + ".trim.mp4", fit)
        elif vdur < target - 0.8:
            run(["-y", "-i", vcat, "-vf", "tpad=stop_mode=clone:stop_duration=%.2f,fps=30" % (target - vdur),
                 "-preset", "ultrafast", "-crf", "20", "-c:v", "libx264", "-pix_fmt", "yuv420p", fit])
        else:
            os.replace(vcat, fit)
        # 4) 混音 (音频为准, 视频 -shortest 截尾)
        part = os.path.join(WORK, name + ".mp4")
        fit_dur = probe_dur(fit)
        run(["-y", "-i", fit, "-i", apath, "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
             "-map", "0:v:0", "-map", "1:a:0", "-af", "apad", "-t", "%.2f" % fit_dur, part])
        parts.append(part)
        print("[chapter] %s audio=%.1fs video=%.1fs" % (name, adur, vdur), flush=True)
    # 5) 总拼接 (重编码保证参数一致)
    lst = os.path.join(WORK, "concat_v3.txt")
    with open(lst, "w") as fh:
        for pth in parts:
            fh.write("file '%s'\n" % pth)
    final = os.path.join(VD, "demo_v3.mp4")
    run(["-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", final])
    print("[done]", final, "dur=%.1fs" % probe_dur(final), flush=True)

if __name__ == "__main__":
    main()
