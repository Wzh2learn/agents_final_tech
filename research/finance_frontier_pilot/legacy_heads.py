"""Score target-generation states with the frozen v1 FinQA acquisition heads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from scoring import finqa, parse_dsl, public_execution
import finqa_acquisition_learning as acquisition


ADAPTER_FOLDERS = {"value": "acquisition_value_v1", "risk": "acquisition_risk_control_v1"}
CLASSES = ("A", "B", "N")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def public_inputs(root):
    rows = []
    for index, line in enumerate((root / "panel/public.jsonl").read_text(encoding="utf-8").splitlines()):
        row = json.loads(line)
        dataset = row["dataset"]
        public = {key: row[key] for key in finqa.PUBLIC_KEYS}
        finqa.check_public(public)
        call = root / "calls" / dataset / f"{index:03d}" / "dsl/call.json"
        parsed = parse_dsl(read_json(call)["text"])
        program = parsed["program"]
        execution = public_execution(row, parsed) if program else None
        view = {"current_program": program, "execution_feedback": execution}
        if dataset == "tatqa":
            view["predicted_scale"] = parsed["scale"] if program else None
            view = {key: view[key] for key in ("current_program", "predicted_scale", "execution_feedback")}
        elif not program:
            view["last_tool_feedback"] = None
        record = {"index": index, "dataset": dataset, "id": row["id"]}
        rows.append((record, public, view))
    return rows


def prefix_and_classes(tokenizer, request):
    encode = acquisition.m.tokens.encode_completion
    ids = [
        encode(request, {"role": "assistant", "content": json.dumps({"outcome": label})},
               tokenizer, 16384, completion_kind="text")["input_ids"]
        for label in CLASSES
    ]
    differences = [i for i, tokens in enumerate(zip(*ids)) if len(set(tokens)) > 1]
    if len(differences) != 1:
        raise ValueError("frozen classification labels must differ in one token only")
    pivot = differences[0]
    if any(seq[pivot + 1:] != ids[0][pivot + 1:] for seq in ids):
        raise ValueError("frozen classification label suffix changed")
    classes = [seq[pivot] for seq in ids]
    if len(set(classes)) != len(CLASSES):
        raise ValueError("frozen classification token collision")
    return ids[0][:pivot], classes


def forward(torch, model, tokenizer, public, state, variant):
    request = acquisition.request(public, state, state)
    try:
        prefix, classes = prefix_and_classes(tokenizer, request)
    except acquisition.m.tokens.TokenExclusion as error:
        return {"score": None, "exclusion": error.reason, "details": error.details}
    batch = torch.tensor([prefix], device="cuda")
    started = time.monotonic()
    with torch.inference_mode():
        logits = model(input_ids=batch, use_cache=False, logits_to_keep=1).logits[0, -1, classes].float()
        probabilities = [0.0, *logits[1:].softmax(-1).cpu().tolist()] if variant == "risk" else logits.softmax(-1).cpu().tolist()
    return {
        "score": probabilities[1] - probabilities[0],
        "probabilities": dict(zip(CLASSES, probabilities)),
        "input_tokens": len(prefix),
        "forward_seconds": time.monotonic() - started,
    }


def run(root):
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM
    from scripts.graph.research_gpu_guard import available_gib, gpu_lease

    output = root / "legacy_heads.json"
    if output.exists():
        raise FileExistsError(output)
    started = time.monotonic()
    inputs = public_inputs(root)
    directories = {variant: acquisition.ROOT.parent / folder for variant, folder in ADAPTER_FOLDERS.items()}
    plans = {variant: read_json(directory / "PLAN.json") for variant, directory in directories.items()}
    base_model = plans["value"]["model"]
    if plans["risk"]["model"] != base_model:
        raise ValueError("legacy adapter plans do not share a parent")
    adapters = {
        variant: directory / plans[variant]["adapter_folder"]
        for variant, directory in directories.items()
    }
    tokenizer = acquisition.m.tokens.load_tokenizer(base_model)
    rows = [{**record, "heads": {}} for record, _, _ in inputs]
    totals = {}
    with gpu_lease():
        base = AutoModelForCausalLM.from_pretrained(
            base_model, dtype=torch.bfloat16, device_map={"": 0}, attn_implementation="sdpa",
            local_files_only=True, trust_remote_code=False,
        )
        model = PeftModel.from_pretrained(
            base, str(adapters["value"]), adapter_name="value", is_trainable=False, local_files_only=True,
        )
        model.load_adapter(str(adapters["risk"]), adapter_name="risk", is_trainable=False, local_files_only=True)
        for variant in ADAPTER_FOLDERS:
            acquisition.VARIANT = variant
            model.set_adapter(variant)
            model.eval()
            for result, (_, public, state) in zip(rows, inputs):
                if available_gib() < 32:
                    raise RuntimeError("32 GiB memory reserve")
                observation = forward(torch, model, tokenizer, public, state, variant)
                result["heads"][variant] = observation
                result[variant] = observation["score"]
            completed = [result["heads"][variant] for result in rows if result[variant] is not None]
            totals[variant] = {
                "forward_calls": len(completed),
                "input_tokens": sum(record["input_tokens"] for record in completed),
                "forward_seconds": sum(record["forward_seconds"] for record in completed),
                "exclusions": len(rows) - len(completed),
            }
            print(json.dumps({"variant": variant, **totals[variant]}), flush=True)
        del model, base
        torch.cuda.empty_cache()
    result = {
        "base_model": base_model,
        "adapters": {variant: str(path) for variant, path in adapters.items()},
        "state_projection": "Initial and current are the same first-pass public DSL state; no correction history.",
        "rows": rows,
        "metrics": totals,
        "elapsed_seconds": time.monotonic() - started,
        "generated_tokens": 0,
        "http_posts": 0,
    }
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, allow_nan=False, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Project public states without loading weights")
    args = parser.parse_args()
    if args.dry_run:
        rows = public_inputs(args.root)
        print(json.dumps({"rows": len(rows), "public_states_with_program": sum(bool(row[2]["current_program"]) for row in rows)}))
    else:
        run(args.root)


if __name__ == "__main__":
    main()
