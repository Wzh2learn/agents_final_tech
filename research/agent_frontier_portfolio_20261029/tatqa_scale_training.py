"""Matched next-token LoRA supervision for a scale-only action after native execution."""
from __future__ import annotations

import argparse
from collections import defaultdict
import gc
import json
import os
from pathlib import Path
import random
import time


SCALES = ("", "thousand", "million", "billion", "percent")
ACTIONS = ("KEEP", *SCALES)
LETTERS = tuple("ABCDEF")
ARMS = ("ordinary", "paired")
DEFAULT_MODEL = Path.home() / "wzh/models/hf/Qwen3-8B"


def load_jsonl(path):
    with path.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def write_json(path, data):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def source_groups(rows, count):
    groups = defaultdict(list)
    for row in rows:
        groups[row["source"]].append(row)
    if count is not None and count < 1:
        raise ValueError("Positive TRAIN table budget required")
    result = list(groups.values())[:count]
    for group in result:
        if len(group) != 2 or sum(row["paired"] == "KEEP" for row in group) != 1:
            raise ValueError("Each TRAIN source must have one wrong-scale and one preservation state")
        if group[0]["ordinary"] != group[1]["ordinary"]:
            raise ValueError("Ordinary scale is one fixed gold label per source")
        for row in group:
            if row["ordinary"] not in SCALES or any(row[field] not in ACTIONS for field in ("paired", "negative")):
                raise ValueError("Unknown scale action")
            if row["paired"] == row["negative"]:
                raise ValueError("Positive and negative action must differ")
    if not result:
        raise ValueError("No paired TRAIN sources")
    return result


def action_token_ids(tokenizer):
    encoded = [tokenizer.encode(letter, add_special_tokens=False) for letter in LETTERS]
    if any(len(ids) != 1 for ids in encoded) or len({ids[0] for ids in encoded}) != len(LETTERS):
        raise ValueError("Each scale action needs a distinct one-token label")
    return dict(zip(ACTIONS, (ids[0] for ids in encoded)))


def encode(row, tokenizer, max_tokens):
    scale = row["scale"]
    if scale not in SCALES:
        raise ValueError("Unknown current scale")
    text = row["text"]
    prompt = (
        "Select the answer scale for the already executed numerical program. "
        "Use the question, source evidence and executed value. Leave the program unchanged. "
        "Reply with exactly one letter. A=keep current scale, B=none, C=thousand, "
        "D=million, E=billion, F=percent.\n\n"
        f"{text}\n\nCurrent scale: {scale or 'none'}"
    )
    ids = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], tokenize=True, add_generation_prompt=True,
        enable_thinking=False, return_dict=False,
    )
    if len(ids) > max_tokens:
        raise ValueError(f"Input context exceeds cap ({len(ids)} > {max_tokens} tokens)")
    return ids


def batch_inputs(encoded, pad_id, device, torch):
    length = max(map(len, encoded))
    padding = [length - len(ids) for ids in encoded]
    return {
        "input_ids": torch.tensor([[pad_id] * n + ids for ids, n in zip(encoded, padding)], device=device),
        "attention_mask": torch.tensor([[0] * n + [1] * len(ids) for ids, n in zip(encoded, padding)], device=device),
        "position_ids": torch.tensor([[0] * n + list(range(len(ids))) for ids, n in zip(encoded, padding)], device=device),
    }


def load_backbone(path):
    import torch
    from transformers import AutoModelForCausalLM

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required for Qwen3-8B LoRA")
    return AutoModelForCausalLM.from_pretrained(
        path, dtype=torch.bfloat16, device_map={"": 0}, attn_implementation="sdpa",
        local_files_only=True, trust_remote_code=False,
    )


def load_tokenizer(path):
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False)


def check_memory():
    from scripts.graph.research_gpu_guard import available_gib

    if available_gib() < 32:
        raise RuntimeError("32 GiB host memory reserve reached")


def replay_groups(path):
    if path is None:
        return []
    groups = json.loads(path.read_text(encoding="utf-8"))["groups"]
    for group in groups:
        if not group:
            raise ValueError("Empty FinQA replay group")
        for row in group:
            labels = row["labels"]
            prompt = row["prompt_token_count"]
            if (len(labels) != len(row["input_ids"]) or not 1 <= prompt < len(labels)
                    or any(label != -100 for label in labels[:prompt]) or labels[prompt] < 0
                    or sum(label != -100 for label in labels) != row["supervised_tokens"]):
                raise ValueError("FinQA replay needs the original masked positive target")
    if len(groups) != 121:
        raise ValueError("Expected exactly 121 FinQA replay source groups")
    return groups


def interleaved_schedule(scales, replay_count):
    """Spread one visit to each replay source across the fixed target schedule."""
    scale_index = replay_index = 0
    total = len(scales) + replay_count
    for update in range(total):
        if (update + 1) * len(scales) // total > scale_index:
            yield "scale", scales[scale_index]
            scale_index += 1
        else:
            yield "replay", replay_index
            replay_index += 1


def backward_replay(model, group, stats, torch, F):
    total_tokens = sum(row["supervised_tokens"] for row in group)
    total = 0.
    for row in group:
        check_memory()
        ids = torch.tensor([row["input_ids"]], device="cuda")
        target = torch.tensor(row["labels"][row["prompt_token_count"]:], device="cuda")
        logits = model(input_ids=ids, use_cache=False, logits_to_keep=len(target) + 1).logits[0, :-1, :].float()
        loss = F.cross_entropy(logits, target, ignore_index=-100, reduction="sum") / total_tokens
        if not torch.isfinite(loss):
            raise ValueError("Non-finite FinQA replay training loss")
        loss.backward()
        total += float(loss.detach())
        stats["forward_calls"] += 1
        stats["input_tokens"] += ids.shape[-1]
        stats["supervised_tokens"] += row["supervised_tokens"]
        del ids, target, logits, loss
    return total


def train(args):
    import torch
    from peft import LoraConfig, PeftModel, get_peft_model
    from torch.nn import functional as F
    from scripts.graph.research_gpu_guard import gpu_lease

    if args.epochs < 1 or args.learning_rate <= 0 or args.contrast_weight < 0:
        raise ValueError("Invalid training parameters")
    groups = source_groups(load_jsonl(args.data), args.sources)
    replay = replay_groups(args.replay_data)
    tokenizer = load_tokenizer(args.model)
    tokens = action_token_ids(tokenizer)
    encoded = [[encode(row, tokenizer, args.max_tokens) for row in group] for group in groups]
    schedule = []
    generator = random.Random(args.seed)
    for _ in range(args.epochs):
        order = list(range(len(groups)))
        generator.shuffle(order)
        schedule.extend(order)
    updates = list(interleaved_schedule(schedule, len(replay)))
    args.out.mkdir(parents=True, exist_ok=False)
    state = {
        "stage": "RUNNING", "pid": os.getpid(), "model": str(args.model),
        "warm_start": str(args.warm_start) if args.warm_start else None,
        "seed": args.seed, "epochs": args.epochs, "learning_rate": args.learning_rate,
        "contrast_weight": args.contrast_weight, "margin": args.margin,
        "selected_source_prefix": args.sources, "paired_sources": len(groups),
        "train_sources": [group[0]["source"] for group in groups],
        "replay_sources": len(replay),
        "http_posts": 0, "generated_tokens": 0, "arms": {},
    }
    started = time.monotonic()
    try:
        write_json(args.out / "LIVE.json", state)
        with gpu_lease():
            torch.manual_seed(args.seed)
            base = load_backbone(args.model)
            if args.warm_start:
                model = PeftModel.from_pretrained(base, args.warm_start, is_trainable=True)
            else:
                model = get_peft_model(base, LoraConfig(
                    r=8, lora_alpha=16, lora_dropout=0., target_modules=["q_proj", "v_proj"],
                    task_type="CAUSAL_LM", bias="none",
                ))
            model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
            model.enable_input_require_grads()
            initial = {name: weight.detach().clone() for name, weight in model.named_parameters() if weight.requires_grad}
            parameters = [weight for weight in model.parameters() if weight.requires_grad]
            if not parameters:
                raise ValueError("LoRA trainable parameters missing")
            state["trainable_parameters"] = sum(p.numel() for p in parameters)
            for arm in args.arms:
                with torch.no_grad():
                    for name, weight in model.named_parameters():
                        if name in initial:
                            weight.copy_(initial[name])
                torch.manual_seed(args.seed)
                optimizer = torch.optim.AdamW(parameters, lr=args.learning_rate)
                model.train()
                losses = []
                stats = {"updates": 0, "scale_updates": 0, "replay_updates": 0,
                         "forward_calls": 0, "input_tokens": 0, "supervised_tokens": 0}
                state["arms"][arm] = stats
                arm_started = time.monotonic()
                for kind, index in updates:
                    check_memory()
                    if time.monotonic() - started >= args.wall_seconds:
                        raise TimeoutError("Matched scale training wall limit")
                    optimizer.zero_grad(set_to_none=True)
                    if kind == "replay":
                        losses.append(backward_replay(model, replay[index], stats, torch, F))
                    else:
                        padded = batch_inputs(encoded[index], tokenizer.pad_token_id, "cuda", torch)
                        targets = torch.tensor([tokens[row[arm]] for row in groups[index]], device="cuda")
                        logits = model(**padded, use_cache=False, logits_to_keep=1).logits[:, -1, :].float()
                        loss = F.cross_entropy(logits, targets)
                        if arm == "paired":
                            negatives = torch.tensor([tokens[row["negative"]] for row in groups[index]], device="cuda")
                            row_ids = torch.arange(len(targets), device="cuda")
                            gap = logits[row_ids, negatives] - logits[row_ids, targets]
                            loss = loss + args.contrast_weight * F.softplus(args.margin + gap).mean()
                        if not torch.isfinite(loss):
                            raise ValueError("Non-finite scale training loss")
                        loss.backward()
                        losses.append(float(loss.detach()))
                        stats["forward_calls"] += 1
                        stats["input_tokens"] += sum(map(len, encoded[index]))
                        stats["supervised_tokens"] += len(targets)
                        del padded, logits, targets, loss
                    stats[f"{kind}_updates"] += 1
                    torch.nn.utils.clip_grad_norm_(parameters, 1.0, error_if_nonfinite=True)
                    optimizer.step()
                    stats["updates"] += 1
                    if stats["updates"] % 8 == 0:
                        write_json(args.out / "LIVE.json", state)
                model.save_pretrained(args.out / arm)
                stats.update(first_loss=losses[0], last_loss=losses[-1], seconds=time.monotonic() - arm_started)
                write_json(args.out / "LIVE.json", state)
                del optimizer
                gc.collect()
                torch.cuda.empty_cache()
        state["stage"] = "COMPLETE"
    except BaseException as error:
        state.update(stage="FAILED", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        state["seconds"] = time.monotonic() - started
        write_json(args.out / "LIVE.json", state)
        write_json(args.out / "RESULT.json", state)
    print(json.dumps(state), flush=True)


def predict(args):
    import torch
    from peft import PeftModel
    from scripts.graph.research_gpu_guard import gpu_lease

    arms = dict(item.split("=", 1) for item in args.arm)
    if len(arms) != len(args.arm) or args.batch_size < 1:
        raise ValueError("Use unique --arm name=directory entries and a positive batch size")
    if args.out.exists():
        raise FileExistsError(args.out)
    sources = load_jsonl(args.data)
    tokenizer = load_tokenizer(args.model)
    tokens = action_token_ids(tokenizer)
    encoded = [encode(row, tokenizer, args.max_tokens) if row.get("eligible", True) else None for row in sources]
    output = [dict(source=row["source"], scale=row["scale"], actions={}) for row in sources]
    present = [index for index, ids in enumerate(encoded) if ids is not None]
    counts = {"forward_calls": 0, "input_tokens": 0, "generated_tokens": 0, "http_posts": 0}
    started = time.monotonic()
    with gpu_lease():
        backbone = load_backbone(args.model)
        model = None
        for arm, adapter in arms.items():
            if model is None:
                model = PeftModel.from_pretrained(backbone, adapter, adapter_name=arm)
            else:
                model.load_adapter(adapter, adapter_name=arm)
            model.set_adapter(arm)
            model.eval()
            for start in range(0, len(present), args.batch_size):
                check_memory()
                indices = present[start:start + args.batch_size]
                ids = [encoded[i] for i in indices]
                inputs = batch_inputs(ids, tokenizer.pad_token_id, "cuda", torch)
                with torch.inference_mode():
                    logits = model(**inputs, use_cache=False, logits_to_keep=1).logits[:, -1, list(tokens.values())]
                    logits = logits.float().cpu().tolist()
                for i, values in zip(indices, logits):
                    permitted = range(1, len(ACTIONS)) if arm.split("-", 1)[0] == "ordinary" else range(len(ACTIONS))
                    choice = max(permitted, key=lambda at: values[at])
                    output[i]["actions"][arm] = {"action": ACTIONS[choice], "logits": dict(zip(ACTIONS, values))}
                counts["forward_calls"] += 1
                counts["input_tokens"] += sum(map(len, ids))
            for i, ids in enumerate(encoded):
                if ids is None:
                    output[i]["actions"][arm] = {"action": "KEEP", "logits": None}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    counts.update(input_rows=len(sources), neural_rows=len(present) * len(arms), seconds=time.monotonic() - started)
    write_json(args.out, {"rows": output, "counts": counts})
    print(json.dumps(counts), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    training = commands.add_parser("train")
    inference = commands.add_parser("predict")
    for command in (training, inference):
        command.add_argument("--data", required=True, type=Path)
        command.add_argument("--model", default=DEFAULT_MODEL, type=Path)
        command.add_argument("--out", required=True, type=Path)
        command.add_argument("--max-tokens", default=6144, type=int)
    training.add_argument("--warm-start", type=Path)
    training.add_argument("--sources", type=int)
    training.add_argument("--replay-data", type=Path, help="Prepared 121-source FinQA CE replay file")
    training.add_argument("--arms", nargs="+", choices=ARMS, default=ARMS)
    training.add_argument("--epochs", type=int, default=2)
    training.add_argument("--seed", type=int, default=17)
    training.add_argument("--learning-rate", type=float, default=2e-4)
    training.add_argument("--contrast-weight", type=float, default=0.1)
    training.add_argument("--margin", type=float, default=1.0)
    training.add_argument("--wall-seconds", type=float, default=5400)
    inference.add_argument("--arm", action="append", required=True, metavar="NAME=DIRECTORY")
    inference.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()
    (train if args.command == "train" else predict)(args)


if __name__ == "__main__":
    main()
