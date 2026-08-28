"""C4 VLM 探针（段 B）: 视觉层判别力——VLM 读渲染表图首行表头, 与注入映射对账。

端点 :8007（实验专用, 用毕即停）; 全合成渲染甲方零进入。检查点可续跑。
判定（镜像 K2 + qa_arm 口径）: 照读注入变体 = 视觉层吸收（盲）; 纠正回原列名 = 视觉层判别。
"""
import base64
import importlib.util
import json
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REND = REPO / "logs" / "graph" / "eval" / "c4_rendered"
OUT = REPO / "logs" / "graph" / "eval" / "c4_visual_probe_results.json"
CKPT = REPO / "logs" / "graph" / "eval" / "c4_visual_probe_checkpoint.json"
ENDPOINT = "http://127.0.0.1:8007/v1/chat/completions"
PROMPT = ("这是一张表格图片。请只读出表格第一行（表头行）每一列的列名，"
          "按从左到右的顺序输出为 JSON 数组（字符串数组），不要输出任何其他文字。")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def norm(s):
    return "".join(ch.lower() for ch in str(s) if ch.isalnum())


def transcribe(b64: str) -> list[str]:
    body = json.dumps({
        "model": "Qwen3-VL-8B-Instruct",
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
        "temperature": 0.0, "max_tokens": 512,
    }).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
    a, b = text.find("["), text.rfind("]")
    if a == -1 or b <= a:
        return []
    try:
        v = json.loads(text[a:b + 1])
        return [str(x) for x in v]
    except Exception:
        return []


def main() -> int:
    assert "8007" in ENDPOINT, "探针只走 :8007"
    vg = load_module("vgmc_exp1", REPO / "research" / "vgmc_exp1.py")
    corpus = vg.load_corpus()
    ckpt = {}
    if CKPT.exists():
        ckpt = json.loads(CKPT.read_text(encoding="utf-8"))
    done = ckpt.get("done", {})
    t0 = time.time()
    for uid in sorted(corpus):
        if uid in done:
            continue
        img = (REND / f"{uid}.png")
        if not img.exists():
            continue
        b64 = base64.b64encode(img.read_bytes()).decode()
        try:
            tr = transcribe(b64)
            err = None
        except Exception as ex:
            tr, err = [], repr(ex)[:120]
        rec = corpus[uid]
        norm_tr = [norm(t) for t in tr]
        entries = []
        for e in rec["entries"]:
            inj, orig = rec["inj_header"][e["col"]], e["original"]
            read = tr[e["col"]] if e["col"] < len(tr) else None
            if read is None:
                verdict = "no_transcript"
            elif norm(read) == norm(inj):
                verdict = "faithful_absorbed"
            elif norm(read) == norm(orig):
                verdict = "corrected_discriminated"
            else:
                verdict = "other"
            entries.append({"col": e["col"], "type": e.get("type"), "injected": inj,
                            "original": orig, "read": read, "verdict": verdict})
        done[uid] = {"transcribed": tr, "error": err, "entries": entries,
                     "latency_s": round(time.time() - t0, 1)}
        t0 = time.time()
        if len(done) % 10 == 0:
            CKPT.write_text(json.dumps({"done": done}, ensure_ascii=False), encoding="utf-8")
            print(f"[probe] {len(done)}/{len(corpus)}", flush=True)
    CKPT.write_text(json.dumps({"done": done}, ensure_ascii=False), encoding="utf-8")

    # 聚合: 逐类视觉判别谱（镜像 K2 by_type）
    by_type = {}
    for uid, blk in done.items():
        for e in blk["entries"]:
            t = e["type"] or "?"
            by_type.setdefault(t, {"n": 0, "faithful": 0, "corrected": 0, "other": 0, "no_transcript": 0})
            by_type[t]["n"] += 1
            if e["verdict"] == "faithful_absorbed":
                by_type[t]["faithful"] += 1
            elif e["verdict"] == "corrected_discriminated":
                by_type[t]["corrected"] += 1
            elif e["verdict"] == "no_transcript":
                by_type[t]["no_transcript"] += 1
            else:
                by_type[t]["other"] += 1
    for t, v in by_type.items():
        v["visual_disc_rate"] = round(v["corrected"] / v["n"], 4) if v["n"] else None
    out = {"meta": {"name": "c4-visual-probe", "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "endpoint": ENDPOINT, "n_tables": len(done),
                    "caliber": "全合成渲染（PIL, 95 表 TAT-QA 底座）; 甲方真实数据红线禁入; 判定镜像 K2+qa_arm"},
           "by_type": by_type, "tables": done}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"n_tables": len(done), "by_type": by_type, "out": str(OUT)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
