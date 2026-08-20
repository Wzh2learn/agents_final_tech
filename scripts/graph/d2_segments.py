#!/usr/bin/env python3
"""D2: spec-decode acceptance rate segmented by traffic type (pure observation).

Segments:
  A kiosk background window (180s) - estimates bleed rate for subtraction
  B eval deterministic 16 questions via :5050 (route=on -> agent attempts)
  C manual agent-route asks x2 via :5050
  D controlled direct :8006 requests: xhigh XML-style vs xhigh freeform

No config changes. Writes logs/graph/eval/d2_acceptance_segments.json.
"""
import json, re, time, urllib.request, subprocess, datetime, pathlib, sys

REPO = pathlib.Path(__file__).resolve().parents[2] if pathlib.Path(__file__).name != "d2_segments.py" else pathlib.Path.cwd()
M8006 = "http://127.0.0.1:8006/metrics"
ASK = "http://127.0.0.1:5050/api/m2/ask"
OUT = REPO / "logs" / "graph" / "eval" / "d2_acceptance_segments.json"

COUNTERS = ["vllm:spec_decode_num_drafts_total",
            "vllm:spec_decode_num_draft_tokens_total",
            "vllm:spec_decode_num_accepted_tokens_total"]
PERPOS = "vllm:spec_decode_num_accepted_tokens_per_pos_total"

def snap():
    txt = urllib.request.urlopen(M8006, timeout=10).read().decode()
    d = {}
    for line in txt.splitlines():
        if line.startswith("#"):
            continue
        for c in COUNTERS:
            if line.startswith(c + "{") or line.startswith(c + " "):
                d[c.split(":")[1]] = float(line.split()[-1])
        m = re.match(re.escape(PERPOS) + r'\{engine="0",model_name="[^"]+",position="(\d)"\}\s+([\d.eE+-]+)', line)
        if m:
            d[f"pos{m.group(1)}"] = float(m.group(2))
    return d

def diff(a, b):
    return {k: b.get(k, 0) - a.get(k, 0) for k in a}

def summarize(name, d, dur_s, bg_rate=None):
    drafts = d.get("spec_decode_num_drafts_total", 0)
    accepted = d.get("spec_decode_num_accepted_tokens_total", 0)
    dtokens = d.get("spec_decode_num_draft_tokens_total", 0)
    seg = {"segment": name, "duration_s": round(dur_s, 1),
           "drafts_raw": round(drafts, 1), "accepted_raw": round(accepted, 1),
           "draft_tokens_raw": round(dtokens, 1)}
    if bg_rate and dur_s:
        sub = bg_rate * dur_s
        drafts = max(0.0, drafts - sub)
        seg["drafts_bg_sub"] = round(drafts, 1)
        seg["bg_drafts_subtracted"] = round(sub, 1)
    seg["acceptance"] = round(accepted / drafts, 3) if drafts > 5 else None
    seg["tokens_per_draft"] = round(dtokens / d.get("spec_decode_num_drafts_total", 1), 2) if d.get("spec_decode_num_drafts_total", 0) > 5 else None
    perpos = {k: round(v, 1) for k, v in d.items() if k.startswith("pos")}
    tot = sum(perpos.values())
    seg["per_pos_pct"] = {k: round(100.0 * v / d.get("spec_decode_num_drafts_total", 1), 2) for k, v in perpos.items()} if d.get("spec_decode_num_drafts_total", 0) > 5 else {}
    return seg

def post_ask(question, timeout=120):
    body = json.dumps({"question": question, "top_k": 3}).encode()
    req = urllib.request.Request(ASK, data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        return time.time() - t0, data.get("model"), len(data.get("sources") or [])
    except Exception as e:
        return time.time() - t0, f"ERR:{e}", 0

def direct_8006(messages, thinking, label):
    payload = {"model": "qwen38-27b-fp8", "messages": messages, "max_tokens": 600,
               "temperature": 0.6,
               "chat_template_kwargs": {"enable_thinking": thinking != "off"}}
    if thinking != "off":
        payload["reasoning_effort"] = thinking
    req = urllib.request.Request("http://127.0.0.1:8006/v1/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read().decode())
        usage = data.get("usage", {})
        return {"label": label, "dur_s": round(time.time() - t0, 1),
                "completion_tokens": usage.get("completion_tokens"),
                "reasoning_tokens": usage.get("completion_tokens_details", {}).get("reasoning_tokens")}
    except Exception as e:
        return {"label": label, "err": str(e), "dur_s": round(time.time() - t0, 1)}

def main():
    report = {"meta": {"name": "d2-acceptance-segments",
                       "generated": datetime.datetime.now().isoformat(timespec="seconds"),
                       "note": "pure observation; kiosk running; bg subtraction from segment A"},
              "segments": [], "controls": []}
    # A: kiosk background
    print("[A] kiosk background window 180s ...", flush=True)
    s0 = snap(); t0 = time.time()
    time.sleep(180)
    s1 = snap(); durA = time.time() - t0
    dA = diff(s0, s1)
    segA = summarize("A_kiosk_background", dA, durA)
    report["segments"].append(segA)
    bg_rate = dA.get("spec_decode_num_drafts_total", 0) / durA if durA else 0
    report["bg_drafts_per_s"] = round(bg_rate, 4)
    print(f"[A] drafts={dA.get('spec_decode_num_drafts_total',0):.0f} bg_rate={bg_rate:.4f}/s acc={segA['acceptance']}", flush=True)

    # B: eval deterministic 16 questions via :5050
    print("[B] eval deterministic via :5050 ...", flush=True)
    s0 = snap(); t0 = time.time()
    rc = subprocess.run([sys.executable, "scripts/m2_eval_deterministic.py"],
                        cwd=str(REPO), capture_output=True, text=True, timeout=1500).returncode
    durB = time.time() - t0
    dB = diff(s0, snap())
    segB = summarize("B_eval_deterministic_16q", dB, durB, bg_rate)
    segB["eval_rc"] = rc
    report["segments"].append(segB)
    print(f"[B] rc={rc} dur={durB:.0f}s drafts_raw={dB.get('spec_decode_num_drafts_total',0):.0f} acc={segB['acceptance']}", flush=True)

    # C: manual agent-route asks x2
    fx = json.loads((REPO / "tests" / "fixtures" / "m2_eval_questions.json").read_text(encoding="utf-8"))
    qs = [q for q in fx.get("questions", []) if q.get("category") == "deterministic"][:2]
    print(f"[C] manual asks x{len(qs)} ...", flush=True)
    s0 = snap(); t0 = time.time()
    cinfo = []
    for q in qs:
        turns = q.get("turns") or [q.get("question", "")]
        first = turns[0] if isinstance(turns, list) else str(turns)
        dur, model, nsrc = post_ask(first)
        cinfo.append({"q": q.get("id"), "dur_s": round(dur, 1), "model": model, "sources": nsrc})
    durC = time.time() - t0
    dC = diff(s0, snap())
    segC = summarize("C_manual_agent_asks", dC, durC, bg_rate)
    segC["asks"] = cinfo
    report["segments"].append(segC)
    print(f"[C] dur={durC:.0f}s drafts_raw={dC.get('spec_decode_num_drafts_total',0):.0f} acc={segC['acceptance']} asks={cinfo}", flush=True)

    # D: controlled direct :8006 requests
    xml_prompt = [
        {"role": "system", "content": "You are a verification agent. Think step by step, then answer using XML tool-call format: <tool>search</tool><query>...</query> and finally <answer>...</answer>."},
        {"role": "user", "content": "List the three largest tables you would need to verify a fund reconciliation statement, then give the final balance identity equation. Use the XML format."}]
    free_prompt = [
        {"role": "user", "content": "In three sentences, explain why speculative decoding is lossless with respect to the target model distribution."}]
    print("[D] controlled direct requests ...", flush=True)
    for msgs, label in ((xml_prompt, "D1_xhigh_xml_agent_style"), (free_prompt, "D2_xhigh_freeform")):
        s0 = snap(); t0 = time.time()
        info = direct_8006(msgs, "xhigh", label)
        dur = time.time() - t0
        dD = diff(s0, snap())
        segD = summarize(label, dD, dur, bg_rate)
        segD["request"] = info
        report["segments"].append(segD)
        print(f"[{label}] dur={dur:.0f}s drafts_raw={dD.get('spec_decode_num_drafts_total',0):.0f} acc={segD['acceptance']} info={info}", flush=True)

    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"report: {OUT}")

if __name__ == "__main__":
    main()