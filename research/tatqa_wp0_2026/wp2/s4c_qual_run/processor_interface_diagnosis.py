#!/usr/bin/env python3
"""Zero-model diagnosis of the S4C online failure (no weights, no requests).

Hypothesis: SchemaConstraintProcessor.__call__(logits, input_ids) assumes a
scores-first invocation, while transformers calls logits processors as
(input_ids, scores). This script inspects the installed convention and
reproduces both call orders with mock tensors only. Read-only on frozen
components.
"""
from __future__ import annotations

import inspect
import json
import sys
import traceback
from pathlib import Path

import torch
import transformers

HERE = Path(__file__).resolve().parent
WP2 = HERE.parent
BRIDGE_V2 = WP2 / "bridge_v2"
sys.path.insert(0, str(BRIDGE_V2))

from constrained_decoding_v2 import build_processor  # noqa: E402
from transformers import AutoTokenizer  # noqa: E402


def attempt(label, fn):
    record = {"label": label, "raised": False, "error": None, "traceback_tail": None}
    try:
        fn()
    except Exception as exc:  # noqa: BLE001
        record["raised"] = True
        record["error"] = f"{type(exc).__name__}: {exc}"
        tb = traceback.format_exc()
        record["traceback_tail"] = "\n".join(tb.strip().splitlines()[-12:])
    return record


def main():
    out = {
        "transformers_version": transformers.__version__,
        "torch_version": torch.__version__,
    }
    try:
        from transformers.generation.logits_process import LogitsProcessor

        out["LogitsProcessor_call_signature"] = str(
            inspect.signature(LogitsProcessor.__call__)
        )
    except Exception as exc:  # noqa: BLE001
        out["LogitsProcessor_call_signature"] = f"{type(exc).__name__}: {exc}"

    try:
        import transformers.generation.utils as gu

        hits = []
        for line_no, line in enumerate(inspect.getsource(gu).splitlines(), 1):
            if "logits_processor(" in line:
                hits.append(f"{line_no}: {line.strip()}")
        out["generation_utils_logits_processor_call_sites"] = hits[:10]
    except Exception as exc:  # noqa: BLE001
        out["generation_utils_logits_processor_call_sites"] = [f"{type(exc).__name__}: {exc}"]

    tokenizer = AutoTokenizer.from_pretrained(
        "/home/testuser/wzh/models/hf/Qwen3-8B",
        local_files_only=True,
        trust_remote_code=False,
    )

    micro = {}
    for label, ids in {"negative_id": [-12], "huge_id": [10 ** 10], "valid_id": [0]}.items():
        micro[label] = attempt(
            f"decode({label})",
            lambda ids=ids: tokenizer.decode(ids, skip_special_tokens=False),
        )
    out["tokenizer_decode_micro"] = micro

    prompt_len = 16
    prompt_ids = torch.full(
        (1, prompt_len),
        tokenizer.convert_tokens_to_ids("Return") or 0,
        dtype=torch.long,
    )
    vocab = len(tokenizer.get_vocab())
    scores = torch.zeros(1, vocab, dtype=torch.float32)
    scores[0, 17] = -12.5
    scores[0, 313] = -3.7
    scores[0, 610] = 9.25

    proc_a = build_processor("plan", tokenizer, prefix_token_count=prompt_len)
    out["call_scores_first__as_offline_dry_run_did"] = attempt(
        "processor(scores, input_ids)  [offline dry-run convention]",
        lambda: proc_a(scores.clone(), prompt_ids.clone()),
    )

    proc_b = build_processor("plan", tokenizer, prefix_token_count=prompt_len)
    out["call_input_ids_first__transformers_convention"] = attempt(
        "processor(input_ids, scores)  [transformers call-site convention]",
        lambda: proc_b(prompt_ids.clone(), scores.clone()),
    )
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()