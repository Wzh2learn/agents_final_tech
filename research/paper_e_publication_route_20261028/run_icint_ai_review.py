#!/usr/bin/env python3
"""Two isolated-context local AI reviews of a frozen manuscript, with receipts."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request


SYSTEM = (
    "You are a careful first-time scientific reader. You have only the supplied manuscript "
    "and no internet, source code, raw data, or external literature. Do not invent checks "
    "you did not perform. Separate what the manuscript states, your inference, and what "
    "would require independent verification. Identify concrete, actionable issues with "
    "the section and a short supporting quote. Be precise about statistical and causal "
    "limits without asking for impossible universal guarantees. Respond as plain text."
)
FOCI = {
    "narrative": (
        "Evaluate the single research question and what each case contributes. Identify "
        "up to five issues that would confuse a first-time reviewer, including whether "
        "the results and a simple baseline support the stated contribution. For each "
        "issue give severity, section, a short quote, and a concrete fix. Also list two "
        "strengths and any manuscript-only uncertainties. Do not claim a venue decision."
    ),
    "methods": (
        "Audit whether the described experimental units, thresholds, statistical claims, "
        "baselines, exposure and reproducibility details allow a reader to interpret "
        "the results. Identify up to five high-impact ambiguities or possible errors; "
        "include the section, short quote, why it matters and a verifiable fix. Separate "
        "suspected errors from missing detail. Do not assess actual reference existence "
        "or assert that numerical calculations were independently checked."
    ),
}


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-blob", required=True)
    parser.add_argument("--source-commit", required=True)
    args = parser.parse_args()
    source = args.manuscript.read_bytes()
    git_blob = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
    if git_blob != args.expected_blob:
        raise ValueError("Manuscript bytes do not match frozen Git blob")
    manuscript = source.decode("utf-8")
    args.output.mkdir(parents=True, exist_ok=False)
    events = []
    manifest = {"source_sha256": hashlib.sha256(source).hexdigest(), "source_git_blob": git_blob,
                "source_commit": args.source_commit, "model": "Qwen3.6-35B-A3B-Q4_K_M.gguf",
                "max_posts": len(FOCI), "max_output_per_post": 4096, "temperature": 0,
                "thinking": False, "requests_independent_context": True, "retries": 0,
                "limitations": "Single local AI model, manuscript-only, not human review or source verification."}
    dump(args.output / "manifest.json", manifest)
    for name, focus in FOCI.items():
        request = {"model": manifest["model"], "temperature": 0, "max_tokens": 4096,
                   "chat_template_kwargs": {"enable_thinking": False},
                   "messages": [{"role": "system", "content": SYSTEM},
                                {"role": "user", "content": focus + "\n\nMANUSCRIPT:\n" + manuscript}]}
        dump(args.output / (name + "_request.json"), request)
        event = {"focus": name, "status": "ATTEMPT_STARTED", "usage": None,
                 "started_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
        events.append(event)
        dump(args.output / "ledger.json", events)
        started = time.monotonic()
        req = urllib.request.Request("http://127.0.0.1:8004/v1/chat/completions",
                                     data=json.dumps(request).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=300) as response:
                raw = response.read()
            (args.output / (name + "_response.json")).write_bytes(raw)
            obj = json.loads(raw)
            event["usage"] = obj.get("usage")
            choice = obj["choices"][0]
            content = choice.get("message", {}).get("content") or ""
            (args.output / (name + "_review.txt")).write_text(content, encoding="utf-8")
            event["finish_reason"] = choice.get("finish_reason")
            event["status"] = "RESPONSE_RECEIVED" if content.strip() else "EMPTY_RESPONSE"
            event["content_chars"] = len(content)
            event["response_sha256"] = hashlib.sha256(raw).hexdigest()
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, IndexError) as exc:
            event["status"] = "REQUEST_OR_PARSE_FAILURE"
            event["error_type"] = type(exc).__name__
        event["elapsed_seconds"] = round(time.monotonic() - started, 3)
        dump(args.output / "ledger.json", events)
        print(json.dumps(event, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
